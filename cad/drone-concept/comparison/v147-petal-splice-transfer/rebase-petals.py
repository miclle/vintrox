"""Transfer a verified alternate leaf family onto the current saved model."""
import json
import sys
from pathlib import Path

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest

base, source, output = map(Path, sys.argv[1:])
base_model = base / 'candidate.FCStd'
source_model = source / 'candidate.FCStd'
record = json.loads((source / 'candidate-check.json').read_text())
mesh = json.loads((base / 'meshes.json').read_text())
assert mesh['fcstd_sha256'] == digest(base_model)
assert record['fcstd_sha256'] == digest(source_model)
assert not record['new_advanced_check_failures'] and not record['contact_regressions']
doc = App.openDocument(str(base_model))
trial = App.openDocument(str(source_model))
before = {obj.Name: obj.Shape.copy() for obj in doc.Objects if obj.Name.startswith('NozzlePetal')}
names = set(record['changed_objects'])
assert names <= before.keys()
for name in names:
    doc.getObject(name).Shape = trial.getObject(name).Shape.copy()
doc.recompute()
output.mkdir()
model = output / 'candidate.FCStd'
doc.saveAs(str(model))
App.closeDocument(doc.Name)
saved = App.openDocument(str(model))
issues = []
for name in sorted(names):
    shape = saved.getObject(name).Shape
    assert shape.isValid() and shape.isClosed() and len(shape.Solids) == len(before[name].Solids), name
    if advanced_errors(shape) != advanced_errors(before[name]):
        issues.append(name)
contacts = []
for pair in record['contacts']:
    a, b = pair['objects']
    first, second = (saved.getObject(name).Shape for name in (a,b))
    gap = first.distToShape(second)[0]
    contacts.append({'objects': [a,b], 'gap_mm': gap,
                     'source_gap_mm': pair['gap_mm'],
                     'regressed': gap > max(.01,pair['gap_mm']+1e-5)})
mesh['fcstd_sha256'] = digest(model)
(output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
(output / 'candidate-check.json').write_text(json.dumps({
    'baseline_fcstd_sha256': digest(base_model), 'fcstd_sha256': digest(model),
    'source_fcstd_sha256': digest(source_model), 'source_baseline_fcstd_sha256': record['baseline_fcstd_sha256'],
    'script_sha256': digest(Path(__file__)), 'changed_objects': sorted(names),
    'new_advanced_check_failures': issues, 'contacts': contacts,
    'contact_regressions': [pair for pair in contacts if pair['regressed']],
}, indent=2) + '\n')
