"""Build a v229-derived closed belly height candidate.

The 60 mm central support strip is fixed by the current formal model. Only
the outer belly floor and the service-plate placement are varied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import FreeCAD as App
import Import
import Part


def belly(shape: Part.Shape, floor_z: float, half_width: float = 30.0) -> Part.Shape:
    result = shape.copy()
    for side in (-1, 1):
        points = [(half_width, -20), (130, -20), (130, floor_z),
                  (62, floor_z), (half_width, 35)]
        vertices = [App.Vector(side * x, -20, z) for x, z in points]
        cutter = Part.Face(Part.makePolygon(vertices + [vertices[0]])).extrude(
            App.Vector(0, 220, 0))
        result = result.cut(cutter)
    result = result.removeSplitter()
    result.check(True)
    if not result.isValid() or not result.isClosed() or len(result.Solids) != 1:
        raise ValueError("Invalid closed belly candidate")
    return result


def service_shape(shape: Part.Shape, side: int, floor_z: float, is_bolt: bool) -> Part.Shape:
    if is_bolt:
        bounds = shape.optimalBoundingBox(False, False)
        center = App.Vector((bounds.XMin + bounds.XMax) / 2,
                            (bounds.YMin + bounds.YMax) / 2, bounds.ZMax)
        ellipse = Part.Ellipse(center, 2.6, 2.184).toShape()
        face = Part.Face(Part.Wire(ellipse))
        face.rotate(center, App.Vector(0, 0, 1), 90)
        moved = face.extrude(App.Vector(0, 0, -1.8))
    else:
        moved = shape.copy()
    moved.translate(App.Vector(side * 10.92, 0, floor_z - 36.7))
    return moved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--floor", type=float, required=True)
    args = parser.parse_args()
    if not 44 <= args.floor <= 53:
        raise ValueError("Belly floor outside the studied range")
    args.output = args.output.resolve()
    args.base = args.base.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    base_hash = hashlib.sha256(args.base.read_bytes()).hexdigest()
    doc = App.openDocument(str(args.base.resolve()))
    old = {obj.Name: obj.Shape.copy() for obj in doc.Objects
           if hasattr(obj, "Shape") and not obj.Shape.isNull()}
    changed = {"ClosedBellyPan": belly(old["ClosedBellyPan"], args.floor)}
    for name, shape in old.items():
        if name.startswith(("BellyServicePlate", "BellyServiceBolt")):
            side = -1 if "Left" in name else 1
            changed[name] = service_shape(shape, side, args.floor,
                                          name.startswith("BellyServiceBolt"))
    for name, shape in changed.items():
        shape.check(True)
        if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1:
            raise ValueError(f"Invalid changed object {name}")
        doc.getObject(name).Shape = shape
    doc.recompute()
    model = args.output / "candidate.FCStd"
    doc.saveAs(str(model))
    App.closeDocument(doc.Name)
    doc = App.openDocument(str(model))
    try:
        with ZipFile(args.base) as archive:
            gui = ElementTree.fromstring(archive.read("GuiDocument.xml"))
            names = [node.attrib["name"] for node in gui.findall(".//ViewProvider")
                     if node.find('./Properties/Property[@name="Visibility"]/Bool[@value="true"]') is not None]
        visible = [doc.getObject(name) for name in names
                   if doc.getObject(name) is not None and not doc.getObject(name).Shape.isNull()]
        step_path = (args.output / "candidate.step").resolve()
        Import.export(visible, str(step_path))
        if not step_path.exists():
            raise RuntimeError("STEP export did not create the candidate file")
        report = {
            "revision": args.output.name,
            "baseline_fcstd_sha256": base_hash,
            "fcstd_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
            "step_sha256": hashlib.sha256(step_path.read_bytes()).hexdigest(),
            "floor_z_mm": args.floor,
            "central_strip_width_mm": 60.0,
            "changed_objects": sorted(changed),
            "visible_features": len(visible),
            "status": "saved candidate; fixed-camera screening pending",
        }
        (args.output / "candidate-check.json").write_text(
            json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
