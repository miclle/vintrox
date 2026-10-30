"""Compare actual visible saved-CAD marking edges at unchanged video cameras."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree

def main():
 root=Path(__file__).resolve().parents[1];b=root/'cad/drone-concept/comparison';p=argparse.ArgumentParser()
 for n in ['ids','renders','comparison','baseline-ids','baseline-renders','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();obs=json.loads((b/'nozzle-marking-study/observations.json').read_text());rows=[];sources=[];board=Image.new('RGB',(1880,800*3),'black')
 for i,o in enumerate(obs):
  f=o['source_frame'];view=f'video-{f//30:02}';values={}
  refpath=a.comparison/f'reference-frames/frame-{f//30+1:02}.png';ref=Image.open(refpath).convert('RGB');cadpath=a.renders/(view+'.png');cad=Image.open(cadpath).convert('RGB');overlay=Image.blend(ref,cad,.5);d=ImageDraw.Draw(overlay);r=ImageDraw.Draw(ref)
  for label,folder,renders in [('baseline',a.baseline_ids,a.baseline_renders),('current',a.ids,a.renders)]:
   manifest=json.loads((folder/'object-id-manifest.json').read_text());render=json.loads((renders/'render-manifest.json').read_text());assert manifest['fcstd_sha256']==render['fcstd_sha256'];assert manifest['camera_config_sha256']==render['camera_config_sha256']==sha(b/'cameras.json')
   ipath=folder/(view+'.png');entry=next(i for i in manifest['images'] if i['view']==view);assert sha(ipath)==entry['sha256'];px=np.array(Image.open(ipath).convert('RGBA'));parts={}
   for kind,names in [('triangle',['BassWarningTriangle','BassWarningTriangleInset']),('plaque',['BassWarningPlaque','BassWarningRedBand'])]:
    mask=np.zeros(px.shape[:2],bool)
    for name in names:
     color=next(x['rgb'] for x in manifest['objects'] if x['name']==name);mask|=np.linalg.norm(px[:,:,:3].astype(float)-color,axis=2)<6
    mask &= px[:,:,3]>127;y,x=np.nonzero(mask&~binary_erosion(mask));edge=np.c_[x,y];dist,idx=cKDTree(edge).query(o[kind]);near=edge[idx];parts[kind]={'reference_px':o[kind],'nearest_visible_px':near.tolist(),'distances_px':dist.tolist(),'rms_px':float(np.sqrt(np.mean(dist**2))),'max_px':float(max(dist))}
    if label=='current':
     for (x,y),(xx,yy) in zip(o[kind],near):r.ellipse((x-2,y-2,x+2,y+2),fill='cyan');d.line((x,y,int(xx),int(yy)),fill='yellow',width=1);d.ellipse((xx-2,yy-2,xx+2,yy+2),fill='red')
   values[label]={'fcstd_sha256':manifest['fcstd_sha256'],'id_manifest_sha256':sha(folder/'object-id-manifest.json'),'parts':parts};sources.append({'path':str(ipath),'sha256':sha(ipath)})
  sources.extend({'path':str(q),'sha256':sha(q)} for q in [refpath,cadpath]);rows.append({'source_frame':f,**values});board.paste(ref,(0,i*800));board.paste(overlay,(940,i*800))
 metrics={}
 for label in ['baseline','current']:
  metrics[label]={}
  for kind in ['triangle','plaque']:
   dist=np.concatenate([o[label]['parts'][kind]['distances_px'] for o in rows]);metrics[label][kind]={'rms_px':float(np.sqrt(np.mean(dist**2))),'max_px':float(max(dist)),'count':len(dist)}
 out=a.output.with_suffix('.png');board.save(out);report={'fcstd_sha256':rows[0]['current']['fcstd_sha256'],'baseline_fcstd_sha256':rows[0]['baseline']['fcstd_sha256'],'measurement_script_sha256':sha(Path(__file__)),'observations_sha256':sha(b/'nozzle-marking-study/observations.json'),'camera_sha256':sha(b/'cameras.json'),'metrics':metrics,'views':rows,'source_files':sources,'image_path':str(out),'image_sha256':sha(out),'limitations':['Same manually observed points used to fit; readback verifies realization, not independent reconstruction.','Closest visible union boundary, not matched geometric vertices.','23 plaque and 9 triangle points, incomplete contour.','Manual edge uncertainty about 2-4px; rightmost plaque edge at frame150 omitted due highlight.']};a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(metrics))
if __name__=='__main__':main()
