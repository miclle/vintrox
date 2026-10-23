"""Fit a circular nozzle exit to manual pixels in three fixed video cameras.

The pixels are inferred petal ends, not surveyed geometry. Partial occlusion and
the circular-plane assumption limit the fit; other views must cross-check it.
No CAD render is deformed or used as a fitting target.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree


OBSERVATIONS = {
    120: [[390,640],[409,667],[448,680],[490,680],[529,668],
          [555,641],[530,628],[480,623],[430,627]],
    60: [[207,579],[224,597],[254,624],[291,648],[329,659]],
    180: [[736,578],[716,601],[681,626],[641,650],[601,661]],
}


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    camera_path = folder/'cameras.json'
    config = json.loads(camera_path.read_text())
    width, height = config['resolution']
    cameras = {}
    for frame in OBSERVATIONS:
        pose = next(v for v in config['views'] if v['source_frame'] == frame)
        eye = np.asarray(pose['eye_mm'])
        forward = np.asarray(pose['target_mm'])-eye
        forward /= np.linalg.norm(forward)
        right = np.cross(forward,[0,0,1]); right /= np.linalg.norm(right)
        up = np.cross(right,forward)
        cameras[frame] = (eye,forward,right,up,pose['lens_mm']/pose['sensor_width_mm']*width)
    angles = np.linspace(0,2*np.pi,1080,endpoint=False)

    def circle(parameters, frame):
        y,z,radius,beta = parameters
        beta = np.radians(beta)
        xyz = np.array([radius*np.cos(angles),
                        y-radius*np.sin(angles)*np.cos(beta),
                        z-radius*np.sin(angles)*np.sin(beta)]).T
        eye,forward,right,up,focal = cameras[frame]
        delta = xyz-eye
        depth = delta@forward
        return np.array([width/2+focal*(delta@right)/depth,
                         height/2-focal*(delta@up)/depth]).T

    def residual(parameters):
        return np.concatenate([cKDTree(circle(parameters,f)).query(points)[0]
                               for f,points in OBSERVATIONS.items()])

    fit = least_squares(residual,[250,70,45,25],
                        bounds=([190,20,30,10],[300,120,65,60]),
                        diff_step=.0001,max_nfev=200)
    records = []
    for frame,points in OBSERVATIONS.items():
        projected = circle(fit.x,frame)
        distance,index = cKDTree(projected).query(points)
        records.append({'source_frame':frame,'reference_px':points,
                        'nearest_circle_px':projected[index].tolist(),
                        'distance_px':distance.tolist()})
    result = {
        'parameter_names':['center_y_mm','center_z_mm','radius_mm','axis_angle_from_down_deg'],
        'parameters':fit.x.tolist(), 'distance_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
        'point_count':sum(map(len,OBSERVATIONS.values())), 'observations':records,
        'reference_video_sha256':config['reference_video_sha256'],
        'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'method':'nearest projected circular rim, three fixed source-only cameras',
        'limitations':['manual visible petal-end identification','partially occluded rim',
                       'circular planar terminal section assumption','not physical measurements'],
    }
    (folder/'nozzle-mouth-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('parameters','distance_rms_px','point_count')}))


if __name__ == '__main__':
    main()
