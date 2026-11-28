"""Rebuild the stepped eye artwork on the measured flat-screen plane."""
import argparse
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
    tmp = args.output.with_suffix(".headless.FCStd")
    # Widths and Z stations follow the front-view trace. Preserve the symmetric eye centres.
    try:
        for suffix, centre in (("_39", -33), ("27", 33)):
            bottom = Part.makeBox(5.3, .5, 4, App.Vector(centre-2.65, -9.6, 171.7))
            body = Part.makeBox(15, .5, 17.8, App.Vector(centre-7.5, -9.6, 175.7))
            cap = Part.makeBox(5.3, .5, 4.5, App.Vector(centre-2.65, -9.6, 193.5))
            doc.getObject("PixelEye" + suffix).Shape = body.fuse(bottom).removeSplitter()
            doc.getObject("PixelEyeTop" + suffix).Shape = cap
        doc.recompute()
        doc.saveAs(str(tmp.resolve()))
    finally:
        App.closeDocument(doc.Name)
    display = ("GuiDocument.xml", "ShapeAppearance", "LineColorArray", "PointColorArray")
    with ZipFile(tmp) as geometry, ZipFile(args.base) as colors, ZipFile(args.output, "x") as out:
        for archive, gui in ((geometry, False), (colors, True)):
            for info in archive.infolist():
                if info.filename.startswith(display) == gui:
                    out.writestr(info, archive.read(info))
    tmp.unlink()


if __name__ == "__main__":
    main()
