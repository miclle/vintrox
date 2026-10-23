"""Project the actual saved side lip surfaces into the source cameras.

The projected convex envelope measures the outer lip only. The wing occlusion,
inner opening, flange and entire assembly are deliberately separate questions.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.spatial import ConvexHull,cKDTree

from fit_drone_lower_pod_outline import project


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'side-ring-check.json')
    args=parser.parse_args()
    fit_path=folder/'side-ring-fit.json';fit=json.loads(fit_path.read_text())
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    doc=App.openDocument(str(args.model))
    try:
        surfaces={};geometry={};observations=[];distances=[]
        for side,suffix in ((-1,'Left'),(1,'Right')):
            obj=doc.getObject('SpeakerOuterLip'+suffix);shape=obj.Shape
            samples=[]
            for face in shape.Faces:
                u0,u1,v0,v1=face.ParameterRange
                for u in np.linspace(u0,u1,180,endpoint=False):
                    samples.extend([list(face.valueAt(float(u),float(v))) for v in np.linspace(v0,v1,64,endpoint=False)])
            surfaces[side]=np.array(samples);bounds=shape.optimalBoundingBox(False,False)
            center=[(bounds.XMin+bounds.XMax)/2,(bounds.YMin+bounds.YMax)/2,(bounds.ZMin+bounds.ZMax)/2]
            geometry[str(side)]={'center_mm':center,'center_method':'midpoint of optimal bounds for symmetric toroidal surface',
                'outer_radius_mm':max(bounds.YLength,bounds.ZLength)/2,
                'axial_depth_mm':bounds.XLength,'sample_count':len(samples)}
        for obs in fit['observations']:
            projected=project(surfaces[obs['side']],obs['source_frame'],cameras)
            hull=projected[ConvexHull(projected).vertices];edge=[]
            for a,b in zip(hull,np.roll(hull,-1,axis=0)):
                edge.extend(a+(b-a)*np.linspace(0,1,max(2,int(np.linalg.norm(b-a)*5)))[:,None])
            edge=np.array(edge);dist,indices=cKDTree(edge).query(obs['reference_px']);distances.extend(dist.tolist())
            observations.append({**obs,'saved_nearest_px':edge[indices].tolist(),'saved_distance_px':dist.tolist()})
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'saved_lip_geometry':geometry,'observations':observations,
            'distance_rms_px':float(np.sqrt(np.mean(np.array(distances)**2))),
            'max_distance_px':max(distances),
            'method':'project saved full torus surfaces; compare convex outer envelopes to visible manual edge points',
            'limitations':['manual feature identification among multiple concentric rings',
                'source fitting points reused; no independent full-contour certification',
                'only sampled outer lip envelope; does not measure inner opening, flange, wing occlusion or complete assembly']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('saved_lip_geometry','distance_rms_px','max_distance_px')}))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
