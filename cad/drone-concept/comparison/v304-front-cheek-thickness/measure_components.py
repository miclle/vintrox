"""Measure archived reference landmarks against visible saved-CAD part edges."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree

from study_drone_source_registration import initial_pose
from study_drone_still_focal import project


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def observations(comparison):
    inputs = {
        "brow": comparison / "v250-brow-tip-profile/brow-tip-samples.json",
        "wing": comparison / "v150-gold-wing-front-edge/visible-wing-edges.json",
        "petal": comparison / "v300-rear-shoulder-nozzle/visible-petal-edges.json",
    }
    for family, path in inputs.items():
        report = read(path)
        for row in report["views"]:
            if family == "brow":
                for name, points in row["reference_points"].items():
                    yield name, points, row, path, report["camera_sha256"]
            else:
                yield family, row["reference_px"], row, path, report.get("camera_config_sha256")


def select_objects(names, component, row):
    if component == "brow":
        return np.isin(names, ["ProjectingBrow", "HoodEdge", "BrowUnderside"])
    if component == "liner":
        return names == "BrowUnderside"
    if component == "wing":
        return np.array([name.startswith("Wing") and row["side"] in name for name in names])
    return np.char.startswith(names, "NozzlePetal")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "package", "mesh", "video-ids", "stills-ids", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    mesh = read(args.mesh)
    fcstd = sha(args.package / "candidate.FCStd")
    if mesh["fcstd_sha256"] != fcstd:
        raise ValueError("The mesh must belong to the saved FCStd")
    screen = np.array(next(row["vertices"] for row in mesh["objects"]
                           if row["name"] == "ScreenPanel210x160x2"))
    comparison = args.root / "cad/drone-concept/comparison"
    groups = {}
    for group, ids in (("video", args.video_ids), ("stills", args.stills_ids)):
        folder = args.package / f"{group}-comparison"
        cameras = folder / "cameras.json"
        manifest_path = ids / "object-id-manifest.json"
        manifest = read(manifest_path)
        camera_sha = sha(cameras)
        if manifest["fcstd_sha256"] != fcstd or manifest["camera_config_sha256"] != camera_sha:
            raise ValueError(f"Mismatched model or cameras for {group}")
        config = read(cameras)
        groups[group] = (folder, ids, config, manifest, camera_sha, sha(manifest_path))

    records, tiles = [], []
    for component, samples, observation, observation_file, expected_camera in observations(comparison):
        view = observation["view"]
        is_video = view.startswith("video-")
        folder, ids, config, manifest, camera_sha, manifest_sha = groups["video" if is_video else "stills"]
        if expected_camera is not None and camera_sha != expected_camera:
            raise ValueError(f"Archived sample camera differs for {view}")
        pose = next(row for row in config["views"] if row["name"] == view)
        if is_video:
            source = folder / "reference-frames" / f'frame-{pose["source_frame"] // 30 + 1:02}.png'
        else:
            source = args.root / pose["source_image"]
        if sha(source) != observation["source_sha256"]:
            raise ValueError(f"Archived reference differs for {view}")
        size = tuple(pose.get("resolution", config["resolution"]))
        focal = pose["lens_mm"] / pose["sensor_width_mm"] * size[0]
        screen_width = float(np.ptp(project(screen, initial_pose(pose), focal, size)[:, 0]))
        historical_width = next(observation[key] for key in (
            "projected_screen_horizontal_span_px", "projected_screen_width_px", "screen_width_px"
        ) if key in observation)
        if abs(historical_width - screen_width) > .01:
            raise ValueError(f"Archived screen projection differs for {view}")

        entry = next(row for row in manifest["images"] if row["view"] == view)
        id_path = ids / entry["path"]
        if sha(id_path) != entry["sha256"]:
            raise ValueError(f"Changed object ID image for {view}")
        rgba = np.array(Image.open(id_path).convert("RGBA"))
        if rgba.shape[:2] != size[::-1]:
            raise ValueError(f"Unexpected image dimensions for {view}")
        names = np.array([row["name"] for row in manifest["objects"]])
        distances, index = cKDTree([row["rgb"] for row in manifest["objects"]]).query(rgba[:, :, :3])
        members = select_objects(names, component, observation)
        mask = members[index] & (distances < 6) & (rgba[:, :, 3] > 127)
        edge = mask ^ binary_erosion(mask)
        coords = np.column_stack(np.nonzero(edge)[::-1])
        if not len(coords):
            raise ValueError(f"No visible {component} edge for {view}")
        xy = np.array(samples)
        distance, nearest = cKDTree(coords).query(xy)
        peak = float(max(distance) / screen_width)
        crop = observation.get("crop_xyxy", [
            max(0, int(xy[:, 0].min()) - 35), max(0, int(xy[:, 1].min()) - 35),
            min(size[0], int(xy[:, 0].max()) + 35), min(size[1], int(xy[:, 1].max()) + 35),
        ])
        label = component if component != "wing" else f'wing {observation["side"]}'
        records.append({
            "component": label, "view": view, "reference_sha256": observation["source_sha256"],
            "observations": str(observation_file.relative_to(args.root)),
            "observations_sha256": sha(observation_file), "camera_sha256": camera_sha,
            "id_manifest_sha256": manifest_sha, "id_image_sha256": entry["sha256"],
            "reference_px": samples, "nearest_visible_edge_px": coords[nearest].tolist(),
            "distance_px": distance.tolist(), "rms_px": float(np.sqrt(np.mean(distance ** 2))),
            "projected_screen_width_px": screen_width, "max_screen_fraction": peak,
        })

        image = Image.open(source).convert("RGB")
        image = image.resize(size, Image.Resampling.LANCZOS) if image.size != size else image
        rgb = (np.asarray(image) * .45).astype("uint8")
        rgb[edge] = (255, 90, 65)
        overlay = Image.fromarray(rgb)
        marker = ImageDraw.Draw(overlay)
        for x, y in samples:
            marker.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(50, 245, 255))
        tile = Image.new("RGB", (420, 220), (22, 25, 28))
        ImageDraw.Draw(tile).text((8, 6), f"{view}  {label}  {peak:.2%}", fill="white")
        thumb = ImageOps.contain(overlay.crop(crop), (408, 194))
        tile.paste(thumb, ((420 - thumb.width) // 2, 24))
        tiles.append(tile)

    board = Image.new("RGB", (1260, (len(tiles) + 2) // 3 * 220), (22, 25, 28))
    for index, tile in enumerate(tiles):
        board.paste(tile, (index % 3 * 420, index // 3 * 220))
    board.save(args.output / "visible-components.png")
    report = {
        "fcstd_sha256": fcstd, "mesh_sha256": sha(args.mesh),
        "method": "One-way distance from archived reference annotations to opaque visible CAD family edges.",
        "limits": ["Measurements cover the annotated portions only.",
                   "ID edges include occlusion boundaries and approximate the antialiased edge.",
                   "Near-edge-on screen projection makes the normalized percentage sensitive to pixel uncertainty."],
        "views": records,
    }
    (args.output / "visible-components.json").write_text(json.dumps(report, indent=2) + "\n")
    for row in records:
        print(row["component"], row["view"], f'{row["max_screen_fraction"]:.2%}')


if __name__ == "__main__":
    main()
