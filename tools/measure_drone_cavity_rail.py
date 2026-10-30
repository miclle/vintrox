"""Compare visible saved-CAD primary rails with the fixed reference scanlines."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1];b=root/'cad/drone-concept/comparison'
    p=argparse.ArgumentParser();p.add_argument('--ids',type=Path,required=True)
    p.add_argument('--output',type=Path,default=b/'cavity-rail-check.json');a=p.parse_args()
    fit_path=b/'cavity-emitter-study/primary-rail-fit.json';fit=json.loads(fit_path.read_text())
    manifest_path=a.ids/'object-id-manifest.json';ids=json.loads(manifest_path.read_text())
    assert ids['camera_config_sha256']==fit['camera_config_sha256']==digest(b/'cameras.json')
    samples=[];sources={};images={}
    for group in fit['observations']:
        for row in group['samples']:
            side='Left' if row['side']==1 else 'Right';name='RearCavityEmitter'+side
            obj=next(o for o in ids['objects'] if o['name']==name);view=f"video-{row['frame']//30:02}"
            path=a.ids/(view+'.png')
            if path not in images:
                assert digest(path)==next(i['sha256'] for i in ids['images'] if i['view']==view)
                images[path]=np.asarray(Image.open(path).convert('RGBA'));sources[str(path.resolve().relative_to(root))]=digest(path)
            rgba=images[path];y=row['row_px'];line=rgba[y].astype(float)
            mask=(np.linalg.norm(line[:,:3]-obj['rgb'],axis=1)<6)&(line[:,3]>127)
            xs=np.flatnonzero(mask)
            if not len(xs):raise ValueError('Missing visible rail at '+str(row))
            center=float(np.mean(xs));samples.append({'source_set':group['set'],'frame':row['frame'],'row_px':y,'object':name,
                'reference_center_x_px':row['reference_center_x_px'],'cad_visible_center_x_px':center,'cad_visible_range_px':[int(min(xs)),int(max(xs))],
                'error_px':center-row['reference_center_x_px']})
    errors=np.array([r['error_px'] for r in samples])
    result={'fcstd_sha256':ids['fcstd_sha256'],'camera_config_sha256':ids['camera_config_sha256'],'source_fit_sha256':digest(fit_path),
        'object_id_manifest_sha256':digest(manifest_path),'measurement_script_sha256':digest(Path(__file__)),
        'samples':samples,'rms_px':float(np.sqrt(np.mean(errors**2))),'max_px':float(max(abs(errors))),
        'source_files':sources,'limitations':['twelve fixed rows, not full rail or cavity contour','manual source centers have about 2px uncertainty','image-space appearance only']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['rms_px'],result['max_px'])


if __name__=='__main__':main()
