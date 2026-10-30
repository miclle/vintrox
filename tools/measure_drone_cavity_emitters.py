"""Read back the split emitters, curved rails and reflector/clamp contacts."""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App


def main():
    root=Path(__file__).resolve().parents[1];cad=root/'cad/drone-concept'
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,default=cad/'vintrox-drone-concept.FCStd')
    p.add_argument('--output',type=Path,default=cad/'comparison/cavity-emitter-check.json');args=p.parse_args()
    d=App.openDocument(str(args.model))
    try:
        names=['RearCyanFrame','RearCyanUpperLeft','RearCyanLowerLeft','RearCyanLowerRight']
        names += [prefix+side for side in ['Left','Right'] for prefix in ['RearCavityEmitter','RearCavityReflector','RearCavityClipUpper','RearCavityClipLower']]
        shell=d.getObject('BassNozzleShell').Shape;parts=[];contacts=[]
        for name in names:
            s=d.getObject(name).Shape;s.check(True)
            parts.append({'name':name,'valid':s.isValid(),'closed':all(x.isClosed() for x in s.Solids),
                          'solids':len(s.Solids),'nozzle_shell_overlap_mm3':s.common(shell).Volume})
        pairs=[(n,'RearRecessLiner') for n in names[:4]]
        for side in ['Left','Right']:
            pairs.append(('RearCavityReflector'+side,'RearRecessLiner'))
            for end in ['Upper','Lower']:
                pairs.extend([('RearCavityEmitter'+side,'RearCavityClip'+end+side),
                              ('RearCavityClip'+end+side,'RearCavityReflector'+side)])
        for left,right in pairs:
            a=d.getObject(left).Shape;b=d.getObject(right).Shape
            contacts.append({'objects':[left,right],'gap_mm':a.distToShape(b)[0],'overlap_mm3':a.common(b).Volume})
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
                'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parts':parts,'contacts':contacts,
                'limitations':['only these twelve lighting parts checked against nozzle shell','legacy panel/liner/slope hidden intersections are outside this check','appearance contacts, not fastening or manufacturing clearances']}
        result['passed']=(len(parts)==12 and all(x['valid'] and x['closed'] and x['solids']==1 and x['nozzle_shell_overlap_mm3']<1e-6 for x in parts)
                          and len(contacts)==14 and all(x['gap_mm']<.01 and x['overlap_mm3']>.001 for x in contacts))
        args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
        if not result['passed']:raise SystemExit(1)
    finally:App.closeDocument(d.Name)


if __name__=='__main__':main()
