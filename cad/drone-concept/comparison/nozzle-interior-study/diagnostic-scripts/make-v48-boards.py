from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
b=Path('cad/drone-concept/comparison');s=b/'nozzle-interior-study';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for kind,name,crop in [('still','still-04',(480,400,820,700)),('still','still-05',(50,400,400,700)),('video','video-04',(315,380,620,710))]:
 camera=b/('stills-52/cameras.json' if kind=='still' else 'cameras.json');conf=json.loads(camera.read_text());pose=next(p for p in conf['views'] if p['name']==name);size=tuple(pose.get('resolution',conf['resolution']))
 ref=Path(pose['source_image']) if 'source_image' in pose else b/'iteration-81/reference-frames'/f"frame-{pose['source_frame']//30+1:02d}.png"
 base=b/('stills-52-renders' if kind=='still' else 'iteration-81-renders')/(name+'.png')
 for candidate in ['v48']:
  new=b/('stills-53-renders' if kind=='still' else 'iteration-82-renders')/(name+'.png')
  if not new.exists():continue
  images=[Image.open(ref).convert('RGB').resize(size,Image.Resampling.LANCZOS),Image.open(base).convert('RGB'),Image.open(new).convert('RGB')]
  assert all(im.size==size for im in images)
  images.append(Image.blend(images[0],images[2],.5));w,h=(crop[2]-crop[0])*2,(crop[3]-crop[1])*2;canvas=Image.new('RGB',(w*4,h+35),(15,18,20));draw=ImageDraw.Draw(canvas)
  for i,(im,label) in enumerate(zip(images,['REFERENCE','V47 BASELINE',candidate.upper(),'50% OVERLAY'])):
   canvas.paste(im.crop(crop).resize((w,h),Image.Resampling.LANCZOS),(i*w,35));draw.text((i*w+8,8),label,fill='white')
  out=s/(name+'-'+candidate+'.png');canvas.save(out)
  (out.with_suffix('.json')).write_text(json.dumps({'camera_sha256':sha(camera),'candidate_fcstd_sha256':json.loads((new.parent/'render-manifest.json').read_text())['fcstd_sha256'],'crop':crop,'scale':2,'alpha':.5,'sources':[{'path':str(p),'sha256':sha(p)} for p in [ref,base,new]],'image_sha256':sha(out),'method':'same fixed camera, common crop, no spatial registration or warp'},indent=2)+'\n')
