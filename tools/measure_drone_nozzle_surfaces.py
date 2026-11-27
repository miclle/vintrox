"""Read saved nozzle surfaces, patch exposure and local interface contacts.

These are appearance checks; no manufacturing or physical acceptance is implied.
"""
import argparse
from pathlib import Path
import json,hashlib
import FreeCAD as App
import Part
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
parser.add_argument('--output',type=Path,default=root/'cad/drone-concept/comparison/nozzle-surface-check.json')
parser.add_argument('--fitted-markings',action='store_true',help='Use the three-view fitted warning-mask interior probes')
args=parser.parse_args();p=args.model;d=App.openDocument(str(p))
shell=d.getObject('BassNozzleShell').Shape
parts=['BassNozzleShell','BassWarningPlaque','BassWarningRedBand','BassWarningTriangle','BassWarningTriangleInset']
checks=[]
for name in parts:
 s=d.getObject(name).Shape;s.check(True);checks.append({'name':name,'valid':s.isValid(),'solids':len(s.Solids),'closed':all(x.isClosed() for x in s.Solids),'volume_mm3':s.Volume})
contacts=[]
for a,b in [('BassWarningPlaque','BassNozzleShell'),('BassWarningTriangle','BassNozzleShell'),('BassWarningRedBand','BassWarningPlaque'),('BassWarningTriangleInset','BassWarningTriangle'),('BassNozzleRolledLip','BassNozzleShell'),('BassNozzleRearCollar','BassNozzleShell')]:
 s,t=d.getObject(a).Shape,d.getObject(b).Shape;contacts.append({'objects':[a,b],'gap_mm':s.distToShape(t)[0],'overlap_mm3':s.common(t).Volume})
axis=App.Vector(0,.574,-.819);axis.normalize();place=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
local={}
for name in parts:
 s=d.getObject(name).Shape.copy();s.Placement=place.inverse().multiply(s.Placement);local[name]=s
probes=[]
probe_layout=[('BassWarningPlaque',[(-15,68),(0,68),(12,68),(-15,77),(0,77),(12,77)]),('BassWarningTriangle',[(-10,50),(10,50),(0,30)]),('BassWarningTriangleInset',[(-5,45),(5,45),(0,35)]),('BassWarningRedBand',[(18,69),(18,73),(18,78)])]
if args.fitted_markings:
 from drone_nozzle_markings import marking_probe_points
 probe_layout=marking_probe_points()
for name,points in probe_layout:
 for x,z in points:
  line=Part.makeLine(App.Vector(x,-120,z),App.Vector(x,0,z))
  body=local['BassNozzleShell'].common(line);tag=local[name].common(line)
  by=min(v.Point.y for v in body.Vertexes);ty=min(v.Point.y for v in tag.Vertexes)
  probes.append({'part':name,'local_xz_mm':[x,z],'forward_exposure_mm':by-ty})
result={'fcstd_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'parts':checks,'contacts':contacts,'surface_probes':probes,'woofer_shell_overlap_mm3':shell.common(d.getObject('WooferEnvelope_D88_Depth40').Shape).Volume,'limitations':['local appearance contacts only; no print interface or physical test','text remains flat render annotation outside curved patches']}
result['measurement_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result['passed']=all(x['valid'] and x['closed'] and x['solids']==1 for x in checks) and all(c['gap_mm']<.01 for c in contacts) and all(q['forward_exposure_mm']>.1 for q in probes) and result['woofer_shell_overlap_mm3']<1e-6
args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));App.closeDocument(d.Name)

if not result['passed']:raise SystemExit(1)
