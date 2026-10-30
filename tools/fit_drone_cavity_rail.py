"""Fit the bright primary rail; dim adjacent pixels remain unclassified reflections."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from PIL import Image
from fit_drone_lower_pod_outline import project

FIT=[(90,1,435,249),(150,-1,435,693.5),(120,1,450,333.5),(120,-1,450,613.5)]
HOLDOUT=[(90,1,420,249),(90,1,450,249.5),(150,-1,420,693.5),(150,-1,450,694),
         (120,1,430,333.5),(120,1,475,333.5),(120,-1,430,614),(120,-1,475,614)]


def main():
    root=Path(__file__).resolve().parents[1];base=root/'cad/drone-concept/comparison';out=base/'cavity-emitter-study'
    cameras=json.loads((base/'cameras.json').read_text())
    def prediction(p,frame,side,row):
        line=project(np.array([[side*p[0],p[1],100],[side*p[0],p[1],200]]),frame,cameras)
        return float(np.interp(row,line[::-1,1],line[::-1,0]))
    def residual(p):return [prediction(p,f,s,y)-x for f,s,y,x in FIT]
    fit=least_squares(residual,[65,238],bounds=([55,220],[75,250]))
    records=[];sources={}
    for name,observations in [('fit',FIT),('additional_scanlines',HOLDOUT)]:
        rows=[]
        for f,s,y,x in observations:
            predicted=prediction(fit.x,f,s,y)
            rows.append({'frame':f,'side':s,'row_px':y,'reference_center_x_px':x,'projected_x_px':predicted,'error_px':predicted-x})
            p=base/f'iteration-68/reference-frames/frame-{f//30+1:02}.png';sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
        e=np.array([r['error_px'] for r in rows]);records.append({'set':name,'samples':rows,'rms_px':float(np.sqrt(np.mean(e*e))),'max_px':float(max(abs(e)))})
    # Unaltered RGB row evidence distinguishes the bright core from a dimmer
    # neighbouring trace; it does not by itself establish a second lamp.
    rows=[]
    for v,y,x0,x1 in [(3,435,236,265),(4,450,324,340),(5,435,677,707)]:
        p=base/f'iteration-68/reference-frames/frame-{v+1:02}.png';im=Image.open(p).convert('RGB')
        rows.append({'frame':v*30,'row_px':y,'pixels':[[x,*im.getpixel((x,y))] for x in range(x0,x1)]})
    result={'axis_absolute_x_mm':float(fit.x[0]),'axis_y_mm':float(fit.x[1]),'observations':records,'raw_rgb_scanlines':rows,
            'camera_config_sha256':hashlib.sha256((base/'cameras.json').read_bytes()).hexdigest(),'source_files':sources,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'manual_center_uncertainty_px':2,'assumptions':['vertical parallel mirrored primary rail axes','four rows fit; eight extra rows from same three views'],
            'limitations':['additional rows are not independent views','does not fit rail endpoints or identify dim trace physical source','appearance inference, not metrology']}
    (out/'primary-rail-fit.json').write_text(json.dumps(result,indent=2)+'\n');print(fit.x,[(r['set'],r['rms_px'],r['max_px']) for r in records])


if __name__=='__main__':main()
