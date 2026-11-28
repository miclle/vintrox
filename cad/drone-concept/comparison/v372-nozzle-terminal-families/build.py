"""Install reference-aligned petal families on the v371 appearance model."""
import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile

import FreeCAD as App


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "donor", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    base = App.openDocument(str(args.base.resolve()))
    donor = App.openDocument(str(args.donor.resolve()))
    temporary = args.output.with_suffix(".headless.FCStd")
    families = {0, 1, 3, 4, 5, 6, 10, 11}
    changed = []
    try:
        for obj in base.Objects:
            match = re.fullmatch(r"NozzlePetal(?:EdgeRail|EndHem|Inset|Ridge|Guide|Hinge)?(\d+)(?:_\d+)?", obj.Name)
            if match and int(match[1]) in families:
                shape = donor.getObject(obj.Name).Shape.copy()
                shape.check(True)
                obj.Shape = shape
                changed.append(obj.Name)
        base.recompute()
        base.saveAs(str(temporary.resolve()))
    finally:
        App.closeDocument(donor.Name)
        App.closeDocument(base.Name)
    display = ("GuiDocument.xml", "ShapeAppearance", "LineColorArray", "PointColorArray")
    with ZipFile(temporary) as shapes, ZipFile(args.base) as colors, ZipFile(args.output, "x") as out:
        for archive, gui in ((shapes, False), (colors, True)):
            for info in archive.infolist():
                if info.filename.startswith(display) == gui:
                    out.writestr(info, archive.read(info))
    temporary.unlink()
    print(json.dumps(changed, indent=2))


if __name__ == "__main__":
    main()
