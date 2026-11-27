"""Thin outer belly wings while preserving the central support-bearing strip.

Image-derived appearance study. A closed solid is retained; this is not a
manufacturing wall-thickness or support load validation.
"""
import FreeCAD as App
import Part


def relieved_belly(shape, floor_z, central_half_width=42):
    if not 44 <= floor_z <= 53:
        raise ValueError('Belly floor outside the studied range')
    if not 32 <= central_half_width <= 42:
        raise ValueError("Central retained strip outside studied range")
    result=shape.copy()
    for side in [-1,1]:
        points=[(central_half_width,-20),(130,-20),(130,floor_z),(62,floor_z),(central_half_width,35)]
        vs=[App.Vector(side*x,-20,z) for x,z in points]
        cut=Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(App.Vector(0,220,0))
        result=result.cut(cut)
    result=result.removeSplitter();result.check(True)
    if not result.isValid() or not result.isClosed() or len(result.Solids)!=1:
        raise ValueError('Invalid closed belly relief')
    return result


def moved_service_shape(shape, side, floor_z, is_bolt=False):
    if is_bolt:
        import math
        bb=shape.optimalBoundingBox(False,False)
        center=App.Vector((bb.XMin+bb.XMax)/2,(bb.YMin+bb.YMax)/2,bb.ZMax)
        # Rebuild the existing elliptical screw analytically. Historical affine
        # screws contain C0/curve-on-surface errors; do not transfer those faults.
        ellipse=Part.Ellipse(center,2.6,2.184).toShape()
        face=Part.Face(Part.Wire(ellipse));face.rotate(center,App.Vector(0,0,1),90)
        moved=face.extrude(App.Vector(0,0,-1.8))
        rz=App.Rotation(App.Vector(0,0,1),25)
        flip=App.Rotation(App.Vector(0,0,1),App.Vector(0,0,-1))
        points=[]
        for x,y in [(-1.56,-.45),(1.56,-.45),(1.56,.45),(-1.56,.45)]:
            q=flip.multVec(rz.multVec(App.Vector(x,y,-.5)))
            points.append(center+App.Vector(q.x*.84,q.y,q.z))
        cutter=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,-2.8))
        moved=moved.cut(cutter)
    else:
        moved=shape.copy()
    # Put the whole plate on the flat outer shelf, with 0.3 mm skin overlap.
    moved.translate(App.Vector(side*10.92,0,floor_z-36.7))
    return moved
