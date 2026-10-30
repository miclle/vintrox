from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path('tools').resolve()))
import FreeCAD as App
from drone_concept import rear_cavity_lighting,raked_rear_parts
from experiment_drone_rear_cavity import signature
b=Path('cad/drone-concept/comparison/source-registration-study');old=b/'root-profile-g54';out=b/'root-profile-clearance';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();d=App.openDocument(str(old/'candidate.FCStd'));mesh=json.loads((old/'meshes.json').read_text());before={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
frame=raked_rear_parts(134,outer_x=112.76)['RearCyanFrame'];source=rear_cavity_lighting(frame,d.getObject('BassNozzleShell').Shape)
changed=[]
for name,(shape,_,_) in source.items():
 oldshape=d.getObject(name).Shape;diff=oldshape.cut(shape).Volume+shape.cut(oldshape).Volume
 print(name,diff,flush=True)
 if diff<1e-6:continue
 assert name in ['RearCyanLowerLeft','RearCyanLowerRight'];shape.check(True);assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1
 d.getObject(name).Shape=shape;v,f=shape.tessellate(.12);next(o for o in mesh['objects'] if o['name']==name).update(vertices=[list(x) for x in v],faces=f);changed.append(name)
assert len(changed)==2;model=out/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
d=App.openDocument(str(model))
for name,value in before.items():
 if name not in changed:assert signature(d.getObject(name).Shape)==value
App.closeDocument(d.Name);mesh['fcstd_sha256']=sha(model);(out/'meshes.json').write_text(json.dumps(mesh));report=json.loads((old/'candidate-check.json').read_text());report.update(fcstd_sha256=sha(model),parent_candidate_sha256=sha(old/'candidate.FCStd'),lighting_adjustment_objects=changed,changed_objects=report['changed_objects']+changed,unchanged_objects=572,status='candidate with lower lamp clearance repair; fixed camera review pending',script_sha256=sha(Path(__file__)),source_module_sha256=sha(Path('tools/drone_nozzle_root_profile.py')),generator_sha256=sha(Path('tools/drone_concept.py')));(out/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(model))
