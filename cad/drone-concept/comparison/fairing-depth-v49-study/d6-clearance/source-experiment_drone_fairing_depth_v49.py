"""Vary v49 fairing middle depth with fixed root and attachment sections."""
import argparse,hashlib,json,math
from pathlib import Path
import FreeCAD as App
import Part
from drone_fairing_depth_v49 import root_shifted_fairing
from experiment_drone_rear_cavity import signature

def main():
    p=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--depth-extra',type=float,choices=[0,2,4,6],required=True)
    p.add_argument('--clear-lamps',action='store_true')
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
    mesh=json.loads(a.base_meshes.read_text());baseline=hashlib.sha256(a.base_model.read_bytes()).hexdigest()
    assert mesh['fcstd_sha256']==baseline=='c71cff088c8bfa8d562ca9b379af5779e9a86312d6cfb10525c1a47baa07cd40'
    d=App.openDocument(str(a.base_model));original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    parts=root_shifted_fairing(depth_extra=a.depth_extra)
    axis=App.Vector(0,.574,-.819);axis.normalize();rotation=App.Rotation(App.Vector(0,0,1),axis);place=App.Placement(App.Vector(0,180,173),rotation)
    for name,key,x,z in [('BassWarningPlaque','bass_warning_label_local_mm',14,73),('BassWarningTriangleInset','bass_alert_local_mm',1,40)]:
        mesh[key]=[mesh[key][0],parts[name].optimalBoundingBox(False,False).YMin-.25,mesh[key][2]]
    if a.clear_lamps:
        envelope=root_shifted_fairing(depth_extra=a.depth_extra,envelope_only=True)
        envelope.Placement=place
        for name in ['RearCyanFrame','RearCyanUpperLeft','RearCyanLowerLeft','RearCyanLowerRight']:
            old=d.getObject(name).Shape
            sh=old.cut(envelope)
            removed=abs(old.cut(sh).Volume)+abs(sh.cut(old).Volume)
            if removed>1e-6:
                sh.Placement=place.inverse().multiply(sh.Placement)
                parts[name]=sh
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
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'clear_lamps':a.clear_lamps,'depth_extra_mm':a.depth_extra,'source_sha256':hashlib.sha256(Path(__file__).with_name('drone_fairing_depth_v49.py').read_bytes()).hexdigest(),'changed_objects':list(parts),'parts':records,'preserved':preserved,'contacts':contacts,'status':'exploratory candidate; full camera and cavity verification pending'}
    (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(model,flush=True)

if __name__=='__main__':main()
