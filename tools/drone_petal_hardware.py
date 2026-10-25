"""Rounded nozzle straps, backed channels and root rolls inferred from references.
Kept separate from the main leaves, gold fairing and rear cavity. Dimensions
are appearance assumptions; these parts are not a manufactured hinge system.
"""
import math
import FreeCAD as App
import Part

def sector_wire(outer, inner, z, start, stop):
    def p(radius, angle):
        a = math.radians(angle)
        return App.Vector(radius*math.cos(a), radius*math.sin(a), z)
    mid = (start+stop)/2
    return Part.Wire([
        Part.Arc(p(outer, start), p(outer, mid), p(outer, stop)).toShape(),
        Part.makeLine(p(outer, stop), p(inner, stop)),
        Part.Arc(p(inner, stop), p(inner, mid), p(inner, start)).toShape(),
        Part.makeLine(p(inner, start), p(outer, start)),
    ])


def profile(points,plane,origin,thickness):
    assert plane=='XZ'
    pts=[App.Vector(x,0,z) for x,z in points]
    result=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,thickness,0))
    result.translate(App.Vector(*origin))
    return result


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

def petal_surface_parts(index, strap_radius=.4):
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
            open_rounded_rail(points,.28))
    return parts


def rolled_petal_root(index,radius=2.3):
    center=App.Vector(0,-1.149,98.5)
    shape=Part.makeTorus(51.5,radius,center,App.Vector(0,0,1),0,360,22.4)
    shape.rotate(center,App.Vector(0,0,1),index*30+18.8)
    ends=[edge for edge in shape.Edges if abs(edge.Length-2*math.pi*radius)<1e-5]
    assert len(ends)==2
    return shape.makeFillet(.3,ends)
