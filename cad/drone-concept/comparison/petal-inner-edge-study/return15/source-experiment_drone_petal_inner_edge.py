"""Cut twelve actual petal inner edges on the exact v52 checkpoint."""
import argparse,hashlib,json,re
from pathlib import Path
import FreeCAD as App
from drone_petal_inner_edge import bevel_inner_exit, inner_return_lip
from experiment_drone_rear_cavity import signature

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser()
 for n in ['base-model','base-meshes','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--width',type=float,required=True);p.add_argument('--method',choices=['bevel','return'],default='bevel');a=p.parse_args()
 if a.output.exists() and any(a.output.iterdir()):raise ValueError('Output must be empty')
 mesh=json.loads(a.base_meshes.read_text());baseline=digest(a.base_model)
 assert mesh['fcstd_sha256']==baseline=='73e6670b87a9ba0c572181d64a359e6706133d9186e6edcf1cf6436c7c072b07'
 d=App.openDocument(str(a.base_model));original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
 axis=App.Vector(0,.574,-.819);axis.normalize();frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis));changed=[]
 for o in d.Objects:
  if not re.fullmatch('NozzlePetal[0-9]+',o.Name):continue
  base=o.Shape.copy();local=base.copy();local.Placement=frame.inverse().multiply(local.Placement)
  s=bevel_inner_exit(local,a.width) if a.method=='bevel' else inner_return_lip(local,int(o.Name[len('NozzlePetal'):]),a.width)
  s.Placement=frame.multiply(s.Placement)
  added=abs(s.cut(base).Volume);removed=abs(base.cut(s).Volume)
  if a.method=='bevel':assert added<1e-5 and 0<removed<25,(o.Name,added,removed)
  else:assert removed<1e-5 and 0<added<50,(o.Name,added,removed)
  o.Shape=s;item=next(x for x in mesh['objects'] if x['name']==o.Name);verts,faces=s.tessellate(.12);item['vertices']=[list(v) for v in verts];item['faces']=faces
  changed.append({'name':o.Name,'valid':s.isValid(),'closed':s.isClosed(),'solids':len(s.Solids),'added_volume_mm3':added,'removed_volume_mm3':removed})
 assert len(changed)==12
 a.output.mkdir(parents=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
 d=App.openDocument(str(model));names={x['name'] for x in changed};preserved=[]
 for n,sig in original.items():
  if n not in names:assert signature(d.getObject(n).Shape)==sig,n;preserved.append(n)
 for n in names:d.getObject(n).Shape.check(True)
 assert len(preserved)==686 and len([n for n in preserved if n.startswith('SupportShaft')])==4
 mesh['fcstd_sha256']=digest(model);(a.output/'meshes.json').write_text(json.dumps(mesh))
 report={'baseline_fcstd_sha256':baseline,'fcstd_sha256':digest(model),'width_mm':a.width,'method':a.method,'parts':changed,'changed_objects':sorted(names),'preserved_objects':preserved,'source_sha256':digest(Path(__file__).with_name('drone_petal_inner_edge.py')),'script_sha256':digest(Path(__file__)),'status':'isolated geometry candidate; fixed-view comparison pending'}
 (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print('12 inner edge changes and 686 protected BReps checked',flush=True);App.closeDocument(d.Name)
if __name__=='__main__':main()
