"""Reposition four warning patches on the unchanged v51 fairing."""
import argparse,hashlib,json,math
from pathlib import Path
import FreeCAD as App
import Part
from drone_fairing_shoulder import root_shifted_fairing
from drone_nozzle_markings import MARKING_SPEC,label_positions
from experiment_drone_rear_cavity import signature

def main():
    p=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
    mesh=json.loads(a.base_meshes.read_text());baseline=hashlib.sha256(a.base_model.read_bytes()).hexdigest()
    assert mesh['fcstd_sha256']==baseline=='d78a7df3e0c30b9c9571b800d308b93ecc75080ae431346db978942929e9550d'
    d=App.openDocument(str(a.base_model));original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    parts={n:s for n,s in root_shifted_fairing(shoulder_inset=6,lower_inset=0,marking_spec=MARKING_SPEC).items() if n.startswith('BassWarning')}
    axis=App.Vector(0,.574,-.819);axis.normalize();rotation=App.Rotation(App.Vector(0,0,1),axis);place=App.Placement(App.Vector(0,180,173),rotation)
    mesh.update(label_positions(parts))
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
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'marking_spec':MARKING_SPEC,'source_sha256':hashlib.sha256(Path(__file__).with_name('drone_nozzle_markings.py').read_bytes()).hexdigest(),'changed_objects':list(parts),'parts':records,'preserved':preserved,'contacts':contacts,'status':'exploratory candidate; full camera and cavity verification pending'}
    (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(model,flush=True)

if __name__=='__main__':main()
