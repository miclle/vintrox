"""Measure the visible union edge, not just the trimmed guard's private edge."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree
from experiment_drone_guard_notch import REFERENCE_EDGE


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for name in ['baseline-ids','candidate','comparison','baseline-renders','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--ids',type=Path)
    parser.add_argument('--renders',type=Path)
    args=parser.parse_args()
    names=['SideGuardRight','SideClosureRight','RearArmourCheekRight']
    results=[]
    for label,folder in [('v43',args.baseline_ids),('current',args.ids or args.candidate/'ids')]:
        manifest_path=folder/'object-id-manifest.json'
        manifest=json.loads(manifest_path.read_text())
        colors=[o['rgb'] for o in manifest['objects'] if o['name'] in names]
        assert len(colors)==3
        path=folder/'video-06.png'
        entry=next(i for i in manifest['images'] if i['view']=='video-06')
        assert digest(path)==entry['sha256']
        pixels=np.array(Image.open(path).convert('RGBA'))
        mask=np.zeros(pixels.shape[:2],bool)
        for color in colors:
            mask|=np.linalg.norm(pixels[:,:,:3].astype(float)-color,axis=2)<6
        mask &= pixels[:,:,3]>127
        yy,xx=np.nonzero(mask&~binary_erosion(mask));edges=np.column_stack([xx,yy])
        distance,indices=cKDTree(edges).query(REFERENCE_EDGE)
        results.append({'label':label,'fcstd_sha256':manifest['fcstd_sha256'],
                        'camera_config_sha256':manifest['camera_config_sha256'],
                        'id_manifest_path':str(manifest_path),
                        'id_manifest_sha256':digest(manifest_path),
                        'reference_px':REFERENCE_EDGE,'nearest_visible_gold_px':edges[indices].tolist(),
                        'distances_px':distance.tolist(),'rms_px':float(np.sqrt(np.mean(distance**2))),
                        'max_px':float(distance.max())})
    assert results[0]['camera_config_sha256']==results[1]['camera_config_sha256']
    files=[args.comparison/'reference-frames/frame-07.png',
           args.baseline_renders/'video-06.png',(args.renders or args.candidate/'video-renders')/'video-06.png']
    crop=(505,460,605,540);scale=5;width=500;height=400
    board=Image.new('RGB',(1500,432),'#151b22');draw=ImageDraw.Draw(board)
    for i,(path,label) in enumerate(zip(files,['REFERENCE','V43','CURRENT CAD'])):
        board.paste(Image.open(path).convert('RGB').crop(crop).resize((width,height),Image.Resampling.NEAREST),(i*width,32))
        draw.text((i*width+8,8),label,fill='white',font=ImageFont.load_default(size=16))
        points=REFERENCE_EDGE if i==0 else results[i-1]['nearest_visible_gold_px']
        for x,y in points:
            px=i*width+(x-crop[0])*scale;py=32+(y-crop[1])*scale
            draw.ellipse((px-4,py-4,px+4,py+4),outline='#00eeff',width=2)
    png=args.output.with_suffix('.png');board.save(png)
    report={'measurement_script_sha256':digest(Path(__file__)),'results':results,
            'boundary_objects':names,'source_frame':180,'manual_uncertainty_px':2,
            'source_files':[{'path':str(p),'sha256':digest(p)} for p in files],
            'image_path':str(png),'image_sha256':digest(png),
            'limitations':['Four construction-view observations, not independent acceptance.',
                           'Union includes adjacent gold parts; a private cut edge may remain occluded.',
                           'Reference component identities are unknown; do not remove surfaces just to improve scores.']}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{'label':r['label'],'rms_px':r['rms_px'],'max_px':r['max_px']} for r in results]))


if __name__=='__main__':main()
