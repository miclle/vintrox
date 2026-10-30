"""Compare real rear-frame edge blends against the hash-bound v48 baseline."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
from experiment_drone_rear_cavity import signature


BASELINE_SHA = '94f972c40e00c3ce739fde8134fa72e807688be6f2b0d098e24099f4f7f56419'
# Saved v48 edge topology: rear-facing outer and inner perimeter, including
# the bent lower edge. Excludes the two small upper mounting recesses.
PERIMETER = [5, 6, 7, 32, 36, 38, 40, 77, 68, 69, 70, 71,
             35, 37, 39, 41, 43, 80, 66, 65, 64, 63, 62, 61]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'meshes', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--radius', type=float, choices=(.7, 1.2), required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new candidate directory')
    assert digest(args.baseline) == BASELINE_SHA
    meshes = json.loads(args.meshes.read_text())
    assert meshes['fcstd_sha256'] == BASELINE_SHA
    doc = App.openDocument(str(args.baseline))
    before = {o.Name: signature(o.Shape) for o in doc.Objects
              if hasattr(o, 'Shape') and not o.Shape.isNull()}
    name = 'RearStructuralFrame'
    old = doc.getObject(name).Shape.copy()
    shape = old.makeFillet(args.radius, [old.Edges[i-1] for i in PERIMETER])
    shape.check(True)
    assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
    doc.getObject(name).Shape = shape
    vertices, faces = shape.tessellate(.12)
    next(o for o in meshes['objects'] if o['name'] == name).update(
        vertices=[list(v) for v in vertices], faces=faces)
    args.output.mkdir(parents=True)
    model = args.output / 'candidate.FCStd'
    doc.recompute()
    doc.saveAs(str(model))
    App.closeDocument(doc.Name)
    doc = App.openDocument(str(model))
    for key, value in before.items():
        if key != name:
            assert signature(doc.getObject(key).Shape) == value, key
    saved = doc.getObject(name).Shape
    saved.check(True)
    assert saved.isValid() and saved.isClosed() and len(saved.Solids) == 1
    contacts = []
    for target in ('RearServicePanel', 'RearArmourCheekLeft', 'RearArmourCheekRight'):
        other = doc.getObject(target).Shape
        contacts.append({'other': target, 'gap_mm': saved.distToShape(other)[0],
                         'overlap_mm3': saved.common(other).Volume})
    assert all(c['gap_mm'] < 1e-6 for c in contacts)
    report = {
        'baseline_fcstd_sha256': BASELINE_SHA, 'fcstd_sha256': digest(model),
        'generator_sha256': digest(Path(__file__)), 'radius_mm': args.radius,
        'changed_objects': [name], 'unchanged_shape_count': len(before)-1,
        'protected_shafts': [n for n in before if n.startswith('SupportShaft')],
        'selected_edge_indices': PERIMETER, 'valid_closed_single_solid': True,
        'advanced_check_passed': True,
        'removed_volume_mm3': old.cut(saved).Volume,
        'added_volume_mm3': saved.cut(old).Volume, 'contacts': contacts,
        'status': 'exploratory candidate; fixed-camera visual review required',
        'limitations': ['Radius inferred for appearance; not a source measurement.',
                       'Only one frame changes. Cavity, nozzle, materials and cameras remain fixed.']}
    App.closeDocument(doc.Name)
    meshes['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(meshes))
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
