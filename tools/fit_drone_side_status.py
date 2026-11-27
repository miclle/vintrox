"""Fit right-side status-mark centers; opposite side is held out for readback."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from fit_drone_lower_pod_outline import project

OBSERVATIONS=[(150,[[387,424],[386,447],[385,469]]),
              (180,[[545,424],[546,447],[545,470]]),
              (210,[[666,412],[666,434],[666,457]])]
HELD_OUT=[(60,-1,[[405,425],[406,449],[407,472]]),
          (90,-1,[[561,423],[560,447],[561,470]])]


def points(p):
    x,y,z,pitch=p
    return np.array([[x,y,z-i*pitch] for i in range(3)])


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text())
    residual=lambda p:np.concatenate([(project(points(p),f,cameras)-px).ravel() for f,px in OBSERVATIONS])
    fit=least_squares(residual,[113,214,180,10],bounds=([75,190,160,7],[125,240,200,15]))
    observations=[]
    for f,px in OBSERVATIONS:
        pp=project(points(fit.x),f,cameras);dist=np.linalg.norm(pp-px,axis=1)
        observations.append({'source_frame':f,'side':1,'reference_px':px,'fitted_px':pp.tolist(),'distance_px':dist.tolist()})
    dd=[v for o in observations for v in o['distance_px']]
    result={'parameters':fit.x.tolist(),'parameter_names':['absolute_x','y','upper_center_z','vertical_pitch'],
        'observations':observations,'held_out_observations':[{'source_frame':f,'side':side,'reference_px':px} for f,side,px in HELD_OUT],
        'distance_rms_px':float(np.sqrt(np.mean(np.array(dd)**2))),'max_distance_px':max(dd),
        'camera_config_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manual mark centers on partly occluded dark panels',
            'shared vertical spacing, mirrored left side and side-normal mounting plane assumed',
            'right-side observations fit geometry; left-side points held out',
            'appearance fitting only; connector function and dimensions unverified']}
    (folder/'side-status-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['parameters','distance_rms_px','max_distance_px']}))

if __name__=='__main__':main()
