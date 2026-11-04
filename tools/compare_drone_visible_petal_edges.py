"""Compare observed tips with actually visible petal-family boundaries.

Unlike hidden BRep edge samples, opaque ID masks honor occlusion. Boundaries
also include roots and occlusion edges, so this remains a partial diagnostic,
not full-part contour acceptance. No metric replaces the original whole IoU.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage
from scipy.spatial import cKDTree

from study_drone_source_registration import initial_pose
from study_drone_still_focal import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boundary(folder, view):
    manifest = json.loads((folder/'object-id-manifest.json').read_text())
    item = next(i for i in manifest['images'] if i['view'] == view)
    path = folder/item['path']
    assert digest(path) == item['sha256']
    rgba = np.asarray(Image.open(path).convert('RGBA'))
    # PNG color quantization/dither makes exact RGB equality leave interior
    # pinholes. Assign nearest palette entry with the same tolerance as the
    # existing object-attribution tools, then union the entire petal family.
    tree = cKDTree([o['rgb'] for o in manifest['objects']])
    distance, index = tree.query(rgba[:, :, :3].reshape(-1, 3))
    family = np.asarray([o['name'].startswith('NozzlePetal') for o in manifest['objects']])
    mask = family[index].reshape(rgba.shape[:2]) & (distance.reshape(rgba.shape[:2]) < 6) & (rgba[:, :, 3] > 127)
    edge = mask ^ ndimage.binary_erosion(mask)
    y, x = np.nonzero(edge)
    if not len(x):
        raise ValueError('no visible petal boundary')
    return manifest, np.column_stack([x, y]), edge


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--baseline-video-ids', type=Path, required=True)
    parser.add_argument('--baseline-still-ids', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    candidate = args.candidate
    baseline = root/'cad/drone-concept/comparison/v69-underbody-loop-radius2p2'
    observations = json.loads((candidate/'tip-measurement.json').read_text())
    mesh = json.loads((baseline/'meshes.json').read_text())
    screen = np.asarray(next(o['vertices'] for o in mesh['objects'] if o['name'] == 'ScreenPanel210x160x2'))
    rows, records = [], []
    for observation in observations['views']:
        view = observation['view']
        video = view.startswith('video-')
        camera_path = baseline/('video-comparison' if video else 'stills-comparison')/'cameras.json'
        cameras = json.loads(camera_path.read_text())
        pose = next(p for p in cameras['views'] if p['name'] == view)
        size = pose.get('resolution', cameras['resolution'])
        focal = pose['lens_mm']/pose['sensor_width_mm']*size[0]
        screen_px = project(screen, initial_pose(pose), focal, size)
        screen_span = float(np.ptp(screen_px[:, 0]))
        folders = [args.baseline_video_ids if video else args.baseline_still_ids,
                   candidate/('video-ids' if video else 'still-ids')]
        xy = np.asarray(observation['reference_px'])
        measurements, edges = [], []
        for folder in folders:
            manifest, points, edge = boundary(folder, view)
            assert manifest['camera_config_sha256'] == digest(camera_path)
            expected = observations['fcstd_sha256'] if folder == folders[1] else mesh['fcstd_sha256']
            assert manifest['fcstd_sha256'] == expected
            distances, indices = cKDTree(points).query(xy)
            measurements.append({'rms_px': float(np.sqrt(np.mean(distances**2))),
                                 'max_px': float(max(distances)),
                                 'distance_px': distances.tolist(),
                                 'max_fraction_projected_screen_width': float(max(distances)/screen_span),
                                 'nearest_visible_boundary_px': points[indices].tolist(),
                                 'id_manifest_sha256': digest(folder/'object-id-manifest.json')})
            edges.append(edge)
        if video:
            frame = pose['source_frame']//30+1
            source_path = baseline/'video-comparison/reference-frames'/f'frame-{frame:02d}.png'
            source = Image.open(source_path).convert('RGB')
        else:
            source_path = root/pose['source_image']
            source = Image.open(source_path).convert('RGB').resize(tuple(size), Image.Resampling.LANCZOS)
        crop = (max(0, int(xy[:, 0].min())-35), max(0, int(xy[:, 1].min())-35),
                min(size[0], int(xy[:, 0].max())+35), min(size[1], int(xy[:, 1].max())+35))
        row = Image.new('RGB', (1200, 260), (18, 21, 24))
        for index, label in enumerate(['REFERENCE + OBSERVED TIPS', 'v69 VISIBLE FAMILY EDGE', 'v78 VISIBLE FAMILY EDGE']):
            im = source.copy()
            if index:
                array = (np.asarray(im)*.3).astype(np.uint8)
                array[edges[index-1]] = [255, 80, 70]
                im = Image.fromarray(array)
            draw = ImageDraw.Draw(im)
            for px, py in xy:
                draw.ellipse((px-2, py-2, px+2, py+2), fill=(0, 235, 255))
            thumb = ImageOps.contain(im.crop(crop), (390, 225))
            row.paste(thumb, (400*index+(400-thumb.width)//2, 30))
            ImageDraw.Draw(row).text((400*index+6, 6), f'{view}: {label}', fill='white')
        rows.append(row)
        records.append({'view': view, 'reference_px': xy.tolist(), 'crop_xyxy': crop,
                        'projected_screen_horizontal_span_px': screen_span,
                        'baseline': measurements[0], 'candidate': measurements[1],
                        'source_sha256': digest(source_path)})
    result = {'fcstd_sha256': observations['fcstd_sha256'], 'baseline_fcstd_sha256': mesh['fcstd_sha256'],
              'script_sha256': digest(Path(__file__)), 'views': records,
              'method': 'nearest visible opaque petal-family mask boundary; fixed cameras and identical crops',
              'limitations': ['partial observed tips only; not full-part 5 percent contour acceptance',
                             'family boundary includes root and occlusion edges as well as terminal edges',
                             'opaque IDs approximate glass occlusion and raster edges',
                             'all observations previously inspected; no fresh held-out validation',
                             'projected screen horizontal span is view dependent, especially near side views',
                             'no revised primary whole-model IoU, image warp or part omission']}
    (candidate/'visible-petal-edges.json').write_text(json.dumps(result, indent=2)+'\n')
    board = Image.new('RGB', (1200, 260*len(rows)))
    for index, row in enumerate(rows):
        board.paste(row, (0, 260*index))
    board.save(candidate/'visible-petal-edges.png')
    print([(r['view'], round(r['baseline']['rms_px'], 2), round(r['candidate']['rms_px'], 2)) for r in records])


if __name__ == '__main__':
    main()
