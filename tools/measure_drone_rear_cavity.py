"""Read the real rear-cavity voids, wall material and unchanged support shafts.

These local probes distinguish an actual recess from a dark surface painted on
solid cladding. They are not manufacturing clearances or full cavity coverage.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--baseline-model',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=root/'cad/drone-concept/comparison/rear-cavity-check.json')
    args=parser.parse_args()
    current=App.openDocument(str(args.model));baseline=App.openDocument(str(args.baseline_model))
    parts=[]
    names=['RearServicePanel','RearRecessLiner','RearCyanFrame','RearLowerSlope']
    for name in names:
        shape=current.getObject(name).Shape;shape.check(True)
        parts.append({'name':name,'valid':shape.isValid(),'solids':len(shape.Solids),
                      'closed':all(s.isClosed() for s in shape.Solids)})
    shafts=[]
    for obj in baseline.Objects:
        if obj.Name.startswith('SupportShaft'):
            before=obj.Shape;after=current.getObject(obj.Name).Shape
            shafts.append({'name':obj.Name,'symmetric_difference_mm3':
                           before.cut(after).Volume+after.cut(before).Volume})
    voids=[]
    for x,z in [(-65,170),(65,170),(-65,90),(65,90),(-65,126),(65,126)]:
        point=App.Vector(x,226 if z==126 else 235+min(0,z-134)*.98,z)
        probe=Part.makeSphere(.6,point)
        voids.append({'point_mm':list(point),'probe_radius_mm':.6,
            'baseline_overlap_mm3':sum(probe.common(baseline.getObject(n).Shape).Volume for n in names),
            'current_overlap_mm3':sum(probe.common(current.getObject(n).Shape).Volume for n in names)})
    # The v35 opening is 138mm wide: probe the retained 2mm walls at |X|=70.
    walls=[]
    liner=current.getObject('RearRecessLiner').Shape
    for x,z in [(-70,170),(70,170),(-70,95),(70,95)]:
        point=App.Vector(x,232+min(0,z-134)*.98,z);probe=Part.makeSphere(.4,point)
        walls.append({'point_mm':list(point),'probe_radius_mm':.4,'liner_overlap_mm3':probe.common(liner).Volume})
    contacts=[]
    for name in ['RearCyanFrame','RearServicePanel','RearLowerSlope']:
        shape=current.getObject(name).Shape
        contacts.append({'objects':[name,'RearRecessLiner'],'gap_mm':shape.distToShape(liner)[0],
                         'overlap_mm3':shape.common(liner).Volume})
    result={'fcstd_sha256':digest(args.model),'baseline_fcstd_sha256':digest(args.baseline_model),
            'measurement_script_sha256':digest(Path(__file__)),'parts':parts,'shafts':shafts,
            'void_probes':voids,'wall_probes':walls,'contacts':contacts,
            'limitations':['six void and four material probes only',
                'does not classify reference shadows as physical nozzle boundaries',
                'appearance geometry, not fabrication or load validation']}
    result['passed']=(all(p['valid'] and p['closed'] and p['solids']==1 for p in parts)
        and len(shafts)==4 and all(p['symmetric_difference_mm3']<1e-6 for p in shafts)
        and all(p['current_overlap_mm3']<1e-6 for p in voids)
        and all(p['liner_overlap_mm3']>.01 for p in walls)
        and all(c['gap_mm']<.01 and c['overlap_mm3']>.001 for c in contacts))
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    App.closeDocument(current.Name);App.closeDocument(baseline.Name)
    print(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
