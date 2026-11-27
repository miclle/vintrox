"""Attribute one static-view CAD silhouette difference to saved CAD objects.

The reference image is resized to the calibrated camera resolution with the
same aspect ratio used by the static comparison.  This is a diagnostic only.
It does not alter the primary IoU, omit parts, or register individual objects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from compare_drone_reference import reference_mask


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--comparison-report", type=Path, required=True)
    parser.add_argument("--view", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-image", type=Path)
    args = parser.parse_args()

    manifest = json.loads((args.ids / "object-id-manifest.json").read_text())
    report = json.loads(args.comparison_report.read_text())
    row = next(item for item in report["views"] if item["view"] == args.view)
    id_row = next(item for item in manifest["images"] if item["view"] == args.view)
    id_path = args.ids / id_row["path"]
    if digest(id_path) != id_row["sha256"]:
        raise ValueError("object ID image hash does not match its manifest")

    render = Image.open(args.render).convert("RGBA")
    reference = Image.open(args.reference).convert("RGB")
    original_reference_size = reference.size
    if reference.size != render.size:
        reference = reference.resize(render.size, Image.Resampling.LANCZOS)
    source = np.asarray(reference)
    cad = np.asarray(render)[:, :, 3] > 127
    ref = reference_mask(source)
    excess = cad & ~ref
    enclosed = ndimage.binary_fill_holes(ref) & ~ref
    exterior = excess & ~enclosed
    ids = np.asarray(Image.open(id_path).convert("RGBA"))[:, :, :3]
    objects = manifest["objects"]
    colors = np.asarray([item["rgb"] for item in objects], dtype=np.int32)
    distance = np.sqrt(((ids[:, :, None, :].astype(np.int32) - colors[None, None, :, :]) ** 2).sum(axis=3))
    index = distance.argmin(axis=2)
    assigned = distance.min(axis=2) < 12
    counts = np.bincount(index[exterior & assigned], minlength=len(objects))
    top = [
        {"name": objects[i]["name"], "pixels": int(counts[i])}
        for i in np.argsort(-counts)
        if counts[i]
    ][:30]

    diagnostic = (source.astype(np.float32) * 0.35).astype(np.uint8)
    diagnostic[excess & enclosed] = [255, 170, 0]
    diagnostic[exterior] = [255, 50, 100]
    diagnostic[ref & ~cad] = [0, 220, 255]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image_path = args.diagnostic_image or args.output.with_name(args.output.stem + "-diagnostic.png")
    image_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(diagnostic).save(image_path)
    result = {
        "view": args.view,
        "fcstd_sha256": manifest["fcstd_sha256"],
        "camera_config_sha256": manifest["camera_config_sha256"],
        "object_id_manifest_sha256": digest(args.ids / "object-id-manifest.json"),
        "render_sha256": digest(args.render),
        "reference_sha256": digest(args.reference),
        "comparison_report_sha256": digest(args.comparison_report),
        "comparison_iou": row["silhouette_iou"],
        "reference_size": list(original_reference_size),
        "comparison_size": list(render.size),
        "reference_resized_with_aspect_ratio": original_reference_size != render.size,
        "excess_pixels": int(excess.sum()),
        "excess_in_enclosed_dark_regions_px": int((excess & enclosed).sum()),
        "excess_outside_filled_reference_px": int(exterior.sum()),
        "top_exterior_objects": top,
        "diagnostic_image": image_path.name,
        "method": "saved-CAD opaque object IDs and fixed-camera binary silhouette partition",
        "limitations": [
            "static reference camera fit and source image interpretation remain uncertain",
            "enclosed dark regions can represent material or genuine apertures",
            "ID attribution is approximate at antialiased edges and occlusions",
            "rankings identify inspection targets and do not prove geometry correctness",
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"view": args.view, "top_exterior_objects": top[:12]}, indent=2))


if __name__ == "__main__":
    main()
