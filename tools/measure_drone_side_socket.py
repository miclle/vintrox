"""Read saved upper socket rims, backing contacts and cladding visibility."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
import numpy as np
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    p.add_argument('--output',type=Path,default=folder/'side-socket-check.json');args=p.parse_args()
    fit_path=folder/'side-socket-fit.json';fit=json.loads(fit_path.read_text())
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text());doc=App.openDocument(str(args.model))
    try:
        shape=lambda name:doc.getObject(name).Shape
        circles={};joints={}
        for side,suffix in [(-1,'Left'),(1,'Right')]:
            lip=shape('SideSocketLip'+suffix)
            faces=[f for f in lip.Faces if type(f.Surface).__name__=='Plane']
            face=max(faces,key=lambda f:side*f.CenterOfMass.x)
            edges=[e for e in face.Edges if type(e.Curve).__name__=='Circle']
            edge=min(edges,key=lambda e:e.Curve.Radius)
            circles[side]={'center_mm':list(edge.Curve.Center),'radius_mm':edge.Curve.Radius,
                'points':np.array([list(p) for p in edge.discretize(Number=1440)])}
            body=shape('SideSocketBase'+suffix);back=shape('SideSocketRecess'+suffix)
            center=App.Vector(*circles[side]['center_mm'])
            ray=Part.makeLine(center-App.Vector(side*.05,0,0),center-App.Vector(side*12,0,0))
            joints[suffix]={'lip_body_gap_mm':lip.distToShape(body)[0],
                'lip_body_overlap_mm3':lip.common(body).Volume,
                'body_back_gap_mm':body.distToShape(back)[0],
                'body_back_overlap_mm3':body.common(back).Volume,
                'back_shell_overlap_mm3':back.common(shape('MainEnclosureShell')).Volume,
                'mouth_cavity_body_intersection_mm':body.common(ray).Length,
                'body_solids':len(body.Solids),'back_solids':len(back.Solids)}
        observations=[];visibility=[]
        for o in fit['observations']:
            side=o['side'];suffix='Right' if side>0 else 'Left';points=circles[side]['points']
            pp=project(points,o['source_frame'],cameras);dd,ii=cKDTree(pp).query(o['reference_px'])
            observations.append({'source_frame':o['source_frame'],'side':side,'reference_px':o['reference_px'],
                'saved_nearest_px':pp[ii].tolist(),'distance_px':dd.tolist()})
            eye=App.Vector(*next(v for v in cameras['views'] if v['source_frame']==o['source_frame'])['eye_mm'])
            cladding=[shape('MainEnclosureShell'),shape('SideClosure'+suffix),shape('SideMechanicalBacking'+suffix),shape('SideGuard'+suffix),shape('RearArmourCheek'+suffix)]
            rays=[]
            for index in ii:
                target=App.Vector(*points[index]);direction=eye-target;direction.normalize()
                ray=Part.makeLine(target+direction*.05,target+direction*80)
                rays.append({'target_mm':list(target),'cladding_intersection_length_mm':sum(s.common(ray).Length for s in cladding)})
            visibility.append({'source_frame':o['source_frame'],'side':side,'rays':rays})
        dd=[d for o in observations for d in o['distance_px']]
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'saved_circles':{str(side):{k:v for k,v in c.items() if k!='points'} for side,c in circles.items()},
            'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(np.array(dd)**2))),'max_distance_px':max(dd),
            'saved_joints':joints,'view_visibility':visibility,
            'limitations':fit['limitations']+['visibility rays test cladding only; wing/flange occlusion is reviewed in images']}
        args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['distance_rms_px','max_distance_px','saved_joints']}))
        print('maximum cladding intersection',max(r['cladding_intersection_length_mm'] for v in visibility for r in v['rays']))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
