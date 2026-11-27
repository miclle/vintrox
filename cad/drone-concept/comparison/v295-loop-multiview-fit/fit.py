"""Fit smooth CAD loop paths and radius to manually observed tube boundaries.

The prior rear-view highlight observations are not used as centreline targets.
Projected normal offsets approximate tube envelopes; actual opaque CAD masks
and fixed-view renders must verify occlusion and final visible boundaries.
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

from drone_underbody_loop import LOOP_PARAMETERS, RIGHT_LOOP_POINTS
from fit_drone_lower_pod_outline import project


# Visible edge segments only. Roots and shell-crossing arcs are omitted from
# these observations because the reference occludes them, never from the CAD.
OBSERVATIONS = [
    (90, -1, [[573,646],[553,670],[532,701],[540,724],[565,737],[594,735],[619,722],[641,691],[645,670],[581,650],[569,670],[554,699],[563,717],[584,723],[606,718],[628,701]]),
    (120, 1, [[359,670],[364,685],[366,698],[362,705],[354,704],[349,699],
              [348,688],[350,678],[371,669],[375,684],[376,699],[372,708],
              [365,713],[354,714],[343,710],[338,702],[338,690]]),
    (120, -1, [[575,665],[569,680],[562,694],[558,703],[563,707],[573,707],
               [584,698],[587,686],[590,675],[598,669],[597,687],[593,703],
               [584,715],[571,722],[559,722],[549,716],[546,706],[548,692]]),
    (180, 1, [[311,657],[311,684],[322,716],[346,738],[375,743],[400,734],
              [417,712],[423,685],[423,657],[322,657],[322,681],[333,708],
              [354,726],[377,727],[395,721],[407,704],[412,680],[411,657]]),
    (60, -1, [[520,666],[509,691],[515,723],[538,745],[564,754],[594,752],
               [622,739],[644,717],[651,693],[533,669],[524,692],[532,713],
               [550,730],[571,737],[592,736],[614,724],[630,707],[637,689]]),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    base = root/'cad/drone-concept/vintrox-drone-concept.FCStd'
    camera_path = root/'cad/drone-concept/comparison/v292-brow-shoulder-inset/video-comparison/cameras.json'
    cameras = json.loads(camera_path.read_text())
    source = np.asarray(RIGHT_LOOP_POINTS)
    t = np.asarray(LOOP_PARAMETERS)
    samples = np.linspace(0, 1, 1000)
    basis = []
    for index in range(len(source)):
        c = Part.BSplineCurve()
        c.interpolate([App.Vector(float(i == index), float(t[i]*100), 0)
                       for i in range(len(source))], Parameters=t.tolist())
        basis.append([c.value(float(s)).x for s in samples])
    basis = np.asarray(basis).T
    weights = np.sin(np.pi*t[:, None]*np.arange(1, 4))

    def stations(p):
        return source+weights@p[:9].reshape(3, 3)

    def envelope(points, frame, side, radius):
        points = points.copy()
        points[:, 0] *= side
        pixels = project(points, frame, cameras)
        tangent = np.gradient(pixels, axis=0)
        normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-8)
        pose = next(p for p in cameras['views'] if p['source_frame'] == frame)
        forward = np.asarray(pose['target_mm'])-pose['eye_mm']
        forward /= np.linalg.norm(forward)
        depth = (points-pose['eye_mm'])@forward
        focal = pose['lens_mm']/pose['sensor_width_mm']*cameras['resolution'][0]
        radius_profile = 2.2 + (radius - 2.2) * np.sin(np.pi*samples)**2
        offset = normal*(focal*radius_profile/depth)[:, None]
        return np.r_[pixels+offset, pixels-offset]

    def measure(p):
        points = basis@stations(p)
        rows = []
        for frame, side, xy in OBSERVATIONS:
            pixels = envelope(points, frame, side, p[-1])
            distances, indices = cKDTree(pixels).query(xy)
            rows.append({'source_frame': frame, 'side': side, 'reference_px': xy,
                         'nearest_px': pixels[indices].tolist(), 'distance_px': distances.tolist(),
                         'rms_px': float(np.sqrt(np.mean(distances**2)))})
        return rows

    def residual(p):
        displacement = stations(p)-source
        points = basis@stations(p)
        seat = (points[:, 2] < 40) & (points[:, 1] < 125)
        local_radius = 2.2 + (p[-1] - 2.2) * np.sin(np.pi*samples)**2
        clearance = 4*np.maximum(42+local_radius+.5-points[:, 0], 0)*seat
        image_errors = [np.asarray(r['distance_px']) * (3 if r['source_frame'] == 180 else 1)
                        for r in measure(p)]
        root_anchor = displacement[1:3] * [1.6, 1.6, 0.8]
        return np.r_[np.concatenate(image_errors), root_anchor.ravel(),
                     .18*displacement.ravel(), .6*np.diff(displacement, n=2, axis=0).ravel(),
                     clearance]

    lower, upper = [-10]*9+[2.2], [10]*9+[5.5]
    seeds = [np.r_[np.zeros(9), 4.5], np.r_[[10, 0, 0, -5, 0, 0, 0, 0, 0], 5]]
    fits = [least_squares(residual, seed, bounds=(lower, upper), diff_step=.0001, max_nfev=125)
            for seed in seeds]
    fit = min(fits, key=lambda f: np.sum(f.fun**2))
    right = stations(fit.x)
    # Remove floating sine remnants at the endpoints, preserving exact roots.
    right[[0, -1]] = source[[0, -1]]
    left = right.copy()
    left[:, 0] *= -1
    rows = measure(fit.x)
    curve = Part.BSplineCurve()
    curve.interpolate([App.Vector(*p) for p in right], Parameters=t.tolist())
    actual = np.asarray([list(curve.value(float(s))) for s in samples])
    error = float(np.max(np.linalg.norm(actual-basis@right, axis=1)))
    assert error < 1e-9
    result = {'baseline_fcstd_sha256': digest(base),
              'camera_config_sha256': digest(camera_path),
              'source_video_sha256': cameras['reference_video_sha256'],
              'script_sha256': digest(Path(__file__)),
              'method': '11 chord-parameter v276 stations; 9 low-frequency coefficients and tapered circular radius',
              'observation_kind': 'visible tube boundary segments',
              'source_control_parameters': t.tolist(), 'source_controls_mm': source.tolist(),
              'parameters': fit.x.tolist(), 'radius_mm': float(fit.x[-1]),
              'bounds': [lower, upper], 'cad_prescreen_max_error_mm': error,
              'regularization': {'displacement_weight_px_per_mm': .08, 'second_difference_weight_px_per_mm': .3},
              'seed_results': [{'cost': float(f.cost), 'nfev': f.nfev, 'success': bool(f.success)} for f in fits],
              'centreline_paths_mm': {'UnderbodyLoop0': left.tolist(), 'UnderbodyLoop1': right.tolist()},
              'fitted': rows, 'baseline': measure(np.r_[np.zeros(9), 2.2]),
              'fit_rms_px': float(np.sqrt(np.mean(np.concatenate([r['distance_px'] for r in rows])**2))),
              'limitations': ['manual visible boundary segments on dark material; uncertain source edges',
                             'frame 90 adds manual observations to the fit; frame 150 is held out',
                             'projected normal-offset circular envelopes approximate perspective and omit occlusion',
                             'opaque final CAD masks must verify visible boundaries',
                             'hidden roots, mirror symmetry and smooth circular tubes remain hypotheses',
                             'no full contour, manufacturing or physical acceptance']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('radius', result['radius_mm'], 'boundary rms', result['fit_rms_px'])
    print([(r['source_frame'], r['side'], r['rms_px']) for r in rows])


if __name__ == '__main__':
    main()
