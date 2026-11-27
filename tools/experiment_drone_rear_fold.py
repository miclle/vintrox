"""Explore wider rear fold blends; retain planes, cavity, nozzle and supports.

The three local constructors are scoped copies of the verified v43 constructors,
with only the rear fold radius made variable. No render or camera is transformed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import profile, rounded_frame, rounded_plate, cylinder
from experiment_drone_rear_cavity import signature

def rear_raked_slab(front, back, bottom, top, half_width, knee=134, fold_radius=8):
    """One rounded prism shared by the raked cavity and closure clearance."""
    shift=(bottom-knee)*.98
    section=[(front+shift,bottom),(back+shift,bottom),(back,knee),
             (back,top),(front,top),(front,knee)]
    shape=profile(section,'YZ',(-half_width,0,0),2*half_width)
    edges=[e for e in shape.Edges if e.BoundBox.XLength>2*half_width-.01
           and abs(e.CenterOfMass.z-knee)<.01]
    return shape.makeFillet(fold_radius,edges)

def raked_rear_parts(knee=134, outer_x=116.76, lower_rise=6, fold_radius=8):
    """Construct folded rear pieces and a curved side-to-back transition.

    Keeping each fold inside a single rounded prism avoids the invalid curve-on-
    surface boundaries produced by shearing and fusing trimmed NURBS halves.
    Corner radii and the hidden nozzle passage remain appearance assumptions.
    """
    slope = .98
    def slab(front, back, bottom, top, half_width):
        return rear_raked_slab(front,back,bottom,top,half_width,knee,fold_radius)
    def framed(w,h,z,border,radius,front,back):
        outline=rounded_frame(w,h,400,border,(-w/2,0,z),radius)
        return outline.common(slab(front,back,z,z+h,w/2))
    # Appearance-derived narrower back face and rounded side transition.
    # The shell backing overlaps the retained internal sloping skin.
    # Raise the lower cladding edge without thinning the rounded frame border
    # or moving the cavity, nozzle, shoulders and upper antenna connections.
    panel_bottom=60.12+lower_rise
    panel=rounded_plate(178.6,233.8-panel_bottom,400,(-89.3,0,panel_bottom),3.36)
    panel=panel.common(slab(218.75,244,panel_bottom,233.8,89.3))
    bore_axis=App.Vector(0,.574,-.819);bore_axis.normalize()
    bore=cylinder(50,180,tuple(App.Vector(0,180,173)-bore_axis*40),tuple(bore_axis))
    # The dark region around the nozzle is a recessed housing, not another
    # cylindrical nozzle wall. Open the cladding and retain an actual backing,
    # side walls, forward lip and recessed light mounting ledge. Dimensions are
    # appearance assumptions checked in both fixed rear-oblique cameras.
    opening=rounded_plate(138,116,400,(-69,0,76),8)
    backing=slab(220,223,74,194,71).cut(bore)
    walls=slab(222,244,74,194,71).cut(opening)
    lip=framed(142,120,74,2,10,242,247)
    light_seat=framed(142,120,74,4,10,238,240)
    liner=backing.fuse(walls).fuse(lip).fuse(light_seat).removeSplitter()
    parts={'RearServicePanel':panel.cut(bore).cut(opening),
           'RearStructuralFrame':framed(178,170-lower_rise,61.8+lower_rise,7.56,10.08,241.75,248),
           'RearCyanFrame':framed(137,115,76.5,1.6,7.5,239.8,241.2),
           'RearRecessLiner':liner}
    return parts


def reprojected_rear_shoulders(outer_x,scale,eye_y,eye_z,exponent=1.5, fold_radius=8):
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
            back=rear_y(z,248,134,.98,fold_radius)
            original_z=eye_z+(z-eye_z)/scale
            original_y=rear_y(original_z,230.5125,136.2828,64.325/69.4764)
            edge=eye_y+scale*(original_y-eye_y)
            rx=outer_x-89;ry=back-edge
            def curve(inset,reverse=False):
                pts=[App.Vector(side*(89+(rx-inset)*math.sin(i*math.pi/32)**(2/exponent)),edge+(ry-inset)*math.cos(i*math.pi/32)**(2/exponent),z) for i in range(17)]
                if reverse:pts.reverse()
                spline=Part.BSplineCurve();spline.interpolate(pts)
                return spline.toShape(),pts
            outer,op=curve(0);inner,ip=curve(3.5,True)
            ot=op[-1]+App.Vector(0,-4*scale,0);it=ip[0]+App.Vector(0,-4*scale,0)
            wires.append(Part.Wire([outer,Part.makeLine(op[-1],ot),Part.makeLine(ot,it),Part.makeLine(it,ip[0]),inner,Part.makeLine(ip[-1],op[0])]))
        result['RearArmourCheek'+suffix]=Part.makeLoft(wires,True,True)
    return result

def rear_fold_parts(radius):
    parts=raked_rear_parts(outer_x=108,fold_radius=radius)
    del parts['RearCyanFrame']  # All four retained light corners lie outside the bend.
    parts.update(reprojected_rear_shoulders(108,1.0089049846660512,
                 481.9590609254328,317.0386845391606,fold_radius=radius))
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        parts['RearStructuralFrame']=parts['RearStructuralFrame'].cut(
            rounded_plate(13.5,2.8,2.1,(side*15.5-6.75,246.7,228),1.3))
        inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
        mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
        def wire(points,x):
            vertices=[App.Vector(x,y,z) for y,z in points]
            return Part.Wire(Part.makePolygon(vertices+[vertices[0]]).Edges)
        pocket=profile(inner,'YZ',(side*94.6,0,0),side*25)
        flare=Part.makeLoft([wire(inner,side*94.6),wire(mouth,side*117)],True,True)
        name='RearArmourCheek'+suffix
        parts[name]=parts[name].cut(pocket).cut(flare)
    slope=profile([(150,58),(228,126),(224.7,129.8),(146.7,61.8)],
                  'YZ',(-100.8,0,0),201.6)
    clearance=rear_raked_slab(223,330,74,194,69,fold_radius=radius).common(
        rounded_plate(138,116,400,(-69,0,76),8))
    parts['RearLowerSlope']=slope.cut(clearance)
    return parts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--radius',type=float,choices=[8,16,24],required=True)
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    mesh=json.loads(args.base_meshes.read_text());baseline_hash=digest(args.base_model)
    assert mesh['fcstd_sha256']==baseline_hash
    doc=App.openDocument(str(args.base_model))
    original={o.Name:signature(o.Shape) for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    parts=rear_fold_parts(args.radius);records=[]
    for name,shape in parts.items():
        try:shape.check(True)
        except ValueError as error:raise ValueError(f'{name}: {error}') from error
        assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1
        before=doc.getObject(name).Shape
        delta=shape.cut(before).Volume+before.cut(shape).Volume
        if args.radius==8:assert delta<1e-6, (name,delta)
        records.append({'name':name,'advanced_check_passed':True,'solids':1,'closed':True,
                        'baseline_symmetric_difference_mm3':delta})
        doc.getObject(name).Shape=shape
        item=next(o for o in mesh['objects'] if o['name']==name)
        vertices,faces=shape.tessellate(.12);item.update(vertices=[list(v) for v in vertices],faces=faces)
    args.output.mkdir(parents=True,exist_ok=True)
    model=args.output/'candidate.FCStd';doc.recompute();doc.saveAs(str(model));App.closeDocument(doc.Name)
    doc=App.openDocument(str(model))
    preserved=[{'name':name,'unchanged_geometry_signature':signature(doc.getObject(name).Shape)==value}
               for name,value in original.items() if name not in parts]
    assert all(p['unchanged_geometry_signature'] for p in preserved)
    pairs=[('RearServicePanel','RearLowerSlope'),('RearStructuralFrame','RearServicePanel'),
           ('RearRecessLiner','RearServicePanel')]
    for side in ['Left','Right']:
        pairs += [('RearArmourCheek'+side,'RearStructuralFrame'),
                  ('RearArmourCheek'+side,'SideGuard'+side)]
    contacts=[]
    for first,second in pairs:
        a,b=doc.getObject(first).Shape,doc.getObject(second).Shape
        contacts.append({'objects':[first,second],'gap_mm':a.distToShape(b)[0],
                         'overlap_mm3':a.common(b).Volume})
    assert all(p['gap_mm']<.01 for p in contacts)
    App.closeDocument(doc.Name)
    mesh['fcstd_sha256']=digest(model);(args.output/'meshes.json').write_text(json.dumps(mesh))
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline_hash,
            'script_sha256':digest(Path(__file__)),'core_helpers_sha256':digest(Path(__file__).with_name('drone_concept.py')),
            'fold_radius_mm':args.radius,'changed_objects':list(parts),'parts':records,
            'preserved':preserved,'contacts':contacts,'status':'candidate; fixed-camera review pending'}
    (args.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'fcstd_sha256':mesh['fcstd_sha256'],'changed_count':len(parts),'radius_mm':args.radius}))


if __name__=='__main__':main()
