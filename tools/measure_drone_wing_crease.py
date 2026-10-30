"""Measure the saved paint-face crease using the fixed reference cameras."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
import numpy as np
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edges(document, suffix):
    side = -1 if suffix == 'Left' else 1
    shape = document.getObject('WingPaint'+suffix).Shape
    broad_faces = sorted(shape.Faces, key=lambda f:f.Area, reverse=True)[:2]
    outward = max(broad_faces, key=lambda f:side*f.CenterOfMass.x)
    return sorted(outward.OuterWire.Edges, key=lambda e:e.Length)


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=folder.parent/'vintrox-drone-concept.FCStd')
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=folder/'wing-crease-check.json')
    args = parser.parse_args()
    fit_path = folder/'wing-crease-study/crease-joint-fit.json'
    fit = json.loads(fit_path.read_text())
    assert digest(args.baseline) == fit['fcstd_sha256']
    cameras_path = folder/'cameras.json'
    cameras = json.loads(cameras_path.read_text())
    current = App.openDocument(str(args.model))
    baseline = App.openDocument(str(args.baseline))
    try:
        records = []
        for observation in fit['observations']:
            suffix = 'Left' if observation['side'] == -1 else 'Right'
            record = {k:observation[k] for k in ['source_frame','side','used_for_fit','reference_px']}
            for label, document in [('baseline',baseline),('current',current)]:
                curve = edges(document, suffix)[1]
                points = np.array([list(v) for v in curve.discretize(Distance=.2)])
                projected = project(points, record['source_frame'], cameras)
                distances, nearest = cKDTree(projected).query(record['reference_px'])
                record[label] = {'rms_px':float(np.sqrt(np.mean(distances**2))),
                                 'max_px':float(max(distances)),
                                 'nearest_px':projected[nearest].tolist()}
            records.append(record)
        before, after = edges(baseline,'Right'), edges(current,'Right')
        preserved = []
        for index, label in [(2,'front_curve'),(0,'upper_closing_edge')]:
            distances = []
            for source, target in [(before[index],after[index]),(after[index],before[index])]:
                distances.extend(target.distToShape(Part.Vertex(v))[0]
                                 for v in source.discretize(Distance=2))
            preserved.append({'edge':label,'bidirectional_sample_distance_max_mm':max(distances)})
        endpoint_distances = [min((v.Point-other.Point).Length for other in after[1].Vertexes)
                              for v in before[1].Vertexes]
        result = {'fcstd_sha256':digest(args.model),'baseline_fcstd_sha256':digest(args.baseline),
                  'measurement_script_sha256':digest(Path(__file__)),
                  'source_fit_sha256':digest(fit_path),'camera_config_sha256':digest(cameras_path),
                  'observations':records,'preserved_edges':preserved,
                  'crease_endpoint_distance_mm':endpoint_distances,
                  'limitations':['manual crease observations; two gold-side views were used for fitting',
                                 'surface lighting and reference edge interpretation remain uncertain',
                                 'front/closing edge sampling is not preservation of every projected pixel']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print([(r['source_frame'],r['baseline']['rms_px'],r['current']['rms_px']) for r in records])
    finally:
        App.closeDocument(current.Name)
        App.closeDocument(baseline.Name)


if __name__ == '__main__':
    main()
