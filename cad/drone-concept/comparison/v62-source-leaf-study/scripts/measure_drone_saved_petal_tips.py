"""Project saved hem edges onto fixed reference-only nozzle observations.

This local diagnosis includes hidden hem segments; it is not a silhouette score
and cannot alone authorize adoption. Cameras and observations never fit CAD.
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
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-stills', action='store_true',
                        help='Also report the two existing static tip observations')
    parser.add_argument('--holdout', type=Path,
                        help='Additional manual video tip observations; never fitted by this script')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    camera_path = root/'cad/drone-concept/comparison/cameras.json'
    config = json.loads(camera_path.read_text())
    doc = App.openDocument(str(args.model))
    points = []
    names = [f'NozzlePetalEndHem{i}' for i in range(12)]
    try:
        for name in names:
            shape = doc.getObject(name).Shape
            for edge in shape.Edges:
                points.extend([list(vertex) for vertex in edge.discretize(Number=40)])
    finally:
        App.closeDocument(doc.Name)
    world = np.asarray(points)
    rows, distances = [], []
    sources = [(config, next(p for p in config['views'] if p['source_frame'] == frame), points)
               for frame, points in OBSERVATIONS.items()]
    extra_paths = []
    if args.holdout:
        for observation in json.loads(args.holdout.read_text())['views']:
            pose = next(p for p in config['views'] if p['source_frame'] == observation['source_frame'])
            sources.append((config, pose, observation['reference_px']))
        extra_paths.append(args.holdout)
    if args.include_stills:
        still_path = root/'cad/drone-concept/comparison/iteration-112-nozzle-depth2-candidate/stills-comparison/cameras.json'
        tip_path = root/'cad/drone-concept/comparison/exit-profile-study/multiview-exit-fit.json'
        stills = json.loads(still_path.read_text())
        tips = json.loads(tip_path.read_text())
        for observation in tips['observations']:
            if observation['view'].startswith('still-'):
                pose = next(p for p in stills['views'] if p['name'] == observation['view'])
                sources.append((stills, pose, observation['reference_px']))
        extra_paths.extend([still_path, tip_path])
    video_distances = []
    for camera_set, pose, observations in sources:
        size = pose.get('resolution', camera_set['resolution'])
        focal = pose['lens_mm']/pose['sensor_width_mm']*size[0]
        pixels = project(world, initial_pose(pose), focal, size)
        distance, index = cKDTree(pixels).query(observations)
        distances.extend(distance.tolist())
        if 'source_frame' in pose:
            video_distances.extend(distance.tolist())
        rows.append({'view': pose['name'], 'source_frame': pose.get('source_frame'),
                     'reference_px': observations, 'saved_edge_px': pixels[index].tolist(),
                     'distance_px': distance.tolist(),
                     'rms_px': float(np.sqrt(np.mean(distance**2)))})
    result = {'fcstd_sha256': digest(args.model), 'camera_config_sha256': digest(camera_path),
              'observation_script_sha256': digest(Path(__file__).with_name('fit_drone_nozzle_outline.py')),
              'measurement_script_sha256': digest(Path(__file__)),
              'reference_video_sha256': config['reference_video_sha256'],
              'extra_sources': [{'path': str(p.resolve().relative_to(root)), 'sha256': digest(p)} for p in extra_paths],
              'boundary_objects': names, 'sample_count': len(points), 'views': rows,
              'rms_px': float(np.sqrt(np.mean(np.square(distances)))),
              'video_rms_px': float(np.sqrt(np.mean(np.square(video_distances)))),
              'max_px': max(distances),
              'limitations': ['manual observations; three video views plus two stills when requested',
                             'nearest sampled hem edge includes hidden segments and thickness',
                             'diagnostic edge distance; not silhouette or unique 3D reconstruction']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'rms_px': result['rms_px'], 'max_px': result['max_px']}))


if __name__ == '__main__':
    main()
