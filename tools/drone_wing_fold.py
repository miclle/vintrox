"""Gold-wing crease refinement with the original blade outline and hub retained.

Build surfaces from transformed section wires so trimmed curves remain consistent.
The three station offsets are appearance fits, not original-part measurements.
"""
import FreeCAD as A
import Part

WING_OUTLINE = [(210.33, 366.67), (202.26, 357.61), (162.35, 311.86), (133.92, 270.72), (95.92, 216.13), (59.43, 173.79), (53.07, 161.74), (54.98, 147.46), (62.36, 136.36), (76.97, 127.85), (90.54, 127.89), (102.98, 134.78), (112.07, 144.17), (116.91, 158.36), (121.32, 174.38), (127.9, 189.4), (138.83, 202.93), (153.77, 218.65), (168.39, 239.46), (182.19, 258.6), (196.51, 278.3), (208.65, 299.93), (215.85, 318.48), (214.45, 337.47)]
WING_CREASE = [(116.91, 158.36), (121.43, 193.27), (129.37, 224.39), (142.5, 248.67), (174.21, 286.7), (214.0, 335.21)]
GOLD_WING_CREASE_OFFSETS = (1.9071327831418121, 6.203890280847322, 3.3243336866335516)
GOLD_WING_REAR_INSET_LOCAL_MM = 5.0
# Blend the rear middle edge into the retained root and tip stations.
GOLD_WING_REAR_STATION_WEIGHTS = {17: .2, 18: .75, 19: 1, 20: .9, 21: .25}
GOLD_WING_FRONT_OFFSETS_LOCAL_MM = {1: .5, 2: 5.5, 3: 2.5, 4: 2.0}


def gold_wing_rear_parts(inset, curved_plate, front_offsets=None):
    """Build the wing layers affected by the selected outline stations."""
    front_offsets = front_offsets or {}
    outline = [(y - inset * GOLD_WING_REAR_STATION_WEIGHTS.get(i, 0)
                + front_offsets.get(i, 0), z)
               for i, (y, z) in enumerate(WING_OUTLINE)]
    matrix = A.Matrix()
    matrix.A11, matrix.A22, matrix.A33 = .817, 1.12, 1.01
    matrix.A13, matrix.A14 = -.04, 6
    matrix.A24, matrix.A34 = 33, -8.8
    fold_parts = gold_wing_fold_parts(outline)
    parts = {
        'WingEdgeRight': curved_plate(outline, 167, 1).transformGeometry(matrix),
        'WingInnerPaintRight': curved_plate(outline, 166.4, .6).transformGeometry(matrix),
        'WingFoldFacetRight': fold_parts['WingFoldFacetRight'],
    }
    if front_offsets:
        for name in ('WingRaisedFaceRight', 'WingPaintRight'):
            parts[name] = fold_parts[name]
    return parts

def gold_wing_fold_parts(wing=WING_OUTLINE, *, crease_corner=None):
    original=WING_CREASE;crease=[list(p) for p in original]
    for i,d in zip([2,3,4],GOLD_WING_CREASE_OFFSETS):crease[i][0]+=d
    if crease_corner is not None:
        crease[2] = list(crease_corner)
    m=A.Matrix();m.A11=.817;m.A22=1.12;m.A33=1.01;m.A24=33;m.A34=-8.8;m.A13=-.04;m.A14=6
    def plate(points,x,thickness,rim=0,centre=None):
     cy,cz=centre or (sum(p[0] for p in points)/len(points),sum(p[1] for p in points)/len(points))
     def section(depth,scale=1):
      pts = [A.Vector(x + depth, cy + (y - cy) * scale, cz + (z - cz) * scale)
             for y, z in points]
      tangent = pts[14] - pts[12]
      tangent.normalize()
      front = Part.BSplineCurve()
      front.interpolate(pts[:14], InitialTangent=pts[1]-pts[0], FinalTangent=tangent)
      rear = Part.BSplineCurve()
      if crease_corner is None:
       rear.interpolate(pts[13:], InitialTangent=tangent, FinalTangent=pts[-1]-pts[-2])
       edges = [front.toShape(), rear.toShape()]
      else:
       lower = Part.BSplineCurve()
       lower.interpolate(pts[13:16], InitialTangent=tangent, FinalTangent=pts[15]-pts[14])
       rear.interpolate(pts[15:], InitialTangent=pts[16]-pts[15], FinalTangent=pts[-1]-pts[-2])
       edges = [front.toShape(), lower.toShape(), rear.toShape()]
      wire = Part.Wire(edges + [Part.makeLine(pts[-1], pts[0])])
      return Part.Wire(wire.transformGeometry(m).Edges)
     if rim:
      span=min(max(p[i] for p in points)-min(p[i] for p in points) for i in [0,1]);scale=1-2*rim/span
      return Part.makeLoft([section(0,scale),section(thickness*.25),section(thickness*.7),section(thickness,scale)],True,True)
     return Part.Face(section(0)).extrude(A.Vector(thickness*.817,0,0))
    main=wing[:14]+crease[1:];inset=[(83+(y-83)*.994,158+(z-158)*.994) for y,z in main];old_inset=[(83+(y-83)*.994,158+(z-158)*.994) for y,z in WING_OUTLINE[:14]+original[1:]];centre=(sum(p[0] for p in old_inset)/len(old_inset),sum(p[1] for p in old_inset)/len(old_inset))
    parts={'WingRaisedFaceRight':plate(main,168,3),'WingPaintRight':plate(inset,170,3.5,.6,centre)}
    def boundary_y(path,z):
     for (y0,z0),(y1,z1) in zip(path,path[1:]):
      if z0<=z<=z1:return y0+(y1-y0)*(z-z0)/(z1-z0)
     raise ValueError(z)
    sections=[]
    for z in [174.4,193.27,crease[2][1],248.67,286.7,335.21]:
     front=boundary_y(crease,z);rear=boundary_y(wing[13:]+[wing[0]],z);vertices=[m.multVec(A.Vector(x,y,z)) for x,y in [(167,front),(169.5,front),(168,rear),(167,rear)]];sections.append(Part.makePolygon(vertices+[vertices[0]]))
    parts['WingFoldFacetRight']=Part.makeLoft(sections,True,True)
    return parts
