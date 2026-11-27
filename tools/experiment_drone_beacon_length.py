"""Screen the rear beacon length with the mounting planes retained."""

import argparse
import json
from pathlib import Path

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest, signature


def check_solid(shape, name):
    if (not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1
            or advanced_errors(shape)):
        raise ValueError(f'Invalid beacon solid: {name}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('base', 'mesh', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--scale', type=float, required=True)
    args = parser.parse_args()
    if not 1 < args.scale <= 1.5:
        parser.error('--scale must be greater than 1 and at most 1.5')
    base_hash = digest(args.base)
    mesh = json.loads(args.mesh.read_text())
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('Baseline mesh does not match the saved model')
    args.output.mkdir(parents=True, exist_ok=False)
    candidate = args.output / 'candidate.FCStd'
    doc = App.openDocument(str(args.base.resolve()))
    originals = {obj.Name: obj.Shape.copy() for obj in doc.Objects
                 if hasattr(obj, 'Shape') and not obj.Shape.isNull()}
    assemblies = [
        ('RearBeacon' + suffix, 'RearBeaconBase' + suffix, 'RearBeaconLens' + suffix, bands)
        for suffix, bands in (
            ('_1', ['RearBeaconBand_1_' + str(index) for index in range(3)]),
            ('_001', [f'RearBeaconBand_1_00{index}' for index in range(1, 4)]),
        )
    ]
    changed = []
    try:
        for body, _, lens, bands in assemblies:
            bounds = originals[body].optimalBoundingBox(False, False)
            transform = App.Matrix()
            transform.A22 = args.scale
            transform.A24 = bounds.YMin * (1 - args.scale)
            for name in [body, *bands, lens]:
                if name == lens:
                    shape = originals[name].copy()
                    shape.translate(App.Vector(0, bounds.YLength * (args.scale - 1), 0))
                else:
                    shape = originals[name].transformGeometry(transform)
                check_solid(shape, name)
                doc.getObject(name).Shape = shape
                changed.append(name)
        doc.recompute()
        doc.saveAs(str(candidate.resolve()))
    finally:
        App.closeDocument(doc.Name)

    saved = App.openDocument(str(candidate.resolve()))
    contacts = []
    try:
        for name, original in originals.items():
            shape = saved.getObject(name).Shape
            if name in changed:
                check_solid(shape, name)
            elif signature(shape) != signature(original):
                raise ValueError(f'Unintended saved geometry change: {name}')
        for body, base, lens, bands in assemblies:
            lamp = saved.getObject(body).Shape
            for name in [base, lens, *bands]:
                other = saved.getObject(name).Shape
                gap = lamp.distToShape(other)[0]
                overlap = lamp.common(other).Volume
                if gap > .01 or (name in bands and overlap <= .01):
                    raise ValueError(f'Detached beacon joint: {name}')
                contacts.append({'objects': [body, name], 'gap_mm': gap,
                                 'overlap_mm3': overlap})
        for item in mesh['objects']:
            if item['name'] in changed:
                vertices, faces = saved.getObject(item['name']).Shape.tessellate(.12)
                item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
    finally:
        App.closeDocument(saved.Name)
    mesh['fcstd_sha256'] = digest(candidate)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
              'script_sha256': digest(Path(__file__)), 'axial_scale': args.scale,
              'changed_objects': changed, 'contacts': contacts,
              'new_advanced_check_failures': [], 'contact_regressions': []}
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
