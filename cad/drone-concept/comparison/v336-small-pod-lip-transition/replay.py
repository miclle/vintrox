"""Advance the small exhaust lips while retaining their mounting and outlet planes."""
import argparse
import json
import math
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, digest

BAND = ('LowerPodRib', 'LowerPodPetalRidge', 'LowerPodEdgeRail')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--advance', type=float, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.advance < 17:
        parser.error('The lip must stay between its original station and the outlet')
    args.output.mkdir(parents=True, exist_ok=False)
    base = App.openDocument(str(args.base.resolve()))
    model = args.output/'candidate.FCStd'
    parts = {}
    contacts = []
    failures = []
    replacements = {}
    try:
        for suffix in ('_1', '_001'):
            shell = 'LowerPod'+suffix
            ring = 'LowerPodRim'+suffix
            diaphragm = 'LowerPodDiaphragm'+suffix
            frame = base.getObject(shell).Shape.Placement
            sectors = {}
            neighbors = {}
            for obj in base.Objects:
                name = obj.Name
                if not name.startswith('LowerPod') or name.startswith('LowerPodClamp'):
                    continue
                shape = obj.Shape.copy()
                if shape.Solids[0].CenterOfMass.x * frame.Base.x <= 0:
                    continue
                shape.Placement = frame.inverse().multiply(shape.Placement)
                matrix = App.Matrix()
                if name == shell:
                    matrix.A33 = 1 + args.advance/36
                    edited = shape.transformGeometry(matrix)
                elif name == ring:
                    shape.translate(App.Vector(0, 0, args.advance))
                    edited = shape
                else:
                    # Both axial maps meet at Z=36+advance. The leaf map also fixes Z=53.
                    scale = 1 - args.advance/17
                    matrix.A33 = scale
                    matrix.A34 = 53*(1-scale)
                    if name == diaphragm:
                        cone = next(f for f in shape.Faces if isinstance(f.Surface, Part.Cone))
                        edges = sorted((e.Curve.Center.z, e.Curve.Radius) for e in cone.Edges
                                       if isinstance(e.Curve, Part.Circle))
                        (bottom, r0), (top, r1) = edges
                        edited = Part.makeCone(r0, r1, scale*(top-bottom),
                                               App.Vector(0, 0, scale*bottom+matrix.A34))
                    elif name.startswith(BAND):
                        center = shape.Solids[0].CenterOfMass
                        sector = int(math.degrees(math.atan2(center.y, center.x)) % 360 // 20)
                        if name.startswith('LowerPodRib'):
                            sectors[sector] = name
                        else:
                            neighbors[name] = sector
                        edited = shape.transformGeometry(matrix)
                    else:
                        raise ValueError(name)
                edited.Placement = frame.multiply(edited.Placement)
                replacements[name+'.Shape.brp'] = edited.exportBrepToString()
            if len(sectors) != 18 or len(neighbors) != 54:
                raise ValueError('Unexpected number of leaves or details')
            contacts.extend((name, target) for name in sectors.values() for target in (shell, ring, diaphragm))
            contacts.extend((name, sectors[sector]) for name, sector in neighbors.items())
            contacts.extend((shell, n) for n in (ring,'LowerPodClamp'+suffix,'MainEnclosureShell',
                                                 'BottomChassis','ClosedBellyPan'))
        if len(replacements) != 150:
            raise ValueError('Missing or duplicated pod parts')
        with ZipFile(args.base) as src, ZipFile(model, 'w', ZIP_DEFLATED) as dst:
            if replacements.keys() - set(src.namelist()):
                raise ValueError('BRep not present in saved baseline archive')
            for member in src.namelist():
                dst.writestr(member, replacements[member] if member in replacements else src.read(member))
        saved = App.openDocument(str(model.resolve()))
        try:
            for member in replacements:
                name = member.split('.')[0]
                old, new = (d.getObject(name).Shape for d in (base, saved))
                errors = advanced_errors(new)
                valid = (new.isValid() and new.isClosed() and len(new.Solids) == len(old.Solids)
                         and not set(errors)-set(advanced_errors(old)))
                parts[name] = dict(valid=bool(valid), advanced_errors=errors)
                if not valid:
                    failures.append(name)
            checks = []
            for a, b in contacts:
                gaps = [d.getObject(a).Shape.distToShape(d.getObject(b).Shape)[0] for d in (base, saved)]
                checks.append(dict(pair=[a,b],baseline_gap_mm=gaps[0],saved_gap_mm=gaps[1],
                                   regressed=gaps[1] > max(.01,gaps[0]+.001)))
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(base.Name)
    report = dict(baseline_fcstd_sha256=digest(args.base), fcstd_sha256=digest(model),
                  advance_mm=args.advance, parts=parts, contacts=checks, invalid_parts=failures)
    (args.output/'geometry.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Invalid parts', failures, 'contact regressions', sum(c['regressed'] for c in checks))
    if failures or any(c['regressed'] for c in checks):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
