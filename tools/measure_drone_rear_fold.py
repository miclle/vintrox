"""Read candidate fold changes and plot actual saved X=80 mm sections."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
from PIL import Image,ImageDraw,ImageFont


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidates',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    baseline=App.openDocument(str(args.baseline))
    vertices=[App.Vector(80,y,z) for y,z in [(190,105),(260,105),(260,175),(190,175)]]
    plane=Part.Face(Part.makePolygon(vertices+[vertices[0]]))
    def sections(doc):
        return [{'name':name,'edges_yz_mm':[[[p.y,p.z] for p in edge.discretize(Number=101)]
                 for edge in doc.getObject(name).Shape.section(plane).Edges]}
                for name in ['RearServicePanel','RearStructuralFrame']]
    all_sections=[{'label':'V43 R8','sections':sections(baseline)}]
    results=[]
    try:
        for folder in args.candidates:
            check=json.loads((folder/'candidate-check.json').read_text())
            model=folder/'candidate.FCStd'
            assert digest(model)==check['fcstd_sha256']
            assert digest(args.baseline)==check['baseline_fcstd_sha256']
            doc=App.openDocument(str(model))
            try:
                changed=[]
                for name in check['changed_objects']:
                    before=baseline.getObject(name).Shape;after=doc.getObject(name).Shape
                    after.check(True)
                    differences=[s for s in [before.cut(after),after.cut(before)] if s.Volume>1e-6]
                    z_range=None
                    if differences:
                        box=Part.makeCompound(differences).optimalBoundingBox(False,False)
                        z_range=[box.ZMin,box.ZMax]
                        assert box.ZMin>=125-1e-5 and box.ZMax<=145+1e-5,(name,z_range)
                    changed.append({'name':name,'symmetric_difference_mm3':sum(s.Volume for s in differences),
                                    'difference_z_range_mm':z_range,'advanced_check_passed':True})
                protected=[]
                for obj in baseline.Objects:
                    if not (obj.Name.startswith('SupportShaft') or obj.Name=='BassNozzleShell'):
                        continue
                    after=doc.getObject(obj.Name).Shape
                    delta=obj.Shape.cut(after).Volume+after.cut(obj.Shape).Volume
                    assert delta<1e-6
                    protected.append({'name':obj.Name,'symmetric_difference_mm3':delta})
                assert len(protected)==5
                results.append({'candidate':folder.name,'fcstd_sha256':digest(model),
                                'parts':changed,'protected_geometry':protected,'passed':True})
                all_sections.append({'label':f"R{check['fold_radius_mm']:g}",'sections':sections(doc)})
            finally:
                App.closeDocument(doc.Name)
    finally:
        App.closeDocument(baseline.Name)
    colors=['#dddddd','#43d9ff','#ffbb52']
    board=Image.new('RGB',(1000,800),'#151b22');draw=ImageDraw.Draw(board)
    font=ImageFont.load_default(size=18)
    def pixel(y,z):return (100+(y-214)*20,720-(z-116)*20)
    for value in range(216,253,4):
        x,_=pixel(value,116);draw.line((x,80,x,720),fill='#323a44')
        draw.text((x-10,735),str(value),fill='white',font=font)
    for value in range(116,149,4):
        _,y=pixel(214,value);draw.line((100,y,860,y),fill='#323a44')
        draw.text((55,y-9),str(value),fill='white',font=font)
    for row,color in zip(all_sections,colors):
        for part in row['sections']:
            for edge in part['edges_yz_mm']:
                # Draw only segments inside the stated plot domain.
                for a,b in zip(edge,edge[1:]):
                    if all(214<=p[0]<=252 and 116<=p[1]<=148 for p in [a,b]):
                        draw.line([pixel(*a),pixel(*b)],fill=color,width=2)
    draw.text((100,15),'SAVED BREP SECTION: X = 80 mm',fill='white',font=font)
    for i,(row,color) in enumerate(zip(all_sections,colors)):
        draw.text((100+i*180,45),row['label'],fill=color,font=font)
    draw.text((810,765),'Y (mm)',fill='white',font=font)
    draw.text((20,50),'Z (mm)',fill='white',font=font)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    picture=args.output.with_suffix('.png');board.save(picture)
    report={'baseline_fcstd_sha256':digest(args.baseline),'measurement_script_sha256':digest(Path(__file__)),
            'candidate_results':results,'sections':all_sections,'image_path':str(picture),
            'image_sha256':digest(picture),'passed':True,
            'limitations':['Geometric section comparison only; not source-image metrology.',
                           'Protected nozzle and shafts checked by saved BRep difference; no physical validation.']}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('Saved fold differences confined to Z=125..145; nozzle and four shafts unchanged')


if __name__=='__main__':main()
