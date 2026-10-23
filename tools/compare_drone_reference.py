"""Compare raw turntable frames with camera-matched CAD renders without warping.

Run with FreeCAD's bundled Python (Pillow, NumPy, SciPy) or equivalent packages.
Masks use the video's black background; scores are image-space diagnostics,
not 3D accuracy, and are only comparable with the same camera configuration.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage


def reference_mask(rgb):
    mask = np.max(rgb, axis=2) > 18
    mask = ndimage.binary_closing(mask, iterations=1)
    # Fill only tiny dark compression/material islands, preserving open handles.
    holes = ndimage.binary_fill_holes(mask) & ~mask
    labels, _ = ndimage.label(holes)
    sizes = np.bincount(labels.ravel())
    return mask | ((labels > 0) & (sizes[labels] < 100))


def compare(reference, render):
    if reference.size != render.size:
        raise ValueError('Reference and CAD render dimensions differ')
    ref = np.asarray(reference.convert('RGB'))
    cad_rgba = np.asarray(render.convert('RGBA'))
    alpha = cad_rgba[:, :, 3:4]/255
    cad = (cad_rgba[:, :, :3]*alpha).astype(np.uint8)
    rm = reference_mask(ref)
    cm = cad_rgba[:, :, 3] > 127
    re = rm ^ ndimage.binary_erosion(rm)
    ce = cm ^ ndimage.binary_erosion(cm)
    rd = ndimage.distance_transform_edt(~re)
    cd = ndimage.distance_transform_edt(~ce)
    errors = np.concatenate([rd[ce], cd[re]])
    metrics = {'silhouette_iou': float((rm & cm).sum()/max((rm | cm).sum(), 1)),
               'symmetric_edge_mean_px': float(errors.mean()),
               'symmetric_edge_p95_px': float(np.percentile(errors,95)),
               'reference_foreground_px': int(rm.sum()), 'cad_foreground_px': int(cm.sum())}
    overlay = (ref*.5+cad*.5).astype(np.uint8)
    outlines = (ref*.35).astype(np.uint8)
    outlines[ndimage.binary_dilation(re)] = [0,235,255]
    outlines[ndimage.binary_dilation(ce)] = [255,75,75]
    difference = np.zeros_like(ref)
    difference[rm & cm] = [150,155,158]
    difference[rm & ~cm] = [0,220,255]
    difference[cm & ~rm] = [255,70,70]
    return metrics, Image.fromarray(overlay), Image.fromarray(outlines), Image.fromarray(difference), Image.fromarray(cad)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--renders',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cameras',type=Path,default=Path('cad/drone-concept/comparison/cameras.json'))
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    video=root/'references/alexander-shevchuk-drone/video-cam.mp4'
    config=json.loads(args.cameras.read_text())
    manifest=json.loads((args.renders/'render-manifest.json').read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(args.cameras)==manifest['camera_config_sha256'], 'Camera configuration changed after rendering'
    assert digest(video)==config['reference_video_sha256'], 'Reference video changed'
    args.output.mkdir(parents=True,exist_ok=True)
    shutil.copy2(args.cameras, args.output/'cameras.json')
    refs=args.output/'reference-frames';refs.mkdir(exist_ok=True)
    if any('source_frame' in p for p in config['views']):
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',"select='not(mod(n,30))'",'-fps_mode','vfr',str(refs/'frame-%02d.png')],check=True)
    assert len(config['views']) == len(manifest['images']), 'Missing comparison view'
    rows=[];report=[]
    for pose,item in zip(config['views'],manifest['images']):
        assert pose['name']==item['view']
        render=args.renders/item['path'];assert digest(render)==item['sha256']
        if 'source_image' in pose:
            source=root/pose['source_image'];assert digest(source)==pose['source_sha256']
            ref=Image.open(source)
            size=tuple(pose.get('resolution',config['resolution']))
            assert abs(ref.width/ref.height-size[0]/size[1]) < .001, 'Reference aspect ratio changed'
            ref=ref.resize(size,Image.Resampling.LANCZOS)
        else:
            ref=Image.open(refs/f"frame-{pose['source_frame']//30+1:02d}.png")
        cad=Image.open(render)
        metrics,overlay,outline,difference,solid=compare(ref,cad)
        name=pose['name']
        overlay.save(args.output/(name+'-overlay.png'))
        outline.save(args.output/(name+'-edges.png'))
        difference.save(args.output/(name+'-difference.png'))
        row=Image.new('RGB',(1880,430),(20,23,27));draw=ImageDraw.Draw(row)
        for j,(im,label) in enumerate([(ref,'REFERENCE'),(solid,'CAD'),(overlay,'50% OVERLAY'),(difference,'CYAN: REFERENCE / RED: CAD')]):
            preview = ImageOps.contain(im, (470,400), Image.Resampling.LANCZOS)
            row.paste(preview,(j*470+(470-preview.width)//2,30+(400-preview.height)//2))
            draw.text((j*470+8,8),label,fill='white')
        row.save(args.output/(name+'-comparison.png'))
        rows.append(row.resize((940,215)))
        report.append({'view':name,'source_frame':pose.get('source_frame'),
                       'time_seconds':pose.get('time_seconds'),'source_image':pose.get('source_image'),
                       'score_interpretation':pose.get('score_interpretation','silhouette diagnostic only'),**metrics})
    board=Image.new('RGB',(940,215*len(rows)))
    for i,row in enumerate(rows):board.paste(row,(0,215*i))
    board.save(args.output/'comparison-board.png')
    result={'fcstd_sha256':manifest['fcstd_sha256'],'reference_video_sha256':digest(video),
            'render_manifest_sha256':digest(args.renders/'render-manifest.json'),
            'comparison_script_sha256':digest(Path(__file__)),
            'camera_config_sha256':digest(args.cameras),'camera_status':config['status'],
            'registration':'camera projection only; no image warp, stretch or per-part alignment',
            'excluded_from_cad':manifest['excluded_added_support_prefixes'],
            'mask_method':'reference max(RGB)>18; one-pixel closing; fill holes smaller than 100 pixels; CAD alpha>127',
            'limitations':['black-material/background ambiguity','camera fit uncertainty','visible surfaces only'],
            'mean_silhouette_iou':sum(x['silhouette_iou'] for x in report)/len(report),'views':report}
    (args.output/'comparison-report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
