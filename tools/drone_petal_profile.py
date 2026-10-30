"""Controlled nozzle taper trial with a shared unchanged root section.

Scoped v46 leaf/hardware constructors. Radius decreases linearly toward the
existing terminal plane; root centre/radius, exit centre/axis and sheet thickness
stay fixed. Surface dimensions are appearance assumptions, not manufacturing.
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

def petal_surface_parts(index, strap_radius=.4, terminal_inset=0):
    guide_span=4.9;guide_start=103;guide_lift=.35
    angle = index*30+15
    scale = 30/22.5
    upper = [(98,52.05,-.98,-.15),(108,49.4,.7,-1.5),(111.6,48.38,1.33,-1.95)]
    stations = [(100,51.49,-.62,-.43),(108,49.4,.7,-1.5),
                (111.4,48.44,1.295,-1.925),(120,46,2.8,-3),(123.5,45,3.41,-3.5)]
    upper = taper_sections(upper, terminal_inset)
    stations = taper_sections(stations, terminal_inset)
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


def tube(points, radius):
    """Swept circular wire; decorative cable, not an electrical model."""
    points = [App.Vector(*p) for p in points]
    curve = Part.BSplineCurve()
    if (points[0]-points[-1]).Length < .01:
        curve.interpolate(points[:-1], PeriodicFlag=True)
    else:
        curve.interpolate(points)
    path = Part.Wire(curve.toShape())
    tangent = curve.tangent(curve.FirstParameter)[0]
    section = Part.Wire([Part.makeCircle(radius, points[0], tangent)])
    return path.makePipeShell([section], True, False)


def taper_sections(rows, inset):
    if not 0 <= inset <= 4:
        raise ValueError('Terminal inset outside the appearance study range')
    root, terminal = 96.8067, 128.43
    return [(z, r-inset*max(0, min(1, (z-root)/(terminal-root))), dy, tilt)
            for z,r,dy,tilt in rows]


def tapered_leaf_parts(i, terminal_inset=2.1):
    """Round-edged leaves with a shared root and a smaller terminal section."""
    phase, pitch = 15, 30
    a=i*pitch+phase
    angular_scale=pitch/22.5
    sections=[(96.8067,52.3215,-1.149,0),(108,49.4,.7,-1.5),
              (120,46,2.8,-3),(128.43,43.6,4.28,-4.2)]
    sections = taper_sections(sections, terminal_inset)
    def section(ro,ri,z,dy,tilt,start,stop):
        w=sector_wire(ro,ri,z,start,stop)
        w.rotate(App.Vector(0,0,z),App.Vector(1,0,0),tilt)
        w.translate(App.Vector(0,dy,0))
        return w
    def skin(outer,inner,start,stop,stations=sections):
        return Part.makeLoft([section(r+outer,r+inner,z,dy,t,a+start*angular_scale,a+stop*angular_scale)
                             for z,r,dy,t in stations],True,True)
    petal=skin(0,-2,1.2,21.3)
    # Round the four radial section edges: visible sheet corners, not an
    # arbitrary render bevel. Keep most of the fitted terminal circular arc.
    end_normal=App.Vector(0,-math.sin(math.radians(-4.2)),math.cos(math.radians(-4.2)))
    radial=[e for e in petal.Edges if abs(e.Length-2)<1e-5 and (
        abs(e.CenterOfMass.z-96.8067)<1e-5 or
        abs(end_normal.dot(e.CenterOfMass-App.Vector(0,4.28,128.43)))<1e-5)]
    if len(radial)!=4:raise ValueError('Expected four radial petal corner edges')
    petal=petal.makeFillet(.85,radial)
    # Round tapered cutters before trimming the curved sheet surfaces.
    def window(start,stop,z0,z1,radius):
        theta=math.radians(a+11.25*angular_scale)
        tangent=App.Vector(math.sin(theta),-math.cos(theta),0)
        def point(z,angle):
            lo,hi=next((l,h) for l,h in zip(sections,sections[1:]) if l[0]<=z<=h[0])
            f=(z-lo[0])/(hi[0]-lo[0]);r,dy,tilt=[lo[j]+f*(hi[j]-lo[j]) for j in [1,2,3]]
            t=math.radians(a+angle*angular_scale);q=App.Vector(r*math.cos(t),dy+r*math.sin(t)*math.cos(math.radians(tilt)),z+r*math.sin(t)*math.sin(math.radians(tilt)))
            return (tangent.dot(q),q.z)
        pts=[point(z0,start),point(z0,stop),point(z1,stop),point(z1,start)]
        tool=profile(pts,'XZ',(0,-80,0),160)
        axial=[e for e in tool.Edges if abs(e.Length-160)<1e-6]
        assert len(axial)==4
        tool=tool.makeFillet(radius,axial)
        tool.rotate(App.Vector(),App.Vector(0,0,1),math.degrees(theta)-90)
        return tool
    recess=skin(1,-.8,0,22.5).common(window(2.7,19.8,99.5,127,1.0))
    inset=skin(-.65,-.95,0,22.5).common(window(3.1,19.4,99.8,126.7,.8))
    parts={f'NozzlePetal{i}':petal.cut(recess),f'NozzlePetalInset{i}':inset}
    for edge_index,edge_offset in enumerate((1.7,20.8)):
        edge=a+edge_offset*angular_scale
        t=math.radians(edge)
        # Stop before the rounded corners rather than overhanging their ends.
        stations=taper_sections([(98,52.05,-.98,-.15),(108,49.4,.7,-1.5),
                                 (120,46,2.8,-3),(127.3,43.92,4.08,-4.04)], terminal_inset)
        points=[((r+.05)*math.cos(t),dy+(r+.05)*math.sin(t)*math.cos(math.radians(tilt)),
                 z+(r+.05)*math.sin(t)*math.sin(math.radians(tilt))) for z,r,dy,tilt in stations]
        parts[f'NozzlePetalEdgeRail{i}_{int(i*22.5+(1.7,20.8)[edge_index])}']=tube(points,.28)
    parts[f'NozzlePetalEndHem{i}']=skin(.1,-.4,2.6,19.9,taper_sections([(127.7,43.81,4.15,-4.1),(128.43,43.6,4.28,-4.2)], terminal_inset))
    parts.update(petal_surface_parts(i, terminal_inset=terminal_inset))
    return parts


def tapered_inner_parts(terminal_inset=2.1):
    """Follow the petal taper inside, preserving the original radial offsets."""
    rows = taper_sections([(96.8067,48.8215,-1.149,0),(108,45.9,.7,-1.5),
                           (120,42.5,2.8,-3),(128.43,40.1,4.28,-4.2)], terminal_inset)
    def shell(offset):
        wires = []
        for z,r,dy,tilt in rows:
            wire = Part.Wire([Part.makeCircle(r-offset, App.Vector(0,0,z))])
            wire.rotate(App.Vector(0,0,z), App.Vector(1,0,0), tilt)
            wire.translate(App.Vector(0,dy,0))
            wires.append(wire)
        return Part.makeLoft(wires, True, False)
    cone_rows = taper_sections([(103,20,0,0),(110,28,1,0),
                                (119,37,3,0),(123,39,4,0)], terminal_inset)
    cone = Part.makeLoft([Part.Wire([Part.makeCircle(r,App.Vector(0,dy,z))])
                          for z,r,dy,_ in cone_rows], True, False)
    return {'BassInnerThroat': shell(.1).cut(shell(2.6)), 'BassVisualCone': cone}
