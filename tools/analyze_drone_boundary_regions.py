"""Separate existing excess pixels by exterior and enclosed-dark-region location.

This is diagnosis only. The existing reference mask and primary IoU remain
unchanged. Enclosed regions include genuine apertures as well as dark materials;
neither class proves that a CAD part should be trimmed or omitted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage
from scipy.spatial import cKDTree
from compare_drone_reference import reference_mask


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', type=Path, required=True)
    parser.add_argument('--renders', type=Path, required=True)
    parser.add_argument('--comparison', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.ids/'object-id-manifest.json').read_text())
    renders = json.loads((args.renders/'render-manifest.json').read_text())
    report = json.loads((args.comparison/'comparison-report.json').read_text())
    assert manifest['fcstd_sha256'] == renders['fcstd_sha256'] == report['fcstd_sha256']
    assert manifest['camera_config_sha256'] == report['camera_config_sha256']
    objects = manifest['objects']
    tree = cKDTree([o['rgb'] for o in objects])
    aggregate = np.zeros(len(objects), dtype=np.int64)
    views, rows = [], []
    for i, item in enumerate(manifest['images']):
        name = item['view']
        id_path = args.ids/item['path']
        assert digest(id_path) == item['sha256']
        render_item = next(v for v in renders['images'] if v['view'] == name)
        render_path = args.renders/render_item['path']
        assert digest(render_path) == render_item['sha256']
        ids = np.asarray(Image.open(id_path).convert('RGBA'))
        cad = np.asarray(Image.open(render_path).convert('RGBA'))[:, :, 3] > 127
        source = Image.open(args.comparison/f'reference-frames/frame-{i+1:02}.png').convert('RGB')
        ref = reference_mask(np.asarray(source))
        excess = cad & ~ref
        enclosed = ndimage.binary_fill_holes(ref) & ~ref
        exterior = excess & ~enclosed
        distance, index = tree.query(ids[:, :, :3].reshape(-1, 3))
        assigned = (distance.reshape(cad.shape) < 6) & (ids[:, :, 3] > 127)
        count = np.bincount(index[(exterior & assigned).ravel()], minlength=len(objects))
        aggregate += count
        views.append({'view': name, 'original_silhouette_iou': report['views'][i]['silhouette_iou'],
                      'excess_pixels': int(excess.sum()),
                      'excess_in_enclosed_dark_regions_px': int((excess & enclosed).sum()),
                      'excess_outside_filled_reference_px': int(exterior.sum()),
                      'top_exterior_objects': [{'name': objects[j]['name'], 'pixels': int(count[j])}
                                               for j in np.argsort(-count)[:15] if count[j]]})
        diagnostic = (np.asarray(source)*.3).astype(np.uint8)
        diagnostic[excess & enclosed] = [255, 170, 0]
        diagnostic[exterior] = [255, 50, 100]
        diagnostic[ref & ~cad] = [0, 220, 255]
        Image.fromarray(diagnostic).save(args.ids/f'{name}-region-diagnostic.png')
        row = Image.new('RGB', (940, 245), (20, 23, 27))
        draw = ImageDraw.Draw(row)
        draw.text((8, 5), f'{name}: source | pink exterior excess; orange enclosed excess; cyan missing', fill='white')
        for j, im in enumerate([source, Image.fromarray(diagnostic)]):
            thumb = ImageOps.contain(im, (470, 215))
            row.paste(thumb, (j*470+(470-thumb.width)//2, 28))
        rows.append(row)
    families = {}
    for obj, count in zip(objects, aggregate):
        name = re.sub(r'(Left|Right).*', '', obj['name'])
        name = re.sub(r'[_0-9]+$', '', name)
        families[name] = families.get(name, 0)+int(count)
    result = {'fcstd_sha256': manifest['fcstd_sha256'],
              'camera_config_sha256': manifest['camera_config_sha256'],
              'source_script_sha256': digest(Path(__file__)),
              'comparison_report_sha256': digest(args.comparison/'comparison-report.json'),
              'primary_iou_unchanged': True, 'mean_silhouette_iou': report['mean_silhouette_iou'],
              'method': 'partition existing CAD excess by binary-fill-holes location; no revised foreground or IoU',
              'top_exterior_families': sorted([{'family': k, 'pixels': v} for k, v in families.items() if v], key=lambda r: -r['pixels']),
              'views': views,
              'limitations': ['enclosed dark regions can be material or genuine apertures',
                             'exterior class still includes dark silhouettes and open handles',
                             'opaque ID attribution is approximate at glass and antialiased edges',
                             'rankings identify inspection targets, not geometry correctness',
                             'no part omission, image registration or new acceptance metric']}
    (args.ids/'boundary-regions.json').write_text(json.dumps(result, indent=2)+'\n')
    board = Image.new('RGB', (940, 245*len(rows)))
    for i, row in enumerate(rows):
        board.paste(row, (0, 245*i))
    board.save(args.ids/'boundary-regions-board.png')
    print(json.dumps(result['top_exterior_families'][:12], indent=2))


if __name__ == '__main__':
    main()
