"""Read saved isolated candidates, assert invariant shafts and retained outer arcs."""
from pathlib import Path
import json,hashlib,sys,re
import FreeCAD as App
root=Path(__file__).resolve().parents[5];sys.path.insert(0,str(root/'tools'))
from experiment_drone_rear_cavity import signature
b=root/'cad/drone-concept/comparison';study=b/'petal-inner-edge-study';model=b.parent/'vintrox-drone-concept.FCStd';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='73e6670b87a9ba0c572181d64a359e6706133d9186e6edcf1cf6436c7c072b07';assert sha(model)==expected;base=App.openDocument(str(model));axis=App.Vector(0,.574,-.819);axis.normalize();frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis));rows=[]
for name in ['bevel065','return15']:
 p=study/name/'candidate.FCStd';doc=App.openDocument(str(p));check=json.loads((study/name/'candidate-check.json').read_text());assert check['fcstd_sha256']==sha(p) and check['baseline_fcstd_sha256']==expected
 shafts=[]
 for obj in base.Objects:
  if obj.Name.startswith('SupportShaft'):
   saved=doc.getObject(obj.Name).Shape;delta=abs(saved.cut(obj.Shape).Volume)+abs(obj.Shape.cut(saved).Volume);assert delta<1e-6;shafts.append({'name':obj.Name,'symmetric_difference_mm3':delta})
 assert len(shafts)==4
 petals=[]
 for i in range(12):
  n=f'NozzlePetal{i}';old=base.getObject(n).Shape;new=doc.getObject(n).Shape;new.check(True);assert new.isValid() and new.isClosed() and len(new.Solids)==1
  change=old.cut(new) if name=='bevel065' else new.cut(old);change.Placement=frame.inverse().multiply(change.Placement);bb=change.optimalBoundingBox(False,False)
  gaps=[]
  for other in ['BassInnerThroat','BassVisualCone','BassDustCap']:
   target=doc.getObject(other).Shape;overlap=abs(new.common(target).Volume);assert overlap<1e-6,(name,n,other,overlap);gaps.append({'name':other,'overlap_mm3':overlap,'gap_mm':new.distToShape(target)[0]})
  petals.append({'name':n,'advanced_check_passed':True,'changed_volume_mm3':abs(change.Volume),'changed_local_z_bounds_mm':[bb.ZMin,bb.ZMax],'interior_clearance':gaps})
 outline=json.loads((study/name/'outline-check.json').read_text());oldoutline=json.loads((b/'nozzle-outline-check.json').read_text());assert outline['fcstd_sha256']==sha(p) and abs(outline['saved_radius_mm']-oldoutline['saved_radius_mm'])<1e-6 and max(abs(a-b) for a,b in zip(outline['saved_center_mm'],oldoutline['saved_center_mm']))<1e-6 and abs(outline['distance_rms_px']-oldoutline['distance_rms_px'])<1e-6
 scores={}
 for kind,baseline in [('video','iteration-86'),('stills','stills-57')]:
  a=json.loads((b/baseline/'comparison-report.json').read_text());c=json.loads((study/name/kind/'comparison-report.json').read_text());assert c['fcstd_sha256']==sha(p) and c['camera_config_sha256']==a['camera_config_sha256'];scores[kind]={'baseline':a['mean_silhouette_iou'],'candidate':c['mean_silhouette_iou'],'delta_percentage_points':100*(c['mean_silhouette_iou']-a['mean_silhouette_iou']),'views':[{'view':x['view'],'baseline':x['silhouette_iou'],'candidate':y['silhouette_iou'],'delta_percentage_points':100*(y['silhouette_iou']-x['silhouette_iou'])} for x,y in zip(a['views'],c['views'])]}
 rows.append({'name':name,'fcstd_sha256':sha(p),'shafts':shafts,'petals':petals,'outer_terminal_circle_preserved':True,'outer_terminal_radius_mm':outline['saved_radius_mm'],'terminal_observation_rms_px':outline['distance_rms_px'],'scores':scores,'adopted':False});App.closeDocument(doc.Name)
App.closeDocument(base.Name)
result={'baseline_fcstd_sha256':expected,'formal_model_unchanged':sha(model)==expected,'verification_script_sha256':sha(Path(__file__)),'candidates':rows,'decision':'Neither adopted: geometry-only inner edge changes did not clearly reproduce the observed terminal highlights. Inspect surface response and visible border structure next.','limitations':['Bevel propagates around tangent inner perimeter, beyond the initial terminal edge.','Folded return dimensions are appearance hypotheses inferred from visible highlights, not source mesh measurements.','Dark interior is not filled or shortened to improve the image score.','Formal v52 delivery remains authoritative; isolated candidates are not manufacturing releases.'],'passed':True};(study/'review.json').write_text(json.dumps(result,indent=2)+'\n');print('Two saved candidates, 24 petals, eight shaft comparisons and unchanged outer circles verified',flush=True)
