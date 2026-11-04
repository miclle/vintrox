"""Combine only the saved v84 LowerPodRib family with v90.

The v91 experiment copied all 108 v84 LowerPod edge rails and ridges and
regressed across the fixed orbit. This narrower trial copies the 36 saved
LowerPodRib solids only, preserving v90's other BRep and GUI members.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import FreeCAD as App
import Import


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


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("base", "pod", "base-mesh", "pod-check", "appearance-source", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be empty")

    base_hash = digest(args.base)
    mesh = json.loads(args.base_mesh.read_text(encoding="utf-8"))
    if mesh.get("fcstd_sha256") != base_hash:
        raise ValueError("baseline mesh hash mismatch")
    # LowerPodRib is a distinct 36-object family in the saved v84 candidate;
    # v84's explicit root-edit list contains the neighboring rails/ridges, so
    # select this family from the saved source document rather than claiming
    # those 36 objects were part of that edit list.
    pod_check = json.loads(args.pod_check.read_text(encoding="utf-8"))
    changed = sorted(name for name in pod_check.get("preserved_objects", [])
                     if name.startswith("LowerPodRib"))
    if not changed:
        changed = sorted(name for name in pod_check.get("changed_objects", [])
                         if name.startswith("LowerPodRib"))
    if len(changed) != 36:
        raise ValueError(f"expected 36 LowerPodRib objects, got {len(changed)}")
    args.output.mkdir(parents=True, exist_ok=True)

    docs = [App.openDocument(str(path.resolve())) for path in
            (args.base, args.pod / "candidate.FCStd")]
    base, pod = docs
    try:
        base_objects = {obj.Name: obj for obj in base.Objects
                        if hasattr(obj, "Shape") and not obj.Shape.isNull()}
        pod_objects = {obj.Name: obj for obj in pod.Objects
                       if hasattr(obj, "Shape") and not obj.Shape.isNull()}
        if any(name not in base_objects or name not in pod_objects for name in changed):
            raise ValueError("missing LowerPodRib source object")
        base_before = {name: signature(obj.Shape) for name, obj in base_objects.items()}
        for name in changed:
            shape = pod_objects[name].Shape.copy()
            if not shape.isValid() or not shape.Solids or not all(s.isClosed() for s in shape.Solids):
                raise ValueError(f"invalid source shape: {name}")
            base_objects[name].Shape = shape
        base.recompute()
        model = args.output / "candidate.FCStd"
        base.saveAs(str(model.resolve()))
        Import.export([base.getObject(item["name"]) for item in mesh["objects"]],
                      str((args.output / "candidate.step").resolve()))
    finally:
        for doc in docs:
            App.closeDocument(doc.Name)

    with (zipfile.ZipFile(args.base) as base_zip,
          zipfile.ZipFile(args.appearance_source) as appearance_zip,
          zipfile.ZipFile(model) as saved_zip):
        payloads = {name: saved_zip.read(name) for name in saved_zip.namelist()}
        preserved_members = [name for name in base_zip.namelist()
                            if (name.endswith(".brp") or ".Shape.Map." in name)
                            and name.split(".Shape.")[0] not in changed]
        for name in preserved_members:
            payloads[name] = base_zip.read(name)
        gui = [name for name in appearance_zip.namelist()
               if name == "GuiDocument.xml" or name.startswith(
                   ("ShapeAppearance", "LineColorArray", "PointColorArray"))]
        if "GuiDocument.xml" not in gui:
            raise ValueError("appearance source lacks GuiDocument.xml")
        geometry_hashes = {name: hashlib.sha256(data).hexdigest()
                           for name, data in payloads.items() if name not in gui}
        for name in gui:
            payloads[name] = appearance_zip.read(name)
    with zipfile.ZipFile(model, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in payloads.items():
            out.writestr(name, data)
    with zipfile.ZipFile(model) as check:
        for name, expected in geometry_hashes.items():
            if hashlib.sha256(check.read(name)).hexdigest() != expected:
                raise ValueError(f"geometry changed during GUI restore: {name}")

    saved = App.openDocument(str(model.resolve()))
    baseline = App.openDocument(str(args.base.resolve()))
    try:
        for name in changed:
            shape = saved.getObject(name).Shape
            if not shape.isValid() or not shape.Solids or not all(s.isClosed() for s in shape.Solids):
                raise ValueError(f"saved candidate invalid: {name}")
        preserved = []
        for name, old in base_before.items():
            if name in changed:
                continue
            obj = saved.getObject(name)
            if obj is None or obj.Shape.isNull() or signature(obj.Shape) != old:
                raise ValueError(f"unintended saved change: {name}")
            preserved.append(name)
        protected = []
        for obj in baseline.Objects:
            if not obj.Name.startswith(("SupportShaft", "SupportSocket", "SupportFoot", "CentralSupportSeat")):
                continue
            first = saved.getObject(obj.Name).Shape
            delta = abs(first.cut(obj.Shape).Volume) + abs(obj.Shape.cut(first).Volume)
            if delta > 1e-6:
                raise ValueError(f"protected support changed: {obj.Name}: {delta}")
            protected.append({"name": obj.Name, "symmetric_difference_mm3": delta})
        for item in mesh["objects"]:
            if item["name"] in changed:
                vertices, faces = saved.getObject(item["name"]).Shape.tessellate(.12)
                item["vertices"] = [[v.x, v.y, v.z] for v in vertices]
                item["faces"] = faces
        Import.export([saved.getObject(item["name"]) for item in mesh["objects"]],
                      str((args.output / "candidate.step").resolve()))
        mesh["fcstd_sha256"] = digest(model)
        (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
        report = {
            "revision": args.revision,
            "status": "combined saved-CAD trial; fixed-camera comparison required",
            "baseline_revision": "v90-front-cheek-contract097",
            "baseline_fcstd_sha256": base_hash,
            "fcstd_sha256": digest(model),
            "step_sha256": digest(args.output / "candidate.step"),
            "source_script_sha256": digest(Path(__file__)),
            "source_pod_fcstd_sha256": digest(args.pod / "candidate.FCStd"),
            "source_pod_check_sha256": digest(args.pod_check),
            "changed_objects": changed,
            "changed_families": {"LowerPodRib": len(changed)},
            "preserved_shape_count": len(preserved),
            "protected_supports": protected,
            "screen_geometry_preserved": all(
                signature(saved.getObject(name).Shape) == signature(baseline.getObject(name).Shape)
                for name in ("ScreenPanel210x160x2", "ActiveArea200x150")),
            "gui_members_copied": len(gui),
            "geometry_unchanged_during_gui_restore": True,
            "mesh_objects": len(mesh["objects"]),
            "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
            "limitations": [
                "only v84 LowerPodRib solids were combined with v90",
                "measured flat screen retained; curved reference screen remains an appearance assumption",
                "no manufacturing, fit, optical, thermal, electrical, or physical acceptance",
            ],
        }
        (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(baseline.Name)


if __name__ == "__main__":
    main()
