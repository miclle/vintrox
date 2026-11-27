"""Saved interior geometry, finite material/air probes and baseline preservation."""
import argparse,hashlib,json,math
from pathlib import Path
import FreeCAD as App
from drone_nozzle_root_profile import root_sections
from drone_nozzle_interior import interior_parts
from experiment_drone_rear_cavity import signature


def main():
    p=argparse.ArgumentParser()
    for name in ['model','baseline','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--candidate',type=Path)
    a=p.parse_args();sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    d=App.openDocument(str(a.model));base=App.openDocument(str(a.baseline));names=['BassInnerThroat','BassVisualCone','BassDustCap']
    try:
        axis=App.Vector(0,.574,-.819);axis.normalize();frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
        source=interior_parts(True);parts=[]
        for name in names:
            shape=d.getObject(name).Shape;shape.check(True)
            assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1
            generated=source[name];generated.Placement=frame.multiply(generated.Placement)
            # Signed Boolean volumes can be unreliable at coincident B-spline
            # boundaries; retain both signed values and require their magnitudes.
            forward=shape.cut(generated).Volume;backward=generated.cut(shape).Volume
            assert abs(forward)+abs(backward)<1e-6,name
            parts.append({'name':name,'valid':True,'closed':True,'solids':1,'advanced_check_passed':True,
                          'source_difference_mm3':abs(forward)+abs(backward),'signed_cut_volumes_mm3':[forward,backward]})
        candidate_rows=[]
        if a.candidate:
            candidate=App.openDocument(str(a.candidate))
            try:
                for name in names:
                    saved=d.getObject(name).Shape;other=candidate.getObject(name).Shape
                    diff=abs(saved.cut(other).Volume)+abs(other.cut(saved).Volume)
                    assert diff<1e-6,name
                    candidate_rows.append({'name':name,'symmetric_difference_mm3':diff})
            finally:
                if candidate.Name!=d.Name:App.closeDocument(candidate.Name)
        kept=[]
        for o in base.Objects:
            if not hasattr(o,'Shape') or o.Shape.isNull() or o.Name in names:continue
            assert signature(o.Shape)==signature(d.getObject(o.Name).Shape),o.Name
            kept.append(o.Name)
        assert len(kept)==695
        z,r,dy,t=root_sections([(112,44.7666666667,1.4,-2)],1)[0]
        def point(station,radius,theta):
            angle=math.radians(theta);tilt=math.radians(t)
            return frame.multVec(App.Vector(radius*math.cos(angle),dy+radius*math.sin(angle)*math.cos(tilt),station+radius*math.sin(angle)*math.sin(tilt)))
        shapes=[d.getObject(n).Shape for n in names];old_shapes=[base.getObject(n).Shape for n in names]
        air=[]
        for station in [z+3,z+7,z+11]:
            for radius in [0,12,24,34]:
                for angle in ([0] if radius==0 else [0,90,180,270]):
                    q=point(station,radius,angle);new=any(s.isInside(q,1e-5,False) for s in shapes)
                    assert not new,(station,radius,angle)
                    air.append({'point_mm':list(q),'candidate_material':new,'baseline_material':any(s.isInside(q,1e-5,False) for s in old_shapes)})
        floor=[]
        for angle in range(0,360,30):
            q=point(z-23+.4,15,angle);inside=d.getObject('BassVisualCone').Shape.isInside(q,1e-5,False)
            assert inside,angle
            floor.append({'point_mm':list(q),'inside_bowl_backing':inside})
        joins=[]
        for angle in range(0,360,30):
            q=point(z-.1,r-.9,angle)
            left=d.getObject('BassInnerThroat').Shape.isInside(q,1e-5,False);right=d.getObject('BassVisualCone').Shape.isInside(q,1e-5,False)
            joins.append({'point_mm':list(q),'inside_throat':left,'inside_bowl':right})
        assert all(v['inside_throat'] and v['inside_bowl'] for v in joins)
        cap=[]
        for angle in range(0,360,30):
            q=point(z-23+.9,3,angle);left=d.getObject('BassVisualCone').Shape.isInside(q,1e-5,False);right=d.getObject('BassDustCap').Shape.isInside(q,1e-5,False)
            assert left and right,angle
            cap.append({'point_mm':list(q),'inside_bowl':left,'inside_cap':right})
        exterior=[]
        for local in [(0,0,0),(1000,1000,1000),(0,0,150)]:
            q=frame.multVec(App.Vector(*local));assert not any(s.isInside(q,1e-5,False) for s in shapes)
            exterior.append({'point_mm':list(q),'outside_all_three':True})
        result={'passed':True,'fcstd_sha256':sha(a.model),'baseline_fcstd_sha256':sha(a.baseline),'source_module_sha256':sha(Path(__file__).with_name('drone_nozzle_interior.py')),'measurement_script_sha256':sha(Path(__file__)),'parts':parts,'preserved_objects':kept,'air_probes':air,'floor_probes':floor,'rim_contact_probes':joins,'cap_contact_probes':cap,'exterior_probes':exterior,'limitations':['Sparse finite probes are not a continuous wall-thickness or manufacturing test.','Boolean common volumes at coincident surfaces are not used as sole contact proof.','Reference darkness alone does not establish an internal speaker design.']}
        result['candidate_fcstd_sha256']=sha(a.candidate) if a.candidate else sha(a.model)
        result['candidate_comparisons']=candidate_rows
        result['generator_sha256']=sha(Path(__file__).with_name('drone_concept.py'))
        result['shafts']=[name for name in kept if name.startswith('SupportShaft')]
        assert len(result['shafts'])==4
        a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'parts':len(parts),'preserved':len(kept),'air_probes':len(air),'new_air_from_previous_material':sum(p['baseline_material'] for p in air),'floor':len(floor),'rim_contacts':len(joins),'cap_contacts':len(cap)}))
    finally:
        App.closeDocument(d.Name);App.closeDocument(base.Name)


if __name__=='__main__':main()
