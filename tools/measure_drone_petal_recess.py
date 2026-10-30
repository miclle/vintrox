"""Compare formed recess source, selected candidate and saved appearance solids."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
from drone_concept import nozzle_leaf_parts

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def delta(a,b):return a.cut(b).Volume+b.cut(a).Volume

def main():
    p=argparse.ArgumentParser()
    for name in ['model','candidate','baseline','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();base_hash='a517708ecfbf61416ae16f371bdfa9d319ce36b552d257707e69dc5bd9376ca6'
    assert digest(a.baseline)==base_hash
    model=App.openDocument(str(a.model));candidate=App.openDocument(str(a.candidate));base=App.openDocument(str(a.baseline))
    try:
        axis=App.Vector(0,.574,-.819);axis.normalize();place=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
        generated=[];saved=[];contacts=[]
        for i in range(12):
            source=nozzle_leaf_parts(i)
            for n in [f'NozzlePetal{i}',f'NozzlePetalInset{i}']:
                s=source[n];s.Placement=place.multiply(s.Placement);c=candidate.getObject(n).Shape;m=model.getObject(n).Shape
                s.check(True);c.check(True);m.check(True)
                generated.append({'name':n,'advanced_check_passed':True,'symmetric_difference_mm3':delta(s,c)})
                saved.append({'name':n,'valid':m.isValid(),'solids':len(m.Solids),'advanced_check_passed':True,'symmetric_difference_mm3':delta(m,c)})
            leaf=model.getObject(f'NozzlePetal{i}').Shape;inset=model.getObject(f'NozzlePetalInset{i}').Shape
            contacts.append({'objects':[f'NozzlePetal{i}',f'NozzlePetalInset{i}'],'gap_mm':leaf.distToShape(inset)[0],'overlap_mm3':leaf.common(inset).Volume})
        shafts=[{'name':o.Name,'symmetric_difference_mm3':delta(o.Shape,model.getObject(o.Name).Shape)} for o in base.Objects if o.Name.startswith('SupportShaft')]
        assert len(shafts)==4 and all(x['symmetric_difference_mm3']<1e-6 for x in generated+saved+shafts)
        assert all(x['valid'] and x['solids']==1 for x in saved)
        assert all(x['gap_mm']<1e-6 and x['overlap_mm3']>.01 for x in contacts)
        a.output.mkdir(parents=True,exist_ok=True)
        (a.output/'source-equivalence.json').write_text(json.dumps({'generator_sha256':digest(Path(__file__).with_name('drone_concept.py')),'baseline_fcstd_sha256':base_hash,'candidate_fcstd_sha256':digest(a.candidate),'parts':generated,'passed':True},indent=2)+'\n')
        (a.output/'formal-geometry-check.json').write_text(json.dumps({'fcstd_sha256':digest(a.model),'candidate_fcstd_sha256':digest(a.candidate),'measurement_script_sha256':digest(Path(__file__)),'parts':saved,'shafts':shafts,'inset_contacts':contacts,'passed':True},indent=2)+'\n')
        print('24 source/saved parts, 12 inset contacts and four shafts passed',flush=True)
    finally:
        for d in [model,candidate,base]:App.closeDocument(d.Name)
if __name__=='__main__':main()
