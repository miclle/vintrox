"""Fit local mirrored loop stations to the existing fixed-camera observations.

This relaxes v79's global shear, with bounded station motion and an explicit
smoothness prior. Same manual observations are reused, never held-out evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from experiment_drone_loop_radius_candidate import PATH
from fit_drone_loop_multiview import OBSERVATIONS
from fit_drone_lower_pod_outline import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--smooth', action='store_true', help='nine low-frequency sine coefficients instead of independent stations')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    base = root/'cad/drone-concept/comparison/v69-underbody-loop-radius2p2'
    previous = root/'cad/drone-concept/comparison/v79-loop-multiview-path/path-fit.json'
    camera_path = base/'video-comparison/cameras.json'
    cameras = json.loads(camera_path.read_text())
    source = np.asarray([[44.5, y, z] for y, z in PATH])
    seed = np.asarray(json.loads(previous.read_text())['centreline_paths_mm']['UnderbodyLoop1'])
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(source, axis=0), axis=1))]
    t /= t[-1]
    samples = np.linspace(0, 1, 1000)
    # OCCT estimates endpoint tangents differently from scipy CubicSpline.
    # With fixed knots its interpolation is linear in station coordinates;
    # use its actual unit-station basis in the optimizer.
    basis = []
    for index in range(len(source)):
        curve = Part.BSplineCurve()
        curve.interpolate([App.Vector(float(i == index), float(t[i]*100), 0) for i in range(len(source))],
                          Parameters=t.tolist())
        basis.append([curve.value(float(s)).x for s in samples])
    basis = np.asarray(basis).T

    def stations(parameters):
        if args.smooth:
            weights = np.sin(np.pi*t[:, None]*np.arange(1, 4))
            return source+weights@parameters.reshape(3, 3)
        values = source.copy()
        values[1:-1] = parameters.reshape(-1, 3)
        return values

    def measure(parameters):
        points = basis@stations(parameters)
        rows = []
        for frame, side, xy in OBSERVATIONS:
            mirrored = points.copy()
            mirrored[:, 0] *= side
            pixels = project(mirrored, frame, cameras)
            distance, index = cKDTree(pixels).query(xy)
            rows.append({'source_frame': frame, 'side': side, 'reference_px': xy,
                         'nearest_px': pixels[index].tolist(), 'distance_px': distance.tolist(),
                         'rms_px': float(np.sqrt(np.mean(distance**2)))})
        return rows

    def residual(parameters):
        displacement = stations(parameters)-source
        points = basis@stations(parameters)
        # Broad low-frequency motion avoids the point-fitting zigzags of v80.
        clearance = np.maximum(46-points[:, 0], 0)*((points[:, 2] < 40) & (points[:, 1] < 125))
        return np.r_[np.concatenate([r['distance_px'] for r in measure(parameters)]),
                     .1*displacement.ravel(), .4*np.diff(displacement, n=2, axis=0).ravel(),
                     clearance if args.smooth else []]

    lower, upper = source[1:-1]-[0, 12, 12], source[1:-1]+[32, 12, 12]
    start = seed[1:-1].ravel()
    if args.smooth:
        weights = np.sin(np.pi*t[:, None]*np.arange(1, 4))
        start = np.linalg.lstsq(weights, seed-source, rcond=None)[0].ravel()
        lower, upper = np.full(9, -25.), np.full(9, 25.)
    fit = least_squares(residual, start, bounds=(lower.ravel(), upper.ravel()),
                        diff_step=.0001, max_nfev=500)
    right = stations(fit.x)
    curve = Part.BSplineCurve()
    curve.interpolate([App.Vector(*p) for p in right], Parameters=t.tolist())
    actual = np.asarray([list(curve.value(float(s))) for s in samples])
    interpolation_error = float(np.max(np.linalg.norm(actual-basis@right, axis=1)))
    assert interpolation_error < 1e-9, interpolation_error
    left = right.copy()
    left[:, 0] *= -1
    observations = measure(fit.x)
    result = {'baseline_fcstd_sha256': digest(base/'candidate.FCStd'),
              'camera_config_sha256': digest(camera_path),
              'source_video_sha256': cameras['reference_video_sha256'],
              'script_sha256': digest(Path(__file__)), 'seed_fit_sha256': digest(previous),
              'method': '11 chord-parameter cubic interpolation stations; endpoints fixed; '+('9 low-frequency sine coefficients' if args.smooth else '27 bounded local coordinates'),
              'parameters': fit.x.tolist(), 'bounds': [lower.tolist(), upper.tolist()],
              'regularization': {'displacement_weight_px_per_mm': .1, 'second_difference_weight_px_per_mm': .4},
              'cad_prescreen_max_error_mm': interpolation_error,
              'optimizer': {'success': bool(fit.success), 'message': fit.message, 'nfev': fit.nfev},
              'source_controls_mm': source.tolist(), 'source_control_parameters': t.tolist(),
              'centreline_paths_mm': {'UnderbodyLoop0': left.tolist(), 'UnderbodyLoop1': right.tolist()},
              'baseline': measure(np.zeros(9) if args.smooth else source[1:-1].ravel()), 'fitted': observations,
              'fit_rms_px': float(np.sqrt(np.mean(np.concatenate([r['distance_px'] for r in observations])**2))),
              'limitations': ['same uncertain manual dark-tube observations as v79; no fresh held-out data',
                             '27 coordinates and smoothness priors do not recover unique hidden geometry',
                             'CAD interpolation and saved loft must be independently remeasured',
                             'station x bounds alone do not guarantee interpolated support clearance',
                             'no full contour, manufacturing or physical acceptance']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(result['optimizer'], 'rms', result['fit_rms_px'])
    print([(r['source_frame'], r['side'], r['rms_px']) for r in observations])


if __name__ == '__main__':
    main()
