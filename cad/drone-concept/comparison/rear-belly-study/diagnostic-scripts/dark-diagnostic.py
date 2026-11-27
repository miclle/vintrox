"""Common gamma lift for visual diagnosis only; never used in silhouette scores."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import numpy as np,json,hashlib
root=Path(__file__).resolve().parents[5];b=root/'cad/drone-concept/comparison';s=b/'rear-belly-study';board=Image.new('RGB',(1320,900),'#141719');d=ImageDraw.Draw(board);f=ImageFont.load_default(size=16);sources=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for i,v in enumerate([2,3,5,6]):
 crop={2:(465,590,795,785),3:(405,570,735,765),5:(215,570,545,765),6:(145,590,475,785)}[v];rp=b/'iteration-86/reference-frames'/f'frame-{v+1:02}.png';cp=b/'iteration-86-renders'/f'video-{v:02}.png';ref=Image.open(rp).convert('RGB').crop(crop);cad=Image.open(cp).convert('RGB').crop(crop)
 lifted=Image.fromarray(np.uint8((np.array(ref)/255.)**.4*255));liftcad=Image.fromarray(np.uint8((np.array(cad)/255.)**.4*255))
 for j,(im,label) in enumerate([(ref,'REFERENCE'),(lifted,'REFERENCE GAMMA .4'),(cad,'V52 CAD'),(liftcad,'CAD GAMMA .4')]):
  board.paste(im,(j*330,i*225+30));d.text((j*330+5,i*225+6),str(v)+'s '+label,font=f,fill='white')
 sources.append({'view':v,'crop':crop,'reference':str(rp),'reference_sha256':sha(rp),'cad':str(cp),'cad_sha256':sha(cp)})
board.save(s/'dark-body-diagnostic.png');(s/'dark-body-diagnostic.json').write_text(json.dumps({'purpose':'visual shadow/material diagnosis; not scoring evidence','display_transform':'uint8((RGB/255)**0.4*255) applied identically; original pixels shown alongside','baseline_fcstd_sha256':json.loads((b/'iteration-86-renders/render-manifest.json').read_text())['fcstd_sha256'],'sources':sources,'script_sha256':sha(Path(__file__)),'image_sha256':sha(s/'dark-body-diagnostic.png')},indent=2)+'\n')
