from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import binary_erosion
import numpy as np,json,hashlib
root=Path(__file__).resolve().parents[5];b=root/'cad/drone-concept/comparison';s=b/'orbit-lighting-study';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());ids=read(b/'object-ids-v53/object-id-manifest.json');colors={o['name']:o['rgb'] for o in ids['objects']};groups={'rear_gold':['RearStructuralFrame','RearServicePanel','RearArmourCheekLeft','RearArmourCheekRight'],'nozzle_shell':['BassNozzleShell'],'nozzle_petals':[n for n in colors if n.startswith('NozzlePetal') and n[len('NozzlePetal'):].isdigit()]};rows=[];identity=[];alpha=[];sources=[]
for i in range(10):
 name=f'video-{i:02}.png';paths=[b/'iteration-87/reference-frames'/f'frame-{i+1:02}.png',b/'iteration-87-renders'/name,s/'video-renders'/name,b/'object-ids-v53'/name,s/'static-control-renders'/name];ref,old,new,idpx,control=[np.array(Image.open(p).convert('RGBA')) for p in paths];sources.extend({'path':str(p.relative_to(root)),'sha256':sha(p)} for p in paths)
 assert np.array_equal(old[:,:,3],new[:,:,3]);alpha.append({'view':name,'alpha_exactly_equal':True})
 diff=np.abs(old.astype(float)-control.astype(float));assert diff.max()<=1;identity.append({'view':name,'max_rgba_delta_8bit':float(diff.max()),'mean_rgba_delta_8bit':float(diff.mean()),'changed_pixels':int((diff.max(axis=2)>0).sum())})
 for group,names in groups.items():
  mask=np.zeros(old.shape[:2],bool)
  for n in names:mask|=np.linalg.norm(idpx[:,:,:3].astype(float)-colors[n],axis=2)<6
  mask=binary_erosion(mask&(idpx[:,:,3]>127),iterations=3)
  count=int(mask.sum())
  if count<100:continue
  a=np.abs(ref[:,:,:3].astype(float)-old[:,:,:3])[mask].mean();c=np.abs(ref[:,:,:3].astype(float)-new[:,:,:3])[mask].mean()
  rows.append({'view':f'video-{i:02}','group':group,'interior_pixels':count,'baseline_rgb_mae_8bit':float(a),'camera_yaw_rgb_mae_8bit':float(c),'delta_8bit':float(c-a)})
for p in sorted((s/'stills-renders').glob('*.png')):
 old=np.array(Image.open(b/'stills-58-renders'/p.name).convert('RGBA'));new=np.array(Image.open(p).convert('RGBA'));assert np.array_equal(old[:,:,3],new[:,:,3]);alpha.append({'view':p.name,'alpha_exactly_equal':True})
aggregates=[]
for group in groups:
 r=[x for x in rows if x['group']==group];n=sum(x['interior_pixels'] for x in r);aggregates.append({'group':group,'pixels':n,'baseline_rgb_mae_8bit':sum(x['interior_pixels']*x['baseline_rgb_mae_8bit'] for x in r)/n,'camera_yaw_rgb_mae_8bit':sum(x['interior_pixels']*x['camera_yaw_rgb_mae_8bit'] for x in r)/n})
# Replace ambiguous generic headings: both columns show the same v53 geometry.
font=ImageFont.load_default(size=16)
for name in ['left','back','right']:
 p=s/f'detail-{name}.json';d=read(p);crop=d['crop_xyxy'];w,h=crop[2]-crop[0],crop[3]-crop[1];ims=[Image.open(root/a['path']).convert('RGB') for a in d['source_files']];ims.append(Image.blend(ims[0],ims[2],.5));board=Image.new('RGB',(4*w,h+32),'#111518');draw=ImageDraw.Draw(board)
 for i,(im,label) in enumerate(zip(ims,['REFERENCE','v53 / STATIC LIGHTS','SAME v53 / CAMERA-YAW LIGHTS','50% OVERLAY / LIGHT TEST'])):board.paste(im.crop(crop),(i*w,32));draw.text((i*w+8,8),label,font=font,fill='white')
 board.save(s/f'detail-{name}.png');d.update(image_sha256=sha(s/f'detail-{name}.png'),interpretation='Identical v53 geometry and cameras; studio lighting hypothesis only.');p.write_text(json.dumps(d,indent=2)+'\n')
report={'fcstd_sha256':ids['fcstd_sha256'],'measurement_script_sha256':sha(Path(__file__)),'groups':groups,'interior_erosion_pixels':3,'rows':rows,'aggregate_by_group':aggregates,'static_identity_control':identity,'native_alpha_comparisons':alpha,'source_files':sources,'limitations':['Same-pixel RGB MAE is a lighting/material diagnostic; shape mismatch and reference texture remain confounders.','No source brightness filtering or image registration; only 3px CAD-part boundary erosion.','Source studio arrangement is unknown. Camera-yaw rig remains a hypothesis.','Native alpha and all 17 silhouette scores remain unchanged.']};(s/'lighting-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(aggregates,indent=2))
