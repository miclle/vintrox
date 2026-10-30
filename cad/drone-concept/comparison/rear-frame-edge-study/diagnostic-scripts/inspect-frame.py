from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import binary_erosion
import numpy as np,json,hashlib
root=Path(__file__).resolve().parents[5];b=root/'cad/drone-concept/comparison';out=b/'rear-frame-edge-study';ids=json.loads((b/'object-ids-v53/object-id-manifest.json').read_text());names=['RearStructuralFrame','RearServicePanel','RearArmourCheekLeft','RearArmourCheekRight'];palette=[(255,0,180),(255,255,0),(0,255,255),(0,255,255)];colors={n:next(o['rgb'] for o in ids['objects'] if o['name']==n) for n in names}
board=Image.new('RGB',(1680,1536),'#111518');draw=ImageDraw.Draw(board);font=ImageFont.load_default(size=16);rows=[]
for row,i in enumerate([2,3,5,6]):
 refp=b/'iteration-87/reference-frames'/f'frame-{i+1:02}.png';cadp=b/'iteration-87-renders'/f'video-{i:02}.png';idp=b/'object-ids-v53'/f'video-{i:02}.png';ref=Image.open(refp).convert('RGB');cad=Image.open(cadp).convert('RGB');px=np.array(Image.open(idp).convert('RGBA'));m=np.array(cad);parts=[]
 for j,(name,color) in enumerate(colors.items()):
  mask=(np.linalg.norm(px[:,:,:3].astype(float)-color,axis=2)<6)&(px[:,:,3]>127);y,x=np.nonzero(mask)
  if len(x):parts.append({'name':name,'visible_pixels':len(x),'bbox':[int(x.min()),int(y.min()),int(x.max()),int(y.max())]})
  m[mask&~binary_erosion(mask)]=palette[j]
 crop=(190,300,750,652)
 for col,(im,label) in enumerate([(ref,'REFERENCE'),(cad,'CAD'),(Image.fromarray(m),'FRAME PINK / PANEL YELLOW / CHEEK CYAN')]):
  x=col*560;y=row*384;board.paste(im.crop(crop),(x,y+32));draw.text((x+5,y+5),f'{i}s {label}',font=font,fill='white')
 rows.append({'view':i,'crop':crop,'parts':parts,'sources':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [refp,cadp,idp]]})
board.save(out/'body-inspection.png');(out/'body-inspection.json').write_text(json.dumps(rows,indent=2)+'\n')
