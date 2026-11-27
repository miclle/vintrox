"""Move the saved visual bass bowl and cap along their existing axis."""
import argparse
import json
from pathlib import Path

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest

parser = argparse.ArgumentParser(description=__doc__)
for name in ('model', 'meshes', 'output'):
    parser.add_argument('--' + name, type=Path, required=True)
parser.add_argument('--depth-mm', type=float, required=True)
args = parser.parse_args()
mesh = json.loads(args.meshes.read_text())
base_hash = digest(args.model)
assert mesh['fcstd_sha256'] == base_hash
doc = App.openDocument(str(args.model))
names = ('BassVisualCone', 'BassDustCap')
axis = App.Vector(*mesh['bass_axis'])
axis.normalize()
for name in names:
    obj = doc.getObject(name)
    moved = obj.Shape.copy()
    moved.translate(axis * -args.depth_mm)
    assert moved.isValid() and moved.isClosed() and len(moved.Solids) == 1
    assert advanced_errors(moved) == advanced_errors(obj.Shape)
    obj.Shape = moved
doc.recompute()
args.output.mkdir()
model = args.output / 'candidate.FCStd'
doc.saveAs(str(model))
App.closeDocument(doc.Name)

saved = App.openDocument(str(model))
cone = saved.getObject('BassVisualCone').Shape
contacts = {}
for name in ('BassDustCap', 'BassInnerThroat', 'BassNozzleShell', 'BassChamberBackplate'):
    other = saved.getObject(name).Shape
    contacts[name] = {'gap_mm': cone.distToShape(other)[0],
                      'overlap_mm3': abs(cone.common(other).Volume)}
assert all(contacts[name]['gap_mm'] < .01 and contacts[name]['overlap_mm3'] > .01
           for name in ('BassDustCap', 'BassInnerThroat'))
assert all(contacts[name]['overlap_mm3'] < .01
           for name in ('BassNozzleShell', 'BassChamberBackplate'))
App.closeDocument(saved.Name)
model_hash = digest(model)
mesh['fcstd_sha256'] = model_hash
(args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
record = {'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': model_hash,
          'script_sha256': digest(Path(__file__)), 'changed_objects': list(names),
          'depth_mm': args.depth_mm, 'contacts': contacts,
          'new_advanced_check_failures': [], 'contact_regressions': []}
(args.output / 'candidate-check.json').write_text(json.dumps(record, indent=2) + '\n')
