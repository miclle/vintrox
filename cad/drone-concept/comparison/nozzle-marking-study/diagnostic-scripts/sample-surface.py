import sys,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[5];sys.path.insert(0,str(root/'tools'))
import FreeCAD as App,Part
import numpy as np
model=root/'cad/drone-concept/vintrox-drone-concept.FCStd';assert hashlib.sha256(model.read_bytes()).hexdigest()=='d78a7df3e0c30b9c9571b800d308b93ecc75080ae431346db978942929e9550d'
d=App.openDocument(str(model));a=App.Vector(0,.574,-.819);a.normalize();frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),a));s=d.getObject('BassNozzleShell').Shape.copy();s.Placement=frame.inverse().multiply(s.Placement)
xs=np.linspace(-36,36,37);zs=np.linspace(15,88,74);rows=[]
for x in xs:
 row=[]
 for z in zs:
  t=s.common(Part.makeLine(App.Vector(x,-120,z),App.Vector(x,0,z)));row.append(min((v.Point.y for v in t.Vertexes),default=None))
 rows.append(row)
report={'fcstd_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'x_mm':xs.tolist(),'z_mm':zs.tolist(),'front_y_mm':rows,'frame_origin_mm':[0,180,173],'frame_axis':list(a),'method':'frontmost saved outer-shell intersection with local Y ray; interpolation only used for parameter fitting'}
p=root/'cad/drone-concept/comparison/nozzle-marking-study/surface-grid.json';p.write_text(json.dumps(report,indent=2)+'\n');print('sampled',len(xs)*len(zs),'rays')
