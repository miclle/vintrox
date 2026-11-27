"""Project saved CAD landmarks into fixed reference cameras, without image warps.

These sparse points check placement, not all component contours or detail fidelity.
Run with FreeCAD's bundled Python. Reference scale is appearance-derived.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import numpy as np


def center(shape):
    return np.average([tuple(s.CenterOfMass) for s in shape.Solids],
                      axis=0, weights=[s.Volume for s in shape.Solids]).tolist()


def project(point, frame, parameters):
    radius, focal, elevation, azimuth, cy, cz, *_, cx = parameters
    angle, elevation = math.radians(azimuth-36*frame), math.radians(elevation)
    toward = np.array([math.cos(angle)*math.cos(elevation),
                       math.sin(angle)*math.cos(elevation), math.sin(elevation)])
    right = np.array([-math.sin(angle), math.cos(angle), 0])
    up = np.cross(toward, right)
    delta = np.asarray(point)-[cx, cy, cz]
    depth = radius-delta@toward
    return np.array([470+focal*(delta@right)/depth, 400-focal*(delta@up)/depth])


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fit_path = root/'cad/drone-concept/comparison/camera-fit.json'
    fit = json.loads(fit_path.read_text())
    doc = App.openDocument(str(args.model))
    try:
        points = {}
        for side, suffix, color in [(-1, 'Left', 'red'), (1, 'Right', 'gold')]:
            vertices = [v.Point for v in doc.getObject('WingPaint'+suffix).Shape.Vertexes]
            top = max(v.z for v in vertices)
            points[color] = np.mean([tuple(v) for v in vertices if v.z >= top-.1], axis=0).tolist()
            points[color+'_hub'] = center(doc.getObject('WingHubMark'+suffix).Shape)
            lens = next(o for o in doc.Objects if o.Name.startswith('RearBeaconLens')
                        and center(o.Shape)[0]*side > 0)
            points[color+'_beacon'] = center(lens.Shape)
        for corner in range(4):
            points['screen'+str(corner)] = [-100 if corner%2 == 0 else 100, -9,
                                           225 if corner < 2 else 75]
        observations = fit['observations'] + [
            (0,'red_hub',[245,474]), (1,'red_hub',[408,478]), (2,'red_hub',[600,477]),
            (7,'gold_hub',[541,477]), (8,'gold_hub',[702,474]),
            (4,'red_beacon',[681,278]), (4,'gold_beacon',[269,278]),
            (1,'red_beacon',[180,267]), (2,'red_beacon',[284,275]), (2,'gold_beacon',[200,249]),
        ]
        results = []
        for frame, name, observed in observations:
            predicted = project(points[name], frame, fit['parameters'])
            error = float(np.linalg.norm(predicted-observed))
            results.append({'frame':frame*30, 'landmark':name, 'source_px':observed,
                            'cad_px':predicted.tolist(), 'distance_px':error})
        distances = np.array([r['distance_px'] for r in results])
        width, threshold = 455, 455*.05
        result = {
            'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'camera_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'method':'saved colored wing-tip top vertices, hub/lens centers, actual flat display corners',
            'reference_front_display_width_px':width, 'five_percent_threshold_px':threshold,
            'cad_landmarks_mm':points, 'observations':results,
            'distance_rms_px':float(np.sqrt(np.mean(distances**2))),
            'max_distance_px':float(distances.max()),
            'within_threshold':int((distances <= threshold).sum()), 'count':len(results),
            'limitations':['sparse landmarks do not certify whole contours',
                           'manual source points and curved display uncertainty',
                           'paint-tip vertices approximate the visible tip'],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('distance_rms_px','max_distance_px','within_threshold','count')}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
