"""Test rear-frame width while preserving the v53 rear panel and nozzle."""
import argparse, hashlib, json
from pathlib import Path
import FreeCAD as App
from drone_concept import rounded_frame, rear_raked_slab, rounded_plate
from experiment_drone_rear_cavity import signature


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def diff(a,b): return abs(a.cut(b).Volume)+abs(b.cut(a).Volume)

def make_frame(width):
    bottom=67.8; top=231.8; border=7.56; radius=10.08
    shape=rounded_frame(width, top-bottom, 400, border, (-width/2,0,bottom), radius)
    shape=shape.common(rear_raked_slab(241.75,248,bottom,top,width/2))
    for side in (-1,1):
        shape=shape.cut(rounded_plate(13.5,2.8,2.1,(side*15.5-6.75,246.7,228),1.3))
    shape.check(True)
    if not shape.isValid() or not shape.isClosed() or len(shape.Solids)!=1: raise ValueError('invalid frame')
    return shape

def main():
    p=argparse.ArgumentParser()
    for n in ['base-model','base-meshes','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--width',type=float,choices=[172,178,184],required=True);a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('use empty output')
    meshes=json.loads(a.base_meshes.read_text());baseline=digest(a.base_model);assert meshes['fcstd_sha256']==baseline
    d=App.openDocument(str(a.base_model));old={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    oldsig={n:signature(s) for n,s in old.items()};name='RearStructuralFrame';shape=make_frame(a.width);base=old[name]
    if a.width==178: assert diff(shape,base)<1e-6
    d.getObject(name).Shape=shape;item=next(x for x in meshes['objects'] if x['name']==name);v,f=shape.tessellate(.12);item.update(vertices=[list(q) for q in v],faces=f)
    a.output.mkdir(parents=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name);d=App.openDocument(str(model))
    preserved=[]
    for n,sig in oldsig.items():
        if n==name:continue
        assert signature(d.getObject(n).Shape)==sig,n;preserved.append(n)
    assert len(preserved)==697
    shafts=[]
    for n in preserved:
        if n.startswith('SupportShaft'): shafts.append({'name':n,'signature_unchanged':True})
    assert len(shafts)==4
    contacts=[]
    for other in ['RearServicePanel','RearArmourCheekLeft','RearArmourCheekRight','RearRecessLiner','RearRailCarrier']:
        t=d.getObject(other).Shape;contacts.append({'objects':[name,other],'gap_mm':shape.distToShape(t)[0],'overlap_mm3':shape.common(t).Volume})
    meshes['fcstd_sha256']=digest(model);(a.output/'meshes.json').write_text(json.dumps(meshes))
    report={'baseline_fcstd_sha256':baseline,'fcstd_sha256':meshes['fcstd_sha256'],'width_mm':a.width,'changed_objects':[name],'preserved_objects':preserved,'shafts':shafts,'contacts':contacts,'source_sha256':digest(Path(__file__)),'script_sha256':digest(Path(__file__)),'status':'isolated rear-frame width candidate; fixed-view review pending'}
    (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');App.closeDocument(d.Name);print(model,flush=True)
if __name__=='__main__':main()
