"""Round the exposed inner perimeter of the rear frame for appearance trials.

The two straight sides seed an OCCT tangent chain, so the result is a perimeter
roundover, not a fillet confined to those two straight segments. No cavity or
nozzle material is added.
"""


def rounded_frame_inner_edge(shape, radius):
    if not 0.5 <= radius <= 2.5:
        raise ValueError('Radius outside the studied appearance range')
    edges = [e for e in shape.Edges
             if abs(abs(e.CenterOfMass.x) - 81.44) < 1e-6
             and abs(e.CenterOfMass.y - 248) < 1e-6
             and e.BoundBox.ZLength > 80
             and e.BoundBox.XLength < 1e-6
             and e.BoundBox.YLength < 1e-6]
    if len(edges) != 2:
        raise ValueError('Expected the two original inner rear-frame edges')
    result = shape.makeFillet(radius, edges)
    result.check(True)
    if not result.isValid() or not result.isClosed() or len(result.Solids) != 1:
        raise ValueError('Invalid rear-frame roundover')
    return result
