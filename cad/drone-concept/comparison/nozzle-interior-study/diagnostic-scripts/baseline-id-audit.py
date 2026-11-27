from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
b=Path('cad/drone-concept/comparison');out=b/'nozzle-interior-study';ids=b/'object-ids-v47';m=json.load(open(ids/'object-id-manifest.json'));rgb={o['name']:o['rgb'] for o in m['objects']};records=[]
for name,crop in [('video-02',(175,420,480,700)),('video-04',(315,380,620,710)),('video-06',(490,420,775,700))]:
 im=np.asarray(Image.open(ids/(name+'.png')).convert('RGB'));r=[]
 for key in ['BassVisualCone','BassDustCap','BassInnerThroat']:
  mask=np.all(im==rgb[key],axis=2);r.append({'object':key,'visible_pixels':int(mask.sum())})
 canvas=Image.new('RGB',((crop[2]-crop[0])*4,(crop[3]-crop[1])*2+35),(15,18,20));draw=ImageDraw.Draw(canvas)
 for j,(path,label) in enumerate([(b/'iteration-81-renders'/(name+'.png'),'V47 RENDER'),(ids/(name+'.png'),'OPAQUE OBJECT IDS')]):
  p=Image.open(path).convert('RGB').crop(crop);canvas.paste(p.resize((p.width*2,p.height*2)),(j*p.width*2,35));draw.text((j*p.width*2+8,8),label,fill='white')
 canvas.save(out/(name+'-baseline-ids.png'));records.append({'view':name,'objects':r})
report={'fcstd_sha256':m['fcstd_sha256'],'camera_sha256':m['camera_config_sha256'],'views':records,'object_rgb':{k:rgb[k] for k in ['BassVisualCone','BassDustCap','BassInnerThroat']},'method':'exact RGB count on baseline opaque object-ID images; no source boundary interpretation','limitations':['Counts cover whole image and only tell which saved part is visible.','A dark reference patch is not assumed to be a solid cap or tube.']};(out/'baseline-id-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(records))
