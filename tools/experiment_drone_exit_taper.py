"""Test a small petal hinge rotation in saved CAD, keeping the housing fixed.

This is an appearance study, not a claim of a working iris mechanism. The
reference shadows remain part of the recessed housing, never an added tube.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import FreeCAD as App
from experiment_drone_rear_cavity import signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('base-model', 'base-meshes', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--degrees', type=float, choices=(2, 4), required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    mesh = json.loads(args.base_meshes.read_text())
    baseline_hash = digest(args.base_model)
    assert mesh['fcstd_sha256'] == baseline_hash
    document = App.openDocument(str(args.base_model))
    original = {o.Name: signature(o.Shape) for o in document.Objects
                if hasattr(o, 'Shape') and not o.Shape.isNull()}
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    placement = App.Placement(App.Vector(0, 180, 173),
                              App.Rotation(App.Vector(0, 0, 1), axis))
    pattern = re.compile(r'^NozzlePetal(?:Inset|Ridge|Guide|EdgeRail|EndHem)?(\d+)(?:_|$)')
    changed, checks = [], []
    for item in mesh['objects']:
        match = pattern.match(item['name'])
        if not match:
            continue
        index = int(match.group(1))
        angle = math.radians(index*30+30)
        local_pivot = App.Vector(51.5*math.cos(angle),
                                -1.149+51.5*math.sin(angle), 98.5)
        pivot = placement.multVec(local_pivot)
        tangent = placement.Rotation.multVec(App.Vector(-math.sin(angle), math.cos(angle), 0))
        obj = document.getObject(item['name'])
        shape = obj.Shape.copy()
        shape.rotate(pivot, tangent, -args.degrees)
        shape.check(True)
        assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
        assert abs(shape.Volume-obj.Shape.Volume) < 1e-6
        obj.Shape = shape
        vertices, faces = shape.tessellate(.12)
        item.update(vertices=[list(v) for v in vertices], faces=faces)
        changed.append(obj.Name)
    assert len(changed) == 96
    args.output.mkdir(parents=True, exist_ok=True)
    model = args.output/'candidate.FCStd'
    document.recompute()
    document.saveAs(str(model))
    App.closeDocument(document.Name)
    saved = App.openDocument(str(model))
    for name, before in original.items():
        if name not in changed:
            assert signature(saved.getObject(name).Shape) == before, name
    for index in range(12):
        leaf = saved.getObject(f'NozzlePetal{index}').Shape
        hinge = saved.getObject(f'NozzlePetalHinge{index}').Shape
        checks.append({'leaf': index, 'root_gap_mm': leaf.distToShape(hinge)[0],
                       'overlap_mm3': leaf.common(hinge).Volume})
    assert max(c['root_gap_mm'] for c in checks) < .01
    # Volume/vertex signatures cover every untouched part; use solid difference
    # as an additional exact guard for the four explicitly protected shafts.
    baseline = App.openDocument(str(args.base_model))
    shafts = []
    for obj in baseline.Objects:
        if obj.Name.startswith('SupportShaft'):
            other = saved.getObject(obj.Name).Shape
            delta = obj.Shape.cut(other).Volume + other.cut(obj.Shape).Volume
            assert delta < 1e-6
            shafts.append({'name': obj.Name, 'symmetric_difference_mm3': delta})
    assert len(shafts) == 4
    App.closeDocument(baseline.Name)
    App.closeDocument(saved.Name)
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh))
    result = {'status': 'candidate only; fixed-camera comparison required',
              'baseline_fcstd_sha256': baseline_hash, 'fcstd_sha256': digest(model),
              'script_sha256': digest(Path(__file__)), 'hinge_rotation_degrees': -args.degrees,
              'changed_objects': changed, 'unchanged_objects': len(original)-len(changed),
              'root_contacts': checks, 'protected_shafts': shafts,
              'limitations': ['Rigid leaf rotation is an appearance experiment, not mechanical acceptance.',
                             'Gold housing, rolled lip, root hinges, rear cavity and cameras stay fixed.']}
    (args.output/'candidate-check.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'fcstd_sha256': digest(model), 'changed': len(changed),
                      'max_root_gap_mm': max(c['root_gap_mm'] for c in checks)}))


if __name__ == '__main__':
    main()
