"""Saved/source equivalence and preservation for the v49 local fairing blend."""
import argparse, hashlib, json, math
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import nozzle_fairing_parts
from drone_fairing_blend import root_shifted_fairing
from drone_nozzle_root_profile import ROOT_DELTA
from experiment_drone_rear_cavity import signature

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def difference(a,b): return abs(a.cut(b).Volume)+abs(b.cut(a).Volume)

def main():
 p=argparse.ArgumentParser()
 for name in ['model','baseline','candidate','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();assert digest(a.baseline)=='94f972c40e00c3ce739fde8134fa72e807688be6f2b0d098e24099f4f7f56419'
 current=App.openDocument(str(a.model));base=App.openDocument(str(a.baseline));candidate=App.openDocument(str(a.candidate))
 axis=App.Vector(0,.574,-.819);axis.normalize();frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
 parts=[];old_parts=[];comparisons=[];source=nozzle_fairing_parts()
 try:
  for name,s in source.items():
   s.Placement=frame;s.check(True);saved=current.getObject(name).Shape;saved.check(True)
   delta=difference(s,saved);assert saved.isValid() and saved.isClosed() and len(saved.Solids)==1 and delta<1e-6,name
   parts.append({'name':name,'advanced_check_passed':True,'closed':True,'solids':1,'source_difference_mm3':delta})
   delta=difference(saved,candidate.getObject(name).Shape);assert delta<1e-6,name
   comparisons.append({'name':name,'symmetric_difference_mm3':delta})
  for name,s in root_shifted_fairing(blend_power=1).items():
   s.Placement=frame;delta=difference(s,base.getObject(name).Shape);assert delta<1e-6,name
   old_parts.append({'name':name,'source_difference_mm3':delta})
  preserved=[]
  for o in base.Objects:
   if o.Name in source or not hasattr(o,'Shape') or o.Shape.isNull():continue
   assert signature(o.Shape)==signature(current.getObject(o.Name).Shape),o.Name
   preserved.append(o.Name)
  shafts=[n for n in preserved if n.startswith('SupportShaft')];assert len(shafts)==4 and len(preserved)==687
  probes=[]
  for z,rx,ry,dy in [(0,49,49,0),(94.81,53.82,53.82,-1.15)]:
   w=z/94.81;actual_z=z+ROOT_DELTA[0]*w;rotation=App.Rotation(App.Vector(1,0,0),ROOT_DELTA[3]*w)
   for inset in [0,4]:
    for i in range(16):
     angle=i*math.tau/16
     q=rotation.multVec(App.Vector((rx+ROOT_DELTA[1]*w-inset)*math.cos(angle),(ry+ROOT_DELTA[1]*w-inset)*math.sin(angle),0))+App.Vector(0,dy+ROOT_DELTA[2]*w,actual_z)
     point=Part.Vertex(frame.multVec(q));old=point.distToShape(base.getObject('BassNozzleShell').Shape)[0];new=point.distToShape(current.getObject('BassNozzleShell').Shape)[0]
     assert max(old,new)<1e-4,(z,inset,i,old,new)
     probes.append({'station':z,'inset':inset,'phase_index':i,'baseline_surface_distance_mm':old,'current_surface_distance_mm':new})
  report={'fcstd_sha256':digest(a.model),'baseline_fcstd_sha256':digest(a.baseline),'candidate_fcstd_sha256':digest(a.candidate),'generator_sha256':digest(Path(__file__).with_name('drone_concept.py')),'source_module_sha256':digest(Path(__file__).with_name('drone_fairing_blend.py')),'measurement_script_sha256':digest(Path(__file__)),'parts':parts,'baseline_source_parts':old_parts,'candidate_comparisons':comparisons,'preserved_objects':preserved,'shafts':shafts,'endpoint_probes':probes,'passed':True,'limitations':['64 finite endpoint samples do not prove a continuous thickness field.','Unchanged nozzle leaves and inner cavity verified by saved geometry signatures and archive payload preservation.','No manufacturing or physical acceptance.']}
  a.output.write_text(json.dumps(report,indent=2)+'\n');print('11 source/saved parts, 687 protected shapes, 64 endpoint samples passed',flush=True)
 finally:
  for d in [current,base,candidate]:App.closeDocument(d.Name)
if __name__=='__main__':main()
