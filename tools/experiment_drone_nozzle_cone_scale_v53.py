import argparse,hashlib,json,sys
from pathlib import Path
import FreeCAD as App, Part, Import
sys.path.insert(0,'/Users/miclle/github/miclle/vintrox/tools')
from drone_nozzle_interior import root_sections,bowl

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--shrink',type=float,required=True);a=p.parse_args()
if a.output.exists() and any(a.output.iterdir()):raise ValueError('output must be empty')
if not 0<a.shrink<12:raise ValueError('range')
a.output.mkdir(parents=True,exist_ok=True);basehash=digest(a.baseline);d=App.openDocument(str(a.baseline))
# Rebuild the real recessed bowl with a smaller radial profile; the surrounding recess remains separate.
rows0=root_sections([(96.8067,48.8215,-1.149,0),(104,47.35,.05,-1),(112,44.7666666667,1.4,-2)],1);z,r,dy,t=rows0[-1]
f=1-a.shrink/44
rows=[(z-23,20*f,dy,t),(z-16,28*f,dy,t),(z-7,(r-5)*f,dy,t),(z,(r-.7)*f,dy,t)]
shape=bowl(rows,ruled=True)
axis=App.Vector(0,.574,-.819);axis.normalize();shape.Placement=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
o=d.getObject('BassVisualCone');old=o.Shape;o.Shape=shape
if not shape.isValid() or not shape.Solids:raise ValueError('invalid candidate')
d.recompute();model=a.output/'candidate.FCStd';d.saveAs(str(model));App.closeDocument(d.Name)
d=App.openDocument(str(model));s=d.getObject('BassVisualCone').Shape
if not s.isValid() or not s.Solids or not all(x.isClosed() for x in s.Solids):raise ValueError('readback')
visible=[x for x in d.Objects if getattr(x,'Visibility',False) and hasattr(x,'Shape') and not x.Shape.isNull()];Import.export(visible,str(a.output/'candidate.step'))
meshes=[]
for x in visible:
 v,faces=x.Shape.tessellate(.12);meshes.append({'name':x.Name,'vertices':[[p.x,p.y,p.z] for p in v],'faces':faces,'color':list(x.ViewObject.ShapeColor[:3]) if x.ViewObject else [.8,.8,.8],'material':getattr(x,'RenderMaterial','paint')})
(a.output/'render-meshes.json').write_text(json.dumps({'fcstd_sha256':digest(model),'objects':meshes}))
(a.output/'candidate-check.json').write_text(json.dumps({'baseline_fcstd_sha256':basehash,'fcstd_sha256':digest(model),'shrink_mm':a.shrink,'changed_objects':['BassVisualCone'],'readback_passed':True,'step_exported':True,'before_volume':old.Volume,'after_volume':shape.Volume,'interpretation':'shorter radial bowl inside a non-cylindrical shadow housing; throat, petals, shell and supports unchanged','status':'candidate; fixed-camera visual comparison pending','limitations':['appearance-only inner bowl','dark reference region remains ambiguous','not manufacturing validation']},indent=2)+'\n');print(digest(model));App.closeDocument(d.Name)
