"""Contract each complete leaf assembly around its hinge in the nozzle frame."""
import argparse
import json
from pathlib import Path
import re
from zipfile import ZipFile

import FreeCAD as App
import Part


def radial_tangent(centre, frame):
    position = frame.inverse().multVec(centre)
    radius = App.Vector(position.x, position.y, 0)
    return frame.Rotation.multVec(App.Vector(-radius.y, radius.x, 0).normalize())


def width_matrix(centre, tangent, factor):
    matrix = App.Matrix()
    # I + (k-1) tt^T scales only the tangential component.
    for row in range(3):
        for col in range(3):
            setattr(matrix, f"A{row+1}{col+1}", int(row == col) + (factor-1)*tangent[row]*tangent[col])
    shift = tangent * ((1-factor) * tangent.dot(centre))
    matrix.A14, matrix.A24, matrix.A34 = tuple(shift)
    return matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    doc = App.openDocument(str(args.base.resolve()))
    temporary = args.output.with_suffix(".headless.FCStd")
    try:
        frame = App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),App.Vector(0,.574,-.819)))
        axes = [doc.getObject(f"NozzlePetalHinge{i}").Shape for i in range(12)]
        centres = [sum((s.CenterOfMass * s.Volume for s in axis.Solids), App.Vector()) / axis.Volume
                   for axis in axes]
        transforms = [width_matrix(c, radial_tangent(c, frame), .96) for c in centres]
        before = {}
        for obj in doc.Objects:
            if not obj.Name.startswith("NozzlePetal"):
                continue
            match = re.fullmatch(r"NozzlePetal(?:Inset|Ridge|EdgeRail|Guide|EndHem|Hinge)?(\d+)(?:_\d+)?",obj.Name)
            if match is None:
                raise ValueError(obj.Name)
            old = obj.Shape
            before[obj.Name] = (len(old.Solids), old.Volume)
            shape = old.transformGeometry(transforms[int(match[1])])
            if not shape.isValid():
                solids = shape.Solids
                for solid in solids:
                    if not solid.isValid():
                        solid.fix(1e-7, 1e-7, 1e-4)
                shape = Part.makeCompound(solids) if len(solids) > 1 else solids[0]
            obj.Shape = shape
        doc.recompute()
        doc.saveAs(str(temporary.resolve()))
    finally:
        App.closeDocument(doc.Name)
    display = ("GuiDocument.xml", "ShapeAppearance", "LineColorArray", "PointColorArray")
    with ZipFile(temporary) as geometry, ZipFile(args.base) as colors, ZipFile(args.output, "x") as out:
        for archive, gui in ((geometry, False), (colors, True)):
            for info in archive.infolist():
                if info.filename.startswith(display) == gui:
                    out.writestr(info, archive.read(info))
    temporary.unlink()
    doc = App.openDocument(str(args.output.resolve()))
    try:
        maximum_error = 0
        for name, (count, volume) in before.items():
            shape = doc.getObject(name).Shape
            error = abs(shape.Volume / volume - .96)
            if len(shape.Solids) != count or not shape.isValid() or not shape.isClosed() or error > .001:
                raise ValueError(f"Saved affine shape differs: {name}, {count}, {len(shape.Solids)}, {error}")
            maximum_error = max(maximum_error,error)
        if len(before)!=108:
            raise ValueError("Incomplete petal families")
        print(json.dumps(dict(objects=len(before), factor=.96, maximum_volume_ratio_error=maximum_error,
                              solid_counts_preserved=True),indent=2))
    finally:
        App.closeDocument(doc.Name)


if __name__=="__main__":
    main()
