"""Package an axial diagnostic with preserved BReps, native colors and STEP.

Does not waive the diagnostic's advanced BOP or contact failures. Unchanged
archive members are restored before reopening and exporting the final model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import Import


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--diagnostic', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--appearance-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('output must be a new empty directory')
    report = json.loads((args.diagnostic/'candidate-check.json').read_text())
    mesh = json.loads((args.diagnostic/'meshes.json').read_text())
    source = args.diagnostic/'candidate.FCStd'
    if (report['baseline_fcstd_sha256'] != digest(args.base) or
            report['fcstd_sha256'] != digest(source) or
            mesh['fcstd_sha256'] != digest(source)):
        raise ValueError('diagnostic source hashes differ')
    changed = set(report['changed_objects'])
    with zipfile.ZipFile(args.base) as base, zipfile.ZipFile(source) as saved, zipfile.ZipFile(args.appearance_source) as appearance:
        payloads = {n: saved.read(n) for n in saved.namelist()}
        preserved = [n for n in base.namelist() if
                     (n.endswith('.brp') or '.Shape.Map.' in n) and
                     n.split('.Shape.')[0] not in changed]
        for name in preserved:
            payloads[name] = base.read(name)
        gui = [n for n in appearance.namelist() if n == 'GuiDocument.xml' or
               n.startswith(('ShapeAppearance', 'LineColorArray', 'PointColorArray'))]
        if 'GuiDocument.xml' not in gui:
            raise ValueError('appearance source lacks native GUI data')
        geometry = {n: hashlib.sha256(b).hexdigest() for n, b in payloads.items() if n not in gui}
        for name in gui:
            payloads[name] = appearance.read(name)
    args.output.mkdir(parents=True, exist_ok=True)
    model = args.output/'candidate.FCStd'
    with zipfile.ZipFile(model, 'w', compression=zipfile.ZIP_DEFLATED) as saved:
        for name, data in payloads.items():
            saved.writestr(name, data)
    with zipfile.ZipFile(model) as saved:
        assert all(hashlib.sha256(saved.read(n)).hexdigest() == h for n, h in geometry.items())
    doc = App.openDocument(str(model.resolve()))
    try:
        for item in mesh['objects']:
            if item['name'] in changed:
                vertices, faces = doc.getObject(item['name']).Shape.tessellate(.12)
                item.update(vertices=[list(v) for v in vertices], faces=faces)
        Import.export([doc.getObject(o['name']) for o in mesh['objects']],
                      str((args.output/'candidate.step').resolve()))
    finally:
        App.closeDocument(doc.Name)
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report.update(diagnostic_fcstd_sha256=report['fcstd_sha256'],
                  fcstd_sha256=digest(model), step_sha256=digest(args.output/'candidate.step'),
                  finalizer_sha256=digest(Path(__file__)),
                  appearance_source_sha256=digest(args.appearance_source),
                  gui_members_copied=len(gui), unchanged_archive_members_restored=len(preserved),
                  geometry_unchanged_during_gui_restore=True,
                  changed_mesh_geometry='retessellated from final reopened FCStd')
    (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'fcstd_sha256': digest(model), 'changed': len(changed),
                      'new_advanced_failures': len(report['new_advanced_check_failures']),
                      'contact_regressions': len(report['contact_regressions'])}))


if __name__ == '__main__':
    main()
