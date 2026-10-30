import FreeCAD as A,json
from pathlib import Path
root=Path('/Users/miclle/github/miclle/vintrox');d=A.openDocument(str(root/'cad/drone-concept/vintrox-drone-concept.FCStd'));out={}
for name in ['RearStructuralFrame','RearServicePanel','RearArmourCheekLeft']:
 s=d.getObject(name).Shape;out[name]={'bounds':str(s.BoundBox),'edges':[]}
 for i,e in enumerate(s.Edges):
  b=e.BoundBox;c=e.CenterOfMass
  out[name]['edges'].append({'index':i+1,'length':e.Length,'center':list(c),'bounds':[b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax],'curve':type(e.Curve).__name__})
 print(name,'edges',len(s.Edges),s.BoundBox)
 for e in out[name]['edges']:
  if name=='RearArmourCheekLeft' and e['bounds'][5]<68:print(e)
  if name=='RearStructuralFrame' and e['length']>60:print(e)
(root/'cad/drone-concept/comparison/rear-frame-edge-study/baseline-edges.json').write_text(json.dumps(out,indent=2)+'\n')
A.closeDocument(d.Name)
