"""Nozzle inner edge finish alternatives; appearance-only hypotheses.

The fitted 43.6 mm outer circle is retained. The bevel follows the complete tangent inner perimeter;
this does not infer missing wall material from the reference's dark interior.
"""
import FreeCAD as App


def bevel_inner_exit(shape, width):
    if not .1 <= width <= 1:
        raise ValueError('Studied inner bevel width must be 0.1 to 1 mm')
    center=App.Vector(0,4.28,128.43)
    normal=App.Rotation(App.Vector(1,0,0),-4.2).multVec(App.Vector(0,0,1))
    edges=[]
    for edge in shape.Edges:
        if edge.Length<5:continue
        points=edge.discretize(Number=17)
        if max(abs(normal.dot(p-center)) for p in points)<1e-5 and max(abs((p-center).Length-41.6) for p in points)<1e-5:
            edges.append(edge)
    if len(edges)!=1:raise ValueError(f'Expected one terminal inner arc, found {len(edges)}')
    result=shape.makeChamfer(width,edges)
    result.check(True)
    if not result.isValid() or len(result.Solids)!=1 or not result.isClosed():
        raise ValueError('Invalid bevel')
    return result


def inner_return_lip(shape, index, width=1.5, depth=.8):
    """Add a short inward return at each terminal arc, retaining the outer circle."""
    import Part, math
    from drone_nozzle_root_profile import sector_wire
    if not .5 <= width <= 2.5 or not .4 <= depth <= 1.2:
        raise ValueError('Return lip outside studied appearance range')
    angle=index*30+15
    # Start inside the rounded corners, attach 0.5 mm into the existing sheet.
    wire=sector_wire(42.1,41.6-width,128.43-depth,angle+3.6,angle+26.4)
    lip=Part.Face(wire).extrude(App.Vector(0,0,depth))
    lip.rotate(App.Vector(0,0,128.43),App.Vector(1,0,0),-4.2)
    lip.translate(App.Vector(0,4.28,0))
    # Round radial corners of the bent strip, independent of display shading.
    radial=[e for e in lip.Edges if abs(e.Length-(width+.5))<1e-5]
    if len(radial)!=4:raise ValueError('Expected four lip corner edges')
    lip=lip.makeFillet(.2,radial)
    result=shape.fuse(lip).removeSplitter();result.check(True)
    if not result.isValid() or len(result.Solids)!=1 or not result.isClosed():
        raise ValueError('Invalid return lip')
    return result
