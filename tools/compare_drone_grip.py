"""Compare the unchanged fixed upper-strip ROI across all ten video views."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from compare_drone_reference import reference_mask
from scipy import ndimage
base=Path('cad/drone-concept/comparison/v69-underbody-loop-radius2p2')
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--candidate',type=Path,required=True)
p=parser.parse_args().candidate
roi=(180,90,750,200)
rows=[];records=[]
for i in range(10):
 rp=base/f'video-comparison/reference-frames/frame-{i+1:02}.png'
 cp=p/f'video-renders/video-{i:02}.png'
 bp=base/f'video-renders/video-{i:02}.png'
 ims=[Image.open(q).crop(roi) for q in [rp,bp,cp]]
 # Diagnose only the upper silhouette in this fixed ROI: no fitted threshold
 # or feature isolation that could erase the neighbouring wings/antenna.
 rm=reference_mask(np.asarray(ims[0].convert('RGB')))
 checks=[]
 for im in ims[1:]:
  cm=np.asarray(im.convert('RGBA'))[:,:,3]>127
  re=rm^ndimage.binary_erosion(rm);ce=cm^ndimage.binary_erosion(cm)
  errors=np.r_[ndimage.distance_transform_edt(~re)[ce],ndimage.distance_transform_edt(~ce)[re]]
  checks.append({'iou':float((rm&cm).sum()/(rm|cm).sum()),'edge_mean_px':float(errors.mean()),'edge_p95_px':float(np.percentile(errors,95))})
 records.append({'view':f'video-{i:02}','roi_px':roi,'baseline':checks[0],'candidate':checks[1]})
 row=Image.new('RGB',(1710,140),(20,23,27));d=ImageDraw.Draw(row)
 for k,(im,label) in enumerate(zip(ims,['reference','v69',p.name])):
  row.paste(im.convert('RGB'),(k*570,25));d.text((k*570+5,5),f'{i:02} {label}',fill='white')
 rows.append(row)
b=Image.new('RGB',(1710,1400))
for i,row in enumerate(rows):b.paste(row,(0,i*140))
b.save(p/'grip-comparison.png')
(p/'grip-comparison.json').write_text(json.dumps({'candidate_fcstd_sha256':hashlib.sha256((p/'candidate.FCStd').read_bytes()).hexdigest(),'source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'camera_config_sha256':hashlib.sha256((base/'video-comparison/cameras.json').read_bytes()).hexdigest(),'method':'fixed whole upper-strip ROI, reference black-background mask vs CAD alpha; no part omission or registration','limitations':['ROI includes adjacent wings and antenna; not isolated grip contour acceptance','dark material ambiguity; manual cross-section hypothesis; no dimensional measurement'],'views':records},indent=2)+'\n')
print([(r['view'],round(r['baseline']['iou'],5),round(r['candidate']['iou'],5)) for r in records])
