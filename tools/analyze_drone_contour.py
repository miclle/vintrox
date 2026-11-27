"""Attribute existing silhouette excess pixels to visible saved CAD objects.

This ranks where to inspect. Source darkness can also cause excess classifications;
no pixel classification is changed and rankings are not design correctness scores.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

from compare_drone_reference import reference_mask


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ids',type=Path,required=True)
    parser.add_argument('--renders',type=Path,required=True)
    parser.add_argument('--comparison',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((args.ids/'object-id-manifest.json').read_text())
    renders=json.loads((args.renders/'render-manifest.json').read_text())
    report=json.loads((args.comparison/'comparison-report.json').read_text())
    assert manifest['fcstd_sha256']==renders['fcstd_sha256']==report['fcstd_sha256']
    assert manifest['camera_config_sha256']==renders['camera_config_sha256']==report['camera_config_sha256']
    objects=manifest['objects'];tree=cKDTree([o['rgb'] for o in objects])
    aggregate=np.zeros(len(objects),dtype=np.int64);views=[]
    for i,item in enumerate(manifest['images']):
        id_path=args.ids/item['path']
        assert hashlib.sha256(id_path.read_bytes()).hexdigest()==item['sha256']
        ids=np.asarray(Image.open(id_path).convert('RGBA'))
        cad=np.asarray(Image.open(args.renders/item['path']).convert('RGBA'))[:,:,3]>127
        ref=reference_mask(np.asarray(Image.open(args.comparison/f'reference-frames/frame-{i+1:02d}.png').convert('RGB')))
        excess=cad&~ref;missing=ref&~cad
        distance,index=tree.query(ids[:,:,:3].reshape(-1,3))
        assigned=(distance.reshape(cad.shape)<6)&(ids[:,:,3]>127)
        count=np.bincount(index[(excess&assigned).ravel()],minlength=len(objects))
        aggregate+=count
        ranking=[{'name':objects[j]['name'],'excess_pixels':int(count[j])}
                 for j in np.argsort(-count)[:20] if count[j]]
        labels,n=ndimage.label(missing);regions=[]
        for j,sl in enumerate(ndimage.find_objects(labels),1):
            size=int((labels[sl]==j).sum())
            if size>250:regions.append({'pixels':size,'bbox_xyxy':[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]})
        views.append({'view':item['view'],'excess_pixels':int(excess.sum()),'missing_pixels':int(missing.sum()),
                      'attributed_excess_pixels':int(count.sum()),
                      'id_mask_disagreement_pixels':int(((ids[:,:,3]>127)^cad).sum()),
                      'top_excess_objects':ranking,'large_missing_regions':sorted(regions,key=lambda r:-r['pixels'])})
    family={}
    for obj,count in zip(objects,aggregate):
        name=re.sub(r'(Left|Right).*','',obj['name']);name=re.sub(r'[_0-9]+$','',name)
        family[name]=family.get(name,0)+int(count)
    result={'fcstd_sha256':manifest['fcstd_sha256'],'camera_config_sha256':manifest['camera_config_sha256'],
            'comparison_report_sha256':hashlib.sha256((args.comparison/'comparison-report.json').read_bytes()).hexdigest(),
            'top_excess_families':sorted([{'family':k,'pixels':v} for k,v in family.items() if v],key=lambda r:-r['pixels'])[:35],
            'views':views,'limitations':['visibility attribution is not proof of geometric error',
                'dark source materials/background ambiguity is unchanged',
                'opaque ID pass can differ slightly from the presentation alpha',
                'pixel totals count a component separately in each view']}
    (args.ids/'contour-attribution.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['top_excess_families'][:20],indent=2))


if __name__=='__main__':main()
