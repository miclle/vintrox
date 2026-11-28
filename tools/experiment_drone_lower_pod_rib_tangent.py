"""Screen a small tangential scale of the saved LowerPodRib CAD family."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def advanced_errors(shape):
    try:
        shape.check(True)
    except ValueError as error:
        return sorted(line.strip() for line in str(error).splitlines()
                      if line.startswith('Error in '))
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scale', type=float, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('output must be empty')
    args.output.mkdir(parents=True)
    base_hash = digest(args.base)
    doc = App.openDocument(str(args.base.resolve()))
    originals = {}
    changed = []
    try:
        for obj in doc.Objects:
            if not obj.Name.startswith('LowerPodRib') or obj.Shape.isNull():
                continue
            original = obj.Shape.copy()
            originals[obj.Name] = original
            local = original.copy()
            frame = local.Placement
            local.Placement = App.Placement()
            matrix = App.Matrix()
            matrix.A22 = args.scale
            candidate = local.transformGeometry(matrix)
            candidate.Placement = frame.multiply(candidate.Placement)
            if (not candidate.isValid() or not candidate.isClosed()
                    or len(candidate.Solids) != len(original.Solids)):
                raise ValueError(f'invalid transformed BRep: {obj.Name}')
            if advanced_errors(candidate) != advanced_errors(original):
                raise ValueError(f'new BRep errors: {obj.Name}')
            obj.Shape = candidate
            changed.append(obj.Name)
        if len(changed) != 36:
            raise ValueError(f'expected 36 LowerPodRib objects, got {len(changed)}')
        doc.recompute()
        model = args.output / 'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)

    # FreeCAD may reserialize untouched BReps. Restore every unrelated geometry
    # member from the baseline archive while retaining the candidate GUI state.
    restored = args.output / 'candidate.restored.FCStd'
    changed_members = {name + '.Shape.brp' for name in changed}
    with ZipFile(args.base) as source, ZipFile(model) as candidate, ZipFile(restored, 'w', ZIP_DEFLATED) as out:
        for name in candidate.namelist():
            if (name.endswith('.brp') or '.Shape.Map.' in name):
                owner = name.split('.Shape.')[0]
                if name not in changed_members and owner not in changed:
                    out.writestr(name, source.read(name))
                    continue
            out.writestr(name, candidate.read(name))
    restored.replace(model)

    saved = App.openDocument(str(model.resolve()))
    try:
        records = []
        for name, original in originals.items():
            shape = saved.getObject(name).Shape
            if (not shape.isValid() or not shape.isClosed()
                    or len(shape.Solids) != len(original.Solids)):
                raise ValueError(f'saved candidate invalid: {name}')
            records.append({'name': name, 'baseline_advanced_errors': advanced_errors(original),
                            'candidate_advanced_errors': advanced_errors(shape),
                            'volume_mm3': shape.Volume})
    finally:
        App.closeDocument(saved.Name)
    report = {
        'status': 'saved LowerPodRib tangential-scale candidate; fixed-camera comparison pending',
        'baseline_fcstd_sha256': base_hash,
        'fcstd_sha256': digest(model),
        'scale': args.scale,
        'changed_objects': changed,
        'fixed_root_and_terminal_stations': True,
        'transform': 'local tangential Y scale about the saved rib frame, Z unchanged',
        'parts': records,
        'registration': 'fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts',
        'limitations': ['appearance study using saved real CAD BReps', 'flat measured screen retained; curved reference screen remains an assumption', 'no manufacturing, fit, optical, thermal, electrical, or physical acceptance'],
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'candidate': str(model), 'changed': len(changed), 'sha256': digest(model)}))


if __name__ == '__main__':
    main()
