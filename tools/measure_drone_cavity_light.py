"""Fixed scanlines on visible outer cyan rails, separate from nozzle shadows.

Color thresholds locate luminous traces only. Multiple traces and bloom make
these local diagnostics unsuitable as physical dimensions or silhouette scores.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

SAMPLES=[(4,y,305,350,'left') for y in (430,450,475)]+[(4,y,600,640,'right') for y in (430,450,475)]+[(3,y,230,275,'left') for y in (420,435,450)]+[(5,y,675,715,'right') for y in (420,435,450)]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def trace(row,x0,side,threshold):
    mask=(row[:,1]-row[:,0]>threshold)&(row[:,2]-row[:,0]>threshold)&(row[:,1]>110)
    xs=np.flatnonzero(mask)+x0
    runs=np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
    runs=[r for r in runs if len(r)>=2]
    if not runs:return None
    run=runs[0] if side=='left' else runs[-1]
    return float(np.mean(run))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--renders',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();manifest=json.loads((a.renders/'render-manifest.json').read_text())
    source_files={};observations=[];images={}
    for view,y,x0,x1,side in SAMPLES:
        paths=[a.reference/f'reference-frames/frame-{view+1:02}.png',a.renders/f'video-{view:02}.png']
        values=[]
        for path in paths:
            if path not in images:
                images[path]=np.asarray(Image.open(path).convert('RGB')).astype(float)
                source_files[str(path)]=digest(path)
            values.append([trace(images[path][y,x0:x1],x0,side,t) for t in (20,25,30)])
        ref,cad=values
        observations.append({'view':view,'row_px':y,'search_x_px':[x0,x1],'outer_side':side,
            'thresholds':[20,25,30],'reference_centers_px':ref,'cad_centers_px':cad,
            'error_px':None if ref[1] is None or cad[1] is None else cad[1]-ref[1]})
    errors=[o['error_px'] for o in observations if o['error_px'] is not None]
    result={'fcstd_sha256':manifest['fcstd_sha256'],'camera_config_sha256':manifest['camera_config_sha256'],
            'render_manifest_sha256':digest(a.renders/'render-manifest.json'),'script_sha256':digest(Path(__file__)),
            'observations':observations,'measured_samples':len(errors),'expected_samples':len(SAMPLES),
            'rms_px':float(np.sqrt(np.mean(np.square(errors)))) if errors else None,
            'max_px':float(max(map(abs,errors))) if errors else None,'source_files':source_files,
            'method':'outermost contiguous cyan run of at least two pixels; G-R and B-R > threshold, G >110; native fixed rows',
            'limitations':['outer luminous trace only; not the second inner rail','bloom and saturated whites affect detected centers','no pass/fail or complete outline claim']}
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('measured_samples','rms_px','max_px')}))


if __name__=='__main__':main()
