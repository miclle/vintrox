"""Curved warning-mask layout inferred jointly from three fixed rear views."""
import FreeCAD as App
import Part
from drone_nozzle_root_profile import profile

# Local XZ mask coordinates, in mm. Image-derived; no manufacturing authority.
MARKING_SPEC={'triangle':[0.15418656123994104,34.21085354447391,30.111802117826446,26.490943736852692],
              'plaque':[0.23496463076827287,68.68872555473642,47.32734150401426,14.065844727972232]}

def marking_masks(spec=MARKING_SPEC):
    def plate(w,h,x,z,r):
        s=Part.makeBox(w,110,h,App.Vector(x,-110,z))
        return s.makeFillet(r,[e for e in s.Edges if e.BoundBox.YLength>109.99])
    px,pz,pw,ph=spec['plaque'];tx,tz,tw,th=spec['triangle']
    if not (30<pw<60 and 10<ph<22 and 20<tw<38 and 15<th<35):raise ValueError('Warning mask outside studied range')
    inset=1.7
    # Triangle inset follows an equal inward edge offset, retaining a real white rim.
    triangle=profile([(tx,tz),(tx-tw/2,tz+th),(tx+tw/2,tz+th)],'XZ',(0,-110,0),110)
    slope=tw/(2*th);length=(1+slope*slope)**.5
    top=tz+inset*length/slope;bottom=tz+th-inset;half=slope*(bottom-top)
    red=profile([(tx,top),(tx-half,bottom),(tx+half,bottom)],'XZ',(0,-110,0),110)
    return {'BassWarningPlaque':('white',plate(pw,ph,px-pw/2,pz,2)),
            'BassWarningRedBand':('red',plate(5,ph-2,px+pw/2-6,pz+1,.7)),
            'BassWarningTriangle':('white',triangle),'BassWarningTriangleInset':('red',red)}

def marking_probe_points(spec=MARKING_SPEC):
    x,z,w,h=spec['plaque'];tx,tz,tw,th=spec['triangle']
    return [('BassWarningPlaque',[(x+d*w,z+f*h) for f in [.25,.75] for d in [-.3,0,.23]]),
            ('BassWarningTriangle',[(tx-.3*tw,tz+.85*th),(tx+.3*tw,tz+.85*th),(tx,tz+.2*th)]),
            ('BassWarningTriangleInset',[(tx-.15*tw,tz+.7*th),(tx+.15*tw,tz+.7*th),(tx,tz+.4*th)]),
            ('BassWarningRedBand',[(x+w/2-3.5,z+f*h) for f in [.25,.5,.75]])]

def label_positions(parts,spec=MARKING_SPEC):
    x,z,w,h=spec['plaque'];tx,tz,tw,th=spec['triangle']
    return {'bass_warning_label_local_mm':[x+w/2-10,parts['BassWarningPlaque'].optimalBoundingBox(False,False).YMin-.25,z+8],
            'bass_alert_local_mm':[tx+2,parts['BassWarningTriangleInset'].optimalBoundingBox(False,False).YMin-.25,tz+th*.82],
            'bass_warning_text_size_mm':6.2,'bass_alert_text_size_mm':18.5}
