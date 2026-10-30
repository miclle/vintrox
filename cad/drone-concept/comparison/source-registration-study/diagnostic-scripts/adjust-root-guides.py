"""Rebuild the root-profile trial's guide spacing with unchanged major surfaces."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path('tools').resolve()))
import FreeCAD as App
from drone_nozzle_root_profile import petal_surface_parts
from experiment_drone_rear_cavity import signature
b=Path('cad/drone-concept/comparison/source-registration-study');source=b/'root-profile';out=b/'root-profile-g54';out.mkdir(exist_ok=False);digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=json.load(open(source/'candidate-check.json'));mesh=json.load(open(source/'meshes.json'));assert digest(source/'candidate.FCStd')==mesh['fcstd_sha256']==before['fcstd_sha256'];d=App.openDocument(str(source/'candidate.FCStd'));old={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()};axis=App.Vector(0,.574,-.819);axis.normalize();frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis));names=[]
for index in range(12):
 for name,shape in petal_surface_parts(index,root_fraction=1,guide_span=5.4).items():
  shape.Placement=frame.multiply(shape.Placement);shape.check(True);assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1;d.getObject(name).Shape=shape;vertices,faces=shape.tessellate(.12);item=next(o for o in mesh['objects'] if o['name']==name);item.update(vertices=[list(v) for v in vertices],faces=faces);names.append(name)
model=out/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name);d=App.openDocument(str(model))
for name,value in old.items():
 if name not in names:assert signature(d.getObject(name).Shape)==value
contacts=[]
for i in range(12):
 ridge=d.getObject(f'NozzlePetalRidge{i}').Shape
 for name in [f'NozzlePetal{i}',f'NozzlePetalHinge{i}',f'NozzlePetalGuide{i}_0',f'NozzlePetalGuide{i}_1']:
  shape=d.getObject(name).Shape;gap=ridge.distToShape(shape)[0];assert gap<.01;contacts.append({'objects':[f'NozzlePetalRidge{i}',name],'gap_mm':gap})
App.closeDocument(d.Name);mesh['fcstd_sha256']=digest(model);(out/'meshes.json').write_text(json.dumps(mesh));report={'status':'candidate only; complete fixed-camera review pending','baseline_fcstd_sha256':before['baseline_fcstd_sha256'],'fcstd_sha256':digest(model),'parent_candidate_sha256':before['fcstd_sha256'],'changed_objects':before['changed_objects'],'guide_adjustment_objects':names,'guide_span_degrees_before_angular_scale':5.4,'source_module_sha256':digest(Path('tools/drone_nozzle_root_profile.py')),'script_sha256':digest(Path(__file__)),'guide_contacts':contacts,'protected_shafts':before['protected_shafts'],'unchanged_objects':before['unchanged_objects']};(out/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'sha256':digest(model),'guide_parts':len(names)}))
