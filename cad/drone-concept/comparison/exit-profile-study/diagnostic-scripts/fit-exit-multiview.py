"""One-off v46 exit study. Run from the repository root; no formal files are written."""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path('tools').resolve()))
from fit_drone_nozzle_outline import OBSERVATIONS
from study_drone_still_focal import basis,project
b=Path('cad/drone-concept/comparison');out=b/'exit-profile-study'
vc=json.load(open(b/'cameras.json'));sc=json.load(open(b/'stills-51/cameras.json'))
obs={f'video-{k//30:02d}':v for k,v in OBSERVATIONS.items()}
obs.update({'still-04':[[600,657],[636,662],[675,652],[713,629],[745,606],[753,577],[627,579],[658,560],[686,556],[725,555],[605,609]],'still-05':[[118,570],[132,600],[166,626],[199,648],[229,659],[253,653],[139,543],[176,557],[205,582],[238,616],[255,636]]})
cams={}
for cfg in [vc,sc]:
 for p in cfg['views']:
  if p['name'] not in obs:continue
  d=np.array(p['eye_mm'])-p['target_mm'];d/=np.linalg.norm(d);q=np.r_[p['eye_mm'],math.degrees(math.atan2(d[1],d[0])),math.degrees(math.asin(d[2])),p.get('roll_degrees',0)];size=p.get('resolution',cfg['resolution']);cams[p['name']]=(q,p['lens_mm']/p['sensor_width_mm']*size[0],size)
t=np.linspace(0,2*math.pi,1440,endpoint=False)
def curve(params,key):
 y,z,r,beta=params;beta=math.radians(beta);xyz=np.array([r*np.cos(t),y-r*np.sin(t)*math.cos(beta),z-r*np.sin(t)*math.sin(beta)]).T
 return project(xyz,*cams[key])
def residual(params,keys):
 return np.concatenate([cKDTree(curve(params,k)).query(obs[k])[0]/np.sqrt(len(obs[k])) for k in keys])
base=json.load(open(out/'baseline-circles.json'));q0=[base['saved_center_mm'][1],base['saved_center_mm'][2],base['saved_radius_mm'],math.degrees(math.asin(base['saved_axis'][1]))]
fit=least_squares(lambda q:residual(q,list(obs)),q0,bounds=([200,30,30,10],[290,100,60,60]),diff_step=.0001,max_nfev=400)
rows=[]
for k in obs:
 row={'view':k,'reference_px':obs[k]}
 for label,p in [('baseline',q0),('trial',fit.x)]:
  d,idx=cKDTree(curve(p,k)).query(obs[k]);row[label]={'rms_px':float(np.sqrt(np.mean(d*d))),'max_px':float(max(d)),'nearest_px':curve(p,k)[idx].tolist()}
 rows.append(row)
result={'status':'exploratory manual observations; not adopted','baseline_parameters':q0,'trial_parameters':fit.x.tolist(),'observations':rows,'limitations':['Low still points are manually inferred visible petal tips, with uncertain corner and layer correspondence.','All five views have equal aggregate least-squares weight.','Partial occlusion and planar circular exit assumption apply.','Formal camera and model unchanged.']}
result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result['sources']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [b/'cameras.json',b/'stills-51/cameras.json',out/'baseline-circles.json',Path('tools/fit_drone_nozzle_outline.py')]}
(out/'multiview-exit-fit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['baseline_parameters','trial_parameters']}));print([(r['view'],r['baseline']['rms_px'],r['trial']['rms_px']) for r in rows])
