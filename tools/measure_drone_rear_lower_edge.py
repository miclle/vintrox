"""Verify the v40 lower-edge generator, selected candidate and saved BReps."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part

from drone_concept import raked_rear_parts, rounded_plate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def difference(a, b):
    return a.cut(b).Volume+b.cut(a).Volume


def main():
    parser = argparse.ArgumentParser()
    for name in ['model', 'candidate', 'baseline', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    baseline_hash = 'ea492d3652025456d2dcf20d264cc826f46d479edaf1a9fb3742ff9dcf70ebe3'
    assert digest(args.baseline) == baseline_hash
    model = App.openDocument(str(args.model))
    candidate = App.openDocument(str(args.candidate))
    baseline = App.openDocument(str(args.baseline))
    try:
        source = raked_rear_parts(134, outer_x=112.76)
        for side in (-1, 1):
            source['RearStructuralFrame'] = source['RearStructuralFrame'].cut(
                rounded_plate(13.5, 2.8, 2.1, (side*15.5-6.75, 246.7, 228), 1.3))
        names = ['RearServicePanel', 'RearStructuralFrame']
        generated = []; saved = []; upper = []
        scope = Part.makeBox(400, 400, 216, App.Vector(-200, 0, 84))
        for name in names:
            s = source[name]; c = candidate.getObject(name).Shape; m = model.getObject(name).Shape
            s.check(True); c.check(True); m.check(True)
            generated.append({'name': name, 'advanced_check_passed': True, 'symmetric_difference_mm3': difference(s, c)})
            saved.append({'name': name, 'valid': m.isValid(), 'solids': len(m.Solids),
                          'advanced_check_passed': True, 'symmetric_difference_mm3': difference(m, c)})
            upper.append({'name': name, 'scope_z_min_mm': 84,
                          'symmetric_difference_mm3': difference(m.common(scope), baseline.getObject(name).Shape.common(scope))})
        shafts = [{'name': o.Name, 'symmetric_difference_mm3': difference(o.Shape, model.getObject(o.Name).Shape)}
                  for o in baseline.Objects if o.Name.startswith('SupportShaft')]
        assert len(shafts) == 4 and all(x['symmetric_difference_mm3'] < 1e-6 for x in generated+saved+upper+shafts)
        assert all(x['valid'] and x['solids'] == 1 for x in saved)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output/'source-equivalence.json').write_text(json.dumps({
            'generator_sha256': digest(Path(__file__).with_name('drone_concept.py')),
            'baseline_fcstd_sha256': baseline_hash, 'candidate_fcstd_sha256': digest(args.candidate),
            'parts': generated, 'passed': True}, indent=2)+'\n')
        (args.output/'formal-geometry-check.json').write_text(json.dumps({
            'fcstd_sha256': digest(args.model), 'candidate_fcstd_sha256': digest(args.candidate),
            'measurement_script_sha256': digest(Path(__file__)), 'parts': saved,
            'shafts': shafts, 'upper_cladding_preservation': upper, 'passed': True}, indent=2)+'\n')
        print('Source, saved parts, upper cladding and four shafts passed', flush=True)
    finally:
        for doc in [model, candidate, baseline]:
            App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
