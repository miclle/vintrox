"""Screen saved-hem extension against seven previously inspected views.

Nearest hem samples include hidden edges. This model-space hypothesis is not a
CAD candidate, silhouette score, or fresh held-out validation.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import least_squares

from fit_drone_nozzle_outline import OBSERVATIONS
from study_drone_source_registration import initial_pose
from study_drone_still_focal import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--joint', action='store_true',
                        help='Fit axial span, radial shear and local Y shear jointly at Z98')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    study = root/'cad/drone-concept/comparison'
    model = study/'v69-underbody-loop-radius2p2/candidate.FCStd'
    video_path = study/'v69-underbody-loop-radius2p2/video-comparison/cameras.json'
    still_path = study/'v69-underbody-loop-radius2p2/stills-comparison/cameras.json'
    extra_path = study/'v62-source-leaf-study/tip-holdout-90-150.json'
    tip_path = study/'exit-profile-study/multiview-exit-fit.json'
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    frame = App.Placement(App.Vector(0, 180, 173),
                          App.Rotation(App.Vector(0, 0, 1), axis))
    doc = App.openDocument(str(model))
    points, radial = [], []
    try:
        for index in range(12):
            shape = doc.getObject(f'NozzlePetalEndHem{index}').Shape.copy()
            shape.Placement = frame.inverse().multiply(shape.Placement)
            for edge in shape.Edges:
                samples = [list(v) for v in edge.discretize(Number=40)]
                points.extend(samples)
                angle = np.radians(index*30+30)
                radial.extend([[np.cos(angle), np.sin(angle)]]*len(samples))
    finally:
        App.closeDocument(doc.Name)
    points = np.asarray(points)
    video, still = json.loads(video_path.read_text()), json.loads(still_path.read_text())
    observations = [(video, next(p for p in video['views'] if p['source_frame'] == frame_id), xy, 'fit')
                    for frame_id, xy in OBSERVATIONS.items()]
    for item in json.loads(extra_path.read_text())['views']:
        pose = next(p for p in video['views'] if p['source_frame'] == item['source_frame'])
        observations.append((video, pose, item['reference_px'], 'previously_inspected_extra'))
    for item in json.loads(tip_path.read_text())['observations']:
        if item['view'].startswith('still-'):
            pose = next(p for p in still['views'] if p['name'] == item['view'])
            observations.append((still, pose, item['reference_px'], 'previously_inspected_extra'))
    def measure(parameters, station):
        factor, radial_shift, centre_shift = parameters
        transformed = points.copy()
        weight = (points[:, 2]-station)/17
        transformed[:, :2] += np.asarray(radial)*weight[:, None]*radial_shift
        transformed[:, 1] += weight*centre_shift
        transformed[:, 2] = station+(transformed[:, 2]-station)*factor
        world = np.asarray([list(frame.multVec(App.Vector(*v))) for v in transformed])
        rows = []
        for config, pose, xy, selection in observations:
            size = pose.get('resolution', config['resolution'])
            focal = pose['lens_mm']/pose['sensor_width_mm']*size[0]
            pixels = project(world, initial_pose(pose), focal, size)
            distances, _ = cKDTree(pixels).query(xy)
            rows.append({'view': pose['name'], 'selection': selection,
                         'rms_px': float(np.sqrt(np.mean(distances**2))),
                         'distances_px': distances.tolist()})
        record = {'parameters': list(parameters), 'views': rows}
        for selection, key in [('fit', 'fit_rms'), ('previously_inspected_extra', 'extra_rms')]:
            values = np.concatenate([row['distances_px'] for row in rows if row['selection'] == selection])
            record[key] = float(np.sqrt(np.mean(values**2)))
        return record
    records = []
    fit_record = None
    if args.joint:
        def residual(parameters):
            return np.concatenate([r['distances_px'] for r in measure(parameters, 98)['views']])
        lower, upper = [.8, -6, -5], [1.6, 10, 5]
        fit = least_squares(residual, [1.25, 2, 0], bounds=(lower, upper),
                            diff_step=.001, max_nfev=100)
        fit_record = {'parameters': fit.x.tolist(), 'bounds': [lower, upper],
                      'all_seven_views_rms_px': float(np.sqrt(np.mean(fit.fun**2))),
                      'active_bounds': fit.active_mask.tolist()}
        for parameters in [[1, 0, 0], [1.35, 0, 0], fit.x.tolist(), [1.5, 2.5, 4]]:
            records.append(measure(parameters, 98))
    else:
        for factor in [1, 1.08, 1.12, 1.16, 1.20, 1.24, 1.28]:
            record = measure([factor, 0, 0], 83)
            record['factor'] = factor
            records.append(record)
    for record in records:
        print(record['parameters'], record['fit_rms'], record['extra_rms'], flush=True)
    sources = [video_path, still_path, extra_path, tip_path,
               Path(__file__).with_name('fit_drone_nozzle_outline.py')]
    result = {'baseline_sha256': digest(model), 'script_sha256': digest(Path(__file__)),
              'sources': [{'path': str(p.relative_to(root)), 'sha256': digest(p)} for p in sources],
              'station_mm': 98 if args.joint else 83, 'factors': records,
              'parameter_names': ['axial_factor', 'radial_shift_per_17mm', 'centre_y_shift_per_17mm'],
              'joint_fit': fit_record,
              'limitations': ['previously inspected observations; no fresh held-out views',
                             'includes hidden hem edges; not silhouette or unique 3D reconstruction',
                             'hypothetical global affine points; actual CAD solid anchoring can differ']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
