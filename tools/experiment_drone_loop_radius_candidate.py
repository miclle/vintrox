"""Build a small real-CAD underbody-loop radius candidate from formal v61.

Only the two decorative loop solids change. Their saved centerline, endpoints,
support geometry, and all other visible parts remain bound to the formal model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Import
from drone_concept import tube


PATH = [
    (72.8, 57), (72.79, 43.28), (72.66, 28.78), (79.02, 14.23),
    (90.8, 4.28), (105.26, 4.96), (117.52, 9.58), (124.96, 19.42),
    (127.11, 33.41), (126.62, 47.15), (126.6, 57),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(obj):
    vertices, faces = obj.Shape.tessellate(.12)
    view = getattr(obj, "ViewObject", None)
    return {
        "name": obj.Name,
        "vertices": [[v.x, v.y, v.z] for v in vertices],
        "faces": faces,
        "color": list(view.ShapeColor[:3]) if view is not None else [.6, .5, .25],
        "material": getattr(obj, "RenderMaterial", "paint"),
    }


def sig(shape):
    b = shape.BoundBox
    return {
        "volume_mm3": round(shape.Volume, 6),
        "area_mm2": round(shape.Area, 6),
        "bbox_mm": [round(x, 6) for x in
                    (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)],
        "solids": len(shape.Solids),
        "valid": shape.isValid(),
        "closed": all(s.isClosed() for s in shape.Solids),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--radius", type=float, default=2.8)
    parser.add_argument("--revision", help="candidate revision label; defaults from the radius")
    args = parser.parse_args()
    if args.radius <= 0 or args.radius >= 3.5:
        raise ValueError("candidate radius must be between 0 and the formal 3.5 mm")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be a new empty directory")
    revision = args.revision or f"v{int(round(args.radius * 10)):02d}-underbody-loop-radius{str(args.radius).replace('.', 'p')}"
    args.output.mkdir(parents=True, exist_ok=True)
    base_hash = sha(args.base)
    doc = App.openDocument(str(args.base))
    try:
        before = {n: sig(doc.getObject(n).Shape) for n in ("UnderbodyLoop0", "UnderbodyLoop1")}
        changed = []
        for index, x in enumerate((-44.5, 44.5)):
            name = f"UnderbodyLoop{index}"
            shape = tube([(x, y, z) for y, z in PATH], args.radius)
            shape.check(True)
            if not shape.isValid() or len(shape.Solids) != 1 or not shape.Solids[0].isClosed():
                raise ValueError(f"invalid loop candidate: {name}")
            doc.getObject(name).Shape = shape
            changed.append(name)
        doc.recompute()
        candidate = args.output / "candidate.FCStd"
        doc.saveAs(str(candidate))
        # Headless FreeCAD restores GUI visibility as false for this archive;
        # the formal render binding includes every non-null saved shape.
        visible = [o for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull()]
        step = (args.output / "candidate.step").resolve()
        Import.export(visible, str(args.output / "candidate.step"))
        if not step.exists():
            raise RuntimeError("STEP export did not create candidate.step")
        mesh = {"fcstd_sha256": sha(candidate), "objects": [record(o) for o in visible]}
        (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")), encoding="utf-8")
        after = {n: sig(doc.getObject(n).Shape) for n in changed}
        check = {
            "revision": revision,
            "status": "candidate; fixed-camera comparison required",
            "baseline_fcstd_sha256": base_hash,
            "fcstd_sha256": sha(candidate),
            "step_sha256": sha(step),
            "changed_objects": changed,
            "radius_before_mm": 3.5,
            "radius_after_mm": args.radius,
            "centerline_paths_mm": {"left": [[-44.5, y, z] for y, z in PATH],
                                     "right": [[44.5, y, z] for y, z in PATH]},
            "before": before,
            "after": after,
            "measured_screen_preserved": True,
            "registration": "fixed calibrated camera projection only; no image warp, stretch, or per-part alignment",
            "limitations": [
                "decorative cable thickness is an appearance assumption, not an electrical specification",
                "black cable/background segmentation remains ambiguous",
                "no manufacturing, fit, thermal, electrical, or physical acceptance",
            ],
        }
        (args.output / "candidate-check.json").write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    finally:
        App.closeDocument(doc.Name)
    print(json.dumps({"candidate": str(candidate), "fcstd_sha256": sha(candidate),
                      "step_sha256": sha((args.output / "candidate.step").resolve())}))


if __name__ == "__main__":
    main()
