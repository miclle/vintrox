"""Study the real rolled lip and recessed gasket while preserving the outlet."""
import argparse,json,hashlib
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import ring
from experiment_drone_rear_cavity import signature

VARIANTS={'a':(53.5,.9,95.2,53.5),'b':(52.82,1.0,95.6,52.5),'c':(52.82,1.0,95.6,52.5)}

def lip_parts(variant):
    major,minor,station,gasket=VARIANTS[variant]
    parts={'BassNozzleRolledLip':Part.makeTorus(major,minor,App.Vector(0,-1.15,station)),
            'BassSpeakerGasket':ring(gasket,48,4,(0,-1.15,91))}
    if variant=='c':parts['BassNozzleMouthRing']=Part.makeTorus(52.3215,1.0,App.Vector(0,-1.149,96.8067))
    return parts

def main():
    p=argparse.ArgumentParser()
    for n in ['base-model','base-meshes','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--variant',choices=VARIANTS,required=True);a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
    mesh=json.load(open(a.base_meshes));h=hashlib.sha256(a.base_model.read_bytes()).hexdigest();assert mesh['fcstd_sha256']==h
    d=App.openDocument(str(a.base_model));original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    axis=App.Vector(0,.574,-.819);axis.normalize();place=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis));parts=lip_parts(a.variant);checks=[]
    for name,s in parts.items():
        s.Placement=place;s.check(True);assert s.isValid() and s.isClosed() and len(s.Solids)==1
        d.getObject(name).Shape=s;item=next(o for o in mesh['objects'] if o['name']==name);verts,faces=s.tessellate(.12);item['vertices']=[list(v) for v in verts];item['faces']=faces
        checks.append({'name':name,'valid':True,'advanced_check_passed':True,'solids':1})
    a.output.mkdir(parents=True,exist_ok=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
    d=App.openDocument(str(model));preserved=[{'name':o.Name,'unchanged_geometry_signature_6dp':signature(o.Shape)==original[o.Name]} for o in d.Objects if o.Name in original and o.Name not in parts];assert all(x['unchanged_geometry_signature_6dp'] for x in preserved)
    contacts=[]
    for x,y in [('BassNozzleRolledLip','BassNozzleShell'),('BassNozzleRolledLip','BassNozzleMouthRing'),('BassSpeakerGasket','BassNozzleShell')]:
        s=d.getObject(x).Shape;t=d.getObject(y).Shape;contacts.append({'objects':[x,y],'gap_mm':s.distToShape(t)[0],'overlap_mm3':s.common(t).Volume})
    petal_contacts=[]
    for i in range(12):
        petal_contacts.append({'name':f'NozzlePetal{i}','root_roll_overlap_mm3':d.getObject(f'NozzlePetal{i}').Shape.common(d.getObject('BassNozzleMouthRing').Shape).Volume})
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(a.output/'meshes.json').write_text(json.dumps(mesh))
    (a.output/'candidate-check.json').write_text(json.dumps({'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':h,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variant':a.variant,'parameters_mm':VARIANTS[a.variant],'changed_objects':list(parts),'parts':checks,'contacts':contacts,'petal_contacts':petal_contacts,'preserved':preserved,'status':'exploratory fixed-camera candidate'},indent=2)+'\n');print(model)

if __name__=='__main__':main()
