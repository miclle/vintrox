"""Compare visible underside geometry from v292 in fixed reference views."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_fill_holes
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from compare_drone_reference import reference_mask

GROUP_COLORS = {
    "ClosedBellyPan": (255, 72, 82),
    "UnderbodyLoop": (33, 226, 255),
    "UnderbodyHarness": (255, 214, 47),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_view(base, group, name, ids):
    comparison = base / ("video-comparison" if group == "video" else "stills-comparison")
    report_path = comparison / "comparison-report.json"
    report = json.loads(report_path.read_text())
    row = next(item for item in report["views"] if item["view"] == name)
    id_manifest_path = ids / "object-id-manifest.json"
    id_manifest = json.loads(id_manifest_path.read_text())
    assert id_manifest["camera_config_sha256"] == digest(comparison / "cameras.json")
    render_directory = base / ("video-renders" if group == "video" else "still-renders")
    render_manifest = json.loads((render_directory / "render-manifest.json").read_text())
    assert id_manifest["fcstd_sha256"] == report["fcstd_sha256"] == render_manifest["fcstd_sha256"]
    id_entry = next(item for item in id_manifest["images"] if item["view"] == name)
    id_path = ids / id_entry["path"]
    assert digest(id_path) == id_entry["sha256"]
    render_entry = next(item for item in render_manifest["images"] if item["view"] == name)
    render_path = render_directory / render_entry["path"]
    assert digest(render_path) == render_entry["sha256"]
    render = Image.open(render_path).convert("RGBA")
    ref_path = (
        comparison / "reference-frames" / f"frame-{int(name[-2:]) + 1:02}.png"
        if group == "video" else ROOT / row["source_image"]
    )
    reference = Image.open(ref_path).convert("RGB")
    if reference.size != render.size:
        reference = reference.resize(render.size, Image.Resampling.LANCZOS)
    ref = np.asarray(reference)
    silhouette = reference_mask(ref)
    filled_silhouette = binary_fill_holes(silhouette)
    cad = np.asarray(render)[:, :, 3] > 127
    iou = np.count_nonzero(cad & silhouette) / np.count_nonzero(cad | silhouette)
    if not np.isclose(iou, row["silhouette_iou"], rtol=0, atol=1e-12):
        raise ValueError(f"{name}: silhouette IoU differs from the baseline report")
    id_pixels = np.asarray(Image.open(id_path).convert("RGBA"))
    objects = id_manifest["objects"]
    distances, indices = cKDTree([item["rgb"] for item in objects]).query(id_pixels[:, :, :3])
    assigned = (distances < 6) & (id_pixels[:, :, 3] > 127) & cad
    masks = {}
    for prefix in GROUP_COLORS:
        group_indices = [i for i, item in enumerate(objects) if item["name"].startswith(prefix)]
        masks[prefix] = assigned & np.isin(indices, group_indices)
    y, x = np.nonzero(np.logical_or.reduce(list(masks.values())))
    bounds = (
        max(0, int(x.min()) - 24), max(0, int(y.min()) - 32),
        min(ref.shape[1], int(x.max()) + 25), min(ref.shape[0], int(y.max()) + 21),
    )
    marked = np.asarray(render.convert("RGB")).copy()
    for prefix, color in GROUP_COLORS.items():
        mask = masks[prefix]
        marked[mask] = (.45 * marked[mask] + .55 * np.asarray(color)).astype(np.uint8)
    cad_rgb = Image.new("RGB", render.size)
    cad_rgb.paste(render, mask=render.getchannel("A"))
    details = {}
    for prefix, mask in masks.items():
        details[prefix] = {
            "visible_px": int(mask.sum()),
            "outside_reference_mask_px": int((mask & ~silhouette).sum()),
            "outside_filled_reference_mask_px": int((mask & ~filled_silhouette).sum()),
            "outside_mask_with_nonzero_reference_rgb_px": int((mask & ~silhouette & np.any(ref > 0, axis=2)).sum()),
        }
    record = {
        "view": name, "fcstd_sha256": id_manifest["fcstd_sha256"],
        "camera_sha256": id_manifest["camera_config_sha256"], "reference_sha256": digest(ref_path),
        "render_sha256": render_entry["sha256"], "object_id_sha256": id_entry["sha256"],
        "comparison_report_sha256": digest(report_path), "crop_xyxy": bounds,
        "silhouette_iou": row["silhouette_iou"], "visible_cad_groups": details,
    }
    return record, [im.crop(bounds) for im in (reference, cad_rgb, Image.fromarray(marked))]


def main():
    parser = argparse.ArgumentParser()
    for name in ("baseline", "still-ids", "video-ids", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    views = [
        ("stills", "still-04", args.still_ids),
        ("stills", "still-05", args.still_ids),
        ("stills", "still-06", args.still_ids),
        ("video", "video-02", args.video_ids),
        ("video", "video-03", args.video_ids),
        ("video", "video-06", args.video_ids),
    ]
    panel_width, panel_height = 380, 220
    board = Image.new("RGB", (3 * panel_width, len(views) * panel_height + 36), (18, 20, 23))
    draw = ImageDraw.Draw(board)
    labels = ("Reference", "Saved CAD", "CAD: red pan, cyan loops, yellow harness")
    for col, label in enumerate(labels):
        draw.text((col * panel_width + 8, 10), label, fill="white")
    records = []
    for index, (group, name, ids) in enumerate(views):
        record, images = inspect_view(args.baseline, group, name, ids)
        records.append(record)
        top = 36 + index * panel_height
        draw.text((8, top), name, fill="white")
        for col, image in enumerate(images):
            image.thumbnail((panel_width - 8, panel_height - 22), Image.Resampling.LANCZOS)
            board.paste(image, (col * panel_width + (panel_width - image.width) // 2, top + 16))
    board.save(args.output / "underside-views.png")
    report = {
        "method": "Baseline reference segmentation and fixed cameras, with visible CAD mesh attribution.",
        "limitations": [
            "The reference mask can omit dark surfaces.",
            "The still-06 source is a wireframe.",
            "The object ID pass is opaque, with approximate attribution at antialiased edges.",
        ],
        "views": records,
    }
    (args.output / "underside-views.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
