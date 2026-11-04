"""Extend saved nozzle leaves in real BRep space for visual diagnosis.

The default anchors crossing solids at their lower end. The tip-splice option
retains the root, guides and hinges and adds an explicit planar seam. Both are
diagnostic and may fail advanced geometry or contact checks. Neither rebuilds
the saved model from the currently divergent nozzle generator.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

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


def extend_tip(shape, frame, factor, station, radial_shift=0, centre_shift=0,
               leaf_index=0):
    """Keep the root BRep and splice an affine tip at a real planar seam."""
    local = shape.copy()
    local.Placement = frame.inverse().multiply(local.Placement)
    bounds = local.optimalBoundingBox(False, False)
    if bounds.ZMax <= station:
        return shape.copy(), None
    # Boxes fully cover this saved nozzle in its local frame. The seam is an
    # explicit CAD edge; no claim of tangent continuity is made at the station.
    lower = local.common(Part.makeBox(400, 400, station+200,
                                     App.Vector(-200, -200, -200)))
    upper = local.common(Part.makeBox(400, 400, 300-station,
                                     App.Vector(-200, -200, station)))
    matrix = App.Matrix()
    matrix.A33 = factor
    matrix.A34 = station*(1-factor)
    # Shear about the fixed seam changes the terminal radius and centre without
    # moving any seam point. 17 mm is the nominal saved terminal span; actual
    # shifts vary with each point's saved local Z and are recorded as such.
    angle = math.radians(leaf_index*30+30)
    matrix.A13 = radial_shift*math.cos(angle)/17
    matrix.A23 = (radial_shift*math.sin(angle)+centre_shift)/17
    matrix.A14 = -station*matrix.A13
    matrix.A24 = -station*matrix.A23
    tip = upper.transformGeometry(matrix)
    result = lower.fuse(tip) if not lower.isNull() else tip
    new_max = result.optimalBoundingBox(False, False).ZMax
    result.Placement = frame.multiply(result.Placement)
    return result, [bounds.ZMin, bounds.ZMax, new_max]


def main():
    parser = argparse.ArgumentParser()
    for name in ['base-model', 'base-meshes', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--factor', type=float, required=True)
    parser.add_argument('--station', type=float, default=98)
    parser.add_argument('--construction', choices=['solid-affine', 'tip-splice'],
                        default='solid-affine')
    parser.add_argument('--tip-radial-shift', type=float, default=0,
                        help='Tip-splice shear: radial shift per 17 mm of original axial span')
    parser.add_argument('--tip-centre-shift', type=float, default=0,
                        help='Tip-splice shear: local Y shift per 17 mm of original axial span')
    args = parser.parse_args()
    if not 1 < args.factor <= 2:
        raise ValueError('Exploratory factor must be in (1, 2]')
    if not -200 < args.station < 300:
        raise ValueError('station is outside the local clipping envelope')
    if max(abs(args.tip_radial_shift), abs(args.tip_centre_shift)) > 10:
        raise ValueError('tip shear is outside the exploratory 10 mm range')
    if args.construction != 'tip-splice' and (args.tip_radial_shift or args.tip_centre_shift):
        raise ValueError('tip shear requires tip-splice construction')
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
        if args.construction == 'tip-splice' and name.startswith(('NozzlePetalGuide', 'NozzlePetalHinge')):
            continue
        old = base.getObject(name).Shape
        if args.construction == 'tip-splice':
            index = int(re.fullmatch(r'NozzlePetal(?:Inset|EdgeRail|EndHem|Ridge)?(\d+)(?:_\d+)?', name)[1])
            shape, bounds = extend_tip(old, frame, args.factor, args.station,
                                       args.tip_radial_shift, args.tip_centre_shift, index)
        else:
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
            names += [f'NozzlePetalGuide{index}_{rail}' for rail in range(2)
                      if f'NozzlePetalGuide{index}_{rail}' not in names]
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
        contact_regressions = [c for c in contacts if c['regressed']]
        status = ('diagnostic candidate; geometry/contact failures prevent adoption'
                  if issues or contact_regressions else
                  'saved research candidate; image comparison and export checks required')
        report = {'status': status,
                  'new_advanced_check_failures': issues,
                  'contact_regressions': contact_regressions,
                  'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': digest(model),
                  'script_sha256': digest(Path(__file__)), 'factor': args.factor,
                  'construction': args.construction,
                  'tip_radial_shift_per_17mm_span_mm': args.tip_radial_shift,
                  'tip_centre_y_shift_per_17mm_span_mm': args.tip_centre_shift,
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
