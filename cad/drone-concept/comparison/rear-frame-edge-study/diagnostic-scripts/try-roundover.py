import FreeCAD as A,json,time
from pathlib import Path
root=Path('/Users/miclle/github/miclle/vintrox');out=root/'cad/drone-concept/comparison/rear-frame-edge-study';d=A.openDocument(str(root/'cad/drone-concept/vintrox-drone-concept.FCStd'));results=[]
for name,idx in [('RearStructuralFrame',[35,43]),('RearArmourCheekLeft',[1]),('RearArmourCheekRight',[1])]:
 s=d.getObject(name).Shape
 for radius in [0.8,1.5,2.5]:
  record={'name':name,'seed_edges':idx,'radius_mm':radius};start=time.time()
  try:
   f=s.makeFillet(radius,[s.Edges[i-1] for i in idx]);f.check(True);assert f.isValid() and f.isClosed() and len(f.Solids)==1
   record.update(passed=True,added_mm3=abs(f.cut(s).Volume),removed_mm3=abs(s.cut(f).Volume),faces=len(f.Faces))
   f.exportBrep(str(out/f'{name}-r{radius}.brep'))
  except Exception as e:record.update(passed=False,error=str(e))
  record['elapsed_seconds']=time.time()-start;results.append(record);print(record,flush=True)
(out/'roundover-feasibility.json').write_text(json.dumps(results,indent=2)+'\n');A.closeDocument(d.Name)
