"""Back-project a visible loop arc and recover actual saved pipe centerlines.

The side plane comes from the earlier three-view low-point fit. Full arc points
are manually read in frame 180; roots hidden by the body are inferred separately.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree

from measure_drone_landmarks import project


PIXELS=[[316,655],[316,683],[328,712],[350,733],[377,734],
        [400,727],[414,709],[418,682],[417,655]]


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'loop-profile-check.json')
    args=parser.parse_args()
    camera_path=folder/'camera-fit.json';parameters=json.loads(camera_path.read_text())['parameters']
    cameras=folder/'cameras.json';pose=json.loads(cameras.read_text())['views'][6]
    origin=np.array(pose['eye_mm']);forward=np.array(pose['target_mm'])-origin
    forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right)
    up=np.cross(right,forward);focal=pose['lens_mm']/pose['sensor_width_mm']*940
    world=[]
    for x,y in PIXELS:
        ray=forward+(x-470)/focal*right+(400-y)/focal*up
        world.append((origin+ray*(44.5-origin[0])/ray[0]).tolist())
    doc=App.openDocument(str(args.model))
    try:
        paths={}
        for name in ('UnderbodyLoop0','UnderbodyLoop1'):
            faces=[f for f in doc.getObject(name).Shape.Faces if f.Surface.isUPeriodic()]
            if len(faces)!=1:raise ValueError('Expected one periodic swept pipe surface: '+name)
            face=faces[0];u0,u1,v0,v1=face.ParameterRange
            # Opposite samples around the periodic circular/elliptic section
            # cancel the radius. This reads the saved surface, not generator data.
            samples=[np.mean([list(face.valueAt(float(u),float(v)))
                              for u in np.linspace(u0,u1,16,endpoint=False)],axis=0)
                     for v in np.linspace(v0,v1,400)]
            paths[name]=np.array(samples)
        projected=np.array([project(p,6,parameters) for p in paths['UnderbodyLoop1']])
        distances,indices=cKDTree(projected).query(PIXELS)
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
                'camera_fit_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
                'camera_config_sha256':hashlib.sha256(cameras.read_bytes()).hexdigest(),
                'source_video_sha256':hashlib.sha256((root/'references/alexander-shevchuk-drone/video-cam.mp4').read_bytes()).hexdigest(),
                'source_frame':180,'source_centerline_px':PIXELS,'fixed_side_plane_x_mm':44.5,
                'source_backprojected_world_mm':world,
                'inferred_hidden_roots_mm':[[44.5,72.8,57],[44.5,126.6,57]],
                'saved_centerlines_mm':{k:p.tolist() for k,p in paths.items()},
                'centerline_method':'approximate mean of 16 periodic section samples on the saved pipe surface',
                'saved_nearest_px':projected[indices].tolist(),'distance_px':distances.tolist(),
                'distance_rms_px':float(np.sqrt(np.mean(distances**2))),
                'max_distance_px':float(max(distances)),
                'limitations':['manual centerline observations on dark tubes',
                    'fixed side plane from the earlier sparse multi-view fit',
                    'visible arc from one view; mirror symmetry and hidden roots are inferred',
                    'not a full silhouette or independent geometric validation']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('distance_rms_px','max_distance_px')}))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
