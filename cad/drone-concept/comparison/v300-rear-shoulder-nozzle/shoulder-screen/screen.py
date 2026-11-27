"""Screen a mirrored transverse contraction of the saved rear shoulder solids."""
import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest

parser = argparse.ArgumentParser(description=__doc__)
for name in ("base", "mesh", "output"):
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--scale", type=float, choices=(.88, .94, 1.06), required=True)
args = parser.parse_args()
model_hash = digest(args.base)
mesh = json.loads(args.mesh.read_text())
if mesh["fcstd_sha256"] != model_hash:
    raise ValueError("The mesh must match the saved FCStd")

args.output.mkdir(parents=True)
model = args.output / "candidate.FCStd"
original = App.openDocument(str(args.base.resolve()))
changes = {}
joints = []
checks = []
try:
    for sign, side in ((-1, "Left"), (1, "Right")):
        name = "RearArmourCheek" + side
        shape = original.getObject(name).Shape
        matrix = App.Matrix()
        matrix.A11 = args.scale
        matrix.A14 = sign * 89 * (1 - args.scale)
        changes[name + ".Shape.brp"] = shape.transformGeometry(matrix).exportBrepToString()

    with ZipFile(args.base) as source, ZipFile(model, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            target.writestr(name, changes[name] if name in changes else source.read(name))

    saved = App.openDocument(str(model.resolve()))
    try:
        for side in ("Left", "Right"):
            name = "RearArmourCheek" + side
            before = original.getObject(name).Shape
            after = saved.getObject(name).Shape
            errors = advanced_errors(after)
            valid = after.isValid() and after.isClosed() and len(after.Solids) == 1
            checks.append({"name": name, "valid_closed_solid": valid, "advanced_errors": errors})
            for neighbor in ("RearStructuralFrame", "RearServicePanel", "RearLowerSlope",
                             "SideClosure" + side, "SideGuard" + side, "SideMechanicalBacking" + side):
                part = original.getObject(neighbor).Shape
                old_gap = before.distToShape(part)[0]
                new_gap = after.distToShape(part)[0]
                joints.append({"objects": [name, neighbor], "baseline_gap_mm": old_gap,
                               "gap_mm": new_gap, "regressed": new_gap > max(.01, old_gap + 1e-5)})
            item = next(entry for entry in mesh["objects"] if entry["name"] == name)
            points, faces = after.tessellate(.12)
            item.update(vertices=[list(point) for point in points], faces=faces)
    finally:
        App.closeDocument(saved.Name)
finally:
    App.closeDocument(original.Name)
mesh["fcstd_sha256"] = digest(model)
report = {"baseline_fcstd_sha256": model_hash, "fcstd_sha256": mesh["fcstd_sha256"],
          "scale": args.scale, "fixed_inner_x_mm": [-89, 89],
          "changed_archive_members": sorted(changes), "parts": checks, "contacts": joints}
(args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
if any(not check["valid_closed_solid"] or check["advanced_errors"] for check in checks):
    raise ValueError("Saved shoulder geometry check failed")
if any(joint["regressed"] for joint in joints):
    raise ValueError("Saved shoulder contact check failed")
(args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
