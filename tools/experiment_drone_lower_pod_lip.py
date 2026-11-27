"""Rebuild only saved small-pod shells and petals around a fitted shell lip.

Root and terminal section stations stay fixed, not their neighborhoods. Source geometry is read from the saved
baseline; only the small-pod family uses its documented circular-section model.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part

from drone_concept import round_loft, sector_wire, tube, cylinder
from experiment_drone_petal_axial import advanced_errors, signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['base', 'mesh', 'fit', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('output must be empty')
    fit = json.loads(args.fit.read_text())
    mesh = json.loads(args.mesh.read_text())
    assert fit['baseline_fcstd_sha256'] == mesh['fcstd_sha256'] == digest(args.base)
    lip_z, radius = fit['parameters']

    def warp_z(z):
        if z <= 10:
            return z
        return z+(lip_z-36)*((z-10)/26 if z <= 36 else (53-z)/17)

    def warp_r(r, z):
        weight = max(0, (z-10)/26 if z <= 36 else (53-z)/17)
        return r*(1+(radius/27.5-1)*weight)

    def section(z, ro, ri):
        return warp_z(z), warp_r(ro, z), warp_r(ri, z)

    doc = App.openDocument(str(args.base.resolve()))
    before = {o.Name: signature(o.Shape) for o in doc.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()}
    original = {o.Name: o.Shape.copy() for o in doc.Objects if o.Name.startswith('LowerPod')}
    changed, records = [], []
    try:
        for obj in doc.Objects:
            name = obj.Name
            if name not in original or name.startswith('LowerPodClamp'):
                continue
            local = obj.Shape.copy()
            placement = local.Placement
            local.Placement = App.Placement()
            centre = local.Solids[0].CenterOfMass
            angle = math.degrees(math.atan2(centre.y, centre.x)) % 360
            index = int(angle//20)
            if name.startswith('LowerPodEdgeRail'):
                edge = min([2.2, 17.8], key=lambda e: abs(angle-(index*20+e)))
                a = math.radians(index*20+edge)
                points = [(warp_r(ro, z)*math.cos(a), warp_r(ro, z)*math.sin(a), warp_z(z))
                          for z, ro in [(30, 27.5), (40, 25.8), (53, 20.53624)]]
                shape = tube(points, .35)
            elif name.startswith(('LowerPodRib', 'LowerPodPetalRidge')):
                sections = [section(z, ro, ri) for z, ro, ri in
                            [(30, 27.5, 24.8), (40, 25.8, 23.1), (53, 20.53624, 18.1)]]
                if name.startswith('LowerPodRib'):
                    shape = Part.makeLoft([sector_wire(ro, ri, z, index*20+1.5, index*20+18.5)
                                           for z, ro, ri in sections], True, False)
                    recess = Part.makeLoft([sector_wire(warp_r(ro+1, z), warp_r(ro-.7, z), warp_z(z),
                                                       index*20+4, index*20+16)
                                            for z, ro in [(32, 27.4), (40, 25.8), (51, 21.6)]], True, False)
                    shape = shape.cut(recess)
                else:
                    shape = Part.makeLoft([sector_wire(warp_r(ro+.5, z), warp_r(ro, z), warp_z(z),
                                                       index*20+8, index*20+10)
                                            for z, ro in [(30, 27.5), (40, 25.8), (53, 20.53624)]], True, False)
            elif name.startswith('LowerPodRim'):
                shape = Part.makeTorus(radius, .8, App.Vector(0, 0, lip_z))
            elif name.startswith('LowerPodDiaphragm'):
                shape = cylinder(warp_r(21.5, 44), 2, (0, 0, warp_z(44)))
            else:
                shape = round_loft([(warp_z(z), warp_r(r, z), 0)
                                    for z, r in [(0,18), (10,24), (27,28), (37,27)]])
                inside = round_loft([(warp_z(z), warp_r(r, z), 0)
                                     for z, r in [(-1,14), (10,20), (27,24), (39,23)]])
                shape = shape.cut(inside)
            shape.Placement = placement.multiply(shape.Placement)
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == len(original[name].Solids), name
            old_errors, errors = advanced_errors(original[name]), advanced_errors(shape)
            assert errors == old_errors, (name, errors, old_errors)
            obj.Shape = shape
            changed.append(name)
            records.append({'name': name, 'index': index if 'Rib' in name or 'Rail' in name or 'Ridge' in name else None,
                            'baseline_advanced_errors': old_errors, 'advanced_errors': errors})
        doc.recompute()
        args.output.mkdir(parents=True)
        model = args.output/'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)
    saved = App.openDocument(str(model.resolve()))
    try:
        preserved = [n for n in before if n not in changed]
        for name in preserved:
            assert signature(saved.getObject(name).Shape) == before[name], name
        supports = [saved.getObject(n) for n in preserved if n.startswith(('Support', 'CentralSupport'))]
        collisions = []
        for name in changed:
            shape = saved.getObject(name).Shape
            assert advanced_errors(shape) == advanced_errors(original[name]), name
            for support in supports:
                overlap = shape.common(support.Shape).Volume
                previous = original[name].common(support.Shape).Volume
                assert overlap <= previous+1e-6, (name, support.Name, overlap, previous)
                if overlap or previous:
                    collisions.append({'objects': [name, support.Name], 'overlap_mm3': overlap, 'baseline_overlap_mm3': previous})
            vertices, faces = shape.tessellate(.12)
            item = next(i for i in mesh['objects'] if i['name'] == name)
            item.update(vertices=[list(v) for v in vertices], faces=faces)
        report = {'status': 'saved small-pod lip candidate; complete view and export verification pending',
                  'baseline_fcstd_sha256': digest(args.base), 'fcstd_sha256': digest(model),
                  'script_sha256': digest(Path(__file__)), 'fit_sha256': digest(args.fit),
                  'changed_objects': changed, 'preserved_objects': preserved, 'parts': records,
                  'new_advanced_check_failures': [], 'contact_checks_pending': True,
                  'support_pair_checks': len(changed)*len(supports), 'nonzero_support_overlaps': collisions,
                  'lip_local_z_mm': lip_z, 'lip_major_radius_mm': radius,
                  'fixed_root_stations_mm': [0,10], 'fixed_terminal_z_mm': 53,
                  'limitations': ['documented circular-section pod hypothesis; no complete source geometry',
                                 'piecewise station remapping, not manufacturing design',
                                 'part contacts and fixed-camera comparison require independent checking']}
        (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
        mesh['fcstd_sha256'] = digest(model)
        (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
        print('changed', len(changed), 'support checks', report['support_pair_checks'])
    finally:
        App.closeDocument(saved.Name)


if __name__ == '__main__':
    main()
