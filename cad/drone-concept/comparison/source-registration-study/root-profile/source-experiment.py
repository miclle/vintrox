"""Build coordinated nozzle-root profile candidates without replacing the formal model."""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App
from drone_nozzle_root_profile import (root_shifted_leaf_parts, root_shifted_inner_parts,
                                       root_shifted_rolls, root_shifted_fairing, ROOT_DELTA)
from experiment_drone_rear_cavity import signature


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    for name in ('base-model', 'base-meshes', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--fraction', type=float, choices=(0, .5, 1), required=True)
    a = p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    mesh = json.loads(a.base_meshes.read_text())
    base_hash = digest(a.base_model)
    assert mesh['fcstd_sha256'] == base_hash
    doc = App.openDocument(str(a.base_model))
    original = {o.Name: signature(o.Shape) for o in doc.Objects
                if hasattr(o, 'Shape') and not o.Shape.isNull()}
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    placement = App.Placement(App.Vector(0, 180, 173),
                              App.Rotation(App.Vector(0, 0, 1), axis))
    records, changed = [], []
    for index in range(13):
        source = (root_shifted_leaf_parts(index,a.fraction) if index<12 else
                  {**root_shifted_inner_parts(a.fraction), **root_shifted_rolls(a.fraction),
                   **root_shifted_fairing(a.fraction)})
        for name, shape in source.items():
            for tag,key,x,z in [('BassWarningPlaque','bass_warning_label_local_mm',14,73),
                                 ('BassWarningTriangleInset','bass_alert_local_mm',1,40)]:
                if name==tag:
                    mesh[key]=[x,shape.optimalBoundingBox(False,False).YMin-.25,
                               z+ROOT_DELTA[0]*z/94.81*a.fraction]
            shape.Placement = placement.multiply(shape.Placement)
            shape.check(True)
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1, name
            previous = doc.getObject(name).Shape
            delta = shape.cut(previous).Volume + previous.cut(shape).Volume
            if a.fraction == 0:
                assert delta < 1e-6, (name, delta)
            doc.getObject(name).Shape = shape
            item = next(o for o in mesh['objects'] if o['name'] == name)
            vertices, faces = shape.tessellate(.12)
            item.update(vertices=[list(v) for v in vertices], faces=faces)
            records.append({'name': name, 'valid': True, 'advanced_check_passed': True,
                            'closed': True, 'solids': 1, 'symmetric_difference_mm3': delta})
            changed.append(name)
        print('built leaf', index, flush=True)
    assert len(changed) == 124
    a.output.mkdir(parents=True, exist_ok=True)
    model = a.output/'candidate.FCStd'
    doc.recompute()
    doc.saveAs(str(model))
    App.closeDocument(doc.Name)
    saved = App.openDocument(str(model))
    for name, before in original.items():
        if name not in changed:
            assert signature(saved.getObject(name).Shape) == before, name
    contacts = []
    for index in range(12):
        leaf = saved.getObject(f'NozzlePetal{index}').Shape
        for name in [f'NozzlePetalHinge{index}', f'NozzlePetalInset{index}',
                     f'NozzlePetalRidge{index}', f'NozzlePetalEndHem{index}',
                     *[n for n in changed if n.startswith(f'NozzlePetalEdgeRail{index}_')]]:
            other = saved.getObject(name).Shape
            contacts.append({'leaf': index, 'part': name,
                             'gap_mm': leaf.distToShape(other)[0],
                             'overlap_mm3': leaf.common(other).Volume})
    for first,second in [('BassNozzleRolledLip','BassNozzleShell'),('BassSpeakerGasket','BassNozzleShell'),
                         ('BassNozzleRolledLip','BassNozzleMouthRing'),('BassNozzleRearCollar','BassNozzleShell')]:
        left,right=saved.getObject(first).Shape,saved.getObject(second).Shape
        contacts.append({'parts':[first,second],'gap_mm':left.distToShape(right)[0],
                         'overlap_mm3':left.common(right).Volume})
    assert max(c['gap_mm'] for c in contacts) < .01, [c for c in contacts if c['gap_mm']>=.01]
    baseline=App.openDocument(str(a.base_model));shafts=[]
    for obj in baseline.Objects:
        if obj.Name.startswith('SupportShaft'):
            other=saved.getObject(obj.Name).Shape
            difference=obj.Shape.cut(other).Volume+other.cut(obj.Shape).Volume
            assert difference<1e-6
            shafts.append({'name':obj.Name,'difference_mm3':difference})
    assert len(shafts)==4
    App.closeDocument(baseline.Name)
    App.closeDocument(saved.Name)
    mesh['fcstd_sha256'] = digest(model)
    (a.output/'meshes.json').write_text(json.dumps(mesh))
    report = {'status': 'isolated candidate; full fixed-camera review pending',
              'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': digest(model),
              'root_shift_fraction': a.fraction, 'terminal_radius_mm': 43.6,
              'script_sha256': digest(Path(__file__)),
              'source_module_sha256': digest(Path(__file__).with_name('drone_nozzle_root_profile.py')),
              'changed_objects': changed, 'parts': records,
              'unchanged_objects': len(original)-len(changed), 'contacts': contacts,
              'protected_shafts':shafts,
              'source_fit_sha256':digest(Path('cad/drone-concept/comparison/source-registration-study/five-video-root-fit.json'))}
    (a.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'model_sha256': digest(model), 'changed': len(changed),
                      'max_contact_gap_mm': max(c['gap_mm'] for c in contacts)}))


if __name__ == '__main__':
    main()
