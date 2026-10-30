"""Independently refit the five-video root observations with fixed source cameras and no CAD inputs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from study_drone_source_registration import initial_pose, circle_pixels


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    b=root/'cad/drone-concept/comparison';study=b/'source-registration-study'
    paths=[b/'cameras.json',b/'nozzle-root-fit.json',study/'root-holdout.json']
    camera,old,extra=[json.loads(path.read_text()) for path in paths]
    initial=np.r_[old['parameters'],math.degrees(math.asin(old['fixed_axis'][1]))]
    observations=old['observations']+extra['views'];rows=[]
    for obs in observations:
        pose=next(v for v in camera['views'] if v['source_frame']==obs['source_frame'])
        size=pose.get('resolution',camera['resolution'])
        q=np.r_[initial_pose(pose),pose['lens_mm']/pose['sensor_width_mm']*size[0]]
        rows.append((obs,q,size))
    def fit(selected):
        def residual(x):
            return np.concatenate([cKDTree(circle_pixels(x,q,size)).query(obs['reference_px'])[0]
                                   for obs,q,size in selected])
        starts=[initial, np.array([225,90,54,35]), np.array([235,90,54,30])]
        trials=[least_squares(residual,start,bounds=([200,50,35,15],[275,150,80,65]),
                             x_scale='jac',diff_step=1e-5,max_nfev=2500) for start in starts]
        return min(trials,key=lambda item:sum(item.fun*item.fun))
    fitted=fit(rows);result=[];all_old=[];all_new=[]
    for obs,q,size in rows:
        values={}
        for key,x,collector in [('baseline',initial,all_old),('fitted',fitted.x,all_new)]:
            dist,index=cKDTree(circle_pixels(x,q,size)).query(obs['reference_px'])
            collector.extend(dist.tolist())
            values[key]={'rms_px':float(np.sqrt(np.mean(dist*dist))),'max_px':float(max(dist))}
        result.append({'source_frame':obs['source_frame'],'reference_px':obs['reference_px'],**values})
    loo=[]
    for i,(obs,q,size) in enumerate(rows):
        candidate=fit(rows[:i]+rows[i+1:])
        dist,_=cKDTree(circle_pixels(candidate.x,q,size)).query(obs['reference_px'])
        loo.append({'held_out_frame':obs['source_frame'],'parameters':candidate.x.tolist(),
                    'held_out_rms_px':float(np.sqrt(np.mean(dist*dist)))})
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    report={'parameters':fitted.x.tolist(),'baseline_parameters':initial.tolist(),'views':result,
            'baseline_rms_px':float(np.sqrt(np.mean(np.square(all_old)))),
            'fit_rms_px':float(np.sqrt(np.mean(np.square(all_new)))),
            'leave_one_view_out':loo,'script_sha256':sha(Path(__file__)),
            'helper_sha256':sha(Path(__file__).with_name('study_drone_source_registration.py')),
            'source_files':[{'path':str(path.relative_to(root)),'sha256':sha(path)} for path in paths],
            'limitations':['Circular root and manual centreline observations are appearance assumptions.',
                          'The two added views are no longer held out of the five-view fit.',
                          'Residuals reuse fitting points; leave-one-view-out does not prove unique reconstruction.']}
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['parameters','baseline_rms_px','fit_rms_px']}))


if __name__=='__main__':main()
