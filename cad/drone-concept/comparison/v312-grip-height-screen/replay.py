"""Test a flatter grip wrap on the saved CAD about the grip centre."""

import argparse
from collections import Counter
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('base', 'mesh', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--height-scale', type=float, choices=(.94, .97), required=True)
    args = parser.parse_args()

    model_hash = digest(args.base)
    mesh = json.loads(args.mesh.read_text())
    if mesh['fcstd_sha256'] != model_hash:
        raise ValueError('Baseline mesh differs from saved CAD')
    args.output.mkdir(parents=True)
    saved_path = args.output / 'candidate.FCStd'
    names = ['HandleGrip', *(f'GripBand{index}' for index in range(10))]
    baseline = App.openDocument(str(args.base.resolve()))
    try:
        centre = 301.5
        matrix = App.Matrix()
        matrix.A33 = args.height_scale
        matrix.A34 = centre * (1 - args.height_scale)
        replacements = {
            name + '.Shape.brp': baseline.getObject(name).Shape
            .transformGeometry(matrix).exportBrepToString()
            for name in names
        }
        with ZipFile(args.base) as source, ZipFile(saved_path, 'w', ZIP_DEFLATED) as target:
            if not replacements.keys() <= set(source.namelist()):
                raise ValueError('Missing saved grip shapes')
            for member in source.namelist():
                data = replacements[member] if member in replacements else source.read(member)
                target.writestr(member, data)
        saved = App.openDocument(str(saved_path.resolve()))
        try:
            checks, contacts = [], []
            fixed = ('HandleArmLeft', 'HandleArmRight', 'HandleGripCuffLeft', 'HandleGripCuffRight')
            for item in mesh['objects']:
                name = item['name']
                if name not in names:
                    continue
                shape = saved.getObject(name).Shape
                original = baseline.getObject(name).Shape
                checks.append({
                    'name': name, 'valid': shape.isValid(), 'closed': shape.isClosed(),
                    'solids': len(shape.Solids), 'original_solids': len(original.Solids),
                    'errors': advanced_errors(shape), 'original_errors': advanced_errors(original),
                })
                for neighbor in fixed if name == 'HandleGrip' else ('HandleGrip',):
                    old = baseline.getObject(neighbor).Shape
                    new = saved.getObject(neighbor).Shape
                    contacts.append({'objects': [name, neighbor],
                                     'baseline_gap_mm': original.distToShape(old)[0],
                                     'gap_mm': shape.distToShape(new)[0]})
                vertices, faces = shape.tessellate(.12)
                item.update(vertices=[list(v) for v in vertices], faces=faces)
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(baseline.Name)
    mesh['fcstd_sha256'] = digest(saved_path)
    valid = all(row['valid'] and row['closed'] and row['solids'] == row['original_solids']
                and not (Counter(row['errors']) - Counter(row['original_errors']))
                for row in checks)
    joined = all(row['gap_mm'] <= max(.01, row['baseline_gap_mm'] + .001) for row in contacts)
    report = {'baseline_fcstd_sha256': model_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
              'script_sha256': digest(Path(__file__)), 'height_scale': args.height_scale,
              'centre_z_mm': centre, 'advanced_checks': checks, 'contacts': contacts,
              'geometry_checks_passed': valid, 'contacts_passed': joined}
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    if not valid or not joined:
        raise ValueError('Grip shape or contact checks failed')
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))


if __name__ == '__main__':
    main()
