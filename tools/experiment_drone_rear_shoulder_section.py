"""Compare flatter rear-shoulder sections against the saved v61 baseline.

Only the two cheek solids change. The side/back endpoints, R24 lower fold,
status opening, model palette and calibrated cameras remain fixed.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part

from drone_concept import profile, reprojected_rear_shoulders
from experiment_drone_rear_cavity import signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shoulder_parts(exponent):
    parts = reprojected_rear_shoulders(
        108, 1.0089049846660512, 481.9590609254328, 317.0386845391606,
        exponent=exponent, fold_radius=24)
    inner = [(190, 182), (214, 182), (214, 145), (204, 133), (190, 145)]
    mouth = [(185, 190), (239, 190), (239, 140), (206, 128), (185, 140)]
    for side, suffix in [(-1, 'Left'), (1, 'Right')]:
        def wire(points, x):
            vertices = [App.Vector(x, y, z) for y, z in points]
            return Part.Wire(Part.makePolygon(vertices + [vertices[0]]).Edges)
        pocket = profile(inner, 'YZ', (side*94.6, 0, 0), side*25)
        flare = Part.makeLoft([wire(inner, side*94.6), wire(mouth, side*117)],
                              True, True)
        name = 'RearArmourCheek' + suffix
        parts[name] = parts[name].cut(pocket).cut(flare)
    return parts


def difference(first, second):
    return abs(first.cut(second).Volume) + abs(second.cut(first).Volume)


def main():
    parser = argparse.ArgumentParser()
    for name in ['base-model', 'base-meshes', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--exponent', type=float, choices=[1.1, 1.25, 1.5], required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use a new empty output directory')
    mesh = json.loads(args.base_meshes.read_text())
    baseline_hash = digest(args.base_model)
    assert mesh['fcstd_sha256'] == baseline_hash
    baseline = App.openDocument(str(args.base_model))
    original = {obj.Name: signature(obj.Shape) for obj in baseline.Objects
                if hasattr(obj, 'Shape') and not obj.Shape.isNull()}
    baseline_parts = shoulder_parts(1.5)
    source_checks = []
    for name, shape in baseline_parts.items():
        delta = difference(shape, baseline.getObject(name).Shape)
        assert delta < 1e-6, (name, delta)
        source_checks.append({'name': name, 'baseline_source_difference_mm3': delta})
    records = []
    parts = shoulder_parts(args.exponent)
    for name, shape in parts.items():
        shape.check(True)
        assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
        records.append({'name': name, 'advanced_check_passed': True,
                        'closed': True, 'solids': 1,
                        'baseline_difference_mm3': difference(shape, baseline.getObject(name).Shape)})
        baseline.getObject(name).Shape = shape
    args.output.mkdir(parents=True, exist_ok=True)
    model = args.output/'candidate.FCStd'
    baseline.recompute()
    baseline.saveAs(str(model))
    App.closeDocument(baseline.Name)
    saved = App.openDocument(str(model))
    base = App.openDocument(str(args.base_model))
    try:
        preserved = []
        for name, before in original.items():
            if name in parts:
                continue
            same = signature(saved.getObject(name).Shape) == before
            assert same, name
            preserved.append(name)
        supports = []
        for name in preserved:
            if not name.startswith(('SupportShaft', 'SupportFoot', 'SupportSocket', 'CentralSupportSeat')):
                continue
            delta = difference(saved.getObject(name).Shape, base.getObject(name).Shape)
            assert delta < 1e-6, (name, delta)
            supports.append({'name': name, 'difference_mm3': delta})
        contacts = []
        for suffix in ['Left', 'Right']:
            cheek = saved.getObject('RearArmourCheek'+suffix).Shape
            for other in ['RearStructuralFrame', 'SideGuard'+suffix]:
                shape = saved.getObject(other).Shape
                gap = cheek.distToShape(shape)[0]
                assert gap < .01, (suffix, other, gap)
                contacts.append({'objects': ['RearArmourCheek'+suffix, other],
                                 'gap_mm': gap, 'overlap_mm3': cheek.common(shape).Volume})
        for name in parts:
            shape = saved.getObject(name).Shape
            shape.check(True)
            delta = difference(shape, parts[name])
            assert delta < 1e-6
            vertices, faces = shape.tessellate(.12)
            item = next(obj for obj in mesh['objects'] if obj['name'] == name)
            item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
        mesh['fcstd_sha256'] = digest(model)
        (args.output/'meshes.json').write_text(json.dumps(mesh))
        report = {'status': 'isolated appearance candidate; fixed-camera comparison pending',
                  'baseline_fcstd_sha256': baseline_hash, 'fcstd_sha256': digest(model),
                  'exponent': args.exponent, 'fold_radius_mm': 24,
                  'script_sha256': digest(Path(__file__)),
                  'generator_sha256': digest(Path(__file__).with_name('drone_concept.py')),
                  'baseline_source_checks': source_checks, 'parts': records,
                  'changed_objects': list(parts), 'preserved_objects': preserved,
                  'protected_supports': supports, 'contacts': contacts,
                  'limitations': ['image-derived shape assumption', 'no physical or manufacturing acceptance']}
        (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'exponent': args.exponent, 'fcstd_sha256': digest(model),
                          'changed_objects': list(parts), 'preserved_shapes': len(preserved),
                          'protected_supports': len(supports)}), flush=True)
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(base.Name)


if __name__ == '__main__':
    main()
