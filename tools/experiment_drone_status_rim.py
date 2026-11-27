"""Restore an inset, bevelled status-pocket rim without moving the controls."""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App
import Part
import numpy as np
from drone_concept import profile,cylinder,box
from experiment_drone_rear_cavity import signature

REFERENCE_EDGE=[[529,524],[543,512],[556,499],[563,487],[563,420]]

def uncut_side_closure(side):
    """Recreate planar extrusion before rounding, avoiding affine 3D fillets.

    The Y/Z perimeter retains the existing transformed corner curves. The
    thickness-edge fillet is now a true 2.1mm world-space radius; this is an
    intentional small geometric change, not a lossless normalization.
    """
    outline=[(54.4,187.9),(69.67,241.01),(171.39,244.33),(183.98,232.58),
             (184.41,133.67),(132.95,50.96),(80.38,49.36),(53.38,72.45)]
    source=profile(outline,'YZ',(0,0,0),1)
    source=source.makeFillet(10,[e for e in source.Edges if e.BoundBox.XLength>.99])
    face=min((f for f in source.Faces if abs(f.normalAt(0,0).x)>.99),key=lambda f:f.CenterOfMass.x)
    matrix=App.Matrix();matrix.A22=1.25;matrix.A33=.84;matrix.A34=24;matrix.A14=side*100.8
    wire=Part.Wire(face.OuterWire.transformGeometry(matrix).Edges)
    result=Part.Face(wire).extrude(App.Vector(side*12.6,0,0))
    result=result.makeFillet(2.1,[e for e in result.Edges if e.BoundBox.XLength<.01])
    result=result.cut(cylinder(64,17,(side*100,129.09686,153.62312),(side,0,0)))
    result=result.cut(cylinder(21.2,23,(side*97.8,192.27910630805997,201.20766206780763),(side,0,0)))
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rim_patch(side, inner_x, flare, cameras):
    eye=np.array(next(p for p in cameras['views'] if p['source_frame']==180)['eye_mm'])
    pose=next(p for p in cameras['views'] if p['source_frame']==180)
    forward=np.array(pose['target_mm'])-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    focal=pose['lens_mm']/pose['sensor_width_mm']*940
    scale=(108-eye[0])/(116.76-eye[0])
    full=uncut_side_closure(side)
    full.scale(scale)
    full.translate(App.Vector(side*(108-scale*116.76),eye[1]*(1-scale),eye[2]*(1-scale)))
    local=box(106-inner_x,42,63,((inner_x if side>0 else -106),193,127))
    patch=full.common(local)
    profiles=[]
    for x,extra in [(inner_x-.05,0),(104.6103319,flare),(106,flare+1.5)]:
        edge=[]
        for px,py in REFERENCE_EDGE:
            ray=forward+(px-470)/focal*right+(400-py)/focal*up
            q=eye+ray*((x-eye[0])/ray[0]);edge.append((q[1]+extra,q[2]))
        # Extend beyond the patch: pre-existing shell, not this cutter, closes
        # the socket end of the opening. The lower diagonal follows the trace.
        outline=[(185,115),(edge[0][0]-10,115),*edge,(edge[-1][0],195),(185,195)]
        vertices=[App.Vector(side*x,y,z) for y,z in outline]
        profiles.append(Part.Wire(Part.makePolygon(vertices+[vertices[0]]).Edges))
    opening=Part.makeLoft(profiles,True,True)
    return patch.cut(opening).removeSplitter()


def main():
    parser=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','cameras','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--inner-x',type=float,choices=[100,100.5,101],required=True)
    parser.add_argument('--flare',type=float,choices=[3.8,5.0],required=True)
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):raise ValueError('Use empty output')
    mesh=json.loads(args.base_meshes.read_text());base_hash=digest(args.base_model)
    assert mesh['fcstd_sha256']==base_hash
    cameras=json.loads(args.cameras.read_text());doc=App.openDocument(str(args.base_model))
    original={o.Name:signature(o.Shape) for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    records=[]
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        name='SideClosure'+suffix;before=doc.getObject(name).Shape
        patch=rim_patch(side,args.inner_x,args.flare,cameras)
        shape=before.fuse(patch).removeSplitter()
        try:shape.check(True)
        except ValueError as error:raise ValueError(f'{name}: {error}') from error
        assert shape.isValid() and shape.isClosed() and len(shape.Solids)==len(before.Solids)
        added=shape.cut(before).Volume;removed=before.cut(shape).Volume
        assert added>0 and removed<1e-6
        doc.getObject(name).Shape=shape
        item=next(o for o in mesh['objects'] if o['name']==name)
        vertices,faces=shape.tessellate(.12);item.update(vertices=[list(v) for v in vertices],faces=faces)
        records.append({'name':name,'advanced_check_passed':True,'solids':len(shape.Solids),'baseline_solids':len(before.Solids),'closed':True,
                        'added_volume_mm3':added,'removed_volume_mm3':removed})
    args.output.mkdir(parents=True,exist_ok=True);model=args.output/'candidate.FCStd'
    doc.recompute();doc.saveAs(str(model));App.closeDocument(doc.Name)
    doc=App.openDocument(str(model));changed=[p['name'] for p in records]
    preserved=[{'name':name,'unchanged_geometry_signature':signature(doc.getObject(name).Shape)==value}
               for name,value in original.items() if name not in changed]
    assert all(p['unchanged_geometry_signature'] for p in preserved)
    contacts=[]
    for suffix in ['Left','Right']:
        for prefix in ['SideGuard','HandleArm','RearArmourCheek']:
            first,second='SideClosure'+suffix,prefix+suffix
            a,b=doc.getObject(first).Shape,doc.getObject(second).Shape
            gap=a.distToShape(b)[0];assert gap<.01
            contacts.append({'objects':[first,second],'gap_mm':gap,'overlap_mm3':a.common(b).Volume})
    App.closeDocument(doc.Name);mesh['fcstd_sha256']=digest(model)
    (args.output/'meshes.json').write_text(json.dumps(mesh))
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':base_hash,
            'script_sha256':digest(Path(__file__)),'core_helpers_sha256':digest(Path(__file__).with_name('drone_concept.py')),
            'camera_config_sha256':digest(args.cameras),'source_frame':180,'reference_edge_px':REFERENCE_EDGE,
            'rim_inner_x_mm':args.inner_x,'outer_recess_flare_mm':args.flare,
            'changed_objects':changed,'parts':records,'preserved':preserved,'contacts':contacts,
            'status':'candidate; visibility and complete fixed-view review required'}
    (args.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'fcstd_sha256':mesh['fcstd_sha256'],'parts':records}))


if __name__=='__main__':main()
