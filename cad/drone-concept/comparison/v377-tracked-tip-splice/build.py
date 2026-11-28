"""Rebuild the mirrored terminal splices from the frame-180 triangulation."""
import argparse
import json
import re
from pathlib import Path

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, extend_tip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    records = json.loads(Path(__file__).with_name("triangulation.json").read_text())
    corner = next(row for row in records if row["frame"] == 180)
    frame = App.Placement(App.Vector(0, 180, 173),
                          App.Rotation(App.Vector(0, 0, 1), App.Vector(0, .574, -.819)))
    inverse = frame.inverse()
    old = inverse.multVec(App.Vector(*corner["nearest_hem_vertex"][2]))
    target = inverse.multVec(App.Vector(*corner["point_mm"]))
    station = 107
    slope = (target - old) * (1 / (old.z - station))
    pattern = re.compile(r"NozzlePetal(?:Inset|Ridge|EdgeRail|Guide|EndHem|Hinge)?(\d+)(?:_\d+)?")
    doc = App.openDocument(str(args.baseline.resolve()))
    try:
        for obj in doc.Objects:
            match = pattern.fullmatch(obj.Name)
            if not match or int(match[1]) not in (0, 4):
                continue
            index = int(match[1])
            local = App.Vector(slope.x if index == 0 else -slope.x, slope.y, slope.z)
            original = obj.Shape
            shape, bounds = extend_tip(original, frame, 1, station, leaf_index=index,
                                       ring_slope=local)
            if bounds is None:
                continue
            if (not shape.isValid() or not shape.isClosed()
                    or len(shape.Solids) != len(original.Solids)
                    or set(advanced_errors(shape)) - set(advanced_errors(original))):
                raise ValueError(obj.Name)
            obj.Shape = shape
        doc.recompute()
        doc.saveAs(str(args.output.resolve()))
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
