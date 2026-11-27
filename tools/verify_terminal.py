"""Read back the modular-terminal package without saving any CAD document."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import csv
import hashlib
import json
import math
import FreeCAD as App
import Part
import Mesh
import terminal_model as model

ROOT=Path(__file__).resolve().parents[1]


def compare_step_geometry(objects,step):
    """Match world-coordinate solids by exact bounds and bidirectional differences.

    Do not reject on standalone volume integration: identical trimmed STEP surfaces
    can integrate a few 1e-5 mm3 apart even when both Boolean differences are empty.
    """
    assert step.isValid(),'STEP invalid'
    refs=[(obj.Name,s) for obj in objects for s in obj.Shape.Solids]
    candidates=list(step.Solids)
    assert len(refs)==len(candidates),'STEP solid count differs'
    max_cut=0.;max_volume=0.
    for name,solid in refs:
        bb=solid.optimalBoundingBox(False,False)
        for index,other in enumerate(candidates):
            ob=other.optimalBoundingBox(False,False)
            if any(abs(getattr(bb,k)-getattr(ob,k))>1e-6 for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')):continue
            residual=max(solid.cut(other).Volume,other.cut(solid).Volume)
            if residual<=1e-6:
                max_cut=max(max_cut,residual);max_volume=max(max_volume,abs(solid.Volume-other.Volume))
                candidates.pop(index);break
        else:raise ValueError('STEP geometry mismatch: '+name)
    return {'matched_solids':len(refs),'length_tolerance_mm':1e-6,'bidirectional_cut_tolerance_mm3':1e-6,'max_bidirectional_difference_mm3':max_cut,'max_standalone_volume_integration_difference_mm3':max_volume}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def mesh_volume(mesh):
    # Center first to avoid cancellation; accumulate signed tetrahedra in double precision.
    center=mesh.BoundBox.Center;terms=[]
    for facet in mesh.Facets:
        a,b,c=(App.Vector(*point)-center for point in facet.Points)
        terms.append(a.dot(b.cross(c))/6.)
    return abs(math.fsum(terms))


def verify_csv_manifest(path,records):
    fields=['ID','Name','Label','X_mm','Y_mm','Z_mm','Status']
    with Path(path).open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=fields:raise ValueError('CSV manifest header mismatch')
        rows=list(reader)
    if len(rows)!=len(records):raise ValueError('CSV manifest part count mismatch')
    for row,record in zip(rows,records):
        if set(row)!=set(fields) or any(row[key]!=value for key,value in
                [('ID',record['id']),('Name',record['name']),('Label',record['label']),('Status','ASSUMED / UNTESTED')]):
            raise ValueError('CSV manifest identity/status mismatch: '+record['id'])
        try:dimensions=[float(row[key]) for key in ('X_mm','Y_mm','Z_mm')]
        except (TypeError,ValueError) as error:raise ValueError('CSV manifest invalid dimensions: '+record['id']) from error
        if any(not math.isfinite(actual) or abs(actual-expected)>1e-6
               for actual,expected in zip(dimensions,record['print_bounds_mm'])):
            raise ValueError('CSV manifest dimensions mismatch: '+record['id'])
    return {'matched_parts':len(rows),'dimension_tolerance_mm':1e-6}


def readback(root=ROOT,exercise=False):
    out=Path(root)/'cad/terminal'
    inputs=[out/'vintrox-terminal.FCStd',out/'vintrox-terminal.step',out/'parts.json',out/'parts.csv']
    inputs+=sorted((out/'parts').glob('*'));inputs+=sorted((out/'previews').glob('*.png'))
    hashes={str(p.relative_to(root)):sha(p) for p in inputs}
    doc=App.openDocument(str(out/'vintrox-terminal.FCStd'))
    try:
        doc.recompute()
        report=model.validate(doc)
        assert not report['errors'],report
        assert not [o.Name for o in doc.Objects if 'Invalid' in o.State]
        p=doc.Parameters
        for alias,value in ([('ScreenW',210),('ScreenH',160),('ScreenT',2),('DriverW',94.5),('DriverH',63.5),('DriverT',5),('DiskW',80.5),('DiskH',131.5),('DiskT',13)] if exercise else []):
            assert abs(float(getattr(p,alias))-value)<1e-6,('Source dimension differs',alias)
        report['hardware_envelopes']={}
        for obj in doc.Hardware.Group:
            bb=obj.Shape.optimalBoundingBox(False,False)
            report['hardware_envelopes'][obj.Name]={'xyz_mm':[round(bb.XLength,4),round(bb.YLength,4),round(bb.ZLength,4)],'min_xyz_mm':[round(bb.XMin,4),round(bb.YMin,4),round(bb.ZMin,4)],'evidence':obj.EvidenceStatus}
        panel=doc.ScreenPanel.Shape.optimalBoundingBox(False,False)
        ribbon=doc.ScreenRibbonBoard.Shape.optimalBoundingBox(False,False)
        assert abs(panel.XMin-ribbon.XMin)<1e-6
        assert abs(ribbon.YMin-panel.YMax-float(p.RibbonGap))<1e-6
        assert abs(ribbon.ZMin-panel.ZMin-float(p.RibbonEndGap))<1e-6
        saved_manifest=json.loads((out/'parts.json').read_text())
        assert saved_manifest==model.parts_manifest(doc),'Part manifest differs from saved model'
        csv_comparison=verify_csv_manifest(out/'parts.csv',saved_manifest)
        step=Part.Shape();step.read(str(out/'vintrox-terminal.step'))
        assembly=compare_step_geometry(model.physical(doc),step)
        expected=set();parts=[]
        for obj,record in zip(doc.Printed.Group,saved_manifest):
            stem=obj.PartID+'-'+obj.Name;step_path=out/'parts'/(stem+'.step');mesh_path=out/'parts'/(stem+'.stl')
            expected.update((step_path.name,mesh_path.name))
            shape=model.print_shape(obj);s=Part.Shape();s.read(str(step_path))
            match=compare_step_geometry([SimpleNamespace(Name=obj.Name,Shape=shape)],s)
            m=Mesh.Mesh(str(mesh_path))
            assert m.isSolid() and m.countComponents()==1,(obj.Name,'mesh is not one closed object')
            mesh_bounds=m.BoundBox;shape_bounds=shape.optimalBoundingBox(False,False)
            assert max(abs(getattr(mesh_bounds,k)-getattr(shape_bounds,k)) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))<.15
            volume=mesh_volume(m);error=abs(volume-shape.Volume)/shape.Volume
            assert error<.003,(obj.Name,error)
            assert max(abs(getattr(shape_bounds,k)) for k in ('XMin','YMin','ZMin'))<1e-6
            parts.append({'id':obj.PartID,'name':obj.Name,'step_matched_solids':match['matched_solids'],'stl_closed':True,'stl_components':1,'mesh_volume_relative_difference':round(error,8),'print_bounds_mm':record['print_bounds_mm'],'fits_assumed_256_cube':record['assumed_256_cube_fit']})
        assert {q.name for q in (out/'parts').iterdir()}==expected,'Unexpected or missing files in parts/'
        probes=[]
        if exercise:
            for alias,delta,dimension in [('ScreenW',10,'Width'),('ScreenH',10,'Height'),('Depth',5,'Depth'),('Fit',.1,None),('FootH',1,None),('RibbonT',.2,None),('FrontRun',2,None),('RearDrop',.5,None),('SideRecess',.2,None),('GrilleRise',1,None),('ControlBevel',1,None),('BaseCorner',1,None)]:
                cell=p.getCellFromAlias(alias);old=float(getattr(p,alias));derived=float(getattr(p,dimension)) if dimension else None
                p.set(cell,str(old+delta));doc.recompute()
                changed=model.validate(doc)
                assert not changed['errors'],(alias,changed)
                assert not [o.Name for o in doc.Objects if 'Invalid' in o.State]
                if dimension:assert abs(float(getattr(p,dimension))-derived-delta)<1e-6
                if alias=='ScreenW':assert abs(doc.ScreenPanel.Shape.BoundBox.XLength-old-delta)<1e-6
                if alias=='ScreenH':assert abs(doc.ScreenPanel.Shape.BoundBox.ZLength-old-delta)<1e-6
                if alias=='Depth':assert abs(doc.RearPanel.Shape.optimalBoundingBox(False,False).YMax-old-delta)<1e-6
                if alias=='RibbonT':assert abs(doc.ScreenRibbonBoard.Shape.BoundBox.YLength-old-delta)<1e-6
                if alias=='FrontRun':assert abs(doc.TopBlankProfile.Geometry[1].StartPoint.x-old-delta)<1e-6
                if alias=='RearDrop':assert abs(doc.TopBlankProfile.Geometry[4].StartPoint.y-(float(p.Height)-old-delta))<1e-6
                if alias=='SideRecess':assert abs(doc.LeftInset.LengthFwd.Value-(old+delta+.01))<1e-6
                if alias=='GrilleRise':assert abs(doc.GrilleLeftSlot0Profile.Geometry[1].StartPoint.y-doc.GrilleLeftSlot0Profile.Geometry[0].StartPoint.y-old-delta)<1e-6
                if alias=='ControlBevel':assert abs(doc.ControlBlankProfile.Geometry[0].StartPoint.y-(float(p.BaseT)+float(p.Seam)+old+delta))<1e-6
                if alias=='BaseCorner':assert abs(doc.BaseBlankProfile.Geometry[0].StartPoint.x-old-delta)<1e-6
                if alias=='FootH':assert abs(doc.Foot0.Shape.BoundBox.ZLength-old-delta)<1e-6
                probes.append({'parameter':alias,'delta_mm':delta,'accepted':True})
                p.set(cell,str(old));doc.recompute()
            for alias,value in [('DiskY',138),('SpeakerT',65),('Depth',150)]:
                cell=p.getCellFromAlias(alias);old=float(getattr(p,alias))
                p.set(cell,str(value));doc.recompute();changed=model.validate(doc)
                assert changed['errors'],(alias,'Deliberate conflict was not detected')
                probes.append({'parameter':alias,'value_mm':value,'accepted':False,'expected_conflict_detected':True,'errors':changed['errors']})
                p.set(cell,str(old));doc.recompute()
            assert not model.validate(doc)['errors']
        assert all(sha(Path(root)/name)==digest for name,digest in hashes.items()),'Readback changed an input file'
        report['saved_readback']={'freecad_version':'.'.join(App.Version()[:3]),'assembly_step':assembly,'csv_manifest_comparison':csv_comparison,'parts':parts,'exercise_executed':exercise,'parameter_probes':probes,'all_inputs_unchanged':True}
        report['files_sha256']=hashes
        report['limits']='实体相交阈值0.01mm³；STEP逐实体双向差集阈值1e-6mm³；均非加工公差。标准接口和螺钉头仅示意；未验证实际打印、紧固、插头/弯线、完整拆卸路径、声学或热性能。'
        return report
    finally:App.closeDocument(doc.Name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.output and args.output.resolve()==(ROOT/'cad/terminal/terminal-validation.json').resolve() and not args.exercise:
        parser.error('Formal report requires --exercise')
    report=readback(exercise=args.exercise)
    if args.output:args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'body_mm':report['body_mm'],'printed_parts':report['printed_parts'],'assembly_solids':report['assembly_solids'],'errors':report['errors'],'step_matched':report['saved_readback']['assembly_step']['matched_solids'],'parts_verified':len(report['saved_readback']['parts']),'parameter_probes':report['saved_readback']['parameter_probes']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
