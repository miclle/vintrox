"""Check fixed-camera rays to the status slot and bracket as well as mark corners."""
import argparse, hashlib, json
from pathlib import Path
import FreeCAD as App
import Part


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ['model','baseline-model','cameras','output']:
        p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args(); cameras=json.loads(args.cameras.read_text())
    results=[]
    for label,path in [('baseline',args.baseline_model),('candidate',args.model)]:
        doc=App.openDocument(str(path)); rows=[]
        try:
            for frame,side in [(150,1),(180,1),(210,1),(60,-1),(90,-1)]:
                suffix='Right' if side>0 else 'Left'
                eye=App.Vector(*next(v for v in cameras['views'] if v['source_frame']==frame)['eye_mm'])
                cladding=[doc.getObject(n+suffix).Shape for n in ['SideClosure','SideMechanicalBacking','SideGuard','RearArmourCheek']]
                cladding.append(doc.getObject('MainEnclosureShell').Shape)
                for prefix in ['SideStatusSlot','SideStatusBracket']:
                    obj=doc.getObject(prefix+suffix); b=obj.Shape.optimalBoundingBox(False,False)
                    # On the rectangular slot's visible rim, not its central hole.
                    offsets=([(-.45,-.45),(-.45,.45),(.45,-.45),(.45,.45),(0,-.45),(0,.45)]
                             if prefix=='SideStatusSlot' else [(-.45,-.45),(-.45,.45),(.45,-.45),(.45,.45)])
                    for dy,dz in offsets:
                        target=App.Vector(b.XMax if side>0 else b.XMin,b.Center.y+dy*b.YLength,b.Center.z+dz*b.ZLength)
                        direction=eye-target;direction.normalize()
                        ray=Part.makeLine(target+direction*.05,target+direction*80)
                        intersections=[{'object':n,'length_mm':s.common(ray).Length} for n,s in zip(
                            ['SideClosure'+suffix,'SideMechanicalBacking'+suffix,'SideGuard'+suffix,'RearArmourCheek'+suffix,'MainEnclosureShell'],cladding)]
                        rows.append({'source_frame':frame,'object':obj.Name,'target_mm':list(target),
                                     'intersections':intersections,'occluded':any(i['length_mm']>1e-6 for i in intersections)})
            results.append({'label':label,'fcstd_sha256':digest(path),'rays':rows,'occluded_count':sum(r['occluded'] for r in rows)})
        finally:App.closeDocument(doc.Name)
    regressions=[{'source_frame':a['source_frame'],'object':a['object'],'target_mm':a['target_mm']}
                 for a,b in zip(results[0]['rays'],results[1]['rays']) if not a['occluded'] and b['occluded']]
    report={'camera_config_sha256':digest(args.cameras),'script_sha256':digest(Path(__file__)),
            'results':results,'new_occlusions':regressions,
            'limitations':['Finite surface samples, not a proof of visibility over the entire feature.',
                           'Existing bracket occlusion is reported separately from candidate regressions.']}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'occluded_counts':[r['occluded_count'] for r in results],'new_occlusions':len(regressions)}))

if __name__=='__main__':main()
