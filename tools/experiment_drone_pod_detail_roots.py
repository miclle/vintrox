"""Terminate small-pod decorative rails at the lip instead of through the shell.

Only the hidden/rootward part of each saved ridge/rail is trimmed. The visible
terminal and body are retained as saved solids, without resynthesizing lofts.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['base', 'mesh', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--root-z', type=float, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('output must be empty')
    mesh = json.loads(args.mesh.read_text())
    assert mesh['fcstd_sha256'] == digest(args.base)
    doc = App.openDocument(str(args.base.resolve()))
    before = {o.Name: signature(o.Shape) for o in doc.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()}
    records = []
    try:
        for obj in doc.Objects:
            if not obj.Name.startswith(('LowerPodPetalRidge', 'LowerPodEdgeRail')):
                continue
            previous = obj.Shape.copy()
            local = previous.copy()
            placement = local.Placement
            local.Placement = App.Placement()
            shape = local.common(Part.makeBox(100, 100, 30, App.Vector(-50, -50, args.root_z)))
            shape.Placement = placement.multiply(shape.Placement)
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == len(previous.Solids)
            errors = advanced_errors(shape)
            assert errors == advanced_errors(previous), (obj.Name, errors)
            added_volume = shape.cut(previous).Volume
            assert added_volume < 1e-6, (obj.Name, added_volume)
            obj.Shape = shape
            records.append({'name': obj.Name, 'advanced_errors': errors,
                            'added_volume_mm3': added_volume,
                            'removed_volume_mm3': previous.Volume-shape.Volume})
        assert len(records) == 108
        doc.recompute()
        args.output.mkdir(parents=True)
        model = args.output/'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)
    saved = App.openDocument(str(model.resolve()))
    try:
        changed = [r['name'] for r in records]
        preserved = [n for n in before if n not in changed]
        assert all(signature(saved.getObject(n).Shape) == before[n] for n in preserved)
        for item in mesh['objects']:
            if item['name'] in changed:
                vertices, faces = saved.getObject(item['name']).Shape.tessellate(.12)
                item.update(vertices=[list(v) for v in vertices], faces=faces)
        mesh['fcstd_sha256'] = digest(model)
        (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
        report = {'baseline_fcstd_sha256': digest(args.base), 'fcstd_sha256': digest(model),
                  'script_sha256': digest(Path(__file__)), 'changed_objects': changed,
                  'preserved_objects': preserved, 'parts': records, 'root_local_z_mm': args.root_z,
                  'new_advanced_check_failures': [], 'contact_checks_pending': True,
                  'support_clearance_basis': 'each changed solid is contained in its baseline solid within 1e-6 mm3; no support volume can be newly added',
                  'limitations': ['root termination is inferred from visible shell/lip boundary',
                                 'contact and image verification required; no manufacturing acceptance']}
        (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
        print('trimmed roots', len(records))
    finally:
        App.closeDocument(saved.Name)


if __name__ == '__main__':
    main()
