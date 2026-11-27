"""Fit a bounded loop-centreline deformation to fixed video observations.

Dark-tube centre pixels are manual estimates, not physical measurements. All
views have been inspected; this is appearance fitting, not new holdout evidence.
The deformation acts on CAD centre points, never on reference images.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from experiment_drone_loop_radius_candidate import PATH
from fit_drone_lower_pod_outline import project


OBSERVATIONS = [
    (180, 1, [[316,655],[316,683],[328,712],[350,733],[377,734],
              [400,727],[414,709],[418,682],[417,655]]),
    (60, -1, [[526,665],[516,691],[524,718],[544,738],[568,746],
              [594,744],[618,732],[636,712],[644,691]]),
    (120, 1, [[372,657],[378,676],[383,692],[377,700],[369,699]]),
    (120, -1, [[577,654],[571,674],[564,696],[567,705],
               [578,707],[590,697],[596,678],[596,660]]),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deform(points, t, parameters, side):
    """Keep both hidden roots fixed and allow the visible loop to twist."""
    values = np.asarray(points).copy()
    weight = np.sin(np.pi*np.asarray(t))**.6
    weight[np.isclose(t, 0) | np.isclose(t, 1)] = 0
    dx, x_shear, dy, y_spread, dz, z_spread = parameters
    y, z = values[:, 1].copy(), values[:, 2].copy()
    # Offset and shear are nonnegative at the innermost source station. This
    # keeps the centreline outside the unchanged central seat; the loft still
    # needs an exact saved-solid collision check because it can overshoot.
    values[:, 0] = side*(44.5+weight*(dx+x_shear*(y-72.66)))
    values[:, 1] += weight*(dy+y_spread*(y-100))
    values[:, 2] += weight*(dz+z_spread*(z-30))
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    base = root/'cad/drone-concept/comparison/v69-underbody-loop-radius2p2'
    model = base/'candidate.FCStd'
    cameras_path = base/'video-comparison/cameras.json'
    cameras = json.loads(cameras_path.read_text())
    doc = App.openDocument(str(model))
    try:
        faces = [f for f in doc.getObject('UnderbodyLoop1').Shape.Faces if f.Surface.isUPeriodic()]
        if len(faces) != 1:
            raise ValueError('expected a single saved periodic pipe surface')
        face = faces[0]
        u0, u1, v0, v1 = face.ParameterRange
        t = np.linspace(0, 1, 500)
        points = np.asarray([np.mean([list(face.valueAt(float(u), float(v)))
                             for u in np.linspace(u0, u1, 16, endpoint=False)], axis=0)
                             for v in np.linspace(v0, v1, len(t))])
    finally:
        App.closeDocument(doc.Name)
    def measure(parameters):
        rows = []
        for frame, side, xy in OBSERVATIONS:
            pixels = project(deform(points, t, parameters, side), frame, cameras)
            distance, index = cKDTree(pixels).query(xy)
            rows.append({'source_frame': frame, 'side': side, 'reference_px': xy,
                         'nearest_px': pixels[index].tolist(), 'distance_px': distance.tolist(),
                         'rms_px': float(np.sqrt(np.mean(distance**2)))})
        return rows
    def residual(parameters):
        return np.concatenate([r['distance_px'] for r in measure(parameters)])
    lower = [0, 0, -30, -.8, -20, -.8]
    upper = [30, 1, 30, 1, 20, 1]
    fit = least_squares(residual, [1, .2, 0, .1, -2, 0], bounds=(lower, upper),
                        diff_step=.001, max_nfev=250)
    # Construct from the existing eleven interpolation stations. Their saved
    # curve parameter is recovered numerically; final saved pipe is remeasured.
    _, indices = cKDTree(points).query([[44.5, y, z] for y, z in PATH])
    control = np.asarray([[44.5, y, z] for y, z in PATH])
    right = deform(control, t[indices], fit.x, 1)
    left = right.copy()
    left[:, 0] *= -1
    result = {'baseline_fcstd_sha256': digest(model), 'camera_config_sha256': digest(cameras_path),
              'source_video_sha256': cameras['reference_video_sha256'],
              'script_sha256': digest(Path(__file__)),
              'parameter_names': ['x_offset_at_y72p66', 'x_y_shear', 'y_offset', 'y_spread', 'z_offset', 'z_spread'],
              'parameters': fit.x.tolist(), 'bounds': [lower, upper],
              'fit_rms_px': float(np.sqrt(np.mean(fit.fun**2))),
              'baseline': measure([0]*6), 'fitted': measure(fit.x),
              'centreline_paths_mm': {'UnderbodyLoop0': left.tolist(), 'UnderbodyLoop1': right.tolist()},
              'source_controls_mm': control.tolist(), 'source_control_parameters': t[indices].tolist(),
              'limitations': ['manual dark-tube centre observations; uncertain identification and thickness',
                             'frame180 observations reused from historical one-view fit',
                             'all observations previously inspected, not fresh held-out validation',
                             'mirror symmetry, fixed roots and smooth bounded deformation are hypotheses',
                             'saved swept centreline must be independently remeasured',
                             'no full-contour, manufacturing, electrical or physical acceptance']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('parameters', result['parameters'], 'rms', result['fit_rms_px'])
    print([(r['source_frame'], r['side'], r['rms_px']) for r in result['fitted']])


if __name__ == '__main__':
    main()
