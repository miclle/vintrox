"""Compare rear-shoulder sections and isolate rear-frame surface overlap.

A/B-style narrowing with recessed returns is exploratory; later candidates
reapply the side-status opening or retain baseline shoulders entirely. Trimming
common faces repairs actual geometry rather than changing renderer settings.
Candidate FCStd files are not GUI/STEP deliveries.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import FreeCAD as App
import Part
from experiment_drone_rear_cavity import signature
from drone_concept import profile, box, rounded_plate


def rear_shoulders(outer_x, edge_y=230.5125, add_returns=True):
    def rear_y(z,y,h,s,r=8):
        angle=math.atan(s);d=r*math.tan(angle/2)
        top=h+d;bottom=h-d/math.sqrt(1+s*s)
        if z>=top:return y
        if z<=bottom:return y+(z-h)*s
        return y-r+math.sqrt(r*r-(z-top)**2)
    result={}
    stations=(67.3,100,123,125,127,129,131,133,135,137,139,141,143,145,180,222)
    for side,suffix in ((-1,'Left'),(1,'Right')):
        wires=[];returns=[]
        for z in stations:
            back=rear_y(z,248,134,.98)
            edge=rear_y(z,edge_y,136.2828,64.325/69.4764)
            rx=outer_x-89;ry=back-edge
            def curve(inset,reverse=False):
                points=[App.Vector(side*(89+(rx-inset)*math.sin(a)),edge+(ry-inset)*math.cos(a),z)
                        for a in [i*math.pi/2/16 for i in range(17)]]
                if reverse:points.reverse()
                spline=Part.BSplineCurve();spline.interpolate(points)
                return spline.toShape(),points
            outer,op=curve(0);inner,ip=curve(3.5,True)
            ot=op[-1]+App.Vector(0,-4,0);it=ip[0]+App.Vector(0,-4,0)
            wires.append(Part.Wire([outer,Part.makeLine(op[-1],ot),Part.makeLine(ot,it),Part.makeLine(it,ip[0]),inner,Part.makeLine(ip[-1],op[0])]))
            # The recessed crosswise return carries the narrowed gold shell
            # back to the existing side guard, leaving a visible depth step.
            points=[App.Vector(side*x,y,z) for x,y in [(outer_x-3.1,edge-4),(116.76,edge-4),(116.76,edge+.25),(outer_x-3.1,edge+.25)]]
            returns.append(Part.makePolygon(points+[points[0]]))
        result['RearArmourCheek'+suffix]=Part.makeLoft(wires,True,True)
        if add_returns:result['RearShoulderReturn'+suffix]=Part.makeLoft(returns,True,True)
    for name,shape in result.items():
        shape.check(True)
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid shoulder '+name)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-model',type=Path,required=True)
    p.add_argument('--base-meshes',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--outer-x',type=float,choices=(108,100.8,116.76),required=True)
    p.add_argument('--edge-y',type=float,default=230.5125)
    p.add_argument('--no-return',action='store_true')
    p.add_argument('--wide-carrier',action='store_true')
    p.add_argument('--trim-frame-overlap',action='store_true')
    p.add_argument('--carrier-only',action='store_true')
    p.add_argument('--open-frame-slots',action='store_true')
    p.add_argument('--status-clearance',action='store_true',help='Reapply the existing side-status aperture to rebuilt shoulders')
    args=p.parse_args();out=args.output
    if out.exists() and any(out.iterdir()):raise ValueError('Use an empty candidate directory')
    out.mkdir(parents=True,exist_ok=True)
    mesh=json.loads(args.base_meshes.read_text());base_hash=hashlib.sha256(args.base_model.read_bytes()).hexdigest()
    if mesh['fcstd_sha256']!=base_hash:raise ValueError('Baseline model/mesh hash mismatch')
    d=App.openDocument(str(args.base_model));parts={} if args.carrier_only else rear_shoulders(args.outer_x,args.edge_y,not args.no_return);added=[]
    if args.status_clearance:
        # Rebuilding the shoulder must preserve the original later-stage side
        # status opening; its flared aperture is a real cut, not transparency.
        for side,suffix in [(-1,'Left'),(1,'Right')]:
            inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
            mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
            pocket=profile(inner,'YZ',(side*94.6,0,0),side*25)
            def section(points,x):
                vs=[App.Vector(x,y,z) for y,z in points];return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
            flared=Part.makeLoft([section(inner,side*94.6),section(mouth,side*117)],True,True)
            for prefix in ['RearArmourCheek','RearShoulderReturn']:
                name=prefix+suffix
                if name in parts:parts[name]=parts[name].cut(pocket).cut(flared)
    if args.wide_carrier:
        rail_w,rail_h,rail_z=121.16123372,20.62114643,210.93081714
        carrier=box(201.6,21,44,(-100.8,227,191),2.5)
        carrier=carrier.cut(rounded_plate(rail_w+.5,rail_h+.5,5,(-rail_w/2-.25,245.5,rail_z-rail_h/2-.25),1.8))
        for side in (-1,1):carrier=carrier.cut(rounded_plate(13.5,2.8,2.1,(side*15.5-6.75,246.7,228),1.3))
        parts['RearRailCarrier']=carrier
    if args.open_frame_slots:
        frame=d.getObject('RearStructuralFrame').Shape.copy()
        for side in (-1,1):frame=frame.cut(rounded_plate(13.5,2.8,2.1,(side*15.5-6.75,246.7,228),1.3))
        parts['RearStructuralFrame']=frame
    if args.trim_frame_overlap:
        carrier=parts.get('RearRailCarrier',d.getObject('RearRailCarrier').Shape).copy()
        parts['RearRailCarrier']=carrier.cut(parts.get('RearStructuralFrame',d.getObject('RearStructuralFrame').Shape)).removeSplitter()
    original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    for name,shape in parts.items():
        shape.check(True)
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid final shoulder '+name)
        obj=d.getObject(name)
        if obj is None:
            obj=d.addObject('PartDesign::Feature',name);obj.Label='后肩内收连接板'+('左' if name.endswith('Left') else '右');added.append(name)
            mesh['objects'].append({'name':name,'label':obj.Label,'vertices':[],'faces':[],'color':[.06,.075,.065],'material':'metal'})
        obj.Shape=shape
    d.recompute();model=out/'candidate.FCStd';d.saveAs(str(model))
    for item in mesh['objects']:
        if item['name'] in parts:
            vertices,faces=d.getObject(item['name']).Shape.tessellate(.12)
            item['vertices']=[list(v) for v in vertices];item['faces']=faces
    App.closeDocument(d.Name);d=App.openDocument(str(model));base=App.openDocument(str(args.base_model))
    unchanged={name:signature(d.getObject(name).Shape)==value for name,value in original.items() if name not in parts}
    if not all(unchanged.values()):raise ValueError('Unrelated geometry changed')
    shafts=[]
    for name in original:
        if name.startswith('SupportShaft'):
            a=d.getObject(name).Shape;b=base.getObject(name).Shape
            shafts.append({'name':name,'symmetric_difference_mm3':a.cut(b).Volume+b.cut(a).Volume})
    if any(s['symmetric_difference_mm3']>1e-6 for s in shafts):raise ValueError('Protected support changed')
    contacts=[]
    for side in ('Left','Right'):
        pairs=[('RearArmourCheek'+side,'RearStructuralFrame')]
        pairs += [('RearArmourCheek'+side,'RearShoulderReturn'+side),('RearShoulderReturn'+side,'SideGuard'+side)] if not args.no_return else [('RearArmourCheek'+side,'SideGuard'+side)]
        for a,b in pairs:
            s,t=d.getObject(a).Shape,d.getObject(b).Shape
            contacts.append({'objects':[a,b],'gap_mm':s.distToShape(t)[0],'overlap_mm3':s.common(t).Volume})
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(out/'meshes.json').write_text(json.dumps(mesh))
    report={'base_fcstd_sha256':base_hash,'fcstd_sha256':mesh['fcstd_sha256'],'gold_outer_x_mm':args.outer_x,'side_join_y_mm':args.edge_y,'status_clearance_reapplied':args.status_clearance,'wide_carrier':args.wide_carrier,'frame_overlap_trimmed':args.trim_frame_overlap,'carrier_only':args.carrier_only,'frame_slots_opened':args.open_frame_slots,'changed_objects':[n for n in parts if n not in added],'added_objects':added,'contacts':contacts,'shafts':shafts,'unchanged_geometry_signatures':unchanged,'status':'exploratory; visible boundary and all-view review pending'}
    (out/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(model,flush=True)
    App.closeDocument(d.Name);App.closeDocument(base.Name)


if __name__=='__main__':main()
