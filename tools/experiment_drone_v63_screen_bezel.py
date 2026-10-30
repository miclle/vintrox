"""Build and audit the v63 screen-surround appearance candidate.

The measured flat panel and active area remain bound to the saved model.  Only
the surrounding CAD solids are changed; fixed-camera rendering is performed by
the existing render/compare tools after this script writes a mesh binding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Import
import Part


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box(w, depth, h, pos):
    return Part.makeBox(w, depth, h, App.Vector(*pos))


def rounded_plate(w, h, depth, pos, radius):
    shape = box(w, depth, h, pos)
    edges = [e for e in shape.Edges if e.BoundBox.YLength > depth - .01]
    return shape.makeFillet(radius, edges)


def rounded_frame(w, h, depth, border, pos, radius):
    x, y, z = pos
    outer = rounded_plate(w, h, depth, pos, radius)
    inner = rounded_plate(w - 2 * border, h - 2 * border, depth + 2,
                         (x + border, y - 1, z + border),
                         max(1, radius - border / 2))
    return outer.cut(inner)


def shape_signature(shape):
    b = shape.BoundBox
    return {
        "volume_mm3": round(shape.Volume, 6),
        "area_mm2": round(shape.Area, 6),
        "bbox_mm": [round(v, 6) for v in
                    (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)],
        "solids": len(shape.Solids),
        "valid": shape.isValid(),
    }


def mesh_record(obj):
    vertices, faces = obj.Shape.tessellate(.12)
    view = getattr(obj, "ViewObject", None)
    color = list(view.ShapeColor[:3]) if view is not None else [.6, .5, .25]
    return {
        "name": obj.Name,
        "vertices": [[v.x, v.y, v.z] for v in vertices],
        "faces": faces,
        "color": color,
        "material": getattr(obj, "RenderMaterial", "paint"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be a new empty directory")
    args.output.mkdir(parents=True)

    base_hash = digest(args.base)
    doc = App.openDocument(str(args.base))
    try:
        names = ["ScreenBezel", "BezelLip"]
        before = {name: shape_signature(doc.getObject(name).Shape) for name in names}
        # Preserve the measured panel and active rectangle.  The candidate
        # trims only the visual surround by 2 mm at each outer side.
        bezel = rounded_plate(216, 168, 11, (-108, -13, 65), 11).cut(
            rounded_plate(202, 152, 13, (-101, -14, 73), 8.5))
        lip = rounded_frame(220, 172, 3, 2, (-110, -15, 63), 12)
        for name, shape in (("ScreenBezel", bezel), ("BezelLip", lip)):
            shape.check(True)
            if not shape.isValid() or len(shape.Solids) != 1:
                raise ValueError(f"invalid candidate shape: {name}")
            doc.getObject(name).Shape = shape
        doc.recompute()

        candidate = args.output / "candidate.FCStd"
        doc.saveAs(str(candidate))
        visible = [o for o in doc.Objects if hasattr(o, "Shape") and
                   o.Visibility and not o.Shape.isNull()]
        Import.export(visible, str(args.output / "candidate.step"))
        mesh = {"fcstd_sha256": digest(candidate), "objects":
                [mesh_record(o) for o in visible]}
        (args.output / "meshes.json").write_text(json.dumps(mesh), encoding="utf-8")
        after = {name: shape_signature(doc.getObject(name).Shape) for name in names}
        report = {
            "revision": "v63-screen-bezel-study",
            "status": "candidate; fixed-camera comparison required",
            "baseline_fcstd_sha256": base_hash,
            "fcstd_sha256": digest(candidate),
            "step_sha256": digest(args.output / "candidate.step"),
            "changed_objects": names,
            "measured_screen_preserved": True,
            "screen_objects": {
                name: shape_signature(doc.getObject(name).Shape)
                for name in ["ScreenPanel210x160x2", "ActiveArea200x150"]
            },
            "before": before,
            "after": after,
            "saved_readback": False,
            "registration": "fixed calibrated camera projection only; no image warp, stretch, or per-part alignment",
            "limitations": [
                "appearance study only; flat measured screen retained",
                "reference curved screen and hidden surfaces are not observable",
                "no manufacturing, fit, optical, thermal, or physical acceptance",
            ],
        }
        (args.output / "candidate-check.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
    finally:
        App.closeDocument(doc.Name)

    # Independent saved readback and support preservation.
    saved = App.openDocument(str(candidate))
    base = App.openDocument(str(args.base))
    try:
        checks = {}
        for name in ["ScreenBezel", "BezelLip", "ScreenPanel210x160x2", "ActiveArea200x150"]:
            obj = saved.getObject(name)
            obj.Shape.check(True)
            checks[name] = shape_signature(obj.Shape)
            if not obj.Shape.isValid() or any(not solid.isClosed() for solid in obj.Shape.Solids):
                raise ValueError(f"saved readback failed: {name}")
        protected = [o.Name for o in base.Objects if o.Name.startswith((
            "SupportShaft", "SupportSocket", "SupportFoot", "CentralSupport"))]
        for name in protected:
            a, b = saved.getObject(name).Shape, base.getObject(name).Shape
            if abs(a.common(b).Volume - a.Volume) > 1e-6 or abs(b.common(a).Volume - b.Volume) > 1e-6:
                raise ValueError(f"protected support changed: {name}")
        report_path = args.output / "candidate-check.json"
        report = json.loads(report_path.read_text())
        report["saved_readback"] = True
        report["saved_readback_checks"] = checks
        report["protected_supports"] = protected
        report["protected_supports_unchanged"] = True
        report["source_script_sha256"] = digest(Path(__file__))
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(base.Name)
    print(json.dumps({"candidate": str(candidate), "fcstd_sha256": digest(candidate),
                      "step_sha256": digest(args.output / "candidate.step"),
                      "saved_readback": True}))


if __name__ == "__main__":
    main()
