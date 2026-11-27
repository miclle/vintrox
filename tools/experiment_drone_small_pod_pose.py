"""Reposition the saved small-pod assemblies symmetrically about their roots."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest, signature


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offset', type=float, nargs=3, required=True,
                        metavar=('X', 'Y', 'Z'))
    parser.add_argument('--rotation-vector', type=float, nargs=3, required=True,
                        metavar=('RX', 'RY', 'RZ'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = App.openDocument(str(args.base.resolve()))
    baseline_hash = digest(args.base)
    records = []
    roots = {}
    try:
        for side, suffix in [(-1, '_1'), (1, '_001')]:
            pivot = baseline.getObject('LowerPod' + suffix).Shape.Placement.Base
            x, y, z = args.offset
            rx, ry, rz = args.rotation_vector
            axis = App.Vector(rx, side * ry, side * rz)
            rotation = App.Rotation(axis, axis.Length) if axis.Length else App.Rotation()
            delta = pivot + App.Vector(side * x, y, z) - rotation.multVec(pivot)
            roots[side] = App.Placement(delta, rotation)

        originals = {obj.Name: obj.Shape.copy() for obj in baseline.Objects
                     if hasattr(obj, 'Shape') and not obj.Shape.isNull()}
        changed = {name for name in originals if name.startswith('LowerPod')}
        if len(changed) != 152:
            raise ValueError(f'Expected 152 small-pod objects, found {len(changed)}')
        for name in changed:
            shape = originals[name].copy()
            side = -1 if shape.Solids[0].CenterOfMass.x < 0 else 1
            shape.Placement = roots[side].multiply(shape.Placement)
            baseline.getObject(name).Shape = shape
        baseline.recompute()
        model = args.output / 'candidate.FCStd'
        baseline.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(baseline.Name)

    # FreeCAD can reserialize unrelated BReps even when their shapes are equal.
    # Retain the original members so only the pod geometry can affect rendering.
    restored = model.with_suffix('.restored')
    with (ZipFile(args.base) as source, ZipFile(model) as candidate,
          ZipFile(restored, 'w', compression=ZIP_DEFLATED) as output):
        preserved_members = {
            name for name in source.namelist()
            if (name.endswith('.brp') or '.Shape.Map.' in name)
            and name.split('.Shape.')[0] not in changed
        }
        for name in candidate.namelist():
            archive = source if name in preserved_members else candidate
            output.writestr(name, archive.read(name))
    restored.replace(model)

    saved = App.openDocument(str(model.resolve()))
    try:
        for name, original in originals.items():
            shape = saved.getObject(name).Shape
            if name not in changed:
                if signature(shape) != signature(original):
                    raise ValueError(f'Unintended saved shape change: {name}')
                continue
            side = -1 if original.Solids[0].CenterOfMass.x < 0 else 1
            expected = original.copy()
            expected.Placement = roots[side].multiply(expected.Placement)
            if (signature(shape) != signature(expected) or not shape.isValid()
                    or not shape.isClosed() or len(shape.Solids) != len(original.Solids)):
                raise ValueError(f'Failed rigid-placement readback: {name}')
            before = advanced_errors(original)
            after = advanced_errors(shape)
            records.append({'object': name, 'baseline_advanced_errors': before,
                            'candidate_advanced_errors': after})
        mounts = []
        for name in sorted(changed):
            if not name.startswith(('LowerPod_', 'LowerPodClamp')):
                continue
            shape = saved.getObject(name).Shape
            for host in ('MainEnclosureShell', 'BottomChassis', 'ClosedBellyPan',
                         'RearLowerSlope'):
                mounts.append({
                    'objects': [name, host],
                    'baseline_overlap_mm3': originals[name].common(originals[host]).Volume,
                    'candidate_overlap_mm3': shape.common(originals[host]).Volume,
                })
        support_overlaps = []
        supports = {name: shape for name, shape in originals.items()
                    if name.startswith(('Support', 'CentralSupport'))}
        for name in sorted(changed):
            shape = saved.getObject(name).Shape
            for support, solid in supports.items():
                if not shape.BoundBox.intersect(solid.BoundBox):
                    continue
                before = originals[name].common(solid).Volume
                after = shape.common(solid).Volume
                if before > 1e-6 or after > 1e-6:
                    support_overlaps.append({'objects': [name, support],
                                             'baseline_overlap_mm3': before,
                                             'candidate_overlap_mm3': after})
    finally:
        App.closeDocument(saved.Name)

    report = {
        'baseline_fcstd_sha256': baseline_hash,
        'fcstd_sha256': digest(model),
        'script_sha256': digest(Path(__file__)),
        'offset_right_mm': args.offset,
        'rotation_vector_right_deg': args.rotation_vector,
        'changed_objects': sorted(changed),
        'preserved_shape_count': len(originals) - len(changed),
        'preserved_geometry_archive_members': len(preserved_members),
        'new_advanced_check_failures': sorted(
            record['object'] for record in records
            if set(record['candidate_advanced_errors']) - set(record['baseline_advanced_errors'])
        ),
        'mount_overlaps': mounts,
        'support_overlaps': support_overlaps,
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
