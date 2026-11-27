"""Joint source-only root reconstruction and still camera diagnostic.

The root is constrained by three original video views and two still photos.
Still wing/hub/beacon observations constrain poses; the terminal is held out.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from study_drone_source_registration import (ROOT_POINTS, initial_pose, basis,
                                             project, ellipse_residual, circle_pixels)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    b=root/'cad/drone-concept/comparison'
    paths=[b/'cameras.json',b/'stills-51/cameras.json',b/'rear-still-camera-fit.json',
           b/'nozzle-root-fit.json',b/'nozzle-mouth-fit.json',
           b/'exit-profile-study/multiview-exit-fit.json']
    video,still,landmarks,roll,terminal,tips=[json.loads(p.read_text()) for p in paths]
    root0=np.r_[roll['parameters'],math.degrees(math.asin(roll['fixed_axis'][1]))]
    static=[]
    for name,xy in ROOT_POINTS.items():
        pose=next(p for p in still['views'] if p['name']==name)
        known=next(r for r in landmarks if r['view']==name)
        static.append({'name':name,'root_xy':xy,'pose':pose,
                       'world':np.array([known['world_landmarks_mm'][n] for n in known['landmarks']]),
                       'land_xy':np.array(list(known['landmarks'].values())),
                       'tip_xy':next(r['reference_px'] for r in tips['observations'] if r['view']==name),
                       'size':pose.get('resolution',still['resolution'])})
    moving=[]
    for record in roll['observations']:
        pose=next(p for p in video['views'] if p['source_frame']==record['source_frame'])
        size=pose.get('resolution',video['resolution'])
        moving.append((record,np.r_[initial_pose(pose),pose['lens_mm']/pose['sensor_width_mm']*size[0]],size))
    start=np.r_[root0,*[initial_pose(d['pose']) for d in static],88/36*960]
    def camera(q,index):
        return np.r_[q[4+6*index:10+6*index],q[-1]]
    def residual(q):
        rows=[ellipse_residual(q[:4],cam,size,record['reference_px'])/3
              for record,cam,size in moving]
        for i,d in enumerate(static):
            cam=camera(q,i)
            rows.extend([(project(d['world'],cam[:6],cam[6],d['size'])-d['land_xy']).ravel()/3,
                         ellipse_residual(q[:4],cam,d['size'],d['root_xy'])/3])
        return np.concatenate(rows)
    lower=[200,50,35,15]+[-4000,-4000,-3000,-360,-70,-30]*2+[40/36*960]
    upper=[275,150,80,65]+[4000,4000,3000,360,70,30]*2+[140/36*960]
    fits=[]
    for beta,lens in [(25,65),(35,88),(45,110),(35,65),(35,110)]:
        q=start.copy();q[3]=beta;q[-1]=lens/36*960
        fits.append(least_squares(residual,q,bounds=(lower,upper),x_scale='jac',
                                  diff_step=1e-5,max_nfev=2500))
    fit=min(fits,key=lambda f:sum(f.fun*f.fun));new=json.loads(json.dumps(still));records=[]
    for i,d in enumerate(static):
        q=camera(fit.x,i);pose=next(p for p in new['views'] if p['name']==d['name'])
        outward,_,_=basis(q[:6]);pose.update(eye_mm=q[:3].tolist(),target_mm=(q[:3]-1000*outward).tolist(),
                         lens_mm=float(q[6]/960*36),roll_degrees=float(q[5]))
        pose['score_interpretation']='diagnostic joint source root reconstruction; terminal held out'
        root_curve=circle_pixels(fit.x[:4],q,d['size']);tip_curve=circle_pixels(terminal['parameters'],q,d['size'])
        rd,_=cKDTree(root_curve).query(d['root_xy']);td,_=cKDTree(tip_curve).query(d['tip_xy'])
        records.append({'view':d['name'],'root_rms_px':float(np.sqrt(np.mean(rd*rd))),
                        'landmark_coordinate_rms_px':float(np.sqrt(np.mean((project(d['world'],q[:6],q[6],d['size'])-d['land_xy'])**2))),
                        'terminal_holdout_rms_px':float(np.sqrt(np.mean(td*td)))})
    for record,cam,size in moving:
        dist,_=cKDTree(circle_pixels(fit.x[:4],cam,size)).query(record['reference_px'])
        records.append({'source_frame':record['source_frame'],'root_rms_px':float(np.sqrt(np.mean(dist*dist)))})
    new['status']='DIAGNOSTIC ONLY: joint source root and still-camera fit; formal cameras unchanged'
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'diagnostic-cameras.json').write_text(json.dumps(new,indent=2)+'\n')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    result={'status':'source-only diagnostic; no formal model or camera changed','baseline_root_parameters':root0.tolist(),
            'joint_root_parameters':fit.x[:4].tolist(),'shared_lens_mm':float(fit.x[-1]/960*36),
            'views':records,'multistarts':[{'weighted_rms':float(np.sqrt(np.mean(f.fun*f.fun))),
                                         'root':f.x[:4].tolist(),'lens_mm':float(f.x[-1]/960*36),'converged':bool(f.success)} for f in fits],
            'source_files':[{'path':str(p.relative_to(root)),'sha256':digest(p)} for p in paths],
            'script_sha256':digest(Path(__file__)),
            'helper_sha256':digest(Path(__file__).with_name('study_drone_source_registration.py')),
            'limitations':['Shared still focal length and circular root are assumptions.',
                          'All root points are reused fitting observations; terminal pixels are held out of this fit only.',
                          'Sparse manual correspondence uncertainty remains; no CAD geometry participates.']}
    (a.output/'joint-root-study.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
