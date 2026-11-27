"""Explore shoulder cross-section fullness, retaining v37 attachment endpoints."""
import argparse,json,hashlib,math
from pathlib import Path
import FreeCAD as App
import Part
from drone_concept import profile
from experiment_drone_rear_cavity import signature

def rear_bow_parts(exponent):
    outer_x=108.0;scale=1.0089049846660512;eye_y=481.9590609254328;eye_z=317.0386845391606
    def rear_y(z,y,knee,slope,radius=8):
        angle=math.atan(slope);d=radius*math.tan(angle/2)
        top=knee+d;bottom=knee-d/math.sqrt(1+slope*slope)
        if z>=top:return y
        if z<=bottom:return y+(z-knee)*slope
        return y-radius+math.sqrt(radius*radius-(z-top)**2)
    map_z=lambda z:eye_z+scale*(z-eye_z)
    stations=sorted(set([map_z(z) for z in [67.3,100,123,125,127,129,131,133,135,137,139,141,143,145,180,222]]+
                        [125,127,129,131,133,135,137,139,141,143,145]))
    result={}
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        wires=[]
        for z in stations:
            back=rear_y(z,248,134,.98)
            original_z=eye_z+(z-eye_z)/scale
            original_y=rear_y(original_z,230.5125,136.2828,64.325/69.4764)
            edge=eye_y+scale*(original_y-eye_y)
            rx=outer_x-89;ry=back-edge
            def curve(inset,reverse=False):
                pts=[App.Vector(side*(89+(rx-inset)*math.sin(i*math.pi/32)**(2/exponent)),edge+(ry-inset)*math.cos(i*math.pi/32)**(2/exponent),z) for i in range(17)]
                if reverse:pts.reverse()
                spline=Part.BSplineCurve();spline.interpolate(pts)
                return spline.toShape(),pts
            outer,op=curve(0);inner,ip=curve(3.5,True)
            ot=op[-1]+App.Vector(0,-4*scale,0);it=ip[0]+App.Vector(0,-4*scale,0)
            wires.append(Part.Wire([outer,Part.makeLine(op[-1],ot),Part.makeLine(ot,it),Part.makeLine(it,ip[0]),inner,Part.makeLine(ip[-1],op[0])]))
        result['RearArmourCheek'+suffix]=Part.makeLoft(wires,True,True)
    return result


def main():
    p=argparse.ArgumentParser()
    for name in ['base-model','base-meshes','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--exponent',type=float,choices=[1.5,1.75,2.5,3.5],required=True);a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use empty output')
    mesh=json.loads(a.base_meshes.read_text());base_hash=hashlib.sha256(a.base_model.read_bytes()).hexdigest();assert mesh['fcstd_sha256']==base_hash
    d=App.openDocument(str(a.base_model));original={o.Name:signature(o.Shape) for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()}
    parts=rear_bow_parts(a.exponent)
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        inner=[(190,182),(214,182),(214,145),(204,133),(190,145)];mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
        def wire(points,x):
            vs=[App.Vector(x,y,z) for y,z in points];return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
        pocket=profile(inner,'YZ',(side*94.6,0,0),side*25)
        flared=Part.makeLoft([wire(inner,side*94.6),wire(mouth,side*117)],True,True)
        name='RearArmourCheek'+suffix;parts[name]=parts[name].cut(pocket).cut(flared)
    checks=[]
    for n,s in parts.items():
        s.check(True);assert s.isValid() and len(s.Solids)==1 and s.isClosed();d.getObject(n).Shape=s
        item=next(o for o in mesh['objects'] if o['name']==n);verts,faces=s.tessellate(.12);item['vertices']=[list(v) for v in verts];item['faces']=faces
        checks.append({'name':n,'valid':True,'advanced_check_passed':True,'solids':1})
    a.output.mkdir(parents=True,exist_ok=True);model=a.output/'candidate.FCStd';d.recompute();d.saveAs(str(model));App.closeDocument(d.Name)
    d=App.openDocument(str(model));preserved=[]
    for o in d.Objects:
        if o.Name not in original or o.Name in parts:continue
        preserved.append({'name':o.Name,'unchanged_geometry_signature_6dp':signature(o.Shape)==original[o.Name]})
    assert all(x['unchanged_geometry_signature_6dp'] for x in preserved)
    contacts=[]
    for suffix in ['Left','Right']:
        for other in ['RearStructuralFrame','SideGuard'+suffix]:
            s=d.getObject('RearArmourCheek'+suffix).Shape;t=d.getObject(other).Shape
            contacts.append({'objects':['RearArmourCheek'+suffix,other],'gap_mm':s.distToShape(t)[0],'overlap_mm3':s.common(t).Volume})
    mesh['fcstd_sha256']=hashlib.sha256(model.read_bytes()).hexdigest();(a.output/'meshes.json').write_text(json.dumps(mesh))
    (a.output/'candidate-check.json').write_text(json.dumps({'fcstd_sha256':mesh['fcstd_sha256'],'baseline_fcstd_sha256':base_hash,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'exponent':a.exponent,'changed_objects':list(parts),'parts':checks,'preserved':preserved,'contacts':contacts,'status':'exploratory geometry'},indent=2)+'\n')
    print(model,flush=True)

if __name__=='__main__':main()
