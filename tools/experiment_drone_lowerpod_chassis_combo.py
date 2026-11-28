"""Combine the screened LowerPod and BottomChassis appearance scales."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_errors(shape):
    try:
        shape.check(True)
    except ValueError as exc:
        return sorted(
            line.strip() for line in str(exc).splitlines()
            if line.startswith("Error in ")
        )
    return []


def scale_lower_pod(shape, scale):
    frame = shape.Placement
    local = shape.copy()
    local.Placement = App.Placement()
    matrix = App.Matrix()
    matrix.A11 = scale
    matrix.A22 = scale
    candidate = local.transformGeometry(matrix)
    candidate.Placement = frame.multiply(candidate.Placement)
    return candidate


def scale_chassis(shape, scale):
    bounds = shape.BoundBox
    matrix = App.Matrix()
    matrix.A22 = scale
    matrix.A24 = bounds.YMin * (1 - scale)
    return shape.transformGeometry(matrix)


def preserve_unmodified_breps(base: Path, model: Path, changed: set[str]) -> None:
    restored = model.with_suffix(".restored.FCStd")
    with ZipFile(base) as source, ZipFile(model) as candidate, ZipFile(
        restored, "w", ZIP_DEFLATED
    ) as output:
        for name in candidate.namelist():
            owner = name.split(".Shape.")[0]
            if (name.endswith(".brp") or ".Shape.Map." in name) and owner not in changed:
                output.writestr(name, source.read(name))
            else:
                output.writestr(name, candidate.read(name))
    restored.replace(model)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lower-pod-scale", type=float, default=0.995)
    parser.add_argument("--chassis-scale", type=float, default=0.995)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be empty")

    mesh = json.loads(args.mesh.read_text(encoding="utf-8"))
    baseline_hash = digest(args.base)
    if mesh["fcstd_sha256"] != baseline_hash:
        raise ValueError("mesh and FCStd hashes differ")

    changed = ["LowerPod_1", "LowerPod_001", "BottomChassis"]
    args.output.mkdir(parents=True, exist_ok=True)
    document = App.openDocument(str(args.base.resolve()))
    originals = {}
    try:
        for name in changed:
            obj = document.getObject(name)
            if obj is None or obj.Shape.isNull():
                raise ValueError(f"missing {name}")
            originals[name] = obj.Shape.copy()

        for name in ("LowerPod_1", "LowerPod_001"):
            original = originals[name]
            candidate = scale_lower_pod(original, args.lower_pod_scale)
            if (
                not candidate.isValid()
                or not candidate.isClosed()
                or len(candidate.Solids) != len(original.Solids)
                or check_errors(candidate) != check_errors(original)
            ):
                raise ValueError(f"invalid transformed shell {name}")
            document.getObject(name).Shape = candidate

        original = originals["BottomChassis"]
        candidate = scale_chassis(original, args.chassis_scale)
        if not candidate.isValid() or not candidate.isClosed() or len(candidate.Solids) != 1:
            raise ValueError("invalid transformed BottomChassis")
        document.getObject("BottomChassis").Shape = candidate
        document.recompute()
        model = args.output / "candidate.FCStd"
        document.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(document.Name)

    preserve_unmodified_breps(args.base, model, set(changed))
    saved = App.openDocument(str(model.resolve()))
    try:
        invalid = []
        closed = 0
        records = []
        for obj in saved.Objects:
            if not hasattr(obj, "Shape") or obj.Shape.isNull():
                continue
            if not obj.Shape.isValid():
                invalid.append(obj.Name)
            if obj.Shape.isClosed():
                closed += 1
        for name in changed:
            shape = saved.getObject(name).Shape
            records.append(
                {
                    "name": name,
                    "valid": shape.isValid(),
                    "closed": shape.isClosed(),
                    "solids": len(shape.Solids),
                    "errors": check_errors(shape),
                }
            )
            item = next(item for item in mesh["objects"] if item["name"] == name)
            vertices, faces = shape.tessellate(0.12)
            item["vertices"] = [[vertex.x, vertex.y, vertex.z] for vertex in vertices]
            item["faces"] = faces
        mesh["fcstd_sha256"] = digest(model)
        (args.output / "meshes.json").write_text(
            json.dumps(mesh, separators=(",", ":")), encoding="utf-8"
        )
        contacts = []
        chassis = saved.getObject("BottomChassis").Shape
        for name in (
            "MainEnclosureShell",
            "ClosedBellyPan",
            "LowerPod_1",
            "LowerPod_001",
            "UnderbodyLoop0",
            "UnderbodyLoop1",
        ):
            other = saved.getObject(name).Shape
            contacts.append(
                {
                    "objects": ["BottomChassis", name],
                    "gap_mm": chassis.distToShape(other)[0],
                    "overlap_mm3": chassis.common(other).Volume,
                }
            )
        report = {
            "revision": args.revision,
            "baseline_fcstd_sha256": baseline_hash,
            "fcstd_sha256": digest(model),
            "lower_pod_scale": args.lower_pod_scale,
            "chassis_scale": args.chassis_scale,
            "changed_objects": changed,
            "visible_features": 696,
            "all_shapes_valid": not invalid,
            "all_shapes_closed": closed == 698,
            "invalid_objects": invalid,
            "records": records,
            "contacts": contacts,
            "status": "saved combo candidate; fixed-camera screening pending",
        }
        (args.output / "candidate-check.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        App.closeDocument(saved.Name)


if __name__ == "__main__":
    main()
