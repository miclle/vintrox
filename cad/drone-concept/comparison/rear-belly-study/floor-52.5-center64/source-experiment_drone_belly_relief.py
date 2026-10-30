"""Study a shallower closed underbody at the exact v52 fixed-camera baseline."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
from drone_belly_relief import relieved_belly,moved_service_shape
from experiment_drone_rear_cavity import signature

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def diff(a,b):return abs(a.cut(b).Volume)+abs(b.cut(a).Volume)
def main():
 p=argparse.ArgumentParser()
 for n in ['base-model','base-meshes','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--floor',type=float,required=True);p.add_argument('--central-half-width',type=float,default=42);a=p.parse_args()
 if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
 mesh=json.loads(a.base_meshes.read_text());basehash=sha(a.base_model);assert mesh['fcstd_sha256']==basehash=='73e6670b87a9ba0c572181d64a359e6706133d9186e6edcf1cf6436c7c072b07'
 d=App.openDocument(str(a.base_model));old={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()};parts={'ClosedBellyPan':relieved_belly(old['ClosedBellyPan'],a.floor,a.central_half_width)}
 for n,s in old.items():
  if n.startswith(('BellyServicePlate','BellyServiceBolt')):parts[n]=moved_service_shape(s,-1 if 'Left' in n else 1,a.floor,is_bolt=n.startswith('BellyServiceBolt'))
 assert len(parts)==7
 protected=Part.makeBox(2*a.central_half_width,220,200,App.Vector(-a.central_half_width,-20,-100));assert diff(parts['ClosedBellyPan'].common(protected),old['ClosedBellyPan'].common(protected))<1e-6
 records=[]
 for n,s in parts.items():
  s.check(True);assert s.isValid() and s.isClosed() and len(s.Solids)==1;d.getObject(n).Shape=s;v,f=s.tessellate(.12);item=next(x for x in mesh['objects'] if x['name']==n);item.update(vertices=[list(p) for p in v],faces=f);records.append({'name':n,'valid':True,'closed':True,'advanced_check_passed':True,'volume_mm3':s.Volume})
 a.output.mkdir(parents=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name);d=App.openDocument(str(model));preserved=[]
 for n,s in old.items():
  if n not in parts:assert signature(s)==signature(d.getObject(n).Shape),n;preserved.append(n)
 assert len(preserved)==691
 pan=d.getObject('ClosedBellyPan').Shape;contacts=[]
 for n in ['CentralSupportSeat','BottomChassis','MainEnclosureShell','UnderbodyLoop0','UnderbodyLoop1','BellyServicePlateLeft','BellyServicePlateRight']:
  s=d.getObject(n).Shape;gap=pan.distToShape(s)[0];volume=abs(pan.common(s).Volume);assert gap<.01 and volume>.001,(n,gap,volume);contacts.append({'name':n,'gap_mm':gap,'overlap_mm3':volume})
 shafts=[{'name':n,'symmetric_difference_mm3':diff(s,d.getObject(n).Shape)} for n,s in old.items() if n.startswith('SupportShaft')];assert len(shafts)==4 and all(x['symmetric_difference_mm3']<1e-6 for x in shafts)
 mesh['fcstd_sha256']=sha(model);(a.output/'meshes.json').write_text(json.dumps(mesh));(a.output/'candidate-check.json').write_text(json.dumps({'baseline_fcstd_sha256':basehash,'fcstd_sha256':sha(model),'floor_z_mm':a.floor,'changed_objects':list(parts),'parts':records,'preserved_objects':preserved,'shafts':shafts,'contacts':contacts,'central_strip_width_mm':2*a.central_half_width,'central_strip_symmetric_difference_mm3':diff(pan.common(protected),old['ClosedBellyPan'].common(protected)),'source_sha256':sha(Path(__file__).with_name('drone_belly_relief.py')),'script_sha256':sha(Path(__file__)),'status':'isolated closed-underbody appearance candidate; fixed-view review pending'},indent=2)+'\n');print(model,flush=True);App.closeDocument(d.Name)
if __name__=='__main__':main()
