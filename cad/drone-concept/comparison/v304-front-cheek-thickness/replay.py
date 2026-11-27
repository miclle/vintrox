"""Contract the thickness of the front cheek skins around their inner faces."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "mesh", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--scale", type=float, choices=(.75, .5), required=True)
    args = parser.parse_args()
    mesh = json.loads(args.mesh.read_text())
    baseline = digest(args.base)
    if mesh["fcstd_sha256"] != baseline:
        raise ValueError("Mesh and model inputs differ")
    args.output.mkdir(parents=True)
    model = args.output / "candidate.FCStd"
    original = App.openDocument(str(args.base.resolve()))
    replacements, checks = {}, []
    try:
        for side in ("Left", "Right"):
            name = "FrontCheek" + side
            shape = original.getObject(name).Shape
            bounds = shape.optimalBoundingBox(False, False)
            inner_x = bounds.XMax if side == "Left" else bounds.XMin
            matrix = App.Matrix()
            matrix.A11 = args.scale
            matrix.A14 = inner_x * (1 - args.scale)
            replacements[name + ".Shape.brp"] = shape.transformGeometry(matrix).exportBrepToString()

        with ZipFile(args.base) as source, ZipFile(model, "w", ZIP_DEFLATED) as output:
            if not replacements.keys() <= set(source.namelist()):
                raise ValueError("Missing front cheek archive entries")
            for name in source.namelist():
                output.writestr(name, replacements[name] if name in replacements else source.read(name))

        saved = App.openDocument(str(model.resolve()))
        try:
            for side in ("Left", "Right"):
                name = "FrontCheek" + side
                before = original.getObject(name).Shape
                after = saved.getObject(name).Shape
                if (not after.isValid() or not after.isClosed() or len(after.Solids) != 1
                        or advanced_errors(after) != advanced_errors(before)):
                    raise ValueError(f"Invalid saved solid: {name}")
                contacts = []
                for prefix in ("FrontCheekBridge", "CheekUtilityLabel", "VentBacking",
                               "CheekDial", "SideFrontSpine", "HoodShoulderPlate"):
                    obj = saved.getObject(prefix + side)
                    if obj is None:
                        continue
                    other = obj.Shape
                    prior_gap = before.distToShape(other)[0]
                    gap = after.distToShape(other)[0]
                    contacts.append({"objects": [name, obj.Name], "before_gap_mm": prior_gap,
                                     "gap_mm": gap, "contact_lost": prior_gap <= .01 < gap})
                bridge = saved.getObject("FrontCheekBridge" + side).Shape
                overlap = after.common(bridge).Volume
                checks.append({"name": name, "bridge_overlap_mm3": overlap, "contacts": contacts})
                points, faces = after.tessellate(.12)
                item = next(item for item in mesh["objects"] if item["name"] == name)
                item.update(vertices=[list(point) for point in points], faces=faces)
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(original.Name)

    mesh["fcstd_sha256"] = digest(model)
    report = {"fcstd_sha256": mesh["fcstd_sha256"], "baseline_fcstd_sha256": baseline,
              "thickness_scale": args.scale, "changed_archive_members": sorted(replacements),
              "parts": checks}
    (args.output / "geometry.json").write_text(json.dumps(report, indent=2) + "\n")
    if any(part["bridge_overlap_mm3"] <= .01 or any(row["contact_lost"] for row in part["contacts"])
           for part in checks):
        raise ValueError("An existing cheek contact was lost")
    (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))


if __name__ == "__main__":
    main()
