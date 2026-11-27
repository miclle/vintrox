from pathlib import Path
import FreeCAD as A,Part,json
root=Path('/Users/miclle/github/miclle/vintrox');d=A.openDocument(str(root/'cad/drone-concept/vintrox-drone-concept.FCStd'))
axis=A.Vector(0,.574,-.819);axis.normalize();frame=A.Placement(A.Vector(0,180,173),A.Rotation(A.Vector(0,0,1),axis))
s=d.getObject('NozzlePetal8').Shape.copy();s.Placement=frame.inverse().multiply(s.Placement)
center=A.Vector(0,4.28,128.43);normal=A.Vector(0,0,1);normal=A.Rotation(A.Vector(1,0,0),-4.2).multVec(normal)
rows=[]
for i,e in enumerate(s.Edges):
 pts=e.discretize(Number=15);plane=max(abs(normal.dot(p-center)) for p in pts);r=[((p-center)-normal*normal.dot(p-center)).Length for p in pts]
 if plane<.01:rows.append({'index':i,'length':e.Length,'type':type(e.Curve).__name__,'plane_distance':plane,'rmin':min(r),'rmax':max(r),'vertices':[list(v.Point) for v in e.Vertexes]})
print(json.dumps(rows,indent=2));(root/'cad/drone-concept/comparison/petal-inner-edge-study/terminal-edges.json').write_text(json.dumps(rows,indent=2)+'\n')
A.closeDocument(d.Name)
