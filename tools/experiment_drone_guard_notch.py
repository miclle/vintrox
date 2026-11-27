"""Trim stepped guard-notch tips to a reference-derived continuous edge.

Back-projection constrains a real cut at the existing X=108 side plane. It never
warps an image. Mirror symmetry and the depth of the cut remain assumptions.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
import numpy as np
from experiment_drone_rear_cavity import signature

REFERENCE_EDGE=[[563,487],[556,499],[543,512],[529,524]]
CUT_OUTLINE=[[520,475],[570,475],*REFERENCE_EDGE,[520,525]]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','cameras','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use an empty candidate directory')
    camera=json.loads(args.cameras.read_text())
    pose=next(p for p in camera['views'] if p['source_frame']==180)
    eye=np.array(pose['eye_mm']);forward=np.array(pose['target_mm'])-eye
    forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right)
    up=np.cross(right,forward);focal=pose['lens_mm']/pose['sensor_width_mm']*940
    yz=[]
    for x,y in CUT_OUTLINE:
        ray=forward+(x-470)/focal*right+(400-y)/focal*up
        point=eye+ray*((108-eye[0])/ray[0]);yz.append(point[1:].tolist())
    mesh=json.loads(args.base_meshes.read_text());baseline=digest(args.base_model)
    assert mesh['fcstd_sha256']==baseline
    doc=App.openDocument(str(args.base_model))
    original={o.Name:signature(o.Shape) for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    checks=[]
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        points=[App.Vector(side*103,y,z) for y,z in yz]
        cutter=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(side*18,0,0))
        name='SideGuard'+suffix;before=doc.getObject(name).Shape
        shape=before.cut(cutter).removeSplitter();shape.check(True)
        assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1
        removed=before.cut(shape).Volume;added=shape.cut(before).Volume
        assert removed>0 and added<1e-6
        doc.getObject(name).Shape=shape
        record=next(o for o in mesh['objects'] if o['name']==name)
        vertices,faces=shape.tessellate(.12);record.update(vertices=[list(v) for v in vertices],faces=faces)
        checks.append({'name':name,'advanced_check_passed':True,'solids':1,'closed':True,
                       'removed_volume_mm3':removed,'added_volume_mm3':added})
    args.output.mkdir(parents=True,exist_ok=True)
    model=args.output/'candidate.FCStd';doc.recompute();doc.saveAs(str(model));App.closeDocument(doc.Name)
    doc=App.openDocument(str(model));changed=[p['name'] for p in checks]
    preserved=[{'name':name,'unchanged_geometry_signature':signature(doc.getObject(name).Shape)==value}
               for name,value in original.items() if name not in changed]
    assert all(p['unchanged_geometry_signature'] for p in preserved)
    contacts=[]
    for suffix in ['Left','Right']:
        for prefix in ['SideClosure','RearArmourCheek','CyanSideTube']:
            first,second='SideGuard'+suffix,prefix+suffix
            a,b=doc.getObject(first).Shape,doc.getObject(second).Shape
            gap=a.distToShape(b)[0];assert gap<.01
            contacts.append({'objects':[first,second],'gap_mm':gap,'overlap_mm3':a.common(b).Volume})
    App.closeDocument(doc.Name)
    mesh['fcstd_sha256']=digest(model);(args.output/'meshes.json').write_text(json.dumps(mesh))
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline,
            'script_sha256':digest(Path(__file__)),'camera_config_sha256':digest(args.cameras),
            'source_frame':180,'reference_edge_px':REFERENCE_EDGE,'cut_outline_px':CUT_OUTLINE,
            'cut_outline_yz_mm':yz,'side_plane_x_mm':108,'changed_objects':changed,
            'parts':checks,'preserved':preserved,'contacts':contacts,
            'limitations':['Four manually observed edge points; about two pixels uncertainty.',
                           'Source camera participates in construction; other views must check the result.',
                           'Mirror symmetry and a side-normal cut are inferred, not source measurements.']}
    (args.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'fcstd_sha256':mesh['fcstd_sha256'],'parts':checks}))


if __name__=='__main__':main()
