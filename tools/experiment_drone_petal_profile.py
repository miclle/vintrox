"""Build shared-root taper candidates without replacing the formal model."""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App
from drone_petal_profile import tapered_leaf_parts
from experiment_drone_rear_cavity import signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    for name in ('base-model', 'base-meshes', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--inset', type=float, choices=(0, 1, 2.1, 3), required=True)
    a = p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    mesh = json.loads(a.base_meshes.read_text())
    base_hash = digest(a.base_model)
    assert mesh['fcstd_sha256'] == base_hash
    doc = App.openDocument(str(a.base_model))
    original = {o.Name: signature(o.Shape) for o in doc.Objects
                if hasattr(o, 'Shape') and not o.Shape.isNull()}
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    placement = App.Placement(App.Vector(0, 180, 173),
                              App.Rotation(App.Vector(0, 0, 1), axis))
    records, changed = [], []
    for index in range(12):
        for name, shape in tapered_leaf_parts(index, a.inset).items():
            shape.Placement = placement.multiply(shape.Placement)
            shape.check(True)
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1, name
            previous = doc.getObject(name).Shape
            delta = shape.cut(previous).Volume + previous.cut(shape).Volume
            if a.inset == 0:
                assert delta < 1e-6, (name, delta)
            doc.getObject(name).Shape = shape
            item = next(o for o in mesh['objects'] if o['name'] == name)
            vertices, faces = shape.tessellate(.12)
            item.update(vertices=[list(v) for v in vertices], faces=faces)
            records.append({'name': name, 'valid': True, 'advanced_check_passed': True,
                            'closed': True, 'solids': 1, 'symmetric_difference_mm3': delta})
            changed.append(name)
        print('built leaf', index, flush=True)
    assert len(changed) == 96
    a.output.mkdir(parents=True, exist_ok=True)
    model = a.output/'candidate.FCStd'
    doc.recompute()
    doc.saveAs(str(model))
    App.closeDocument(doc.Name)
    saved = App.openDocument(str(model))
    for name, before in original.items():
        if name not in changed:
            assert signature(saved.getObject(name).Shape) == before, name
    contacts = []
    for index in range(12):
        leaf = saved.getObject(f'NozzlePetal{index}').Shape
        for name in [f'NozzlePetalHinge{index}', f'NozzlePetalInset{index}',
                     f'NozzlePetalRidge{index}', f'NozzlePetalEndHem{index}',
                     *[n for n in changed if n.startswith(f'NozzlePetalEdgeRail{index}_')]]:
            other = saved.getObject(name).Shape
            contacts.append({'leaf': index, 'part': name,
                             'gap_mm': leaf.distToShape(other)[0],
                             'overlap_mm3': leaf.common(other).Volume})
    assert max(c['gap_mm'] for c in contacts) < .01
    App.closeDocument(saved.Name)
    mesh['fcstd_sha256'] = digest(model)
    (a.output/'meshes.json').write_text(json.dumps(mesh))
    report = {'status': 'isolated candidate; full fixed-camera review pending',
              'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': digest(model),
              'terminal_radial_inset_mm': a.inset, 'terminal_radius_mm': 43.6-a.inset,
              'script_sha256': digest(Path(__file__)),
              'source_module_sha256': digest(Path(__file__).with_name('drone_petal_profile.py')),
              'changed_objects': changed, 'parts': records,
              'unchanged_objects': len(original)-len(changed), 'contacts': contacts}
    (a.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'model_sha256': digest(model), 'changed': len(changed),
                      'max_contact_gap_mm': max(c['gap_mm'] for c in contacts)}))


if __name__ == '__main__':
    main()
