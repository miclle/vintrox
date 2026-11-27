"""Rebuild both roof ribs at a lower height with the same mounting plane."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--height', type=float, choices=(3.0, 4.5), required=True)
    args = parser.parse_args()

    mesh = json.loads(args.mesh.read_text())
    baseline_hash = digest(args.base)
    if mesh['fcstd_sha256'] != baseline_hash:
        raise ValueError('Baseline mesh does not match the saved CAD')
    args.output.mkdir(parents=True, exist_ok=False)
    model = args.output / 'candidate.FCStd'
    names = ('RoofRaisedRib0', 'RoofRaisedRib1')
    records = {}
    baseline = App.openDocument(str(args.base.resolve()))
    try:
        panel = baseline.getObject('RoofAccessPanel').Shape
        for name in names:
            shape = baseline.getObject(name).Shape
            bounds = shape.optimalBoundingBox(False, False)
            matrix = App.Matrix()
            matrix.A33 = args.height / bounds.ZLength
            matrix.A34 = bounds.ZMin * (1 - matrix.A33)
            rib = shape.transformGeometry(matrix)
            rib.exportBrep(str(args.output / f'{name}.Shape.brp'))
            records[name] = {'base_gap_mm': shape.distToShape(panel)[0],
                             'base_height_mm': bounds.ZLength,
                             'fixed_bottom_mm': bounds.ZMin}
        with ZipFile(args.base) as source, ZipFile(model, 'w', ZIP_DEFLATED) as target:
            replacements = {f'{name}.Shape.brp' for name in names}
            if not replacements.issubset(source.namelist()):
                raise ValueError('Missing stored rib geometry')
            for member in source.namelist():
                data = ((args.output / member).read_bytes()
                        if member in replacements else source.read(member))
                target.writestr(member, data)

        saved = App.openDocument(str(model.resolve()))
        try:
            for name, record in records.items():
                shape = saved.getObject(name).Shape
                errors = advanced_errors(shape)
                bbox = shape.optimalBoundingBox(False, False)
                gap = shape.distToShape(panel)[0]
                if (errors or not shape.isValid() or len(shape.Solids) != 1
                        or not shape.isClosed() or abs(bbox.ZLength - args.height) > 1e-6
                        or gap > record['base_gap_mm'] + 1e-6):
                    raise ValueError(f'Rib geometry or attachment changed unexpectedly: {name}')
                record.update(height_mm=bbox.ZLength, panel_gap_mm=gap,
                              advanced_errors=errors, closed_solid=True)
                item = next(item for item in mesh['objects'] if item['name'] == name)
                points, faces = shape.tessellate(.12)
                item.update(vertices=[list(point) for point in points], faces=faces)
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(baseline.Name)

    mesh['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {'baseline_fcstd_sha256': baseline_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
              'changed_objects': list(names), 'ribs': records}
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
