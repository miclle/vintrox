from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib
from scipy.ndimage import binary_erosion
root=Path(__file__).resolve().parents[5];b=root/'cad/drone-concept/comparison';out=b/'rear-belly-study';ids=json.loads((b/'object-ids-v52/object-id-manifest.json').read_text());names=['ClosedBellyPan','MainEnclosureShell','RearLowerSlope'];colors={n:next(o['rgb'] for o in ids['objects'] if o['name']==n) for n in names};board=Image.new('RGB',(1800,1080),'#111518');draw=ImageDraw.Draw(board);font=ImageFont.load_default(size=16);rows=[]
for k,i in enumerate([2,3,5,6]):
 ref=Image.open(b/'iteration-86/reference-frames'/f'frame-{i+1:02}.png').convert('RGB');cad=Image.open(b/'iteration-86-renders'/f'video-{i:02}.png').convert('RGB');px=np.array(Image.open(b/'object-ids-v52'/f'video-{i:02}.png').convert('RGBA'));marked=cad.copy();m=np.array(marked);parts=[]
 for j,(name,color) in enumerate(colors.items()):
  mask=(np.linalg.norm(px[:,:,:3].astype(float)-color,axis=2)<6)&(px[:,:,3]>127);y,x=np.nonzero(mask)
  if len(x):parts.append({'name':name,'visible_pixels':len(x),'bbox':[int(x.min()),int(y.min()),int(x.max()),int(y.max())]})
  edge=mask&~binary_erosion(mask);m[edge]=[(255,0,160),(255,255,0),(0,255,255)][j]
 marked=Image.fromarray(m);crop=(170,440,770,680)
 for col,(im,label) in enumerate([(ref,'REFERENCE'),(cad,'CAD'),(marked,'PAN MAGENTA / SHELL YELLOW / REAR CYAN')]):
  x=col*600;y=k*270;board.paste(im.crop(crop),(x,y+30));draw.text((x+5,y+5),f'{i}s {label}',font=font,fill='white')
 rows.append({'view':i,'parts':parts})
board.save(out/'body-inspection.png');(out/'body-inspection.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
