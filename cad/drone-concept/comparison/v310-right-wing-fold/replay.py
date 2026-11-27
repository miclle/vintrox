"""Rebuild the gold wing's rear boundary from its source profile stations."""

import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App

from drone_concept import curved_wing_plate
from drone_wing_fold import GOLD_WING_REAR_STATION_WEIGHTS, gold_wing_rear_parts
from experiment_drone_petal_axial import advanced_errors

JOINTS = [
    ('WingEdgeRight', 'WingInnerPaintRight'),
    ('WingEdgeRight', 'WingFoldFacetRight'),
    ('WingEdgeRight', 'WingRaisedFaceRight'),
    ('WingEdgeRight', 'WingHubSeatRight'),
    ('WingInnerPaintRight', 'WingSpineRight'),
    ('WingFoldFacetRight', 'WingRaisedFaceRight'),
    ('WingFoldFacetRight', 'WingPaintRight'),
    ('WingRaisedFaceRight', 'WingPaintRight'),
    ('WingPaintRight', 'WingHubMarkRight'),
]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('base', 'mesh', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--pose', type=Path, required=True)
    parser.add_argument('--fit', type=Path, required=True)
    parser.add_argument('--scale', type=float, choices=(.5, 1.0), required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty output directory')
    baseline_hash = digest(args.base)
    mesh = json.loads(args.mesh.read_text())
    if mesh['fcstd_sha256'] != baseline_hash:
        raise ValueError('Baseline FCStd and mesh binding differ')
    doc = App.openDocument(str(args.base.resolve()))
    fit = json.loads(args.fit.read_text())
    pose = json.loads(args.pose.read_text())
    centre = App.Vector(*pose['hub_centres_mm']['Right'])
    front_offsets = {
        station: offset + args.scale * delta for station, offset, delta in zip(
            fit['stations'], fit['nominal_offsets_local_y_mm'], fit['delta_local_y_mm'],
            strict=True,
        )
    }
    changed = gold_wing_rear_parts(5, curved_wing_plate, front_offsets)
    for shape in changed.values():
        shape.rotate(centre, App.Vector(1, 0, 0), pose['angles_deg'][0])
        shape.rotate(centre, App.Vector(0, 1, 0), pose['angles_deg'][1])
    checks, contacts = [], []
    try:
        names = set(changed).union(*(set(pair) for pair in JOINTS))
        old = {name: doc.getObject(name).Shape for name in names}
        for name, shape in changed.items():
            if not shape.isValid() or len(shape.Solids) != 1 or not shape.isClosed():
                raise ValueError(f'Expected a valid closed solid: {name}')
            errors = advanced_errors(shape)
            checks.append({'name': name, 'baseline_errors': advanced_errors(old[name]),
                           'candidate_errors': errors})
            doc.getObject(name).Shape = shape
        doc.recompute()
        for first, second in JOINTS[:9 if front_offsets else 7]:
            old_first, old_second = old[first], old[second]
            a, b = doc.getObject(first).Shape, doc.getObject(second).Shape
            gap = a.distToShape(b)[0]
            previous_gap = old_first.distToShape(old_second)[0]
            contacts.append({'objects': [first, second], 'gap_mm': gap,
                             'baseline_gap_mm': previous_gap,
                             'overlap_mm3': a.common(b).Volume,
                             'baseline_overlap_mm3': old_first.common(old_second).Volume,
                             'regressed': gap > max(.01, previous_gap+1e-5)})
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output/'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)
    # The finalizer restores the saved palette and retessellates changed shapes
    # from the final reopened document before comparing or exporting.
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {
        'baseline_fcstd_sha256': baseline_hash,
        'fcstd_sha256': mesh['fcstd_sha256'],
        'script_sha256': digest(Path(__file__)),
        'changed_objects': sorted(changed),
        'inset_local_mm': 5,
        'fit_sha256': digest(args.fit),
        'pose_sha256': digest(args.pose),
        'fit_scale': args.scale,
        'rear_station_weights': GOLD_WING_REAR_STATION_WEIGHTS,
        'front_offsets_local_mm': front_offsets,
        'advanced_checks': checks,
        'contacts': contacts,
        'new_advanced_check_failures': [r for r in checks if r['candidate_errors']],
        'contact_regressions': [r for r in contacts if r['regressed']],
        'status': 'geometry diagnostic pending final readback and rendering',
    }
    (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('fcstd_sha256', 'new_advanced_check_failures', 'contact_regressions')}))


if __name__ == '__main__':
    main()
