"""Fit the visible inner rim of the upper side socket in four fixed views.

Arcs hidden by wing or large flange are excluded from edge observations, not
from rendering. Mirrored circular mouths normal to the side plane are assumed.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project

OBSERVATIONS=[
 (60,-1,[[421,345],[416,352],[413,363],[416,376],[423,386],[435,392],[448,390]]),
 (90,-1,[[602,334],[611,339],[618,349],[619,363],[616,379],[607,392],[599,397],[590,389],[585,376],[584,361],[588,347],[594,338]]),
 (150,1,[[341,336],[350,341],[356,351],[357,366],[354,381],[347,392],[338,395],[329,387],[325,374],[325,359],[329,345]]),
 (180,1,[[530,344],[534,354],[536,366],[532,380],[523,391],[511,396]])]


def circle(p,side,count=1440):
    x,y,z,r=p;t=np.linspace(0,2*np.pi,count,endpoint=False)
    return np.column_stack([np.full(count,side*x),y+r*np.cos(t),z+r*np.sin(t)])


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text())
    residual=lambda p:np.concatenate([cKDTree(project(circle(p,s),f,cameras)).query(px)[0] for f,s,px in OBSERVATIONS])
    fit=least_squares(residual,[121,190,202,14],bounds=([100,175,185,10],[140,220,220,20]),diff_step=.0001,max_nfev=200)
    observations=[]
    for f,side,px in OBSERVATIONS:
        pp=project(circle(fit.x,side),f,cameras);dd,ii=cKDTree(pp).query(px)
        observations.append({'source_frame':f,'side':side,'reference_px':px,'fitted_nearest_px':pp[ii].tolist(),'distance_px':dd.tolist()})
    dd=[d for o in observations for d in o['distance_px']]
    result={'parameters':fit.x.tolist(),'parameter_names':['absolute_mouth_x','center_y','center_z','inner_radius'],
        'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(np.array(dd)**2))),'max_distance_px':max(dd),
        'camera_config_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manual dark-rim arcs with wing/flange occlusion; uncertain by several pixels',
            'circular mouths, side-normal axes and mirror symmetry assumed',
            'same arcs fit and check placement; not independent accuracy',
            'body profile, depth and unknown socket function remain appearance assumptions']}
    (folder/'side-socket-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['parameters','distance_rms_px','max_distance_px']}))

if __name__=='__main__':main()
