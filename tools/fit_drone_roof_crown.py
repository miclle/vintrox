"""Fit rounded crown parameters against visible roof boundary marks.

The longitudinal station family is an appearance assumption. Front lift is
bounded to 3 mm to retain a shallow fitted instrument recess. All observations
participate; this is not independent validation or physical metrology.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull,cKDTree
from fit_drone_lower_pod_outline import project

ROOF_OBSERVATIONS=[(180,[[203,245],[220,232],[241,224],[261,220],[281,216]]),
    (270,[[273,226],[280,219],[290,213],[305,210],[324,208],
          [624,208],[644,210],[658,215],[670,225]])]
STATIONS=[(0,233),(15,235),(30,240.5),(40,247.2),(56.6,259.4),(70,267),
          (85,269),(106,269),(160,269),(178,266),(195,258),(210,250),(220,246)]


def sections(p):
    radius,dz,frontdz=p
    result=[]
    for y,z in STATIONS:
        z+=dz*min(y/85,1,(220-y)/35)+frontdz*np.exp(-((y-45)/30)**2)
        r=min(8+(radius-8)*min(max((y-45)/40,0),1,max((220-y)/30,0)),z-220-.1)
        result.append([y,z,r])
    return result


def cloud(p):
    pts=[]
    for y,z,r in sections(p):
        for side in (-1,1):
            pts.extend([[side*(100.8-r+r*np.cos(a)),y,z-r+r*np.sin(a)] for a in np.linspace(0,np.pi/2,40)])
            pts.append([side*100.8,y,220])
    return np.array(pts)


def projected_boundary(p,frame,cameras):
    pp=project(cloud(p),frame,cameras);hull=pp[ConvexHull(pp).vertices]
    return np.concatenate([a+(b-a)*np.linspace(0,1,150)[:,None] for a,b in zip(hull,np.roll(hull,-1,axis=0))])


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    path=folder/'cameras.json';cameras=json.loads(path.read_text())
    def residual(p):
        return np.concatenate([cKDTree(projected_boundary(p,f,cameras)).query(px)[0] for f,px in ROOF_OBSERVATIONS])
    fit=least_squares(residual,[22,-2,2],bounds=([10,-6,0],[28,2,3]),diff_step=.001,max_nfev=100)
    result={'parameter_names':['crown_radius_mm','crown_height_delta_mm','front_lift_mm'],
        'parameters':fit.x.tolist(),'parameter_bounds':[[10,-6,0],[28,2,3]],
        'front_lift_bound_active':bool(fit.x[2]>2.99),'section_y_top_radius_mm':sections(fit.x),
        'observations':[{'source_frame':f,'reference_px':px} for f,px in ROOF_OBSERVATIONS],
        'proxy_distance_rms_px':float(np.sqrt(np.mean(residual(fit.x)**2))),
        'proxy_max_distance_px':float(max(residual(fit.x))),
        'camera_config_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['longitudinal station family and fixed 201.6 mm width assumed',
            'front lift constrained to preserve shallow instrument recess',
            'proxy samples section contours; actual saved loft is checked separately',
            'same manual points used for fitting; visible partial boundaries only']}
    (folder/'roof-crown-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['parameters']));print(result['proxy_distance_rms_px'])

if __name__=='__main__':main()
