"""Compare small-pod lip observations and nearby loop occlusions in opaque IDs."""
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


def main():
    parser = argparse.ArgumentParser()
    for name in ['candidate', 'baseline', 'baseline-ids']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.candidate
    fit = json.loads((folder/'lip-fit.json').read_text())
    loop_fit = json.loads((root/'cad/drone-concept/comparison/v82-loop-visible-boundaries/path-fit.json').read_text())
    camera_path = folder/'video-comparison/cameras.json'
    cameras = json.loads(camera_path.read_text())
    mesh = json.loads((folder/'meshes.json').read_text())
    screen = np.asarray(next(o['vertices'] for o in mesh['objects'] if o['name'] == 'ScreenPanel210x160x2'))
    sources = [('v69', args.baseline_ids, args.baseline),
               (folder.name.split('-')[0], folder/'video-ids', folder/'candidate.FCStd')]
    records, rows = [], []
    for kind, observations in [('lip', fit['fitted']), ('loop', loop_fit['fitted'])]:
        for obs in observations:
            frame, side = obs['source_frame'], obs['side']
            xy = np.asarray(obs['reference_px'])
            span = float(np.ptp(project(screen, frame, cameras)[:, 0]))
            row = Image.new('RGB', (1000, 300), (20, 20, 20))
            draw = ImageDraw.Draw(row)
            measured = []
            box = (int(xy[:, 0].min())-20, int(xy[:, 1].min())-20,
                   int(xy[:, 0].max())+20, int(xy[:, 1].max())+20)
            for column, (label, ids, model) in enumerate(sources):
                manifest = json.loads((ids/'object-id-manifest.json').read_text())
                assert manifest['fcstd_sha256'] == digest(model)
                assert manifest['camera_config_sha256'] == digest(camera_path)
                item = next(i for i in manifest['images'] if i['view'] == f'video-{frame//30:02d}')
                path = ids/item['path']
                assert digest(path) == item['sha256']
                rgba = np.asarray(Image.open(path).convert('RGBA'))
                tree = cKDTree([o['rgb'] for o in manifest['objects']])
                distance, index = tree.query(rgba[:, :, :3].reshape(-1, 3))
                name = ('LowerPodRim_001' if side == 1 else 'LowerPodRim_1') if kind == 'lip' else ('UnderbodyLoop1' if side == 1 else 'UnderbodyLoop0')
                family = np.asarray([o['name'] == name for o in manifest['objects']])
                mask = family[index].reshape(rgba.shape[:2]) & (distance.reshape(rgba.shape[:2]) < 6) & (rgba[:, :, 3] > 127)
                edge = mask ^ ndimage.binary_erosion(mask)
                y, x = np.nonzero(edge)
                assert len(x), (name, frame)
                points = np.column_stack([x, y])
                distances, nearest = cKDTree(points).query(xy)
                sampled = rgba[xy[:, 1], xy[:, 0]]
                d, idx = tree.query(sampled[:, :3])
                owners = [manifest['objects'][int(j)]['name'] if a[3] > 127 and e < 6 else 'background'
                          for a, e, j in zip(sampled, d, idx)]
                measured.append({'model': label, 'fcstd_sha256': digest(model),
                                 'rms_px': float(np.sqrt(np.mean(distances**2))),
                                 'max_px': float(max(distances)), 'distance_px': distances.tolist(),
                                 'max_fraction_projected_screen_width': float(max(distances)/span),
                                 'visible_object_at_observation': owners,
                                 'nearest_visible_boundary_px': points[nearest].tolist()})
                reference = Image.open(folder/'video-comparison/reference-frames'/f'frame-{frame//30+1:02d}.png').convert('RGB')
                pixels = np.asarray(reference).copy()
                pixels[edge] = [30, 240, 240]
                im = Image.fromarray(pixels)
                markers = ImageDraw.Draw(im)
                for px, py in xy:
                    markers.ellipse((px-2, py-2, px+2, py+2), fill=(255, 70, 70))
                im = im.crop(box)
                im.thumbnail((480, 260))
                row.paste(im, (column*500, 30))
                draw.text((column*500+5, 5), f'{label} {kind} frame {frame} side {side}', fill='white')
            records.append({'kind': kind, 'source_frame': frame, 'side': side,
                            'reference_px': xy.tolist(), 'measurements': measured})
            rows.append(row)
    board = Image.new('RGB', (1000, len(rows)*300), (20, 20, 20))
    for i, row in enumerate(rows):
        board.paste(row, (0, i*300))
    board.save(folder/'visible-pod-loop-edges.png')
    result = {'fcstd_sha256': digest(folder/'candidate.FCStd'), 'script_sha256': digest(Path(__file__)),
              'camera_config_sha256': digest(camera_path), 'observations': records,
              'limitations': ['manual lip observations approximate band centre; compared to visible ID boundary',
                             'one-way point distance includes occlusion edges; not complete contour acceptance',
                             'all observations previously inspected; no new held-out evidence',
                             'opaque glass/edge attribution differs from photographic shading',
                             'no observations omitted and no change to primary IoU']}
    (folder/'visible-pod-loop-edges.json').write_text(json.dumps(result, indent=2)+'\n')
    print([(r['kind'], r['source_frame'], [round(x['rms_px'], 3) for x in r['measurements']]) for r in records])


if __name__ == '__main__':
    main()
