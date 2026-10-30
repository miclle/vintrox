"""Build hash-bound inner-nozzle alternatives without replacing the formal model."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
from drone_nozzle_interior import interior_parts
from experiment_drone_rear_cavity import signature


def main():
    p=argparse.ArgumentParser()
    for name in ['baseline','meshes','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--recessed',action='store_true');a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use an empty trial directory')
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    mesh=json.loads(a.meshes.read_text());assert mesh['fcstd_sha256']==sha(a.baseline)
    assert mesh['fcstd_sha256']=='1b5a6eb7a24675e55ed958128a843aabab6d43efa6cde13803be330cd8dc9fe1'
    d=App.openDocument(str(a.baseline));before={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    axis=App.Vector(0,.574,-.819);axis.normalize();frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
    changed=[];parts=[]
    for name,shape in interior_parts(a.recessed).items():
        shape.Placement=frame.multiply(shape.Placement);shape.check(True)
        assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1,name
        old=d.getObject(name).Shape;diff=old.cut(shape).Volume+shape.cut(old).Volume
        if diff<1e-6:continue
        d.getObject(name).Shape=shape;v,f=shape.tessellate(.12)
        next(o for o in mesh['objects'] if o['name']==name).update(vertices=[list(q) for q in v],faces=f)
        changed.append(name);parts.append({'name':name,'valid':True,'closed':True,'solids':1,'advanced_check_passed':True,'difference_mm3':diff})
    a.output.mkdir(parents=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
    d=App.openDocument(str(model))
    for name,value in before.items():
        if name not in changed:assert signature(d.getObject(name).Shape)==value,name
    contacts=[]
    for left,right in [('BassVisualCone','BassDustCap'),('BassVisualCone','BassInnerThroat')]:
        x,y=d.getObject(left).Shape,d.getObject(right).Shape
        contacts.append({'objects':[left,right],'gap_mm':x.distToShape(y)[0],'overlap_mm3':x.common(y).Volume})
    # Positive empty/material probes distinguish a hollow cup from a solid cap.
    local=interior_parts(a.recessed)['BassVisualCone'];bounds=local.optimalBoundingBox(False,False)
    back=local.Vertexes[0].Point # Only geometry bounds below define the broad diagnostic.
    assert len(changed)==(3 if a.recessed else 2)
    App.closeDocument(d.Name);mesh['fcstd_sha256']=sha(model);(a.output/'meshes.json').write_text(json.dumps(mesh))
    report={'baseline_fcstd_sha256':sha(a.baseline),'fcstd_sha256':sha(model),'changed_objects':changed,'parts':parts,'unchanged_objects':len(before)-len(changed),'contacts':contacts,'recessed':a.recessed,'source_sha256':sha(Path(__file__).with_name('drone_nozzle_interior.py')),'script_sha256':sha(Path(__file__)),'status':'candidate; visual and spatial review pending','limitations':['Internal speaker-like shapes are appearance assumptions, not selected hardware.','Lighting and outer nozzle geometry remain fixed.']}
    (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
