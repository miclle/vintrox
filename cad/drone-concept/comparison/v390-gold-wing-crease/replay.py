"""Rebuild the three gold-wing fold solids from the v388 saved assembly."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App

from drone_wing_fold import WING_OUTLINE, GOLD_WING_REAR_STATION_WEIGHTS, gold_wing_fold_parts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.model.read_bytes()).hexdigest() != '72b9c0673e8d980ff7c779c4cb084fc5f8872c46ec546a81ee3f99d372413e88':
        raise ValueError('Expected v388 saved model')
    args.output.mkdir(exist_ok=False, parents=True)
    comparison = Path(__file__).resolve().parents[1]
    pose = json.loads((comparison / 'v306-wing-pose/half-angle.json').read_text())
    centre = App.Vector(*pose['hub_centres_mm']['Right'])
    offsets = {1: .5, 2: 5.5, 3: 2.5, 4: 2, 14: 2.8, 15: 3.8, 16: 1}
    outline = [(y + offsets.get(i, 0) - 5 * GOLD_WING_REAR_STATION_WEIGHTS.get(i, 0), z)
               for i, (y, z) in enumerate(WING_OUTLINE)]
    shapes = gold_wing_fold_parts(outline, crease_corner=(132.02, 230.14))
    baseline = App.openDocument(str(args.model.resolve()))
    for shape in shapes.values():
        for axis, angle in zip(((1, 0, 0), (0, 1, 0)), pose['angles_deg'], strict=True):
            shape.rotate(centre, App.Vector(*axis), angle)
        shape.check(True)
        if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1:
            raise ValueError('Invalid fold solid')
    joints = [('WingEdgeRight', 'WingFoldFacetRight'), ('WingEdgeRight', 'WingRaisedFaceRight'),
              ('WingFoldFacetRight', 'WingRaisedFaceRight'), ('WingFoldFacetRight', 'WingPaintRight'),
              ('WingRaisedFaceRight', 'WingPaintRight'), ('WingPaintRight', 'WingHubMarkRight')]
    distances = []
    for first, second in joints:
        old = [baseline.getObject(n).Shape for n in (first, second)]
        new = [shapes.get(n, original) for n, original in zip((first, second), old)]
        before = old[0].distToShape(old[1])[0]
        after = new[0].distToShape(new[1])[0]
        if after > max(.01, before + 1e-5):
            raise ValueError((first, second, before, after))
        distances.append(dict(objects=[first, second], before_mm=before, after_mm=after))
    # Save through FreeCAD so the document's topology metadata follows the new solids.
    for name, shape in shapes.items():
        baseline.getObject(name).Shape = shape
    baseline.recompute()
    baseline.saveAs(str((args.output / 'geometry.FCStd').resolve()))
    App.closeDocument(baseline.Name)
    (args.output / 'joints.json').write_text(json.dumps(distances, indent=2) + '\n')


if __name__ == '__main__':
    main()
