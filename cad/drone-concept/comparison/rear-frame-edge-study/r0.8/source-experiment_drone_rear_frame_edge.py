"""Saved-CAD rear-frame roundover candidates; formal model stays unchanged."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
from drone_rear_frame_edge import rounded_frame_inner_edge
from experiment_drone_rear_cavity import signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def difference(a, b):
    return abs(a.cut(b).Volume) + abs(b.cut(a).Volume)


def main():
    p = argparse.ArgumentParser()
    for name in ['base-model', 'base-meshes', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--radius', type=float, required=True)
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    meshes = json.loads(args.base_meshes.read_text())
    baseline = digest(args.base_model)
    assert meshes['fcstd_sha256'] == baseline
    doc = App.openDocument(str(args.base_model))
    originals = {o.Name: o.Shape.copy() for o in doc.Objects
                 if hasattr(o, 'Shape') and not o.Shape.isNull()}
    name = 'RearStructuralFrame'
    before = originals[name]
    shape = rounded_frame_inner_edge(before, args.radius)
    removed, added = before.cut(shape), shape.cut(before)
    assert abs(added.Volume) < 1e-6 and removed.Volume > 0
    doc.getObject(name).Shape = shape
    vertices, faces = shape.tessellate(.12)
    item = next(o for o in meshes['objects'] if o['name'] == name)
    item.update(vertices=[list(v) for v in vertices], faces=faces)
    args.output.mkdir(parents=True)
    model = args.output / 'candidate.FCStd'
    doc.recompute()
    doc.saveAs(str(model))
    App.closeDocument(doc.Name)
    doc = App.openDocument(str(model))
    saved = doc.getObject(name).Shape
    saved.check(True)
    assert difference(saved, shape) < 1e-6
    preserved = []
    for n, s in originals.items():
        if n != name:
            assert signature(s) == signature(doc.getObject(n).Shape), n
            preserved.append(n)
    assert len(preserved) == 697
    shafts = [{'name': n, 'symmetric_difference_mm3': difference(s, doc.getObject(n).Shape)}
              for n, s in originals.items() if n.startswith('SupportShaft')]
    assert len(shafts) == 4 and all(s['symmetric_difference_mm3'] < 1e-6 for s in shafts)
    contacts = []
    for n in ['RearServicePanel', 'RearArmourCheekLeft', 'RearArmourCheekRight',
              'RearRailCarrier', 'RearRecessLiner']:
        other = doc.getObject(n).Shape
        contacts.append({'name': n, 'before_gap_mm': before.distToShape(other)[0],
                         'gap_mm': saved.distToShape(other)[0],
                         'overlap_mm3': saved.common(other).Volume})
    assert all(abs(c['gap_mm'] - c['before_gap_mm']) < 1e-5 for c in contacts)
    report = {'baseline_fcstd_sha256': baseline, 'fcstd_sha256': digest(model),
              'radius_mm': args.radius, 'changed_objects': [name],
              'removed_volume_mm3': removed.Volume, 'added_volume_mm3': added.Volume,
              'removed_bounds_mm': [removed.BoundBox.XMin, removed.BoundBox.XMax,
                                    removed.BoundBox.YMin, removed.BoundBox.YMax,
                                    removed.BoundBox.ZMin, removed.BoundBox.ZMax],
              'advanced_check_passed': True, 'source_saved_difference_mm3': difference(saved, shape),
              'preserved_objects': preserved, 'shafts': shafts, 'contacts': contacts,
              'source_sha256': digest(Path(__file__).with_name('drone_rear_frame_edge.py')),
              'script_sha256': digest(Path(__file__)),
              'status': 'isolated perimeter roundover; fixed-view review pending'}
    meshes['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(meshes))
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    App.closeDocument(doc.Name)
    print(model, flush=True)


if __name__ == '__main__':
    main()
