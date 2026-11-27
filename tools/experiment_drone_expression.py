"""Build a reference-derived pixel expression on the unchanged measured flat screen."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import Import
import numpy as np
from scipy.optimize import least_squares
from drone_concept import profile
from fit_drone_lower_pod_outline import project

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
    parser.add_argument("--features", choices=['all', 'mouth'], default='all')
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("output must be a new empty directory")
    mesh = json.loads(args.base_mesh.read_text())
    baseline_hash = sha(args.base)
    if mesh["fcstd_sha256"] != baseline_hash:
        raise ValueError("baseline mesh is not bound to the saved FCStd")
    args.output.mkdir(parents=True, exist_ok=True)
    changed = {"PixelEye_39", "PixelEyeTop_39", "PixelEye27", "PixelEyeTop27", "PixelMouth", "PixelSmileHighlight"}
    cameras = json.loads(Path("cad/drone-concept/comparison/v69-underbody-loop-radius2p2/video-comparison/cameras.json").read_text())
    def world(pixels):
        result = []
        for px in pixels:
            fit = least_squares(lambda xz: project(np.array([[xz[0], -9.6, xz[1]]]), 270, cameras)[0]-px, [0, 150])
            result.append(fit.x.tolist())
        return result
    observations = {
        "PixelMouth": [[307,499],[643,499],[643,529],[632,529],[632,549],[621,549],[621,569],[609,569],[609,579],[587,579],[587,589],[565,589],[565,598],[520,598],[520,606],[431,606],[431,598],[386,598],[386,589],[364,589],[364,579],[341,579],[341,569],[330,569],[330,549],[319,549],[319,529],[307,529]],
        "PixelSmileHighlight": [[318,510],[632,510],[632,529],[543,529],[543,539],[407,539],[407,529],[318,529]],
        "PixelEye_39": [[396,381],[408,381],[408,391],[419,391],[419,431],[408,431],[408,440],[396,440],[396,431],[385,431],[385,391],[396,391]],
        "PixelEye27": [[543,381],[555,381],[555,391],[566,391],[566,431],[555,431],[555,440],[543,440],[543,431],[532,431],[532,391],[543,391]],
    }
    # Keep the existing separate eye-top objects as the upper rectangular cells.
    observations["PixelEyeTop_39"] = [[396,381],[408,381],[408,391],[396,391]]
    observations["PixelEyeTop27"] = [[543,381],[555,381],[555,391],[543,391]]
    if args.features == 'mouth':
        observations = {n: px for n, px in observations.items() if n in ['PixelMouth', 'PixelSmileHighlight']}
        changed = set(observations)
    world_polygons = {n: world(px) for n, px in observations.items()}
    doc = App.openDocument(str(args.base.resolve()))
    try:
        shapes = {o.Name: o.Shape.copy() for o in doc.Objects
                  if hasattr(o, "Shape") and not o.Shape.isNull()}
        before = {n: shape_signature(s) for n, s in shapes.items()}
        for name, polygon in world_polygons.items():
            # Trim eye bodies below the separate top cap; no duplicate volume.
            if name.startswith('PixelEye') and not name.startswith('PixelEyeTop'):
                polygon = polygon[2:]+polygon[:2]
                polygon = [p for p, px in zip(polygon, observations[name][2:]+observations[name][:2]) if px[1] != 381]
            depth = .4 if name == 'PixelSmileHighlight' else .5
            y = -10 if name == 'PixelSmileHighlight' else -9.6
            shape = profile(polygon, 'XZ', (0, y, 0), depth)
            shape.check(True)
            if not shape.isValid() or len(shape.Solids) != 1 or not shape.Solids[0].isClosed():
                raise ValueError(f'invalid expression: {name}')
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
        "changed_objects": sorted(changed), "source_observations_frame270_px": observations, "world_polygons_xz_mm": world_polygons,
        "before": {n: before[n] for n in sorted(changed)}, "after": after,
        "preserved_shape_count": len(preserved), "preserved_shapes": preserved,
        "screen_objects": {n: before[n] for n in ("ScreenPanel210x160x2", "ActiveArea200x150")},
        "opening_mm": [202, 152], "gui_members_copied_from_appearance_source": len(gui_names),
        "appearance_source_sha256": sha(args.appearance_source),
        "unchanged_brep_and_map_members_restored": len(preserved_members),
        "geometry_unchanged_during_gui_restore": True,
        "mesh_objects": len(mesh["objects"]),
        "distinct_rgb_triples": len({tuple(o["color"]) for o in mesh["objects"]}),
        "unchanged_mesh_geometry": "all baseline vertices/faces reused except named expression solids",
        "changed_mesh_geometry": "tessellated from final reopened candidate FCStd",
        "registration": "fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts",
        "limitations": ["manual expression contours from frame 270; other views are held out",
                       "measured flat screen retained; curved cover is only an appearance assumption",
                       "no manufacturing, fit, optical, thermal, electrical, or physical acceptance"],
    }
    (args.output / "candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("fcstd_sha256", "step_sha256", "mesh_objects", "distinct_rgb_triples")}))


if __name__ == "__main__":
    main()
