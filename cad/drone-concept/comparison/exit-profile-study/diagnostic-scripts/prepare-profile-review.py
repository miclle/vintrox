"""Create hash-bound crop boards for the v46 exit experiment from repo root."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path.cwd()
BASE = ROOT/'cad/drone-concept/comparison'
STUDY = BASE/'exit-profile-study'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def board(name, crop, camera_path, baseline_dir, candidate_dir, filename):
    config = json.loads(camera_path.read_text())
    pose = next(p for p in config['views'] if p['name'] == name)
    size = tuple(pose.get('resolution', config['resolution']))
    source = (ROOT/pose['source_image'] if 'source_image' in pose else
              BASE/'iteration-80/reference-frames'/f"frame-{pose['source_frame']//30+1:02d}.png")
    old_path, new_path = baseline_dir/(name+'.png'), candidate_dir/(name+'.png')
    ref = Image.open(source).convert('RGB').resize(size, Image.Resampling.LANCZOS)
    old, new = Image.open(old_path).convert('RGB'), Image.open(new_path).convert('RGB')
    assert old.size == new.size == size
    panels = [(ref, 'REFERENCE'), (old, 'V46 BASELINE'),
              (new, 'SHARED ROOT / RADIUS -2.1 mm'),
              (Image.blend(ref, new, .5), 'TRIAL / REFERENCE 50% OVERLAY')]
    w, h = (crop[2]-crop[0])*2, (crop[3]-crop[1])*2
    canvas = Image.new('RGB', (w*4, h+40), (12, 15, 18))
    draw = ImageDraw.Draw(canvas)
    for col, (im, title) in enumerate(panels):
        canvas.paste(im.crop(crop).resize((w, h), Image.Resampling.LANCZOS), (col*w, 40))
        draw.text((col*w+8, 10), title, fill='white')
    output = STUDY/filename
    canvas.save(output)
    metadata = {'camera_sha256': digest(camera_path), 'crop_xyxy': crop,
                'uniform_scale': 2, 'overlay_alpha': .5,
                'sources': [{'path': str(p.relative_to(ROOT)), 'sha256': digest(p)}
                            for p in (source, old_path, new_path)],
                'image_sha256': digest(output),
                'method': 'same camera and common crop; no warp or per-part alignment'}
    output.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n')


for name, crop in [('still-04', (480, 400, 820, 700)), ('still-05', (50, 400, 400, 700))]:
    board(name, crop, BASE/'stills-51/cameras.json', BASE/'stills-51-renders',
          STUDY/'profile-21-lined/still-renders', name+'-profile21.png')
for name, crop in [('video-02', (175, 420, 480, 700)), ('video-04', (315, 380, 620, 710)),
                   ('video-06', (490, 420, 775, 700))]:
    board(name, crop, BASE/'cameras.json', BASE/'iteration-80-renders',
          STUDY/'profile-21-lined/video-renders', name+'-profile21.png')

