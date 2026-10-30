"""Diagnose the fixed 88mm still-lens assumption using existing source landmarks.

No CAD vertices, nozzle pixels or silhouette scores participate in this fit.
The generated camera set is diagnostic; it does not replace the formal cameras.
"""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def basis(q):
    az,el,roll=np.radians(q[3:6]);toward=np.array([np.cos(az)*np.cos(el),np.sin(az)*np.cos(el),np.sin(el)])
    right=np.array([-np.sin(az),np.cos(az),0]);up=np.cross(toward,right)
    return toward,np.cos(roll)*right+np.sin(roll)*up,-np.sin(roll)*right+np.cos(roll)*up


def project(world,q,focal,size):
    toward,right,up=basis(q);d=world-q[:3];depth=-(d@toward)
    return np.stack([size[0]/2+focal*(d@right)/depth,size[1]/2-focal*(d@up)/depth],axis=1)


def main():
    p=argparse.ArgumentParser()
    for name in ['cameras','landmarks','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();config=json.loads(a.cameras.read_text());records=json.loads(a.landmarks.read_text());starts=[];data=[]
    for record in records:
        pose=next(v for v in config['views'] if v['name']==record['view'])
        direction=np.array(pose['eye_mm'])-pose['target_mm'];direction/=np.linalg.norm(direction)
        starts.append(pose['eye_mm']+[math.degrees(math.atan2(direction[1],direction[0])),math.degrees(math.asin(direction[2])),pose.get('roll_degrees',0)])
        data.append((np.array([record['world_landmarks_mm'][n] for n in record['landmarks']]),np.array(list(record['landmarks'].values())),pose.get('resolution',config['resolution'])))
    def residual(q, observations=None):
        return np.concatenate([(project(world,q[i*6:i*6+6],q[-1],size)-(observations[i] if observations is not None else xy)).ravel() for i,(world,xy,size) in enumerate(data)])
    lower=[-4000,-4000,-3000,-360,-70,-30]*len(data)+[600]
    upper=[4000,4000,3000,360,70,30]*len(data)+[5000]
    fits=[]
    for focal in [900,1500,2346.6666667,3500]:
        start=np.r_[np.array(starts).ravel(),focal]
        fit=least_squares(residual,start,bounds=(lower,upper),max_nfev=1500,x_scale='jac',diff_step=1e-5)
        fits.append(fit)
    best=min(fits,key=lambda f:np.sum(f.fun**2));new=json.loads(json.dumps(config));rows=[]
    for i,record in enumerate(records):
        pose=next(p for p in new['views'] if p['name']==record['view']);q=best.x[i*6:i*6+6];toward,_,_=basis(q)
        pose.update(eye_mm=q[:3].tolist(),target_mm=(q[:3]-toward*1000).tolist(),lens_mm=float(best.x[-1]*36/data[i][2][0]),roll_degrees=float(q[5]))
        pose['score_interpretation']='diagnostic shared focal fit to existing source landmarks; nozzle not fitted'
        predicted=project(data[i][0],q,best.x[-1],data[i][2]);baseline=project(data[i][0],np.array(starts[i]),2346.6666667,data[i][2])
        rows.append({'view':record['view'],'source_landmarks':record['landmarks'],'baseline_coordinate_rms_px':float(np.sqrt(np.mean((baseline-data[i][1])**2))),'coordinate_rms_px':float(np.sqrt(np.mean((predicted-data[i][1])**2))),'predicted_px':predicted.tolist(),'parameters':q.tolist()})
    # Deterministic sensitivity to two-pixel manual observation uncertainty.
    rng=np.random.default_rng(46);samples=[]
    for trial in range(24):
        obs=[xy+rng.normal(0,2,xy.shape) for _,xy,_ in data]
        fit=least_squares(lambda q:residual(q,obs),best.x,bounds=(lower,upper),max_nfev=300,x_scale='jac',diff_step=1e-5)
        samples.append(float(fit.x[-1]*36/960))
    new['status']='DIAGNOSTIC ONLY: shared free focal from existing source landmarks; formal cameras unchanged'
    a.output.mkdir(parents=True,exist_ok=True);(a.output/'diagnostic-cameras.json').write_text(json.dumps(new,indent=2)+'\n')
    result={'source_camera_sha256':digest(a.cameras),'landmark_source_sha256':digest(a.landmarks),'script_sha256':digest(Path(__file__)),
            'focal_pixels':float(best.x[-1]),'lens_mm':float(best.x[-1]*36/960),'coordinate_rms_px':float(np.sqrt(np.mean(best.fun**2))),
            'multi_start_results':[{'start_focal_px':v,'fitted_focal_px':float(f.x[-1]),'coordinate_rms_px':float(np.sqrt(np.mean(f.fun**2))),'converged':bool(f.success)} for v,f in zip([900,1500,2346.6666667,3500],fits)],
            'observations':rows,'two_pixel_sensitivity_lens_mm':samples,'sensitivity_range_mm':[min(samples),max(samples)],
            'limitations':['Only twelve sparse source landmarks across three views; shared lens is an assumption.','Two-pixel sensitivity samples are not a statistical confidence interval.','No formal camera or model changed; lower silhouette remains held out.']}
    (a.output/'focal-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['lens_mm','coordinate_rms_px','sensitivity_range_mm']}))


if __name__=='__main__':main()
