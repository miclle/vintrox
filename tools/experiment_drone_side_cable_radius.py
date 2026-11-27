"""Study the sweep radius and lower turns of the external barrel's decorative cable."""

import argparse
import json
from pathlib import Path

import FreeCAD as App

from drone_concept import side_cable_solid
from experiment_drone_petal_axial import advanced_errors, digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--radius', type=float, choices=(1.5, 1.8, 2.1), required=True)
    parser.add_argument('--lower-coil-scale', type=float, choices=(.85, 1.0), default=1.0)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output must be empty')
    mesh = json.loads(args.mesh.read_text())
    base_hash = digest(args.base)
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('mesh does not match saved baseline')

    doc = App.openDocument(str(args.base.resolve()))
    try:
        cable = doc.getObject('SideCableLeft')
        before = cable.Shape
        after = side_cable_solid(args.radius, args.lower_coil_scale)
        if not after.isValid() or not after.isClosed() or len(after.Solids) != 1:
            raise ValueError('invalid cable sweep')
        boots = ('UtilityCableBootLeft', 'SideCableTopBootLeft')
        contacts = []
        for name in boots:
            boot = doc.getObject(name).Shape
            contacts.append({'boot': name, 'baseline_overlap_mm3': before.common(boot).Volume,
                             'candidate_overlap_mm3': after.common(boot).Volume})
        support_collisions = []
        for obj in doc.Objects:
            if obj.Name.startswith(('SupportShaft', 'SupportSocket', 'SupportFoot', 'CentralSupportSeat')):
                old_volume = before.common(obj.Shape).Volume
                new_volume = after.common(obj.Shape).Volume
                support_collisions.append({'part': obj.Name, 'baseline_overlap_mm3': old_volume,
                                           'candidate_overlap_mm3': new_volume})
        cable.Shape = after
        doc.recompute()
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output / 'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
        regressions = [c['boot'] for c in contacts if c['candidate_overlap_mm3'] <= .01]
        regressions.extend(c['part'] for c in support_collisions
                           if c['candidate_overlap_mm3'] > c['baseline_overlap_mm3'] + 1e-6)
        errors = advanced_errors(after)
    finally:
        App.closeDocument(doc.Name)

    mesh['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {'fcstd_sha256': mesh['fcstd_sha256'], 'baseline_fcstd_sha256': base_hash,
              'script_sha256': digest(Path(__file__)),
              'generator_sha256': digest(Path(__file__).with_name('drone_concept.py')),
              'changed_objects': ['SideCableLeft'], 'radius_mm': args.radius,
              'lower_coil_scale': args.lower_coil_scale,
              'boot_contacts': contacts, 'support_collisions': support_collisions,
              'contact_regressions': regressions, 'new_advanced_check_failures': errors}
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('radius_mm', 'contact_regressions',
                                                   'new_advanced_check_failures')}))


if __name__ == '__main__':
    main()
