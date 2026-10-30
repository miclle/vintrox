"""Saved-CAD cavity proportion trials with unchanged nozzle and support shafts."""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App
from drone_concept import rounded_plate, rounded_frame, rear_raked_slab, cylinder, profile, box
from experiment_drone_rear_cavity import signature


def cavity_parts(width, bottom, top, light_recess=0, split_light=False):
    height=top-bottom
    slab=rear_raked_slab
    def frame(w,h,z,border,radius,front,back):
        return rounded_frame(w,h,400,border,(-w/2,0,z),radius).common(slab(front,back,z,z+h,w/2))
    axis=App.Vector(0,.574,-.819);axis.normalize()
    bore=cylinder(50,180,tuple(App.Vector(0,180,173)-axis*40),tuple(axis))
    panel=rounded_plate(178.6,173.68,400,(-89.3,0,60.12),3.36).common(slab(218.75,244,60.12,233.8,89.3))
    opening=rounded_plate(width,height,400,(-width/2,0,bottom),8)
    backing=slab(220,223,bottom-2,top+2,width/2+2).cut(bore)
    walls=slab(222,244,bottom-2,top+2,width/2+2).cut(opening)
    lip=frame(width+4,height+4,bottom-2,2,10,242,247)
    seat=frame(width+4,height+4,bottom-2,4,10,238-light_recess,240-light_recess)
    liner=backing.fuse(walls).fuse(lip).fuse(seat).removeSplitter()
    slope=profile([(150,58),(228,126),(224.7,129.8),(146.7,61.8)],'YZ',(-100.8,0,0),201.6)
    clearance=slab(223,330,bottom-2,top+2,width/2).common(opening)
    light=frame(width-1,height-1,bottom+.5,1.6,7.5,239.8-light_recess,241.2-light_recess)
    if split_light:light=light.cut(box(200,400,45,(-100,0,94)))
    return {'RearServicePanel':panel.cut(bore).cut(opening),'RearRecessLiner':liner,
            'RearCyanFrame':light,
            'RearLowerSlope':slope.cut(clearance)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-model',type=Path,required=True)
    p.add_argument('--base-meshes',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--width',type=float,required=True)
    p.add_argument('--bottom',type=float,required=True)
    p.add_argument('--top',type=float,required=True)
    p.add_argument('--light-recess',type=float,default=0)
    p.add_argument('--split-light',action='store_true')
    args=p.parse_args();out=args.output
    if out.exists() and any(out.iterdir()):raise ValueError('Use an empty output directory')
    mesh=json.loads(args.base_meshes.read_text());base_hash=hashlib.sha256(args.base_model.read_bytes()).hexdigest()
    if mesh['fcstd_sha256']!=base_hash:raise ValueError('Baseline hash mismatch')
    out.mkdir(parents=True,exist_ok=True)
    doc=App.openDocument(str(args.base_model));parts=cavity_parts(args.width,args.bottom,args.top,args.light_recess,args.split_light)
    for name,s in parts.items():
        s.check(True)
        expected=2 if args.split_light and name=='RearCyanFrame' else 1
        if not s.isValid() or len(s.Solids)!=expected:raise ValueError('Invalid candidate '+name)
        doc.getObject(name).Shape=s
        item=next(i for i in mesh['objects'] if i['name']==name)
        vertices,faces=s.tessellate(.12);item['vertices']=[list(v) for v in vertices];item['faces']=faces
    doc.recompute();model=out/'candidate.FCStd';doc.saveAs(str(model));App.closeDocument(doc.Name)
    saved=App.openDocument(str(model));base=App.openDocument(str(args.base_model));checks=[]
    for obj in saved.Objects:
        if not hasattr(obj,'Shape') or obj.Shape.isNull():continue
        original=base.getObject(obj.Name).Shape;s=obj.Shape
        delta=s.cut(original).Volume+original.cut(s).Volume if obj.Name.startswith('SupportShaft') else None
        same=signature(s)==signature(original) if obj.Name not in parts else None
        checks.append({'name':obj.Name,'valid':s.isValid(),'solids':len(s.Solids),
                       'unchanged_geometry_signature_6dp':same,'shaft_symmetric_difference_mm3':delta})
    if any(not c['valid'] or c['unchanged_geometry_signature_6dp'] is False or (c['shaft_symmetric_difference_mm3'] or 0)>1e-6 for c in checks):raise ValueError('Saved geometry check failed')
    liner=saved.getObject('RearRecessLiner').Shape
    contacts=[]
    for name in ('RearCyanFrame','RearServicePanel','RearLowerSlope'):
        s=saved.getObject(name).Shape
        contacts.append({'name':name,'gap_mm':s.distToShape(liner)[0],'overlap_mm3':s.common(liner).Volume})
    if any(c['gap_mm']>.01 or c['overlap_mm3']<.001 for c in contacts):raise ValueError('Detached cavity part')
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest()
    (out/'meshes.json').write_text(json.dumps(mesh))
    result={'baseline_fcstd_sha256':base_hash,'fcstd_sha256':mesh['fcstd_sha256'],
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'width_mm':args.width,'bottom_z_mm':args.bottom,'top_z_mm':args.top,'light_recess_mm':args.light_recess,'split_light':args.split_light,
            'changed_objects':list(parts),'saved_readback':checks,'contacts':contacts,
            'status':'isolated candidate; multi-view review pending','gui_state_present':False}
    (out/'candidate-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(model,flush=True)


if __name__=='__main__':main()
