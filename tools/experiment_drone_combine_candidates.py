"""Combine disjoint saved-CAD trials without changing the baseline contract."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import Import


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(shape):
    b = shape.BoundBox
    return {'solids': len(shape.Solids), 'valid': bool(shape.isValid()),
            'closed': all(s.isClosed() for s in shape.Solids),
            'volume_mm3': round(shape.Volume, 6), 'area_mm2': round(shape.Area, 6),
            'bbox_mm': [round(v, 6) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)]}


def main():
    p = argparse.ArgumentParser()
    for name in ['base', 'shoulders', 'grip', 'base-mesh', 'appearance-source', 'output']:
        p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('output must be empty')
    base_hash = digest(args.base)
    mesh = json.loads(args.base_mesh.read_text())
    assert mesh['fcstd_sha256'] == base_hash
    shoulder_report = json.loads((args.shoulders/'candidate-check.json').read_text())
    grip_report = json.loads((args.grip/'candidate-check.json').read_text())
    shoulder_names = set(shoulder_report['changed_objects'])
    grip_names = set(grip_report['changed_objects'])
    assert shoulder_names == {'RearArmourCheekLeft', 'RearArmourCheekRight'}
    assert grip_names == {f'GripBand{i}' for i in range(10)}
    assert shoulder_names.isdisjoint(grip_names)
    docs = [App.openDocument(str(args.base.resolve())),
            App.openDocument(str((args.shoulders/'candidate.FCStd').resolve())),
            App.openDocument(str((args.grip/'candidate.FCStd').resolve()))]
    base, shoulders, grip = docs
    before = {o.Name: signature(o.Shape) for o in base.Objects
              if hasattr(o, 'Shape') and not o.Shape.isNull()}
    changed = sorted(shoulder_names | grip_names)
    try:
        for name in sorted(shoulder_names):
            shape = shoulders.getObject(name).Shape.copy()
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
            base.getObject(name).Shape = shape
        for name in sorted(grip_names):
            shape = grip.getObject(name).Shape.copy()
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
            base.getObject(name).Shape = shape
        base.recompute()
        args.output.mkdir(parents=True)
        model = args.output/'candidate.FCStd'
        base.saveAs(str(model.resolve()))
    finally:
        for doc in docs:
            App.closeDocument(doc.Name)
    saved = App.openDocument(str(model.resolve()))
    try:
        preserved = []
        for name, old in before.items():
            obj = saved.getObject(name)
            assert obj is not None and obj.Shape.isValid() and obj.Shape.isClosed()
            if name not in changed:
                assert signature(obj.Shape) == old, name
                preserved.append(name)
        supports = [o for o in saved.Objects if o.Name.startswith(
            ('SupportShaft','SupportSocket','SupportFoot','CentralSupportSeat'))]
        support_checks = []
        base_doc = App.openDocument(str(args.base.resolve()))
        try:
            for obj in supports:
                delta = obj.Shape.cut(base_doc.getObject(obj.Name).Shape).Volume + \
                        base_doc.getObject(obj.Name).Shape.cut(obj.Shape).Volume
                support_checks.append({'name': obj.Name, 'symmetric_difference_mm3': delta})
                assert delta < 1e-6
        finally:
            App.closeDocument(base_doc.Name)
        for item in mesh['objects']:
            if item['name'] in changed:
                vertices, faces = saved.getObject(item['name']).Shape.tessellate(.12)
                item.update(vertices=[list(v) for v in vertices], faces=faces)
        Import.export([saved.getObject(item['name']) for item in mesh['objects']],
                      str((args.output/'candidate.step').resolve()))
    finally:
        App.closeDocument(saved.Name)
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    with zipfile.ZipFile(args.base) as base_zip, zipfile.ZipFile(model) as saved_zip, \
         zipfile.ZipFile(args.appearance_source) as appearance:
        payloads = {n: saved_zip.read(n) for n in saved_zip.namelist()}
        members = [n for n in base_zip.namelist() if
                   (n.endswith('.brp') or '.Shape.Map.' in n) and
                   n.split('.Shape.')[0] not in changed]
        for name in members:
            payloads[name] = base_zip.read(name)
        gui = [n for n in appearance.namelist() if n == 'GuiDocument.xml' or
               n.startswith(('ShapeAppearance','LineColorArray','PointColorArray'))]
        assert 'GuiDocument.xml' in gui
        geometry = {n: hashlib.sha256(b).hexdigest() for n,b in payloads.items() if n not in gui}
        for name in gui:
            payloads[name] = appearance.read(name)
    with zipfile.ZipFile(model, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in payloads.items(): out.writestr(name, data)
    with zipfile.ZipFile(model) as check:
        assert all(digest_bytes(check.read(n)) == h for n,h in geometry.items())
    # GUI archive replacement changes the FCStd container hash. Rebind the
    # render mesh contract to the final saved file after that replacement.
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    assert json.loads((args.output/'meshes.json').read_text())['fcstd_sha256'] == digest(model)
    report = {'status': 'combined saved-CAD trial; fixed-camera comparison pending',
              'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': digest(model),
              'step_sha256': digest(args.output/'candidate.step'),
              'script_sha256': digest(Path(__file__)),
              'source_candidates': {'shoulders_fcstd_sha256': digest(args.shoulders/'candidate.FCStd'),
                                    'grip_fcstd_sha256': digest(args.grip/'candidate.FCStd')},
              'changed_objects': changed, 'preserved_objects': preserved,
              'protected_supports': support_checks, 'gui_members_copied': len(gui),
              'unchanged_geometry_members_restored': len(members),
              'geometry_unchanged_during_gui_restore': True,
              'limitations': ['disjoint trials combined without joint re-fitting',
                             'screen-space evidence required before adoption',
                             'no manufacturing or physical acceptance']}
    (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'fcstd_sha256': report['fcstd_sha256'], 'changed': len(changed),
                      'preserved': len(preserved), 'gui_members': len(gui)}))


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


if __name__ == '__main__': main()
