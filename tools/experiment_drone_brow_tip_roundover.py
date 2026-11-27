"""Round the two forward bottom edges of the saved U-shaped brow liner."""

import argparse
import json
from math import sqrt
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, digest


def tip_edges(shape):
    bottom = shape.optimalBoundingBox(False, False).ZMin
    tips = [edge for edge in shape.Edges
            if abs(edge.BoundBox.ZMin - bottom) < .001
            and edge.BoundBox.ZLength < .001
            and edge.BoundBox.YLength < .1
            and edge.BoundBox.XLength > .1]
    front = min(edge.CenterOfMass.y for edge in tips)
    edges = [edge for edge in tips if abs(edge.CenterOfMass.y - front) < .01]
    if len(edges) != 2 or edges[0].CenterOfMass.x * edges[1].CenterOfMass.x >= 0:
        raise ValueError('Expected two mirrored front tip edges')
    return edges


def trim_profile(shape, radius, cover_front):
    # The front plane recedes by 0.394 mm of Y per mm of Z. Construct
    # the arc in profile coordinates before applying that saved slope.
    edge = tip_edges(shape)[0]
    front, bottom = edge.CenterOfMass.y, edge.CenterOfMass.z
    bounds = shape.BoundBox

    def point(y, z):
        return App.Vector(bounds.XMin - 1, front + y - .394 * z, bottom + z)

    start = point(radius, 0)
    end = point(0, radius)
    middle = point(radius - radius / sqrt(2), radius - radius / sqrt(2))
    # The pre-existing outer roll can extend forward of the nominal tip.
    front_limit = min(-1, bounds.YMin - front - 1) if cover_front else -1
    outer_bottom = point(front_limit, -1)
    inner_bottom = point(radius, -1)
    outer_top = point(front_limit, radius)
    cutter = Part.Face(Part.Wire([
        Part.makeLine(outer_bottom, inner_bottom), Part.makeLine(inner_bottom, start),
        Part.Arc(start, middle, end).toShape(), Part.makeLine(end, outer_top),
        Part.makeLine(outer_top, outer_bottom),
    ])).extrude(App.Vector(bounds.XLength + 2, 0, 0))
    return shape.cut(cutter)


def trim_assembly(base, output, radius, cover_front):
    names = ('ProjectingBrow', 'HoodEdge', 'BrowUnderside')
    neighbors = ('ScreenBezel', 'HoodShoulderPlateLeft', 'HoodShoulderPlateRight')
    document = App.openDocument(str(base.resolve()))
    try:
        originals = {name: document.getObject(name).Shape.copy() for name in names}
        for name, shape in originals.items():
            document.getObject(name).Shape = trim_profile(shape, radius, cover_front)
        document.recompute()
        headless = output / 'headless.FCStd'
        document.saveAs(str(headless.resolve()))
    finally:
        App.closeDocument(document.Name)
    model = output / 'candidate.FCStd'
    with (ZipFile(base) as source, ZipFile(headless) as candidate,
          ZipFile(model, 'w', compression=ZIP_DEFLATED) as result):
        members = {f'{name}.Shape.brp' for name in names}
        if not members.issubset(source.namelist()) or not members.issubset(candidate.namelist()):
            raise ValueError('Missing front brow BRep members')
        for member in source.namelist():
            archive = candidate if member in members else source
            result.writestr(member, archive.read(member))
    saved = App.openDocument(str(model.resolve()))
    try:
        records = {}
        for name, original in originals.items():
            shape = saved.getObject(name).Shape
            errors = advanced_errors(shape)
            before_errors = advanced_errors(original)
            removed = original.Volume - shape.Volume
            if (not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1
                    or sorted(errors) != sorted(before_errors) or removed <= 0):
                raise ValueError(f'Invalid saved profile trim: {name}')
            contacts = []
            for other in names + neighbors:
                if other == name:
                    continue
                current = saved.getObject(other).Shape
                previous = originals.get(other, current)
                before = original.distToShape(previous)[0]
                after = shape.distToShape(current)[0]
                contacts.append({'object': other, 'baseline_gap_mm': before,
                                 'candidate_gap_mm': after,
                                 'baseline_overlap_mm3': original.common(previous).Volume,
                                 'candidate_overlap_mm3': shape.common(current).Volume})
            records[name] = {'removed_volume_mm3': removed, 'advanced_errors': errors,
                             'contacts': contacts}
        return model, records, {
            name: saved.getObject(name).Shape.tessellate(.12) for name in names
        }
    finally:
        App.closeDocument(saved.Name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--base-mesh', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--radius', type=float, required=True)
    parser.add_argument('--assembly', action='store_true',
                        help='Cut the rounded profile into the outer brow, trim and liner')
    parser.add_argument('--cover-front', action='store_true',
                        help='Extend the assembly cutter past the pre-existing rolled rim')
    args = parser.parse_args()
    limit = 10 if args.assembly else 5
    if not 0 < args.radius <= limit:
        parser.error(f'radius must be in (0, {limit}] mm')
    if args.cover_front and not args.assembly:
        parser.error('--cover-front requires --assembly')
    base_hash = digest(args.base)
    mesh = json.loads(args.base_mesh.read_text())
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('Base mesh differs from the saved FCStd')
    args.output.mkdir(parents=True, exist_ok=False)
    if args.assembly:
        model, records, triangles = trim_assembly(
            args.base, args.output, args.radius, args.cover_front
        )
        for item in mesh['objects']:
            if item['name'] in triangles:
                vertices, faces = triangles[item['name']]
                item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
        mesh['fcstd_sha256'] = digest(model)
        (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
        report = {'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': mesh['fcstd_sha256'],
                  'script_sha256': digest(Path(__file__)), 'radius_mm': args.radius,
                  'cover_front': args.cover_front, 'changed_objects': list(records),
                  'geometry': records}
        (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
        return
    name = 'BrowUnderside'
    doc = App.openDocument(str(args.base.resolve()))
    try:
        liner = doc.getObject(name)
        original = liner.Shape.copy()
        edges = tip_edges(original)
        liner.Shape = original.makeFillet(args.radius, edges)
        doc.recompute()
        headless = args.output / 'headless.FCStd'
        doc.saveAs(str(headless.resolve()))
    finally:
        App.closeDocument(doc.Name)

    # Keep the original geometry and display archives byte-for-byte away from
    # the liner. A headless save can otherwise reserialize unrelated shapes.
    model = args.output / 'candidate.FCStd'
    with (ZipFile(args.base) as base, ZipFile(headless) as candidate,
          ZipFile(model, 'w', compression=ZIP_DEFLATED) as output):
        replaced = [member for member in base.namelist()
                    if member.startswith(name + '.Shape.')]
        if not replaced or not set(replaced).issubset(candidate.namelist()):
            raise ValueError('Missing liner archive members')
        for member in base.namelist():
            source = candidate if member in replaced else base
            output.writestr(member, source.read(member))
    saved = App.openDocument(str(model.resolve()))
    try:
        shape = saved.getObject(name).Shape
        errors = advanced_errors(shape)
        if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1 or errors:
            raise ValueError('Saved liner failed the closed solid or advanced check')
        removed = original.Volume - shape.Volume
        if removed <= 0:
            raise ValueError('The roundover did not reduce liner volume')
        joints = []
        for neighbor in ('ProjectingBrow', 'HoodEdge', 'ScreenBezel',
                         'HoodShoulderPlateLeft', 'HoodShoulderPlateRight'):
            adjacent = saved.getObject(neighbor).Shape
            joints.append({
                'object': neighbor,
                'baseline_gap_mm': original.distToShape(adjacent)[0],
                'candidate_gap_mm': shape.distToShape(adjacent)[0],
                'baseline_overlap_mm3': original.common(adjacent).Volume,
                'candidate_overlap_mm3': shape.common(adjacent).Volume,
            })
        vertices, faces = shape.tessellate(.12)
        item = next(item for item in mesh['objects'] if item['name'] == name)
        item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
    finally:
        App.closeDocument(saved.Name)

    mesh['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {
        'baseline_fcstd_sha256': base_hash,
        'fcstd_sha256': mesh['fcstd_sha256'],
        'script_sha256': digest(Path(__file__)),
        'changed_objects': [name],
        'replaced_archive_members': replaced,
        'radius_mm': args.radius,
        'front_edges_world_mm': [[list(v.Point) for v in edge.Vertexes] for edge in edges],
        'removed_volume_mm3': removed,
        'saved_solid_advanced_errors': errors,
        'contacts': joints,
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
