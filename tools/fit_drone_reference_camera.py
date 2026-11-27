"""Fit a turntable camera to reference landmarks, without using CAD vertices.

Run with FreeCAD Python (NumPy/SciPy/Pillow). Scale assumes a 200 mm source
screen width. Fitted dimensions are appearance estimates, not measurements.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.optimize import least_squares

PARAMETER_NAMES = [
    'orbit_radius_mm', 'focal_pixels', 'elevation_degrees', 'initial_azimuth_degrees',
    'target_y_mm', 'target_z_mm', 'wing_tip_x_mm', 'wing_tip_y_mm', 'wing_tip_z_mm',
    'reference_display_height_mm', 'target_x_mm',
]
# Approximate manual corners: top-left, top-right, bottom-left, bottom-right.
# Curved glass and hood occlusion limit their accuracy.
DISPLAY_CORNERS = {
    0: [(491,321), (820,295), (491,677), (820,619)],
    8: [(123,295), (456,324), (123,619), (456,676)],
    9: [(246,310), (701,310), (246,660), (701,660)],
}


def observations(frames):
    result = []
    for i in range(10):
        frame = Image.open(frames/f'frame-{i+1:02d}.png').convert('RGB')
        if frame.size != (940, 800):
            raise ValueError('Expected original 940 x 800 video frames')
        red, green, blue = np.asarray(frame, dtype=float).transpose(2, 0, 1)
        masks = [('red', (red > green*1.5) & (red > blue*1.6) & (red > 50)),
                 ('gold', (red > green*1.03) & (green > blue*1.4) & (red > 65))]
        for name, mask in masks:
            mask[150:] = False
            labels, count = ndimage.label(mask)
            sizes = np.bincount(labels.ravel())
            candidates = [k for k in range(1, count+1) if sizes[k] > 45]
            if not candidates:
                raise ValueError(f'Cannot find {name} wing tip in frame {i*30}')
            label = min(candidates, key=lambda k: np.where(labels == k)[0].min())
            ys, xs = np.where(labels == label)
            select = ys < ys.min()+5
            result.append((i, name, [float(xs[select].mean()), float(ys[select].mean())]))
    for i, corners in DISPLAY_CORNERS.items():
        result.extend((i, 'screen'+str(k), point) for k, point in enumerate(corners))
    return result


def project(parameters, frame, name):
    radius, focal, elevation, azimuth, cy, cz, wx, wy, wz, height, cx = parameters
    angle = math.radians(azimuth-36*frame)
    elevation = math.radians(elevation)
    toward = np.array([math.cos(angle)*math.cos(elevation),
                       math.sin(angle)*math.cos(elevation), math.sin(elevation)])
    right = np.array([-math.sin(angle), math.cos(angle), 0])
    up = np.cross(toward, right)
    if name in ('red', 'gold'):
        point = np.array([-wx if name == 'red' else wx, wy, wz])
    else:
        corner = int(name[-1])
        point = np.array([-100 if corner % 2 == 0 else 100, -9,
                          150+(height/2 if corner < 2 else -height/2)])
    delta = point-np.array([cx, cy, cz])
    depth = radius-np.dot(delta, toward)
    return np.array([470+focal*np.dot(delta, right)/depth,
                     400-focal*np.dot(delta, up)/depth])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    points = observations(args.frames)

    def residual(parameters):
        return np.concatenate([project(parameters, i, name)-point for i, name, point in points])

    initial = [800,1520,12,-126,130,163,147,247,352,160,-2]
    bounds = ([300,500,-10,-145,20,100,90,120,250,130,-30],
              [2000,5000,30,-110,250,220,230,350,450,180,30])
    fit = least_squares(residual, initial, bounds=bounds, loss='soft_l1',
                        f_scale=5, max_nfev=3000)
    if not fit.success:
        raise RuntimeError('Camera fitting did not converge: '+fit.message)
    errors = residual(fit.x).reshape(-1, 2)
    result = {
        'parameter_names': PARAMETER_NAMES, 'parameters': fit.x.tolist(),
        'observations': points,
        'predicted_pixels': [project(fit.x, i, name).tolist() for i, name, _ in points],
        'residual_pixels': errors.tolist(),
        'rms_px': float(np.sqrt(np.mean(errors**2))),
        'landmark_distance_rms_px': float(np.sqrt(np.mean(np.sum(errors**2, axis=1)))),
        'method': '20 extracted wing tips and 12 manual display corners; 36 degree increments; source display height fitted, actual CAD screen unchanged',
        'limitations': ['manual corner uncertainty', 'curved source screen approximated as a plane',
                       'symmetric tip assumption', '200 mm source width sets scale'],
        'reference_frame_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted(args.frames.glob('frame-*.png'))},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'coordinate_rms_px': result['rms_px'],
                      'parameters': dict(zip(PARAMETER_NAMES, fit.x))}, indent=2))


if __name__ == '__main__':
    main()
