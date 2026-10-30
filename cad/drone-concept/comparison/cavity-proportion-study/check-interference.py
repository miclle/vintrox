import FreeCAD as App
from pathlib import Path
import json,hashlib
root=Path('cad/drone-concept/comparison/cavity-proportion-study')
paths=[('baseline',Path('cad/drone-concept/vintrox-drone-concept.FCStd'))]+[(v,root/v/'candidate.FCStd') for v in 'abcde']
results=[]
for variant,p in paths:
 d=App.openDocument(str(p));shell=d.getObject('BassNozzleShell').Shape;rows=[]
 for name in ['RearRecessLiner','RearCyanFrame','RearServicePanel','RearLowerSlope']:
  s=d.getObject(name).Shape
  rows.append({'name':name,'shell_overlap_mm3':s.common(shell).Volume,'solids':len(s.Solids)})
 results.append({'variant':variant,'fcstd_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'parts':rows})
 App.closeDocument(d.Name)
 print(variant,rows[1],flush=True)
(root/'interference-check.json').write_text(json.dumps({'method':'saved BRep common volume between each named cavity part and BassNozzleShell','results':results,'limitations':['includes hidden intersections; volume alone does not identify a visible artifact','appearance candidates; not assembly clearance acceptance']},indent=2)+'\n')
