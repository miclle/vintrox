"""Fit the front control housing and knob-cap centers in three fixed views."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from fit_drone_lower_pod_outline import project

RAIL=[(270,[[247,693],[705,693],[705,747],[247,747]]),
      (0,[[486,708],[819,642],[819,695],[486,766]]),
      (240,[[124,645],[471,704],[471,767],[124,699]])]
KNOBS=[(270,[[548,721],[609,721],[670,721]]),
       (0,[[727,695],[768,686],[808,678]]),
       (240,[[337,721],[383,731],[427,740]])]
BUTTONS=[(270,[[287,716],[383,716],[433,716],[484,716]]),
         (0,[[519,730],[597,715],[635,709],[674,699]]),
         (240,[[147,675],[215,688],[254,696],[292,704]])]


def rail_points(p):
    w,h,y,z=p
    return np.array([[sx*w/2,y,z+sz*h/2] for sx,sz in [(-1,1),(1,1),(1,-1),(-1,-1)]])


def knob_points(p):
    first,pitch,y,z=p
    return np.array([[first+i*pitch,y,z] for i in range(3)])


def button_points(p):
    return np.array([[x,p[4],p[5]] for x in p[:4]])


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text())
    groups={}
    for name,observed,make,initial,bounds in [
        ('rail',RAIL,rail_points,[205,25,-20,48],([190,18,-40,30],[220,35,0,65])),
        ('knobs',KNOBS,knob_points,[32,26,-35,50],([20,20,-60,30],[50,32,-10,65])),
        ('buttons',BUTTONS,button_points,[-83,-40,-17,5,-28,50],
         ([-100,-50,-30,-10,-50,30],[-70,-25,0,20,0,65]))]:
        residual=lambda p:np.concatenate([(project(make(p),f,cameras)-px).ravel() for f,px in observed])
        fitted=least_squares(residual,initial,bounds=bounds)
        points=make(fitted.x);obs=[]
        for f,px in observed:
            pp=project(points,f,cameras);dd=np.linalg.norm(pp-px,axis=1)
            obs.append({'source_frame':f,'reference_px':px,'fitted_px':pp.tolist(),'distance_px':dd.tolist()})
        distances=[d for o in obs for d in o['distance_px']]
        groups[name]={'parameters':fitted.x.tolist(),'world_points_mm':points.tolist(),'observations':obs,
            'distance_rms_px':float(np.sqrt(np.mean(np.array(distances)**2))),'max_distance_px':max(distances)}
    result={'camera_config_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'groups':groups,
        'limitations':['manual corner extrapolations and cap-center observations',
            'symmetrical housing and horizontal control rows assumed',
            'same points used for fitting and readback; not independent accuracy',
            'appearance dimensions only; not physical panel or electrical validation']}
    (folder/'front-control-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{n:v[n] for n in ['parameters','distance_rms_px','max_distance_px']} for k,v in groups.items()},indent=2))

if __name__=='__main__':main()
