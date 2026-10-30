"""Complete the v46 shared-root taper trial with its matching inner surfaces."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path('tools').resolve()))
import FreeCAD as App
from drone_petal_profile import tapered_inner_parts
from experiment_drone_rear_cavity import signature
b=Path('cad/drone-concept/comparison/exit-profile-study');src=b/'profile-21';out=b/'profile-21-lined';out.mkdir(exist_ok=False)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();check=json.load(open(src/'candidate-check.json'));mesh=json.load(open(src/'meshes.json'));assert digest(src/'candidate.FCStd')==mesh['fcstd_sha256']==check['fcstd_sha256']
doc=App.openDocument(str(src/'candidate.FCStd'));original={o.Name:signature(o.Shape) for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()};base=App.openDocument(str(Path('cad/drone-concept/vintrox-drone-concept.FCStd')))
axis=App.Vector(0,.574,-.819);axis.normalize();place=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis));changed=[];zero=[]
for name,shape in tapered_inner_parts(0).items():
 shape.Placement=place.multiply(shape.Placement);old=base.getObject(name).Shape;delta=shape.cut(old).Volume+old.cut(shape).Volume;assert delta<1e-6;zero.append({'name':name,'difference_mm3':delta})
for name,shape in tapered_inner_parts(2.1).items():
 shape.Placement=place.multiply(shape.Placement);shape.check(True);assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1;doc.getObject(name).Shape=shape;item=next(o for o in mesh['objects'] if o['name']==name);vertices,faces=shape.tessellate(.12);item.update(vertices=[list(v) for v in vertices],faces=faces);changed.append(name)
model=out/'candidate.FCStd';doc.recompute();doc.saveAs(str(model));App.closeDocument(doc.Name);doc=App.openDocument(str(model));shafts=[]
for name,value in original.items():
 if name not in changed:assert signature(doc.getObject(name).Shape)==value,name
 if name.startswith('SupportShaft'):
  a=doc.getObject(name).Shape;c=base.getObject(name).Shape;delta=a.cut(c).Volume+c.cut(a).Volume;assert delta<1e-6;shafts.append({'name':name,'difference_mm3':delta})
assert len(shafts)==4
contacts=[];liner=doc.getObject('BassInnerThroat').Shape;cone=doc.getObject('BassVisualCone').Shape
for index in range(12):
 leaf=doc.getObject(f'NozzlePetal{index}').Shape
 for name,shape in [('BassInnerThroat',liner),('BassVisualCone',cone)]:
  overlap=leaf.common(shape).Volume;gap=leaf.distToShape(shape)[0];assert overlap<1e-6 and gap>1,(index,name,gap,overlap);contacts.append({'leaf':index,'part':name,'overlap_mm3':overlap,'gap_mm':gap})
App.closeDocument(doc.Name);App.closeDocument(base.Name);mesh['fcstd_sha256']=digest(model);(out/'meshes.json').write_text(json.dumps(mesh));report={'status':'candidate only; fixed-camera review pending','baseline_fcstd_sha256':check['baseline_fcstd_sha256'],'fcstd_sha256':digest(model),'leaf_candidate_sha256':check['fcstd_sha256'],'changed_objects':check['changed_objects']+changed,'unchanged_objects':check['unchanged_objects']-2,'terminal_radial_inset_mm':2.1,'source_module_sha256':digest(Path('tools/drone_petal_profile.py')),'script_sha256':digest(Path(__file__)),'zero_inset_inner_equivalence':zero,'inner_clearances':contacts,'protected_shafts':shafts};(out/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'sha256':digest(model),'changed':len(report['changed_objects']),'min_inner_gap_mm':min(c['gap_mm'] for c in contacts)}))
