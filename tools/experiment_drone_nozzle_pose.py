"""Rotate the saved rear nozzle assembly together about its root mounting axis."""
import argparse
import json
import math
from pathlib import Path

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest


# Baseline joints into the fixed rear housing. Internal joints move together.
HOUSING_JOINTS = {
    'BassNozzleRearCollar': ('MainEnclosureShell', 'RearServicePanel', 'RearRailCarrier'),
    'BassNozzleShell': ('MainEnclosureShell', 'RearServicePanel', 'RearStructuralFrame',
                        'RearRecessLiner', 'RearRailCarrier', 'RearLowerSlope'),
    'BassChamberBackplate': ('MainEnclosureShell',),
    'WooferMountSeat': ('MainEnclosureShell',),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--angle', type=float, required=True, help='Signed angle about model X in degrees')
    args = parser.parse_args()
    if not math.isfinite(args.angle) or not 0 < abs(args.angle) <= 12:
        parser.error('angle must be finite, nonzero, and within 12 degrees')
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output must be empty')

    mesh = json.loads(args.mesh.read_text())
    base_hash = digest(args.base)
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('mesh does not match saved baseline')

    pivot = App.Vector(*mesh['bass_origin_mm'])
    axis = App.Vector(1, 0, 0)
    rotation = App.Rotation(axis, args.angle)
    doc = App.openDocument(str(args.base.resolve()))
    parts, contacts = [], []
    try:
        moving = [obj for obj in doc.Objects if obj.Name.startswith(('Bass', 'Nozzle', 'Woofer'))
                  and hasattr(obj, 'Shape') and not obj.Shape.isNull()]
        before = {obj.Name: obj.Shape.copy() for obj in moving}
        if not all(name in before for name in HOUSING_JOINTS) or len(moving) != 143:
            raise ValueError(f'unexpected nozzle assembly ({len(moving)} shapes)')
        for obj in moving:
            old = before[obj.Name]
            rotated = old.copy()
            rotated.rotate(pivot, axis, args.angle)
            if (not rotated.isValid() or not rotated.isClosed()
                    or len(rotated.Solids) != len(old.Solids)):
                raise ValueError(f'invalid rotated solid: {obj.Name}')
            baseline_errors = advanced_errors(old)
            candidate_errors = advanced_errors(rotated)
            obj.Shape = rotated
            parts.append({'name': obj.Name, 'baseline_errors': baseline_errors,
                          'candidate_errors': candidate_errors})

        for name, targets in HOUSING_JOINTS.items():
            moved = doc.getObject(name).Shape
            for target in targets:
                fixed = doc.getObject(target).Shape
                old_overlap = before[name].common(fixed).Volume
                overlap = moved.common(fixed).Volume
                gap = moved.distToShape(fixed)[0]
                contacts.append({'objects': [name, target], 'baseline_overlap_mm3': old_overlap,
                                 'overlap_mm3': overlap, 'gap_mm': gap,
                                 'regressed': gap > .01 or overlap < .01})

        reserve = doc.getObject('WooferEnvelope_D88_Depth40').Shape
        shell = doc.getObject('BassNozzleShell').Shape
        reserve_overlap = reserve.common(shell).Volume
        doc.recompute()
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output / 'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)

    # The finalizer restores the saved GUI state and tessellates the moved BReps.
    mesh['fcstd_sha256'] = digest(model)
    mesh['bass_axis'] = list(rotation.multVec(App.Vector(*mesh['bass_axis'])))
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {
        'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
        'script_sha256': digest(Path(__file__)), 'angle_degrees': args.angle,
        'axis_world': list(axis), 'pivot_world_mm': list(pivot),
        'candidate_bass_axis': mesh['bass_axis'], 'parts': parts,
        'changed_objects': sorted(before), 'housing_joints': contacts,
        'woofer_shell_overlap_mm3': reserve_overlap,
        'new_advanced_check_failures': [row['name'] for row in parts
                                       if row['baseline_errors'] != row['candidate_errors']],
        'contact_regressions': [row for row in contacts if row['regressed']],
    }
    if reserve_overlap > 1e-6:
        report['contact_regressions'].append({'objects': ['WooferEnvelope_D88_Depth40',
                                                          'BassNozzleShell'],
                                              'overlap_mm3': reserve_overlap})
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('fcstd_sha256', 'new_advanced_check_failures',
                                                   'contact_regressions')}))


if __name__ == '__main__':
    main()
