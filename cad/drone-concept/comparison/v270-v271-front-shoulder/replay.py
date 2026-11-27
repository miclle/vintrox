"""Test a symmetric inward translation of the saved front shoulder assembly."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import FreeCAD as App
from experiment_drone_petal_axial import advanced_errors

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--inward-mm', type=float, choices=(2, 4), required=True)
parser.add_argument('--group', choices=('all', 'crown', 'plate'), default='all')
args = parser.parse_args()
base = args.base.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
model = output / 'candidate.FCStd'
source = App.openDocument(str(base))
originals = {}
translated = {}
pairs = []
for side in ('Left', 'Right'):
    crown = 'HoodShoulderCrown' + side
    plate = 'HoodShoulderPlate' + side
    bolt = 'HoodShoulderBolt' + side
    liner = 'HoodShoulderSlotLiner' + side
    sign = -1 if side == 'Left' else 1
    marks = [obj.Name for obj in source.Objects if obj.Name.startswith('HoodMark')
             and sign * obj.Shape.CenterOfMass.x > 0]
    assert len(marks) == 4
    pairs += [(crown, mark) for mark in marks] + [(plate, bolt), (plate, liner),
              (crown, 'ProjectingBrow'), (plate, 'ProjectingBrow'),
              (plate, 'BrowUnderside'), (plate, 'ScreenBezel')]
    groups = {'all': (crown, plate, bolt, liner, *marks),
              'crown': (crown, *marks), 'plate': (plate, bolt, liner)}
    for name in groups[args.group]:
        shape = source.getObject(name).Shape
        originals[name] = shape.copy()
        moved = shape.copy()
        moved.translate(App.Vector(-sign * args.inward_mm, 0, 0))
        translated[name] = moved
        shape_path = output / f'{name}.Shape.brp'
        moved.exportBrep(str(shape_path))

with ZipFile(base) as before, ZipFile(model, 'w', ZIP_DEFLATED) as after:
    replacements = {f'{name}.Shape.brp' for name in originals}
    assert replacements.issubset(before.namelist())
    for member in before.namelist():
        payload = (output / member).read_bytes() if member in replacements else before.read(member)
        after.writestr(member, payload)

saved = App.openDocument(str(model))
geometry = {}
for name, original in originals.items():
    shape = saved.getObject(name).Shape
    before_errors = advanced_errors(original)
    after_errors = advanced_errors(shape)
    expected_center = translated[name].CenterOfMass
    geometry[name] = {
        'solids': len(shape.Solids), 'valid': shape.isValid(),
        'closed': all(solid.isClosed() for solid in shape.Solids),
        'positive_volume': shape.Volume > 0,
        'center_difference_mm': (shape.CenterOfMass - expected_center).Length,
        'relative_volume_difference': abs(shape.Volume / original.Volume - 1),
        'baseline_advanced_errors': before_errors, 'candidate_advanced_errors': after_errors,
    }
    assert geometry[name]['center_difference_mm'] < 1e-6, name

contacts = []
for left, right in pairs:
    a, b = (source.getObject(name).Shape for name in (left, right))
    c, d = (saved.getObject(name).Shape for name in (left, right))
    contacts.append({'objects': [left, right],
                     'baseline_gap_mm': a.distToShape(b)[0],
                     'candidate_gap_mm': c.distToShape(d)[0],
                     'baseline_overlap_mm3': a.common(b).Volume,
                     'candidate_overlap_mm3': c.common(d).Volume})
report = {'baseline_fcstd_sha256': hashlib.sha256(base.read_bytes()).hexdigest(),
          'fcstd_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
          'inward_mm_per_side': args.inward_mm, 'geometry': geometry, 'contacts': contacts}
if args.group != 'all':
    report['group'] = args.group
(output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
App.closeDocument(saved.Name)
App.closeDocument(source.Name)
