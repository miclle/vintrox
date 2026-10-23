"""Fit a curved coil to visible dark cable centerlines in fixed video views.

Manual observations omit hidden portions. Coil phase/turn count and the smooth
axis are appearance approximations, not electrical or manufactured cable data.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project

OBSERVATIONS={
60:[[399,490],[382,491],[368,496],[371,504],[387,514],[405,525],
    [389,534],[373,543],[370,547],[389,550],[411,558],[424,567],[424,579],
    [412,587],[396,591],[384,586],[389,577],[405,575],[423,582],[433,593],
    [436,606],[429,619],[417,628],[404,627],[400,617],[410,605],[428,598],
    [446,601],[460,611],[466,623],[459,634],[446,640],[437,635],[434,624],
    [445,611],[462,602],[480,597],[497,601],[502,609],[489,619],[477,628],
    [477,637],[493,641],[510,639]],
90:[[581,483],[596,484],[599,490],[591,494],[576,495],[560,499],
    [560,509],[574,518],[591,526],[604,526],[604,530],[589,540],[577,548],
    [586,549],[604,551],[620,559],[628,570],[627,581],[615,588],[602,588],
    [590,581],[589,572],[599,569],[613,573],[628,582],[635,597],[635,610],
    [625,620],[612,622],[601,616],[597,604],[601,592],[613,584],
    [632,585],[650,593],[658,601],[651,610],[640,616],[642,624],[658,625]],
}
HELD_OUT={120:[[704,469],[718,470],[728,473],[726,478],[714,485],
               [704,493],[704,499],[720,501],[735,501],[744,508],[741,515],
               [728,521],[713,518],[710,513],[721,513],[735,522],[748,533],
               [753,545],[750,556],[736,561],[722,555],[716,547],[721,538],
               [736,541],[749,553],[753,570],[747,585],[737,591],[726,585],
               [718,571],[721,560]]}


def coil(parameters,count=1400):
    p=np.asarray(parameters);control=p[:12].reshape(4,3);t=np.linspace(0,1,count)
    weights=np.array([(1-t)**3,3*t*(1-t)**2,3*t*t*(1-t),t**3]).T
    centers=weights@control
    normals=[np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]) for az,el in ((p[17],p[18]),(p[19],p[20]))]
    normal=(1-t)[:,None]*normals[0]+t[:,None]*normals[1];normal/=np.linalg.norm(normal,axis=1)[:,None]
    u=np.tile([1.,0.,0.],(count,1));u-=normal*np.sum(u*normal,axis=1)[:,None];u/=np.linalg.norm(u,axis=1)[:,None]
    v=np.cross(normal,u)
    radius=(1-t)**2*p[12]+2*t*(1-t)*p[13]+t*t*p[14]
    angle=p[15]+t*2*np.pi*p[16]
    return centers+radius[:,None]*(np.cos(angle)[:,None]*u+np.sin(angle)[:,None]*v)


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    path=folder/'cameras.json';cameras=json.loads(path.read_text())
    initial=np.array([-133,182,85,-141,217,89,-126,224,122,-115,217,145,10,12,9,0,5.0,np.pi/2,0,np.pi/2,1.45])
    lo=np.r_[initial[:12]-np.tile([12,15,12],4),5,5,5,-2*np.pi,4.0,-np.pi,-1.5,-np.pi,-1.5]
    hi=np.r_[initial[:12]+np.tile([12,15,12],4),17,19,16,2*np.pi,6.0,np.pi,1.5,np.pi,1.5]
    source_trees={}
    for f,pixels in OBSERVATIONS.items():
        poly=np.array(pixels);samples=np.concatenate([a+(b-a)*np.linspace(0,1,12)[:,None] for a,b in zip(poly[:-1],poly[1:])])
        source_trees[f]=cKDTree(samples)
    def residual(p):
        points=coil(p,900);dd=[]
        for f,px in OBSERVATIONS.items():
            pp=project(points,f,cameras)
            dd.extend(cKDTree(pp).query(px)[0])
            dd.extend(.5*source_trees[f].query(pp[::12])[0])
        return np.r_[dd,.10*(p[:12]-initial[:12])]
    candidates=[]
    for hand in (-1,1):
        bounds_lo=lo.copy();bounds_hi=hi.copy()
        if hand<0:bounds_lo[16]=-6;bounds_hi[16]=-4
        for phase in (-np.pi,-np.pi/2,0,np.pi/2,np.pi):
            guess=initial.copy();guess[15]=phase;guess[16]*=hand
            fit=least_squares(residual,guess,bounds=(bounds_lo,bounds_hi),loss='soft_l1',f_scale=3,diff_step=.0001,max_nfev=600)
            candidates.append(fit)
    fit=min(candidates,key=lambda r:r.cost);groups={}
    for name,source in [('fitted',OBSERVATIONS),('held_out',HELD_OUT)]:
        obs=[];dist=[]
        for frame,px in source.items():
            pp=project(coil(fit.x),frame,cameras);dd,ii=cKDTree(pp).query(px);dist.extend(dd)
            obs.append({'source_frame':frame,'reference_px':px,'fitted_nearest_px':pp[ii].tolist(),'distance_px':dd.tolist()})
        groups[name]={'observations':obs,'distance_rms_px':float(np.sqrt(np.mean(np.array(dist)**2))),'max_distance_px':float(max(dist))}
    d={'parameters':fit.x.tolist(),'parameter_names':['axis_control_xyz_0_to_3','radius_bottom','radius_middle','radius_top','phase_radians','turns','plane_azimuth_bottom','plane_elevation_bottom','plane_azimuth_top','plane_elevation_top'],
       'groups':groups,'tube_radius_mm':1.8,'inferred_terminal_centers_mm':[[-132,155.5,77],[-114.5,200,179]],'matching_method':'symmetric projected centerline distance; fixed cameras and a shared 3D curve','camera_config_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
       'source_video_sha256':cameras['reference_video_sha256'],'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'limitations':['manual dark-wire centers and overlapping loops are ambiguous by several pixels',
                     'smooth cubic axis, progressively tilted coil planes and varying radius are appearance assumptions',
                     'hidden leads and terminal placement are inferred separately',
                     'held-out frame checks visible samples only, not the whole cable contour']}
    (folder/'side-cable-fit.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'parameters':fit.x.tolist(),'groups':{k:{x:v[x] for x in ['distance_rms_px','max_distance_px']} for k,v in groups.items()}},indent=2))


if __name__=='__main__':main()
