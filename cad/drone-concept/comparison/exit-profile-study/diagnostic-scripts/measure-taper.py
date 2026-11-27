"""One-off v46 exit study. Run from the repository root; no formal files are written."""
from pathlib import Path
import sys,json,math,hashlib
import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path('tools').resolve()))
from study_drone_still_focal import project
b=Path('cad/drone-concept/comparison');s=b/'exit-profile-study';base_path=Path('cad/drone-concept/vintrox-drone-concept.FCStd');cand_path=s/'taper-4/candidate.FCStd'
assert hashlib.sha256(base_path.read_bytes()).hexdigest() == '475c208851231c3c98da53e59c62ad1a18de1bf969f6d0622db8e5f93b03b7e5', 'This study requires the v46 baseline'
base=App.openDocument(str(base_path));cand=App.openDocument(str(cand_path));cir=json.load(open(s/'baseline-circles.json'));center=np.array(cir['saved_center_mm']);axis=np.array(cir['saved_axis']);radius=cir['saved_radius_mm'];samples={'baseline':[],'candidate':[]};edges=[]
for i in range(12):
 name=f'NozzlePetal{i}';obj=base.getObject(name);matches=[]
 for j,e in enumerate(obj.Shape.Edges):
  pts=np.array([list(p) for p in e.discretize(Number=61)]);d=pts-center
  if max(abs(d@axis))<.001 and max(abs(np.linalg.norm(d,axis=1)-radius))<.001 and e.Length>1:
   matches.append(j)
 assert len(matches)==1,(name,matches)
 j=matches[0];edges.append({'name':name,'edge_index':j})
 for key,doc in [('baseline',base),('candidate',cand)]:samples[key].extend([list(p) for p in doc.getObject(name).Shape.Edges[j].discretize(Number=241)])
obs=json.load(open(s/'multiview-exit-fit.json'))['observations'];configs=[json.load(open(b/'cameras.json')),json.load(open(b/'stills-51/cameras.json'))];rows=[]
for row in obs:
 cfg=next(c for c in configs if any(p['name']==row['view'] for p in c['views']));pose=next(p for p in cfg['views'] if p['name']==row['view']);d=np.array(pose['eye_mm'])-pose['target_mm'];d/=np.linalg.norm(d);q=np.r_[pose['eye_mm'],math.degrees(math.atan2(d[1],d[0])),math.degrees(math.asin(d[2])),pose.get('roll_degrees',0)];size=pose.get('resolution',cfg['resolution']);f=pose['lens_mm']/pose['sensor_width_mm']*size[0];record={'view':row['view'],'reference_px':row['reference_px']}
 for key,points in samples.items():
  pixels=project(np.array(points),q,f,size);dist,idx=cKDTree(pixels).query(row['reference_px']);record[key]={'rms_px':float(np.sqrt(np.mean(dist*dist))),'max_px':float(max(dist)),'nearest_px':pixels[idx].tolist(),'distance_px':dist.tolist()}
 rows.append(record)
result={'baseline_fcstd_sha256':hashlib.sha256(base_path.read_bytes()).hexdigest(),'candidate_fcstd_sha256':hashlib.sha256(cand_path.read_bytes()).hexdigest(),'selection':'saved terminal outer arcs on the baseline circle, matched edge indices after rigid transformations','edges':edges,'observations':rows,'limitations':['Manual visible petal end samples have uncertain corner/layer correspondence.','Actual sampled arcs include hidden portions; nearest-point association is not a correspondence proof.','Different from historical continuous circle metric; baseline and candidate use the same actual arc method.']}
result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result['observations_sha256']=hashlib.sha256((s/'multiview-exit-fit.json').read_bytes()).hexdigest()
result['camera_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [b/'cameras.json',b/'stills-51/cameras.json']}
(s/'taper-4/terminal-arcs-check.json').write_text(json.dumps(result,indent=2)+'\n');print([(r['view'],r['baseline']['rms_px'],r['candidate']['rms_px']) for r in rows]);App.closeDocument(base.Name);App.closeDocument(cand.Name)
