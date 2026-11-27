"""Combine the saved v88 petal contraction and v85 front-brow studies.

This creates an independent saved-CAD appearance candidate from v69. Only the
saved BRep shapes listed by the two source candidates are copied; every other
shape remains byte-for-byte bound to v69. GUI appearance is restored from the
v88 display-audited file, then the candidate must be re-rendered and compared
with the fixed cameras before any adoption decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import FreeCAD as App
import Import


PETAL_PREFIXES = ("NozzlePetal",)
BROW_NAMES = {"ProjectingBrow", "BrowUnderside"}
PROTECTED_PREFIXES = ("SupportShaft", "SupportSocket", "SupportFoot", "CentralSupportSeat")
GUI_PREFIXES = ("ShapeAppearance", "LineColorArray", "PointColorArray")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def object_names(doc, prefixes=()):
    return {obj.Name for obj in doc.Objects if any(obj.Name.startswith(p) for p in prefixes)
            and hasattr(obj, "Shape") and not obj.Shape.isNull()}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("base", "petal", "brow", "base-mesh", "appearance-source", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be empty")

    base_hash = digest(args.base)
    mesh = json.loads(args.base_mesh.read_text(encoding="utf-8"))
    if mesh.get("fcstd_sha256") != base_hash:
        raise ValueError("baseline mesh hash mismatch")

    docs = [App.openDocument(str(path.resolve())) for path in
            (args.base, args.petal / "candidate.FCStd", args.brow / "candidate.FCStd")]
    base, petal, brow = docs
    try:
        petal_names = object_names(petal, PETAL_PREFIXES)
        brow_names = {name for name in BROW_NAMES if brow.getObject(name) is not None}
        if not petal_names or brow_names != BROW_NAMES:
            raise ValueError("source candidate object set is incomplete")
        changed = sorted(petal_names | brow_names)
        if petal_names & brow_names:
            raise ValueError("candidate object sets overlap")
        base_shapes = {obj.Name: obj.Shape.copy() for obj in base.Objects
                       if hasattr(obj, "Shape") and not obj.Shape.isNull()}
        for name in sorted(petal_names):
            source = petal.getObject(name).Shape
            if not source.isValid() or not source.isClosed() or not source.Solids:
                raise ValueError(f"invalid petal shape: {name}")
            base.getObject(name).Shape = source.copy()
        for name in sorted(brow_names):
            source = brow.getObject(name).Shape
            if not source.isValid() or not source.isClosed() or not source.Solids:
                raise ValueError(f"invalid brow shape: {name}")
            base.getObject(name).Shape = source.copy()
        base.recompute()
        args.output.mkdir(parents=True)
        model = args.output / "candidate.FCStd"
        base.saveAs(str(model.resolve()))
    finally:
        for doc in docs:
            App.closeDocument(doc.Name)

    # Reopen the saved CAD, verify preservation, update changed tessellation and
    # export only the same visible mesh contract as v69.
    saved = App.openDocument(str(model.resolve()))
    baseline = App.openDocument(str(args.base.resolve()))
    try:
        changed_checks = {}
        for name in changed:
            shape = saved.getObject(name).Shape
            if not shape.isValid() or not shape.isClosed() or not shape.Solids:
                raise ValueError(f"saved candidate invalid: {name}")
            changed_checks[name] = signature(shape)
        preserved = []
        for name, old_shape in base_shapes.items():
            obj = saved.getObject(name)
            if obj is None or obj.Shape.isNull() or not obj.Shape.isValid() or not obj.Shape.isClosed():
                raise ValueError(f"missing preserved object: {name}")
            if name not in changed:
                if signature(obj.Shape) != signature(old_shape):
                    raise ValueError(f"unintended saved shape change: {name}")
                preserved.append(name)
        protected = []
        for obj in baseline.Objects:
            if not obj.Name.startswith(PROTECTED_PREFIXES):
                continue
            first = saved.getObject(obj.Name).Shape
            second = obj.Shape
            delta = abs(first.cut(second).Volume) + abs(second.cut(first).Volume)
            if delta > 1e-6:
                raise ValueError(f"protected support changed: {obj.Name}")
            protected.append({"name": obj.Name, "symmetric_difference_mm3": delta})
        for item in mesh["objects"]:
            if item["name"] in changed:
                vertices, faces = saved.getObject(item["name"]).Shape.tessellate(.12)
                item.update(vertices=[list(v) for v in vertices], faces=faces)
        Import.export([saved.getObject(item["name"]) for item in mesh["objects"]],
                      str((args.output / "candidate.step").resolve()))
    finally:
        App.closeDocument(baseline.Name)
        App.closeDocument(saved.Name)

    # Use v88's audited GUI payload, while restoring untouched BRep members from
    # v69. This preserves colors/visibility without changing geometry.
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
               if name == "GuiDocument.xml" or name.startswith(GUI_PREFIXES)]
        if "GuiDocument.xml" not in gui:
            raise ValueError("appearance source lacks GuiDocument.xml")
        geometry_hashes = {name: digest_bytes(data) for name, data in payloads.items()
                           if name not in gui}
        for name in gui:
            payloads[name] = appearance_zip.read(name)
    with zipfile.ZipFile(model, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in payloads.items():
            out.writestr(name, data)
    with zipfile.ZipFile(model) as check:
        for name, expected in geometry_hashes.items():
            if digest_bytes(check.read(name)) != expected:
                raise ValueError(f"geometry archive changed during GUI restore: {name}")

    mesh["fcstd_sha256"] = digest(model)
    (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
    report = {
        "revision": args.revision,
        "status": "combined saved-CAD trial; fixed-camera comparison pending",
        "baseline_fcstd_sha256": base_hash,
        "fcstd_sha256": digest(model),
        "step_sha256": digest(args.output / "candidate.step"),
        "script_sha256": digest(Path(__file__)),
        "source_candidates": {
            "petal_fcstd_sha256": digest(args.petal / "candidate.FCStd"),
            "brow_fcstd_sha256": digest(args.brow / "candidate.FCStd"),
        },
        "changed_objects": changed,
        "changed_families": {"NozzlePetal": len(petal_names), "front_brow": len(brow_names)},
        "preserved_objects": preserved,
        "protected_supports": protected,
        "gui_members_copied": len(gui),
        "geometry_unchanged_during_gui_restore": True,
        "screen_input_preserved": ["ScreenPanel210x160x2", "ActiveArea200x150"],
        "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
        "limitations": [
            "disjoint petal and brow trials combined without joint re-fitting",
            "screen-space evidence required before adoption",
            "measured flat screen retained; curved reference screen remains an appearance assumption",
            "no manufacturing, fit, optical, thermal, electrical, or physical acceptance",
        ],
    }
    (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"fcstd_sha256": report["fcstd_sha256"],
                      "step_sha256": report["step_sha256"],
                      "changed": len(changed), "preserved": len(preserved),
                      "gui_members": len(gui)}))


if __name__ == "__main__":
    main()
