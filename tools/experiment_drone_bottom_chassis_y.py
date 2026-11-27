"""Screen small Y-length changes to the saved BottomChassis solid."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Import


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", type=float, required=True)
    args = parser.parse_args()
    if not 0.95 <= args.scale <= 1.05:
        raise ValueError("Use a small BottomChassis Y scale")
    args.output = args.output.resolve()
    args.base = args.base.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    base_hash = hashlib.sha256(args.base.read_bytes()).hexdigest()
    doc = App.openDocument(str(args.base))
    try:
        source = doc.getObject("BottomChassis").Shape
        bounds = source.BoundBox
        matrix = App.Matrix()
        matrix.A22 = args.scale
        matrix.A24 = bounds.YMin * (1 - args.scale)
        candidate = source.transformGeometry(matrix)
        candidate.check(True)
        if not candidate.isValid() or not candidate.isClosed() or len(candidate.Solids) != 1:
            raise ValueError("Invalid transformed BottomChassis")
        doc.getObject("BottomChassis").Shape = candidate
        doc.recompute()
        model = args.output / "candidate.FCStd"
        doc.saveAs(str(model))
    finally:
        App.closeDocument(doc.Name)
    doc = App.openDocument(str(model))
    try:
        visible = [obj for obj in doc.Objects if hasattr(obj, "Shape") and not obj.Shape.isNull()]
        Import.export(visible, str((args.output / "candidate.step").resolve()))
        report = {
            "revision": args.output.name,
            "baseline_fcstd_sha256": base_hash,
            "fcstd_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
            "step_sha256": hashlib.sha256((args.output / "candidate.step").read_bytes()).hexdigest(),
            "changed_objects": ["BottomChassis"],
            "y_scale": args.scale,
            "fixed_y_min_mm": bounds.YMin,
            "visible_features": len(visible),
            "status": "saved candidate; fixed-camera screening pending",
        }
        (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
