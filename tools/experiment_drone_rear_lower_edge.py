"""Raise only the lower rear frame/panel edges at fixed camera geometry."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App

from drone_concept import cylinder, rear_raked_slab, rounded_frame, rounded_plate
from experiment_drone_rear_cavity import signature


def rear_lower_parts(rise):
    bottom = 60.12 + rise
    panel = rounded_plate(178.6, 233.8-bottom, 400, (-89.3, 0, bottom), 3.36)
    panel = panel.common(rear_raked_slab(218.75, 244, bottom, 233.8, 89.3))
    axis = App.Vector(0, .574, -.819); axis.normalize()
    bore = cylinder(50, 180, tuple(App.Vector(0, 180, 173)-axis*40), tuple(axis))
    opening = rounded_plate(138, 116, 400, (-69, 0, 76), 8)
    bottom = 61.8 + rise
    frame = rounded_frame(178, 231.8-bottom, 400, 7.56, (-89, 0, bottom), 10.08)
    frame = frame.common(rear_raked_slab(241.75, 248, bottom, 231.8, 89))
    for side in (-1, 1):
        frame = frame.cut(rounded_plate(13.5, 2.8, 2.1, (side*15.5-6.75, 246.7, 228), 1.3))
    return {'RearServicePanel': panel.cut(bore).cut(opening), 'RearStructuralFrame': frame}


def main():
    parser = argparse.ArgumentParser()
    for name in ['base-model', 'base-meshes', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--rise', type=float, choices=[2, 4, 6], required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty output directory')
    meshes = json.loads(args.base_meshes.read_text())
    base_hash = hashlib.sha256(args.base_model.read_bytes()).hexdigest()
    assert meshes['fcstd_sha256'] == base_hash
    doc = App.openDocument(str(args.base_model))
    original = {o.Name: signature(o.Shape) for o in doc.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()}
    parts = rear_lower_parts(args.rise)
    checks = []
    for name, shape in parts.items():
        shape.check(True)
        assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
        doc.getObject(name).Shape = shape
        item = next(o for o in meshes['objects'] if o['name'] == name)
        vertices, faces = shape.tessellate(.12)
        item.update(vertices=[list(v) for v in vertices], faces=faces)
        checks.append({'name': name, 'valid': True, 'advanced_check_passed': True, 'solids': 1})
    args.output.mkdir(parents=True, exist_ok=True)
    model = args.output/'candidate.FCStd'
    doc.recompute(); doc.saveAs(str(model)); App.closeDocument(doc.Name)
    doc = App.openDocument(str(model))
    preserved = [{'name': o.Name, 'unchanged_geometry_signature_6dp': signature(o.Shape) == original[o.Name]}
                 for o in doc.Objects if o.Name in original and o.Name not in parts]
    assert all(o['unchanged_geometry_signature_6dp'] for o in preserved)
    contacts = []
    for name in parts:
        for other in ['RearArmourCheekLeft', 'RearArmourCheekRight', 'RearLowerSlope', 'RearRecessLiner', 'RearRailCarrier']:
            a = doc.getObject(name).Shape; b = doc.getObject(other).Shape
            contacts.append({'objects': [name, other], 'gap_mm': a.distToShape(b)[0], 'overlap_mm3': a.common(b).Volume})
    meshes['fcstd_sha256'] = hashlib.sha256(model.read_bytes()).hexdigest()
    (args.output/'meshes.json').write_text(json.dumps(meshes))
    (args.output/'candidate-check.json').write_text(json.dumps({
        'fcstd_sha256': meshes['fcstd_sha256'], 'baseline_fcstd_sha256': base_hash,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rise_mm': args.rise, 'changed_objects': list(parts), 'parts': checks,
        'preserved': preserved, 'contacts': contacts, 'status': 'exploratory geometry'}, indent=2)+'\n')
    App.closeDocument(doc.Name)
    print(model, flush=True)


if __name__ == '__main__':
    main()
