"""Read fitted side marks, held-out opposite views and recessed panel continuity."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
import numpy as np
from fit_drone_lower_pod_outline import project


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    p.add_argument('--output',type=Path,default=folder/'side-status-check.json');args=p.parse_args()
    fit_path=folder/'side-status-fit.json';fit=json.loads(fit_path.read_text())
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text());doc=App.openDocument(str(args.model))
    try:
        shape=lambda name:doc.getObject(name).Shape
        points={};joints={};probes=[]
        for side,suffix in [(-1,'Left'),(1,'Right')]:
            points[side]=[];plate=shape('SideStatusPlate'+suffix)
            for i in range(3):
                mark=shape(f'SideStatusMark{suffix}{i}');b=mark.optimalBoundingBox(False,False)
                points[side].append([b.XMax if side>0 else b.XMin,b.Center.y,b.Center.z])
            names=[f'SideStatusMark{suffix}{i}' for i in range(3)]
            names += [name+suffix for name in ['SideStatusBracket','SideStatusSlot'] if doc.getObject(name+suffix)]
            joints[suffix]={'plate_shell_overlap_mm3':plate.common(shape('MainEnclosureShell')).Volume,
                'detail_plate_gaps_mm':{name:shape(name).distToShape(plate)[0] for name in names},
                'plate_solids':len(plate.Solids)}
            cladding=Part.makeCompound([shape('MainEnclosureShell'),shape('SideClosure'+suffix),shape('SideMechanicalBacking'+suffix)])
            for x,y,z in points[side]:
                probes.append({'side':side,'mark_center_mm':[x,y,z],
                    'recess_probe_overlap_mm3':plate.common(Part.makeSphere(.12,App.Vector(x-side*.5,y,z))).Volume,
                    'backing_probe_overlap_mm3':plate.common(Part.makeSphere(.12,App.Vector(x-side*1.1,y,z))).Volume,
                    'outward_occlusion_overlap_mm3':[cladding.common(Part.makeSphere(.12,App.Vector(side*d,y,z))).Volume for d in [99,105,114]]})
        groups={}
        for name,source in [('fitted',fit['observations']),('held_out',fit['held_out_observations'])]:
            observations=[]
            for o in source:
                pp=project(np.array(points[o['side']]),o['source_frame'],cameras);dd=np.linalg.norm(pp-o['reference_px'],axis=1)
                observations.append({'source_frame':o['source_frame'],'side':o['side'],'reference_px':o['reference_px'],
                    'saved_px':pp.tolist(),'distance_px':dd.tolist()})
            dd=[d for o in observations for d in o['distance_px']]
            groups[name]={'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(np.array(dd)**2))),'max_distance_px':max(dd)}
        visibility=[]
        for o in fit['observations']+fit['held_out_observations']:
            side=o['side'];suffix='Right' if side>0 else 'Left'
            eye=App.Vector(*next(v for v in cameras['views'] if v['source_frame']==o['source_frame'])['eye_mm'])
            cladding=[shape('MainEnclosureShell'),shape('SideClosure'+suffix),
                      shape('SideMechanicalBacking'+suffix),shape('SideGuard'+suffix),shape('RearArmourCheek'+suffix)]
            rays=[]
            for i,(x,y,z) in enumerate(points[side]):
                b=shape(f'SideStatusMark{suffix}{i}').optimalBoundingBox(False,False)
                for dy,dz in [(0,0),(-.45,-.45),(-.45,.45),(.45,-.45),(.45,.45)]:
                    target=App.Vector(x,y+dy*b.YLength,z+dz*b.ZLength)
                    direction=eye-target;direction.normalize()
                    ray=Part.makeLine(target+direction*.05,target+direction*80)
                    rays.append({'mark_index':i,'target_mm':list(target),
                                 'cladding_intersection_length_mm':sum(part.common(ray).Length for part in cladding)})
            visibility.append({'source_frame':o['source_frame'],'side':side,'rays':rays})
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'saved_mark_centers_mm':points,'groups':groups,'saved_joints':joints,'cavity_probes':probes,'view_visibility':visibility,
            'visibility_method':'individual cladding BRep intersections; sum is diagnostic and may double-count overlaps',
            'limitations':fit['limitations']+['local cavity/backing probes do not prove sealing or physical assembly']}
        args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:{n:v[n] for n in ['distance_rms_px','max_distance_px']} for k,v in groups.items()}));print(json.dumps(joints))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
