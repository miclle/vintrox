"""Add saved GUI appearance to a headless candidate without changing geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--appearance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('display output already exists')
    digest = lambda b: hashlib.sha256(b).hexdigest()
    with zipfile.ZipFile(args.model) as model, zipfile.ZipFile(args.appearance) as appearance:
        names = lambda z: {o.attrib['name'] for o in ET.fromstring(z.read('Document.xml')).findall('./Objects/Object')}
        if names(model) != names(appearance):
            raise ValueError('model and appearance object names differ')
        payload = {n: model.read(n) for n in model.namelist()}
        original = {n: digest(b) for n, b in payload.items()}
        gui = [n for n in appearance.namelist() if n == 'GuiDocument.xml' or
               n.startswith(('ShapeAppearance', 'LineColorArray', 'PointColorArray'))]
        if 'GuiDocument.xml' not in gui:
            raise ValueError('appearance source lacks GUI data')
        for name in gui:
            payload[name] = appearance.read(name)
    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_DEFLATED) as saved:
        for n, b in payload.items():
            saved.writestr(n, b)
    with zipfile.ZipFile(args.output) as saved:
        changed = [n for n, h in original.items() if n not in gui and digest(saved.read(n)) != h]
    if changed:
        raise ValueError(f'non-GUI members changed: {changed}')
    report = {
        'status': 'display-copy-restored; native GUI visual check pending',
        'source_model_sha256': digest(args.model.read_bytes()),
        'display_model_sha256': digest(args.output.read_bytes()),
        'appearance_source_sha256': digest(args.appearance.read_bytes()),
        'copied_gui_members': len(gui), 'non_gui_members_changed': changed,
        'document_xml_and_brep_bytes_unchanged': True,
        'display_model': args.output.name,
        'limitations': ['saved appearance payload verification; not a native GUI screenshot or physical validation'],
    }
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
