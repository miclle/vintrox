"""Compare real rear-cavity depth and light-rim occlusion with fixed cameras.

Use a hash-bound v30 model/mesh pair. Candidate files are geometry-only and do
not replace the formal deliverable. All dimensions are appearance assumptions.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
from drone_concept import rounded_plate, rounded_frame, profile, cylinder


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shape_digest(shape):
    return hashlib.sha256(shape.exportBrepToString().encode()).hexdigest()


def signature(shape):
    return [round(shape.Volume,6),round(shape.Area,6),
            sorted(tuple(round(c,6) for c in v.Point) for v in shape.Vertexes)]


def slab(front, back, bottom, top, half_width):
    knee=134; shift=(bottom-knee)*.98
    shape=profile([(front+shift,bottom),(back+shift,bottom),(back,knee),
                   (back,top),(front,top),(front,knee)],'YZ',(-half_width,0,0),2*half_width)
    edges=[e for e in shape.Edges if e.BoundBox.XLength>2*half_width-.01
           and abs(e.CenterOfMass.z-knee)<.01]
    return shape.makeFillet(8,edges)


def cavity_parts(panel, variant):
    wide=variant in ('c','d','e')
    w,h,r=(144,110,8) if wide else (138,104,5)
    window=rounded_plate(w,h,400,(-w/2,0,135-h/2),r)
    axis=App.Vector(0,.574,-.819);axis.normalize()
    bore=cylinder(50,180,tuple(App.Vector(0,180,173)-axis*40),tuple(axis))
    bottom,top,hw=(78,192,74) if wide else (82,188,70)
    back=slab(220,223,bottom,top,hw).cut(bore)
    inner=window if wide else rounded_plate(134,100,400,(-67,0,85),4)
    walls=slab(222,244,bottom,top,hw).cut(inner)
    liner=back.fuse(walls)
    parts={'RearServicePanel':panel.cut(window)}
    if variant!='a':
        rw,rh,rb,rr=(148,114,2,10) if wide else (144,110,3,8)
        rim=rounded_frame(rw,rh,400,rb,(-rw/2,0,135-rh/2),rr)
        liner=liner.fuse(rim.common(slab(242,247,135-rh/2,135+rh/2,rw/2)))
        if variant in ('d','e'):
            # Rear mounting ledge contacts the light; the forward lip remains
            # clear so its shadow cannot erase the observed luminous border.
            ledge=rounded_frame(148,114,400,4,(-74,0,78),10)
            liner=liner.fuse(ledge.common(slab(238 if variant=='e' else 244,240 if variant=='e' else 246,78,192,74)))
        lw,lh,lb,lr,front,end=(143,109,1.6,7.5,245.8,247.2) if wide else (140,106,1.4,6,243,244.5)
        if variant=='e':front-=6;end-=6
        light=rounded_frame(lw,lh,400,lb,(-lw/2,0,135-lh/2),lr)
        parts['RearCyanFrame']=light.common(slab(front,end,135-lh/2,135+lh/2,lw/2))
    parts['RearRecessLiner']=liner.removeSplitter()
    return parts


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-model',type=Path,required=True)
    parser.add_argument('--base-meshes',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--variant',choices=('a','b','c','d','e'),required=True)
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use a new candidate directory')
    mesh=json.loads(args.base_meshes.read_text())
    if mesh['fcstd_sha256']!=digest(args.base_model):
        raise ValueError('Baseline model/mesh hash mismatch')
    args.output.mkdir(parents=True,exist_ok=True)
    doc=App.openDocument(str(args.base_model))
    protected={o.Name:(shape_digest(o.Shape),signature(o.Shape)) for o in doc.Objects if hasattr(o,'Shape')
               and o.Name.startswith(('Support','CentralSupport','Bass','Nozzle','Woofer','Screen'))}
    parts=cavity_parts(doc.getObject('RearServicePanel').Shape,args.variant)
    checks=[]
    for name,shape in parts.items():
        shape.check(True)
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid cavity part: '+name)
        doc.getObject(name).Shape=shape
        checks.append({'name':name,'valid':True,'solids':1,'volume_mm3':shape.Volume})
    if not all(shape_digest(doc.getObject(n).Shape)==v[0] for n,v in protected.items()):
        raise ValueError('Protected geometry changed before saving')
    doc.recompute();model=args.output/'candidate.FCStd';doc.saveAs(str(model))
    mesh['fcstd_sha256']=digest(model)
    for item in mesh['objects']:
        if item['name'] in parts:
            vertices,faces=parts[item['name']].tessellate(.12)
            item['vertices']=[list(p) for p in vertices];item['faces']=faces
    (args.output/'meshes.json').write_text(json.dumps(mesh))
    App.closeDocument(doc.Name);doc=App.openDocument(str(model))
    unchanged={name:signature(doc.getObject(name).Shape)==value[1] for name,value in protected.items()}
    # BRep text normalization can alter low-order floats during save/read.
    # Shafts must additionally retain the exact BRep representation.
    shafts={name:shape_digest(doc.getObject(name).Shape)==value[0]
            for name,value in protected.items() if name.startswith('SupportShaft')}
    if len(shafts)!=4 or not all(shafts.values()):raise ValueError('Shaft BRep changed')
    if not all(unchanged.values()):raise ValueError('Protected support/nozzle/screen geometry changed')
    result={'base_fcstd_sha256':digest(args.base_model),'fcstd_sha256':digest(model),
            'script_sha256':digest(Path(__file__)),'variant':args.variant,'changes':checks,
            'protected_unchanged':unchanged,'shaft_brep_unchanged':shafts,'back_y_mm':223,'front_y_mm':247,
            'status':'geometry-only candidate; fixed-camera visual review required',
            'limitations':['dimensions inferred from appearance','dark reference edges are not assumed to be nozzle contours']}
    (args.output/'candidate-check.json').write_text(json.dumps(result,indent=2)+'\n')
    App.closeDocument(doc.Name)
    print(model)


if __name__=='__main__':main()
