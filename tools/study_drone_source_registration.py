"""Diagnose still-photo registration from reference-only 3D reconstruction.

The fitted root circle comes from the reference video, not CAD vertices. The
video-derived terminal circle and static-photo petal tips are held out of this
camera fit. Nothing replaces the formal model or formal camera configuration.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from study_drone_still_focal import basis, project

ROOT_POINTS = {
    'still-04': [[550,533],[580,510],[610,493],[640,480],
                 [670,473],[700,472],[730,480],[746,493]],
    'still-05': [[125,479],[137,467],[155,462],[180,464],
                 [205,472],[230,484],[253,498],[270,513]],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initial_pose(pose):
    outward = np.array(pose['eye_mm'])-pose['target_mm']
    outward /= np.linalg.norm(outward)
    return np.r_[pose['eye_mm'], math.degrees(math.atan2(outward[1],outward[0])),
                 math.degrees(math.asin(outward[2])), pose.get('roll_degrees',0)]


def circle_geometry(parameters):
    y,z,r,beta = parameters
    beta = math.radians(beta)
    center = np.array([0,y,z])
    u,v = np.array([r,0,0]), np.array([0,-r*math.cos(beta),-r*math.sin(beta)])
    return center,u,v


def circle_pixels(parameters, q, size):
    center,u,v = circle_geometry(parameters)
    angles = np.linspace(0,2*math.pi,2880,endpoint=False)
    world = center+np.cos(angles)[:,None]*u+np.sin(angles)[:,None]*v
    return project(world,q[:6],q[6],size)


def ellipse_residual(parameters, q, size, observations):
    """Smooth Sampson distance to the projected circle's analytic conic."""
    center,u,v = circle_geometry(parameters)
    outward,right,up = basis(q[:6])
    forward = -outward
    focal = q[6]
    matrix = np.stack([focal*right+size[0]/2*forward,
                       -focal*up+size[1]/2*forward, forward])
    homography = matrix@np.column_stack([u,v,center-q[:3]])
    inverse = np.linalg.inv(homography)
    conic = inverse.T@np.diag([1,1,-1])@inverse
    pixels = np.column_stack([observations,np.ones(len(observations))])
    values = np.sum((pixels@conic)*pixels,axis=1)
    gradient = (pixels@(conic+conic.T))[:,:2]
    return values/np.maximum(np.linalg.norm(gradient,axis=1),1e-12)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    paths = [folder/'stills-51/cameras.json',folder/'rear-still-camera-fit.json',
             folder/'nozzle-root-fit.json',folder/'nozzle-mouth-fit.json',
             folder/'exit-profile-study/multiview-exit-fit.json']
    config,landmarks,roll,terminal,tips = [json.loads(f.read_text()) for f in paths]
    root_parameters = roll['parameters']+[math.degrees(math.asin(roll['fixed_axis'][1]))]
    revised = json.loads(json.dumps(config))
    records = []
    for name, pixels in ROOT_POINTS.items():
        pose = next(p for p in config['views'] if p['name']==name)
        known = next(p for p in landmarks if p['view']==name)
        size = pose.get('resolution',config['resolution'])
        world = np.array([known['world_landmarks_mm'][n] for n in known['landmarks']])
        xy = np.array(list(known['landmarks'].values()))
        tip_xy = next(r['reference_px'] for r in tips['observations'] if r['view']==name)
        baseline = np.r_[initial_pose(pose),pose['lens_mm']/pose['sensor_width_mm']*size[0]]
        def residual(q):
            # Both observation classes carry a nominal three-pixel uncertainty.
            return np.r_[(project(world,q[:6],q[6],size)-xy).ravel()/3,
                         ellipse_residual(root_parameters,q,size,pixels)/3]
        fits = []
        for lens in (45,65,88,120):
            start = baseline.copy()
            start[6] = lens/36*size[0]
            fit = least_squares(residual,start,
                bounds=([-4000,-4000,-3000,-360,-70,-30,30/36*size[0]],
                        [4000,4000,3000,360,70,30,160/36*size[0]]),
                x_scale='jac',diff_step=1e-5,max_nfev=1500)
            fits.append(fit)
        best = min(fits,key=lambda f:np.sum(f.fun*f.fun))
        row = {'view':name,'root_reference_px':pixels,'terminal_holdout_px':tip_xy,
               'landmark_reference_px':known['landmarks'],
               'multistarts':[{'lens_mm':float(f.x[6]/size[0]*36),
                              'weighted_rms':float(np.sqrt(np.mean(f.fun*f.fun))),
                              'converged':bool(f.success)} for f in fits]}
        for label,q in [('baseline',baseline),('diagnostic',best.x)]:
            root_curve = circle_pixels(root_parameters,q,size)
            end_curve = circle_pixels(terminal['parameters'],q,size)
            root_distance,root_index = cKDTree(root_curve).query(pixels)
            end_distance,end_index = cKDTree(end_curve).query(tip_xy)
            row[label] = {'parameters':q.tolist(),'lens_mm':float(q[6]/size[0]*36),
                'landmark_coordinate_rms_px':float(np.sqrt(np.mean((project(world,q[:6],q[6],size)-xy)**2))),
                'root_rms_px':float(np.sqrt(np.mean(root_distance**2))),
                'terminal_holdout_rms_px':float(np.sqrt(np.mean(end_distance**2))),
                'root_nearest_px':root_curve[root_index].tolist(),
                'terminal_nearest_px':end_curve[end_index].tolist()}
        new = next(p for p in revised['views'] if p['name']==name)
        outward,_,_ = basis(best.x[:6])
        new.update(eye_mm=best.x[:3].tolist(),target_mm=(best.x[:3]-1000*outward).tolist(),
                   roll_degrees=float(best.x[5]),lens_mm=float(best.x[6]/size[0]*36))
        new['score_interpretation'] = 'diagnostic source-video root registration; terminal held out; not formal'
        records.append(row)
    revised['status'] = 'DIAGNOSTIC ONLY: source-reconstructed root plus existing landmarks; no CAD used in fit'
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'diagnostic-cameras.json').write_text(json.dumps(revised,indent=2)+'\n')
    result = {'status':'diagnostic; formal cameras and CAD unchanged',
              'source_files':[{'path':str(p.relative_to(root)),'sha256':digest(p)} for p in paths],
              'source_images':[{'path':p['source_image'],'sha256':digest(root/p['source_image'])}
                               for p in config['views'] if p['name'] in ROOT_POINTS],
              'script_sha256':digest(Path(__file__)),'root_parameters':root_parameters,
              'terminal_parameters':terminal['parameters'],'views':records,
              'limitations':['Video-derived circles assume symmetry and planarity; manual roll identification remains uncertain.',
                            'Static terminal samples are held out of this fit, but were selected during previous CAD review.',
                            'Nominal three-pixel observation uncertainty is a weighting assumption, not a measured error bar.',
                            'Camera-induced changes must not be reported as geometry improvement.']}
    (a.output/'registration-study.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{key:row[key] for key in ['view','baseline','diagnostic']} for row in records]))


if __name__=='__main__':
    main()
