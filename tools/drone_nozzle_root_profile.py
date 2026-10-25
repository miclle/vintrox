"""Joint nozzle-root study from five fixed reference-video views.

The root moves toward the body while the terminal circle stays fixed. Every
leaf layer and the inner surfaces follow the same section map. Geometry is
an appearance reconstruction, not a fabrication or mechanism specification.
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

def petal_surface_parts(index, strap_radius=.4, root_fraction=0, guide_span=5.4):
    guide_start=shifted_z(103,root_fraction);guide_lift=.35
    angle = index*30+15
    scale = 30/22.5
    upper = [(98,52.05,-.98,-.15),(108,49.4,.7,-1.5),(111.6,48.38,1.33,-1.95)]
    stations = [(100,51.49,-.62,-.43),(108,49.4,.7,-1.5),
                (111.4,48.44,1.295,-1.925),(120,46,2.8,-3),(123.5,45,3.41,-3.5)]
    upper = root_sections(upper, root_fraction)
    stations = root_sections(stations, root_fraction)
    def station(z):
        lo, hi = next((lo,hi) for lo,hi in zip(stations,stations[1:]) if lo[0]<=z<=hi[0])
        fraction = (z-lo[0])/(hi[0]-lo[0])
        return (z, *[lo[j]+fraction*(hi[j]-lo[j]) for j in [1,2,3]])
    lower = [row for row in stations if row[0]>=shifted_z(111.4,root_fraction)]
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
        z = shifted_z(z, root_fraction)
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
            return .15 if z<shifted_z(111.4,root_fraction) else guide_lift
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


ROOT_DELTA = (-3.0466361829744244, 1.199312188677304, 8.517128593165324, -.33662871354521684)


def root_weight(z):
    return max(0, min(1, (128.43-z)/(128.43-96.8067)))


def shifted_z(z, fraction):
    return z + ROOT_DELTA[0]*root_weight(z)*fraction


def root_sections(rows, fraction):
    if not 0 <= fraction <= 1:
        raise ValueError('Root-shift fraction must be between zero and one')
    return [tuple(value + delta*root_weight(row[0])*fraction
                  for value, delta in zip(row, ROOT_DELTA)) for row in rows]


def root_shifted_leaf_parts(i, root_fraction=1.0, guide_span=5.4):
    """Round-edged leaves with a shared root and a smaller terminal section."""
    phase, pitch = 15, 30
    a=i*pitch+phase
    angular_scale=pitch/22.5
    sections=[(96.8067,52.3215,-1.149,0),(108,49.4,.7,-1.5),
              (120,46,2.8,-3),(128.43,43.6,4.28,-4.2)]
    sections = root_sections(sections, root_fraction)
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
    root_z,_,root_dy,root_tilt = sections[0]
    root_normal = App.Vector(0,-math.sin(math.radians(root_tilt)),math.cos(math.radians(root_tilt)))
    radial=[e for e in petal.Edges if abs(e.Length-2)<1e-5 and (
        abs(root_normal.dot(e.CenterOfMass-App.Vector(0,root_dy,root_z)))<1e-5 or
        abs(end_normal.dot(e.CenterOfMass-App.Vector(0,4.28,128.43)))<1e-5)]
    if len(radial)!=4:raise ValueError('Expected four radial petal corner edges')
    petal=petal.makeFillet(.85,radial)
    # Round tapered cutters before trimming the curved sheet surfaces.
    def window(start,stop,z0,z1,radius):
        z0,z1 = shifted_z(z0,root_fraction),shifted_z(z1,root_fraction)
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
    # Keep the recessed strip embedded in the petal while narrowing its
    # visible angular window. The radial backing and cavity shadow remain.
    inset=skin(-.65,-.95,0,22.5).common(window(4.4,18.1,99.8,126.7,.8))
    parts={f'NozzlePetal{i}':petal.cut(recess),f'NozzlePetalInset{i}':inset}
    for edge_index,edge_offset in enumerate((1.7,20.8)):
        edge=a+edge_offset*angular_scale
        t=math.radians(edge)
        # Stop before the rounded corners rather than overhanging their ends.
        stations=root_sections([(98,52.05,-.98,-.15),(108,49.4,.7,-1.5),
                                 (120,46,2.8,-3),(127.3,43.92,4.08,-4.04)], root_fraction)
        points=[((r+.05)*math.cos(t),dy+(r+.05)*math.sin(t)*math.cos(math.radians(tilt)),
                 z+(r+.05)*math.sin(t)*math.sin(math.radians(tilt))) for z,r,dy,tilt in stations]
        parts[f'NozzlePetalEdgeRail{i}_{int(i*22.5+(1.7,20.8)[edge_index])}']=tube(points,.28)
    parts[f'NozzlePetalEndHem{i}']=skin(.1,-.4,2.6,19.9,root_sections([(127.7,43.81,4.15,-4.1),(128.43,43.6,4.28,-4.2)], root_fraction))
    parts.update(petal_surface_parts(i, root_fraction=root_fraction, guide_span=guide_span))
    return parts


def root_shifted_inner_parts(root_fraction=1.0):
    """Follow the petal taper inside, preserving the original radial offsets."""
    rows = root_sections([(96.8067,48.8215,-1.149,0),(108,45.9,.7,-1.5),
                           (120,42.5,2.8,-3),(128.43,40.1,4.28,-4.2)], root_fraction)
    def shell(offset):
        wires = []
        for z,r,dy,tilt in rows:
            wire = Part.Wire([Part.makeCircle(r-offset, App.Vector(0,0,z))])
            wire.rotate(App.Vector(0,0,z), App.Vector(1,0,0), tilt)
            wire.translate(App.Vector(0,dy,0))
            wires.append(wire)
        return Part.makeLoft(wires, True, False)
    cone_rows = root_sections([(103,20,0,0),(110,28,1,0),
                                (119,37,3,0),(123,39,4,0)], root_fraction)
    cone = Part.makeLoft([Part.Wire([Part.makeCircle(r,App.Vector(0,dy,z),App.Vector(0,-math.sin(math.radians(t)),math.cos(math.radians(t))))])
                          for z,r,dy,t in cone_rows], True, False)
    return {'BassInnerThroat': shell(.1).cut(shell(2.6)), 'BassVisualCone': cone}


def root_shifted_rolls(root_fraction=1.0):
    parts = {}
    for name,row in [('BassNozzleRolledLip',(95.6,52.82,-1.15,0)),
                     ('BassNozzleMouthRing',(96.8067,52.3215,-1.149,0))]:
        z,r,dy,tilt = root_sections([row],root_fraction)[0]
        axis = App.Vector(0,-math.sin(math.radians(tilt)),math.cos(math.radians(tilt)))
        parts[name] = Part.makeTorus(r,1,App.Vector(0,dy,z),axis)
    z,r,dy,tilt = root_sections([(91,52.5,-1.15,0)],root_fraction)[0]
    center = App.Vector(0,dy,z)
    gasket = Part.makeCylinder(r,4,center).cut(Part.makeCylinder(r-4.5,4,center))
    gasket.rotate(center,App.Vector(1,0,0),tilt)
    parts['BassSpeakerGasket'] = gasket
    for i in range(12):
        parts[f'NozzlePetalHinge{i}'] = root_shifted_hinge(i, root_fraction)
    return parts


def root_shifted_hinge(i, root_fraction=1.0):
    z,r,dy,tilt = root_sections([(98.5,51.5,-1.149,0)],root_fraction)[0]
    center = App.Vector(0,dy,z)
    roll = Part.makeTorus(r,2.3,center,App.Vector(0,0,1),0,360,22.4)
    roll.rotate(center,App.Vector(0,0,1),i*30+18.8)
    ends = [e for e in roll.Edges if abs(e.Length-2*math.pi*2.3)<1e-5]
    assert len(ends)==2
    roll = roll.makeFillet(.3,ends)
    roll.rotate(center,App.Vector(1,0,0),tilt)
    return roll


def root_shifted_fairing(root_fraction=1.0, envelope_only=False):
    """Blend the unchanged rear attachment into the revised root position."""
    original = [(0,49,49,0),(28,70,63,-1),(60,68,63,1),(94.81,53.82,53.82,-1.15)]
    def weight(z):
        return max(0,min(1,z/94.81))*root_fraction
    def loft(inset=0,expand=0):
        wires = []
        for z,rx,ry,dy in original:
            w=weight(z)
            actual_z=z+ROOT_DELTA[0]*w
            points=[]
            for i in range(128):
                t=i*math.tau/128
                points.append(App.Vector((rx+ROOT_DELTA[1]*w-inset+expand)*math.cos(t),
                                         (ry+ROOT_DELTA[1]*w-inset+expand)*math.sin(t),actual_z))
            curve=Part.BSplineCurve();curve.interpolate(points,PeriodicFlag=True)
            wire=Part.Wire([curve.toShape()])
            wire.rotate(App.Vector(0,0,actual_z),App.Vector(1,0,0),ROOT_DELTA[3]*w)
            wire.translate(App.Vector(0,dy+ROOT_DELTA[2]*w,0))
            wires.append(wire)
        return Part.makeLoft(wires,True,False)
    if envelope_only:
        return loft(expand=.3)
    outer=loft()
    parts={'BassNozzleShell':outer.cut(loft(inset=4))}
    coating=loft(expand=.35).cut(outer)
    for side,(start,end) in enumerate(((212,234),(306,328))):
        for i,z in enumerate((76,84,92)):
            w=weight(z);actual_z=z+ROOT_DELTA[0]*w
            wire=sector_wire(100,40,actual_z,start,end)
            wire.rotate(App.Vector(0,0,actual_z),App.Vector(1,0,0),ROOT_DELTA[3]*w)
            wire.translate(App.Vector(0,ROOT_DELTA[2]*w,0))
            direction=App.Vector(0,-math.sin(math.radians(ROOT_DELTA[3]*w)),math.cos(math.radians(ROOT_DELTA[3]*w)))
            mask=Part.Face(wire).extrude(direction*2.5*(1+ROOT_DELTA[0]*root_fraction/94.81))
            parts[f'BassSideStripe{side}_{i}']=coating.common(mask)
    def plate(w,h,depth,pos,radius):
        shape=Part.makeBox(w,depth,h,App.Vector(*pos))
        edges=[e for e in shape.Edges if e.BoundBox.YLength>depth-.01]
        return shape.makeFillet(radius,edges)
    def moved_mask(shape):
        matrix=App.Matrix()
        matrix.A23=ROOT_DELTA[2]*root_fraction/94.81
        matrix.A33=1+ROOT_DELTA[0]*root_fraction/94.81
        return shape.transformGeometry(matrix)
    white=loft(expand=.65).cut(loft(inset=.25))
    red=loft(expand=.95).cut(loft(expand=.4))
    masks={'BassWarningPlaque':(white,plate(44,17,110,(-22,-110,65),1.3)),
           'BassWarningRedBand':(red,plate(4.5,14.5,110,(16,-110,66.25),.7)),
           'BassWarningTriangle':(white,profile([(-14,53),(14,53),(0,28)],'XZ',(0,-110,0),110)),
           'BassWarningTriangleInset':(red,profile([(-11.5,51),(11.5,51),(0,31)],'XZ',(0,-110,0),110))}
    for name,(skin,mask) in masks.items():
        parts[name]=skin.common(moved_mask(mask))
    return parts
