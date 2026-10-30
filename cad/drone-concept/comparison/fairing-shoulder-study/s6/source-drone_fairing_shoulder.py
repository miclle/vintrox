"""Shoulder width study on v50; keep the attachment and root sections fixed."""
import math
import FreeCAD as App
import Part
from drone_nozzle_root_profile import ROOT_DELTA, sector_wire, profile

def root_shifted_fairing(root_fraction=1.0, envelope_only=False, blend_power=4.0, depth_extra=4.0, shoulder_inset=0.0):
    """Blend the unchanged rear attachment into the revised root position."""
    original = [(0,49,49,0),(28,70-shoulder_inset,63+depth_extra,-1),(60,68-shoulder_inset,63+depth_extra,1),(94.81,53.82,53.82,-1.15)]
    if not 0 <= shoulder_inset <= 8:
        raise ValueError("Shoulder inset outside study range")
    if not 0 <= depth_extra <= 6:
        raise ValueError("Middle-depth increment outside study range")
    if not 1 <= blend_power <= 4:
        raise ValueError('Fairing root blend power outside study range')
    def weight(z):
        return max(0,min(1,z/94.81))**blend_power*root_fraction
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
