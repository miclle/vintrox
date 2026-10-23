"""Unwarped side-frame detail crops: source, prior CAD, current CAD, overlay."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--after',type=Path,required=True)
    parser.add_argument('--comparison',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--view-index',type=int,choices=range(10),default=6)
    parser.add_argument('--crop',type=int,nargs=4,default=(180,280,620,680))
    parser.add_argument('--display-scale',type=int,choices=(1,2,3,4),default=1)
    args = parser.parse_args()
    before_manifest = args.before/'render-manifest.json'
    after_manifest = args.after/'render-manifest.json'
    before,after = (json.loads(p.read_text()) for p in (before_manifest,after_manifest))
    if before['camera_config_sha256'] != after['camera_config_sha256']:
        raise ValueError('Detail comparison requires identical cameras')
    files = [args.comparison/f'reference-frames/frame-{args.view_index+1:02d}.png',
             args.before/f'video-{args.view_index:02d}.png',args.after/f'video-{args.view_index:02d}.png']
    pictures = [Image.open(p).convert('RGB') for p in files]
    if any(p.size != (940,800) for p in pictures):
        raise ValueError('Expected native reference camera image dimensions')
    pictures.append(Image.blend(pictures[0],pictures[2],.5))
    crop = tuple(args.crop)
    width,height=crop[2]-crop[0],crop[3]-crop[1]
    if width<=0 or height<=0:raise ValueError('Invalid crop bounds')
    display_width,display_height=width*args.display_scale,height*args.display_scale
    board = Image.new('RGB',(4*display_width,display_height+32),(15,18,20))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=16)
    for i,(picture,label) in enumerate(zip(pictures,['REFERENCE','PREVIOUS CAD','CURRENT CAD','50% OVERLAY'])):
        detail=picture.crop(crop)
        if args.display_scale>1:
            detail=detail.resize((display_width,display_height),Image.Resampling.NEAREST)
        board.paste(detail,(display_width*i,32))
        draw.text((display_width*i+10,8),label,font=font,fill='white')
    board.save(args.output)
    manifest = {'fcstd_sha256':after['fcstd_sha256'],
                'prior_fcstd_sha256':before['fcstd_sha256'],
                'camera_config_sha256':after['camera_config_sha256'],
                'view_index':args.view_index,'crop_xyxy':crop,'display_scale':args.display_scale,
                'spatial_transformation':'identical pixel crop; optional common integer enlargement for display only',
                'source_files':[{'path':str(p),'sha256':digest(p)} for p in files],
                'image_path':str(args.output),'image_sha256':digest(args.output)}
    args.output.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__ == '__main__':
    main()
