"""Independently compare saved petal roots below an axial splice station."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--check', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check = json.loads(args.check.read_text())
    if check['fcstd_sha256'] != digest(args.candidate):
        raise ValueError('candidate differs from construction record')
    if check['baseline_fcstd_sha256'] != digest(args.baseline):
        raise ValueError('baseline differs from construction record')
    station = check['fixed_station_mm']
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    frame = App.Placement(App.Vector(0, 180, 173),
                          App.Rotation(App.Vector(0, 0, 1), axis))
    # Exclude the seam by 0.01 mm to avoid coincident-face boolean ambiguity.
    clip = Part.makeBox(400, 400, station+200-.01,
                        App.Vector(-200, -200, -200))
    candidate = App.openDocument(str(args.candidate.resolve()))
    baseline = App.openDocument(str(args.baseline.resolve()))
    rows = []
    try:
        for name in check['changed_objects']:
            first = candidate.getObject(name).Shape.copy()
            second = baseline.getObject(name).Shape.copy()
            first.Placement = frame.inverse().multiply(first.Placement)
            second.Placement = frame.inverse().multiply(second.Placement)
            first, second = first.common(clip), second.common(clip)
            delta = abs(first.cut(second).Volume)+abs(second.cut(first).Volume)
            rows.append({'name': name, 'root_symmetric_difference_mm3': delta})
    finally:
        App.closeDocument(candidate.Name)
        App.closeDocument(baseline.Name)
    passed = all(row['root_symmetric_difference_mm3'] < 1e-6 for row in rows)
    result = {'candidate_fcstd_sha256': digest(args.candidate),
              'baseline_fcstd_sha256': digest(args.baseline),
              'script_sha256': digest(Path(__file__)),
              'check': 'independent symmetric volume difference below splice station minus 0.01mm',
              'station_mm': station, 'threshold_mm3': 1e-6,
              'passed': passed, 'rows': rows}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('roots checked', len(rows), 'passed', passed)
    if not passed:
        raise SystemExit('root geometry changed')


if __name__ == '__main__':
    main()
