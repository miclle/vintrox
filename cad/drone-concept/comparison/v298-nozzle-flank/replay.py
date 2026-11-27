"""Trim the outer flank of four saved nozzle leaves with a tapered planar cut."""

import argparse
import json
import math
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, digest

LEAVES = (7, 9)
PETAL_NAME = re.compile(r'NozzlePetal(?:Inset|EdgeRail|EndHem|Ridge|Guide|Hinge)?(\d+)(?:_\d+)?')


def trim_cutter(index: int, slope: float) -> Part.Shape:
    """Build a prism that starts cutting at local Z 112 mm."""
    angle = math.radians(index * 30 + 30)
    radial = App.Vector(math.cos(angle), math.sin(angle), 0)
    side = 1 if index in (9, 10) else -1
    tangent = App.Vector(-math.sin(angle), math.cos(angle), 0) * side
    section = [(8, 112), (8 - slope * 28, 140), (30, 140), (30, 112)]
    points = [radial * -120 + tangent * width + App.Vector(0, 0, height)
              for width, height in section]
    return Part.Face(Part.makePolygon(points + points[:1])).extrude(radial * 240)


def main() -> None:
    """Save, reopen, and retessellate the trimmed geometry."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--slope', type=float, choices=(.32, .40), required=True)
    args = parser.parse_args()

    mesh = json.loads(args.mesh.read_text(encoding='utf-8'))
    baseline_hash = digest(args.base)
    if mesh['fcstd_sha256'] != baseline_hash:
        raise ValueError('Baseline meshes differ from the saved CAD')

    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output / 'candidate.FCStd'
    nozzle_axis = App.Vector(0, .574, -.819)
    nozzle_axis.normalize()
    frame = App.Placement(App.Vector(0, 180, 173), App.Rotation(App.Vector(0, 0, 1), nozzle_axis))
    cutters = {index: trim_cutter(index, args.slope) for index in LEAVES}
    records = {}
    doc = App.openDocument(str(args.base.resolve()))
    try:
        for item in mesh['objects']:
            name = item['name']
            match = PETAL_NAME.fullmatch(name)
            if match is None or int(match[1]) not in cutters:
                continue
            shape = doc.getObject(name).Shape
            local = shape.copy()
            local.Placement = frame.inverse().multiply(local.Placement)
            if local.BoundBox.ZMax <= 112:
                continue
            candidate = local.cut(cutters[int(match[1])])
            removed = local.Volume - candidate.Volume
            if removed <= 1e-5:
                continue
            candidate.Placement = frame.multiply(candidate.Placement)
            filename = f'{name}.Shape.brp'
            candidate.exportBrep(str(args.output / filename))
            records[name] = {
                'archive_member': filename,
                'removed_volume_mm3': removed,
                'baseline_solids': len(shape.Solids),
                'baseline_advanced_errors': advanced_errors(shape),
            }
        with ZipFile(args.base) as source, ZipFile(output, 'w', ZIP_DEFLATED) as target:
            replacements = {record['archive_member'] for record in records.values()}
            if not replacements or not replacements.issubset(source.namelist()):
                raise ValueError('Expected nozzle BRep archive members')
            for member in source.namelist():
                payload = ((args.output / member).read_bytes() if member in replacements
                           else source.read(member))
                target.writestr(member, payload)

        saved = App.openDocument(str(output.resolve()))
        try:
            for item in mesh['objects']:
                name = item['name']
                if name not in records:
                    continue
                record = records[name]
                shape = saved.getObject(name).Shape
                record.update(valid=shape.isValid(), closed=shape.isClosed(),
                              solids=len(shape.Solids), advanced_errors=advanced_errors(shape))
                vertices, faces = shape.tessellate(.12)
                item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)

            contacts = []
            for index in LEAVES:
                leaf = f'NozzlePetal{index}'
                attached = [f'NozzlePetalHinge{index}', 'BassNozzleMouthRing']
                attached.extend(name for name in records if name != leaf and
                                int(PETAL_NAME.fullmatch(name)[1]) == index)
                for name in attached:
                    baseline_gap = doc.getObject(leaf).Shape.distToShape(doc.getObject(name).Shape)[0]
                    gap = saved.getObject(leaf).Shape.distToShape(saved.getObject(name).Shape)[0]
                    contacts.append({'objects': [leaf, name], 'baseline_gap_mm': baseline_gap,
                                     'gap_mm': gap, 'regressed': gap > max(.01, baseline_gap + 1e-5)})
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(doc.Name)

    mesh['fcstd_sha256'] = digest(output)
    report = {
        'baseline_fcstd_sha256': baseline_hash,
        'fcstd_sha256': mesh['fcstd_sha256'],
        'changed_objects': list(records),
        'parts': records,
        'contacts': contacts,
        'taper_start_axial_mm': 112,
        'tangential_limit_at_start_mm': 8,
        'tangential_taper_slope': args.slope,
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    if any(not part['valid'] or not part['closed'] or part['solids'] != part['baseline_solids']
           or part['advanced_errors'] != part['baseline_advanced_errors']
           for part in records.values()) or any(contact['regressed'] for contact in contacts):
        raise ValueError('Saved geometry or contact checks failed')
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))


if __name__ == '__main__':
    main()
