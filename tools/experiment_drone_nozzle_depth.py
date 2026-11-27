"""Reduce only nozzle mid-body depth; fixed endpoints, cameras and supports."""
import argparse,hashlib,json,math
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import sector_wire,profile,rounded_plate
from experiment_drone_rear_cavity import signature

def fairing_depth_parts(reduction):
    """Rounded shoulder sections and conforming surface patches, in nozzle axes.

    Four stations avoid ripples from dense, independently adjusted circles.
    Superellipse exponents, section widths and thickness are appearance choices;
    candidate I rounds the shoulder after the cavity depth was corrected;
    exposed side edges and shadow-sensitive upper samples remain separate checks.
    """
    sections=[(0,49,49,0,2),(28,70,66-reduction,-1,2),
              (60,68,66-reduction,1,2),(94.81,53.82,53.82,-1.15,2)]
    def loft(inset=0,expand=0):
        wires=[]
        for z,rx,ry,dy,n in sections:
            points=[]
            for i in range(128):
                angle=i*math.tau/128;c,s=math.cos(angle),math.sin(angle)
                points.append(App.Vector((rx-inset+expand)*math.copysign(abs(c)**(2/n),c),
                    dy+(ry-inset+expand)*math.copysign(abs(s)**(2/n),s),z))
            curve=Part.BSplineCurve();curve.interpolate(points,PeriodicFlag=True)
            wires.append(Part.Wire([curve.toShape()]))
        return Part.makeLoft(wires,True,False)
    outer=loft()
    parts={'BassNozzleShell':outer.cut(loft(inset=4))}
    coating=loft(expand=.35).cut(outer)
    for side,(start,end) in enumerate(((212,234),(306,328))):
        for i,z in enumerate((76,84,92)):
            stencil=Part.Face(sector_wire(100,40,z,start,end)).extrude(App.Vector(0,0,2.5))
            parts[f'BassSideStripe{side}_{i}']=coating.common(stencil)
    white=loft(expand=.65).cut(loft(inset=.25))
    red=loft(expand=.95).cut(loft(expand=.4))
    parts['BassWarningPlaque']=white.common(rounded_plate(44,17,110,(-22,-110,65),1.3))
    parts['BassWarningRedBand']=red.common(rounded_plate(4.5,14.5,110,(16,-110,66.25),.7))
    parts['BassWarningTriangle']=white.common(profile([(-14,53),(14,53),(0,28)],'XZ',(0,-110,0),110))
    parts['BassWarningTriangleInset']=red.common(profile([(-11.5,51),(11.5,51),(0,31)],'XZ',(0,-110,0),110))
    for name,shape in parts.items():
        if not shape.isValid() or len(shape.Solids)!=1:
            raise ValueError('Invalid nozzle surface: '+name)
        shape.check(True)
    return parts


def main():
    p=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--depth-reduction',type=float,choices=[2,3,4],required=True)
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
    mesh=json.loads(a.base_meshes.read_text());baseline=hashlib.sha256(a.base_model.read_bytes()).hexdigest()
    assert mesh['fcstd_sha256']==baseline
    d=App.openDocument(str(a.base_model));original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    parts=fairing_depth_parts(a.depth_reduction)
    axis=App.Vector(0,.574,-.819);axis.normalize();rotation=App.Rotation(App.Vector(0,0,1),axis);place=App.Placement(App.Vector(0,180,173),rotation)
    for name,key,x,z in [('BassWarningPlaque','bass_warning_label_local_mm',14,73),('BassWarningTriangleInset','bass_alert_local_mm',1,40)]:
        mesh[key]=[x,parts[name].optimalBoundingBox(False,False).YMin-.25,z]
    records=[]
    for name,s in parts.items():
        s.Placement=place;s.check(True);assert s.isValid() and len(s.Solids)==1 and s.isClosed()
        d.getObject(name).Shape=s
        item=next(o for o in mesh['objects'] if o['name']==name);verts,faces=s.tessellate(.12);item['vertices']=[list(v) for v in verts];item['faces']=faces
        records.append({'name':name,'valid':True,'advanced_check_passed':True,'solids':1})
    a.output.mkdir(parents=True,exist_ok=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
    d=App.openDocument(str(model));preserved=[]
    for o in d.Objects:
        if o.Name not in original or o.Name in parts:continue
        preserved.append({'name':o.Name,'unchanged_geometry_signature_6dp':signature(o.Shape)==original[o.Name]})
    assert all(x['unchanged_geometry_signature_6dp'] for x in preserved)
    contacts=[]
    for x,y in [('BassWarningPlaque','BassNozzleShell'),('BassWarningTriangle','BassNozzleShell'),('BassWarningRedBand','BassWarningPlaque'),('BassWarningTriangleInset','BassWarningTriangle'),('BassNozzleRolledLip','BassNozzleShell'),('BassNozzleRearCollar','BassNozzleShell')]:
        s=d.getObject(x).Shape;t=d.getObject(y).Shape;contacts.append({'objects':[x,y],'gap_mm':s.distToShape(t)[0],'overlap_mm3':s.common(t).Volume})
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(a.output/'meshes.json').write_text(json.dumps(mesh))
    report={'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':baseline,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'depth_reduction_mm':a.depth_reduction,'changed_objects':list(parts),'parts':records,'preserved':preserved,'contacts':contacts,'status':'exploratory candidate; full camera and cavity verification pending'}
    (a.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n');print(model,flush=True)

if __name__=='__main__':main()
