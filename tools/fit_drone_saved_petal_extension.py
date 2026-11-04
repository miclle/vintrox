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

from fit_drone_nozzle_outline import OBSERVATIONS
from study_drone_source_registration import initial_pose
from study_drone_still_focal import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
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
    points = []
    try:
        for index in range(12):
            shape = doc.getObject(f'NozzlePetalEndHem{index}').Shape.copy()
            shape.Placement = frame.inverse().multiply(shape.Placement)
            for edge in shape.Edges:
                points.extend([list(v) for v in edge.discretize(Number=40)])
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
    records = []
    for factor in [1, 1.08, 1.12, 1.16, 1.20, 1.24, 1.28]:
        transformed = points.copy()
        transformed[:, 2] = 83+(transformed[:, 2]-83)*factor
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
        record = {'factor': factor, 'views': rows}
        for selection, key in [('fit', 'fit_rms'), ('previously_inspected_extra', 'extra_rms')]:
            values = np.concatenate([row['distances_px'] for row in rows if row['selection'] == selection])
            record[key] = float(np.sqrt(np.mean(values**2)))
        records.append(record)
        print(factor, record['fit_rms'], record['extra_rms'], flush=True)
    sources = [video_path, still_path, extra_path, tip_path,
               Path(__file__).with_name('fit_drone_nozzle_outline.py')]
    result = {'baseline_sha256': digest(model), 'script_sha256': digest(Path(__file__)),
              'sources': [{'path': str(p.relative_to(root)), 'sha256': digest(p)} for p in sources],
              'station_mm': 83, 'factors': records,
              'limitations': ['previously inspected observations; no fresh held-out views',
                             'includes hidden hem edges; not silhouette or unique 3D reconstruction',
                             'hypothetical global affine points; actual CAD solid anchoring can differ']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
