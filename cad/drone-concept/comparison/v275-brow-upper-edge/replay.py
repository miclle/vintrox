"""Replay a mirrored local trim of the front brow from the saved v272 candidate."""

import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import hashlib

import FreeCAD as App
import Part
from experiment_drone_petal_axial import advanced_errors

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', type=Path, required=True, help='Rebuilt v272 crown-only FCStd')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
work = args.output.resolve()
work.mkdir(parents=True, exist_ok=False)
base = args.base.resolve()
model = work / 'candidate.FCStd'
doc = App.openDocument(str(base))
name = 'ProjectingBrow'
before = doc.getObject(name).Shape
shape = before.copy()
for sign in (-1, 1):
    wires = []
    for z, x in ((230, 130), (234, 114.5), (241, 110.5), (247, 110.5), (252, 130)):
        vertices = [App.Vector(sign * px, y, z)
                    for px, y in ((x, -31), (135, -35), (135, 19), (x, 15))]
        wires.append(Part.makePolygon(vertices + vertices[:1]))
    shape = shape.cut(Part.makeLoft(wires, True, True))
payload = work / 'ProjectingBrow.Shape.brp'
shape.exportBrep(str(payload))
with ZipFile(base) as source, ZipFile(model, 'w', ZIP_DEFLATED) as target:
    for member in source.namelist():
        target.writestr(member, payload.read_bytes() if member == payload.name else source.read(member))

saved = App.openDocument(str(model))
after = saved.getObject(name).Shape
neighbors = ['HoodShoulderCrownLeft','HoodShoulderCrownRight','HoodShoulderPlateLeft',
             'HoodShoulderPlateRight','BrowUnderside','HoodEdge']
contacts = []
for neighbor in neighbors:
    other = doc.getObject(neighbor).Shape
    contacts.append({'object': neighbor, 'before_gap_mm': before.distToShape(other)[0],
                     'after_gap_mm': after.distToShape(other)[0],
                     'before_overlap_mm3': before.common(other).Volume,
                     'after_overlap_mm3': after.common(other).Volume})
result = {'base_fcstd_sha256': hashlib.sha256(base.read_bytes()).hexdigest(),
          'fcstd_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
          'valid': after.isValid(), 'closed': all(s.isClosed() for s in after.Solids),
          'solid_count': len(after.Solids), 'removed_mm3': before.Volume - after.Volume,
          'before_errors': advanced_errors(before), 'after_errors': advanced_errors(after),
          'contacts': contacts}
if (not result['valid'] or not result['closed'] or result['solid_count'] != 1
        or result['removed_mm3'] <= 0 or result['before_errors'] != result['after_errors']
        or any(pair['after_gap_mm'] > .01 for pair in contacts)):
    raise ValueError('Saved upper-edge trim failed the geometry or contact checks')
App.closeDocument(saved.Name)
App.closeDocument(doc.Name)
(work/'trim-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
