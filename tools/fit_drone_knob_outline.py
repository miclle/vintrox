"""Fit the first control knob cap to three fixed-view visible outlines.

Manual dark edges carry several pixels of uncertainty. A circular cap and a
shared axis in the YZ plane are assumptions, not measured source dimensions.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project

OBSERVATIONS=[
 (270,[[548,708],[556,710],[562,716],[563,724],[557,731],[548,734],[539,731],[535,724],[536,716],[541,710]]),
 (0,[[729,680],[735,684],[737,692],[732,700],[724,704],[719,699],[718,691],[722,684]]),
 (240,[[324,704],[332,707],[338,714],[338,723],[331,729],[323,726],[317,720],[316,712],[319,707]])]


def circle(p,count=1440):
    x,y,z,r,nz=p;normal=np.array([0.,-1.,nz]);normal/=np.linalg.norm(normal)
    u=np.array([1.,0.,0.]);v=np.cross(normal,u)
    t=np.linspace(0,2*np.pi,count,endpoint=False)
    return np.array([x,y,z])+r*(np.cos(t)[:,None]*u+np.sin(t)[:,None]*v),normal


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text())
    def residual(p):
        points,_=circle(p)
        return np.concatenate([cKDTree(project(points,f,cameras)).query(px)[0] for f,px in OBSERVATIONS])
    fit=least_squares(residual,[34,-19,45,6.3,0],bounds=([25,-35,35,4,-.7],[45,-10,55,9,.7]),diff_step=.0001,max_nfev=200)
    points,axis=circle(fit.x);observations=[]
    for frame,px in OBSERVATIONS:
        pp=project(points,frame,cameras);dd,ii=cKDTree(pp).query(px)
        observations.append({'source_frame':frame,'reference_px':px,'fitted_nearest_px':pp[ii].tolist(),'distance_px':dd.tolist()})
    result={'parameters':fit.x.tolist(),'parameter_names':['cap_x','cap_y','cap_z','cap_radius','axis_z_over_minus_y'],
        'axis':axis.tolist(),'distance_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
        'max_distance_px':float(max(residual(fit.x))),'observations':observations,
        'camera_config_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manually read dark cap edges; several pixels of uncertainty',
            'circular cap and shared YZ-plane axis assumed',
            'same observations fit and check geometry; not independent accuracy',
            'other two knobs reuse radius and axis; appearance only, not manufacturing dimensions']}
    (folder/'knob-outline-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['parameters','axis','distance_rms_px','max_distance_px']}))

if __name__=='__main__':main()
