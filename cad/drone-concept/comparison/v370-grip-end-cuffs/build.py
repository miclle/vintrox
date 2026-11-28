"""Bridge the exposed ends of the wrapped grip to the tilted handle arms."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import FreeCAD as App
import Part


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    doc = App.openDocument(str(args.base.resolve()))
    geometry = args.output.with_suffix(".headless.FCStd")
    records = {}
    try:
        grip = doc.getObject("HandleGrip").Shape
        section, = grip.slice(App.Vector(1, 0, 0), 0)
        # Match the wrap crest at the end of the full-height grip section.
        surface = Part.Face(section)
        surface.scale(1.06, App.Vector(0, 172, 301.5))
        for sign, side in ((1, "Right"), (-1, "Left")):
            cap = surface.extrude(App.Vector(sign * 18, 0, 0))
            cap.translate(App.Vector(sign * 92, 0, 0))
            end = doc.getObject("HandleGripCuff" + side)
            shape = end.Shape.fuse(cap).removeSplitter()
            shape.check(True)
            if len(shape.Solids) != 1 or not shape.isClosed():
                raise ValueError(f"Open grip cuff on {side}")
            end.Shape = shape
        doc.recompute()
        doc.saveAs(str(geometry.resolve()))
    finally:
        App.closeDocument(doc.Name)
    display = ("GuiDocument.xml", "ShapeAppearance", "LineColorArray", "PointColorArray")
    with ZipFile(geometry) as shapes, ZipFile(args.base) as colors, ZipFile(args.output, "x") as out:
        for archive, gui in ((shapes, False), (colors, True)):
            for info in archive.infolist():
                if info.filename.startswith(display) == gui:
                    out.writestr(info, archive.read(info))
    geometry.unlink()
    doc = App.openDocument(str(args.output.resolve()))
    try:
        for side, wrap in (("Left", "GripBand0"), ("Right", "GripBand9")):
            cuff = doc.getObject("HandleGripCuff" + side).Shape
            cuff.check(True)
            contacts = {name: cuff.common(doc.getObject(name).Shape).Volume
                        for name in (wrap, "HandleGrip", "HandleArm" + side)}
            if min(contacts.values()) <= 0 or len(cuff.Solids) != 1 or not cuff.isClosed():
                raise ValueError(f"Invalid saved grip joint on {side}: {contacts}")
            records[side] = contacts
    finally:
        App.closeDocument(doc.Name)
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
