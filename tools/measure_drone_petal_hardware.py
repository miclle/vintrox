"""Bind production nozzle hardware to saved candidate and formal BReps."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
from drone_concept import nozzle_leaf_parts
from drone_petal_hardware import rolled_petal_root


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def delta(a,b):return a.cut(b).Volume+b.cut(a).Volume


def main():
    p=argparse.ArgumentParser()
    for name in ['model','candidate','baseline','candidate-geometry','output']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();baseline_hash='b386c41de3c1ad8983d5397d1c5509545b22864bc1194007796de6a55102d958'
    assert digest(a.baseline)==baseline_hash
    evidence=json.loads(a.candidate_geometry.read_text())
    assert evidence['passed'] and evidence['fcstd_sha256']==digest(a.candidate)
    model=App.openDocument(str(a.model));candidate=App.openDocument(str(a.candidate));baseline=App.openDocument(str(a.baseline))
    try:
        axis=App.Vector(0,.574,-.819);axis.normalize()
        frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
        source_rows=[];saved_rows=[]
        for i in range(12):
            generated=nozzle_leaf_parts(i)
            generated[f'NozzlePetalHinge{i}']=rolled_petal_root(i)
            names=[f'NozzlePetalRidge{i}',f'NozzlePetalGuide{i}_0',f'NozzlePetalGuide{i}_1',f'NozzlePetalHinge{i}']
            for name in names:
                shape=generated[name];shape.Placement=frame.multiply(shape.Placement)
                other=candidate.getObject(name).Shape;current=model.getObject(name).Shape
                for part in [shape,other,current]:
                    part.check(True);assert part.isValid() and part.isClosed() and len(part.Solids)==1
                source_rows.append({'name':name,'advanced_check_passed':True,'symmetric_difference_mm3':delta(shape,other)})
                saved_rows.append({'name':name,'valid':True,'solids':1,'closed':True,'advanced_check_passed':True,'symmetric_difference_mm3':delta(current,other)})
        shafts=[{'name':o.Name,'symmetric_difference_mm3':delta(o.Shape,model.getObject(o.Name).Shape)} for o in baseline.Objects if o.Name.startswith('SupportShaft')]
        protected=[{'name':name,'symmetric_difference_mm3':delta(baseline.getObject(name).Shape,model.getObject(name).Shape)} for name in [*[f'NozzlePetal{i}' for i in range(12)],'BassNozzleShell','BassNozzleRolledLip','RearServicePanel','RearRecessLiner']]
        contacts=[]
        for row in evidence['contacts']:
            x,y=row['objects'];first=model.getObject(x).Shape;second=model.getObject(y).Shape
            contacts.append({'objects':[x,y],'gap_mm':first.distToShape(second)[0],'overlap_mm3':first.common(second).Volume})
        assert len(source_rows)==48 and len(shafts)==4 and len(contacts)==72
        assert all(r['symmetric_difference_mm3']<1e-6 for r in source_rows+saved_rows+shafts+protected)
        assert all(r['gap_mm']<.01 for r in contacts)
        assert len(evidence['channel_probes'])==36 and all(r['channel_centre_is_empty'] and r['ridge_backing_is_solid'] for r in evidence['channel_probes'])
        a.output.mkdir(parents=True,exist_ok=True)
        source={'generator_sha256':digest(Path(__file__).with_name('drone_concept.py')),
                'source_module_sha256':digest(Path(__file__).with_name('drone_petal_hardware.py')),
                'baseline_fcstd_sha256':baseline_hash,'candidate_fcstd_sha256':digest(a.candidate),'parts':source_rows,'passed':True}
        saved={'fcstd_sha256':digest(a.model),'candidate_fcstd_sha256':digest(a.candidate),
               'measurement_script_sha256':digest(Path(__file__)),'parts':saved_rows,'shafts':shafts,
               'protected_geometry':protected,'hardware_contacts':contacts,
               'candidate_geometry_sha256':digest(a.candidate_geometry),'channel_probes':evidence['channel_probes'],
               'probe_evidence_method':'candidate probes transferred only after saved/source shape equivalence and unchanged primary leaves',
               'passed':True}
        for name,data in [('source-equivalence.json',source),('formal-geometry-check.json',saved)]:
            (a.output/name).write_text(json.dumps(data,indent=2)+'\n')
        print('48 source/saved parts, 72 contacts, 36 backed-recess probes and four shafts passed')
    finally:
        for name in {model.Name,candidate.Name,baseline.Name}:App.closeDocument(name)


if __name__=='__main__':main()
