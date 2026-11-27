"""Adjust the small-pod leaf band in each saved pod's local coordinates."""

import argparse
import json
import math
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, digest

LEAF_PREFIXES = ('LowerPodRib', 'LowerPodEdgeRail', 'LowerPodPetalRidge')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--axial-scale', type=float, choices=(.94, 1.06, 1.10), required=True)
    parser.add_argument('--anchor-z', type=float, choices=(30, 36), default=30,
                        help='Fixed axial station in the saved pod frame, in mm')
    args = parser.parse_args()

    mesh = json.loads(args.mesh.read_text(encoding='utf-8'))
    base_hash = digest(args.base)
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('Mesh is bound to a different FCStd')
    args.output.mkdir(parents=True)
    output = args.output / 'candidate.FCStd'
    part_records = {}
    contact_records = []
    matrix = App.Matrix()
    matrix.A33 = args.axial_scale
    matrix.A34 = args.anchor_z * (1 - args.axial_scale)
    base = App.openDocument(str(args.base.resolve()))
    try:
        pod_names = {-1: 'LowerPod_1', 1: 'LowerPod_001'}
        frames = {side: base.getObject(name).Shape.Placement for side, name in pod_names.items()}
        suffixes = {-1: '_1', 1: '_001'}
        leaves = {}
        for item in mesh['objects']:
            name = item['name']
            if not name.startswith((*LEAF_PREFIXES, 'LowerPodDiaphragm')):
                continue
            shape = base.getObject(name).Shape
            side = 1 if shape.Solids[0].CenterOfMass.x > 0 else -1
            frame = frames[side]
            local = shape.copy()
            local.Placement = frame.inverse().multiply(local.Placement)
            center = local.Solids[0].CenterOfMass
            sector = int((math.degrees(math.atan2(center.y, center.x)) % 360) // 20)
            if name.startswith('LowerPodRib'):
                if (side, sector) in leaves:
                    raise ValueError(f'Duplicate leaf sector on side {side}: {sector}')
                leaves[side, sector] = name
            if name.startswith('LowerPodDiaphragm'):
                # Rebuild the analytic cone so axial scaling does not convert its seams to splines.
                bounds = local.optimalBoundingBox(False, False)
                if abs(bounds.ZMin - 42) > 1e-6 or abs(bounds.ZMax - 44) > 1e-6:
                    raise ValueError(f'Unexpected diaphragm stations: {name}')
                start = App.Vector(0, 0, args.anchor_z + (42 - args.anchor_z) * args.axial_scale)
                edited = Part.makeCone(22.815, 19.015, 2 * args.axial_scale, start)
            else:
                edited = local.transformGeometry(matrix)
            edited.Placement = frame.multiply(edited.Placement)
            filename = f'{name}.Shape.brp'
            edited.exportBrep(str(args.output / filename))
            part_records[name] = {
                'archive_member': filename, 'side': side, 'sector': sector,
                'baseline_solids': len(shape.Solids),
                'baseline_advanced_errors': advanced_errors(shape),
            }
        if len(part_records) != 146:
            raise ValueError(f'Expected 146 leaf-band and diaphragm shapes, found {len(part_records)}')
        if len(leaves) != 36:
            raise ValueError(f'Expected 36 occupied leaf sectors, found {len(leaves)}')
        with ZipFile(args.base) as source, ZipFile(output, 'w', ZIP_DEFLATED) as target:
            replacements = {record['archive_member'] for record in part_records.values()}
            if not replacements.issubset(source.namelist()):
                raise ValueError('Missing saved leaf-band members')
            for filename in source.namelist():
                payload = (args.output / filename).read_bytes() if filename in replacements else source.read(filename)
                target.writestr(filename, payload)

        candidate = App.openDocument(str(output.resolve()))
        try:
            for item in mesh['objects']:
                name = item['name']
                if name not in part_records:
                    continue
                previous = base.getObject(name).Shape
                shape = candidate.getObject(name).Shape
                record = part_records[name]
                record.update(valid=shape.isValid(), closed=shape.isClosed(),
                              solids=len(shape.Solids), advanced_errors=advanced_errors(shape))
                side = record['side']
                suffix = suffixes[side]
                if name.startswith('LowerPodRib'):
                    neighbors = [pod_names[side], 'LowerPodRim' + suffix, 'LowerPodDiaphragm' + suffix]
                elif name.startswith(LEAF_PREFIXES):
                    neighbors = [leaves[side, record['sector']]]
                else:
                    neighbors = []
                for neighbor in neighbors:
                    old_gap = previous.distToShape(base.getObject(neighbor).Shape)[0]
                    gap = shape.distToShape(candidate.getObject(neighbor).Shape)[0]
                    contact_records.append({'objects': [name, neighbor], 'baseline_gap_mm': old_gap,
                                            'gap_mm': gap, 'regressed': gap > max(.01, old_gap + .001)})
                vertices, faces = shape.tessellate(.12)
                item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
        finally:
            App.closeDocument(candidate.Name)
    finally:
        App.closeDocument(base.Name)

    mesh['fcstd_sha256'] = digest(output)
    report = {
        'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
        'axial_scale': args.axial_scale, 'anchor_z_mm': args.anchor_z,
        'gap_change_tolerance_mm': .001, 'diaphragm_radial_allowance_mm': .015,
        'parts': part_records, 'contacts': contact_records,
        'new_advanced_failures': [name for name, record in part_records.items()
                                  if record['advanced_errors'] != record['baseline_advanced_errors']],
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    if report['new_advanced_failures'] or any(
        not record['valid'] or not record['closed'] or record['solids'] != record['baseline_solids']
        for record in part_records.values()
    ) or any(record['regressed'] for record in contact_records):
        raise ValueError('Small-pod saved geometry or contact check failed')
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))


if __name__ == '__main__':
    main()
