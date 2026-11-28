"""Build a fixed-camera front-brow contraction candidate from saved CAD.

The default transforms the two front brow solids about model X=0. An optional
depth scaling transforms the complete brow assembly about its rear plane.
The liner options reduce the depth or height of the saved inner liner.
The measured flat screen, active area, four supports, side controls, grilles,
external barrels, and all other saved BRep members remain bound to the supplied
baseline.  This is an appearance candidate; it does not claim physical fit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import Import

from experiment_drone_petal_axial import advanced_errors


CHANGED = ("ProjectingBrow", "BrowUnderside")
PROTECTED_PREFIXES = ("SupportShaft", "SupportSocket", "SupportFoot", "CentralSupportSeat")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(shape):
    box = shape.BoundBox
    return {
        "volume_mm3": round(shape.Volume, 6),
        "area_mm2": round(shape.Area, 6),
        "bbox_mm": [round(v, 6) for v in
                    (box.XMin, box.XMax, box.YMin, box.YMax, box.ZMin, box.ZMax)],
        "solids": len(shape.Solids),
        "valid": bool(shape.isValid()),
        "closed": all(s.isClosed() for s in shape.Solids),
    }


def symmetric_difference(first, second):
    return abs(first.cut(second).Volume) + abs(second.cut(first).Volume)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--base-mesh", type=Path, required=True)
    parser.add_argument("--appearance-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", type=float, required=True,
                        help="X scale about model centre, e.g. 0.985")
    depth = parser.add_mutually_exclusive_group()
    depth.add_argument("--depth-scale", type=float, default=1.0,
                        help="Y scale of complete brow assembly about its rear plane")
    depth.add_argument("--liner-setback", type=float, default=0.0,
                       help="Move the liner front edge rearward by this many mm")
    depth.add_argument("--liner-height-scale", type=float, default=1.0,
                       help="Shorten the liner legs about the top of the saved liner")
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if not 0.95 <= args.scale <= 1.05 or args.scale == 1 or not 0.85 <= args.depth_scale <= 1.1:
        raise ValueError("X scale must be in [0.95, 1.05], excluding 1, depth scale in [0.85, 1.1]")
    if not 0 <= args.liner_setback <= 10 or (args.liner_setback and args.scale != 1):
        parser.error("liner setback must be between 0 and 10 mm with --scale 1")
    if not 0.8 <= args.liner_height_scale <= 1 or (
            args.liner_height_scale != 1 and args.scale != 1):
        parser.error("liner height scale must be in [0.8, 1] with --scale 1")
    if args.scale == args.depth_scale == args.liner_height_scale == 1 and not args.liner_setback:
        raise ValueError("at least one scale must change")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be a new empty directory")

    mesh = json.loads(args.base_mesh.read_text(encoding="utf-8"))
    base_hash = sha(args.base)
    if mesh["fcstd_sha256"] != base_hash:
        raise ValueError("base mesh is not bound to the saved base FCStd")
    args.output.mkdir(parents=True, exist_ok=True)

    doc = App.openDocument(str(args.base.resolve()))
    before = {}
    try:
        objects = {o.Name: o for o in doc.Objects
                   if hasattr(o, "Shape") and not o.Shape.isNull()}
        before = {name: signature(objects[name].Shape) for name in objects}
        changed = set(CHANGED)
        if args.depth_scale != 1:
            prefixes = ("HoodShoulder", "HoodTopInset", "HoodMark")
            changed.update(n for n in objects if n == "HoodEdge" or n.startswith(prefixes))
        changed = sorted(changed)
        rear_y = objects["ProjectingBrow"].Shape.optimalBoundingBox(False, False).YMax
        matrix = App.Matrix()
        matrix.A11 = args.scale
        matrix.A22 = args.depth_scale
        matrix.A24 = rear_y * (1 - args.depth_scale)
        liner_checks = {}
        liner_only = args.liner_setback or args.liner_height_scale != 1
        if liner_only:
            changed = ["BrowUnderside"]
        if args.liner_setback:
            liner = objects["BrowUnderside"].Shape
            # The saved liner was sheared by y -= .4*z. Keep its rear
            # mounting section fixed in the unsheared depth coordinate.
            unshear = App.Matrix()
            unshear.A23 = .4
            bounds = liner.transformGeometry(unshear).optimalBoundingBox(False, False)
            matrix.A22 = 1 - args.liner_setback / bounds.YLength
            matrix.A23 = .4 * (matrix.A22 - 1)
            matrix.A24 = bounds.YMax * (1 - matrix.A22)
        if args.liner_height_scale != 1:
            liner = objects["BrowUnderside"].Shape
            top_z = liner.optimalBoundingBox(False, False).ZMax
            matrix.A33 = args.liner_height_scale
            matrix.A34 = top_z * (1 - matrix.A33)
            # Keep y + 0.4*z fixed while raising the two lower ends.
            matrix.A23 = .4 * (1 - matrix.A33)
            matrix.A24 = -.4 * matrix.A34
        for name in changed:
            source = objects[name].Shape.copy()
            transformed = source.transformGeometry(matrix)
            if (not transformed.isValid() or not transformed.Solids or
                    not all(s.isClosed() for s in transformed.Solids)):
                raise ValueError(f"invalid transformed solid: {name}")
            if liner_only:
                joint = objects["ProjectingBrow"].Shape
                liner_checks = {
                    "baseline_advanced_errors": advanced_errors(source),
                    "candidate_advanced_errors": advanced_errors(transformed),
                    "baseline_brow_gap_mm": source.distToShape(joint)[0],
                    "candidate_brow_gap_mm": transformed.distToShape(joint)[0],
                }
                if args.liner_setback:
                    liner_checks["fixed_rear_y_plus_point4_z_mm"] = bounds.YMax
                else:
                    liner_checks["fixed_top_z_mm"] = top_z
            objects[name].Shape = transformed
        doc.recompute()
        model = args.output / "candidate.FCStd"
        doc.saveAs(str(model.resolve()))
        visible = [item["name"] for item in mesh["objects"]]
        Import.export([doc.getObject(name) for name in visible],
                      str((args.output / "candidate.step").resolve()))
    finally:
        App.closeDocument(doc.Name)

    # Headless FreeCAD writes fresh GUI data. Restore the known saved appearance
    # while retaining candidate BRep bytes and every unchanged base BRep member.
    with (zipfile.ZipFile(args.base) as base_zip,
          zipfile.ZipFile(args.appearance_source) as appearance_zip,
          zipfile.ZipFile(model) as saved_zip):
        payloads = {name: saved_zip.read(name) for name in saved_zip.namelist()}
        gui_names = [name for name in appearance_zip.namelist()
                     if name == "GuiDocument.xml" or
                     name.startswith(("ShapeAppearance", "LineColorArray", "PointColorArray"))]
        if "GuiDocument.xml" not in gui_names:
            raise ValueError("appearance source lacks GuiDocument.xml")
        preserved_members = [name for name in base_zip.namelist()
                             if (name.endswith(".brp") or ".Shape.Map." in name)
                             and name.split(".Shape.")[0] not in changed]
        for name in preserved_members:
            payloads[name] = base_zip.read(name)
        geometry_hashes = {name: hashlib.sha256(data).hexdigest()
                           for name, data in payloads.items() if name not in gui_names}
        for name in gui_names:
            payloads[name] = appearance_zip.read(name)
    with zipfile.ZipFile(model, "w", compression=zipfile.ZIP_DEFLATED) as saved_zip:
        for name, data in payloads.items():
            saved_zip.writestr(name, data)
    with zipfile.ZipFile(model) as check_zip:
        for name, expected in geometry_hashes.items():
            if hashlib.sha256(check_zip.read(name)).hexdigest() != expected:
                raise ValueError(f"geometry changed during GUI restore: {name}")

    saved = App.openDocument(str(model.resolve()))
    base = App.openDocument(str(args.base.resolve()))
    try:
        checks = {}
        for name in changed:
            shape = saved.getObject(name).Shape
            checks[name] = signature(shape)
            if not shape.isValid() or not shape.Solids or not all(s.isClosed() for s in shape.Solids):
                raise ValueError(f"saved readback failed: {name}")
        preserved = []
        for name, expected in before.items():
            if name in changed:
                continue
            actual = signature(saved.getObject(name).Shape)
            if actual != expected:
                raise ValueError(f"unintended saved shape change: {name}")
            preserved.append(name)
        support_checks = []
        for obj in base.Objects:
            if not obj.Name.startswith(PROTECTED_PREFIXES):
                continue
            delta = symmetric_difference(saved.getObject(obj.Name).Shape, obj.Shape)
            if delta > 1e-6:
                raise ValueError(f"protected support changed: {obj.Name}")
            support_checks.append({"name": obj.Name, "symmetric_difference_mm3": delta})
        for item in mesh["objects"]:
            if item["name"] in changed:
                vertices, faces = saved.getObject(item["name"]).Shape.tessellate(.12)
                item["vertices"] = [[v.x, v.y, v.z] for v in vertices]
                item["faces"] = faces
        # Export after final archive restoration and saved readback, so STEP
        # describes exactly the same visible geometry as the bound meshes.
        Import.export([saved.getObject(item["name"]) for item in mesh["objects"]],
                      str((args.output / "candidate.step").resolve()))
        mesh["fcstd_sha256"] = sha(model)
        (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
        report = {
            "revision": args.revision,
            "status": "saved CAD candidate; fixed-camera comparison required",
            "baseline_fcstd_sha256": base_hash,
            "fcstd_sha256": sha(model),
            "step_sha256": sha(args.output / "candidate.step"),
            "source_script_sha256": sha(Path(globals().get("__file__", "tools/experiment_drone_front_brow_contract.py"))),
            "changed_objects": list(changed),
            "x_scale_about_model_center": args.scale,
            "depth_scale": args.depth_scale,
            "depth_pivot_y_mm": rear_y,
            "before": {name: before[name] for name in changed},
            "after": checks,
            "preserved_shape_count": len(preserved),
            "protected_supports": support_checks,
            "screen_objects": {
                name: signature(saved.getObject(name).Shape)
                for name in ("ScreenPanel210x160x2", "ActiveArea200x150")
            },
            "screen_geometry_preserved": all(
                signature(saved.getObject(name).Shape) == before[name]
                for name in ("ScreenPanel210x160x2", "ActiveArea200x150")),
            "gui_members_copied_from_appearance_source": len(gui_names),
            "unchanged_brep_members_restored": len(preserved_members),
            "geometry_unchanged_during_gui_restore": True,
            "mesh_objects": len(mesh["objects"]),
            "distinct_rgb_triples": len({tuple(item["color"]) for item in mesh["objects"]}),
            "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
            "limitations": [
                "front-brow scale is an image-derived appearance hypothesis",
                "measured flat screen retained; curved reference screen remains an appearance assumption",
                "no manufacturing, fit, optical, thermal, electrical, or physical acceptance",
            ],
        }
        if args.liner_setback:
            report.update(liner_setback_mm=args.liner_setback, liner_checks=liner_checks)
        if args.liner_height_scale != 1:
            report.update(liner_height_scale=args.liner_height_scale, liner_checks=liner_checks)
        (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({key: report[key] for key in
                          ("fcstd_sha256", "step_sha256", "mesh_objects",
                           "distinct_rgb_triples", "screen_geometry_preserved")}))
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(base.Name)


if __name__ == "__main__":
    main()
