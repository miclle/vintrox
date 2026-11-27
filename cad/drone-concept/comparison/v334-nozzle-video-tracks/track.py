"""Track manually identified reference tips across adjacent, unwarped source frames."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion
from scipy.signal import correlate2d
from scipy.spatial import cKDTree


def match(previous, current, point, half=7, search=12):
    x, y = point
    radius = half + search
    a = previous[y-half:y+half+1, x-half:x+half+1].astype(float)
    b = current[y-radius:y+radius+1, x-radius:x+radius+1].astype(float)
    if a.shape != (2*half+1, 2*half+1) or b.shape != (2*radius+1, 2*radius+1):
        raise ValueError('Search region exceeds the source image')
    a -= a.mean()
    ones = np.ones_like(a)
    sums = correlate2d(b, ones, mode='valid')
    squares = correlate2d(b*b, ones, mode='valid')
    norm = np.sqrt(np.maximum(squares - sums*sums/a.size, 0)) * np.linalg.norm(a)
    scores = correlate2d(b, a, mode='valid') / np.maximum(norm, 1e-9)
    j, i = np.unravel_index(np.argmax(scores), scores.shape)
    return [int(x+i-search), int(y+j-search)], float(scores[j, i])


def visible_boundary(path, view, manifest):
    entry = next(v for v in manifest['images'] if v['view'] == view)
    data = path/entry['path']
    if hashlib.sha256(data.read_bytes()).hexdigest() != entry['sha256']:
        raise ValueError('Object ID image hash differs')
    rgba = np.asarray(Image.open(data).convert('RGBA'))
    objects = manifest['objects']
    distance, index = cKDTree([obj['rgb'] for obj in objects]).query(
        rgba[:, :, :3].reshape(-1, 3))
    ids = index.reshape(rgba.shape[:2])
    family = np.array([obj['name'].startswith('NozzlePetal') for obj in objects])
    mask = family[ids] & (distance.reshape(ids.shape) < 6) & (rgba[:, :, 3] > 127)
    y, x = np.nonzero(mask & ~binary_erosion(mask))
    return np.column_stack((x, y)), ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('video', 'ids', 'formal', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.ids/'object-id-manifest.json').read_text())
    formal = json.loads((args.formal/'video.json').read_text())
    source_hash = hashlib.sha256(args.video.read_bytes()).hexdigest()
    if source_hash != formal['reference_video_sha256'] or any(
        manifest[key] != formal[key] for key in ('fcstd_sha256', 'camera_config_sha256')
    ):
        raise ValueError('Reference video or saved-model camera binding differs')
    measurements = json.loads((args.formal/'visible-edges.json').read_text())
    anchors = [(60, [280, 626]), (90, [263, 606]), (180, [632, 646])]
    board = Image.new('RGB', (980, 3*162), (20, 23, 26))
    draw = ImageDraw.Draw(board)
    records = []
    for row, (frame, anchor) in enumerate(anchors):
        view = f'video-{frame//30:02}'
        metrics = next(v for v in measurements['views'] if v['view'] == view)
        old = metrics['reference_px'][int(np.argmax(metrics['candidate']['distance_px']))]
        edge, ids = visible_boundary(args.ids, view, manifest)
        distance, index = cKDTree(edge).query(anchor)
        nx, ny = edge[index]
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            subprocess.run(['ffmpeg', '-v', 'error', '-i', str(args.video), '-vf',
                            f'select=between(n\\,{frame-4}\\,{frame+4})', '-fps_mode', 'vfr',
                            str(folder/'%02d.png')], check=True)
            frames = [Image.open(p).convert('RGB') for p in sorted(folder.glob('*.png'))]
        if len(frames) != 9:
            raise ValueError('Expected nine source frames')
        gray = [np.asarray(im.convert('L')) for im in frames]
        track = {4: {'xy': anchor}}
        for direction in (-1, 1):
            for step in range(1, 5):
                i = 4 + step*direction
                before = track[i-direction]['xy']
                xy, score = match(gray[i-direction], gray[i], before)
                back, _ = match(gray[i], gray[i-direction], xy)
                track[i] = dict(xy=xy, correlation=score,
                                reverse_error_px=float(np.linalg.norm(np.subtract(back, before))))
        for col, i in enumerate(range(0, 9, 2)):
            x, y = anchor
            left, top = x-47, y-30
            tile = frames[i].crop((left, top, left+94, top+65)).resize((188, 130), Image.Resampling.NEAREST)
            x0, y0 = col*196, row*162+22
            board.paste(tile, (x0, y0))
            draw.text((x0+4, y0-17), f'Frame {frame+i-4}', fill='white')
            marks = [(track[i]['xy'], '#4bff8a')]
            if i == 4:
                marks.append((old, '#24ddff'))
            for (px, py), color in marks:
                mx, my = x0+2*(px-left)+1, y0+2*(py-top)+1
                draw.ellipse((mx-5, my-5, mx+5, my+5), outline=color)
        records.append(dict(source_frame=frame, historical_sample_px=old,
                            manual_anchor_px=anchor, nearest_visible_cad_px=[int(nx), int(ny)],
                            nearest_object=manifest['objects'][ids[ny, nx]]['name'],
                            distance_px=float(distance),
                            screen_width_px=metrics['projected_screen_horizontal_span_px'],
                            track=[dict(frame=frame+i-4, **track[i]) for i in range(9)]))
    args.output.mkdir(exist_ok=True, parents=True)
    board.save(args.output/'tracks.png')
    (args.output/'tracks.json').write_text(json.dumps(dict(
        video_sha256=source_hash, fcstd_sha256=formal['fcstd_sha256'],
        camera_config_sha256=formal['camera_config_sha256'], observations=records
    ), indent=2)+'\n')


if __name__ == '__main__':
    main()
