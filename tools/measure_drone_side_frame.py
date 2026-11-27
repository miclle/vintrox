"""Check saved side-profile edges against the manually observed video boundary."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.spatial import ConvexHull,cKDTree

from fit_drone_side_frame import OBSERVATIONS
from measure_drone_landmarks import project


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'side-frame-check.json')
    args = parser.parse_args()
    camera_path = folder/'camera-fit.json'
    parameters = json.loads(camera_path.read_text())['parameters']
    source = folder/'side-frame-fit.json'
    doc = App.openDocument(str(args.model))
    result = {'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
              'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'camera_fit_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
              'source_fit_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'source_frame':180,'profiles':{},
              'limitations':['one side view, manually selected boundary pixels',
                             'outer rim uses its convex projected solid silhouette, including rounded shoulders',
                             'light observations are centerline pixels, compared to tube surface',
                             'not a full model silhouette or physical assembly verification']}
    try:
        for key,name in [('outer','SideGuardRight'),('spine','SideFrontSpineRight'),('light','CyanSideTubeRight')]:
            shape = doc.getObject(name).Shape
            if key in ('light','outer'):
                samples = shape.tessellate(.2)[0]
            else:
                faces = [f for f in shape.Faces if f.findPlane(1e-6) is not None
                         and abs(f.normalAt(0,0).x)>.9999]
                face = max(faces,key=lambda f:f.CenterOfMass.x)
                samples = [p for e in face.OuterWire.Edges for p in e.discretize(Number=120)]
            pixels = np.array([project(list(p),6,parameters) for p in samples])
            if key == 'outer':
                boundary=pixels[ConvexHull(pixels).vertices]
                pixels=np.concatenate([a+(b-a)*np.linspace(0,1,120)[:,None]
                    for a,b in zip(boundary,np.roll(boundary,-1,axis=0))])
            distance,index = cKDTree(pixels).query(OBSERVATIONS[key])
            result['profiles'][key] = {'object':name,'source_px':OBSERVATIONS[key],
                'saved_boundary_px':pixels[index].tolist(),'distance_px':distance.tolist(),
                'method':('convex projected solid silhouette' if key=='outer' else
                          'tube surface samples' if key=='light' else 'outer wire of front planar face'),
                'distance_rms_px':float(np.sqrt(np.mean(distance**2))),
                'max_distance_px':float(max(distance))}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:{n:v[n] for n in ('distance_rms_px','max_distance_px')}
                          for k,v in result['profiles'].items()}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
