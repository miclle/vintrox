"""Compare saved rear-transition lower outlines with visible source boundaries.

Older rear-rake traces mixed true boundaries and highlight creases. These points
follow the lower gold edge against the nozzle/dark region, and are kept separate.
They were not used to fit a camera or optimize construction parameters.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import binary_erosion
from PIL import Image


OBSERVATIONS = [
    (60,'Left',[[326,533],[350,558],[376,584],[405,610],[433,633],[460,648]]),
    (180,'Right',[[621,531],[597,555],[572,581],[546,607],[520,629],[492,646],[467,651]]),
    (90,'Left',[[459,504],[476,530],[494,556],[511,582],[529,608],[549,630],[571,636]]),
    (150,'Right',[[481,504],[465,529],[447,555],[430,580],[413,605],[393,630],[371,639]]),
]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'rear-transition-check.json')
    parser.add_argument('--ids',type=Path,default=folder/'object-ids-v29')
    args=parser.parse_args();camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    manifest_path=args.ids/'object-id-manifest.json';manifest=json.loads(manifest_path.read_text())
    assert manifest['fcstd_sha256']==digest(args.model)
    assert manifest['camera_config_sha256']==digest(camera_path)
    names=['RearArmourCheekLeft','RearArmourCheekRight','RearServicePanel','RearStructuralFrame',
           'SideGuardLeft','SideGuardRight','RearLowerSlope','MainEnclosureShell','SideClosureLeft','SideClosureRight']
    colors=[o['rgb'] for o in manifest['objects'] if o['name'] in names]
    assert len(colors)==len(names)
    doc=App.openDocument(str(args.model))
    try:
        observations=[];contacts=[];parts=[]
        for frame,side,ref in OBSERVATIONS:
            image=next(i for i in manifest['images'] if i['view']==f'video-{frame//30:02d}')
            path=args.ids/image['path'];assert digest(path)==image['sha256']
            pixels=np.asarray(Image.open(path).convert('RGBA'))
            rgb=pixels[:,:,:3].astype(float);mask=np.zeros(pixels.shape[:2],dtype=bool)
            for color in colors:mask|=np.linalg.norm(rgb-color,axis=2)<6
            mask&=pixels[:,:,3]>127
            boundary=mask&~binary_erosion(mask)
            yy,xx=np.nonzero(boundary);edges=np.column_stack([xx,yy])
            distance,indices=cKDTree(edges).query(ref)
            observations.append({'source_frame':frame,'side':side,'reference_px':ref,'object_id_image':image,
                'saved_nearest_px':edges[indices].tolist(),'distance_px':distance.tolist(),
                'distance_rms_px':float(np.sqrt(np.mean(distance**2))),
                'max_distance_px':float(max(distance))})
        for side in ('Left','Right'):
            shape=doc.getObject('RearArmourCheek'+side).Shape
            bbox=shape.optimalBoundingBox(False,False)
            parts.append({'name':'RearArmourCheek'+side,'valid':shape.isValid(),
                          'solids':len(shape.Solids),'bounds_mm':[bbox.XMin,bbox.XMax,bbox.YMin,bbox.YMax,bbox.ZMin,bbox.ZMax]})
            for other in ('RearStructuralFrame','RearServicePanel','SideGuard'+side):
                target=doc.getObject(other).Shape
                contacts.append({'objects':['RearArmourCheek'+side,other],
                                 'gap_mm':shape.distToShape(target)[0],
                                 'overlap_mm3':shape.common(target).Volume})
        distance=np.array([v for o in observations for v in o['distance_px']])
        result={'fcstd_sha256':digest(args.model),'camera_config_sha256':digest(camera_path),
            'source_video_sha256':cameras['reference_video_sha256'],
            'measurement_script_sha256':digest(Path(__file__)),
            'object_id_manifest_sha256':digest(manifest_path),'boundary_objects':names,
            'method':'visible named rear-gold group boundary from flat object-ID render; RGB distance < 6, alpha > 127',
            'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(distance**2))),
            'max_distance_px':float(max(distance)),'contacts':contacts,'parts':parts,
            'rear_armour_bolt_objects':[o.Name for o in doc.Objects if o.Name.startswith('RearArmourBolt')],
            'limitations':['manual lower gold boundaries, including some partly occluded segments',
                'visible object-ID group boundary includes occlusion by adjacent non-gold parts',
                'fixed cameras and unchanged source/CAD masks; no image warping',
                'cross-section, thickness and upper hidden joins remain appearance assumptions',
                'point distances do not establish the complete 3D contour or manufacturing accuracy']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ['fcstd_sha256','distance_rms_px','max_distance_px','contacts']},indent=2))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
