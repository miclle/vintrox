"""Joint rear width and side-view profile study, using actual scaled BReps.

The existing manual side-frame fit assumed X116.76. Reproject its Y/Z profile
onto another parallel X plane while retaining all calibrated cameras. The
reference eye defines a uniform CAD scale, not an image transform. Controls,
nozzle, screen, ring-connected wires and supports stay at their saved stations.
Candidates are exploratory; connection regressions are reported, not hidden.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part
from drone_concept import profile, box
from experiment_drone_rear_cavity import signature

PREFIXES=('SideClosure','SideMechanicalBacking','SideGuard','SideFrameShoe',
          'SideFrameBolt','CyanSideTube','SideFrontSpine')


def shoulders(outer_x,scale,eye_y,eye_z):
    def rear_y(z,y,knee,slope,radius=8):
        angle=math.atan(slope);d=radius*math.tan(angle/2)
        top=knee+d;bottom=knee-d/math.sqrt(1+slope*slope)
        if z>=top:return y
        if z<=bottom:return y+(z-knee)*slope
        return y-radius+math.sqrt(radius*radius-(z-top)**2)
    map_z=lambda z:eye_z+scale*(z-eye_z)
    stations=sorted(set([map_z(z) for z in [67.3,100,123,125,127,129,131,133,135,137,139,141,143,145,180,222]]+
                        [125,127,129,131,133,135,137,139,141,143,145]))
    result={}
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        wires=[]
        for z in stations:
            back=rear_y(z,248,134,.98)
            original_z=eye_z+(z-eye_z)/scale
            original_y=rear_y(original_z,230.5125,136.2828,64.325/69.4764)
            edge=eye_y+scale*(original_y-eye_y)
            rx=outer_x-89;ry=back-edge
            def curve(inset,reverse=False):
                pts=[App.Vector(side*(89+(rx-inset)*math.sin(i*math.pi/32)),edge+(ry-inset)*math.cos(i*math.pi/32),z) for i in range(17)]
                if reverse:pts.reverse()
                spline=Part.BSplineCurve();spline.interpolate(pts)
                return spline.toShape(),pts
            outer,op=curve(0);inner,ip=curve(3.5,True)
            ot=op[-1]+App.Vector(0,-4*scale,0);it=ip[0]+App.Vector(0,-4*scale,0)
            wires.append(Part.Wire([outer,Part.makeLine(op[-1],ot),Part.makeLine(ot,it),Part.makeLine(it,ip[0]),inner,Part.makeLine(ip[-1],op[0])]))
        result['RearArmourCheek'+suffix]=Part.makeLoft(wires,True,True)
    return result


def main():
    p=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','cameras','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--outer-x',type=float,choices=[108,102],required=True)
    p.add_argument('--normalize-guard',action='store_true',help='Reparameterize the cut guard before the same advanced check')
    p.add_argument('--preserve-handle-seats',action='store_true')
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use an empty candidate directory')
    mesh=json.loads(a.base_meshes.read_text());base_hash=hashlib.sha256(a.base_model.read_bytes()).hexdigest()
    if mesh['fcstd_sha256']!=base_hash:raise ValueError('Baseline mesh mismatch')
    cameras=json.loads(a.cameras.read_text());eye=next(v['eye_mm'] for v in cameras['views'] if v['source_frame']==180)
    scale=(a.outer_x-eye[0])/(116.76-eye[0])
    d=App.openDocument(str(a.base_model));parts={}
    for item in mesh['objects']:
        name=item['name']
        if not name.startswith(PREFIXES):continue
        side=-1 if 'Left' in name else 1
        s=d.getObject(name).Shape.copy()
        s.translate(App.Vector(side*4,0,0))
        s.scale(scale)
        s.translate(App.Vector(side*(a.outer_x-scale*116.76),eye[1]*(1-scale),eye[2]*(1-scale)))
        if a.preserve_handle_seats and name.startswith('SideClosure'):
            seat=d.getObject(name).Shape.common(box(40,21,5,((90 if side>0 else -130),98.5,223)))
            s=s.fuse(seat)
        parts[name]=s
    parts.update(shoulders(a.outer_x,scale,eye[1],eye[2]))
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
        mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
        def wire(points,x):
            vs=[App.Vector(x,y,z) for y,z in points];return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
        pocket=profile(inner,'YZ',(side*94.6,0,0),side*25)
        flared=Part.makeLoft([wire(inner,side*94.6),wire(mouth,side*117)],True,True)
        for prefix in ['SideClosure','SideMechanicalBacking','RearArmourCheek']:
            name=prefix+suffix;parts[name]=parts[name].cut(pocket).cut(flared)
        relief=profile([(212,140),(239,140),(239,189),(212,189)],'YZ',(side*90,0,0),side*30)
        name='SideGuard'+suffix;parts[name]=parts[name].cut(relief)
        if a.normalize_guard:parts[name]=parts[name].toNurbs().removeSplitter()
    checks=[]
    for name,s in parts.items():
        print('CHECK',name,flush=True);s.check(True)
        if not s.isValid() or not s.Solids or not all(q.isClosed() for q in s.Solids):raise ValueError(name)
        d.getObject(name).Shape=s
        item=next(i for i in mesh['objects'] if i['name']==name);vertices,faces=s.tessellate(.12)
        item['vertices']=[list(v) for v in vertices];item['faces']=faces
        checks.append({'name':name,'valid':True,'advanced_check_passed':True,'solids':len(s.Solids)})
    a.output.mkdir(parents=True,exist_ok=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
    saved=App.openDocument(str(model));base=App.openDocument(str(a.base_model))
    preserved=[]
    for obj in saved.Objects:
        if not hasattr(obj,'Shape') or obj.Shape.isNull() or obj.Name in parts:continue
        old=base.getObject(obj.Name).Shape
        same=signature(obj.Shape)==signature(old)
        delta=obj.Shape.cut(old).Volume+old.cut(obj.Shape).Volume if obj.Name.startswith('SupportShaft') else None
        preserved.append({'name':obj.Name,'unchanged_geometry_signature_6dp':same,'shaft_difference_mm3':delta})
    if any(not x['unchanged_geometry_signature_6dp'] or (x['shaft_difference_mm3'] or 0)>1e-6 for x in preserved):raise ValueError('Unrelated shape changed')
    contacts=[]
    for suffix in ['Left','Right']:
        for left,right in [('RearArmourCheek'+suffix,'RearStructuralFrame'),('RearArmourCheek'+suffix,'SideGuard'+suffix),
                           ('SideGuard'+suffix,'SideClosure'+suffix),('HandleArm'+suffix,'SideClosure'+suffix),
                           ('CyanSideTube'+suffix,'SideGuard'+suffix)]:
            x=saved.getObject(left).Shape;y=saved.getObject(right).Shape
            contacts.append({'objects':[left,right],'gap_mm':x.distToShape(y)[0],'overlap_mm3':x.common(y).Volume})
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(a.output/'meshes.json').write_text(json.dumps(mesh))
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':base_hash,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(a.cameras.read_bytes()).hexdigest(),'outer_x_mm':a.outer_x,'cad_uniform_scale':scale,
            'reprojection_eye_mm':eye,'normalize_guard':a.normalize_guard,'preserve_handle_seats':a.preserve_handle_seats,'changed_objects':list(parts),'parts':checks,'preserved':preserved,'contacts':contacts,
            'status':'exploratory candidate; connector, light radius and fixed-control fit require review',
            'limitations':['uses the existing frame-180 plane assumption to recover its Y/Z profile','both sides assumed symmetric','uniform CAD scale also changes local thickness and radii slightly','not a final manufacturing or GUI delivery']}
    (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(model,flush=True)


if __name__=='__main__':main()
