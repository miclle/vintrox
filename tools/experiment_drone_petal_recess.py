"""Compare formed leaf recesses without changing pitch or terminal circles."""
import argparse, hashlib, json, math
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import sector_wire, profile
from experiment_drone_rear_cavity import signature


def petal_recess_parts(i, variant):
    a=i*30+15; scale=30/22.5
    sections=[(96.8067,52.3215,-1.149,0),(108,49.4,.7,-1.5),
              (120,46,2.8,-3),(128.43,43.6,4.28,-4.2)]
    def skin(outer,inner,start,stop):
        wires=[]
        for z,r,dy,tilt in sections:
            w=sector_wire(r+outer,r+inner,z,a+start*scale,a+stop*scale)
            w.rotate(App.Vector(0,0,z),App.Vector(1,0,0),tilt);w.translate(App.Vector(0,dy,0));wires.append(w)
        return Part.makeLoft(wires,True,True)
    petal=skin(0,-2,1.2,21.3)
    normal=App.Vector(0,-math.sin(math.radians(-4.2)),math.cos(math.radians(-4.2)))
    edges=[e for e in petal.Edges if abs(e.Length-2)<1e-5 and (
        abs(e.CenterOfMass.z-96.8067)<1e-5 or
        abs(normal.dot(e.CenterOfMass-App.Vector(0,4.28,128.43)))<1e-5)]
    assert len(edges)==4
    petal=petal.makeFillet(.85,edges)
    narrow=variant=='b'
    cut_start,cut_stop=(2.7,19.8) if narrow else (3.4,19.1)
    inset_start,inset_stop=(3.1,19.4) if narrow else (4.2,18.3)
    end=127.0 if narrow else 125.8
    # Round a planar tapered cutter before intersecting curved leaf skins.
    # Filleting their trimmed multi-station faces directly creates invalid wires.
    def window(start,stop,z0,z1,radius):
        theta=math.radians(a+11.25*scale)
        tangent=App.Vector(math.sin(theta),-math.cos(theta),0)
        def point(z,angle):
            lo,hi=next((l,h) for l,h in zip(sections,sections[1:]) if l[0]<=z<=h[0])
            f=(z-lo[0])/(hi[0]-lo[0]);r,dy,tilt=[lo[j]+f*(hi[j]-lo[j]) for j in [1,2,3]]
            t=math.radians(a+angle*scale);q=App.Vector(r*math.cos(t),dy+r*math.sin(t)*math.cos(math.radians(tilt)),z+r*math.sin(t)*math.sin(math.radians(tilt)))
            return (tangent.dot(q),q.z)
        pts=[point(z0,start),point(z0,stop),point(z1,stop),point(z1,start)]
        tool=profile(pts,'XZ',(0,-80,0),160)
        axial=[e for e in tool.Edges if abs(e.Length-160)<1e-6]
        assert len(axial)==4
        tool=tool.makeFillet(radius,axial)
        tool.rotate(App.Vector(),App.Vector(0,0,1),math.degrees(theta)-90)
        return tool
    recess=skin(1,-.8,0,22.5).common(window(cut_start,cut_stop,99.5,end,1.0))
    inset=skin(-.65,-.95,0,22.5).common(window(inset_start,inset_stop,99.8,end-.3,.8))
    return {f'NozzlePetal{i}':petal.cut(recess),f'NozzlePetalInset{i}':inset}


def main():
    p=argparse.ArgumentParser()
    for n in ['base-model','base-meshes','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--variant',choices=['a','b'],required=True);a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
    base_hash=hashlib.sha256(a.base_model.read_bytes()).hexdigest();mesh=json.loads(a.base_meshes.read_text());assert mesh['fcstd_sha256']==base_hash
    doc=App.openDocument(str(a.base_model));old={o.Name:signature(o.Shape) for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    axis=App.Vector(0,.574,-.819);axis.normalize();place=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
    changed=[]
    for i in range(12):
        for name,s in petal_recess_parts(i,a.variant).items():
            s.Placement=place.multiply(s.Placement);s.check(True)
            assert s.isValid() and s.isClosed() and len(s.Solids)==1
            doc.getObject(name).Shape=s;item=next(o for o in mesh['objects'] if o['name']==name)
            vertices,faces=s.tessellate(.12);item.update(vertices=[list(v) for v in vertices],faces=faces);changed.append(name)
    a.output.mkdir(parents=True);model=a.output/'candidate.FCStd';doc.recompute();doc.saveAs(str(model));App.closeDocument(doc.Name)
    doc=App.openDocument(str(model));preserved=[{'name':o.Name,'unchanged_geometry_signature_6dp':signature(o.Shape)==old[o.Name]} for o in doc.Objects if o.Name in old and o.Name not in changed]
    assert all(o['unchanged_geometry_signature_6dp'] for o in preserved)
    parts=[];contacts=[]
    for name in changed:
        s=doc.getObject(name).Shape;s.check(True);parts.append({'name':name,'valid':s.isValid(),'solids':len(s.Solids),'advanced_check_passed':True})
    for i in range(12):
        s=doc.getObject(f'NozzlePetal{i}').Shape;t=doc.getObject(f'NozzlePetalInset{i}').Shape
        contacts.append({'objects':[f'NozzlePetal{i}',f'NozzlePetalInset{i}'],'gap_mm':s.distToShape(t)[0],'overlap_mm3':s.common(t).Volume})
    assert all(x['gap_mm']<1e-6 and x['overlap_mm3']>.01 for x in contacts)
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(a.output/'meshes.json').write_text(json.dumps(mesh))
    (a.output/'candidate-check.json').write_text(json.dumps({'baseline_fcstd_sha256':base_hash,'fcstd_sha256':mesh['fcstd_sha256'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variant':a.variant,'changed_objects':changed,'parts':parts,'contacts':contacts,'preserved':preserved,'status':'exploratory geometry; visual review pending'},indent=2)+'\n')
    App.closeDocument(doc.Name);print(model,flush=True)


if __name__=='__main__':main()
