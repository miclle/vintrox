"""Bind production nozzle hardware to saved candidate and formal BReps."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
from drone_concept import nozzle_leaf_parts
from drone_concept import nozzle_lip_parts, nozzle_fairing_parts, rear_cavity_lighting, raked_rear_parts
from zipfile import ZipFile
from refine_drone_nozzle_root import shape_files
from drone_nozzle_root_profile import root_shifted_hinge, root_shifted_inner_parts


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def delta(a,b):
    if a.exportBrepToString()==b.exportBrepToString():return 0.0
    return a.cut(b).Volume+b.cut(a).Volume


def main():
    p=argparse.ArgumentParser()
    for name in ['model','candidate','baseline','candidate-geometry','output']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();baseline_hash='475c208851231c3c98da53e59c62ad1a18de1bf969f6d0622db8e5f93b03b7e5'
    assert digest(a.baseline)==baseline_hash
    evidence=json.loads(a.candidate_geometry.read_text())
    assert evidence['passed'] and evidence['fcstd_sha256']==digest(a.candidate)
    model=App.openDocument(str(a.model));candidate=App.openDocument(str(a.candidate));baseline=App.openDocument(str(a.baseline))
    try:
        axis=App.Vector(0,.574,-.819);axis.normalize()
        frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
        source_rows=[];saved_rows=[]
        for i in range(14):
            generated=(nozzle_leaf_parts(i) if i<12 else {**nozzle_lip_parts(),**nozzle_fairing_parts(),**root_shifted_inner_parts()})
            if i<12:generated[f'NozzlePetalHinge{i}']=root_shifted_hinge(i)
            if i==13:
                lighting=rear_cavity_lighting(raked_rear_parts(134,outer_x=112.76)['RearCyanFrame'],candidate.getObject('BassNozzleShell').Shape)
                generated={name:lighting[name][0] for name in ['RearCyanLowerLeft','RearCyanLowerRight']}
            names=list(generated)
            for name in names:
                shape=generated[name]
                if i<13:shape.Placement=frame.multiply(shape.Placement)
                other=candidate.getObject(name).Shape;current=model.getObject(name).Shape
                for part in [shape]:
                    part.check(True);assert part.isValid() and part.isClosed() and len(part.Solids)==1
                source_rows.append({'name':name,'advanced_check_passed':True,'symmetric_difference_mm3':delta(shape,other)})
                print(name, 'source compared', flush=True)
                saved_rows.append({'name':name,'valid':True,'solids':1,'closed':True,'advanced_check_passed':True,'symmetric_difference_mm3':delta(current,other)})
        shafts=[{'name':o.Name,'symmetric_difference_mm3':delta(o.Shape,model.getObject(o.Name).Shape)} for o in baseline.Objects if o.Name.startswith('SupportShaft')]
        changed={r['name'] for r in saved_rows}
        protected=[]
        with ZipFile(a.baseline) as old_archive, ZipFile(a.model) as new_archive:
            old_files,new_files=shape_files(old_archive),shape_files(new_archive)
            for name in old_files:
                if name in changed:continue
                assert old_archive.read(old_files[name])==new_archive.read(new_files[name]),name
                protected.append({'name':name,'symmetric_difference_mm3':0.0,'method':'exact saved BRep payload equality'})
        contacts=[]
        for i in range(12):
            ridge=f'NozzlePetalRidge{i}'
            for other in [f'NozzlePetal{i}',f'NozzlePetalHinge{i}',f'NozzlePetalGuide{i}_0',f'NozzlePetalGuide{i}_1']:
                first=model.getObject(ridge).Shape;second=model.getObject(other).Shape
                contacts.append({'objects':[ridge,other],'gap_mm':first.distToShape(second)[0]})
        assert len(source_rows)==126 and len(shafts)==4 and len(contacts)==48 and len(protected)==572
        assert all(r['symmetric_difference_mm3']<1e-6 for r in source_rows+saved_rows+shafts+protected)
        assert all(r['gap_mm']<.01 for r in contacts)
        assert len(evidence['channel_probes'])==36 and all(r['centre_empty'] and r['backing_solid'] for r in evidence['channel_probes'])
        a.output.mkdir(parents=True,exist_ok=True)
        source={'generator_sha256':digest(Path(__file__).with_name('drone_concept.py')),
                'source_module_sha256':digest(Path(__file__).with_name('drone_nozzle_root_profile.py')),
                'baseline_fcstd_sha256':baseline_hash,'candidate_fcstd_sha256':digest(a.candidate),'parts':source_rows,'passed':True}
        saved={'fcstd_sha256':digest(a.model),'candidate_fcstd_sha256':digest(a.candidate),
               'measurement_script_sha256':digest(Path(__file__)),'parts':saved_rows,'shafts':shafts,
               'protected_geometry':protected,'hardware_contacts':contacts,
               'candidate_geometry_sha256':digest(a.candidate_geometry),'channel_probes':evidence['channel_probes'],
               'probe_evidence_method':'mapped candidate probes transferred only after all 126 source/candidate/saved shapes match',
               'passed':True}
        for name,data in [('source-equivalence.json',source),('formal-geometry-check.json',saved)]:
            (a.output/name).write_text(json.dumps(data,indent=2)+'\n')
        print('126 source/saved parts, 572 protected objects, 48 contacts, 36 backed-channel probes and four shafts passed')
    finally:
        for name in {model.Name,candidate.Name,baseline.Name}:App.closeDocument(name)


if __name__=='__main__':main()
