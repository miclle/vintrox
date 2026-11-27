"""Measure projected small-pod observations against saved visible ID boundaries."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(folder, observations):
    manifest = json.loads((folder / 'object-id-manifest.json').read_text())
    assert observations['camera_config_sha256'] == manifest['camera_config_sha256']
    objects = manifest['objects']
    palette = cKDTree([obj['rgb'] for obj in objects])
    ribs = np.array([obj['name'].startswith('LowerPodRib') for obj in objects])
    rows = []
    for obs in observations['observations'] + observations['additional_view_checks']:
        view = f"video-{obs['source_frame'] // 30:02d}"
        entry = next(item for item in manifest['images'] if item['view'] == view)
        path = folder / entry['path']
        assert digest(path) == entry['sha256']
        with Image.open(path) as image:
            rgba = np.asarray(image.convert('RGBA'))
        points = np.asarray(obs['reference_px'])
        x0, y0 = np.maximum(points.min(axis=0) - 40, 0)
        x1, y1 = np.minimum(points.max(axis=0) + 41, (rgba.shape[1], rgba.shape[0]))
        crop = rgba[y0:y1, x0:x1]
        distance, index = palette.query(crop[:, :, :3])
        mask = ribs[index] & (distance < 6) & (crop[:, :, 3] > 127)
        y, x = np.nonzero(mask ^ binary_erosion(mask))
        pixels = np.column_stack((x + x0, y + y0))
        distance, index = cKDTree(pixels).query(points)
        rows.append({
            'view': view,
            'side': obs['side'],
            'reference_px': points.tolist(),
            'nearest_px': pixels[index].tolist(),
            'distance_px': distance.tolist(),
            'rms_px': float(np.sqrt(np.mean(distance ** 2))),
            'max_px': float(distance.max()),
        })
    return {
        'fcstd_sha256': manifest['fcstd_sha256'],
        'camera_config_sha256': manifest['camera_config_sha256'],
        'method': 'Distance to the visible LowerPodRib family mask, cropped around previously marked terminal samples',
        'limitations': ['Includes rib gaps, attachment and occlusion edges', 'Samples only cover existing end-rim annotations'],
        'views': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('ids', 'observations', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.ids, json.loads(args.observations.read_text()))
    result['observations_sha256'] = digest(args.observations)
    result['script_sha256'] = digest(Path(__file__))
    args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
