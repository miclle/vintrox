"""Add the visible concentric rim and recessed socket to the rear barrel cap."""

import argparse
import json
from pathlib import Path

import FreeCAD as App

from drone_concept import (BARREL_REAR_SOCKET_X_MM, BARREL_REAR_SOCKET_Z_MM,
                           barrel_rear_cap_shape)
from experiment_drone_petal_axial import advanced_errors, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('base', 'mesh', 'output'):
        parser.add_argument('--' + argument, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output must be empty')
    mesh = json.loads(args.mesh.read_text())
    base_hash = digest(args.base)
    if mesh['fcstd_sha256'] != base_hash:
        raise ValueError('mesh does not match saved baseline')

    name = 'UtilityCollarLeft3'
    doc = App.openDocument(str(args.base.resolve()))
    try:
        obj = doc.getObject(name)
        previous = obj.Shape
        shape = barrel_rear_cap_shape()
        if not shape.isValid() or len(shape.Solids) != 1 or not shape.isClosed():
            raise ValueError('invalid rear cap')
        errors = advanced_errors(shape)
        liner = doc.getObject('UtilityLinerLeft').Shape
        boot = doc.getObject('UtilityCableBootLeft').Shape
        contacts = {
            'liner_overlap_mm3': shape.common(liner).Volume,
            'boot_overlap_mm3': shape.common(boot).Volume,
            'previous_liner_overlap_mm3': previous.common(liner).Volume,
            'previous_boot_overlap_mm3': previous.common(boot).Volume,
        }
        # The visible socket ends within the cap. Sample the recess and floor.
        socket_open = not shape.isInside(App.Vector(BARREL_REAR_SOCKET_X_MM, 157.75, BARREL_REAR_SOCKET_Z_MM), .001, True)
        socket_floor = shape.isInside(App.Vector(BARREL_REAR_SOCKET_X_MM, 155.5, BARREL_REAR_SOCKET_Z_MM), .001, True)
        if not socket_open or not socket_floor:
            raise ValueError('expected a recessed socket with a solid floor')
        support_overlaps = {
            part.Name: shape.common(part.Shape).Volume - previous.common(part.Shape).Volume
            for part in doc.Objects
            if part.Name.startswith(('SupportShaft', 'SupportFoot', 'SupportSocket', 'CentralSupportSeat'))
        }
        obj.Shape = shape
        doc.recompute()
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output / 'candidate.FCStd'
        doc.saveAs(str(model.resolve()))
    finally:
        App.closeDocument(doc.Name)

    mesh['fcstd_sha256'] = digest(model)
    (args.output / 'meshes.json').write_text(json.dumps(mesh, separators=(',', ':')))
    regressions = [part for part, delta in support_overlaps.items() if delta > 1e-6]
    regressions.extend(key for key in ('liner_overlap_mm3', 'boot_overlap_mm3')
                       if contacts[key] <= .01)
    report = {
        'baseline_fcstd_sha256': base_hash,
        'fcstd_sha256': mesh['fcstd_sha256'],
        'script_sha256': digest(Path(__file__)),
        'changed_objects': [name],
        'contacts': contacts,
        'support_overlap_deltas_mm3': support_overlaps,
        'socket_probes': {'opening': socket_open, 'floor': socket_floor},
        'new_advanced_check_failures': errors,
        'contact_regressions': regressions,
    }
    (args.output / 'candidate-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
