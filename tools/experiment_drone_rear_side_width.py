"""Joint side-cladding station and rear-shoulder trials in real saved CAD.

Side-profile fitting previously fixed the X mounting station by assumption.
Translate the connected side trim without distorting its Y/Z profile, and
rebuild the shoulder to keep its connection to the unshifted rear frame.
"""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import profile, cylinder, box
from experiment_drone_rear_shoulders import rear_shoulders
from experiment_drone_rear_cavity import signature

# Wires terminate at the unchanged speaker ring; retain their original station.
PREFIXES=('SideClosure','SideMechanicalBacking','SideGuard','SideFrameShoe','SideFrameBolt','CyanSideTube','SideFrontSpine')


def rebuilt_side_closure(side):
    """Recreate planar extrusion before rounding, avoiding affine 3D fillets.

    The Y/Z perimeter retains the existing transformed corner curves. The
    thickness-edge fillet is now a true 2.1mm world-space radius; this is an
    intentional small geometric change, not a lossless normalization.
    """
    outline=[(54.4,187.9),(69.67,241.01),(171.39,244.33),(183.98,232.58),
             (184.41,133.67),(132.95,50.96),(80.38,49.36),(53.38,72.45)]
    source=profile(outline,'YZ',(0,0,0),1)
    source=source.makeFillet(10,[e for e in source.Edges if e.BoundBox.XLength>.99])
    face=min((f for f in source.Faces if abs(f.normalAt(0,0).x)>.99),key=lambda f:f.CenterOfMass.x)
    matrix=App.Matrix();matrix.A22=1.25;matrix.A33=.84;matrix.A34=24;matrix.A14=side*100.8
    wire=Part.Wire(face.OuterWire.transformGeometry(matrix).Edges)
    result=Part.Face(wire).extrude(App.Vector(side*12.6,0,0))
    result=result.makeFillet(2.1,[e for e in result.Edges if e.BoundBox.XLength<.01])
    result=result.cut(cylinder(64,17,(side*100,129.09686,153.62312),(side,0,0)))
    result=result.cut(cylinder(21.2,23,(side*97.8,192.27910630805997,201.20766206780763),(side,0,0)))
    inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
    mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
    def section(points,x):
        vs=[App.Vector(x,y,z) for y,z in points]
        return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
    result=result.cut(profile(inner,'YZ',(side*94.6,0,0),side*25))
    return result.cut(Part.makeLoft([section(inner,side*94.6),section(mouth,side*117)],True,True))


def rebuilt_side_bolt(side,index):
    """Analytic elliptical extrusion with the original scaled screwdriver slot."""
    y,z=((83,62),(115,62),(178,229),(70,223))[index]
    radius=1.7 if index<2 else 2.6
    center=App.Vector(side*139*.84,y*1.25,z*.84+24)
    ellipse=Part.Ellipse(center+App.Vector(0,radius*1.25,0),center+App.Vector(0,0,radius*.84),center)
    result=Part.Face(Part.Wire([ellipse.toShape()])).extrude(App.Vector(side*1.8*.84,0,0))
    slot=box(radius*1.2,.9,2.8,(-radius*.6,-.45,-.5))
    slot.rotate(App.Vector(),App.Vector(0,0,1),25)
    slot.Placement=App.Placement(App.Vector(side*139,y,z),App.Rotation(App.Vector(0,0,1),App.Vector(side,0,0))).multiply(slot.Placement)
    matrix=App.Matrix();matrix.A11=.84;matrix.A22=1.25;matrix.A33=.84;matrix.A34=24
    return result.cut(slot.transformGeometry(matrix))


def main():
    p=argparse.ArgumentParser();p.add_argument('--base-model',type=Path,required=True);p.add_argument('--base-meshes',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--inset',type=float,required=True)
    p.add_argument('--fixed-status-aperture',action='store_true',help='Keep the cavity mouth aligned with the unchanged status marks')
    p.add_argument('--status-relief-front-y',type=float,default=225,help='Front edge of the guard notch around the status marks')
    p.add_argument('--preserve-handle-seats',action='store_true',help='Retain the original local mounting faces beneath the handle arms')
    a=p.parse_args();out=a.output
    if not 0<a.inset<11:raise ValueError('Use a positive exploratory inset below 11mm')
    if out.exists() and any(out.iterdir()):raise ValueError('Use an empty output directory')
    mesh=json.loads(a.base_meshes.read_text());base_hash=hashlib.sha256(a.base_model.read_bytes()).hexdigest()
    if mesh['fcstd_sha256']!=base_hash:raise ValueError('Baseline hash mismatch')
    out.mkdir(parents=True,exist_ok=True);d=App.openDocument(str(a.base_model));parts={};repairs=[]
    for item in mesh['objects']:
        name=item['name']
        if not name.startswith(PREFIXES):continue
        side=-1 if 'Left' in name else 1 if 'Right' in name else None
        if side is None:raise ValueError('Missing explicit side: '+name)
        original=d.getObject(name).Shape
        if name.startswith('SideClosure'):
            s=rebuilt_side_closure(side)
        elif name.startswith('SideGuard'):
            s=original.toNurbs()
        elif name.startswith('SideFrameBolt'):
            s=rebuilt_side_bolt(side,int(name[-1]))
        else:s=original.copy()
        if name.startswith(('SideClosure','SideGuard','SideFrameBolt')):
            s.check(True)
            method='world-space planar extrusion with 2.1mm edge fillets' if name.startswith('SideClosure') else 'analytic elliptical extrusion' if name.startswith('SideFrameBolt') else 'toNurbs'
            repairs.append({'name':name,'method':method,
                            'volume_delta_mm3':s.Volume-original.Volume,'symmetric_difference_mm3':s.cut(original).Volume+original.cut(s).Volume,
                            'boolean_difference_is_diagnostic_only':True,
                            'advanced_check_passed':True,'original_solids':len(original.Solids),'rebuilt_solids':len(s.Solids)})
        seat=s.common(box(40,21,5,((90 if side>0 else -130),98.5,223))) if a.preserve_handle_seats and name.startswith('SideClosure') else None
        s.translate(App.Vector(-side*a.inset,0,0))
        if seat is not None:s=s.fuse(seat)
        parts[name]=s
    cheeks=rear_shoulders(116.76-a.inset,add_returns=False)
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
        mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
        aperture_inset=0 if a.fixed_status_aperture else a.inset
        pocket=profile(inner,'YZ',(side*(94.6-aperture_inset),0,0),side*25)
        def wire(points,x):
            vs=[App.Vector(x,y,z) for y,z in points];return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
        flared=Part.makeLoft([wire(inner,side*(94.6-aperture_inset)),wire(mouth,side*(117-aperture_inset))],True,True)
        name='RearArmourCheek'+suffix;parts[name]=cheeks[name].cut(pocket).cut(flared)
        if a.fixed_status_aperture:
            for prefix in ['SideClosure','SideMechanicalBacking']:
                name=prefix+suffix;parts[name]=parts[name].cut(pocket).cut(flared)
            front=a.status_relief_front_y
            relief=profile([(front,140),(239,140),(239,189),(front,189)],'YZ',(side*100,0,0),side*16.5)
            name='SideGuard'+suffix;parts[name]=parts[name].cut(relief)
    for name,s in parts.items():
        print('Advanced check:',name,flush=True)
        s.check(True)
        expected_solids=1 if name.startswith('RearArmourCheek') else len(d.getObject(name).Shape.Solids)
        if not s.isValid() or len(s.Solids)!=expected_solids:raise ValueError('Invalid shifted part '+name)
        d.getObject(name).Shape=s
        item=next(i for i in mesh['objects'] if i['name']==name);verts,faces=s.tessellate(.12)
        item['vertices']=[list(v) for v in verts];item['faces']=faces
    d.recompute();model=out/'candidate.FCStd';d.saveAs(str(model));App.closeDocument(d.Name)
    current=App.openDocument(str(model));base=App.openDocument(str(a.base_model));checks=[]
    for o in current.Objects:
        if not hasattr(o,'Shape') or o.Shape.isNull():continue
        old=base.getObject(o.Name).Shape;s=o.Shape
        same=signature(s)==signature(old) if o.Name not in parts else None
        delta=s.cut(old).Volume+old.cut(s).Volume if o.Name.startswith('SupportShaft') else None
        checks.append({'name':o.Name,'valid':s.isValid(),'solids':len(s.Solids),'closed':all(q.isClosed() for q in s.Solids),
                       'unchanged_geometry_signature_6dp':same,'shaft_symmetric_difference_mm3':delta})
    if any(not c['valid'] or not c['closed'] or c['unchanged_geometry_signature_6dp'] is False or (c['shaft_symmetric_difference_mm3'] or 0)>1e-6 for c in checks):raise ValueError('Saved preservation failed')
    contacts=[]
    for suffix in ['Left','Right']:
        pairs=[('RearArmourCheek'+suffix,'RearStructuralFrame'),('RearArmourCheek'+suffix,'SideGuard'+suffix),
               ('SideGuard'+suffix,'SideClosure'+suffix),('SideFrameShoe'+suffix,'SideGuard'+suffix),('CyanSideTube'+suffix,'SideGuard'+suffix)]
        if a.preserve_handle_seats:pairs.append(('HandleArm'+suffix,'SideClosure'+suffix))
        for l,r in pairs:
            x=current.getObject(l).Shape;y=current.getObject(r).Shape
            contacts.append({'objects':[l,r],'gap_mm':x.distToShape(y)[0],'overlap_mm3':x.common(y).Volume})
    if any(c['gap_mm']>.01 for c in contacts):raise ValueError('Detached rear/side joint')
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(out/'meshes.json').write_text(json.dumps(mesh))
    report={'baseline_fcstd_sha256':base_hash,'fcstd_sha256':mesh['fcstd_sha256'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'side_station_inset_mm':a.inset,'fixed_status_aperture':a.fixed_status_aperture,'status_relief_front_y_mm':a.status_relief_front_y,'preserve_handle_seats':a.preserve_handle_seats,'shoulder_outer_x_mm':116.76-a.inset,'changed_objects':list(parts),'saved_readback':checks,'contacts':contacts,'baseline_curve_repairs':repairs,
            'status':'isolated real-CAD candidate; multi-view and side-status review pending','gui_state_present':False,
            'limitations':['side X station is inferred, not measured','ring/wing/socket/status controls and ring-connected wires stay at baseline stations to expose fit conflicts','unchanged legacy wires retain recorded advanced BRep errors; candidate is not a manufacturing release','contacts do not establish manufacture or full visual acceptance']}
    (out/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(model,flush=True)


if __name__=='__main__':main()
