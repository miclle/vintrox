"""Screen inset changes to the saved rear cooling core."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import FreeCAD as App

from drone_concept import cooling_fin
from experiment_drone_petal_axial import advanced_errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--mesh', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--drop', type=float, choices=(1.5, 3.0), required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    mesh = json.loads(args.mesh.read_text())
    if mesh['fcstd_sha256'] != digest(args.base):
        raise ValueError('FCStd and mesh hashes differ')
    name = 'RearCoolingCore'
    matrix = App.Matrix()
    matrix.A11 = .84
    matrix.A22 = 1.25
    # Keep the core's bottom at Z=236 mm and open the gaps downward.
    matrix.A33 = 1 - args.drop / 28.2
    matrix.A34 = 236 - matrix.A33 * 256
    shape = cooling_fin(-90.25, 180.5, True).transformGeometry(matrix)
    payload = args.output / f'{name}.Shape.brp'
    shape.exportBrep(str(payload))
    model = args.output / 'candidate.FCStd'
    with ZipFile(args.base) as baseline, ZipFile(model, 'w', ZIP_DEFLATED) as saved:
        assert payload.name in baseline.namelist()
        for member in baseline.namelist():
            data = payload.read_bytes() if member == payload.name else baseline.read(member)
            saved.writestr(member, data)
    doc = App.openDocument(str(model.resolve()))
    try:
        shape = doc.getObject(name).Shape
        errors = advanced_errors(shape)
        if errors or not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1:
            raise ValueError(f'Saved core failed geometry checks: {errors}')
        contacts = {}
        for label in [f'RearCoolingFin{i}' for i in range(15)] + ['RearUpperClosure']:
            overlap = shape.common(doc.getObject(label).Shape).Volume
            if overlap <= 0:
                raise ValueError(f'Saved core lost contact with {label}')
            contacts[label] = overlap
        item = next(obj for obj in mesh['objects'] if obj['name'] == name)
        vertices, faces = shape.tessellate(.12)
        item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
        mesh['fcstd_sha256'] = digest(model)
        (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
        report = {'baseline_fcstd_sha256': digest(args.base),
                  'fcstd_sha256': mesh['fcstd_sha256'],
                  'changed_objects': [name], 'drop_mm': args.drop,
                  'fixed_bottom_mm': 236.0, 'contact_overlap_mm3': contacts,
                  'closed_solids': len(shape.Solids), 'advanced_geometry_errors': errors}
        (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
