"""Fit a root-anchored antenna curve to the exposed reference scanlines."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

from fit_drone_lower_pod_outline import project


SEARCH_WINDOWS = ((0, 280, 365), (3, 265, 350), (4, 465, 487),
                  (5, 590, 670), (8, 565, 640))
FITTED_FRAMES = (90, 120, 150)
CHECK_FRAMES = (0, 240)
ROOT_Y_MM = 243.75
REGULARIZATION = 0.2


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True,
                        help='Saved baseline package with its fixed video comparison')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    comparison = args.baseline / 'video-comparison'
    camera_path = comparison / 'cameras.json'
    cameras = json.loads(camera_path.read_text())
    samples = []
    for view, left, right in SEARCH_WINDOWS:
        with Image.open(comparison / 'reference-frames' / f'frame-{view + 1:02d}.png') as image:
            intensity = np.max(np.asarray(image.convert('RGB')), axis=2)
        for row in range(10, 96, 10):
            columns = np.flatnonzero(intensity[row, left:right] > 18) + left
            if not columns.size:
                raise ValueError(f'No antenna edges in frame {view * 30}, row {row}')
            samples.append({'frame': view * 30, 'row': row,
                            'midpoint_x': float((columns[0] + columns[-1]) / 2),
                            'left_x': int(columns[0]), 'right_x': int(columns[-1])})

    heights = np.linspace(237, 394, 600)
    stations = (heights - 237) / 100

    def residual(coefficients):
        linear, quadratic, cubic = coefficients
        y = (ROOT_Y_MM + linear * stations + quadratic * stations * stations
             + cubic * stations * stations * stations)
        points = np.column_stack([np.zeros_like(heights), y, heights])
        pixels = {frame: project(points, frame, cameras) for frame in FITTED_FRAMES}
        errors = []
        for sample in samples:
            frame = sample['frame']
            if frame in pixels:
                x, y = pixels[frame][::-1].T
                errors.append(np.interp(sample['row'], y, x) - sample['midpoint_x'])
        return np.r_[errors, coefficients * REGULARIZATION]

    solution = least_squares(residual, [0, 15, 0])
    if not solution.success:
        raise RuntimeError(solution.message)
    report = {'parameters': solution.x.tolist(), 'samples': samples,
              'baseline_fcstd_sha256': digest(args.baseline / 'candidate.FCStd'),
              'camera_sha256': digest(camera_path),
              'reference_sha256': cameras['reference_video_sha256'],
              'root_y_mm': ROOT_Y_MM, 'control_heights_mm': [*range(236, 385, 8), 385],
              'fitted_frames': FITTED_FRAMES, 'check_frames': CHECK_FRAMES,
              'search_windows': SEARCH_WINDOWS, 'regularization': REGULARIZATION}
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
