"""Restore source leaf sections without historical non-uniform transforms.

The source exit is checked against reference-only observations separately.
Candidates do not replace the formal model until multiview review and delivery.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App

import drone_nozzle_root_profile as source_profile
from experiment_drone_petal_axial import signature, advanced_errors


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['base-model', 'base-meshes', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--terminal-inset', type=float, default=0,
                        help='Reduce tip radius progressively while preserving root radius')
    parser.add_argument('--terminal-axial-shift', type=float, default=0,
                        help='Shift terminal station along local Z; keep root section fixed')
    parser.add_argument('--corner-radius', type=float, default=.85)
    args = parser.parse_args()
    if not 0 <= args.terminal_inset <= 6:
        raise ValueError('Terminal radius inset must be between 0 and 6 mm')
    if not -10 <= args.terminal_axial_shift <= 3:
        raise ValueError('Terminal axial shift must be between -10 and 3 mm')
    if not .3 <= args.corner_radius <= .85:
        raise ValueError('Corner radius must be between 0.3 and 0.85 mm')
    original_sections = source_profile.root_sections
    original_z = source_profile.shifted_z
    def tapered_sections(rows, fraction):
        result = original_sections(rows, fraction)
        return [(z+args.terminal_axial_shift*(1-source_profile.root_weight(original[0])),
                 radius-args.terminal_inset*(1-source_profile.root_weight(original[0])), dy, tilt)
                for original, (z, radius, dy, tilt) in zip(rows, result)]
    source_profile.root_sections = tapered_sections
    source_profile.shifted_z = lambda z, fraction: (original_z(z, fraction)
        + args.terminal_axial_shift*(1-source_profile.root_weight(z)))
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use a new empty output directory')
    mesh = json.loads(args.base_meshes.read_text())
    assert mesh['fcstd_sha256'] == digest(args.base_model)
    doc = App.openDocument(str(args.base_model))
    before = {o.Name: signature(o.Shape) for o in doc.Objects
              if hasattr(o, 'Shape') and not o.Shape.isNull()}
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    frame = App.Placement(App.Vector(0, 180, 173), App.Rotation(App.Vector(0, 0, 1), axis))
    records, changed = [], []
    for index in range(12):
        for name, shape in source_profile.root_shifted_leaf_parts(index, corner_radius=args.corner_radius).items():
            shape.Placement = frame.multiply(shape.Placement)
            errors = advanced_errors(shape)
            assert not errors, (name, errors)
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1, name
            doc.getObject(name).Shape = shape
            changed.append(name)
            records.append({'name': name, 'advanced_check_passed': True, 'solids': 1})
        print('built source leaf', index, flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    doc.recompute()
    model = args.output/'candidate.FCStd'
    doc.saveAs(str(model))
    App.closeDocument(doc.Name)
    saved = App.openDocument(str(model))
    base = App.openDocument(str(args.base_model))
    try:
        preserved = []
        supports = []
        for name, original in before.items():
            if name in changed:
                continue
            first, second = saved.getObject(name).Shape, base.getObject(name).Shape
            assert signature(first) == original, name
            preserved.append(name)
            if name.startswith(('Support', 'CentralSupport')):
                delta = abs(first.cut(second).Volume)+abs(second.cut(first).Volume)
                assert delta < 1e-6, name
                supports.append({'name': name, 'difference_mm3': delta})
        contacts = []
        for index in range(12):
            leaf = saved.getObject(f'NozzlePetal{index}').Shape
            names = ['BassNozzleMouthRing', 'BassNozzleShell', f'NozzlePetalHinge{index}',
                     f'NozzlePetalInset{index}', f'NozzlePetalRidge{index}', f'NozzlePetalEndHem{index}']
            names += [n for n in changed if n.startswith((f'NozzlePetalEdgeRail{index}_', f'NozzlePetalGuide{index}_'))]
            for name in names:
                shape = saved.getObject(name).Shape
                contacts.append({'leaf': index, 'part': name,
                                 'gap_mm': leaf.distToShape(shape)[0],
                                 'overlap_mm3': leaf.common(shape).Volume})
        for record in records:
            name = record['name']
            shape = saved.getObject(name).Shape
            assert not advanced_errors(shape), name
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
            vertices, faces = shape.tessellate(.12)
            item = next(o for o in mesh['objects'] if o['name'] == name)
            item.update(vertices=[list(v) for v in vertices], faces=faces)
        mesh['fcstd_sha256'] = digest(model)
        (args.output/'meshes.json').write_text(json.dumps(mesh))
        report = {'status': 'isolated source-leaf candidate; fixed-camera review pending',
                  'baseline_fcstd_sha256': digest(args.base_model), 'fcstd_sha256': digest(model),
                  'script_sha256': digest(Path(__file__)),
                  'source_sha256': digest(Path(__file__).with_name('drone_nozzle_root_profile.py')),
                  'terminal_radial_inset_mm': args.terminal_inset,
                  'terminal_axial_shift_mm': args.terminal_axial_shift,
                  'corner_radius_mm': args.corner_radius,
                  'changed_objects': changed, 'preserved_objects': preserved,
                  'protected_supports': supports, 'parts': records, 'contacts': contacts,
                  'contact_gaps_over_0_01_mm': [c for c in contacts if c['gap_mm'] > .01],
                  'limitations': ['appearance source reconstruction', 'no manufacturing acceptance']}
        (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'model': str(model), 'changed': len(changed),
                          'max_gap_mm': max(c['gap_mm'] for c in contacts)}), flush=True)
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(base.Name)


if __name__ == '__main__':
    main()
