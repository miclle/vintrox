from pathlib import Path
import subprocess,hashlib,json
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[5];s=root/'cad/drone-concept/comparison/rear-frame-edge-study';video=root/'references/alexander-shevchuk-drone/video-cam.mp4';out=s/'reference-sequence';out.mkdir(exist_ok=True);records=[];crop=(230,270,710,665)
for frame in [90,105,120,135,150]:
 p=out/f'frame-{frame:03}.png'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f'select=eq(n\\,{frame})','-frames:v','1',str(p)],check=True)
 records.append({'source_frame':frame,'seconds':frame/30,'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
board=Image.new('RGB',(5*480,427),'#111518');draw=ImageDraw.Draw(board);font=ImageFont.load_default(size=16)
for i,rec in enumerate(records):
 p=root/rec['path'];board.paste(Image.open(p).convert('RGB').crop(crop),(i*480,32));draw.text((i*480+8,8),f"{rec['seconds']}s / frame {rec['source_frame']}",font=font,fill='white')
board.save(out/'sequence.png');(out/'provenance.json').write_text(json.dumps({'reference_video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'frames':records,'crop_xyxy':crop,'method':'native source pixels; no brightness or spatial transform'},indent=2)+'\n')
