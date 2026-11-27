"""Compare saved handle-arm silhouettes and surface-mark attachment.

Convex projected boundaries are appropriate for these convex side plates only;
this does not measure the full handle assembly or cloth topology.
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
    parser=argparse.ArgumentParser();parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'handle-profile-check.json');args=parser.parse_args()
    fit_path=folder/'handle-profile-fit.json';fit=json.loads(fit_path.read_text())
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    doc=App.openDocument(str(args.model))
    try:
        observations=[];connections={}
        for frame,side,points,used in [(180,'Right',fit['reference_outline_px'],True),
                                      (60,'Left',fit['additional_reference_px'],False)]:
            arm=doc.getObject('HandleArm'+side).Shape
            verts=np.array([list(p) for p in arm.tessellate(.08)[0]])
            projected=project(verts,frame,cameras);hull=projected[ConvexHull(projected).vertices]
            boundary=np.concatenate([a+(b-a)*np.linspace(0,1,200)[:,None] for a,b in zip(hull,np.roll(hull,-1,axis=0))])
            distance,indices=cKDTree(boundary).query(points)
            observations.append({'source_frame':frame,'side':side,'used_for_construction':used,
                'reference_px':points,'saved_nearest_px':boundary[indices].tolist(),
                'distance_px':distance.tolist(),'distance_rms_px':float(np.sqrt(np.mean(distance**2))),
                'max_distance_px':float(max(distance))})
        for side in ('Left','Right'):
            arm=doc.getObject('HandleArm'+side).Shape;inset=doc.getObject('HandleInset'+side).Shape
            cuff=doc.getObject('HandleGripCuff'+side).Shape;grip=doc.getObject('HandleGrip').Shape
            connections[side]={'inset_arm_overlap_mm3':inset.common(arm).Volume,
                'arm_grip_gap_mm':arm.distToShape(grip)[0],'cuff_grip_gap_mm':cuff.distToShape(grip)[0],
                'mark_inset_overlap_mm3':[doc.getObject(f'HandleMark{side}{i}').Shape.common(inset).Volume for i in range(3)]}
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],'observations':observations,
            'connections':connections,
            'limitations':['manual pixels and inferred fixed side plane; mirror assumption',
                'saved convex plate silhouette only; excludes inset, grip and cloth',
                'opposite frame not used for construction but shares fitted cameras',
                'attachment is appearance connectivity, not structural qualification']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'views':[{k:o[k] for k in ('source_frame','distance_rms_px','max_distance_px')} for o in observations], 'connections':connections},indent=2))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
