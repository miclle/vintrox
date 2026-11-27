"""Transfer the tested side cable BRep into its colored baseline archive."""
import argparse
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


def shape_properties(archive):
    document = ElementTree.fromstring(archive.read('Document.xml'))
    properties = document.find('./ObjectData/Object[@name="SideCableLeft"]/Properties')
    return {node.get('name'): ElementTree.tostring(node) for node in properties
            if node.get('name') in ('Shape', 'Placement')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('base', 'candidate', 'output'):
        parser.add_argument(f'--{argument}', type=Path, required=True)
    args = parser.parse_args()

    member = 'SideCableLeft.Shape.brp'
    with ZipFile(args.base) as base, ZipFile(args.candidate) as candidate:
        if shape_properties(base) != shape_properties(candidate):
            raise ValueError('Side cable placement or shape references differ')
        if any(name.startswith('SideCableLeft.Shape.Map.')
               for archive in (base, candidate) for name in archive.namelist()):
            raise ValueError('Side cable depends on an external element map')
        with ZipFile(args.output, 'x') as output:
            for info in base.infolist():
                if info.filename == member:
                    output.writestr(member, candidate.read(member), compress_type=info.compress_type)
                else:
                    output.writestr(info.filename, base.read(info.filename),
                                    compress_type=info.compress_type)
        with ZipFile(args.output) as output:
            changed = [name for name in base.namelist() if base.read(name) != output.read(name)]
            if changed != [member] or base.namelist() != output.namelist():
                raise ValueError(f'Unexpected archive changes: {changed}')


if __name__ == '__main__':
    main()
