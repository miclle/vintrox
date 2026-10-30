"""Verify saved rear shoulders against the reviewed fixed-endpoint construction."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import reprojected_rear_shoulders,profile

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def delta(a,b):return a.cut(b).Volume+b.cut(a).Volume

def main():
    p=argparse.ArgumentParser()
    for n in ['model','candidate','baseline','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();base_hash='72f70bbc88e8ec059fb033c6388f89bd8a96a877e0f683a1a0d805848d590adc';assert digest(a.baseline)==base_hash
    model=App.openDocument(str(a.model));candidate=App.openDocument(str(a.candidate));base=App.openDocument(str(a.baseline))
    try:
        source=reprojected_rear_shoulders(108.0,1.0089049846660512,481.9590609254328,317.0386845391606)
        generated=[];saved=[];contacts=[]
        for side,suffix in [(-1,'Left'),(1,'Right')]:
            inner=[(190,182),(214,182),(214,145),(204,133),(190,145)];mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
            def wire(points,x):
                v=[App.Vector(x,y,z) for y,z in points];return Part.Wire(Part.makePolygon(v+[v[0]]).Edges)
            n='RearArmourCheek'+suffix
            s=source[n].cut(profile(inner,'YZ',(side*94.6,0,0),side*25)).cut(Part.makeLoft([wire(inner,side*94.6),wire(mouth,side*117)],True,True))
            c=candidate.getObject(n).Shape;m=model.getObject(n).Shape;s.check(True);c.check(True);m.check(True)
            generated.append({'name':n,'advanced_check_passed':True,'symmetric_difference_mm3':delta(s,c)})
            saved.append({'name':n,'valid':m.isValid(),'solids':len(m.Solids),'advanced_check_passed':True,'symmetric_difference_mm3':delta(m,c)})
            for other in ['RearStructuralFrame','SideGuard'+suffix]:
                t=model.getObject(other).Shape;contacts.append({'objects':[n,other],'gap_mm':m.distToShape(t)[0],'overlap_mm3':m.common(t).Volume})
        shafts=[{'name':o.Name,'symmetric_difference_mm3':delta(o.Shape,model.getObject(o.Name).Shape)} for o in base.Objects if o.Name.startswith('SupportShaft')]
        assert len(shafts)==4 and all(x['symmetric_difference_mm3']<1e-6 for x in generated+saved+shafts)
        assert all(x['valid'] and x['solids']==1 for x in saved) and all(x['gap_mm']<.01 for x in contacts)
        a.output.mkdir(parents=True,exist_ok=True)
        (a.output/'source-equivalence.json').write_text(json.dumps({'generator_sha256':digest(Path(__file__).with_name('drone_concept.py')),'baseline_fcstd_sha256':base_hash,'candidate_fcstd_sha256':digest(a.candidate),'parts':generated,'passed':True},indent=2)+'\n')
        (a.output/'formal-geometry-check.json').write_text(json.dumps({'fcstd_sha256':digest(a.model),'candidate_fcstd_sha256':digest(a.candidate),'measurement_script_sha256':digest(Path(__file__)),'parts':saved,'shafts':shafts,'shoulder_contacts':contacts,'passed':True},indent=2)+'\n')
        print('Two source/saved shoulders, four contacts and four shafts passed',flush=True)
    finally:
        for d in [model,candidate,base]:App.closeDocument(d.Name)
if __name__=='__main__':main()
