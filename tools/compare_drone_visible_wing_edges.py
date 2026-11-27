"""Compare annotated reference points with visible wing boundaries in fixed-camera CAD renders."""
import argparse
import json
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage
from scipy.spatial import cKDTree
import numpy as np
from study_drone_source_registration import initial_pose
from study_drone_still_focal import project

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'candidate', 'fit', 'mesh'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    base = args.baseline
    candidate = args.candidate
    fit = args.fit
    camera = base/'video-comparison/cameras.json'
    config = json.loads(camera.read_text())
    mesh = json.loads(args.mesh.read_text())
    assert mesh['fcstd_sha256'] == digest(base/'candidate.FCStd')
    screen = np.array(next(o['vertices'] for o in mesh['objects'] if o['name'] == 'ScreenPanel210x160x2'))
    models = [base, candidate]
    manifests = [json.loads((m/'video-ids/object-id-manifest.json').read_text()) for m in models]
    for model, manifest in zip(models, manifests):
        assert manifest['fcstd_sha256'] == digest(model/'candidate.FCStd')
        assert manifest['camera_config_sha256'] == digest(camera)
    rows = []
    records = []
    fit_report = json.loads(fit.read_text())
    assert fit_report['fcstd_sha256'] == manifests[0]['fcstd_sha256']
    assert fit_report['camera_config_sha256'] == digest(camera)
    for obs in fit_report['observations']:
        frame = obs['source_frame']
        view = f'video-{frame//30:02d}'
        pose = next(v for v in config['views'] if v['name']==view)
        size = pose.get('resolution', config['resolution'])
        span = np.ptp(project(screen, initial_pose(pose), pose['lens_mm']/pose['sensor_width_mm']*size[0], size)[:, 0])
        xy = np.array(obs['reference_px'])
        source = base/'video-comparison/reference-frames'/f'frame-{frame//30+1:02d}.png'
        ref = Image.open(source).convert('RGB')
        crop = (max(0,int(xy[:,0].min())-35), max(0,int(xy[:,1].min())-35),
                min(size[0],int(xy[:,0].max())+35), min(size[1],int(xy[:,1].max())+35))
        row=Image.new('RGB',(1350,300),(20,23,25))
        metrics=[]
        for i,label in enumerate(('REFERENCE', 'BASELINE', 'CANDIDATE')):
            img=ref.copy()
            if i:
                model, manifest = models[i-1], manifests[i-1]
                entry = next(v for v in manifest['images'] if v['view']==view)
                path = model/'video-ids'/entry['path']
                assert digest(path)==entry['sha256']
                rgba=np.asarray(Image.open(path).convert('RGBA'))
                d,k=cKDTree([o['rgb'] for o in manifest['objects']]).query(rgba[:,:,:3].reshape(-1,3))
                family=np.array([o['name'].startswith('Wing') and obs['side'] in o['name'] for o in manifest['objects']])
                mask=family[k].reshape(rgba.shape[:2]) & (d.reshape(rgba.shape[:2])<6) & (rgba[:,:,3]>127)
                edge=mask ^ ndimage.binary_erosion(mask)
                y,x=np.nonzero(edge)
                points=np.column_stack([x,y])
                distances,indices=cKDTree(points).query(xy)
                metrics.append({'model':label,'rms_px':float(np.sqrt(np.mean(distances**2))),
                                'max_px':float(max(distances)), 'max_fraction_projected_screen_width':float(max(distances)/span),
                                'nearest_visible_boundary_px':points[indices].tolist(),'distance_px':distances.tolist()})
                arr=np.asarray(img).copy()
                arr[edge]=[255,80,70]
                img=Image.fromarray(arr)
            draw=ImageDraw.Draw(img)
            for x,y in xy:
                draw.ellipse((x-2,y-2,x+2,y+2),fill=(0,255,255))
            cropped=ImageOps.contain(img.crop(crop),(435,267))
            row.paste(cropped,(i*450+(450-cropped.width)//2,25))
            ImageDraw.Draw(row).text((i*450+5,5),f'{view} {obs["side"]} {label}',fill='white')
        rows.append(row)
        records.append({'view':view,'side':obs['side'],'used_for_fit':obs['used_for_fit'],'reference_px':xy.tolist(),
                        'source_sha256':digest(source),'projected_screen_width_px':float(span),'measurements':metrics})
    board=Image.new('RGB',(1350,len(rows)*300))
    for i,row in enumerate(rows):
        board.paste(row,(0,i*300))
    board.save(candidate/'visible-wing-edges.png')
    report={'baseline_fcstd_sha256':manifests[0]['fcstd_sha256'],'fcstd_sha256':manifests[1]['fcstd_sha256'],
            'camera_config_sha256':digest(camera),'script_sha256':digest(Path(__file__)),'fit_sha256':digest(fit),'views':records,
            'method':'one-way observed samples to the visible wing-family ID boundary, identical camera and crop',
            'limitations':['historical manual samples','two non-fit observations cover root only','visible mask includes occlusion edges','not a complete component acceptance measurement']}
    (candidate/'visible-wing-edges.json').write_text(json.dumps(report,indent=2)+'\n')
    for v in records:
        print(v['view'],v['side'],v['used_for_fit'],[(round(m['rms_px'],2),round(100*m['max_fraction_projected_screen_width'],2)) for m in v['measurements']])


if __name__ == '__main__':
    main()
