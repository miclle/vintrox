"""Inspect consecutive source views without image registration or warping."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[5];b=root/'cad/drone-concept/comparison';s=b/'petal-inner-edge-study';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();board=Image.new('RGB',(1880,1062),'#151719');draw=ImageDraw.Draw(board);font=ImageFont.load_default(size=18);sources=[]
for i,frame in enumerate([90,100,110,120,130,140,150,160]):
 p=b/'upper-boundary-study'/f'frame-{frame:03}.png';im=Image.open(p).convert('RGB');assert im.size==(940,800)
 # Same full-width bottom crop at native size.
 crop=(0,500,940,740);im=im.crop(crop)
 x=i%2*940;y=i//2*265;board.paste(im,(x,y+25));draw.text((x+8,y+3),f'SOURCE FRAME {frame} / {frame/30:.3f}s',font=font,fill='white');sources.append({'path':str(p),'sha256':sha(p),'source_frame':frame})
out=s/'reference-inner-edge-sequence.png';board.save(out);(s/'reference-inner-edge-sequence.json').write_text(json.dumps({'reference_video_sha256':sha(root/'references/alexander-shevchuk-drone/video-cam.mp4'),'script_sha256':sha(Path(__file__)),'crop_xyxy':[0,500,940,740],'pixel_transform':'identical native crop; no image scaling or registration','sources':sources,'image_sha256':sha(out),'observations':['Rear half of the segmented exit is visible in the reference; do not shorten it based on its low brightness.','Narrow bright terminal borders appear across adjacent views; width and exact folded profile remain uncertain.']},indent=2)+'\n')
