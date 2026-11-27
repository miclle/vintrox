"""Fit the top instrument rectangle to three unchanged video cameras.

Manual metal-rim corners define an appearance plane; hidden rear roof shape
is not determined by this fit. These are not measured manufacturing dimensions.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from fit_drone_lower_pod_outline import project

# Corner order: front-left, front-right, back-right, back-left.
OBSERVATIONS=[(0,[0,1,2,3],[[467,269],[723,254],[702,228],[443,239]]),
              (240,[0,1,2,3],[[222,254],[486,269],[509,239],[241,228]]),
              (270,[2,3],[[640,236],[304,236]])]

def corners(p):
    width,height,y,z,angle=p;a=np.deg2rad(angle)
    return np.array([[x*width/2,y+t*height/2*np.cos(a),z+t*height/2*np.sin(a)]
                     for x,t in [(-1,-1),(1,-1),(1,1),(-1,1)]])

def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    path=folder/'cameras.json';cameras=json.loads(path.read_text())
    def residual(p):
        return np.concatenate([(project(corners(p),f,cameras)[ids]-px).ravel() for f,ids,px in OBSERVATIONS])
    fit=least_squares(residual,[150,24,45,255,31],bounds=([120,15,0,230,5],[190,50,100,290,70]))
    obs=[]
    for frame,ids,px in OBSERVATIONS:
        pp=project(corners(fit.x),frame,cameras)[ids];dist=np.linalg.norm(pp-px,axis=1)
        obs.append({'source_frame':frame,'corner_indices':ids,'reference_px':px,'fitted_px':pp.tolist(),'distance_px':dist.tolist()})
    result={'parameter_names':['width_mm','slope_length_mm','center_y_mm','center_z_mm','pitch_deg'],
        'parameters':fit.x.tolist(),'corners_mm':corners(fit.x).tolist(),'observations':obs,
        'distance_rms_px':float(np.sqrt(np.mean([d*d for o in obs for d in o['distance_px']]))),
        'max_distance_px':max(d for o in obs for d in o['distance_px']),
        'camera_config_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manual border corners, front rim partly occluded by brow',
            'flat symmetric rectangular rim assumed; rounded corners approximated',
            'same camera and observations used for fitting, not independent validation',
            'roof surface beyond this instrument plane remains a separate visual inference']}
    (folder/'roof-instrument-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['parameters','corners_mm','distance_rms_px','max_distance_px']},indent=2))

if __name__=='__main__':main()
