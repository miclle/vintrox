"""Isolated saved-CAD petal candidates; never replaces the delivery model.

A rotates the assembly and B also refines the leaf; both inadvertently rotate
the oblique terminal plane and are diagnostic only. C changes phase within each
section, retaining the terminal circle, and adds the stepped central strap.
D tests twelve broader leaves against the original sixteen-leaf assumption. Dimensions
are appearance assumptions, not manufacturing specifications.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import FreeCAD as App
from drone_concept import cylinder, nozzle_leaf_parts as refined_leaf_parts
from experiment_drone_rear_cavity import signature




def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-model',type=Path,required=True)
    p.add_argument('--base-meshes',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--variant',choices=('a','b','c','d'),required=True)
    p.add_argument('--phase-degrees',type=float,default=11.25)
    args=p.parse_args();out=args.output
    if out.exists() and any(out.iterdir()):raise ValueError('Use a new candidate directory')
    out.mkdir(parents=True,exist_ok=True)
    mesh=json.loads(args.base_meshes.read_text());base_hash=hashlib.sha256(args.base_model.read_bytes()).hexdigest()
    if mesh['fcstd_sha256']!=base_hash:raise ValueError('Baseline model/mesh mismatch')
    d=App.openDocument(str(args.base_model))
    axis=App.Vector(0,.574,-.819);axis.normalize()
    frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
    spin=App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),args.phase_degrees))
    replacement={}
    count=12 if args.variant=='d' else 16
    pitch=360/count
    if args.variant in ('b','c','d'):
        for i in range(count):replacement.update(refined_leaf_parts(i,args.phase_degrees if args.variant in ('c','d') else 0,args.variant in ('c','d'),pitch))
    if args.variant=='d':
        for i in range(count):
            t=math.radians(i*pitch+args.phase_degrees+pitch/2)
            radial=(math.cos(t),math.sin(t),0);tangent=(-math.sin(t),math.cos(t),0)
            replacement[f'NozzlePetalHinge{i}']=cylinder(1.3,6,(51.5*radial[0]-3*tangent[0],-1.149+51.5*radial[1]-3*tangent[1],95.8),tangent)
    removed=[]
    for obj in list(d.Objects):
        m=re.match(r'NozzlePetal(?:Inset|Ridge|EdgeRail|Guide|EndHem|Hinge)?(\d+)',obj.Name)
        if m and int(m[1])>=count:
            removed.append(obj.Name);d.removeObject(obj.Name)
    mesh['objects']=[item for item in mesh['objects'] if item['name'] not in removed]
    changed=[]
    for item in mesh['objects']:
        name=item['name']
        if not name.startswith('NozzlePetal'):continue
        obj=d.getObject(name)
        if name in replacement:s=replacement[name].copy()
        else:
            s=obj.Shape.copy();s.Placement=frame.inverse().multiply(s.Placement)
        if args.variant in ('c','d'):
            if name not in replacement:
                # Root hinges rotate within the first section plane, whose
                # center is offset from the main nozzle axis.
                s.rotate(App.Vector(0,-1.149,95.8),App.Vector(0,0,1),args.phase_degrees)
            s.Placement=frame.multiply(s.Placement)
        else:
            s.Placement=frame.multiply(spin).multiply(s.Placement)
        s.check(True)
        if not s.isValid() or len(s.Solids)!=1:raise ValueError('Invalid candidate: '+name)
        obj.Shape=s
        vertices,faces=s.tessellate(.12);item['vertices']=[list(v) for v in vertices];item['faces']=faces
        changed.append(name)
    d.recompute();model=out/'candidate.FCStd';d.saveAs(str(model));App.closeDocument(d.Name)
    # Independent saved readback and preservation are part of the candidate,
    # rather than inferred from the generation recipe.
    saved=App.openDocument(str(model));base=App.openDocument(str(args.base_model));checks=[]
    for obj in saved.Objects:
        if not hasattr(obj,'Shape') or obj.Shape.isNull():continue
        s=obj.Shape;original=base.getObject(obj.Name).Shape
        delta=s.cut(original).Volume+original.cut(s).Volume if obj.Name.startswith('SupportShaft') else None
        unchanged=(signature(s)==signature(original)) if obj.Name not in changed else None
        checks.append({'name':obj.Name,'valid':s.isValid(),'solids':len(s.Solids),'unchanged_geometry_signature_6dp':unchanged,'shaft_symmetric_difference_mm3':delta})
    if any(not c['valid'] or c['unchanged_geometry_signature_6dp'] is False or (c['shaft_symmetric_difference_mm3'] or 0)>1e-6 for c in checks):raise ValueError('Saved candidate failed')
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest()
    (out/'meshes.json').write_text(json.dumps(mesh))
    (out/'candidate-check.json').write_text(json.dumps({'variant':args.variant,'phase_degrees':args.phase_degrees,'petal_count':count,'removed_objects':removed,'base_fcstd_sha256':base_hash,'fcstd_sha256':mesh['fcstd_sha256'],'changed_objects':changed,'saved_readback':checks,'status':'exploratory; full delivery and visual review pending','gui_state_present':False},indent=2)+'\n')
    App.closeDocument(saved.Name);App.closeDocument(base.Name);print(model,flush=True)


if __name__=='__main__':main()
