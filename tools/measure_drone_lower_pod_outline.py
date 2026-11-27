"""Compare saved small-exhaust terminal edges with source-only observations."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree

from fit_drone_lower_pod_outline import project


# Additional source views, not included in the four-view fitting objective.
CHECK_VIEWS=[
    {'source_frame':30,'side':-1,'reference_px':[[523,760],[526,774],[541,784],[560,788],[581,782],
        [592,771],[590,759],[575,750],[552,749],[534,754]]},
    {'source_frame':210,'side':1,'reference_px':[[351,768],[356,783],[374,789],[395,787],[418,777],
        [426,763],[421,751],[403,749],[378,753],[360,759]]},
]


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'lower-pod-outline-check.json')
    args=parser.parse_args()
    fit_path=folder/'lower-pod-outline-fit.json';fit=json.loads(fit_path.read_text())
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    doc=App.openDocument(str(args.model))
    try:
        saved={-1:[],1:[]};counts={-1:0,1:0}
        for obj in doc.Objects:
            if not obj.Name.startswith('LowerPodRib'):continue
            side=-1 if obj.Shape.Solids[0].CenterOfMass.x<0 else 1
            axis=np.array(fit['right_axis']);axis[0]*=side
            faces=[f for f in obj.Shape.Faces if f.findPlane(1e-6) is not None
                   and abs(np.dot(f.normalAt(0,0),axis))>.6]
            end=max(faces,key=lambda f:np.dot(f.CenterOfMass,axis))
            outer=max(end.Edges,key=lambda e:e.Length)
            saved[side].extend([list(p) for p in outer.discretize(Number=60)])
            counts[side]+=1
        if any(c!=18 for c in counts.values()):raise ValueError('Expected 18 saved petals per side')
        observations=[];distances=[];geometry={};checks=[];check_distances=[]
        for side in (-1,1):
            points=np.array(saved[side]);anchor=points.mean(axis=0)
            _,_,basis=np.linalg.svd(points-anchor,full_matrices=False)
            normal=basis[-1]
            if normal[2]>0:normal=-normal
            u,v=basis[:2];x=(points-anchor)@u;y=(points-anchor)@v
            cx,cy,k=np.linalg.lstsq(np.column_stack([2*x,2*y,np.ones(len(x))]),x*x+y*y,rcond=None)[0]
            radius=np.sqrt(k+cx*cx+cy*cy);center=anchor+cx*u+cy*v
            geometry[str(side)]={'center_mm':center.tolist(),'radius_mm':float(radius),'normal':normal.tolist(),
                'circle_fit_max_error_mm':float(max(abs(np.hypot(x-cx,y-cy)-radius))),
                'plane_fit_max_error_mm':float(max(abs((points-anchor)@normal))),
                'petal_count':counts[side]}
        for obs in fit['observations']:
            pp=project(np.array(saved[obs['side']]),obs['source_frame'],cameras)
            dist,indices=cKDTree(pp).query(obs['reference_px']);distances.extend(dist.tolist())
            observations.append({**obs,'saved_nearest_px':pp[indices].tolist(),'saved_distance_px':dist.tolist()})
        for obs in CHECK_VIEWS:
            pp=project(np.array(saved[obs['side']]),obs['source_frame'],cameras)
            dist,indices=cKDTree(pp).query(obs['reference_px']);check_distances.extend(dist.tolist())
            checks.append({**obs,'saved_nearest_px':pp[indices].tolist(),'saved_distance_px':dist.tolist()})
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'saved_terminal_geometry':geometry,'observations':observations,
            'distance_rms_px':float(np.sqrt(np.mean(np.array(distances)**2))),
            'max_distance_px':max(distances),
            'additional_view_checks':checks,
            'additional_view_rms_px':float(np.sqrt(np.mean(np.array(check_distances)**2))),
            'additional_view_max_px':max(check_distances),
            'limitations':['saved outer petal-end arcs only, not entire exhaust contour',
                'manual dark-rim observations and symmetry assumptions',
                '37 fitting observations reused; 20 additional view points were not used in fitting',
                'additional views share the same inferred cameras and manual pixel uncertainty']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('saved_terminal_geometry','distance_rms_px','max_distance_px',
                                               'additional_view_rms_px','additional_view_max_px')}))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
