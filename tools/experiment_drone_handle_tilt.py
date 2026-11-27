"""Test the rear-view handle width by tilting the saved side assemblies."""

import argparse
import json
import math
from pathlib import Path

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--angle', type=float, required=True,
                        help='Rotation in degrees: positive inward, negative outward')
    args = parser.parse_args()
    if not math.isfinite(args.angle) or not 0 < abs(args.angle) <= 2.5:
        parser.error('--angle magnitude must be finite and in (0, 2.5] degrees')
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output must be empty')
    base_hash = digest(args.base)
    mesh = json.loads(args.mesh.read_text())
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('mesh does not match saved baseline')

    changed, checks, contacts = [], [], []
    doc = App.openDocument(str(args.base.resolve()))
    try:
        for side, sign in (('Left', -1), ('Right', 1)):
            arm, inset, cuff = (prefix + side for prefix in
                                ('HandleArm', 'HandleInset', 'HandleGripCuff'))
            marks = [f'HandleMark{side}{i}' for i in range(3)]
            moving = [arm, inset, cuff, *marks]
            joints = [(arm, 'SideClosure' + side, True), (arm, 'HandleGrip', False),
                      (cuff, 'HandleGrip', False), (inset, arm, True),
                      *((mark, inset, True) for mark in marks)]
            names = set(moving) | {second for _, second, _ in joints}
            before = {name: doc.getObject(name).Shape for name in names}
            after = before.copy()
            # The axis passes just below the rounded arm root.
            pivot = App.Vector(sign * 116, 110, 220)
            axis = App.Vector(0, -sign, 0)
            for name in moving:
                previous = before[name]
                shape = previous.copy()
                shape.rotate(pivot, axis, args.angle)
                if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != len(previous.Solids):
                    raise ValueError(f'invalid solid after rotation: {name}')
                old_errors = advanced_errors(previous)
                errors = advanced_errors(shape)
                checks.append({'name': name, 'baseline_errors': old_errors, 'candidate_errors': errors})
                after[name] = shape
                doc.getObject(name).Shape = shape
                changed.append(name)
            for first, second, needs_overlap in joints:
                original_a, original_b = before[first], before[second]
                candidate_a, candidate_b = after[first], after[second]
                old_gap = original_a.distToShape(original_b)[0]
                gap = candidate_a.distToShape(candidate_b)[0]
                volume = candidate_a.common(candidate_b).Volume
                contacts.append({
                    'objects': [first, second], 'baseline_gap_mm': old_gap, 'gap_mm': gap,
                    'baseline_overlap_mm3': original_a.common(original_b).Volume,
                    'overlap_mm3': volume, 'requires_overlap': needs_overlap,
                    'failed': gap > max(.01, old_gap + 1e-5) or (needs_overlap and volume <= .01),
                })
        doc.recompute()
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output / 'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)

    # Finalization restores GUI state and retessellates the moving objects.
    mesh['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {
        'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
        'script_sha256': digest(Path(__file__)), 'angle_degrees': args.angle,
        'axis_pivots_world_mm': [[-116, 110, 220], [116, 110, 220]],
        'rotation_axes': [[0, 1, 0], [0, -1, 0]], 'changed_objects': sorted(changed),
        'advanced_checks': checks, 'contacts': contacts,
        'new_advanced_check_failures': [r['name'] for r in checks
                                        if r['baseline_errors'] != r['candidate_errors']],
        'contact_regressions': [r for r in contacts if r['failed']],
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('fcstd_sha256', 'new_advanced_check_failures', 'contact_regressions')}))


if __name__ == '__main__':
    main()
