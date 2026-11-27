"""Fixed-camera diagnostic boards and per-view metrics; no registration changes."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[4]; b=root/'cad/drone-concept/comparison'; out=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads((out/'r12/candidate-check.json').read_text())
rows=[];boards=[]
for index,crop in [(3,(150,290,550,735)),(4,(220,290,720,735)),(5,(410,290,810,735))]:
 name=f'video-{index:02d}'
 paths=[b/f'iteration-82/reference-frames/frame-{index+1:02d}.png',b/f'iteration-82-renders/{name}.png',out/f'r12/video-renders/{name}.png']
 images=[]
 for path in paths:
  im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,'black');bg.alpha_composite(im);images.append(bg.convert('RGB').crop(crop))
 images.append(Image.blend(images[0],images[2],.5))
 w,h=images[0].size;board=Image.new('RGB',(w*4,h+34),(20,23,27));draw=ImageDraw.Draw(board)
 for j,(im,label) in enumerate(zip(images,['REFERENCE','V48 BASELINE','R1.2 CANDIDATE','50% OVERLAY'])):
  board.paste(im,(j*w,34));draw.text((j*w+8,10),label,fill='white')
 dest=out/f'{name}-detail.png';board.save(dest)
 meta={'model_sha256':check['fcstd_sha256'],'baseline_sha256':check['baseline_fcstd_sha256'],'camera_sha256':sha(b/'cameras.json'),'crop':crop,'alpha':.5,'method':'same camera and common pixel crop; no image warp','sources':[{'path':str(p.relative_to(root)),'sha256':sha(p)} for p in paths],'image_sha256':sha(dest)}
 dest.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');boards.append(str(dest.relative_to(root)))
for kind,baseline in [('video','iteration-82'),('stills','stills-53')]:
 old=json.loads((b/baseline/'comparison-report.json').read_text());new=json.loads((out/'r12'/kind/'comparison-report.json').read_text())
 assert old['camera_config_sha256']==new['camera_config_sha256']
 assert old['mask_method']==new['mask_method'] and old['excluded_from_cad']==new['excluded_from_cad']
 assert new['fcstd_sha256']==check['fcstd_sha256']
 rows.append({'kind':kind,'baseline_mean_iou':old['mean_silhouette_iou'],'candidate_mean_iou':new['mean_silhouette_iou'],'views':[{'view':a['view'],'baseline_iou':a['silhouette_iou'],'candidate_iou':c['silhouette_iou'],'delta_percentage_points':100*(c['silhouette_iou']-a['silhouette_iou'])} for a,c in zip(old['views'],new['views'])]})
review={'baseline_fcstd_sha256':check['baseline_fcstd_sha256'],'candidate_fcstd_sha256':check['fcstd_sha256'],'camera_sha256':sha(b/'cameras.json'),'script_sha256':sha(Path(__file__)),'views':rows,'boards':boards,'decision':'pending visual review'}
(out/'review.json').write_text(json.dumps(review,indent=2)+'\n')
for row in rows:print(row['kind'],row['baseline_mean_iou'],row['candidate_mean_iou'],row['views'])
