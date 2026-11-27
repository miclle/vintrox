"""Preserve the forward shoulder and retain the contracted rear section."""
import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, digest

p = argparse.ArgumentParser(description=__doc__)
for name in ('base', 'wide', 'mesh', 'out'):
    p.add_argument('--' + name, required=True, type=Path)
p.add_argument('--transition', type=float, default=230)
a = p.parse_args()
data = json.loads(a.mesh.read_text())
assert data['fcstd_sha256'] == digest(a.base)
a.out.mkdir(parents=True)
model = a.out / 'candidate.FCStd'
narrow = App.openDocument(str(a.base.resolve()))
wide = App.openDocument(str(a.wide.resolve()))
changes = {}
for sign, side in ((-1, 'Left'), (1, 'Right')):
    name = 'RearArmourCheek' + side
    original = wide.getObject(name).Shape
    current = narrow.getObject(name).Shape
    x = -130 if sign < 0 else 80
    front = Part.makeBox(50, a.transition - 140, 195, App.Vector(x, 140, 45))
    back = Part.makeBox(50, 257 - a.transition, 195, App.Vector(x, a.transition, 45))
    shape = original.common(front).fuse(current.common(back)).removeSplitter()
    if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1 or advanced_errors(shape):
        raise ValueError('Invalid shoulder: ' + name)
    changes[name + '.Shape.brp'] = shape.exportBrepToString()
with ZipFile(a.base) as source, ZipFile(model, 'w', ZIP_DEFLATED) as output:
    for name in source.namelist():
        output.writestr(name, changes[name] if name in changes else source.read(name))
saved = App.openDocument(str(model.resolve()))
joins = []
for side in ('Left', 'Right'):
    name = 'RearArmourCheek' + side
    before = narrow.getObject(name).Shape
    shape = saved.getObject(name).Shape
    assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1 and not advanced_errors(shape)
    points, faces = shape.tessellate(.12)
    item = next(item for item in data['objects'] if item['name'] == name)
    item.update(vertices=[list(point) for point in points], faces=faces)
    for neighbor in ('RearStructuralFrame', 'RearServicePanel', 'RearLowerSlope',
                     'SideClosure' + side, 'SideGuard' + side, 'SideMechanicalBacking' + side):
        other = saved.getObject(neighbor).Shape
        before_gap = before.distToShape(other)[0]
        gap = shape.distToShape(other)[0]
        joins.append({'objects': [name, neighbor], 'baseline_gap_mm': before_gap,
                      'gap_mm': gap, 'contact_lost': before_gap <= .01 < gap})
assert not any(row['contact_lost'] for row in joins)
App.closeDocument(saved.Name)
App.closeDocument(wide.Name)
App.closeDocument(narrow.Name)
data['fcstd_sha256'] = digest(model)
(a.out / 'meshes.json').write_text(json.dumps(data, separators=(',', ':')))
(a.out / 'geometry.json').write_text(json.dumps({
    'fcstd_sha256': data['fcstd_sha256'], 'baseline_fcstd_sha256': digest(a.base),
    'wide_donor_fcstd_sha256': digest(a.wide), 'transition_y_mm': a.transition,
    'changed_archive_members': sorted(changes), 'contacts': joins,
}, indent=2) + '\n')
