"""Compare manual loop edges to final opaque CAD masks with real occlusion."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

from fit_drone_lower_pod_outline import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boundary(folder, frame, side):
    manifest = json.loads((folder/'object-id-manifest.json').read_text())
    item = next(i for i in manifest['images'] if i['view'] == f'video-{frame//30:02d}')
    path = folder/item['path']
    assert digest(path) == item['sha256']
    rgba = np.asarray(Image.open(path).convert('RGBA'))
    distance, index = cKDTree([o['rgb'] for o in manifest['objects']]).query(rgba[:, :, :3].reshape(-1, 3))
    name = 'UnderbodyLoop1' if side == 1 else 'UnderbodyLoop0'
    family = np.asarray([o['name'] == name for o in manifest['objects']])
    mask = family[index].reshape(rgba.shape[:2]) & (distance.reshape(rgba.shape[:2]) < 6) & (rgba[:, :, 3] > 127)
    edge = mask ^ ndimage.binary_erosion(mask)
    y, x = np.nonzero(edge)
    assert len(x)
    return manifest, mask, np.column_stack([x, y])


def main():
    parser = argparse.ArgumentParser()
    for name in ['candidate', 'baseline-ids', 'previous-ids']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    candidate = args.candidate
    root = Path(__file__).resolve().parents[1]
    baseline = root/'cad/drone-concept/comparison/v69-underbody-loop-radius2p2'
    fit = json.loads((candidate/'path-fit.json').read_text())
    camera_path = candidate/'video-comparison/cameras.json'
    cameras = json.loads(camera_path.read_text())
    assert digest(camera_path) == fit['camera_config_sha256']
    mesh = json.loads((candidate/'meshes.json').read_text())
    screen = np.asarray(next(o['vertices'] for o in mesh['objects'] if o['name'] == 'ScreenPanel210x160x2'))
    sources = [('v69', args.baseline_ids, digest(baseline/'candidate.FCStd')),
               ('v81', args.previous_ids, digest(root/'cad/drone-concept/comparison/v81-smooth-loop-radius5/candidate.FCStd')),
               ('v82', candidate/'video-ids', digest(candidate/'candidate.FCStd'))]
    records, rows = [], []
    for obs in fit['fitted']:
        frame, side = obs['source_frame'], obs['side']
        reference = Image.open(candidate/'video-comparison/reference-frames'/f'frame-{frame//30+1:02d}.png').convert('RGB')
        xy = np.asarray(obs['reference_px'])
        span = float(np.ptp(project(screen, frame, cameras)[:, 0]))
        box = (int(xy[:, 0].min())-18, int(xy[:, 1].min())-18,
               int(xy[:, 0].max())+18, int(xy[:, 1].max())+18)
        row = Image.new('RGB', (1440, 360), (20, 20, 20))
        draw = ImageDraw.Draw(row)
        measurements = []
        for i, (label, folder, expected) in enumerate(sources):
            manifest, mask, points = boundary(folder, frame, side)
            assert manifest['fcstd_sha256'] == expected
            assert manifest['camera_config_sha256'] == digest(camera_path)
            distances, index = cKDTree(points).query(xy)
            item = next(i for i in manifest['images'] if i['view'] == f'video-{frame//30:02d}')
            rgba = np.asarray(Image.open(folder/item['path']).convert('RGBA'))
            sampled = rgba[xy[:, 1], xy[:, 0]]
            color_distance, object_index = cKDTree([o['rgb'] for o in manifest['objects']]).query(sampled[:, :3])
            owners = [manifest['objects'][int(j)]['name'] if a[3] > 127 and d < 6 else 'background'
                      for a, d, j in zip(sampled, color_distance, object_index)]
            data = {'model': label, 'fcstd_sha256': expected,
                    'id_manifest_sha256': digest(folder/'object-id-manifest.json'),
                    'rms_px': float(np.sqrt(np.mean(distances**2))),
                    'max_px': float(max(distances)), 'distance_px': distances.tolist(),
                    'max_fraction_projected_screen_width': float(max(distances)/span),
                    'visible_object_at_observation': owners,
                    'nearest_visible_boundary_px': points[index].tolist()}
            measurements.append(data)
            rgb = np.asarray(reference).copy()
            rgb[mask] = (.5*rgb[mask]+.5*np.asarray([255, 60, 60])).astype('uint8')
            im = Image.fromarray(rgb)
            d = ImageDraw.Draw(im)
            for x, y in xy:
                d.ellipse((x-1, y-1, x+1, y+1), fill=(0, 255, 255))
            crop = im.crop(box)
            crop.thumbnail((450, 310))
            scale = min(450/crop.width, 310/crop.height)
            crop = crop.resize((int(crop.width*scale), int(crop.height*scale)))
            row.paste(crop, (i*480, 38))
            draw.text((i*480+4, 5), f'{label} frame {frame} side {side}: RMS {data["rms_px"]:.2f}px', fill='white')
        rows.append(row)
        records.append({'source_frame': frame, 'side': side, 'reference_px': xy.tolist(),
                        'projected_screen_horizontal_span_px': span, 'measurements': measurements})
    board = Image.new('RGB', (1440, len(rows)*360))
    for i, row in enumerate(rows):
        board.paste(row, (0, i*360))
    board.save(candidate/'visible-loop-edges.png')
    report = {'fcstd_sha256': digest(candidate/'candidate.FCStd'),
              'fit_sha256': digest(candidate/'path-fit.json'), 'camera_config_sha256': digest(camera_path),
              'script_sha256': digest(Path(__file__)), 'views': records,
              'method': 'nearest observed pixels to per-loop opaque visible mask boundary; fixed cameras',
              'limitations': ['manual uncertain dark-material edge observations, same data as fitting',
                             'opaque ID boundaries include occlusion edges and hidden-root boundaries',
                             'observation-to-CAD distances only; no complete contour or held-out acceptance',
                             'mask attribution is approximate at antialiasing and transparency',
                             'original whole-model IoU and segmentation remain unchanged']}
    (candidate/'visible-loop-edges.json').write_text(json.dumps(report, indent=2)+'\n')
    print([(r['source_frame'], r['side'], [(m['model'], m['rms_px'], m['max_fraction_projected_screen_width']) for m in r['measurements']]) for r in records])


if __name__ == '__main__':
    main()
