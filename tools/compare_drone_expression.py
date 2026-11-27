"""Compare screen expression masks in fixed video views, including held-out views.

Threshold sensitivity is retained; this measures screen artwork in rendered
images, not whole-part geometry or optical performance of the curved cover.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage
from fit_drone_lower_pod_outline import project


GROUPS = {'left_eye': ['PixelEye_39', 'PixelEyeTop_39'],
          'right_eye': ['PixelEye27', 'PixelEyeTop27'],
          'mouth': ['PixelMouth', 'PixelSmileHighlight']}


def mask(image, roi, threshold):
    x0, y0, x1, y1 = roi
    pixels = np.asarray(image.convert('RGB'))[y0:y1, x0:x1]
    selected = ndimage.binary_closing(pixels[:, :, 1] < threshold, iterations=2)
    return ndimage.binary_fill_holes(selected)


def metrics(reference, candidate):
    a = reference ^ ndimage.binary_erosion(reference)
    b = candidate ^ ndimage.binary_erosion(candidate)
    errors = np.concatenate([ndimage.distance_transform_edt(~a)[b],
                             ndimage.distance_transform_edt(~b)[a]])
    return {'iou': float((reference & candidate).sum()/max((reference | candidate).sum(), 1)),
            'edge_mean_px': float(errors.mean()), 'edge_p95_px': float(np.percentile(errors, 95))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    cameras_path = args.baseline/'video-comparison/cameras.json'
    cameras = json.loads(cameras_path.read_text())
    base = json.loads((args.baseline/'meshes.json').read_text())
    candidate = json.loads((args.candidate/'meshes.json').read_text())
    meshes = [{o['name']: o for o in data['objects']} for data in [base, candidate]]
    rows = []
    observations = []
    for index in [0, 8, 9]:
        reference = Image.open(args.baseline/f'video-comparison/reference-frames/frame-{index+1:02}.png')
        renders = [Image.open(p/f'video-renders/video-{index:02}.png') for p in [args.baseline, args.candidate]]
        for group, names in GROUPS.items():
            points = np.concatenate([project(np.asarray(m[name]['vertices']), index*30, cameras)
                                     for m in meshes for name in names])
            x0, y0 = np.maximum(np.floor(points.min(axis=0)-25).astype(int), [0, 0])
            x1, y1 = np.minimum(np.ceil(points.max(axis=0)+25).astype(int), reference.size)
            roi = [int(x0), int(y0), int(x1), int(y1)]
            checks = []
            for threshold in [140, 160, 180]:
                ref = mask(reference, roi, threshold)
                checks.append({'green_threshold': threshold,
                               'baseline': metrics(ref, mask(renders[0], roi, threshold)),
                               'candidate': metrics(ref, mask(renders[1], roi, threshold))})
            observations.append({'view': f'video-{index:02}', 'group': group, 'roi_px': roi,
                                 'used_for_fitting': index == 9, 'thresholds': checks})
            crops = [ImageOps.contain(im.crop(roi), (300, 160)) for im in [reference, *renders]]
            row = Image.new('RGB', (900, 185), (20, 23, 27))
            draw = ImageDraw.Draw(row)
            for j, (im, label) in enumerate(zip(crops, ['REFERENCE', 'V69', args.candidate.name])):
                row.paste(im, (j*300+(300-im.width)//2, 25+(160-im.height)//2))
                draw.text((j*300+5, 5), f'{index:02} {group} {label}', fill='white')
            rows.append(row)
    board = Image.new('RGB', (900, len(rows)*185))
    for i, row in enumerate(rows):board.paste(row, (0, i*185))
    board.save(args.candidate/'expression-comparison.png')
    report = {'candidate_fcstd_sha256': candidate['fcstd_sha256'],
              'baseline_fcstd_sha256': base['fcstd_sha256'],
              'camera_sha256': hashlib.sha256(cameras_path.read_bytes()).hexdigest(),
              'method': 'fixed-camera projected ROI; green channel threshold; 2 px closing; filled feature holes',
              'fit_view': 'video-09', 'held_out_views': ['video-00', 'video-08'],
              'observations': observations,
              'limitations': ['threshold sensitivity; source texture and glass reflections affect masks',
                             'ROI crops are diagnostic only; no image registration or geometry warp',
                             'does not prove whole-part contours, optical behavior, manufacturing or physical acceptance']}
    (args.candidate/'expression-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    for threshold in [140, 160, 180]:
        for fit in [True, False]:
            items=[t for o in observations if o['used_for_fitting']==fit for t in o['thresholds'] if t['green_threshold']==threshold]
            print(threshold,'fitted' if fit else 'held-out',
                  {k:float(np.mean([t[k]['iou'] for t in items])) for k in ['baseline','candidate']})


if __name__ == '__main__':
    main()
