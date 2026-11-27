"""Extend each saved small-pod shell towards its unchanged leaf ends."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest

HOSTS = ('ClosedBellyPan', 'BottomChassis', 'MainEnclosureShell')
SECTIONS = ('_1', '_001')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--extension', type=float, choices=(.25, 1, 2), required=True)
    args = parser.parse_args()
    model_hash = digest(args.base)
    mesh = json.loads(args.mesh.read_text(encoding='utf-8'))
    if mesh['fcstd_sha256'] != model_hash:
        raise ValueError('Mesh and model hashes differ')
    args.output.mkdir(parents=True)
    model = args.output / 'candidate.FCStd'

    base = App.openDocument(str(args.base.resolve()))
    try:
        changes = {}
        leaf_names = [obj.Name for obj in base.Objects if obj.Name.startswith('LowerPodRib')]
        for suffix in SECTIONS:
            shell_name, rim_name = 'LowerPod' + suffix, 'LowerPodRim' + suffix
            shell = base.getObject(shell_name).Shape.copy()
            rim = base.getObject(rim_name).Shape.copy()
            frame = shell.Placement
            shell.Placement = App.Placement()
            matrix = App.Matrix()
            matrix.A33 = 1 + args.extension / 36
            shell = shell.transformGeometry(matrix)
            shell.Placement = frame.multiply(shell.Placement)
            rim.translate(frame.Rotation.multVec(App.Vector(0, 0, args.extension)))
            changes.update({shell_name: shell, rim_name: rim})

        replacements = {f'{name}.Shape.brp': shape.exportBrepToString()
                        for name, shape in changes.items()}
        with ZipFile(args.base) as source, ZipFile(model, 'w', ZIP_DEFLATED) as output:
            if not replacements.keys() <= set(source.namelist()):
                raise ValueError('Missing saved shell or ring BRep')
            for name in source.namelist():
                output.writestr(name, replacements[name] if name in replacements else source.read(name))

        saved = App.openDocument(str(model.resolve()))
        try:
            parts, joints = {}, []
            for item in mesh['objects']:
                name = item['name']
                if name not in changes:
                    continue
                original = base.getObject(name).Shape
                shape = saved.getObject(name).Shape
                before, after = advanced_errors(original), advanced_errors(shape)
                if (before != after or not shape.isValid() or not shape.isClosed()
                        or len(shape.Solids) != len(original.Solids)):
                    raise ValueError(f'Invalid saved BRep: {name}')
                parts[name] = {'solids': len(shape.Solids), 'advanced_errors': after}
                points, faces = shape.tessellate(.12)
                item.update(vertices=[list(point) for point in points], faces=faces)

            for suffix in SECTIONS:
                shell, rim = 'LowerPod' + suffix, 'LowerPodRim' + suffix
                sign = -1 if suffix == '_1' else 1
                pairs = [(shell, target) for target in (*HOSTS, 'LowerPodClamp' + suffix, rim)]
                for leaf in leaf_names:
                    if sign * base.getObject(leaf).Shape.Solids[0].CenterOfMass.x > 0:
                        pairs.extend(((shell, leaf), (rim, leaf)))
                for first, second in pairs:
                    before_a, before_b = (base.getObject(name).Shape for name in (first, second))
                    after_a, after_b = (saved.getObject(name).Shape for name in (first, second))
                    before_gap = before_a.distToShape(before_b)[0]
                    after_gap = after_a.distToShape(after_b)[0]
                    before_overlap = before_a.common(before_b).Volume
                    after_overlap = after_a.common(after_b).Volume
                    joints.append({'objects': [first, second], 'baseline_gap_mm': before_gap,
                                   'gap_mm': after_gap, 'baseline_overlap_mm3': before_overlap,
                                   'overlap_mm3': after_overlap})
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(base.Name)

    mesh['fcstd_sha256'] = digest(model)
    report = {'baseline_fcstd_sha256': model_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
              'extension_at_rim_mm': args.extension, 'parts': parts, 'contacts': joints}
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    if any(j['baseline_gap_mm'] <= .01 < j['gap_mm'] for j in joints):
        raise ValueError('An existing contact became separated')
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))


if __name__ == '__main__':
    main()
