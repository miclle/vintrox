"""Real inner-edge bevel at the nozzle exit; appearance-only hypothesis.

The fitted 43.6 mm outer circle is retained. Only the sharp inner rim is cut;
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
