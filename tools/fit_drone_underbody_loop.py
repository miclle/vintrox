"""Triangulate approximate thick-loop low points from three video directions."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from measure_drone_landmarks import project


def main():
    root=Path(__file__).resolve().parents[1]
    folder=root/'cad/drone-concept/comparison'
    camera_path=folder/'camera-fit.json'
    camera=json.loads(camera_path.read_text())
    observations=[(6,1,[377,734]),(2,-1,[563,739]),(4,1,[386,704]),(4,-1,[554,709])]

    def residual(value):
        return np.concatenate([project([side*value[0],value[1],value[2]],frame,camera['parameters'])-pixel
                               for frame,side,pixel in observations])

    fit=least_squares(residual,[45,125,22])
    result={'status':'historical v9 sparse low-point fit; full path superseded by loop-profile-check.json',
            'parameter_names':['absolute_x_mm','y_mm','z_mm'],'parameters':fit.x.tolist(),
            'coordinate_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
            'observations':[{'source_frame':f*30,'side':s,'pixel':p} for f,s,p in observations],
            'residuals_px':residual(fit.x).reshape(-1,2).tolist(),
            'camera_fit_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'historical_v9_world_path_mm':[[44.5,54,51],[44.5,65,15],[44.5,106,3],[44.5,143,14],[44.5,162,78]],
            'tube_radius_mm':5,'mirror_other_side':True,
            'limitations':['manual centerline estimates on dark tubes','low-point position only',
                           'full path and thickness inferred visually, not measured hardware']}
    (folder/'underbody-loop-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('parameters','coordinate_rms_px')}))


if __name__=='__main__':
    main()
