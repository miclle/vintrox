"""Trim detail roots in the saved pod frame and recheck their actual attachment."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--root', type=float, required=True)
    parser.add_argument('--seat-ridges', choices=('translate', 'shear'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    model = args.output/'candidate.FCStd'
    doc = App.openDocument(str(args.base.resolve()))
    source = json.loads((args.base.parent/'geometry.json').read_text())
    records = {}
    replacements = {}
    try:
        for obj in doc.Objects:
            if not obj.Name.startswith(('LowerPodEdgeRail', 'LowerPodPetalRidge')):
                continue
            original = obj.Shape
            suffix = '_1' if original.Solids[0].CenterOfMass.x < 0 else '_001'
            frame = doc.getObject('LowerPod'+suffix).Shape.Placement
            local = original.copy()
            local.Placement = frame.inverse().multiply(local.Placement)
            cut = local.common(Part.makeBox(120,120,60,App.Vector(-60,-60,args.root)))
            if cut.isNull() or not cut.isValid() or not cut.isClosed() or len(cut.Solids) != len(original.Solids):
                raise ValueError(f'Failed root trim: {obj.Name}')
            cut.Placement = frame.multiply(cut.Placement)
            inset = 0.0
            leaf_name = next(c['pair'][1] for c in source['contacts']
                             if c['pair'][0] == obj.Name and c['pair'][1].startswith('LowerPodRib'))
            if args.seat_ridges and obj.Name.startswith('LowerPodPetalRidge'):
                leaf = doc.getObject(leaf_name).Shape
                center = local.Solids[0].CenterOfMass
                radial = App.Vector(center.x, center.y, 0)
                radial.normalize()
                inward = frame.Rotation.multVec(-radial)
                original_cut = cut.copy()
                for step in range(41):
                    inset = step * .1
                    if args.seat_ridges == 'translate':
                        cut = original_cut.copy()
                        cut.translate(inward * inset)
                    else:
                        # Pivot at the trimmed root to retain its rim contact.
                        candidate = original_cut.copy()
                        candidate.Placement = frame.inverse().multiply(candidate.Placement)
                        affine = App.Matrix()
                        affine.A13 = -radial.x * inset / 10
                        affine.A23 = -radial.y * inset / 10
                        affine.A14 = -affine.A13 * args.root
                        affine.A24 = -affine.A23 * args.root
                        cut = candidate.transformGeometry(affine)
                        cut.Placement = frame.multiply(cut.Placement)
                    if cut.common(leaf).Volume > .005:
                        break
                else:
                    raise ValueError(f'Ridge does not meet leaf after seating: {obj.Name}')
            replacements[obj.Name+'.Shape.brp'] = cut.exportBrepToString()
            records[obj.Name] = dict(suffix=suffix, radial_inset_mm=inset, removed_mm3=original.Volume-cut.Volume)
        if len(records) != 108:
            raise ValueError('Expected 108 saved detail solids')
        with ZipFile(args.base) as src, ZipFile(model, 'w', ZIP_DEFLATED) as dst:
            if replacements.keys()-set(src.namelist()):
                raise ValueError('Missing source BRep')
            for name in src.namelist():
                dst.writestr(name, replacements[name] if name in replacements else src.read(name))
        saved = App.openDocument(str(model.resolve()))
        try:
            for name, record in records.items():
                suffix = record['suffix']
                old, new = (d.getObject(name).Shape for d in (doc,saved))
                # Originating v336 per-sector checks identify the actual leaf.
                leaf = next(c['pair'][1] for c in source['contacts']
                            if c['pair'][0] == name and c['pair'][1].startswith('LowerPodRib'))
                record.update(leaf=leaf, advanced_errors=advanced_errors(new),
                              closed_valid=new.isClosed() and new.isValid(),
                              added_mm3=new.cut(old).Volume)
                for target in [leaf,'LowerPodRim'+suffix]:
                    gap = new.distToShape(saved.getObject(target).Shape)[0]
                    record[target] = dict(gap_mm=gap, old_gap_mm=old.distToShape(doc.getObject(target).Shape)[0])
        finally:
            App.closeDocument(saved.Name)
    finally:
        App.closeDocument(doc.Name)
    result = dict(baseline_fcstd_sha256=digest(args.base),fcstd_sha256=digest(model),
                  root_z_mm=args.root,parts=records)
    (args.output/'trim.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
