"""Explore rounded upper straps and rounded backed channel feet on the nozzle leaves."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part
from drone_concept import sector_wire, profile, tube
from experiment_drone_rear_cavity import signature


from experiment_drone_petal_detail import petal_detail_parts


def rolled_petal_root(index,radius=2.0):
    center=App.Vector(0,-1.149,97.6)
    shape=Part.makeTorus(51.5,radius,center,App.Vector(0,0,1),0,360,22.4)
    shape.rotate(center,App.Vector(0,0,1),index*30+18.8)
    ends=[edge for edge in shape.Edges if abs(edge.Length-2*math.pi*radius)<1e-5]
    assert len(ends)==2
    return shape.makeFillet(.3,ends)


def petal_roll_parts(index,strap_radius,root_radius):
    parts=petal_detail_parts(index,strap_radius)
    parts[f'NozzlePetalHinge{index}']=rolled_petal_root(index,root_radius)
    return parts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--strap-radius',type=float,choices=[.25,.4],default=.4)
    parser.add_argument('--root-radius',type=float,choices=[1.7,2.0],default=2.0)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    mesh = json.loads(args.base_meshes.read_text())
    baseline_hash = digest(args.base_model)
    assert mesh['fcstd_sha256'] == baseline_hash
    document = App.openDocument(str(args.base_model))
    original = {o.Name:signature(o.Shape) for o in document.Objects
                if hasattr(o,'Shape') and not o.Shape.isNull()}
    axis = App.Vector(0,.574,-.819)
    axis.normalize()
    placement = App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
    changed, records = [], []
    for index in range(12):
        for name, shape in petal_roll_parts(index,args.strap_radius,args.root_radius).items():
            shape.Placement = placement.multiply(shape.Placement)
            try:
                shape.check(True)
            except ValueError as error:
                raise ValueError(f'{name}: {error}') from error
            assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1
            document.getObject(name).Shape = shape
            item = next(item for item in mesh['objects'] if item['name']==name)
            vertices, faces = shape.tessellate(.12)
            item['vertices'], item['faces'] = [list(v) for v in vertices], faces
            changed.append(name)
            records.append({'name':name,'advanced_check_passed':True,'solids':1,'closed':True})
    args.output.mkdir(parents=True,exist_ok=True)
    model = args.output/'candidate.FCStd'
    document.recompute()
    document.saveAs(str(model))
    App.closeDocument(document.Name)
    document = App.openDocument(str(model))
    preserved = [{'name':name,'unchanged_geometry_signature':signature(document.getObject(name).Shape)==value}
                 for name,value in original.items() if name not in changed]
    assert all(row['unchanged_geometry_signature'] for row in preserved)
    contacts = []
    for index in range(12):
        ridge = document.getObject(f'NozzlePetalRidge{index}').Shape
        for name in [f'NozzlePetal{index}',f'NozzlePetalGuide{index}_0',f'NozzlePetalGuide{index}_1']:
            shape = document.getObject(name).Shape
            contacts.append({'objects':[f'NozzlePetalRidge{index}',name],
                             'gap_mm':ridge.distToShape(shape)[0],'overlap_mm3':ridge.common(shape).Volume})
    for index in range(12):
        root=document.getObject(f'NozzlePetalHinge{index}').Shape
        for name in [f'NozzlePetal{index}',f'NozzlePetalRidge{index}','BassNozzleRolledLip']:
            other=document.getObject(name).Shape
            contacts.append({'objects':[f'NozzlePetalHinge{index}',name],
                             'gap_mm':root.distToShape(other)[0],'overlap_mm3':root.common(other).Volume})
    App.closeDocument(document.Name)
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh))
    report = {'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline_hash,
              'script_sha256':digest(Path(__file__)),'guide_span_local_deg':4.9,
              'guide_start_station_mm':103,'guide_radial_lift_mm':.35,
              'strap_corner_radius_mm':args.strap_radius,'root_radius_mm':args.root_radius,
              'detail_source_sha256':digest(Path(__file__).with_name('experiment_drone_petal_detail.py')),'channel_foot_corner_radius_mm':.9,
              'changed_objects':changed,'parts':records,'preserved':preserved,'contacts':contacts,
              'status':'candidate only; reference width and whole-orbit checks pending'}
    (args.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'changed_objects':len(changed),'fcstd_sha256':mesh['fcstd_sha256'],
                      'max_contact_gap_mm':max(c['gap_mm'] for c in contacts)}))


if __name__=='__main__':
    main()
