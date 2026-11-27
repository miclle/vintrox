"""Rebuild the red-wing barrel controls on the saved cylindrical envelope."""

import argparse
import json
from pathlib import Path

import FreeCAD as App

from drone_concept import barrel_panel_shapes
from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('base', 'mesh', 'output'):
        parser.add_argument('--' + argument, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output must be empty')
    mesh = json.loads(args.mesh.read_text())
    base_hash = digest(args.base)
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('mesh does not match saved baseline')

    doc = App.openDocument(str(args.base.resolve()))
    try:
        shapes = barrel_panel_shapes()
        errors = {}
        for name, shape in shapes.items():
            old = doc.getObject(name)
            # The old features carry a rigid placement. Assign the replacement
            # in world coordinates with that placement removed.
            old.Placement = App.Placement()
            old.Shape = shape
            if not shape.isValid() or not all(solid.isClosed() for solid in shape.Solids):
                raise ValueError(f'invalid control geometry: {name}')
            if issues := advanced_errors(shape):
                errors[name] = issues
        barrel = doc.getObject('UtilityBarrelLeft').Shape
        liner = doc.getObject('UtilityLinerLeft').Shape
        contacts = {
            'frame_to_barrel_mm3': shapes['UtilityControlLeft'].common(barrel).Volume,
            'inset_to_frame_mm3': shapes['UtilityControlInsetLeft'].common(shapes['UtilityControlLeft']).Volume,
            'red_button_to_barrel_mm3': shapes['UtilitySwitchRedLeft'].common(barrel).Volume,
            'center_slide_to_inset_mm3': shapes['UtilitySwitchLeft'].common(shapes['UtilityControlInsetLeft']).Volume,
            'upper_switch_to_barrel_mm3': shapes['UtilityControlInsetLeft'].common(barrel).Volume,
            'panel_to_liner_gap_mm': shapes['UtilityControlLeft'].distToShape(liner)[0],
        }
        doc.recompute()
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output / 'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)

    mesh['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {
        'baseline_fcstd_sha256': base_hash,
        'fcstd_sha256': mesh['fcstd_sha256'],
        'script_sha256': digest(Path(__file__)),
        'changed_objects': list(shapes),
        'contacts': contacts,
        'new_advanced_check_failures': errors,
        'contact_regressions': [name for name, value in contacts.items()
                                if name.endswith('_mm3') and value <= .01],
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
