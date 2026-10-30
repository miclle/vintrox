"""Fixed still-04 closeup; common crop and scale, no image registration."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ['before','after','cameras','output']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();config=json.loads(a.cameras.read_text())
    before=json.loads((a.before/'render-manifest.json').read_text());after=json.loads((a.after/'render-manifest.json').read_text())
    assert before['camera_config_sha256']==after['camera_config_sha256']==digest(a.cameras)
    pose=next(p for p in config['views'] if p['name']=='still-04');size=tuple(pose.get('resolution',config['resolution']))
    source=Path(pose['source_image']);ref=Image.open(source).convert('RGB').resize(size,Image.Resampling.LANCZOS)
    paths=[source,a.before/'still-04.png',a.after/'still-04.png']
    images=[ref,*[Image.open(p).convert('RGB') for p in paths[1:]]]
    assert all(im.size==size for im in images)
    images.append(Image.blend(images[0],images[2],.5));crop=(590,450,765,595);scale=4
    w,h=(crop[2]-crop[0])*scale,(crop[3]-crop[1])*scale
    board=Image.new('RGB',(4*w,h+32),(15,18,20));draw=ImageDraw.Draw(board)
    for i,(im,label) in enumerate(zip(images,['REFERENCE 04','PREVIOUS CAD','CANDIDATE CAD','50% OVERLAY'])):
        board.paste(im.crop(crop).resize((w,h),Image.Resampling.NEAREST),(i*w,32))
        draw.text((i*w+8,8),label,font=ImageFont.load_default(size=16),fill='white')
    board.save(a.output)
    result={'fcstd_sha256':after['fcstd_sha256'],'baseline_fcstd_sha256':before['fcstd_sha256'],
            'camera_config_sha256':digest(a.cameras),'script_sha256':digest(Path(__file__)),
            'source_files':[{'path':str(p),'sha256':digest(p)} for p in paths],
            'native_comparison_resolution':size,'crop_xyxy':crop,'display_scale':scale,
            'spatial_transformation':'uniform reference resize to fixed camera; identical crop and common integer enlargement; no warp',
            'image_path':str(a.output),'image_sha256':digest(a.output)}
    a.output.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
