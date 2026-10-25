import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App, Import

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def xscale(shape,f):
 m=App.Matrix();m.A11=f
 return shape.transformGeometry(m)
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--inset',type=float,required=True);a=p.parse_args()
if a.output.exists() and any(a.output.iterdir()):raise ValueError('output must be empty')
if not 0<a.inset<10:raise ValueError('range')
a.output.mkdir(parents=True,exist_ok=True); basehash=digest(a.baseline);d=App.openDocument(str(a.baseline));f=1-a.inset/89
changed=[];checks=[]
for name in ['RearServicePanel','RearRecessLiner']:
 o=d.getObject(name);old=o.Shape;s=xscale(old,f)
 if not s.isValid() or not s.Solids:raise ValueError(name)
 o.Shape=s;changed.append(name);checks.append({'name':name,'before_bbox':[old.BoundBox.XMin,old.BoundBox.XMax,old.BoundBox.YMin,old.BoundBox.YMax,old.BoundBox.ZMin,old.BoundBox.ZMax],'after_bbox':[s.BoundBox.XMin,s.BoundBox.XMax,s.BoundBox.YMin,s.BoundBox.YMax,s.BoundBox.ZMin,s.BoundBox.ZMax],'valid':s.isValid(),'solids':len(s.Solids)})
d.recompute();model=a.output/'candidate.FCStd';d.saveAs(str(model));App.closeDocument(d.Name)
d=App.openDocument(str(model));
for n in changed:
 s=d.getObject(n).Shape
 if not s.isValid() or not s.Solids or not all(x.isClosed() for x in s.Solids):raise ValueError('readback '+n)
visible=[o for o in d.Objects if getattr(o,'Visibility',False) and hasattr(o,'Shape') and not o.Shape.isNull()];Import.export(visible,str(a.output/'candidate.step'))
meshes=[]
for o in visible:
 v,faces=o.Shape.tessellate(.12);meshes.append({'name':o.Name,'vertices':[[p.x,p.y,p.z] for p in v],'faces':faces,'color':list(o.ViewObject.ShapeColor[:3]) if o.ViewObject else [.8,.8,.8],'material':getattr(o,'RenderMaterial','paint')})
(a.output/'render-meshes.json').write_text(json.dumps({'fcstd_sha256':digest(model),'objects':meshes}))
(a.output/'candidate-check.json').write_text(json.dumps({'baseline_fcstd_sha256':basehash,'fcstd_sha256':digest(model),'inset_mm':a.inset,'changed_objects':changed,'readback_passed':True,'step_exported':True,'checks':checks,'status':'candidate; fixed-camera visual comparison pending','interpretation':'rear shadow housing width only; nozzle and four supports unchanged','limitations':['appearance candidate only','dark cavity is not treated as nozzle wall','not manufacturing validation']},indent=2)+'\n');print(digest(model));App.closeDocument(d.Name)
