"""Build isolated nozzle-fairing geometry experiments from a saved baseline.

Candidate FCStd files are geometry-only (no GUI state or STEP delivery). They do
not replace the formal appearance model. Mesh materials come from the hash-bound
baseline export. Review decals and all interfaces before adopting a candidate.
"""
import argparse
import sys,json,hashlib,math
from pathlib import Path
import FreeCAD as App
import Part
sys.path.insert(0,str(Path(__file__).resolve().parent))
from drone_concept import sector_wire, profile, rounded_plate
parser=argparse.ArgumentParser()
parser.add_argument('--base-model',type=Path,required=True)
parser.add_argument('--base-meshes',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--variant',choices=('a','b','c','d','e','f','g','h','i'),required=True)
args=parser.parse_args()
out=args.output
if out.exists() and any(out.iterdir()):raise ValueError('Use a new candidate directory')
out.mkdir(parents=True,exist_ok=True)
mesh=json.loads(args.base_meshes.read_text())
base_hash=hashlib.sha256(args.base_model.read_bytes()).hexdigest()
if mesh['fcstd_sha256']!=base_hash:raise ValueError('Baseline model/mesh hash mismatch')
doc=App.openDocument(str(args.base_model))
axis=App.Vector(0,.574,-.819);axis.normalize();rot=App.Rotation(App.Vector(0,0,1),axis);place=App.Placement(App.Vector(0,180,173),rot)
z=[0,10,32,57,76,94.81];dy=[0,-1,-2,-1,-1,-1.15]
if args.variant=='a':r=[49,54,65,69,64,53.82];sx=[1,1.12,1.20,1.20,1.10,1]
elif args.variant=='b':r=[49,60,68,67,64,53.82];sx=[1,1.25,1.25,1.12,1.04,1]
elif args.variant=='c':z=[0,28,60,94.81];r=[49,67,68,53.82];dy=[0,-1.5,-1,-1.15];sx=[1,1.25,1.15,1]
elif args.variant=='d':z=[0,28,60,94.81];r=[49,50.89141936,51.74393630,53.82];dy=[0,-.50621295,-2.07890507,-1.15];sx=[1,75.13263217/r[1],85.85861868/r[2],1]
elif args.variant=='e':z=[0,28,60,94.81];r=[49,65,66,53.82];dy=[0,2,1,-1.15];sx=[1,78/65,72/66,1]
elif args.variant=='f':z=[0,28,60,94.81];r=[49,66,66,53.82];dy=[0,-1,1,-1.15];sx=[1,84/66,73/66,1]
elif args.variant=='g':z=[0,28,60,94.81];r=[49,66,66,53.82];dy=[0,-1,1,-1.15];sx=[1,76/66,70/66,1]
elif args.variant=='h':z=[0,28,60,94.81];r=[49,66,66,53.82];dy=[0,-1,1,-1.15];sx=[1,72/66,69/66,1]
else:z=[0,28,60,94.81];r=[49,66,66,53.82];dy=[0,-1,1,-1.15];sx=[1,70/66,68/66,1]
exponents=[2,2.3,2.15,2] if args.variant=='g' else [2,2.1,2.05,2] if args.variant=='h' else [2,2,2,2] if args.variant=='i' else [2,2.7,2.3,2]
def loft(inset=0,expand=0):
 wires=[]
 for i,(a,b,c,d) in enumerate(zip(z,r,dy,sx)):
  if args.variant in ('e','f','g','h','i'):
   n=exponents[i];rx=b*d-inset+expand;ry=b-inset+expand
   points=[]
   for j in range(128):
    t=j*math.tau/128;co,si=math.cos(t),math.sin(t)
    points.append(App.Vector(rx*math.copysign(abs(co)**(2/n),co),c+ry*math.copysign(abs(si)**(2/n),si),a))
   curve=Part.BSplineCurve();curve.interpolate(points,PeriodicFlag=True);edge=curve.toShape()
  else:edge=Part.Ellipse(App.Vector(0,c,a),b*d-inset+expand,b-inset+expand).toShape()
  wires.append(Part.Wire([edge]))
 return Part.makeLoft(wires,True,False)
outer=loft();inner=loft(4);body=outer.cut(inner);body.Placement=place
obj=doc.getObject('BassNozzleShell');obj.Shape=body
coating=loft(expand=.35).cut(outer)
changed=['BassNozzleShell']
for side,(start,end) in enumerate(((212,234),(306,328))):
 for i,station in enumerate((76,84,92)):
  shape=coating.common(Part.Face(sector_wire(100,40,station,start,end)).extrude(App.Vector(0,0,2.5)))
  shape.Placement=place;name=f'BassSideStripe{side}_{i}';doc.getObject(name).Shape=shape;changed.append(name)
if args.variant in ('d','e','f','g','h','i'):
 white_skin=loft(expand=.65).cut(loft(inset=.25))
 red_skin=loft(expand=.95).cut(loft(expand=.4))
 masks={
  'BassWarningPlaque':(white_skin,rounded_plate(44,17,110,(-22,-110,65),1.3)),
  'BassWarningRedBand':(red_skin,rounded_plate(4.5,14.5,110,(16,-110,66.25),.7)),
  'BassWarningTriangle':(white_skin,profile([(-14,53),(14,53),(0,28)],'XZ',(0,-110,0),110)),
  'BassWarningTriangleInset':(red_skin,profile([(-11.5,51),(11.5,51),(0,31)],'XZ',(0,-110,0),110)),
 }
 for name,(skin,mask) in masks.items():
  sh=skin.common(mask);sh.Placement=place;doc.getObject(name).Shape=sh;changed.append(name)
 # Text stays a display annotation. Place its flat plane just outside the
 # most forward point of its curved patch so it does not disappear inside.
 for name,key,x,z0 in [('BassWarningPlaque','bass_warning_label_local_mm',14,73),
                       ('BassWarningTriangleInset','bass_alert_local_mm',1,40)]:
  local=doc.getObject(name).Shape.copy();local.Placement=App.Placement()
  mesh[key]=[x,local.optimalBoundingBox(False,False).YMin-.25,z0]
if args.variant=='i':
 # Remove only the part of the lower closure protruding into the new cavity;
 # retain its front skin and the two outer side rails.
 from experiment_drone_rear_cavity import slab
 clearance=slab(223,330,78,192,72).common(rounded_plate(144,110,400,(-72,0,80),8))
 obj=doc.getObject('RearLowerSlope');obj.Shape=obj.Shape.cut(clearance)
 changed.append('RearLowerSlope')
checks=[]
for name in changed:
 sh=doc.getObject(name).Shape;sh.check(True);assert sh.isValid() and sh.Solids
 checks.append({'name':name,'valid':sh.isValid(),'solids':len(sh.Solids)})
doc.recompute();model=out/'candidate.FCStd';doc.saveAs(str(model))
mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest()
for item in mesh['objects']:
 if item['name'] in changed:
  vertices,faces=doc.getObject(item['name']).Shape.tessellate(.12);item['vertices']=[list(p) for p in vertices];item['faces']=faces
(out/'meshes.json').write_text(json.dumps(mesh))
(out/'candidate-check.json').write_text(json.dumps({'changed_objects':checks,'status':'exploratory candidate; full detail contacts and delivery not accepted','base_fcstd_sha256':base_hash,'variant':args.variant,'x_factors':sx,'stations_mm':z,'radii_mm':r,'offsets_mm':dy,'superellipse_exponents':exponents if args.variant in ('e','f','g','h','i') else None,'gui_state_present':False},indent=2)+'\n')
App.closeDocument(doc.Name)
print(model,flush=True)
