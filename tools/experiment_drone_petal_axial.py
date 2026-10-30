"""Extend saved nozzle leaves in real BRep space for visual diagnosis.

Parts below the root station remain fixed; crossing solids anchor their lower
end to avoid a sharp piecewise join. This is diagnostic and may fail advanced
geometry or contact checks. It isolates leaf tips from shell/recess shadow and does
not rebuild the saved model from the currently divergent nozzle generator.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(shape):
    return [round(shape.Volume, 6), round(shape.Area, 6),
            sorted(tuple(round(c, 6) for c in v.Point) for v in shape.Vertexes)]


def advanced_errors(shape):
    try:
        shape.check(True)
        return []
    except ValueError as error:
        return sorted(line.strip() for line in str(error).splitlines()
                      if line.startswith('Error in '))


def extend(shape, frame, factor, station):
    local = shape.copy()
    local.Placement = frame.inverse().multiply(local.Placement)
    bounds = local.optimalBoundingBox(False, False)
    if bounds.ZMax <= station:
        return shape.copy(), None
    matrix = App.Matrix()
    matrix.A33 = factor
    matrix.A34 = station*(1-factor)
    if bounds.ZMin >= station:
        result = local.transformGeometry(matrix)
    else:
        solids = []
        for solid in local.Solids:
            box = solid.optimalBoundingBox(False, False)
            if box.ZMax <= station:
                solids.append(solid)
            elif box.ZMin >= station:
                solids.append(solid.transformGeometry(matrix))
            else:
                # A sharp piecewise affine join creates C0 edges in guides.
                # Keep each crossing solid smooth and anchor its own lower end.
                smooth = App.Matrix()
                smooth.A33 = factor
                smooth.A34 = box.ZMin*(1-factor)
                solids.append(solid.transformGeometry(smooth))
        result = Part.makeCompound(solids) if len(solids) > 1 else solids[0]
    result.Placement = frame.multiply(result.Placement)
    local_result = result.copy()
    local_result.Placement = frame.inverse().multiply(local_result.Placement)
    return result, [bounds.ZMin, bounds.ZMax,
                    local_result.optimalBoundingBox(False, False).ZMax]


def main():
    parser = argparse.ArgumentParser()
    for name in ['base-model', 'base-meshes', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--factor', type=float, required=True)
    parser.add_argument('--station', type=float, default=98)
    args = parser.parse_args()
    if not 1 < args.factor <= 2:
        raise ValueError('Exploratory factor must be in (1, 2]')
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use a new empty output directory')
    mesh = json.loads(args.base_meshes.read_text())
    base_hash = digest(args.base_model)
    assert mesh['fcstd_sha256'] == base_hash
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    frame = App.Placement(App.Vector(0, 180, 173),
                          App.Rotation(App.Vector(0, 0, 1), axis))
    base = App.openDocument(str(args.base_model))
    before = {obj.Name: signature(obj.Shape) for obj in base.Objects
              if hasattr(obj, 'Shape') and not obj.Shape.isNull()}
    changed, records = [], []
    for item in mesh['objects']:
        name = item['name']
        if not name.startswith('NozzlePetal'):
            continue
        old = base.getObject(name).Shape
        shape, bounds = extend(old, frame, args.factor, args.station)
        if bounds is None:
            continue
        old_errors, errors = advanced_errors(old), advanced_errors(shape)
        assert shape.isValid() and shape.isClosed(), name
        assert len(shape.Solids) == len(old.Solids), (name, len(shape.Solids), len(old.Solids))
        base.getObject(name).Shape = shape
        records.append({'name': name, 'old_z_bounds_mm': bounds[:2],
                        'expected_new_z_max_mm': bounds[2],
                        'solids': len(shape.Solids), 'advanced_check_passed': not errors,
                        'baseline_advanced_errors': old_errors, 'advanced_errors': errors})
        changed.append(name)
    args.output.mkdir(parents=True, exist_ok=True)
    base.recompute()
    model = args.output/'candidate.FCStd'
    base.saveAs(str(model))
    App.closeDocument(base.Name)
    saved = App.openDocument(str(model))
    base = App.openDocument(str(args.base_model))
    try:
        preserved = []
        for name, original in before.items():
            if name not in changed:
                assert signature(saved.getObject(name).Shape) == original, name
                preserved.append(name)
        supports = []
        for name in preserved:
            if name.startswith(('Support', 'CentralSupport')):
                first, second = saved.getObject(name).Shape, base.getObject(name).Shape
                delta = abs(first.cut(second).Volume)+abs(second.cut(first).Volume)
                assert delta < 1e-6
                supports.append({'name': name, 'difference_mm3': delta})
        contacts = []
        for index in range(12):
            leaf = 'NozzlePetal'+str(index)
            names = ['BassNozzleMouthRing', 'BassNozzleShell', 'NozzlePetalHinge'+str(index)]
            names += [n for n in changed if n != leaf and (
                n in [f'NozzlePetalInset{index}', f'NozzlePetalRidge{index}', f'NozzlePetalEndHem{index}']
                or n.startswith((f'NozzlePetalGuide{index}_', f'NozzlePetalEdgeRail{index}_')))]
            for name in names:
                first, second = saved.getObject(leaf).Shape, saved.getObject(name).Shape
                gap = first.distToShape(second)[0]
                previous_gap = base.getObject(leaf).Shape.distToShape(base.getObject(name).Shape)[0]
                contacts.append({'objects': [leaf, name], 'gap_mm': gap, 'baseline_gap_mm': previous_gap,
                                 'regressed': gap > max(.01, previous_gap+1e-5)})
        for record in records:
            name = record['name']
            shape = saved.getObject(name).Shape
            assert advanced_errors(shape) == record['advanced_errors'], name
            assert shape.isValid() and shape.isClosed()
            local = shape.copy()
            local.Placement = frame.inverse().multiply(local.Placement)
            actual_z = local.optimalBoundingBox(False, False).ZMax
            assert abs(actual_z-record['expected_new_z_max_mm']) < .001, (name, actual_z)
            record['saved_z_max_mm'] = actual_z
            vertices, faces = shape.tessellate(.12)
            item = next(item for item in mesh['objects'] if item['name'] == name)
            item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
        mesh['fcstd_sha256'] = digest(model)
        (args.output/'meshes.json').write_text(json.dumps(mesh))
        issues = [r['name'] for r in records if r['advanced_errors'] != r['baseline_advanced_errors']]
        report = {'status': 'diagnostic candidate only; adoption blocked until geometry issues resolved',
                  'new_advanced_check_failures': issues,
                  'contact_regressions': [c for c in contacts if c['regressed']],
                  'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': digest(model),
                  'script_sha256': digest(Path(__file__)), 'factor': args.factor,
                  'fixed_station_mm': args.station, 'changed_objects': changed,
                  'preserved_objects': preserved, 'protected_supports': supports,
                  'parts': records, 'contacts': contacts,
                  'limitations': ['image-derived axial shape study', 'no manufacturing acceptance']}
        (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'model': str(model), 'changed': len(changed),
                          'protected_supports': len(supports)}), flush=True)
    finally:
        App.closeDocument(saved.Name)
        App.closeDocument(base.Name)


if __name__ == '__main__':
    main()
