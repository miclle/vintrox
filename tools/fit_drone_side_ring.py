"""Fit the visible outer black lip of the two side rings in fixed cameras.

Manual edge picks and a mirrored circular lip are appearance assumptions.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from fit_drone_lower_pod_outline import project


OBSERVATIONS=[
    (0,-1,[[282,353],[307,350],[333,365],[351,395],[362,425],[366,457],
           [365,490],[354,523],[339,549],[315,561],[289,564],[267,555]]),
    (30,-1,[[394,351],[427,352],[460,363],[492,383],[518,413],[535,445],
            [539,477],[531,510],[513,538],[486,559],[452,576],[418,581],
            [382,574],[350,558],[326,534],[312,506]]),
    (180,1,[[334,356],[307,373],[284,399],[270,430],[265,465],[272,500],
            [290,531],[316,553],[349,569],[384,574],[418,566],[448,548],
            [471,521],[483,490],[486,455]]),
    (240,1,[[701,354],[680,349],[654,357],[628,375],[608,403],[594,436],
            [589,469],[592,503],[604,532],[622,550],[646,560],[669,553],[689,541]]),
]


def circle(p,side):
    x,y,z,r=p;angle=np.linspace(0,2*np.pi,1440,endpoint=False)
    return np.column_stack([np.full(len(angle),side*x),y+r*np.cos(angle),z+r*np.sin(angle)])


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    def residual(p):
        return np.concatenate([cKDTree(project(circle(p,s),f,cameras)).query(px)[0]
                               for f,s,px in OBSERVATIONS])
    fit=least_squares(residual,[120,124,155,49],bounds=([90,100,130,35],[150,150,180,65]),
                      diff_step=.0001,max_nfev=200)
    observations=[]
    for frame,side,px in OBSERVATIONS:
        pp=project(circle(fit.x,side),frame,cameras);dist,idx=cKDTree(pp).query(px)
        observations.append({'source_frame':frame,'side':side,'reference_px':px,
                             'fitted_nearest_px':pp[idx].tolist(),'distance_px':dist.tolist()})
    result={'parameter_names':['absolute_x_mm','y_mm','z_mm','outer_radius_mm'],
        'parameters':fit.x.tolist(),'observations':observations,
        'distance_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
        'max_distance_px':float(max(residual(fit.x))),
        'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manual outer lip edge observations with partial wing occlusion',
                      'mirror symmetry, circular radius and parallel side planes assumed',
                      'source fitting points are not independent validation or manufacturing dimensions']}
    (folder/'side-ring-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('parameters','distance_rms_px','max_distance_px')}))


if __name__=='__main__':main()
