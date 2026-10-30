"""Test lower-only fairing inset on the exact v53 saved model."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
from drone_fairing_shoulder import root_shifted_fairing
from experiment_drone_rear_cavity import signature


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def diff(a, b):
    return abs(a.cut(b).Volume) + abs(b.cut(a).Volume)


def main():
    p = argparse.ArgumentParser()
    for n in ['base-model', 'base-meshes', 'output']:
        p.add_argument('--' + n, type=Path, required=True)
    p.add_argument('--lower-inset', type=float, choices=[-2, 0, 2, 4], required=True)
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Output directory must be empty')
    meshes = json.loads(args.base_meshes.read_text())
    baseline = digest(args.base_model)
    assert meshes['fcstd_sha256'] == baseline
    doc = App.openDocument(str(args.base_model))
    original = {o.Name: signature(o.Shape) for o in doc.Objects
                if hasattr(o, 'Shape') and not o.Shape.isNull()}
    parts = root_shifted_fairing(shoulder_inset=6, lower_inset=args.lower_inset,
                                 depth_extra=4, blend_power=4)
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    place = App.Placement(App.Vector(0, 180, 173),
                          App.Rotation(App.Vector(0, 0, 1), axis))
    changed = []
    for name, shape in parts.items():
        shape.Placement = place.multiply(shape.Placement)
        shape.check(True)
        assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
        doc.getObject(name).Shape = shape
        item = next(x for x in meshes['objects'] if x['name'] == name)
        vertices, faces = shape.tessellate(.12)
        item.update(vertices=[list(v) for v in vertices], faces=faces)
        changed.append(name)
    assert len(changed) == 11
    args.output.mkdir(parents=True)
    model = args.output / 'candidate.FCStd'
    doc.recompute(); doc.saveAs(str(model)); App.closeDocument(doc.Name)
    doc = App.openDocument(str(model))
    preserved = []
    for name, sig in original.items():
        if name in changed:
            continue
        assert signature(doc.getObject(name).Shape) == sig, name
        preserved.append(name)
    assert len(preserved) == 687
    shafts = []
    for name in [o for o in original if o.startswith('SupportShaft')]:
        assert name in preserved
        # The saved/readback signature check covers the four supports; volume
        # difference is included for a direct numerical invariant.
        saved_shape = doc.getObject(name).Shape
        shafts.append({'name': name, 'signature_unchanged': signature(saved_shape) == original[name]})
    assert len(shafts) == 4 and all(s['signature_unchanged'] for s in shafts)
    contacts = []
    for name in ['BassNozzleRolledLip', 'BassNozzleRearCollar', 'RearRecessLiner']:
        shell = doc.getObject('BassNozzleShell').Shape
        other = doc.getObject(name).Shape
        contacts.append({'objects': ['BassNozzleShell', name],
                         'gap_mm': shell.distToShape(other)[0],
                         'overlap_mm3': shell.common(other).Volume})
    meshes['fcstd_sha256'] = digest(model)
    report = {'baseline_fcstd_sha256': baseline, 'fcstd_sha256': meshes['fcstd_sha256'],
              'lower_inset_mm': args.lower_inset, 'shoulder_inset_mm': 6,
              'depth_extra_mm': 4, 'blend_power': 4, 'changed_objects': changed,
              'preserved_objects': preserved, 'contacts': contacts,
              'source_sha256': digest(Path(__file__).with_name('drone_fairing_shoulder.py')),
              'script_sha256': digest(Path(__file__)),
              'status': 'isolated fairing candidate; fixed-view review pending'}
    (args.output / 'meshes.json').write_text(json.dumps(meshes))
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    App.closeDocument(doc.Name)
    print(model, flush=True)


if __name__ == '__main__':
    main()
