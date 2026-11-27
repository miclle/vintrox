"""Inspect saved split side flanges, real holes, webs and wire terminations.

This verifies the modeled detail, not the original object's unknown hole count
or manufacturing intent. Source images and interpretation are bound separately.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'flange-detail-check.json')
    args=parser.parse_args();doc=App.openDocument(str(args.model))
    result={'fcstd_sha256':digest(args.model),'measurement_script_sha256':digest(Path(__file__)),
            'source_review_sha256':digest(folder/'flange-detail-review.json'),'sides':{},
            'limitations':['hole count and pitch, split angle and hidden geometry are appearance assumptions',
                          'saved geometry checks do not establish reference fidelity or manufacturability']}
    try:
        for side,suffix in ((-1,'Left'),(1,'Right')):
            shape=doc.getObject('PerforatedSpeakerFlange'+suffix).Shape
            holes={}
            for face in shape.Faces:
                surface=face.Surface
                if type(surface).__name__!='Cylinder' or not 1<surface.Radius<3 or abs(surface.Axis.x)<.99999:
                    continue
                center=surface.Center
                key=tuple(round(v,5) for v in (center.y,center.z,surface.Radius))
                if key in holes:continue
                ray=Part.makeLine(App.Vector(side*96,center.y,center.z),App.Vector(side*120,center.y,center.z))
                hole={'center_yz_mm':[center.y,center.z],'radius_mm':surface.Radius,
                      'radial_station_mm':math.hypot(center.y-129.09686,center.z-153.62312),
                      'flange_axis_intersection_mm':shape.common(ray).Length}
                holes[key]=hole
            webs=[];splits=[]
            for offset in (0,180):
                for radius,first,count in ((55.8,25.25,8),(60.3,34.5,7)):
                    for j in range(count):
                        a=math.radians(offset+first+18.5*j)
                        y,z=129.09686+radius*math.cos(a),153.62312+radius*math.sin(a)
                        ray=Part.makeLine(App.Vector(side*96,y,z),App.Vector(side*120,y,z))
                        webs.append({'radius_mm':radius,'angle_degrees':offset+first+18.5*j,
                                     'material_length_mm':shape.common(ray).Length})
                for radius in (52,55.8,60.3,62):
                    y=129.09686+radius*math.cos(math.radians(offset))
                    ray=Part.makeLine(App.Vector(side*96,y,153.62312),App.Vector(side*120,y,153.62312))
                    splits.append(shape.common(ray).Length)
            wires=[]
            for i in range(2):
                obj=doc.getObject(f'SpeakerBridgeWire{suffix}{i}')
                if obj is None:continue
                caps=[f for f in obj.Shape.Faces if type(f.Surface).__name__=='Plane']
                wires.append({'name':obj.Name,'valid':obj.Shape.isValid(),'solids':len(obj.Shape.Solids),
                              'cap_count':len(caps),
                              'end_flange_overlap_mm3':[obj.Shape.common(Part.makeSphere(2,f.CenterOfMass)).common(shape).Volume for f in caps]})
            bowl=doc.getObject('SpeakerVisualCone'+suffix).Shape
            cavity_probes=[]
            for degrees in (0,90,180,270):
                a=math.radians(degrees)
                y,z=129.09686+35*math.cos(a),153.62312+35*math.sin(a)
                probe=Part.makeCylinder(.6,2,App.Vector(side*113.52074,y,z),App.Vector(-side,0,0))
                wall_ray=Part.makeLine(App.Vector(side*113.52074,y,z),App.Vector(side*103.62074,y,z))
                cavity_probes.append({'angle_degrees':degrees,'mouth_probe_overlap_mm3':bowl.common(probe).Volume,
                                      'deeper_wall_intersection_mm':bowl.common(wall_ray).Length})
            result['sides'][suffix]={'valid':shape.isValid(),'solids':len(shape.Solids),
                'volume_mm3':shape.Volume,'holes':list(holes.values()),'web_probes':webs,
                'split_axis_intersection_mm':splits,'bridge_wires':wires,
                'bowl_valid':bowl.isValid(),'bowl_solids':len(bowl.Solids),'cavity_probes':cavity_probes,
                'old_screw_heads_present':[o.Name for o in doc.Objects if o.Name.startswith('SpeakerBolt'+suffix)]}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({side:{'solids':r['solids'],'holes':len(r['holes']),
              'max_hole_intersection_mm':max(h['flange_axis_intersection_mm'] for h in r['holes']),
              'min_web_mm':min(w['material_length_mm'] for w in r['web_probes']),
              'split_axis_intersection_mm':r['split_axis_intersection_mm'],'bridge_wires':r['bridge_wires'],
              'cavity_probes':r['cavity_probes']}
              for side,r in result['sides'].items()},indent=2))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
