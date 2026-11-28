"""Screen a local radial scale of the saved LowerPod shell bodies."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def errors(shape):
    try:
        shape.check(True)
    except ValueError as exc:
        return sorted(line.strip() for line in str(exc).splitlines()
                      if line.startswith("Error in "))
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if not 0.95 <= args.scale <= 1.05 or args.scale == 1:
        raise ValueError("scale must be in [0.95, 1.05], excluding 1")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be empty")
    mesh = json.loads(args.mesh.read_text(encoding="utf-8"))
    baseline_hash = sha(args.base)
    if mesh["fcstd_sha256"] != baseline_hash:
        raise ValueError("mesh and FCStd hashes differ")
    changed = ["LowerPod_1", "LowerPod_001"]
    args.output.mkdir(parents=True, exist_ok=True)
    doc = App.openDocument(str(args.base.resolve()))
    originals = {}
    try:
        for name in changed:
            obj = doc.getObject(name)
            if obj is None or obj.Shape.isNull():
                raise ValueError(f"missing {name}")
            original = obj.Shape.copy()
            originals[name] = original
            local = original.copy()
            frame = local.Placement
            local.Placement = App.Placement()
            matrix = App.Matrix()
            matrix.A11 = args.scale
            matrix.A22 = args.scale
            candidate = local.transformGeometry(matrix)
            candidate.Placement = frame.multiply(candidate.Placement)
            if (not candidate.isValid() or not candidate.isClosed()
                    or len(candidate.Solids) != len(original.Solids)
                    or errors(candidate) != errors(original)):
                raise ValueError(f"invalid transformed shell {name}")
            obj.Shape = candidate
        doc.recompute()
        model = args.output / "candidate.FCStd"
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)

    restored = args.output / "candidate.restored.FCStd"
    with ZipFile(args.base) as source, ZipFile(model) as candidate, ZipFile(restored, "w", ZIP_DEFLATED) as out:
        for name in candidate.namelist():
            if (name.endswith(".brp") or ".Shape.Map." in name):
                owner = name.split(".Shape.")[0]
                if owner not in changed:
                    out.writestr(name, source.read(name))
                    continue
            out.writestr(name, candidate.read(name))
    restored.replace(model)

    saved = App.openDocument(str(model.resolve()))
    try:
        records = []
        for name, original in originals.items():
            shape = saved.getObject(name).Shape
            if (not shape.isValid() or not shape.isClosed()
                    or len(shape.Solids) != len(original.Solids)):
                raise ValueError(f"saved readback invalid {name}")
            records.append({"name": name, "baseline_errors": errors(original),
                            "candidate_errors": errors(shape),
                            "baseline_volume_mm3": original.Volume,
                            "candidate_volume_mm3": shape.Volume})
        mesh["fcstd_sha256"] = sha(model)
        for item in mesh["objects"]:
            if item["name"] in changed:
                vertices, faces = saved.getObject(item["name"]).Shape.tessellate(.12)
                item["vertices"] = [[v.x, v.y, v.z] for v in vertices]
                item["faces"] = faces
        (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
        report = {
            "revision": args.revision,
            "status": "saved LowerPod shell candidate; fixed-camera comparison pending",
            "baseline_fcstd_sha256": baseline_hash,
            "fcstd_sha256": sha(model),
            "scale": args.scale,
            "changed_objects": changed,
            "fixed_z_stations": True,
            "records": records,
            "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
            "limitations": ["radial shell transform is an appearance hypothesis",
                            "flat measured screen retained; curved reference screen remains an assumption",
                            "no manufacturing, fit, optical, thermal, electrical, or physical acceptance"],
        }
        (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"fcstd_sha256": sha(model), "changed_objects": changed}))
    finally:
        App.closeDocument(saved.Name)


if __name__ == "__main__":
    main()
