"""Compare previous reference points against visible individual leaf silhouettes."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree

def measure(view, folder, model_hash):
    manifest=json.loads((folder/'object-id-manifest.json').read_text())
    if manifest['fcstd_sha256'] != model_hash:
        raise ValueError('ID images do not match the saved model')
    item=next(item for item in manifest['images'] if item['view']==view['view'])
    path=folder/item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('ID image hash mismatch')
    pixels=np.asarray(Image.open(path).convert('RGBA'))
    palette=cKDTree([obj['rgb'] for obj in manifest['objects']])
    distance,ids=palette.query(pixels[:,:,:3].reshape(-1,3))
    leaf_ids=[]
    for obj in manifest['objects']:
        match=re.fullmatch(r'NozzlePetal(?:Inset|EdgeRail|EndHem|Ridge|Guide|Hinge)?(\d+)(?:_\d+)?',obj['name'])
        leaf_ids.append(int(match[1]) if match else -1)
    labels=np.array(leaf_ids)[ids].reshape(pixels.shape[:2])
    labels[(distance.reshape(labels.shape)>=6)|(pixels[:,:,3]<=127)]=-1
    edges=np.zeros(labels.shape,bool)
    for i in range(12):
        mask=labels==i
        edges |= mask & ~binary_erosion(mask)
    rows,cols=np.nonzero(edges)
    xy=np.column_stack((cols,rows))
    distances,indices=cKDTree(xy).query(view['reference_px'])
    closest=xy[indices]
    parts=labels[closest[:,1],closest[:,0]]
    return dict(view=view['view'],camera_config_sha256=manifest['camera_config_sha256'],
                source_points=view['reference_px'],nearest_points=closest.tolist(),
                nearest_leaf=parts.tolist(),distances_px=distances.tolist(),
                rms_px=float(np.sqrt(np.mean(distances**2))),max_px=float(max(distances)),
                max_percent_screen=float(100*max(distances)/view['projected_screen_horizontal_span_px']),
                prior_family_max_percent_screen=100*view['candidate']['max_fraction_projected_screen_width'])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('observations','video-ids','still-ids','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    source=json.loads(args.observations.read_text())
    rows=[measure(v,args.video_ids if v['view'].startswith('video-') else args.still_ids,source['fcstd_sha256'])
          for v in source['views']]
    args.output.write_text(json.dumps(dict(fcstd_sha256=source['fcstd_sha256'],
        input_sha256=hashlib.sha256(args.observations.read_bytes()).hexdigest(),views=rows),indent=2)+'\n')
    print([(v['view'],round(v['max_percent_screen'],2),round(v['rms_px'],2)) for v in rows])

if __name__=='__main__':
    main()
