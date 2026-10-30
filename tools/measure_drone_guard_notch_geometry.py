"""Read back the two side guard parts and protected shaft geometry."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
from drone_guard_notch import trim_guard_notch


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def delta(a, b):
    return a.cut(b).Volume + b.cut(a).Volume


def main():
    parser = argparse.ArgumentParser()
    for name in ['model', 'candidate', 'baseline', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    baseline_hash = 'd03080846462cd5b8318f6dea254456fe77ece6cda06349ba698ea010086d591'
    assert digest(args.baseline) == baseline_hash
    model = App.openDocument(str(args.model))
    candidate = App.openDocument(str(args.candidate))
    baseline = App.openDocument(str(args.baseline))
    try:
        generated, saved = [], []
        for name, side in [('SideGuardLeft',-1),('SideGuardRight',1)]:
            shape=trim_guard_notch(baseline.getObject(name).Shape,side)
            other = candidate.getObject(name).Shape
            current = model.getObject(name).Shape
            for part in [shape, other, current]:
                part.check(True)
                assert part.isValid() and part.isClosed() and len(part.Solids) == 1
            generated.append({'name':name, 'advanced_check_passed':True,
                              'symmetric_difference_mm3':delta(shape, other)})
            saved.append({'name':name, 'valid':True, 'solids':1,
                          'advanced_check_passed':True,
                          'symmetric_difference_mm3':delta(current, other)})
        shafts = [{'name':o.Name, 'symmetric_difference_mm3':delta(o.Shape, model.getObject(o.Name).Shape)}
                  for o in baseline.Objects if o.Name.startswith('SupportShaft')]
        contacts = []
        for first, second in [('SideGuard'+side,prefix+side) for side in ['Left','Right']
                              for prefix in ['SideClosure','RearArmourCheek','CyanSideTube']]:
            a, b = model.getObject(first).Shape, model.getObject(second).Shape
            contacts.append({'objects':[first,second], 'gap_mm':a.distToShape(b)[0],
                             'overlap_mm3':a.common(b).Volume})
        assert len(shafts) == 4
        assert all(p['symmetric_difference_mm3'] < 1e-6 for p in generated+saved+shafts)
        assert all(p['gap_mm'] < .01 for p in contacts)
        args.output.mkdir(parents=True, exist_ok=True)
        source = {'generator_sha256':digest(Path(__file__).with_name('drone_concept.py')),
                  'source_module_sha256':digest(Path(__file__).with_name('drone_guard_notch.py')),
                  'baseline_fcstd_sha256':baseline_hash,
                  'candidate_fcstd_sha256':digest(args.candidate), 'parts':generated, 'passed':True}
        readback = {'fcstd_sha256':digest(args.model), 'candidate_fcstd_sha256':digest(args.candidate),
                    'measurement_script_sha256':digest(Path(__file__)), 'parts':saved,
                    'shafts':shafts, 'guard_contacts':contacts, 'passed':True}
        for filename, value in [('source-equivalence.json',source), ('formal-geometry-check.json',readback)]:
            (args.output/filename).write_text(json.dumps(value, indent=2)+'\n')
        print('Two source/saved parts, six contacts and four shafts passed')
    finally:
        for document in [model, candidate, baseline]:
            App.closeDocument(document.Name)


if __name__ == '__main__':
    main()
