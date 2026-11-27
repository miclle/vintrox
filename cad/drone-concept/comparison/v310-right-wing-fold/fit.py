from pathlib import Path
import json
import sys

import FreeCAD as App
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from drone_concept import curved_wing_plate
from drone_wing_fold import gold_wing_rear_parts, GOLD_WING_FRONT_OFFSETS_LOCAL_MM
from fit_drone_lower_pod_outline import project

base = Path('cad/drone-concept/comparison/v306-wing-pose')
pose = json.loads((base / 'half-angle.json').read_text())
cameras = json.loads((base / 'video-comparison/cameras.json').read_text())
centre = App.Vector(*pose['hub_centres_mm']['Right'])
observation = next(o for o in pose['observations'] if o['source_frame'] == 210)
points = np.asarray(observation['reference_px'])
stations = (0, 1, 2, 3, 4, 5, 16, 17, 18, 19, 20, 21, 22, 23)
nominal = np.array([GOLD_WING_FRONT_OFFSETS_LOCAL_MM.get(i, 0) for i in stations])

def distances(delta):
    offsets = dict(zip(stations, (nominal + delta).tolist()))
    shape = gold_wing_rear_parts(5, curved_wing_plate, offsets)['WingEdgeRight']
    shape.rotate(centre, App.Vector(1, 0, 0), pose['angles_deg'][0])
    shape.rotate(centre, App.Vector(0, 1, 0), pose['angles_deg'][1])
    face = max(shape.Faces, key=lambda f: f.Area)
    outline = np.array([list(p) for edge in face.OuterWire.Edges for p in edge.discretize(Distance=.15)])
    projected = project(outline, 210, cameras)
    distance, idx = cKDTree(projected).query(points)
    return np.linalg.norm(projected[idx] - points, axis=1), projected[idx]

def residual(delta):
    d, nearest = distances(delta)
    return np.r_[(nearest-points).flatten(), delta * .6, np.diff(delta) * .3]

fit = least_squares(residual, np.zeros(len(stations))+.02, bounds=(-5,5), diff_step=.01, max_nfev=120)
baseline = distances(np.zeros(len(stations)))[0]
for scale in (.5, 1):
    d = distances(fit.x * scale)[0]
    print(scale, np.round(fit.x * scale,2), np.round(d,2), flush=True)
result={'stations': stations,'nominal_offsets_local_y_mm': nominal.tolist(),
        'delta_local_y_mm': fit.x.tolist(), 'baseline_distances_px': baseline.tolist(),
        'fit_distances_px': distances(fit.x)[0].tolist(),
        'source_frame': 210,'limitations':['Largest plate face projected with the fixed camera, including potentially occluded points', 'Single-view fit with regularization, requires saved CAD review']}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n')
