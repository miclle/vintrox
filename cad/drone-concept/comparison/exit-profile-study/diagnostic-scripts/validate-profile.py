from pathlib import Path
import sys,json,math,hashlib,ast
sys.path.insert(0,str(Path('tools').resolve()))
from PIL import Image
import FreeCAD as App
from drone_petal_profile import taper_sections
from experiment_drone_rear_cavity import signature
b=Path('cad/drone-concept/comparison/exit-profile-study');p=b/'profile-21-lined';check=json.load(open(p/'candidate-check.json'));digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert digest(p/'candidate.FCStd')==check['fcstd_sha256'];basepath=Path('cad/drone-concept/vintrox-drone-concept.FCStd');assert digest(basepath)==check['baseline_fcstd_sha256'];d=App.openDocument(str(p/'candidate.FCStd'));base=App.openDocument(str(basepath));parts=[];kept=[]
for obj in d.Objects:
 if not hasattr(obj,'Shape') or obj.Shape.isNull():continue
 if obj.Name in check['changed_objects']:
  shape=obj.Shape;assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1;parts.append({'name':obj.Name,'valid':True,'closed':True,'solids':1})
 else:assert signature(obj.Shape)==signature(base.getObject(obj.Name).Shape);kept.append(obj.Name)
assert len(parts)==98 and len(kept)==600
axis=App.Vector(0,.574,-.819);axis.normalize();placement=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis));contacts=[];probes=[]
for i in range(12):
 leaf=d.getObject(f'NozzlePetal{i}').Shape;neighbour=d.getObject(f'NozzlePetal{(i+1)%12}').Shape;overlap=leaf.common(neighbour).Volume;assert overlap<1e-6;contacts.append({'kind':'neighbour','leaf':i,'gap_mm':leaf.distToShape(neighbour)[0],'overlap_mm3':overlap});ridge=d.getObject(f'NozzlePetalRidge{i}').Shape
 for j in range(2):
  guide=d.getObject(f'NozzlePetalGuide{i}_{j}').Shape;gap=ridge.distToShape(guide)[0];assert gap<.01;contacts.append({'kind':'ridge-guide','leaf':i,'guide':j,'gap_mm':gap})
 names=[n for n in check['changed_objects'] if n==f'NozzlePetal{i}' or n in [f'NozzlePetalInset{i}',f'NozzlePetalRidge{i}',f'NozzlePetalGuide{i}_0',f'NozzlePetalGuide{i}_1']];shapes=[d.getObject(n).Shape for n in names];theta=math.radians(i*30+30);stations=taper_sections([(111.4,48.44,1.295,-1.925),(120,46,2.8,-3),(123.5,45,3.41,-3.5)],2.1)
 for z in [116,118,121]:
  lo,hi=next((lo,hi) for lo,hi in zip(stations,stations[1:]) if lo[0]<=z<=hi[0]);f=(z-lo[0])/(hi[0]-lo[0]);r,dy,t=[lo[j]+f*(hi[j]-lo[j]) for j in [1,2,3]]
  def point(offset):
   q=r+offset;return placement.multVec(App.Vector(q*math.cos(theta),dy+q*math.sin(theta)*math.cos(math.radians(t)),z+q*math.sin(theta)*math.sin(math.radians(t))))
  empty=not any(sh.isInside(point(-.3),1e-5,False) for sh in shapes);floor=ridge.isInside(point(-.95),1e-5,False);assert empty and floor,(i,z,empty,floor);probes.append({'leaf':i,'station_mm':z,'centre_empty':empty,'backing_solid':floor})
App.closeDocument(base.Name);App.closeDocument(d.Name)
images=[]
for file in p.rglob('*.png'):
 with Image.open(file) as im:im.verify()
 images.append({'path':str(file),'sha256':digest(file)})
for folder in ['video-renders','still-renders','ids']:
 key='object-id-manifest.json' if folder=='ids' else 'render-manifest.json';manifest=json.load(open(p/folder/key));assert manifest['fcstd_sha256']==check['fcstd_sha256']
 for im in manifest['images']:assert digest(p/folder/im['path'])==im['sha256']
for file in [Path('tools/drone_petal_profile.py'),Path('tools/experiment_drone_petal_profile.py'),b/'diagnostic-scripts/complete-profile.py']:ast.parse(file.read_text())
result={'passed':True,'fcstd_sha256':check['fcstd_sha256'],'formal_fcstd_sha256_unchanged':digest(basepath),'changed_parts':parts,'preserved_objects':kept,'contacts':contacts,'channel_probes':probes,'images':images,'limitations':['Sparse channel probes are not a wall-thickness field or manufacturing acceptance.','No formal model adoption or STEP/GUI release occurred.']};(b/'profile-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'changed':len(parts),'preserved':len(kept),'probes':len(probes),'images':len(images),'minimum_neighbour_gap_mm':min(c['gap_mm'] for c in contacts if c['kind']=='neighbour')}))
