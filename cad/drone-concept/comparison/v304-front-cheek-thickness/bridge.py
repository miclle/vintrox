"""Taper the rear edge of the front cheeks while retaining the bridge mounting strip."""
import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "mesh", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--inset", type=float, choices=(1.5, 3.0), required=True)
    args = parser.parse_args()
    mesh = json.loads(args.mesh.read_text())
    baseline = digest(args.base)
    if mesh["fcstd_sha256"] != baseline:
        raise ValueError("Mesh and model inputs differ")
    args.output.mkdir(parents=True)
    model = args.output / "candidate.FCStd"
    original = App.openDocument(str(args.base.resolve()))
    replacements = {}
    parts = []
    try:
        for side, sign in (("Left", -1), ("Right", 1)):
            for family in ("FrontCheek", "FrontCheekBridge"):
                name = family + side
                before = original.getObject(name).Shape
                # Let the inner portion of the bridge continue to meet the side spine.
                fixed_x, outer_x = (109.2, 116.8) if family == "FrontCheek" else (108.8, 111.1)
                rear_y = 35.86 if family == "FrontCheek" else 36.86
                points = [App.Vector(sign * x, y, 50) for x, y in (
                    (fixed_x, rear_y), (outer_x, rear_y - args.inset),
                    (124, rear_y - args.inset), (124, 45), (fixed_x, 45),
                )]
                cutter = Part.Face(Part.makePolygon(points + points[:1])).extrude(App.Vector(0, 0, 165))
                after = before.cut(cutter)
                replacements[name + ".Shape.brp"] = after.exportBrepToString()
        with ZipFile(args.base) as source, ZipFile(model, "w", ZIP_DEFLATED) as output:
            if not replacements.keys() <= set(source.namelist()):
                raise ValueError("Missing BRep entries")
            for name in source.namelist():
                output.writestr(name, replacements[name] if name in replacements else source.read(name))
        saved = App.openDocument(str(model.resolve()))
        try:
            for side in ("Left", "Right"):
                cheek = saved.getObject("FrontCheek" + side).Shape
                bridge = saved.getObject("FrontCheekBridge" + side).Shape
                spine = saved.getObject("SideFrontSpine" + side).Shape
                overlap = cheek.common(bridge).Volume
                gap = bridge.distToShape(spine)[0]
                if overlap <= .01 or gap > .01:
                    raise ValueError(f"Detached bridge: {side}")
                parts.append({"side": side, "bridge_overlap_mm3": overlap, "bridge_spine_gap_mm": gap})
            for member in replacements:
                name = member.removesuffix(".Shape.brp")
                old = original.getObject(name).Shape
                shape = saved.getObject(name).Shape
                if (not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1
                        or advanced_errors(shape) != advanced_errors(old)):
                    raise ValueError(f"Invalid shape: {name}")
                vertices, faces = shape.tessellate(.12)
                item = next(row for row in mesh["objects"] if row["name"] == name)
                item.update(vertices=[list(point) for point in vertices], faces=faces)
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(original.Name)
    mesh["fcstd_sha256"] = digest(model)
    check = {"fcstd_sha256": mesh["fcstd_sha256"], "baseline_fcstd_sha256": baseline,
             "inset_mm": args.inset, "changed_archive_members": sorted(replacements), "parts": parts}
    (args.output / "geometry.json").write_text(json.dumps(check, indent=2) + "\n")
    (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))


if __name__ == "__main__":
    main()
