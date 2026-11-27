"""Compare a physical cyan rail and metal reflector with a second-emitter hypothesis.

Reference bright/dim strips need not be two physical lamps. Fixed cameras,
materials and saved solids let both hypotheses be inspected without image edits.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import box, rounded_plate, cylinder, tube
from experiment_drone_cavity_proportion import cavity_parts
from experiment_drone_rear_cavity import signature


def emitter_parts(dual=False, curved=False):
    parts={}
    def add(name,label,shape,color,material):parts[name]=(label,shape,color,material)
    for side,suffix,label in [(1,'Left','左'),(-1,'Right','右')]:
        x=side*65.36773626
        def capsule(y,r=1.5):
            return cylinder(r,32,(x,y,141)).fuse(Part.makeSphere(r,App.Vector(x,y,141))).fuse(Part.makeSphere(r,App.Vector(x,y,173))).removeSplitter()
        primary=(tube([(x,231,176),(x,234.6,175),(x,236.50410262,172),
                       (x,236.50410262,147),(x,235.6,142),(x,231,138)],1.5)
                 if curved else capsule(236.50410262))
        add('RearCavityEmitter'+suffix,label+'后凹舱圆头灯条',primary,(.05,.90,.94),'emission')
        backing=rounded_plate(9,42,2,(x-4.5,229.8,136),2)
        add('RearCavityReflector'+suffix,label+'后凹舱金属反射背板',backing,(.42,.45,.43),'metal')
        for name,z in [('Upper',173.5 if curved else 173.8),('Lower',136.8)]:
            clip=rounded_plate(9,4.2,10.5,(x-4.5,230,z),1.6)
            # Rounded recess locates the capsule; a small interference models
            # an appearance clamp rather than a floating rectangular cover.
            clip=clip.cut(cylinder(1.35,7,(x,236.50410262,z-1)))
            add('RearCavityClip'+name+suffix,label+'后凹舱'+('上' if name=='Upper' else '下')+'灯条压座',clip,(.055,.065,.06),'metal')
        if dual:
            secondary=capsule(226.5,1.1)
            # Small end shoes make the second-emitter hypothesis real geometry.
            for z in (139.9,172):secondary=secondary.fuse(box(2.2,5.5,2,(x-1.1,226.5,z)))
            add('RearCavitySecondary'+suffix,label+'后凹舱内侧候选灯条',secondary.removeSplitter(),(.05,.90,.94),'emission')
    return parts


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-model',type=Path,required=True);p.add_argument('--base-meshes',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--dual',action='store_true');p.add_argument('--curved',action='store_true')
    a=p.parse_args();out=a.output
    if out.exists() and any(out.iterdir()):raise ValueError('Use an empty candidate directory')
    mesh=json.loads(a.base_meshes.read_text());base_hash=hashlib.sha256(a.base_model.read_bytes()).hexdigest()
    if mesh['fcstd_sha256']!=base_hash:raise ValueError('Baseline model/mesh mismatch')
    out.mkdir(parents=True,exist_ok=True);d=App.openDocument(str(a.base_model))
    changed=cavity_parts(138,76,192,0,True)
    # Replace long thin vertical emitters by a fitted circular rail; keep the
    # upper and lower luminous corners as separate closed parts.
    frame=changed['RearCyanFrame'].cut(box(200,400,81,(-100,0,94)))
    solids=sorted(frame.Solids,key=lambda s:s.CenterOfMass.z)
    if len(solids)!=2:raise ValueError('Expected upper and lower frame pieces')
    changed['RearCyanFrame']=solids[1]
    added=emitter_parts(a.dual,a.curved)
    added['RearCyanLowerFrame']=('后凹舱下部灯框',solids[0],(.05,.90,.94),'emission')
    envelope=None
    if a.curved:
        wires=[]
        for z,rx,ry,dy in [(0,49,49,0),(28,70,66,-1),(60,68,66,1),(94.81,53.82,53.82,-1.15)]:
            points=[App.Vector((rx+.3)*math.cos(i*math.tau/128),dy+(ry+.3)*math.sin(i*math.tau/128),z) for i in range(128)]
            curve=Part.BSplineCurve();curve.interpolate(points,PeriodicFlag=True);wires.append(Part.Wire([curve.toShape()]))
        envelope=Part.makeLoft(wires,True,False)
        axis=App.Vector(0,.574,-.819);axis.normalize()
        envelope.Placement=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
        if d.getObject('BassNozzleShell').Shape.cut(envelope).Volume>1e-5:raise ValueError('Envelope fails to contain saved shell')
        upper=sorted(changed['RearCyanFrame'].cut(envelope).Solids,key=lambda q:q.CenterOfMass.x)
        lower=sorted(added['RearCyanLowerFrame'][1].cut(envelope).Solids,key=lambda q:q.CenterOfMass.x)
        if len(upper)!=2 or len(lower)!=2:raise ValueError('Expected four clear corner emitters')
        changed['RearCyanFrame']=upper[0]
        del added['RearCyanLowerFrame']
        for name,label,s in [('RearCyanUpperLeft','后凹舱左上灯角',upper[1]),('RearCyanLowerRight','后凹舱右下灯角',lower[0]),('RearCyanLowerLeft','后凹舱左下灯角',lower[1])]:
            added[name]=(label,s,(.05,.90,.94),'emission')
        for name,(label,s,color,material) in list(added.items()):
            if name.startswith('RearCavity'):added[name]=(label,s.cut(envelope),color,material)
    for name,s in changed.items():d.getObject(name).Shape=s
    for name,(label,s,color,material) in added.items():
        obj=d.addObject('Part::Feature',name);obj.Label=label;obj.Shape=s
        obj.addProperty('App::PropertyString','RenderMaterial');obj.RenderMaterial=material
        mesh['objects'].append({'name':name,'color':color,'material':material})
    for item in mesh['objects']:
        if item['name'] not in changed and item['name'] not in added:continue
        s=d.getObject(item['name']).Shape;s.check(True)
        if not s.isValid() or len(s.Solids)!=1:raise ValueError('Invalid solid '+item['name'])
        vertices,faces=s.tessellate(.12);item['vertices']=[list(v) for v in vertices];item['faces']=faces
    d.recompute();model=out/'candidate.FCStd';d.saveAs(str(model));App.closeDocument(d.Name)
    saved=App.openDocument(str(model));base=App.openDocument(str(a.base_model));checks=[]
    for obj in saved.Objects:
        if not hasattr(obj,'Shape') or obj.Shape.isNull():continue
        original=base.getObject(obj.Name)
        same=signature(obj.Shape)==signature(original.Shape) if obj.Name not in changed and obj.Name not in added else None
        delta=obj.Shape.cut(original.Shape).Volume+original.Shape.cut(obj.Shape).Volume if obj.Name.startswith('SupportShaft') else None
        checks.append({'name':obj.Name,'valid':obj.Shape.isValid(),'closed':all(s.isClosed() for s in obj.Shape.Solids),
                       'solids':len(obj.Shape.Solids),'unchanged_geometry_signature_6dp':same,'shaft_symmetric_difference_mm3':delta})
    if any(not c['valid'] or not c['closed'] or c['unchanged_geometry_signature_6dp'] is False or (c['shaft_symmetric_difference_mm3'] or 0)>1e-6 for c in checks):raise ValueError('Saved geometry check failed')
    shell=saved.getObject('BassNozzleShell').Shape;contacts=[]
    for suffix in ('Left','Right'):
        emitter=saved.getObject('RearCavityEmitter'+suffix).Shape
        for target in ('RearCavityClipUpper'+suffix,'RearCavityClipLower'+suffix):
            s=saved.getObject(target).Shape
            contacts.append({'objects':['RearCavityEmitter'+suffix,target],'gap_mm':emitter.distToShape(s)[0],'overlap_mm3':emitter.common(s).Volume})
    intersections=[{'name':n,'shell_overlap_mm3':saved.getObject(n).Shape.common(shell).Volume} for n in list(changed)+list(added)]
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(out/'meshes.json').write_text(json.dumps(mesh))
    result={'baseline_fcstd_sha256':base_hash,'fcstd_sha256':mesh['fcstd_sha256'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'dual_emitter_hypothesis':a.dual,'curved_rails_and_envelope_clearance':a.curved,'changed_objects':list(changed),'added_objects':list(added),'saved_readback':checks,
        'primary_emitter_clamp_contacts':contacts,'shell_intersections':intersections,
        'status':'isolated hypothesis; fixed-camera visual review pending','gui_state_present':False,
        'limitations':['dim inner trace may be reflection rather than a second lamp','hidden intersections not cleared for manufacture']}
    (out/'candidate-check.json').write_text(json.dumps(result,indent=2)+'\n');print(model,flush=True)


if __name__=='__main__':main()
