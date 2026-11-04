"""Combine the disjoint v84 lower-pod and v85 brow CAD trials.

The candidate is built from the saved v69 study.  Shapes are copied from the
two saved candidates, while GUI appearance members and every untouched BRep
member come from v69.  This is an appearance study; the fixed-camera review
must decide whether the combined hypothesis is useful.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import FreeCAD as App
import Import


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser()
    for name in ("base", "pod", "brow", "base-mesh", "appearance-source", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be empty")
    base_hash = digest(args.base)
    mesh = json.loads(args.base_mesh.read_text())
    if mesh["fcstd_sha256"] != base_hash:
        raise ValueError("baseline mesh hash mismatch")

    docs = [App.openDocument(str(path.resolve())) for path in
            (args.base, args.pod / "candidate.FCStd", args.brow / "candidate.FCStd")]
    base, pod, brow = docs
    pod_names = {o.Name for o in pod.Objects if o.Name.startswith("LowerPod")
                 and hasattr(o, "Shape") and not o.Shape.isNull()}
    brow_names = {"ProjectingBrow", "BrowUnderside"}
    if not pod_names or not brow_names.issubset({o.Name for o in brow.Objects}):
        raise ValueError("source candidate object set is incomplete")
    changed = sorted(pod_names | brow_names)
    if pod_names & brow_names:
        raise ValueError("candidate object sets overlap")
    try:
        for name in sorted(pod_names):
            shape = pod.getObject(name).Shape.copy()
            if not shape.isValid() or not shape.isClosed() or len(shape.Solids) == 0:
                raise ValueError(f"invalid pod shape: {name}")
            base.getObject(name).Shape = shape
        for name in sorted(brow_names):
            shape = brow.getObject(name).Shape.copy()
            if not shape.isValid() or not shape.isClosed() or len(shape.Solids) == 0:
                raise ValueError(f"invalid brow shape: {name}")
            base.getObject(name).Shape = shape
        base.recompute()
        args.output.mkdir(parents=True)
        model = args.output / "candidate.FCStd"
        base.saveAs(str(model.resolve()))
    finally:
        for doc in docs:
            App.closeDocument(doc.Name)

    saved = App.openDocument(str(model.resolve()))
    base_check = App.openDocument(str(args.base.resolve()))
    try:
        for name in changed:
            obj = saved.getObject(name)
            if not obj or not obj.Shape.isValid() or not obj.Shape.isClosed():
                raise ValueError(f"saved candidate invalid: {name}")
        preserved = []
        for obj in base_check.Objects:
            if not hasattr(obj, "Shape") or obj.Shape.isNull():
                continue
            other = saved.getObject(obj.Name)
            if obj.Name in changed:
                continue
            if other is None or other.Shape.isNull():
                raise ValueError(f"missing preserved object: {obj.Name}")
            preserved.append(obj.Name)
        support_checks = []
        for name in sorted(n for n in [o.Name for o in base_check.Objects]
                           if n.startswith(("SupportShaft", "SupportSocket",
                                            "SupportFoot", "CentralSupportSeat"))):
            old = base_check.getObject(name).Shape
            new = saved.getObject(name).Shape
            delta = old.cut(new).Volume + new.cut(old).Volume
            if delta > 1e-6:
                raise ValueError(f"protected support changed: {name} {delta}")
            support_checks.append({"name": name, "symmetric_difference_mm3": delta})
        for item in mesh["objects"]:
            if item["name"] in changed:
                vertices, faces = saved.getObject(item["name"]).Shape.tessellate(.12)
                item.update(vertices=[list(v) for v in vertices], faces=faces)
        Import.export([saved.getObject(item["name"]) for item in mesh["objects"]],
                      str((args.output / "candidate.step").resolve()))
    finally:
        App.closeDocument(base_check.Name)
        App.closeDocument(saved.Name)

    # Use the v69 GUI archive, which carries the audited saved colors and
    # visibility.  Only the shape members for changed objects remain from the
    # newly saved candidate.
    with zipfile.ZipFile(args.base) as base_zip, \
         zipfile.ZipFile(args.appearance_source) as appearance_zip, \
         zipfile.ZipFile(model) as saved_zip:
        payloads = {n: saved_zip.read(n) for n in saved_zip.namelist()}
        members = [n for n in base_zip.namelist()
                   if (n.endswith(".brp") or ".Shape.Map." in n)
                   and n.split(".Shape.")[0] not in changed]
        for name in members:
            payloads[name] = base_zip.read(name)
        geometry = {n: digest_bytes(b) for n, b in payloads.items()
                    if n != "GuiDocument.xml" and not n.startswith(
                        ("ShapeAppearance", "LineColorArray", "PointColorArray"))}
        gui = [n for n in appearance_zip.namelist()
               if n == "GuiDocument.xml" or n.startswith(
                   ("ShapeAppearance", "LineColorArray", "PointColorArray"))]
        for name in gui:
            payloads[name] = appearance_zip.read(name)
    with zipfile.ZipFile(model, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in payloads.items():
            out.writestr(name, data)
    with zipfile.ZipFile(model) as check:
        for name, expected in geometry.items():
            if digest_bytes(check.read(name)) != expected:
                raise ValueError(f"geometry archive changed during GUI restore: {name}")

    mesh["fcstd_sha256"] = digest(model)
    (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
    report = {
        "status": "combined saved-CAD trial; fixed-camera comparison pending",
        "baseline_fcstd_sha256": base_hash,
        "fcstd_sha256": digest(model),
        "step_sha256": digest(args.output / "candidate.step"),
        "script_sha256": digest(Path(__file__)),
        "source_candidates": {
            "pod_fcstd_sha256": digest(args.pod / "candidate.FCStd"),
            "brow_fcstd_sha256": digest(args.brow / "candidate.FCStd"),
        },
        "changed_objects": changed,
        "changed_families": {"LowerPod": len(pod_names), "front_brow": len(brow_names)},
        "preserved_objects": preserved,
        "protected_supports": support_checks,
        "gui_members_copied": len(gui),
        "geometry_unchanged_during_gui_restore": True,
        "limitations": [
            "disjoint trials combined without joint re-fitting",
            "screen-space evidence required before adoption",
            "no manufacturing, physical, or assembly acceptance",
        ],
    }
    (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"fcstd_sha256": report["fcstd_sha256"],
                      "changed": len(changed), "preserved": len(preserved),
                      "gui_members": len(gui)}))


if __name__ == "__main__":
    main()
