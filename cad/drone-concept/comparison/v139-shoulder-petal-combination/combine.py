import hashlib
import json
import sys
from pathlib import Path
import FreeCAD as App

base_path, base_mesh, output, *sources = map(Path, sys.argv[1:])
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

base_hash = digest(base_path)
mesh = json.loads(base_mesh.read_text())
assert mesh['fcstd_sha256'] == base_hash
base = App.openDocument(str(base_path))
changed = set()
source_records = []
contacts = []
for source in sources:
    record = json.loads((source/'candidate-check.json').read_text())
    path = source/'candidate.FCStd'
    assert record['baseline_fcstd_sha256'] == base_hash
    assert record['fcstd_sha256'] == digest(path)
    assert not record['contact_regressions'] and not record['new_advanced_check_failures']
    names = set(record['changed_objects'])
    assert changed.isdisjoint(names)
    changed.update(names)
    doc = App.openDocument(str(path))
    for name in names:
        base.getObject(name).Shape = doc.getObject(name).Shape.copy()
    App.closeDocument(doc.Name)
    contacts.extend(record['contacts'])
    source_records.append({'fcstd_sha256': record['fcstd_sha256'], 'changed_objects': sorted(names)})
base.recompute()
output.mkdir()
model = output/'candidate.FCStd'
base.saveAs(str(model))
App.closeDocument(base.Name)
base = App.openDocument(str(base_path))
saved = App.openDocument(str(model))
for name in changed:
    obj = saved.getObject(name)
    assert obj.Shape.isValid() and obj.Shape.isClosed()
for first in source_records[0]['changed_objects']:
    for second in source_records[1]['changed_objects']:
        shapes = [saved.getObject(name).Shape for name in (first, second)]
        assert not shapes[0].BoundBox.intersect(shapes[1].BoundBox), (first,second)
mesh['fcstd_sha256'] = digest(model)
(output/'meshes.json').write_text(json.dumps(mesh,separators=(',', ':')))
(output/'candidate-check.json').write_text(json.dumps({
    'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': digest(model),
    'changed_objects': sorted(changed), 'source_candidates': source_records,
    'inter_family_pair_checks': len(source_records[0]['changed_objects'])*len(source_records[1]['changed_objects']),
    'source_contacts': contacts, 'new_advanced_check_failures': [], 'contact_regressions': [],
    'script_sha256': digest(Path(__file__)),
},indent=2)+'\n')
