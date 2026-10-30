"""Test a shared rigid wing pose against both sides, with fixed cameras.

This is an outline diagnostic, not a replacement for rendered occlusion checks.
The saved model is read only. Rotations retain each hub centre.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from fit_drone_lower_pod_outline import project
from measure_drone_wing_profile import ADDITIONAL


# Full visible gold-wing perimeter in the unscaled video frame at seven seconds.
# Manual observations have several pixels of uncertainty, especially near the hub.
GOLD_OUTLINE = [[826,12],[838,75],[840,113],[779,200],[719,287],
                [698,319],[672,369],[643,419],[620,469],[601,505],[579,531],
                [548,548],[515,545],[487,526],[472,505],[468,476],
                [480,443],[522,397],[580,326],[648,242],[715,155],[783,64]]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(points, centre, side, angles):
    rx = Rotation.from_rotvec(np.radians([angles[0], 0, 0])).as_matrix()
    ry = Rotation.from_rotvec(np.radians([0, side*angles[1], 0])).as_matrix()
    return (points-centre) @ (ry @ rx).T + centre


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=folder.parent/'vintrox-drone-concept.FCStd')
    parser.add_argument('--output', type=Path, default=folder/'wing-pose-study/pose-fit.json')
    args = parser.parse_args()
    camera = folder/'cameras.json'
    cameras = json.loads(camera.read_text())
    construction = folder/'wing-outline-fit.json'
    outline = json.loads(construction.read_text())['source_outline_px']
    observations = [(30, 'Left', outline, True), (210, 'Right', GOLD_OUTLINE, True)]
    observations += [(f, s, px, False) for f, s, px in ADDITIONAL]
    document = App.openDocument(str(args.model))
    points, centres = {}, {}
    try:
        for suffix in ['Left', 'Right']:
            # Largest face is the plate's broad face; its outer wire retains the
            # concave root, unlike a convex hull of projected vertices.
            plate = document.getObject('WingEdge'+suffix).Shape
            face = max(plate.Faces, key=lambda f: f.Area)
            samples = [v for edge in face.OuterWire.Edges for v in edge.discretize(Distance=.2)]
            points[suffix] = np.array([list(v) for v in samples])
            centres[suffix] = np.array(list(document.getObject('WingHubSeat'+suffix).Shape.CenterOfMass))
    finally:
        App.closeDocument(document.Name)

    def distances(angles, frame, suffix, pixels):
        side = -1 if suffix == 'Left' else 1
        moved = transform(points[suffix], centres[suffix], side, angles)
        projected = project(moved, frame, cameras)
        distance, nearest = cKDTree(projected).query(pixels)
        return distance, projected[nearest]

    def residual(angles):
        return np.concatenate([distances(angles, f, s, px)[0]
                               for f, s, px, used in observations if used])

    fits = [least_squares(residual, start, bounds=([-3, -3], [3, 3]),
                          diff_step=.001, max_nfev=200)
            for start in [[0,0],[-1,-1],[1,1],[-1,1],[1,-1]]]
    best = min(fits, key=lambda fit: np.sum(fit.fun**2))
    records = []
    for frame, suffix, pixels, used in observations:
        record = {'source_frame': frame, 'side': suffix, 'used_for_fit': used,
                  'reference_px': pixels}
        for label, angles in [('baseline', [0,0]), ('candidate', best.x)]:
            distance, nearest = distances(angles, frame, suffix, pixels)
            record[label] = {'rms_px': float(np.sqrt(np.mean(distance**2))),
                             'max_px': float(max(distance)), 'nearest_px': nearest.tolist()}
        records.append(record)
    result = {'fcstd_sha256': digest(args.model), 'camera_config_sha256': digest(camera),
              'construction_outline_sha256': digest(construction),
              'source_video_sha256': cameras['reference_video_sha256'],
              'script_sha256': digest(Path(__file__)),
              'parameter_names': ['global_x_rotation_deg', 'mirrored_y_rotation_deg'],
              'angles_deg': best.x.tolist(), 'bounds_deg': [-3,3],
              'hub_centres_mm': {s: c.tolist() for s,c in centres.items()},
              'baseline_fit_rms_px': float(np.sqrt(np.mean(residual([0,0])**2))),
              'candidate_fit_rms_px': float(np.sqrt(np.mean(best.fun**2))),
              'observations': records,
              'limitations': ['manual source edge uncertainty of several pixels',
                              'plate outer wire excludes raised paint and folded face thickness',
                              'distance to projected wire does not establish visibility or occlusion',
                              'shared mirrored rigid pose is an appearance assumption',
                              'independent stills and full orbit must test any saved candidate'],
              'status': 'diagnostic only; authoritative model unchanged'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['angles_deg','baseline_fit_rms_px','candidate_fit_rms_px']}))


if __name__ == '__main__':
    main()
