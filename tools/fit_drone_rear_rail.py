"""Fit the rear panel's visible rectangular border in three fixed cameras."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from fit_drone_lower_pod_outline import project
OBSERVATIONS=[(90,[[240,310],[445,322],[443,367],[240,351]]),
              (120,[[342,319],[606,319],[606,365],[342,365]]),
              (150,[[506,323],[704,309],[703,351],[506,368]])]

def corners(p):
    w,h,y,z=p
    return np.array([[x*w/2,y,z+t*h/2] for x,t in [(1,1),(-1,1),(-1,-1),(1,-1)]])

def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    path=folder/'cameras.json';cameras=json.loads(path.read_text())
    def residual(p):return np.concatenate([(project(corners(p),f,cameras)-px).ravel() for f,px in OBSERVATIONS])
    fit=least_squares(residual,[124,22,238,210],bounds=([100,15,220,190],[150,35,260,230]))
    observations=[]
    for frame,px in OBSERVATIONS:
        pp=project(corners(fit.x),frame,cameras);dist=np.linalg.norm(pp-px,axis=1)
        observations.append({'source_frame':frame,'reference_px':px,'fitted_px':pp.tolist(),'distance_px':dist.tolist()})
    result={'parameter_names':['width_mm','height_mm','front_y_mm','center_z_mm'],'parameters':fit.x.tolist(),
        'corners_mm':corners(fit.x).tolist(),'observations':observations,
        'distance_rms_px':float(np.sqrt(np.mean([d*d for o in observations for d in o['distance_px']]))),
        'max_distance_px':max(d for o in observations for d in o['distance_px']),
        'camera_config_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manual corners extrapolated across small corner radii',
            'symmetric vertical rectangle assumed; same observations used for fit',
            'appearance dimensions only, not recovered function or physical measurements']}
    (folder/'rear-rail-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['parameters','distance_rms_px','max_distance_px']}))
if __name__=='__main__':main()
