"""Rotate saved petal assemblies about their hinge centres in real CAD.

Every object in each petal family receives the same rigid transform. This
keeps internal detail joints intact and avoids deforming the saved surfaces.
Shell contact and fixed-camera rendering still decide whether it is useful.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('base', 'mesh', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--angle', type=float, required=True,
                        help='signed degrees about local tangential hinge axis')
    args = parser.parse_args()
    if not math.isfinite(args.angle) or not 0 < abs(args.angle) <= 12:
        raise ValueError('angle must be finite, nonzero and within 12 degrees')
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('output must be a new empty directory')
    mesh = json.loads(args.mesh.read_text())
    baseline_hash = digest(args.base)
    if mesh['fcstd_sha256'] != baseline_hash:
        raise ValueError('baseline FCStd and mesh binding differ')
    doc = App.openDocument(str(args.base.resolve()))
    changed, records, contacts = [], [], []
    try:
        shapes = {o.Name: o.Shape.copy() for o in doc.Objects
                  if hasattr(o, 'Shape') and not o.Shape.isNull()}
        before = {n: signature(s) for n, s in shapes.items()}
        assembly = {i: [] for i in range(12)}
        for name in shapes:
            match = re.fullmatch(r'NozzlePetal(?:Inset|EdgeRail|EndHem|Ridge|Guide|Hinge)?(\d+)(?:_\d+)?', name)
            if match:
                assembly[int(match[1])].append(name)
        if sum(map(len, assembly.values())) != 108:
            raise ValueError('expected 108 saved petal family objects')
        for index, names in assembly.items():
            hinge = shapes[f'NozzlePetalHinge{index}']
            pivot = App.Vector()
            for solid in hinge.Solids:
                pivot += solid.CenterOfMass * (solid.Volume/hinge.Volume)
            theta = math.radians(index*30+30)
            local_axis = App.Vector(-math.sin(theta), math.cos(theta), 0)
            axis = shapes[f'NozzlePetal{index}'].Placement.Rotation.multVec(local_axis)
            for name in names:
                shape = shapes[name].copy()
                shape.rotate(pivot, axis, args.angle)
                errors = advanced_errors(shape)
                old_errors = advanced_errors(shapes[name])
                if (not shape.isValid() or not shape.isClosed() or
                        len(shape.Solids) != len(shapes[name].Solids) or
                        errors != old_errors):
                    raise ValueError(f'geometry check failed: {name}')
                doc.getObject(name).Shape = shape
                changed.append(name)
                records.append({'name': name, 'index': index,
                                'pivot_world_mm': list(pivot),
                                'axis_world': list(axis),
                                'baseline_advanced_errors': old_errors,
                                'advanced_errors': errors,
                                'relative_volume_change': abs(shape.Volume/shapes[name].Volume-1)})
            leaf = doc.getObject(f'NozzlePetal{index}').Shape
            for name in names + ['BassNozzleShell', 'BassNozzleMouthRing', 'BassNozzleRolledLip']:
                if name == f'NozzlePetal{index}' or name not in shapes:
                    continue
                old_gap = shapes[f'NozzlePetal{index}'].distToShape(shapes[name])[0]
                gap = leaf.distToShape(doc.getObject(name).Shape)[0]
                contacts.append({'objects': [f'NozzlePetal{index}', name],
                                 'baseline_gap_mm': old_gap, 'gap_mm': gap,
                                 'regressed': gap > max(.01, old_gap+1e-5)})
        doc.recompute()
        preserved = [n for n in shapes if n not in changed]
        for name in preserved:
            if signature(doc.getObject(name).Shape) != before[name]:
                raise ValueError('unintended change: '+name)
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output/'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)
    saved = App.openDocument(str(model.resolve()))
    try:
        for name in preserved:
            if signature(saved.getObject(name).Shape) != before[name]:
                raise ValueError('saved preserved shape differs: '+name)
        for item in mesh['objects']:
            if item['name'] in changed:
                vertices, faces = saved.getObject(item['name']).Shape.tessellate(.12)
                item.update(vertices=[list(v) for v in vertices], faces=faces)
    finally:
        App.closeDocument(saved.Name)
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    report = {'status': 'hinge-angle appearance candidate; fixed-camera review pending',
              'baseline_fcstd_sha256': baseline_hash, 'fcstd_sha256': digest(model),
              'script_sha256': digest(Path(__file__)), 'hinge_angle_degrees': args.angle,
              'changed_objects': sorted(changed), 'preserved_shape_count': len(preserved),
              'parts': records, 'contacts': contacts,
              'new_advanced_check_failures': [],
              'contact_regressions': [c for c in contacts if c['regressed']],
              'protected_supports_preserved': all(n in preserved for n in shapes
                                                if n.startswith(('Support', 'CentralSupport'))),
              'screen_geometry_preserved': all(n in preserved for n in
                                            ['ScreenPanel210x160x2', 'ActiveArea200x150']),
              'limitations': ['hinge angle is an appearance hypothesis',
                              'shell contact is measured but not a manufacturing fit check',
                              'flat measured panel preserved; curved cover remains an assumption',
                              'no physical, manufacturing, optical, thermal or electrical acceptance']}
    (args.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'changed_objects': len(changed), 'contacts': len(contacts),
                      'contact_regressions': len(report['contact_regressions'])}))


if __name__ == '__main__':
    main()
