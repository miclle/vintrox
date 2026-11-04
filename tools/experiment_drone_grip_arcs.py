"""Build grip wraps from explicit lines and corner arcs for stable STEP transfer."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import Import
import math
import Part
from drone_concept import box

from experiment_drone_v63_screen_bezel import shape_signature


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--base-mesh", type=Path, required=True)
    parser.add_argument("--appearance-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be a new empty directory")
    mesh = json.loads(args.base_mesh.read_text())
    baseline_hash = sha(args.base)
    if mesh["fcstd_sha256"] != baseline_hash:
        raise ValueError("baseline mesh is not bound to the saved FCStd")
    args.output.mkdir(parents=True, exist_ok=True)
    changed = {f"GripBand{i}" for i in range(10)}
    def wrap(index):
        x0 = -93 + index*18.6
        def section(x, radius, phase=0, fold=0, inner=False):
            cy0, cz0 = (7.5, 5.5) if inner else (16, 14)
            corners=((cy0,cz0,0),(-cy0,cz0,90),
                     (-cy0,-cz0,180),(cy0,-cz0,270))
            def point(cy,cz,angle):
                a=math.radians(angle)
                dy,dz=cy+radius*math.cos(a),cz+radius*math.sin(a)
                return App.Vector(x+dz*.5,122.5+dy,318.5+dz)
            edges=[]
            for i,(cy,cz,start) in enumerate(corners):
                edges.append(Part.Arc(point(cy,cz,start),point(cy,cz,start+45),
                                      point(cy,cz,start+90)).toShape())
                ny,nz,na=corners[(i+1)%4]
                edges.append(Part.makeLine(point(cy,cz,start+90),point(ny,nz,na)))
            return Part.Wire(edges)
        folds=((0,3.4),(.08,3),(.29,3.05),(.33,3.4),
               (.38,3),(.64,3.05),(.70,3.3),(1,3))
        outer=Part.makeLoft([section(x0+t*19,r,index*.79+t*2.3,
                                    .04 if t in (0,1) else .12)
                            for t,r in folds],True,True)
        inner=Part.makeLoft([section(x0-.1,10.8,inner=True),
                            section(x0+19.1,10.8,inner=True)],True,True)
        shape=outer.cut(inner).common(box(183,100,100,(-91.5,80,270)))
        matrix=App.Matrix()
        matrix.A11=1.04
        matrix.A22=1.2
        matrix.A24=25
        matrix.A34=-17
        return shape.transformGeometry(matrix)
    doc = App.openDocument(str(args.base.resolve()))
    try:
        shapes = {o.Name: o.Shape.copy() for o in doc.Objects
                  if hasattr(o, "Shape") and not o.Shape.isNull()}
        before = {n: shape_signature(s) for n, s in shapes.items()}
        for index in range(10):
            name=f"GripBand{index}"
            shape=wrap(index)
            shape.check(True)
            if not shape.isValid() or len(shape.Solids)!=1 or not shape.isClosed():
                raise ValueError(f"invalid wrap: {name}")
            doc.getObject(name).Shape=shape
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
        "changed_objects": sorted(changed), "outer_corner_radius_mm": [3, 3.4],
        "cross_section_corner_centres_yz_mm": [16, 14],
        "construction": "same width, diagonal tape shear and inner core; explicit flat edges and circular corner arcs; no periodic spline overshoot",
        "before": {n: before[n] for n in sorted(changed)}, "after": after,
        "preserved_shape_count": len(preserved), "preserved_shapes": preserved,
        "screen_objects": {n: before[n] for n in ("ScreenPanel210x160x2", "ActiveArea200x150")},
        "gui_members_copied_from_appearance_source": len(gui_names),
        "appearance_source_sha256": sha(args.appearance_source),
        "unchanged_brep_and_map_members_restored": len(preserved_members),
        "geometry_unchanged_during_gui_restore": True,
        "mesh_objects": len(mesh["objects"]),
        "distinct_rgb_triples": len({tuple(o["color"]) for o in mesh["objects"]}),
        "unchanged_mesh_geometry": "all baseline vertices/faces reused except named grip-wrap solids",
        "changed_mesh_geometry": "tessellated from final reopened candidate FCStd",
        "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
        "limitations": ["cross-section appearance hypothesis from front/side reference views; no new camera fit",
                       "measured flat screen retained; curved cover is only an appearance assumption",
                       "no manufacturing, fit, optical, thermal, electrical, or physical acceptance"],
    }
    (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("fcstd_sha256", "step_sha256", "mesh_objects", "distinct_rgb_triples")}))


if __name__ == "__main__":
    main()
