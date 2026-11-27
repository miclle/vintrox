"""Read rolled-lip layering and contact evidence from the saved appearance CAD."""
import argparse,hashlib,json,math
from pathlib import Path
import FreeCAD as App
from drone_concept import nozzle_lip_parts


def main():
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser()
    p.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=App.openDocument(str(a.model))
    try:
        expected=nozzle_lip_parts()
        parts=[]
        for name in ['BassNozzleRolledLip','BassNozzleMouthRing','BassSpeakerGasket']:
            s=d.getObject(name).Shape;s.check(True)
            radii=sorted({(round(f.Surface.MajorRadius,6),round(f.Surface.MinorRadius,6)) for f in s.Faces if hasattr(f.Surface,'MajorRadius')})
            expected_radii=sorted({(round(f.Surface.MajorRadius,6),round(f.Surface.MinorRadius,6)) for f in expected[name].Faces if hasattr(f.Surface,'MajorRadius')})
            assert radii==expected_radii, name
            parts.append({'name':name,'valid':s.isValid(),'closed':s.isClosed(),'solids':len(s.Solids),'advanced_check_passed':True,'torus_radii_mm':radii})
        axis=App.Vector(0,.574,-.819);axis.normalize();place=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
        gold=d.getObject('BassNozzleRolledLip').Shape;metal=d.getObject('BassNozzleMouthRing').Shape;points=[]
        # Midpoints of the two tube centerlines lie strictly inside both tubes.
        # Include finite offsets to distinguish interior material from mere tangency.
        gold_source=next(f.Surface for f in expected['BassNozzleRolledLip'].Faces if hasattr(f.Surface,'MajorRadius'))
        metal_source=next(f.Surface for f in expected['BassNozzleMouthRing'].Faces if hasattr(f.Surface,'MajorRadius'))
        u=App.Vector(1,0,0)
        for i in range(8):
            t=i*math.tau/8
            def centreline(surface):
                v=surface.Axis.cross(u)
                return surface.Center+(u*math.cos(t)+v*math.sin(t))*surface.MajorRadius
            q=(centreline(gold_source)+centreline(metal_source))*.5
            for dz in [-.1,0,.1]:
                w=place.multVec(q+metal_source.Axis*dz)
                points.append({'point_mm':list(w),'inside_gold':gold.isInside(w,1e-6,False),'inside_metal':metal.isInside(w,1e-6,False)})
        contacts=[]
        for left,right in [('BassNozzleRolledLip','BassNozzleShell'),('BassNozzleRolledLip','BassNozzleMouthRing'),('BassSpeakerGasket','BassNozzleShell')]:
            s=d.getObject(left).Shape;t=d.getObject(right).Shape;contacts.append({'objects':[left,right],'gap_mm':s.distToShape(t)[0],'boolean_overlap_mm3':s.common(t).Volume})
        petals=[{'name':f'NozzlePetal{i}','root_roll_overlap_mm3':d.getObject(f'NozzlePetal{i}').Shape.common(metal).Volume} for i in range(12)]
        passed=(all(x['valid'] and x['closed'] and x['solids']==1 for x in parts) and
                all(x['inside_gold'] and x['inside_metal'] for x in points) and all(x['gap_mm']<.01 for x in contacts) and
                all(x['root_roll_overlap_mm3']>.01 for x in petals))
        result={'fcstd_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parts':parts,'contacts':contacts,'interior_contact_probes':points,'petal_contacts':petals,'passed':passed,'limitations':['tori Boolean common may return zero despite 24 strictly interior overlap probes; raw result retained','local appearance contacts, not manufacturing or physical verification']}
        a.output.write_text(json.dumps(result,indent=2)+'\n');print('passed',passed)
        if not passed:raise SystemExit(1)
    finally:App.closeDocument(d.Name)

if __name__=='__main__':main()
