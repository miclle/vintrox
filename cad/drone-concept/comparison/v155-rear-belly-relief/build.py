"""Raise the outer underside of the saved v154 belly pan behind its service plates."""

import hashlib
import json
from pathlib import Path
import sys

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, signature

base, mesh_path, output = map(Path, sys.argv[1:])
pan_name = 'ClosedBellyPan'

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

mesh = json.loads(mesh_path.read_text(encoding='utf-8'))
base_hash = digest(base)
assert mesh['fcstd_sha256'] == base_hash
document = App.openDocument(str(base.resolve()))
pan = document.getObject(pan_name)
original = pan.Shape.copy()
candidate = original.copy()
# Transition from the low outer floor aft of the service plates. Keep the
# support seat and the loop roots inside the original central strip.
stations = [(127, 46), (136, 53.35), (230, 53.35), (230, 10), (127, 10)]
for side in (-1, 1):
    x = side * 52
    points = [App.Vector(x, y, z) for y, z in stations]
    cutter = Part.Face(Part.makePolygon(points + points[:1])).extrude(App.Vector(side * 60, 0, 0))
    candidate = candidate.cut(cutter)
candidate = candidate.removeSplitter()
errors = advanced_errors(candidate)
assert candidate.isValid() and candidate.isClosed() and len(candidate.Solids) == 1 and not errors
assert original.Volume - candidate.Volume > 1
assert candidate.cut(original).Volume < 1e-6

contacts = []
preserved = {}
for obj in document.Objects:
    if obj.Name == pan_name or not hasattr(obj, 'Shape') or obj.Shape.isNull():
        continue
    shape = obj.Shape
    preserved[obj.Name] = signature(shape)
    if not shape.BoundBox.intersect(original.BoundBox):
        continue
    overlap = original.common(shape).Volume
    if overlap > 1e-4:
        updated = candidate.common(shape).Volume
        contacts.append({'name': obj.Name, 'before_mm3': overlap, 'after_mm3': updated})
regressed = [row for row in contacts if row['after_mm3'] < row['before_mm3'] - 1e-4]
print('volumes', original.Volume, candidate.Volume, 'regressed contacts', regressed, flush=True)
assert not regressed
pan.Shape = candidate
document.recompute()
output.mkdir()
model = output / 'candidate.FCStd'
document.saveAs(str(model.resolve()))
App.closeDocument(document.Name)
document = App.openDocument(str(model.resolve()))
try:
    assert all(signature(document.getObject(name).Shape) == shape for name, shape in preserved.items())
    saved = document.getObject(pan_name).Shape
    assert signature(saved) == signature(candidate) and not advanced_errors(saved)
finally:
    App.closeDocument(document.Name)

mesh['fcstd_sha256'] = digest(model)
(output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
report = {
    'baseline_fcstd_sha256': base_hash,
    'fcstd_sha256': mesh['fcstd_sha256'],
    'script_sha256': digest(Path(__file__)),
    'changed_objects': [pan_name],
    'retained_central_strip_mm': 104,
    'cut_profile_yz_mm': stations,
    'removed_mm3': original.Volume - candidate.Volume,
    'positive_baseline_contacts': contacts,
    'new_advanced_check_failures': errors,
    'contact_regressions': regressed,
}
(output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
