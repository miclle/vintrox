"""Measure visible antenna edges in fixed-camera object ID renders."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fit', type=Path, required=True)
    parser.add_argument('--ids', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fit = json.loads(args.fit.read_text())
    manifest_path = args.ids / 'object-id-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest['camera_config_sha256'] != fit['camera_sha256']:
        parser.error('object ID cameras differ from the reference observations')
    color, = (item['rgb'] for item in manifest['objects'] if item['name'] == 'Antenna')
    images = {item['view']: item for item in manifest['images']}
    results = []
    for frame in [*fit['fitted_frames'], *fit['check_frames']]:
        image = images[f'video-{frame // 30:02d}']
        path = args.ids / image['path']
        if digest(path) != image['sha256']:
            raise ValueError(f'Changed object ID image: {path}')
        with Image.open(path) as source:
            rgba = np.asarray(source.convert('RGBA'), dtype=float)
        rows = []
        for sample in (s for s in fit['samples'] if s['frame'] == frame):
            pixels = rgba[sample['row']]
            x = np.flatnonzero((np.linalg.norm(pixels[:, :3] - color, axis=1) < 6)
                               & (pixels[:, 3] > 127))
            if not x.size:
                raise ValueError(f"No visible antenna at frame {frame}, row {sample['row']}")
            rows.append({'row_px': sample['row'],
                         'center_error_px': float((x[0] + x[-1]) / 2 - sample['midpoint_x']),
                         'left_error_px': int(x[0]) - sample['left_x'],
                         'right_error_px': int(x[-1]) - sample['right_x']})
        results.append({'frame': frame, 'fitted': frame in fit['fitted_frames'],
                        'rows': rows,
                        'center_rms_px': float(np.sqrt(np.mean([r['center_error_px']**2 for r in rows])))})
    report = {'fcstd_sha256': manifest['fcstd_sha256'],
              'camera_sha256': manifest['camera_config_sha256'], 'fit_sha256': digest(args.fit),
              'object_id_manifest_sha256': digest(manifest_path), 'views': results,
              'limitations': ['Upper exposed scanlines only; the reference tip is cropped.',
                              'The extreme pixels can include a faint highlight or exclude dark material.']}
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
