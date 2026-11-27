"""Save a rigid-pose wing candidate without changing the authoritative model."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np

from experiment_drone_rear_cavity import signature
from study_drone_wing_pose import transform


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for key in ['base-model', 'base-meshes', 'fit', 'output']:
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    baseline = digest(args.base_model)
    mesh = json.loads(args.base_meshes.read_text())
    fit = json.loads(args.fit.read_text())
    assert mesh['fcstd_sha256'] == fit['fcstd_sha256'] == baseline
    angles = fit['angles_deg']
    document = App.openDocument(str(args.base_model))
    originals = {o.Name: signature(o.Shape) for o in document.Objects
                 if hasattr(o, 'Shape') and not o.Shape.isNull()}
    changed, advanced = [], []
    for obj in document.Objects:
        if not obj.Name.startswith('Wing') or obj.Name not in originals:
            continue
        suffix = 'Left' if 'Left' in obj.Name else 'Right'
        side = -1 if suffix == 'Left' else 1
        centre = fit['hub_centres_mm'][suffix]
        shape = obj.Shape.copy()
        def check_message(shape):
            try:
                shape.check(True)
                return None
            except ValueError as error:
                return str(error)
        before_error = check_message(shape)
        shape.rotate(App.Vector(*centre), App.Vector(1,0,0), angles[0])
        shape.rotate(App.Vector(*centre), App.Vector(0,1,0), side*angles[1])
        after_error = check_message(shape)
        advanced.append({'name':obj.Name,'baseline_error':before_error,
                         'candidate_error':after_error,'unchanged_result':before_error==after_error})
        if before_error != after_error:
            raise ValueError('Changed advanced BRep check: '+obj.Name)
        assert shape.isValid() and shape.isClosed()
        obj.Shape = shape
        item = next(o for o in mesh['objects'] if o['name'] == obj.Name)
        item['vertices'] = transform(np.array(item['vertices']), np.array(centre), side, angles).tolist()
        changed.append(obj.Name)
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output/'candidate.FCStd'
    document.recompute()
    document.saveAs(str(path))
    App.closeDocument(document.Name)
    document = App.openDocument(str(path))
    preserved = [{'name': n, 'unchanged_signature_6dp': signature(document.getObject(n).Shape)==s}
                 for n,s in originals.items() if n not in changed]
    assert all(r['unchanged_signature_6dp'] for r in preserved)
    contacts = []
    for suffix in ['Left','Right']:
        seat = document.getObject('WingHubSeat'+suffix).Shape
        for name in ['WingEdge'+suffix, 'SpeakerHubNeck'+suffix]:
            obj = document.getObject(name)
            if obj is None:
                raise ValueError('Missing wing attachment object: '+name)
            contacts.append({'objects':['WingHubSeat'+suffix,name],
                             'gap_mm':seat.distToShape(obj.Shape)[0],
                             'overlap_mm3':seat.common(obj.Shape).Volume})
    App.closeDocument(document.Name)
    mesh['fcstd_sha256'] = digest(path)
    (args.output/'meshes.json').write_text(json.dumps(mesh))
    result = {'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline,
              'fit_sha256':digest(args.fit),'script_sha256':digest(Path(__file__)),
              'angles_deg':angles,'changed_objects':changed,'preserved':preserved,
              'contacts':contacts,'advanced_checks':advanced,
              'limitations':['Any baseline BOP errors retained verbatim; this is not advanced BRep acceptance'],
              'status':'candidate only; full orbit evaluation required'}
    (args.output/'candidate-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'fcstd_sha256':mesh['fcstd_sha256'],'changed_objects':len(changed),'contacts':contacts}))


if __name__ == '__main__':
    main()
