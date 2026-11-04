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
    parser.add_argument("--expected-step-solids", type=int, default=1010,
                        help="1010 for legacy all-shape export; 1008 for visible-only export")
    parser.add_argument("--verify-mesh-objects", nargs="*", default=[],
                        help="independently retessellate named changed objects after saved readback")
    args = parser.parse_args()

    candidate, _, invalid = read_signatures(args.model)
    baseline, _, baseline_invalid = read_signatures(args.baseline)
    mesh = json.loads(args.mesh.read_text(encoding="utf-8"))
    visible = [item["name"] for item in mesh["objects"]]
    mesh_checks = {}
    visible_volume = sum(candidate[name]['volume_mm3'] for name in visible)
    visible_solids = sum(candidate[name]['solids'] for name in visible)
    if args.verify_mesh_objects:
        doc = App.openDocument(str(args.model.resolve()))
        try:
            by_name = {item['name']: item for item in mesh['objects']}
            for name in args.verify_mesh_objects:
                vertices, faces = doc.getObject(name).Shape.tessellate(.12)
                mesh_checks[name] = {
                    'vertices_equal_saved_readback': [[v.x, v.y, v.z] for v in vertices] == by_name[name]['vertices'],
                    'faces_equal_saved_readback': [list(f) for f in faces] == by_name[name]['faces'],
                }
        finally:
            App.closeDocument(doc.Name)
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
    step_volume = sum(s.Volume for s in step_shape.Solids)
    volume_error = abs(visible_volume-step_volume)/visible_volume
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
        "expected_step_solids": args.expected_step_solids,
        "visible_fcstd_solids": visible_solids,
        "visible_fcstd_volume_mm3": visible_volume,
        "step_volume_mm3": step_volume,
        "visible_export_relative_volume_error": volume_error,
        "changed_mesh_saved_readback": mesh_checks,
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
            len(step_shape.Solids) != args.expected_step_solids or not step_shape.isValid() or
            not result["step_closed"] or mesh['fcstd_sha256'] != result['fcstd_sha256'] or
            (args.expected_step_solids == visible_solids and volume_error > 1e-6) or
            any(not all(check.values()) for check in mesh_checks.values()) or
            not result["protected_supports_equal"]):
        raise SystemExit("candidate readback checks failed")


if __name__ == "__main__":
    main()
