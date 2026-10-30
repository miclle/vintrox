"""Render source-only root correspondence boards without changing images' shape."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
b=Path('cad/drone-concept/comparison');s=b/'source-registration-study';fit=json.load(open(s/'five-video-root-fit.json'));digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for row in fit['views']:
 f=row['source_frame']
 if f not in [90,150]:continue
 crop=(230,500,490,630) if f==90 else (460,500,720,630)
 src=b/'iteration-80/reference-frames'/f'frame-{f//30+1:02d}.png';im=Image.open(src).convert('RGB');w=(crop[2]-crop[0])*3;h=(crop[3]-crop[1])*3;board=Image.new('RGB',(2*w,h+45),(16,19,23));dr=ImageDraw.Draw(board)
 for col,key in enumerate(['baseline','five_video_fit']):
  pic=im.copy();d=ImageDraw.Draw(pic)
  for point,other in zip(row['reference_px'],row[key]['nearest_px']):
   d.line([tuple(point),tuple(other)],fill='white',width=1);x,y=point;d.ellipse((x-1,y-1,x+1,y+1),fill='cyan');x,y=other;d.ellipse((x-1,y-1,x+1,y+1),fill='magenta')
  board.paste(pic.crop(crop).resize((w,h)),(col*w,45));dr.text((col*w+8,10),('ORIGINAL 3-VIEW ROOT' if col==0 else '5-VIDEO-VIEW ROOT')+f" / RMS {row[key]['rms_px']:.2f} px",fill='white')
 path=s/f'video-{f}-root-fit.png';board.save(path);path.with_suffix('.json').write_text(json.dumps({'source_path':str(src),'source_sha256':digest(src),'fit_sha256':digest(s/'five-video-root-fit.json'),'crop_xyxy':crop,'uniform_scale':3,'image_sha256':digest(path),'legend':'cyan manual reference centres; magenta nearest projected circle points; white distance','limitations':['Samples are reused by the five-video fit.','This is a reconstruction diagnostic, not a rendered CAD improvement.']},indent=2)+'\n')
cfg=json.load(open(b/'stills-51/cameras.json'));study=json.load(open(s/'registration-study.json'))
for row in study['views']:
 name=row['view'];pose=next(p for p in cfg['views'] if p['name']==name);src=Path(pose['source_image']);size=tuple(pose.get('resolution',cfg['resolution']));ref=Image.open(src).convert('RGB').resize(size,Image.Resampling.LANCZOS);old=b/'stills-51-renders'/(name+'.png');new=s/'diagnostic-renders'/(name+'.png');a=Image.open(old).convert('RGB');c=Image.open(new).convert('RGB');crop=(480,400,820,700) if name=='still-04' else (50,400,400,700);w=(crop[2]-crop[0])*2;h=(crop[3]-crop[1])*2;board=Image.new('RGB',(3*w,h+45));dr=ImageDraw.Draw(board)
 for k,(im,title) in enumerate([(ref,'REFERENCE'),(Image.blend(ref,a,.5),'V46 / FORMAL CAMERA'),(Image.blend(ref,c,.5),'SAME V46 / DIAGNOSTIC CAMERA')]):
  board.paste(im.crop(crop).resize((w,h)),(k*w,45));dr.text((k*w+8,10),title,fill='white')
 path=s/(name+'-camera-diagnostic.png');board.save(path);path.with_suffix('.json').write_text(json.dumps({'source_files':[{'path':str(p),'sha256':digest(p)} for p in [src,old,new]],'crop_xyxy':crop,'uniform_scale':2,'image_sha256':digest(path),'limitation':'Different cameras; not a geometry before/after comparison.'},indent=2)+'\n')
