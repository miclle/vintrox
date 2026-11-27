"""Measure visible upper nozzle-fairing boundaries in fixed rear views.

The body is partly hidden by the rear frame. Projecting its convex hull exposes
hidden geometry, so use the visible object-ID mask instead. These manual samples
are appearance diagnostics, not dimensions or independent physical acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree

OBSERVATIONS = [
    (90, [[297,408],[312,396],[331,389],[351,385],[372,383],[394,385],
          [416,392],[435,408],[449,431],[458,459],[464,485]]),
    (120, [[340,447],[350,425],[370,408],[395,397],[425,390],[455,386],
           [483,386],[512,389],[542,398],[567,413],[584,432],[598,456]]),
    (150, [[488,431],[499,411],[519,397],[541,389],[564,383],[587,380],
           [610,378],[633,383],[653,395],[669,418],[681,444],[688,473]]),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1]
    folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--ids',type=Path,default=folder/'object-ids-v29')
    parser.add_argument('--renders',type=Path,default=folder/'iteration-63-renders')
    parser.add_argument('--comparison',type=Path,default=folder/'iteration-63')
    parser.add_argument('--output',type=Path,default=folder/'nozzle-fairing-check-v29.json')
    args=parser.parse_args()
    manifest_path=args.ids/'object-id-manifest.json'
    ids=json.loads(manifest_path.read_text())
    renders=json.loads((args.renders/'render-manifest.json').read_text())
    assert ids['fcstd_sha256']==renders['fcstd_sha256']
    assert ids['camera_config_sha256']==renders['camera_config_sha256']==digest(folder/'cameras.json')
    color=next(o['rgb'] for o in ids['objects'] if o['name']=='BassNozzleShell')
    observations=[];sources=[];board=Image.new('RGB',(1880,3*800),'black')
    for row,(frame,reference) in enumerate(OBSERVATIONS):
        name=f'video-{frame//30:02d}'
        entry=next(i for i in ids['images'] if i['view']==name)
        path=args.ids/entry['path'];assert digest(path)==entry['sha256']
        pixels=np.asarray(Image.open(path).convert('RGBA'))
        mask=(np.linalg.norm(pixels[:,:,:3].astype(float)-color,axis=2)<6)&(pixels[:,:,3]>127)
        y,x=np.nonzero(mask&~binary_erosion(mask));edge=np.column_stack([x,y])
        distance,idx=cKDTree(edge).query(reference);nearest=edge[idx]
        observations.append({'source_frame':frame,'reference_px':reference,
                             'nearest_visible_px':nearest.tolist(),'distance_px':distance.tolist(),
                             'rms_px':float(np.sqrt(np.mean(distance**2))),'max_px':float(max(distance))})
        ref_path=args.comparison/f'reference-frames/frame-{frame//30+1:02d}.png'
        cad_path=args.renders/(name+'.png')
        ref=Image.open(ref_path).convert('RGB');cad=Image.open(cad_path).convert('RGB')
        for p in [path,ref_path,cad_path]:sources.append({'path':str(p.resolve().relative_to(root)),'sha256':digest(p)})
        overlay=Image.blend(ref,cad,.5)
        dr=ImageDraw.Draw(ref);do=ImageDraw.Draw(overlay)
        for a,b in zip(reference,nearest.tolist()):
            dr.ellipse((a[0]-3,a[1]-3,a[0]+3,a[1]+3),fill='cyan')
            do.line([tuple(a),tuple(b)],fill='white',width=1)
            do.ellipse((a[0]-3,a[1]-3,a[0]+3,a[1]+3),fill='cyan')
            do.ellipse((b[0]-3,b[1]-3,b[0]+3,b[1]+3),fill='red')
        board.paste(ref,(0,row*800));board.paste(overlay,(940,row*800))
    image_path=args.output.with_suffix('.png');board.save(image_path)
    distances=np.array([v for o in observations for v in o['distance_px']])
    result={'fcstd_sha256':ids['fcstd_sha256'],'camera_config_sha256':ids['camera_config_sha256'],
            'measurement_script_sha256':digest(Path(__file__)),
            'object_id_manifest_sha256':digest(manifest_path),'source_files':sources,
            'reference_video_sha256':json.loads((folder/'cameras.json').read_text())['reference_video_sha256'],
            'observations':observations,'rms_px':float(np.sqrt(np.mean(distances**2))),'max_px':float(max(distances)),
            'image_path':str(image_path.resolve().relative_to(root)),'image_sha256':digest(image_path),
            'limitations':['manual 35-point visible upper boundary; incomplete outer contour',
                          'occlusion boundary depends on neighbouring parts and fixed camera',
                          'closest-point distance permits correspondence ambiguity',
                          'not a fit result, manufacturing measurement or whole-model acceptance']}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['rms_px','max_px','observations']},indent=2))


if __name__=='__main__':main()
