"""Check saved small-pod contacts and retained terminal arcs independently."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for n in ['model', 'baseline', 'output']:
        parser.add_argument('--'+n, type=Path, required=True)
    args = parser.parse_args()
    saved = App.openDocument(str(args.model.resolve()))
    baseline = App.openDocument(str(args.baseline.resolve()))
    records, contacts = [], []
    try:
        groups = {}
        for obj in saved.Objects:
            if not obj.Name.startswith('LowerPod'):
                continue
            side = -1 if obj.Shape.Placement.Base.x < 0 else 1
            groups.setdefault(side, []).append(obj)
        for side, objects in groups.items():
            shell = next(o for o in objects if o.Name.startswith('LowerPod_'))
            rim = next(o for o in objects if o.Name.startswith('LowerPodRim'))
            clamp = next(o for o in objects if o.Name.startswith('LowerPodClamp'))
            diaphragm = next(o for o in objects if o.Name.startswith('LowerPodDiaphragm'))
            pairs = [(shell, rim), (shell, clamp)]
            for obj in objects:
                shape = obj.Shape.copy()
                shape.Placement = App.Placement()
                previous = baseline.getObject(obj.Name).Shape.copy()
                previous.Placement = App.Placement()
                assert obj.Shape.isValid() and obj.Shape.isClosed()
                assert advanced_errors(obj.Shape) == advanced_errors(baseline.getObject(obj.Name).Shape)
                if obj.Name.startswith(('LowerPodRib', 'LowerPodPetalRidge', 'LowerPodEdgeRail')):
                    centre = shape.Solids[0].CenterOfMass
                    index = int((math.degrees(math.atan2(centre.y, centre.x)) % 360)//20)
                    if obj.Name.startswith('LowerPodRib'):
                        # Terminal cross-sections are cut from saved solids,
                        # including actual angular gaps and recess geometry.
                        box = Part.makeBox(100, 100, .001, App.Vector(-50, -50, 52.999))
                        first, second = shape.common(box), previous.common(box)
                        delta = first.cut(second).Volume+second.cut(first).Volume
                        records.append({'name': obj.Name, 'terminal_slice_difference_mm3': delta,
                                        'regressed': delta >= 1e-6})
                        pairs += [(obj, shell), (obj, rim), (obj, diaphragm)]
                        for detail in objects:
                            if not detail.Name.startswith(('LowerPodPetalRidge', 'LowerPodEdgeRail')):
                                continue
                            local = detail.Shape.copy()
                            local.Placement = App.Placement()
                            c = local.Solids[0].CenterOfMass
                            other_index = int((math.degrees(math.atan2(c.y, c.x)) % 360)//20)
                            if index == other_index:
                                pairs.append((obj, detail))
            for first, second in pairs:
                gap = first.Shape.distToShape(second.Shape)[0]
                old = baseline.getObject(first.Name).Shape.distToShape(baseline.getObject(second.Name).Shape)[0]
                contacts.append({'objects': [first.Name, second.Name], 'gap_mm': gap,
                                 'baseline_gap_mm': old, 'regressed': gap > max(.01, old+1e-5)})
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(baseline.Name)
    regressions = [r for r in contacts if r['regressed']]
    terminal_regressions = [r for r in records if r['regressed']]
    result = {'fcstd_sha256': digest(args.model), 'baseline_fcstd_sha256': digest(args.baseline),
              'script_sha256': digest(Path(__file__)), 'terminal_slices': records,
              'terminal_regressions': terminal_regressions,
              'terminal_slice_tolerance_mm3': 1e-6,
              'contacts': contacts, 'contact_regressions': regressions,
              'limitations': ['terminal 0.001 mm slice comparison; not the entire leaf shape',
                             'contact gaps compare CAD solids only; no manufacturing tolerance or physical acceptance']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('terminal checks', len(records), 'terminal regressions', len(terminal_regressions),
          'contacts', len(contacts), 'contact regressions', len(regressions))
    if regressions or terminal_regressions:
        raise SystemExit('small-pod terminal or contact regression; see report')


if __name__ == '__main__':
    main()
