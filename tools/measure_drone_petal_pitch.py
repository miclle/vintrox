"""Sparse rear petal-pitch diagnostic, independent of the whole silhouette.

At source frame 120 / row 590, three visible lower guide-rail pairs are
manually identified. Report their midpoint against visible saved CAD object
IDs, with the native reference pixels attached. This does not establish leaf
count on hidden surfaces, material fidelity, or complete contour accuracy.
"""
import argparse
import hashlib
import json
import io
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROW=590
PAIRS=[(417,429),(470,483),(519,530)]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ids',type=Path,required=True)
    p.add_argument('--renders',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    source=root/'cad/drone-concept/comparison/iteration-66/reference-frames/frame-05.png'
    video=root/'references/alexander-shevchuk-drone/video-cam.mp4'
    frame=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vf',r'select=eq(n\,120)',
                          '-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1'],check=True,capture_output=True)
    assert np.array_equal(np.asarray(Image.open(io.BytesIO(frame.stdout)).convert('RGB')),
                          np.asarray(Image.open(source).convert('RGB'))), 'Reference frame differs from native video'
    ids_path=args.ids/'object-id-manifest.json'
    info=json.loads(ids_path.read_text())
    render_manifest=json.loads((args.renders/'render-manifest.json').read_text())
    assert info['fcstd_sha256']==render_manifest['fcstd_sha256']
    assert info['camera_config_sha256']==render_manifest['camera_config_sha256']
    id_image=args.ids/'video-04.png';render=args.renders/'video-04.png'
    pixels=np.asarray(Image.open(id_image).convert('RGB'))
    centers=[]
    for i in range(32):
        group=[o for o in info['objects'] if o['name']==f'NozzlePetalRidge{i}' or o['name'].startswith(f'NozzlePetalGuide{i}_')]
        mask=np.zeros(pixels.shape[1],bool)
        for obj in group:mask |= np.all(pixels[ROW]==obj['rgb'],axis=1)
        x=np.flatnonzero(mask)
        if len(x):centers.append({'petal_index':i,'range_x_px':[int(x.min()),int(x.max())],'center_x_px':float((x.min()+x.max())/2)})
    records=[]
    for left,right in PAIRS:
        x=(left+right)/2
        chosen=min(centers,key=lambda c:abs(c['center_x_px']-x))
        records.append({'source_guide_rail_x_px':[left,right],'source_midpoint_px':[x,ROW],**chosen,'signed_offset_px':chosen['center_x_px']-x})
    assert len({c['petal_index'] for c in records})==len(records)
    errors=np.array([o['signed_offset_px'] for o in records])
    crop=(360,535,585,650);scale=3
    images=[Image.open(source).convert('RGB'),Image.open(render).convert('RGB')]
    width=(crop[2]-crop[0])*scale;height=(crop[3]-crop[1])*scale
    board=Image.new('RGB',(width*2,height+45),(15,18,20));draw=ImageDraw.Draw(board);font=ImageFont.load_default(size=17)
    for col,im in enumerate(images):
        draw.text((col*width+8,10),'REFERENCE RAIL MIDPOINTS' if col==0 else 'CAD VISIBLE RIDGE MIDPOINTS',font=font,fill='white')
        board.paste(im.crop(crop).resize((width,height),Image.Resampling.NEAREST),(col*width,45))
        for rec in records:
            x=rec['source_midpoint_px'][0] if col==0 else rec['center_x_px']
            u=col*width+(x-crop[0])*scale;v=45+(ROW-crop[1])*scale
            draw.line((u-8,v,u+8,v),fill=(0,240,255),width=2);draw.line((u,v-8,u,v+8),fill=(0,240,255),width=2)
    args.output.parent.mkdir(parents=True,exist_ok=True);png=args.output.with_suffix('.png');board.save(png)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    report={'fcstd_sha256':info['fcstd_sha256'],'camera_config_sha256':info['camera_config_sha256'],
            'measurement_script_sha256':digest(Path(__file__)),'object_id_manifest_sha256':digest(ids_path),
            'reference_video_sha256':digest(video),'native_source_frame_verified':True,'source_frame':120,'row_px':ROW,'manual_source_uncertainty_px':2,
            'observations':records,'rms_offset_px':float(np.sqrt(np.mean(errors**2))),'max_offset_px':float(abs(errors).max()),
            'visible_ridge_centers':centers,'source_files':[{'path':str(f.resolve().relative_to(root)),'sha256':digest(f)} for f in (source,id_image,render)],
            'image_path':str(png),'image_sha256':digest(png),
            'limitations':['three central visible guide pairs only','manual edge pairs, about 2 px uncertainty',
                            'nearest visible ridge matching; not a whole-contour or hidden-leaf count test',
                            'oblique rear views require separate visual review']}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('rms_offset_px','max_offset_px')}))


if __name__=='__main__':main()
