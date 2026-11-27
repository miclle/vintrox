"""Fit the small-pod shell lip while retaining the saved terminal and axis."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from fit_drone_lower_pod_outline import project


OBSERVATIONS = [
    (0, -1, [[334,711],[350,709],[375,716],[400,734],[418,753],[425,768]]),
    (60, -1, [[660,724],[675,704],[697,689],[721,682],[738,686],[749,697]]),
    (180, 1, [[199,704],[205,688],[221,683],[241,688],[261,699],[280,717]]),
    (240, 1, [[538,755],[559,738],[582,719],[606,708],[617,706]]),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    base = root/'cad/drone-concept/comparison/v69-underbody-loop-radius2p2'
    cameras_path = base/'video-comparison/cameras.json'
    cameras = json.loads(cameras_path.read_text())
    doc = App.openDocument(str(base/'candidate.FCStd'))
    try:
        frames = {side: doc.getObject(name).Shape.Placement
                  for side, name in [(-1, 'LowerPodRim_1'), (1, 'LowerPodRim_001')]}
    finally:
        App.closeDocument(doc.Name)
    angle = np.linspace(0, 2*np.pi, 1440, endpoint=False)

    def measure(parameters):
        z, radius = parameters
        rows = []
        for frame, side, xy in OBSERVATIONS:
            points = np.asarray([list(frames[side].multVec(App.Vector(radius*np.cos(a), radius*np.sin(a), z))) for a in angle])
            px = project(points, frame, cameras)
            distance, index = cKDTree(px).query(xy)
            rows.append({'source_frame': frame, 'side': side, 'reference_px': xy,
                         'nearest_px': px[index].tolist(), 'distance_px': distance.tolist(),
                         'rms_px': float(np.sqrt(np.mean(distance**2)))})
        return rows

    def residual(parameters):
        return np.concatenate([r['distance_px'] for r in measure(parameters)])

    fit = least_squares(residual, [36, 27.5], bounds=([30, 22], [46, 32]), diff_step=.0001)
    rows = measure(fit.x)
    result = {'baseline_fcstd_sha256': digest(base/'candidate.FCStd'),
              'camera_config_sha256': digest(cameras_path),
              'source_video_sha256': cameras['reference_video_sha256'],
              'script_sha256': digest(Path(__file__)),
              'parameter_names': ['lip_local_z_mm', 'lip_major_radius_mm'],
              'parameters': fit.x.tolist(), 'baseline_parameters': [36, 27.5],
              'baseline': measure([36, 27.5]), 'fitted': rows,
              'rms_px': float(np.sqrt(np.mean(fit.fun**2))),
              'limitations': ['manual visible lip segments; dark shell/metal boundary uncertain',
                             'fixed saved pod axes and terminals; mirrored circular lip assumed',
                             'all source views previously inspected; no fresh held-out evidence',
                             'no complete visible contour or physical acceptance']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(result['parameters'], result['rms_px'])
    print([(r['source_frame'], r['rms_px']) for r in rows])


if __name__ == '__main__':
    main()
