"""Fit shared cheek and lower-mount Y/Z positions, then read back saved CAD.

X stations are held at existing disc centers. Manual source points and optical
appearance limit accuracy; these four landmarks do not certify complete outlines.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.optimize import least_squares

from measure_drone_landmarks import project


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'cheek-position-check.json')
    args=parser.parse_args()
    camera=folder/'camera-fit.json';parameters=json.loads(camera.read_text())['parameters']
    observations=[(2,'Left',[807,432]),(6,'Right',[140,435])]
    doc=App.openDocument(str(args.model))
    try:
        centers={side:list(doc.getObject('CheekDial'+side).Shape.Solids[0].CenterOfMass)
                 for _,side,_ in observations}
        def residual(yz):
            return np.concatenate([project([centers[side][0],*yz],frame,parameters)-pixel
                                   for frame,side,pixel in observations])
        fit=least_squares(residual,[17,167])
        results=[]
        for frame,side,pixel in observations:
            actual=project(centers[side],frame,parameters)
            predicted=project([centers[side][0],*fit.x],frame,parameters)
            results.append({'frame':frame*30,'side':side,'source_px':pixel,
                            'saved_center_mm':centers[side],'saved_px':actual.tolist(),
                            'saved_distance_px':float(np.linalg.norm(actual-pixel)),
                            'fit_px':predicted.tolist()})
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
                'camera_fit_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),
                'source_video_sha256':hashlib.sha256((root/'references/alexander-shevchuk-drone/video-cam.mp4').read_bytes()).hexdigest(),
                'fitted_shared_y_z_mm':fit.x.tolist(),'fit_coordinate_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
                'observations':results,'limitations':['two manual disc center observations',
                    'X stations retained from existing geometry','joint Y/Z placement only',
                    'fit points are not independent validation and do not certify entire contours']}
        ends=[(2,'Left',[799,665]),(6,'Right',[139,669])]
        mounts={side:list(doc.getObject('ControlEndBolt'+side).Shape.Solids[0].CenterOfMass)
                for _,side,_ in ends}
        def mount_residual(yz):
            return np.concatenate([project([mounts[side][0],*yz],frame,parameters)-pixel
                                   for frame,side,pixel in ends])
        mount_fit=least_squares(mount_residual,[7,47])
        result['end_mount_fit_shared_y_z_mm']=mount_fit.x.tolist()
        result['end_mount_observations']=[]
        for frame,side,pixel in ends:
            actual=project(mounts[side],frame,parameters)
            result['end_mount_observations'].append({'frame':frame*30,'side':side,'source_px':pixel,
                'saved_center_mm':mounts[side],'saved_px':actual.tolist(),
                'saved_distance_px':float(np.linalg.norm(actual-pixel))})
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'fit_y_z_mm':fit.x.tolist(),'saved_distances_px':[p['saved_distance_px'] for p in results],
                          'end_mount_distances_px':[p['saved_distance_px'] for p in result['end_mount_observations']]}))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
