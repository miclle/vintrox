"""Independently read back an underbody-loop candidate FCStd and STEP pair."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part


PROTECTED_PREFIXES = ("SupportShaft", "SupportSocket", "SupportFoot", "CentralSupportSeat")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(shape):
    box = shape.BoundBox
    return {
        "solids": len(shape.Solids),
        "valid": bool(shape.isValid()),
        "closed": all(s.isClosed() for s in shape.Solids),
        "volume_mm3": round(shape.Volume, 6),
        "area_mm2": round(shape.Area, 6),
        "bbox_mm": [round(v, 6) for v in
                    (box.XMin, box.XMax, box.YMin, box.YMax, box.ZMin, box.ZMax)],
    }


def read_signatures(path: Path):
    doc = App.openDocument(str(path))
    try:
        records = {}
        visible = []
        invalid = []
        for obj in doc.Objects:
            if not hasattr(obj, "Shape") or obj.Shape.isNull():
                continue
            record = signature(obj.Shape)
            records[obj.Name] = record
            if not record["valid"] or not record["closed"]:
                invalid.append(obj.Name)
            if obj.Visibility:
                visible.append(obj.Name)
        return records, visible, invalid
    finally:
        App.closeDocument(doc.Name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate, _, invalid = read_signatures(args.model)
    baseline, _, baseline_invalid = read_signatures(args.baseline)
    mesh = json.loads(args.mesh.read_text(encoding="utf-8"))
    visible = [item["name"] for item in mesh["objects"]]
    protected = sorted(name for name in candidate if name.startswith(PROTECTED_PREFIXES))
    protected_comparison = {}
    for name in protected:
        protected_comparison[name] = {
            "candidate": candidate[name],
            "baseline": baseline.get(name),
            "equal": candidate[name] == baseline.get(name),
        }

    step_shape = Part.read(str(args.step))
    step_product = args.step.read_text(encoding="utf-8", errors="replace")
    result = {
        "status": "saved-fcstd-and-step-readback",
        "fcstd_sha256": digest(args.model),
        "step_sha256": digest(args.step),
        "baseline_fcstd_sha256": digest(args.baseline),
        "all_fcstd_shapes_valid": not invalid,
        "all_fcstd_shapes_closed": not invalid,
        "invalid_fcstd_objects": invalid,
        "baseline_invalid_objects": baseline_invalid,
        "saved_objects_total": len(candidate),
        "visible_features": len(visible),
        "visible_object_names": visible,
        "step_solids": len(step_shape.Solids),
        "step_valid": bool(step_shape.isValid()),
        "step_closed": all(s.isClosed() for s in step_shape.Solids),
        "step_product_names": step_product.count("PRODUCT("),
        "protected_supports": protected_comparison,
        "protected_supports_equal": all(item["equal"] for item in protected_comparison.values()),
        "visibility_basis": "candidate meshes.json saved visibility contract; headless FreeCAD visibility flags are not used",
    }
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ("fcstd_sha256", "step_sha256", "saved_objects_total", "visible_features",
                       "step_solids", "step_valid", "protected_supports_equal")}))

    if (invalid or baseline_invalid or len(visible) != 696 or len(candidate) != 698 or
            len(step_shape.Solids) != 1010 or not step_shape.isValid() or
            not result["protected_supports_equal"]):
        raise SystemExit("candidate readback checks failed")


if __name__ == "__main__":
    main()
