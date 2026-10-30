"""Appearance-only recessed nozzle interior, preserving the fitted outer petals.

The previous loft was a solid cone with a flat cap close to the exit. These
alternatives construct a real bowl and an optional shorter throat; unknown
speaker geometry is not inferred from the dark reference area.
"""
import math
import FreeCAD as App
import Part
from drone_nozzle_root_profile import root_sections, root_shifted_inner_parts


def circle(row):
    z,r,dy,tilt=row
    normal=App.Vector(0,-math.sin(math.radians(tilt)),math.cos(math.radians(tilt)))
    return Part.Wire([Part.makeCircle(r,App.Vector(0,dy,z),normal)])


def loft(rows):
    return Part.makeLoft([circle(row) for row in rows],True,False)


def bowl(rows, thickness=1.0):
    """Keep a finite back wall and radial wall; remove the artificial front cap."""
    outer=loft(rows)
    first,last=rows[0],rows[-1]
    # Open the cutter beyond the mouth while leaving the back plate in place.
    inner=[(first[0]+thickness,first[1]-thickness,first[2],first[3])]
    inner += [(z,r-thickness,dy,t) for z,r,dy,t in rows[1:]]
    inner.append((last[0]+2,last[1]+1,last[2],last[3]))
    return outer.cut(loft(inner))


def interior_parts(recessed=False):
    if recessed:
        throat_rows=root_sections([(96.8067,48.8215,-1.149,0),(104,47.35,.05,-1),
                                  (112,44.7666666667,1.4,-2)],1)
        throat=loft([(z,r-.1,dy,t) for z,r,dy,t in throat_rows]).cut(
                    loft([(z,r-2.6,dy,t) for z,r,dy,t in throat_rows]))
        z,r,dy,t=throat_rows[-1]
        rows=[(z-23,20,dy,t),(z-16,28,dy,t),(z-7,r-5,dy,t),(z,r-.7,dy,t)]
    else:
        throat=root_shifted_inner_parts()['BassInnerThroat']
        rows=root_sections([(103,20,0,0),(110,28,1,0),(119,37,3,0),(123,39,4,0)],1)
    cone=bowl(rows)
    z,r,dy,t=rows[0]
    normal=App.Vector(0,-math.sin(math.radians(t)),math.cos(math.radians(t)))
    cap=Part.makeSphere(8,App.Vector(0,dy,z+.7),normal,0,90)
    return {'BassInnerThroat':throat,'BassVisualCone':cone,'BassDustCap':cap}
