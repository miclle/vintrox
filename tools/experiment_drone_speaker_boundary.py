import argparse, hashlib, json
from pathlib import Path
import FreeCAD as App
import Part
import Import
from zipfile import ZipFile
from xml.etree import ElementTree as ET

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sig(s):
 b=s.BoundBox; return {'volume_mm3':round(s.Volume,6),'bbox_mm':[round(v,6) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)],'solids':len(s.Solids),'valid':bool(s.isValid()),'closed':all(x.isClosed() for x in s.Solids)}
def cyl(r,l,pos,axis): return Part.makeCylinder(r,l,App.Vector(*pos),App.Vector(*axis))
def make(name, side, scale, mode):
 suffix='Left' if side<0 else 'Right'; cx,cy,cz=113.62074,129.09686,153.62312; direction=(side,0,0); axis=App.Vector(*direction); radial=(53.78761/54)*scale
 vals={
 f'SpeakerOuterLip{suffix}':Part.makeTorus(53.78761*scale-5*scale,5*scale,App.Vector(side*cx,cy,cz),axis),
 f'SpeakerLipTrim{suffix}':Part.makeTorus((53.78761-.8)*scale,.55*scale,App.Vector(side*(cx+1),cy,cz),axis),
 f'SpeakerSurround{suffix}':Part.makeTorus(43.5*radial,2.8*radial,App.Vector(side*(cx-1.7),cy,cz),axis),
 f'SpeakerCentre{suffix}':cyl(18*scale,5,(side*109,cy,cz),direction),
 f'SpeakerHubNeck{suffix}':cyl(27*scale,30,(side*107,126,151),direction),
 f'SpeakerVisualCone{suffix}':Part.makeCone(44*radial,31*radial,10,App.Vector(side*cx,cy,cz),App.Vector(-side,0,0)).cut(Part.makeCone(40.7*radial,24*radial,9.2,App.Vector(side*(cx+.1),cy,cz),App.Vector(-side,0,0)))
 }
 groups={'lip':('SpeakerOuterLip','SpeakerLipTrim'),'cone':('SpeakerVisualCone','SpeakerSurround'),'hub':('SpeakerHubNeck','SpeakerCentre'),'all':('SpeakerOuterLip','SpeakerLipTrim','SpeakerSurround','SpeakerCentre','SpeakerHubNeck','SpeakerVisualCone')}
 return vals[name] if any(name.startswith(x) for x in groups[mode]) else None

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--scale',type=float,required=True);ap.add_argument('--mode',choices=['lip','cone','hub','all'],required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 base=sha(a.base);
 with ZipFile(a.base) as z:
  gui=ET.fromstring(z.read('GuiDocument.xml')); visible=[]
  for n in gui.findall('.//ViewProvider'):
   v=n.find('./Properties/Property[@name="Visibility"]/Bool')
   if v is not None and v.get('value')=='true': visible.append(n.get('name'))
 doc=App.openDocument(str(a.base.resolve())); names=[]; checks=[]
 for side in (-1,1):
  suffix='Left' if side<0 else 'Right'
  for n in ['SpeakerOuterLip','SpeakerLipTrim','SpeakerSurround','SpeakerCentre','SpeakerHubNeck','SpeakerVisualCone']:
   name=n+suffix; shape=make(name,side,a.scale,a.mode)
   if shape is None: continue
   obj=doc.getObject(name); checks.append({'name':name,'before':sig(obj.Shape),'after':sig(shape)});obj.Shape=shape;names.append(name)
 doc.recompute();model=a.output/'candidate.FCStd';doc.saveAs(str(model));App.closeDocument(doc.Name)
 doc=App.openDocument(str(model)); visible_objects=[doc.getObject(name) for name in visible]
 Import.export(visible_objects,str((a.output/'candidate.step').resolve()))
 step=a.output/'candidate.step'
 result={'revision':a.output.name,'baseline_fcstd_sha256':base,'fcstd_sha256':sha(model),'step_sha256':sha(step),'scale':a.scale,'mode':a.mode,'changed_objects':names,'checks':checks,'visible_features':len(visible_objects),'registration':'fixed cameras; no image warp, stretch, per-part alignment, or omitted visible parts','mesh_rebuild':'tools/export_saved_drone_meshes.py --output <temporary-mesh-json>','builder_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'status':'candidate; fixed-camera screening package'}
 (a.output/'candidate-check.json').write_text(json.dumps(result,indent=2)+'\n');App.closeDocument(doc.Name);print(json.dumps({'candidate':str(model),'step':str(step),'visible_features':len(visible_objects),'changed':names}))
if __name__=='__main__':main()
