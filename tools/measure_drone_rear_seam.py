"""Check rear-frame/carrier common faces and the two recessed antenna slots.

This is saved-CAD evidence for a render artifact and its real geometry repair,
not a whole silhouette, manufacturing fit or physical verification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import rounded_plate


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1];cad=root/'cad/drone-concept'
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,default=cad/'vintrox-drone-concept.FCStd')
    p.add_argument('--baseline-model',type=Path,required=True)
    p.add_argument('--output',type=Path,default=cad/'comparison/rear-seam-check.json');args=p.parse_args()
    base=App.openDocument(str(args.baseline_model));doc=App.openDocument(str(args.model))
    try:
        carrier=doc.getObject('RearRailCarrier').Shape;frame=doc.getObject('RearStructuralFrame').Shape
        old_carrier=base.getObject('RearRailCarrier').Shape;old_frame=base.getObject('RearStructuralFrame').Shape
        planes=lambda s:[f for f in s.Faces if f.findPlane(1e-6) is not None and f.BoundBox.YLength<1e-6 and abs(f.CenterOfMass.y-248)<1e-6]
        area=lambda a,b:sum(x.common(y).Area for x in planes(a) for y in planes(b))
        current_union=carrier.fuse(frame);baseline_union=old_carrier.fuse(old_frame)
        slots=[];cutters=[]
        for side in (-1,1):
            cutter=rounded_plate(13.5,2.8,2.1,(side*15.5-6.75,246.7,228),1.3);cutters.append(cutter)
            void=Part.makeSphere(.2,App.Vector(side*15.5,247.5,229.4))
            floor=Part.makeSphere(.1,App.Vector(side*15.5,246.5,229.4))
            liner=next(o for o in doc.Objects if o.Name.startswith('RearRailAntennaSlot') and o.Shape.BoundBox.Center.x*side>0)
            slots.append({'side':side,'baseline_void_probe_overlap_mm3':baseline_union.common(void).Volume,
                          'void_probe_overlap_mm3':current_union.common(void).Volume,
                          'floor_probe_overlap_mm3':current_union.common(floor).Volume,
                          'liner':liner.Name,'liner_frame_gap_mm':liner.Shape.distToShape(frame)[0],
                          'liner_frame_overlap_mm3':liner.Shape.common(frame).Volume})
        whole_removed=baseline_union.cut(current_union).Volume
        whole_added=current_union.cut(baseline_union).Volume
        # The lower frame outline is revised independently in v40. This check
        # protects the upper shared face and slots; full changed-part geometry
        # remains covered by the generator/candidate/readback equality check.
        seam_scope=Part.makeBox(400,300,166,App.Vector(-200,100,134))
        current_seam=current_union.common(seam_scope)
        baseline_seam=baseline_union.common(seam_scope)
        expected=baseline_seam.common(Part.makeCompound(cutters)).Volume
        removed=baseline_seam.cut(current_seam).Volume;added=current_seam.cut(baseline_seam).Volume
        parts=[]
        for name in ['RearRailCarrier','RearStructuralFrame']:
            s=doc.getObject(name).Shape;s.check(True)
            parts.append({'name':name,'valid':s.isValid(),'solids':len(s.Solids),'closed':all(v.isClosed() for v in s.Solids)})
        result={'fcstd_sha256':digest(args.model),'baseline_fcstd_sha256':digest(args.baseline_model),
                'measurement_script_sha256':digest(Path(__file__)),'parts':parts,
                'baseline_volume_overlap_mm3':old_carrier.common(old_frame).Volume,
                'volume_overlap_mm3':carrier.common(frame).Volume,
                'baseline_coplanar_y248_overlap_mm2':area(old_carrier,old_frame),
                'coplanar_y248_overlap_mm2':area(carrier,frame),'contact_gap_mm':carrier.distToShape(frame)[0],
                'union_removed_volume_mm3':removed,'union_added_volume_mm3':added,
                'seam_scope_z_min_mm':134,'whole_union_removed_volume_mm3':whole_removed,
                'whole_union_added_volume_mm3':whole_added,
                'expected_slot_removed_volume_mm3':expected,'slots':slots,
                'limitations':['union preservation is checked above Z=134mm; full lower-frame changes recorded separately',
                    'front-plane area only for the diagnosed coplanar seam','solid partition and local recess probes, not physical acceptance']}
        result['passed']=(all(c['valid'] and c['closed'] and c['solids']==1 for c in parts)
                          and result['volume_overlap_mm3']<1e-6 and result['coplanar_y248_overlap_mm2']<1e-6
                          and result['contact_gap_mm']<1e-6 and added<1e-6 and abs(removed-expected)<1e-4
                          and all(s['void_probe_overlap_mm3']<1e-6 and s['floor_probe_overlap_mm3']>.001
                                  and s['liner_frame_gap_mm']<.01 and s['liner_frame_overlap_mm3']>.01 for s in slots))
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
        if not result['passed']:raise SystemExit(1)
    finally:App.closeDocument(base.Name);App.closeDocument(doc.Name)


if __name__=='__main__':main()
