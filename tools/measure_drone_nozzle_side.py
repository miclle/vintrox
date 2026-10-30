"""Check exposed gold nozzle edges against black background in two side views.

The upper portion is excluded because the rear housing occludes it. All shell
patches and the rolled lip participate in the ID union: plaque occlusion must
not become a false shell edge. These fixed image rows are appearance diagnostics.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROWS=[440,450,460,470,480,490,495]
VIEWS=[(60,180,300,'left'),(180,660,780,'right')]
PREFIXES=('BassNozzleShell','BassWarning','BassSideStripe','BassNozzleRolledLip')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    p=argparse.ArgumentParser()
    p.add_argument('--ids',type=Path,required=True)
    p.add_argument('--renders',type=Path,required=True)
    p.add_argument('--comparison',type=Path,default=folder/'iteration-65')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    ids_path=args.ids/'object-id-manifest.json';render_path=args.renders/'render-manifest.json'
    ids=json.loads(ids_path.read_text());renders=json.loads(render_path.read_text())
    assert ids['fcstd_sha256']==renders['fcstd_sha256']
    assert ids['camera_config_sha256']==renders['camera_config_sha256']==digest(folder/'cameras.json')
    objects=[o for o in ids['objects'] if o['name'].startswith(PREFIXES)]
    assert len(objects)==12
    sources=[];observations=[];board=Image.new('RGB',(1880,1600),'black')
    for row,(frame,x0,x1,side) in enumerate(VIEWS):
        name=f'video-{frame//30:02}'
        ref_path=args.comparison/f'reference-frames/frame-{frame//30+1:02}.png'
        id_path=args.ids/(name+'.png');cad_path=args.renders/(name+'.png')
        assert digest(id_path)==next(i['sha256'] for i in ids['images'] if i['view']==name)
        assert digest(cad_path)==next(i['sha256'] for i in renders['images'] if i['view']==name)
        ref=Image.open(ref_path).convert('RGB');cad=Image.open(cad_path).convert('RGB')
        pixels=np.array(Image.open(id_path).convert('RGBA'));rgb=pixels[:,:,:3].astype(float)
        mask=np.zeros(pixels.shape[:2],dtype=bool)
        for obj in objects:mask|=np.linalg.norm(rgb-obj['rgb'],axis=2)<6
        mask&=pixels[:,:,3]>127
        source=np.asarray(ref);samples=[]
        overlay=Image.blend(ref,cad,.5);draw=ImageDraw.Draw(ref);other=ImageDraw.Draw(overlay)
        for y in ROWS:
            limits=[]
            for threshold in (12,18,24):
                xs=np.nonzero(np.max(source[y,x0:x1],axis=1)>threshold)[0]+x0
                assert len(xs)>0
                limits.append(int(xs[0] if side=='left' else xs[-1]))
            xs=np.nonzero(mask[y])[0];assert len(xs)>0
            actual=int(xs[0] if side=='left' else xs[-1]);expected=limits[1]
            samples.append({'reference_px':[expected,y],'visible_cad_px':[actual,y],
                            'signed_horizontal_error_px':actual-expected,
                            'thresholds':[12,18,24],'threshold_edge_x_px':limits})
            draw.ellipse((expected-3,y-3,expected+3,y+3),fill='cyan')
            other.line((expected,y,actual,y),fill='yellow',width=2)
            other.ellipse((actual-3,y-3,actual+3,y+3),fill='red')
        board.paste(ref,(0,row*800));board.paste(overlay,(940,row*800))
        observations.append({'source_frame':frame,'edge':side,'source_x_search':[x0,x1],'samples':samples})
        for path in (ref_path,id_path,cad_path):
            sources.append({'path':str(path.resolve().relative_to(root)),'sha256':digest(path)})
    errors=np.array([s['signed_horizontal_error_px'] for o in observations for s in o['samples']])
    spreads=[max(s['threshold_edge_x_px'])-min(s['threshold_edge_x_px']) for o in observations for s in o['samples']]
    png=args.output.with_suffix('.png');board.save(png)
    result={'fcstd_sha256':ids['fcstd_sha256'],'measurement_script_sha256':digest(Path(__file__)),
            'camera_config_sha256':ids['camera_config_sha256'],'object_id_manifest_sha256':digest(ids_path),
            'render_manifest_sha256':digest(render_path),'reference_video_sha256':json.loads((folder/'cameras.json').read_text())['reference_video_sha256'],
            'boundary_objects':[o['name'] for o in objects],'observations':observations,
            'rms_px':float(np.sqrt(np.mean(errors**2))),'max_px':float(max(abs(errors))),
            'max_source_threshold_spread_px':max(spreads),'source_files':sources,
            'image_path':str(png.resolve().relative_to(root)),'image_sha256':digest(png),
            'limitations':['14 horizontal samples on exposed side edges only','reference max RGB threshold 18, sensitivity 12/24',
                          'does not establish the shadowed upper shoulder or complete contour','pixel diagnostics, not physical dimensions']}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('rms_px','max_px','max_source_threshold_spread_px')}))


if __name__=='__main__':main()
