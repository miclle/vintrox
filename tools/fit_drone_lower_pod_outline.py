"""Fit mirrored small exhaust terminal circles to four fixed video views.

Manual dark-rim observations have several pixels of uncertainty. Symmetry and
planar circular ends are assumptions; this is appearance fitting, not metrology.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree


OBSERVATIONS = [
    (0, -1, [[329,738],[337,759],[355,776],[379,787],[396,784],
             [402,775],[386,759],[361,741],[340,735]]),
    (60, -1, [[673,731],[682,742],[703,748],[724,743],[739,731],
              [746,715],[737,710],[717,710],[695,718]]),
    (180, 1, [[205,715],[204,731],[222,745],[245,752],[262,748],
              [269,737],[268,726],[251,714],[227,707],[213,708]]),
    (240, 1, [[549,780],[564,787],[586,783],[607,770],[622,750],
              [622,740],[612,740],[591,750],[565,764]]),
]


def circle(parameters, side, count=1440):
    x,y,z,radius,nx,ny = parameters
    normal=np.array([side*nx,ny,-1.]);normal/=np.linalg.norm(normal)
    u=np.cross(normal,[0,0,1]);u/=np.linalg.norm(u)
    v=np.cross(normal,u)
    angle=np.linspace(0,2*np.pi,count,endpoint=False)
    points=np.array([side*x,y,z])+radius*(np.cos(angle)[:,None]*u+np.sin(angle)[:,None]*v)
    return points,normal


def project(points, frame, cameras):
    pose=next(v for v in cameras['views'] if v['source_frame']==frame)
    eye=np.array(pose['eye_mm']);forward=np.array(pose['target_mm'])-eye
    forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    focal=pose['lens_mm']/pose['sensor_width_mm']*cameras['resolution'][0]
    delta=points-eye;depth=delta@forward
    return np.column_stack([470+focal*(delta@right)/depth,400-focal*(delta@up)/depth])


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    def residual(p):
        return np.concatenate([cKDTree(project(circle(p,s)[0],f,cameras)).query(px)[0]
                               for f,s,px in OBSERVATIONS])
    fit=least_squares(residual,[110,60,20,20,.5,-.4],
                      bounds=([90,30,-5,12,0,-1.5],[130,90,50,30,1.5,-.01]),
                      diff_step=.0001,max_nfev=250)
    observations=[]
    for frame,side,pixels in OBSERVATIONS:
        projected=project(circle(fit.x,side)[0],frame,cameras)
        distance,index=cKDTree(projected).query(pixels)
        observations.append({'source_frame':frame,'side':side,'reference_px':pixels,
                             'fitted_nearest_px':projected[index].tolist(),'distance_px':distance.tolist()})
    result={'parameter_names':['absolute_x_mm','y_mm','z_mm','radius_mm','normal_x_over_minus_z','normal_y_over_minus_z'],
            'parameters':fit.x.tolist(),'right_axis':circle(fit.x,1)[1].tolist(),
            'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
            'max_distance_px':float(max(residual(fit.x))),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':cameras['reference_video_sha256'],
            'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limitations':['manual terminal-edge identification on dark material',
                          'mirror symmetry and circular planar ends assumed',
                          'same points fit geometry; not independent validation or physical dimensions']}
    (folder/'lower-pod-outline-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('parameters','right_axis','distance_rms_px','max_distance_px')}))


if __name__=='__main__':main()
