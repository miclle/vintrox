"""Fit the large nozzle's exposed root roll in three fixed video cameras.

The shell axis is retained. Manual dark-metal roll centreline picks are not
physical measurements and the partly occluded circle remains an assumption.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from fit_drone_lower_pod_outline import project

OBSERVATIONS=[
    (60,[[211,511],[240,527],[270,545],[300,565],[330,584],[360,602]]),
    (120,[[364,574],[375,560],[397,549],[425,541],[455,538],[485,539],
           [514,544],[543,554],[568,568],[581,583]]),
    (180,[[732,504],[708,520],[679,539],[650,560],[621,579],[592,596],[562,613]]),
]


def circle(p):
    y,z,r=p;axis=np.array([0,.574,-.819]);axis/=np.linalg.norm(axis)
    u=np.array([1,0,0]);v=np.cross(axis,u)
    angle=np.linspace(0,2*np.pi,1440,endpoint=False)
    return np.array([0,y,z])+r*(np.cos(angle)[:,None]*u+np.sin(angle)[:,None]*v)


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    def residual(p):
        return np.concatenate([cKDTree(project(circle(p),f,cameras)).query(px)[0] for f,px in OBSERVATIONS])
    fit=least_squares(residual,[238,94,61.5],bounds=([210,70,50],[260,130,75]),
                      diff_step=.0001,max_nfev=200)
    axis=np.array([0,.574,-.819]);axis/=np.linalg.norm(axis)
    local_y=np.cross(axis,[1,0,0]);delta=np.array([0,*fit.x[:2]])-[0,180,173]
    observations=[]
    for frame,px in OBSERVATIONS:
        pp=project(circle(fit.x),frame,cameras);dist,idx=cKDTree(pp).query(px)
        observations.append({'source_frame':frame,'reference_px':px,'fitted_nearest_px':pp[idx].tolist(),
                             'distance_px':dist.tolist()})
    result={'parameter_names':['center_y_mm','center_z_mm','roll_centerline_radius_mm'],
        'parameters':fit.x.tolist(),'fixed_axis':axis.tolist(),
        'local_y_shift_mm':float(delta@local_y),'local_axial_station_mm':float(delta@axis),
        'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
        'max_distance_px':float(max(residual(fit.x))),
        'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manual roll centreline at the gold-shell / dark-petal junction',
                      'fixed shell axis and circular section, partial occlusion',
                      'fitting observations reused; not independent validation or manufacturing dimensions']}
    (folder/'nozzle-root-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('parameters','local_y_shift_mm','local_axial_station_mm','distance_rms_px','max_distance_px')}))


if __name__=='__main__':main()
