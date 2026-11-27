"""Vary v50 shoulder width with fixed root, attachment and local depth."""
import argparse,hashlib,json,math
from pathlib import Path
import FreeCAD as App
import Part
from drone_fairing_shoulder import root_shifted_fairing
from experiment_drone_rear_cavity import signature

def main():
    p=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--shoulder-inset',type=float,choices=[0,2,4,6,8],required=True)
    p.add_argument('--lower-inset',type=float,choices=[-2,0,2,4,6,8])
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
    mesh=json.loads(a.base_meshes.read_text());baseline=hashlib.sha256(a.base_model.read_bytes()).hexdigest()
    assert mesh['fcstd_sha256']==baseline=='094bb2e63081b879e865db74d375f975126968bd2473772973c3dc0b2bd8171a'
    d=App.openDocument(str(a.base_model));original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    parts=root_shifted_fairing(shoulder_inset=a.shoulder_inset,lower_inset=a.lower_inset)
    axis=App.Vector(0,.574,-.819);axis.normalize();rotation=App.Rotation(App.Vector(0,0,1),axis);place=App.Placement(App.Vector(0,180,173),rotation)
    for name,key,x,z in [('BassWarningPlaque','bass_warning_label_local_mm',14,73),('BassWarningTriangleInset','bass_alert_local_mm',1,40)]:
        mesh[key]=[mesh[key][0],parts[name].optimalBoundingBox(False,False).YMin-.25,mesh[key][2]]
    records=[]
    for name,s in parts.items():
        s.Placement=place.multiply(s.Placement);s.check(True);assert s.isValid() and len(s.Solids)==1 and s.isClosed()
        d.getObject(name).Shape=s
        item=next(o for o in mesh['objects'] if o['name']==name);verts,faces=s.tessellate(.12);item['vertices']=[list(v) for v in verts];item['faces']=faces
        records.append({'name':name,'valid':True,'advanced_check_passed':True,'solids':1})
    a.output.mkdir(parents=True,exist_ok=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
    d=App.openDocument(str(model));preserved=[]
    for o in d.Objects:
        if o.Name not in original or o.Name in parts:continue
        preserved.append({'name':o.Name,'unchanged_geometry_signature_6dp':signature(o.Shape)==original[o.Name]})
    assert all(x['unchanged_geometry_signature_6dp'] for x in preserved)
    contacts=[]
    for x,y in [('BassWarningPlaque','BassNozzleShell'),('BassWarningTriangle','BassNozzleShell'),('BassWarningRedBand','BassWarningPlaque'),('BassWarningTriangleInset','BassWarningTriangle'),('BassNozzleRolledLip','BassNozzleShell'),('BassNozzleRearCollar','BassNozzleShell')]:
        s=d.getObject(x).Shape;t=d.getObject(y).Shape;contacts.append({'objects':[x,y],'gap_mm':s.distToShape(t)[0],'overlap_mm3':s.common(t).Volume})
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(a.output/'meshes.json').write_text(json.dumps(mesh))
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'shoulder_inset_mm':a.shoulder_inset,'lower_inset_mm':a.lower_inset if a.lower_inset is not None else a.shoulder_inset,'source_sha256':hashlib.sha256(Path(__file__).with_name('drone_fairing_shoulder.py').read_bytes()).hexdigest(),'changed_objects':list(parts),'parts':records,'preserved':preserved,'contacts':contacts,'status':'exploratory candidate; full camera and cavity verification pending'}
    (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(model,flush=True)

if __name__=='__main__':main()
