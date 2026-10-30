"""Saved/source belly relief equivalence, protected supports, skin and contacts."""
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
 for n in ['model','baseline','candidate','candidate-check','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert sha(a.baseline)=='73e6670b87a9ba0c572181d64a359e6706133d9186e6edcf1cf6436c7c072b07';check=json.loads(a.candidate_check.read_text());assert check['fcstd_sha256']==sha(a.candidate)
 d=App.openDocument(str(a.model));b=App.openDocument(str(a.baseline));c=App.openDocument(str(a.candidate));floor=check['floor_z_mm'];hw=check['central_strip_width_mm']/2
 source={'ClosedBellyPan':relieved_belly(b.getObject('ClosedBellyPan').Shape,floor,hw)}
 for n in check['changed_objects']:
  if n.startswith('BellyService'):source[n]=moved_service_shape(b.getObject(n).Shape,-1 if 'Left' in n else 1,floor,is_bolt=n.startswith('BellyServiceBolt'))
 parts=[];comparisons=[]
 for n,s in source.items():
  saved=d.getObject(n).Shape;saved.check(True);s.check(True);delta=diff(s,saved);dc=diff(saved,c.getObject(n).Shape);assert saved.isValid() and saved.isClosed() and len(saved.Solids)==1 and max(delta,dc)<1e-6,n
  parts.append({'name':n,'advanced_check_passed':True,'source_difference_mm3':delta});comparisons.append({'name':n,'symmetric_difference_mm3':dc})
 preserved=[];shafts=[]
 for o in b.Objects:
  if not hasattr(o,'Shape') or o.Shape.isNull() or o.Name in source:continue
  assert signature(o.Shape)==signature(d.getObject(o.Name).Shape),o.Name;preserved.append(o.Name)
  if o.Name.startswith('SupportShaft'):
   delta=diff(o.Shape,d.getObject(o.Name).Shape);assert delta<1e-6;shafts.append({'name':o.Name,'symmetric_difference_mm3':delta})
 assert len(preserved)==691 and len(shafts)==4
 pan=d.getObject('ClosedBellyPan').Shape;block=Part.makeBox(hw*2,220,200,App.Vector(-hw,-20,-100));central=diff(pan.common(block),b.getObject('ClosedBellyPan').Shape.common(block));assert central<1e-6
 probes=[]
 for x in [-82,-70,70,82]:
  for y in [70,95,120]:
   inside=pan.isInside(App.Vector(x,y,floor+.1),1e-7,True);outside=not pan.isInside(App.Vector(x,y,floor-.1),1e-7,True);assert inside and outside
   probes.append({'xy_mm':[x,y],'inside_at_floor_plus_0_1':inside,'outside_at_floor_minus_0_1':outside})
 contacts=[]
 for n in ['CentralSupportSeat','BottomChassis','MainEnclosureShell','UnderbodyLoop0','UnderbodyLoop1','BellyServicePlateLeft','BellyServicePlateRight']:
  s=d.getObject(n).Shape;gap=pan.distToShape(s)[0];overlap=abs(pan.common(s).Volume);assert gap<.01 and overlap>.001;contacts.append({'name':n,'gap_mm':gap,'overlap_mm3':overlap})
 bolts=[]
 for side in ['Left','Right']:
  for i in range(2):
   n=f'BellyServiceBolt{side}{i}';s=d.getObject(n).Shape;plate=d.getObject('BellyServicePlate'+side).Shape;gap=s.distToShape(plate)[0];assert gap<.01;bolts.append({'name':n,'plate_gap_mm':gap,'advanced_check_passed':True})
 report={'passed':True,'fcstd_sha256':sha(a.model),'baseline_fcstd_sha256':sha(a.baseline),'candidate_fcstd_sha256':sha(a.candidate),'generator_sha256':sha(Path(__file__).with_name('drone_concept.py')),'source_module_sha256':sha(Path(__file__).with_name('drone_belly_relief.py')),'measurement_script_sha256':sha(Path(__file__)),'parts':parts,'candidate_comparisons':comparisons,'preserved_objects':preserved,'shafts':shafts,'central_strip_width_mm':hw*2,'central_strip_symmetric_difference_mm3':central,'outer_floor_z_mm':floor,'floor_probes':probes,'contacts':contacts,'service_screws':bolts,'limitations':['Local appearance contacts and 12 finite material probes do not validate structural strength or manufacturing thickness.','Generator equivalence checks the incremental operation on the exact saved v52 baseline; full GUI rebuild remains outside this study.']};a.output.write_text(json.dumps(report,indent=2)+'\n')
 for doc in [d,b,c]:App.closeDocument(doc.Name)
 print('Seven saved/source solids, protected central strip, four shafts, 12 floor probes and contacts passed',flush=True)
if __name__=='__main__':main()
