"""Measure the saved axial extents and adjacent-pair clearances."""
import argparse
import json
from pathlib import Path
import re

import FreeCAD as App


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    docs = [App.openDocument(str(path.resolve())) for path in (args.baseline,args.candidate)]
    try:
        frame = App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),App.Vector(0,.574,-.819)))
        checks, contacts = [], []
        for obj in docs[0].Objects:
            match = re.fullmatch(r"NozzlePetal(?:Inset|Ridge|EdgeRail|Guide|EndHem|Hinge)?(\d+)(?:_\d+)?",obj.Name)
            if not match:
                continue
            ends = []
            for doc in docs:
                shape = doc.getObject(obj.Name).Shape.copy()
                shape.Placement = frame.inverse().multiply(shape.Placement)
                box = shape.optimalBoundingBox(False, False)
                ends.append([box.ZMin, box.ZMax])
            checks.append(dict(name=obj.Name, axial_bounds_mm=ends))
            leaf = f"NozzlePetal{match[1]}"
            others = ["BassNozzleMouthRing", "BassNozzleShell"] if leaf == obj.Name else [obj.Name]
            for other in others:
                gaps = [doc.getObject(leaf).Shape.distToShape(doc.getObject(other).Shape)[0] for doc in docs]
                contacts.append(dict(objects=[leaf,other], gap_mm=gaps))
        print(json.dumps(dict(axial=checks, contacts=contacts),indent=2))
    finally:
        for doc in docs:
            App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
