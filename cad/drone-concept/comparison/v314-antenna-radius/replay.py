"""Rebuild the saved antenna from a centreline in final assembly coordinates."""

import argparse
import json
from pathlib import Path

import FreeCAD as App

from drone_concept import antenna_path, tube
from experiment_drone_petal_axial import advanced_errors, digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'fit', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--radius', type=float, choices=(1.1, 1.65, 2.2), required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output must be empty')
    base_hash = digest(args.base)
    mesh = json.loads(args.mesh.read_text())
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('mesh does not match saved baseline')
    fit = json.loads(args.fit.read_text())
    if fit['baseline_fcstd_sha256'] != base_hash:
        raise ValueError('fit does not match saved baseline')

    doc = App.openDocument(str(args.base.resolve()))
    try:
        antenna = doc.getObject('Antenna')
        base = doc.getObject('AntennaBase').Shape
        before = antenna.Shape
        path = antenna_path(fit['root_y_mm'], fit['parameters'], fit['control_heights_mm'])
        shape = tube(path, args.radius)
        errors = advanced_errors(shape)
        if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1 or errors:
            raise ValueError(f'invalid antenna sweep: {errors}')
        contact = {'old_gap_mm': before.distToShape(base)[0],
                   'new_gap_mm': shape.distToShape(base)[0],
                   'old_overlap_mm3': before.common(base).Volume,
                   'new_overlap_mm3': shape.common(base).Volume}
        if contact['new_overlap_mm3'] <= 0.01:
            raise ValueError(f'antenna lost its seating overlap: {contact}')
        antenna.Shape = shape
        doc.recompute()
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output / 'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)

    mesh['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {'fcstd_sha256': mesh['fcstd_sha256'], 'baseline_fcstd_sha256': base_hash,
              'script_sha256': digest(Path(__file__)), 'fit_sha256': digest(args.fit),
              'changed_objects': ['Antenna'], 'radius_mm': args.radius,
              'control_points_mm': path, 'seat_contact': contact,
              'contact_regressions': [], 'new_advanced_check_failures': errors}
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(contact))


if __name__ == '__main__':
    main()
