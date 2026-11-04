"""Build a fixed-camera FrontCheek contraction candidate from saved CAD.

The two mirrored front cheek solids and their bridge plates are contracted about
X=0. This is an appearance study: the measured flat screen, side controls,
side grilles, external barrels, and four supports remain unchanged. The saved
CAD and reopened tessellation are bound by hashes before comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import FreeCAD as App
import Import

CHANGED = (
    "FrontCheekLeft", "FrontCheekRight",
    "FrontCheekBridgeLeft", "FrontCheekBridgeRight",
)
PROTECTED_PREFIXES = ("SupportShaft", "SupportSocket", "SupportFoot", "CentralSupportSeat")
GUI_PREFIXES = ("ShapeAppearance", "LineColorArray", "PointColorArray")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sig(shape):
    b = shape.BoundBox
    return {
        "volume_mm3": round(shape.Volume, 6),
        "area_mm2": round(shape.Area, 6),
        "bbox_mm": [round(v, 6) for v in
                    (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)],
        "solids": len(shape.Solids),
        "valid": bool(shape.isValid()),
        "closed": all(s.isClosed() for s in shape.Solids),
    }


def symdiff(a, b):
    return abs(a.cut(b).Volume) + abs(b.cut(a).Volume)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--base-mesh", type=Path, required=True)
    p.add_argument("--appearance-source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--scale", type=float, required=True)
    p.add_argument("--revision", required=True)
    args = p.parse_args()
    if not 0.95 <= args.scale < 1.0:
        raise ValueError("scale must be in [0.95, 1)")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be empty")
    mesh = json.loads(args.base_mesh.read_text(encoding="utf-8"))
    base_hash = sha(args.base)
    if mesh.get("fcstd_sha256") != base_hash:
        raise ValueError("base mesh hash mismatch")
    args.output.mkdir(parents=True, exist_ok=True)

    doc = App.openDocument(str(args.base.resolve()))
    before = {}
    try:
        objects = {o.Name: o for o in doc.Objects
                   if hasattr(o, "Shape") and not o.Shape.isNull()}
        missing = [n for n in CHANGED if n not in objects]
        if missing:
            raise ValueError(f"missing changed objects: {missing}")
        before = {n: sig(objects[n].Shape) for n in CHANGED}
        matrix = App.Matrix()
        matrix.A11 = args.scale
        for name in CHANGED:
            shape = objects[name].Shape.copy()
            transformed = shape.transformGeometry(matrix)
            if (not transformed.isValid() or not transformed.Solids or
                    not all(s.isClosed() for s in transformed.Solids)):
                raise ValueError(f"invalid transformed solid: {name}")
            objects[name].Shape = transformed
        doc.recompute()
        model = args.output / "candidate.FCStd"
        doc.saveAs(str(model.resolve()))
        visible = [o for o in doc.Objects if hasattr(o, "Shape") and
                   o.Visibility and not o.Shape.isNull()]
        Import.export(visible, str((args.output / "candidate.step").resolve()))
    finally:
        App.closeDocument(doc.Name)

    # Restore audited appearance and untouched BRep archive members.
    with (zipfile.ZipFile(args.base) as base_zip,
          zipfile.ZipFile(args.appearance_source) as appearance_zip,
          zipfile.ZipFile(model) as saved_zip):
        payloads = {n: saved_zip.read(n) for n in saved_zip.namelist()}
        gui = [n for n in appearance_zip.namelist()
               if n == "GuiDocument.xml" or n.startswith(GUI_PREFIXES)]
        if "GuiDocument.xml" not in gui:
            raise ValueError("appearance source lacks GuiDocument.xml")
        preserved_members = [n for n in base_zip.namelist()
                             if (n.endswith(".brp") or ".Shape.Map." in n)
                             and n.split(".Shape.")[0] not in CHANGED]
        for n in preserved_members:
            payloads[n] = base_zip.read(n)
        geometry_hashes = {n: hashlib.sha256(b).hexdigest()
                           for n, b in payloads.items() if n not in gui}
        for n in gui:
            payloads[n] = appearance_zip.read(n)
    with zipfile.ZipFile(model, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for n, b in payloads.items():
            out.writestr(n, b)
    with zipfile.ZipFile(model) as check:
        for n, expected in geometry_hashes.items():
            if hashlib.sha256(check.read(n)).hexdigest() != expected:
                raise ValueError(f"geometry changed during GUI restore: {n}")

    # Reopen and independently verify all changed/preserved/protected shapes;
    # bind updated meshes to the final saved FCStd.
    saved = App.openDocument(str(model.resolve()))
    base = App.openDocument(str(args.base.resolve()))
    try:
        checks = {}
        for name in CHANGED:
            obj = saved.getObject(name)
            if obj is None:
                raise ValueError(f"missing saved object: {name}")
            if not obj.Shape.isValid() or not obj.Shape.Solids or not all(s.isClosed() for s in obj.Shape.Solids):
                raise ValueError(f"saved readback invalid: {name}")
            checks[name] = sig(obj.Shape)
        preserved = []
        for obj in base.Objects:
            if not hasattr(obj, "Shape") or obj.Shape.isNull() or obj.Name in CHANGED:
                continue
            other = saved.getObject(obj.Name)
            if other is None or other.Shape.isNull() or sig(other.Shape) != sig(obj.Shape):
                raise ValueError(f"unintended saved change: {obj.Name}")
            preserved.append(obj.Name)
        protected = []
        for obj in base.Objects:
            if not obj.Name.startswith(PROTECTED_PREFIXES):
                continue
            delta = symdiff(saved.getObject(obj.Name).Shape, obj.Shape)
            if delta > 1e-6:
                raise ValueError(f"protected support changed: {obj.Name}: {delta}")
            protected.append({"name": obj.Name, "symmetric_difference_mm3": delta})
        mesh_objects = []
        for item in mesh["objects"]:
            obj = saved.getObject(item["name"])
            if obj is None or obj.Shape.isNull():
                raise ValueError(f"mesh object missing: {item['name']}")
            if item["name"] in CHANGED:
                vertices, faces = obj.Shape.tessellate(.12)
                item["vertices"] = [[v.x, v.y, v.z] for v in vertices]
                item["faces"] = faces
            mesh_objects.append(item["name"])
        Import.export([saved.getObject(n) for n in mesh_objects],
                      str((args.output / "candidate.step").resolve()))
        mesh["fcstd_sha256"] = sha(model)
        (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
        report = {
            "revision": args.revision,
            "status": "saved CAD candidate; fixed-camera comparison required",
            "baseline_fcstd_sha256": base_hash,
            "fcstd_sha256": sha(model),
            "step_sha256": sha(args.output / "candidate.step"),
            "source_script_sha256": sha(Path(__file__)),
            "changed_objects": list(CHANGED),
            "x_scale_about_model_center": args.scale,
            "before": before,
            "after": checks,
            "preserved_shape_count": len(preserved),
            "protected_supports": protected,
            "screen_geometry_preserved": all(
                sig(saved.getObject(n).Shape) == sig(base.getObject(n).Shape)
                for n in ("ScreenPanel210x160x2", "ActiveArea200x150")),
            "gui_members_copied": len(gui),
            "geometry_unchanged_during_gui_restore": True,
            "mesh_objects": len(mesh_objects),
            "distinct_rgb_triples": len({tuple(item["color"]) for item in mesh["objects"]}),
            "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
            "limitations": [
                "front-cheek contraction is an image-derived appearance hypothesis",
                "measured flat screen retained; curved reference screen remains an appearance assumption",
                "no manufacturing, fit, optical, thermal, electrical, or physical acceptance",
            ],
        }
        (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: report[k] for k in ("fcstd_sha256", "step_sha256", "mesh_objects", "distinct_rgb_triples", "screen_geometry_preserved")}))
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(base.Name)


if __name__ == "__main__":
    main()
