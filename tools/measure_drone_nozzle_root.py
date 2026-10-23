"""Read the saved root torus and compare its centreline with source pixels."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree

from fit_drone_lower_pod_outline import project


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'nozzle-root-check.json')
    args=parser.parse_args()
    fit_path=folder/'nozzle-root-fit.json';fit=json.loads(fit_path.read_text())
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    axis=np.array(fit['fixed_axis']);u=np.array([1,0,0]);v=np.cross(axis,u)
    doc=App.openDocument(str(args.model))
    try:
        shape=doc.getObject('BassNozzleMouthRing').Shape;bounds=shape.optimalBoundingBox(False,False)
        center=np.array([(bounds.XMin+bounds.XMax)/2,(bounds.YMin+bounds.YMax)/2,(bounds.ZMin+bounds.ZMax)/2])
        samples=[]
        for face in shape.Faces:
            u0,u1,v0,v1=face.ParameterRange
            for a in np.linspace(u0,u1,180,endpoint=False):
                samples.extend([list(face.valueAt(float(a),float(b))) for b in np.linspace(v0,v1,64,endpoint=False)])
        delta=np.array(samples)-center;radial=np.hypot(delta@u,delta@v)
        radius=float((radial.max()+radial.min())/2)
        angle=np.linspace(0,2*np.pi,1440,endpoint=False)
        points=center+radius*(np.cos(angle)[:,None]*u+np.sin(angle)[:,None]*v)
        observations=[];distances=[]
        for obs in fit['observations']:
            pp=project(points,obs['source_frame'],cameras);dist,idx=cKDTree(pp).query(obs['reference_px'])
            distances.extend(dist.tolist());observations.append({**obs,'saved_nearest_px':pp[idx].tolist(),
                                                               'saved_distance_px':dist.tolist()})
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'saved_center_mm':center.tolist(),'saved_major_radius_mm':radius,
            'saved_minor_radius_mm':float((radial.max()-radial.min())/2),
            'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(np.array(distances)**2))),
            'max_distance_px':max(distances),
            'limitations':['only the root roll centreline, not the complete shell or petals',
                'fixed shell-axis assumption; saved torus sampled numerically',
                'manual fitting observations reused, not independent visual or physical validation']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('saved_center_mm','saved_major_radius_mm','distance_rms_px','max_distance_px')}))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
