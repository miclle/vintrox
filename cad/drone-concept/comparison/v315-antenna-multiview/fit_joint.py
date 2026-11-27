"""Fit a shared antenna centreline to fixed video and static projections."""

import argparse
import json
from pathlib import Path
from scipy.optimize import least_squares
import numpy as np
from study_drone_source_registration import initial_pose
from study_drone_still_focal import project

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
work = Path(__file__).resolve().parent
base = Path('cad/drone-concept/comparison/v310-right-wing-fold')
fit = json.loads((work.parent/'v314-antenna-radius/fit.json').read_text())
video = json.loads((base/'video-comparison/cameras.json').read_text())
stills = json.loads((base/'stills-comparison/cameras.json').read_text())
# Enclose both visible edges on each reference scanline.
static = {
    'still-01': [(15,276,287),(30,283,293),(45,288,298),(60,293,303),(75,297,307),(90,301,311)],
    'still-02': [(30,255,265),(45,265,275),(60,273,282),(75,279,289)],
    'still-03': [(30,670,680),(45,664,674),(60,658,668),(75,653,663),(90,648,658),(105,644,654)],
    'still-04': [(15,676,688),(30,673,683),(45,669,679),(60,665,676),(75,662,673),(90,659,670),(105,656,668)],
    'still-05': [(15,156,168),(30,164,174),(45,172,181),(60,178,187),(75,184,190),(90,189,198),(105,193,199)],
    'still-06': [(15,265,277),(30,270,282),(45,274,287),(60,278,291),(75,282,294),(90,285,297),(105,287,300)],
}
heights = np.linspace(236, 402, 700)
t = (heights - 237)/100
powers = np.array([t, t**2, t**3]).T
initial = np.array(fit['parameters'])
entries = []
for config in (video, stills):
    for pose in config['views']:
        name = pose['name']
        if config is video:
            points = [(s['row'],s['left_x'],s['right_x']) for s in fit['samples']
                      if s['frame'] == pose['source_frame']]
        else:
            points = static.get(name, [])
        if points:
            size = pose.get('resolution',config['resolution'])
            entries.append((name, initial_pose(pose), pose['lens_mm']/pose['sensor_width_mm']*size[0],
                            size, np.array(points)))

def report(parameters):
    world = np.column_stack((np.zeros_like(t),fit['root_y_mm'] + powers@parameters,heights))
    results = {}
    for name, pose, focal, size, points in entries:
        x,y = project(world,pose,focal,size)[::-1].T
        results[name] = np.interp(points[:,0],y,x) - points[:,1:].mean(axis=1)
    return results

def residual(parameters):
    rows = report(parameters)
    return np.concatenate([d if n.startswith('video') else d*.45 for n,d in rows.items()] +
                          [(parameters-initial)*.3])

solution = least_squares(residual,initial,bounds=(initial-12, initial+12))
curves = {}
for label, pars in [('baseline', initial), ('joint',solution.x)]:
    curves[label] = {name:float(np.sqrt(np.mean(d*d))) for name,d in report(pars).items()}
print(json.dumps(curves,indent=2))
fit['parameters'] = solution.x.tolist()
fit['static_samples'] = static
fit['projected_centreline_rms_px'] = curves
fit['control_heights_mm'] = [*fit['control_heights_mm'], 390, 395]
args.output.write_text(json.dumps(fit,indent=2)+'\n')
