"""Explore rounded upper straps and rounded backed channel feet on the nozzle leaves."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part
from drone_concept import sector_wire, profile, tube
from experiment_drone_rear_cavity import signature


def open_rounded_rail(points, radius):
    # Circular sections avoid tiny Boolean slivers at almost-collinear joints.
    # The loft is an open path with solid end caps, never a closed perimeter.
    sections = [Part.Wire([Part.makeCircle(radius, App.Vector(*point),
                                          App.Vector(0,0,1))]) for point in points]
    return Part.makeLoft(sections, True, True)


def rounded_section(z,r,dy,tilt,theta,radius):
 half=(r+.7)*math.sin(math.radians(3.5*30/22.5/2));lo=-1.1;hi=.7;c=radius;k=1/math.sqrt(2)
 radial=App.Vector(math.cos(theta),math.sin(theta),0);tangent=App.Vector(-math.sin(theta),math.cos(theta),0)
 def point(t,v):return radial*(r+v)+tangent*t+App.Vector(0,0,z)
 def line(a,b):return Part.makeLine(point(*a),point(*b))
 def arc(a,m,b):return Part.Arc(point(*a),point(*m),point(*b)).toShape()
 edges=[line((-half+c,hi),(half-c,hi)),arc((half-c,hi),(half-c+c*k,hi-c+c*k),(half,hi-c)),line((half,hi-c),(half,lo+c)),arc((half,lo+c),(half-c+c*k,lo+c-c*k),(half-c,lo)),line((half-c,lo),(-half+c,lo)),arc((-half+c,lo),(-half+c-c*k,lo+c-c*k),(-half,lo+c)),line((-half,lo+c),(-half,hi-c)),arc((-half,hi-c),(-half+c-c*k,hi-c+c*k),(-half+c,hi))]
 w=Part.Wire(edges);w.rotate(App.Vector(0,0,z),App.Vector(1,0,0),tilt);w.translate(App.Vector(0,dy,0));return w

def petal_detail_parts(index, strap_radius=.4):
    guide_span=4.9;guide_start=103;guide_lift=.35
    angle = index*30+15
    scale = 30/22.5
    upper = [(98,52.05,-.98,-.15),(108,49.4,.7,-1.5),(111.6,48.38,1.33,-1.95)]
    stations = [(100,51.49,-.62,-.43),(108,49.4,.7,-1.5),
                (111.4,48.44,1.295,-1.925),(120,46,2.8,-3),(123.5,45,3.41,-3.5)]
    def station(z):
        lo, hi = next((lo,hi) for lo,hi in zip(stations,stations[1:]) if lo[0]<=z<=hi[0])
        fraction = (z-lo[0])/(hi[0]-lo[0])
        return (z, *[lo[j]+fraction*(hi[j]-lo[j]) for j in [1,2,3]])
    lower = [row for row in stations if row[0]>=111.4]
    left, right = 11.25-guide_span/2, 11.25+guide_span/2

    def skin(outer, inner, start, stop, stations):
        wires = []
        for z, radius, dy, tilt in stations:
            wire = sector_wire(radius+outer, radius+inner, z,
                               angle+start*scale, angle+stop*scale)
            wire.rotate(App.Vector(0,0,z), App.Vector(1,0,0), tilt)
            wire.translate(App.Vector(0,dy,0))
            wires.append(wire)
        return Part.makeLoft(wires, True, True)

    theta = math.radians(angle+11.25*scale)
    tangent = App.Vector(math.sin(theta),-math.cos(theta),0)

    def point(z, offset):
        lo, hi = next((lo,hi) for lo,hi in zip(lower,lower[1:]) if lo[0]<=z<=hi[0])
        fraction = (z-lo[0])/(hi[0]-lo[0])
        radius, dy, tilt = [lo[j]+fraction*(hi[j]-lo[j]) for j in [1,2,3]]
        phase = math.radians(angle+offset*scale)
        v = App.Vector(radius*math.cos(phase),
                       dy+radius*math.sin(phase)*math.cos(math.radians(tilt)),
                       z+radius*math.sin(phase)*math.sin(math.radians(tilt)))
        return tangent.dot(v), v.z

    outline = [point(z,offset) for z,offset in
               [(112,left+.55),(112,right-.55),
                (122.9,right-.55),(122.9,left+.55)]]
    cutter = profile(outline,'XZ',(0,-80,0),160)
    axial = [edge for edge in cutter.Edges if abs(edge.Length-160)<1e-6]
    assert len(axial) == 4
    cutter = cutter.makeFillet(.5, axial)
    cutter.rotate(App.Vector(),App.Vector(0,0,1),math.degrees(theta)-90)
    # A 0.38 mm minimum radial backing remains; this is a recess, not a hole.
    recess = skin(.6,-.72,0,22.5,lower).common(cutter)
    strap=Part.makeLoft([rounded_section(z,r,dy,t,theta,strap_radius) for z,r,dy,t in upper],True,False)
    outer_points=[point(z,offset) for z,offset in [(111.4,left-.5),(111.4,right+.5),(123.5,right+.5),(123.5,left-.5)]]
    outer_tool=profile(outer_points,'XZ',(0,-80,0),160)
    outer_axial=[edge for edge in outer_tool.Edges if abs(edge.Length-160)<1e-6]
    outer_tool=outer_tool.makeFillet(.9,outer_axial)
    outer_tool.rotate(App.Vector(),App.Vector(0,0,1),math.degrees(theta)-90)
    channel=skin(.25,-1.1,left-.5,right+.5,lower).common(outer_tool).cut(recess)
    parts = {f'NozzlePetalRidge{index}':strap.fuse(channel).removeSplitter()}
    # Rounded piecewise rails follow the ruled body's stations. A dense spline
    # sweep failed to make a solid; retaining that path would also allow overshoot.
    rail_stations = [station(guide_start), *[row for row in stations if row[0]>guide_start]]
    for rail, offset in enumerate([left,right]):
        phase = math.radians(angle+offset*scale)
        def lift(z):
            return .15 if z<111.4 else guide_lift
        points = [((radius+lift(z))*math.cos(phase),
                   dy+(radius+lift(z))*math.sin(phase)*math.cos(math.radians(tilt)),
                   z+(radius+lift(z))*math.sin(phase)*math.sin(math.radians(tilt)))
                  for z,radius,dy,tilt in rail_stations]
        parts[f'NozzlePetalGuide{index}_{rail}'] = (
            open_rounded_rail(points,.28) if guide_start<111.4 else tube(points,.28))
    return parts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--strap-radius',type=float,choices=[.25,.4],default=.4)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    mesh = json.loads(args.base_meshes.read_text())
    baseline_hash = digest(args.base_model)
    assert mesh['fcstd_sha256'] == baseline_hash
    document = App.openDocument(str(args.base_model))
    original = {o.Name:signature(o.Shape) for o in document.Objects
                if hasattr(o,'Shape') and not o.Shape.isNull()}
    axis = App.Vector(0,.574,-.819)
    axis.normalize()
    placement = App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
    changed, records = [], []
    for index in range(12):
        for name, shape in petal_detail_parts(index,args.strap_radius).items():
            shape.Placement = placement.multiply(shape.Placement)
            try:
                shape.check(True)
            except ValueError as error:
                raise ValueError(f'{name}: {error}') from error
            assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1
            document.getObject(name).Shape = shape
            item = next(item for item in mesh['objects'] if item['name']==name)
            vertices, faces = shape.tessellate(.12)
            item['vertices'], item['faces'] = [list(v) for v in vertices], faces
            changed.append(name)
            records.append({'name':name,'advanced_check_passed':True,'solids':1,'closed':True})
    args.output.mkdir(parents=True,exist_ok=True)
    model = args.output/'candidate.FCStd'
    document.recompute()
    document.saveAs(str(model))
    App.closeDocument(document.Name)
    document = App.openDocument(str(model))
    preserved = [{'name':name,'unchanged_geometry_signature':signature(document.getObject(name).Shape)==value}
                 for name,value in original.items() if name not in changed]
    assert all(row['unchanged_geometry_signature'] for row in preserved)
    contacts = []
    for index in range(12):
        ridge = document.getObject(f'NozzlePetalRidge{index}').Shape
        for name in [f'NozzlePetal{index}',f'NozzlePetalGuide{index}_0',f'NozzlePetalGuide{index}_1']:
            shape = document.getObject(name).Shape
            contacts.append({'objects':[f'NozzlePetalRidge{index}',name],
                             'gap_mm':ridge.distToShape(shape)[0],'overlap_mm3':ridge.common(shape).Volume})
    App.closeDocument(document.Name)
    mesh['fcstd_sha256'] = digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh))
    report = {'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline_hash,
              'script_sha256':digest(Path(__file__)),'guide_span_local_deg':4.9,
              'guide_start_station_mm':103,'guide_radial_lift_mm':.35,
              'strap_corner_radius_mm':args.strap_radius,'channel_foot_corner_radius_mm':.9,
              'changed_objects':changed,'parts':records,'preserved':preserved,'contacts':contacts,
              'status':'candidate only; reference width and whole-orbit checks pending'}
    (args.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'changed_objects':len(changed),'fcstd_sha256':mesh['fcstd_sha256'],
                      'max_contact_gap_mm':max(c['gap_mm'] for c in contacts)}))


if __name__=='__main__':
    main()
