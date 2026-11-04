"""Build a saved-CAD screen-surround expansion from a bound candidate baseline.

Only ScreenBezel and BezelLip change. Other tessellations and saved GUI display
properties come directly from the baseline, including the measured flat screen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import Import

from experiment_drone_v63_screen_bezel import rounded_frame, rounded_plate, shape_signature


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--base-mesh", type=Path, required=True)
    parser.add_argument("--appearance-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expansion", type=float, required=True, help="outer expansion per side in mm")
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if not 0 < args.expansion <= 5:
        raise ValueError("expansion must be in (0, 5] mm per side")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be a new empty directory")
    mesh = json.loads(args.base_mesh.read_text())
    baseline_hash = sha(args.base)
    if mesh["fcstd_sha256"] != baseline_hash:
        raise ValueError("baseline mesh is not bound to the saved FCStd")
    args.output.mkdir(parents=True, exist_ok=True)
    changed = {"ScreenBezel", "BezelLip"}
    e = args.expansion
    doc = App.openDocument(str(args.base.resolve()))
    try:
        shapes = {o.Name: o.Shape.copy() for o in doc.Objects
                  if hasattr(o, "Shape") and not o.Shape.isNull()}
        before = {n: shape_signature(s) for n, s in shapes.items()}
        bezel = rounded_plate(220+2*e, 172+2*e, 11, (-110-e, -13, 63-e), 12).cut(
            rounded_plate(202, 152, 13, (-101, -14, 74), 8.5))
        lip = rounded_frame(224+2*e, 176+2*e, 3, 2, (-112-e, -15, 61-e), 13)
        lip = lip.makeFillet(.45, [edge for edge in lip.Edges if edge.BoundBox.YLength < .01])
        for name, shape in (("ScreenBezel", bezel), ("BezelLip", lip)):
            shape.check(True)
            if not shape.isValid() or len(shape.Solids) != 1 or not shape.Solids[0].isClosed():
                raise ValueError(f"invalid candidate: {name}")
            doc.getObject(name).Shape = shape
        doc.recompute()
        preserved = [n for n in shapes if n not in changed]
        for name in preserved:
            if shape_signature(doc.getObject(name).Shape) != before[name]:
                raise ValueError(f"unintended shape change: {name}")
        model = args.output / "candidate.FCStd"
        doc.saveAs(str(model.resolve()))
        visible_names = [o["name"] for o in mesh["objects"]]
        Import.export([doc.getObject(n) for n in visible_names],
                      str((args.output / "candidate.step").resolve()))
        for item in mesh["objects"]:
            if item["name"] in changed:
                vertices, faces = doc.getObject(item["name"]).Shape.tessellate(.12)
                item["vertices"] = [[v.x, v.y, v.z] for v in vertices]
                item["faces"] = faces
        after = {n: shape_signature(doc.getObject(n).Shape) for n in changed}
    finally:
        App.closeDocument(doc.Name)

    # Headless saving does not preserve the GUI state. Restore its exact saved
    # archive members from the supplied appearance source. Preserve unchanged
    # baseline BRep bytes to avoid incidental OCCT serialization differences.
    with zipfile.ZipFile(args.base) as base, zipfile.ZipFile(args.appearance_source) as appearance, zipfile.ZipFile(model) as saved:
        gui_names = [n for n in appearance.namelist() if n == "GuiDocument.xml" or
                     n.startswith(("ShapeAppearance", "LineColorArray", "PointColorArray"))]
        if "GuiDocument.xml" not in gui_names:
            raise ValueError("appearance source lacks saved GUI data")
        saved_payloads = {n: saved.read(n) for n in saved.namelist()}
        preserved_members = [n for n in base.namelist() if
                             (n.endswith('.brp') or '.Shape.Map.' in n) and
                             n.split('.Shape.')[0] not in changed]
        for name in preserved_members:
            saved_payloads[name] = base.read(name)
        geometry_before = {n: hashlib.sha256(b).hexdigest() for n, b in saved_payloads.items()
                           if n not in gui_names}
        for name in gui_names:
            saved_payloads[name] = appearance.read(name)
    with zipfile.ZipFile(model, "w", compression=zipfile.ZIP_DEFLATED) as saved:
        for name, data in saved_payloads.items():
            saved.writestr(name, data)
    with zipfile.ZipFile(model) as saved:
        assert all(hashlib.sha256(saved.read(n)).hexdigest() == h
                   for n, h in geometry_before.items())
    saved_doc = App.openDocument(str(model.resolve()))
    try:
        for item in mesh["objects"]:
            if item["name"] in changed:
                vertices, faces = saved_doc.getObject(item["name"]).Shape.tessellate(.12)
                item["vertices"] = [[v.x, v.y, v.z] for v in vertices]
                item["faces"] = faces
    finally:
        App.closeDocument(saved_doc.Name)
    mesh["fcstd_sha256"] = sha(model)
    (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
    report = {
        "revision": args.revision, "status": "saved candidate; fixed-camera comparison pending",
        "baseline_fcstd_sha256": baseline_hash, "fcstd_sha256": sha(model),
        "step_sha256": sha(args.output / "candidate.step"),
        "source_script_sha256": sha(Path(__file__)),
        "changed_objects": sorted(changed), "expansion_per_side_mm": e,
        "before": {n: before[n] for n in sorted(changed)}, "after": after,
        "preserved_shape_count": len(preserved), "preserved_shapes": preserved,
        "screen_objects": {n: before[n] for n in ("ScreenPanel210x160x2", "ActiveArea200x150")},
        "opening_mm": [202, 152], "gui_members_copied_from_appearance_source": len(gui_names),
        "appearance_source_sha256": sha(args.appearance_source),
        "unchanged_brep_and_map_members_restored": len(preserved_members),
        "geometry_unchanged_during_gui_restore": True,
        "mesh_objects": len(mesh["objects"]),
        "distinct_rgb_triples": len({tuple(o["color"]) for o in mesh["objects"]}),
        "unchanged_mesh_geometry": "all baseline vertices/faces reused except the two named CAD solids",
        "changed_mesh_geometry": "tessellated from final reopened candidate FCStd",
        "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
        "limitations": ["outer surround dimensions are an appearance hypothesis",
                       "measured flat screen retained; curved cover is only an appearance assumption",
                       "no manufacturing, fit, optical, thermal, electrical, or physical acceptance"],
    }
    (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("fcstd_sha256", "step_sha256", "mesh_objects", "distinct_rgb_triples")}))


if __name__ == "__main__":
    main()
