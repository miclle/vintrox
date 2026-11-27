"""Read the actual saved petal-end arcs and compare them with reference pixels.

This measures the inferred exit circle only, not the complete nozzle contour.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree

from measure_drone_landmarks import project


def main():
    root = Path(__file__).resolve().parents[1]
    cad = root/'cad/drone-concept'
    folder = cad/'comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=cad/'vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'nozzle-outline-check.json')
    parser.add_argument('--expected-petals',type=int,help='Explicit leaf count for isolated geometry candidates')
    args=parser.parse_args()
    model=args.model
    manifest = json.loads((cad/'concept-manifest.json').read_text())
    fit_path = folder/'nozzle-mouth-fit.json'
    fit = json.loads(fit_path.read_text())
    camera_path = folder/'camera-fit.json'
    camera = json.loads(camera_path.read_text())
    axis = App.Vector(*manifest['bass_axis']); axis.normalize()
    origin = App.Vector(*manifest['bass_origin_mm'])
    doc = App.openDocument(str(model))
    try:
        candidates = []
        names = [o.Name for o in doc.Objects if re.fullmatch(r'NozzlePetal\d+',o.Name)]
        for name in names:
            obj = doc.getObject(name)
            faces = [f for f in obj.Shape.Faces if type(f.Surface).__name__ == 'Plane'
                     and abs(f.normalAt(0,0).dot(axis)) > .9]
            for end in faces:
                normal = end.normalAt(0,0)
                if normal.dot(axis) < 0:
                    normal = -normal
                n=np.array(normal)
                u=np.cross(n,[0,0,1]);u/=np.linalg.norm(u)
                v=np.cross(n,u)
                anchor=np.array(end.CenterOfMass)
                circles=[]
                # OCCT stores the transferred circular boundaries as B-splines.
                # Recover circles from saved edge samples, rejecting straight edges.
                for edge in end.Edges:
                    samples=np.array([list(p) for p in edge.discretize(Number=25)])-anchor
                    x,y=samples@u,samples@v
                    system=np.column_stack([2*x,2*y,np.ones(len(x))])
                    if np.linalg.matrix_rank(system)<3:
                        continue
                    cx,cy,constant=np.linalg.lstsq(system,x*x+y*y,rcond=None)[0]
                    r2=constant+cx*cx+cy*cy
                    if r2<=0:
                        continue
                    radius=np.sqrt(r2)
                    error=np.max(abs(np.hypot(x-cx,y-cy)-radius))
                    if error<.001 and 10<radius<200:
                        circles.append((radius,anchor+cx*u+cy*v,float(error)))
                if not circles:
                    continue
                radius,center,error=max(circles,key=lambda c:c[0])
                candidates.append({'name':obj.Name,'center_mm':center.tolist(),
                             'radius_mm':float(radius),'axis':list(normal),'edge_fit_max_error_mm':error})
        # A recess end plane can cross the nozzle axis beyond the actual tip.
        # Select complete shared circles instead of ordering extrapolated planes.
        # This uses saved CAD geometry only, before consulting reference pixels.
        rings = []
        for seed in candidates:
            matches = [c for c in candidates
                       if np.linalg.norm(np.array(c['center_mm'])-seed['center_mm']) < .001
                       and abs(c['radius_mm']-seed['radius_mm']) < .001
                       and np.linalg.norm(np.array(c['axis'])-seed['axis']) < .001]
            by_name = {c['name']: c for c in matches}
            if set(by_name) == set(names) and not any(
                    np.linalg.norm(np.array(ring[0]['center_mm'])-seed['center_mm']) < .001
                    and abs(ring[0]['radius_mm']-seed['radius_mm']) < .001 for ring in rings):
                rings.append(list(by_name.values()))
        if len(rings) < 2:
            raise RuntimeError('Missing complete shared root or terminal circle')
        arcs = max(rings,key=lambda ring:np.dot(np.mean([c['center_mm'] for c in ring],axis=0)-np.array(origin),np.array(axis)))
        if len(arcs) != (args.expected_petals or manifest['nozzle_petals']):
            raise RuntimeError('Missing saved nozzle terminal arcs')
        center = np.mean([a['center_mm'] for a in arcs],axis=0)
        radius = float(np.mean([a['radius_mm'] for a in arcs]))
        normal = np.mean([a['axis'] for a in arcs],axis=0); normal /= np.linalg.norm(normal)
        spread = max(np.linalg.norm(np.array(a['center_mm'])-center) for a in arcs)
        if spread > .001 or max(abs(a['radius_mm']-radius) for a in arcs) > .001:
            raise RuntimeError('Petals do not share a terminal circle')
        u = np.cross(normal,[0,0,1]); u /= np.linalg.norm(u)
        v = np.cross(normal,u)
        angle = np.linspace(0,2*np.pi,1080,endpoint=False)
        points = center+radius*(np.cos(angle)[:,None]*u+np.sin(angle)[:,None]*v)
        observations = []
        distances = []
        for view in fit['observations']:
            projected = np.array([project(p,view['source_frame']//30,camera['parameters']) for p in points])
            distance,index = cKDTree(projected).query(view['reference_px'])
            distances.extend(distance.tolist())
            observations.append({'source_frame':view['source_frame'],'reference_px':view['reference_px'],
                                 'saved_cad_circle_px':projected[index].tolist(),'distance_px':distance.tolist()})
        report = {'fcstd_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
                  'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
                  'camera_fit_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
                  'selection_method':'outer circular arcs shared by all saved leaves; furthest complete section along nozzle axis',
                  'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'terminal_arc_count':len(arcs),'terminal_arcs':arcs,'saved_center_mm':center.tolist(),
                  'saved_radius_mm':radius,'saved_axis':normal.tolist(),'center_spread_mm':float(spread),
                  'distance_rms_px':float(np.sqrt(np.mean(np.array(distances)**2))),
                  'max_distance_px':max(distances),'observations':observations,
                  'limitations':['only terminal circle, not complete nozzle','manual source pixel uncertainty',
                                 'continuous circle interpolates gaps between petal ends']}
        args.output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('terminal_arc_count','saved_center_mm','saved_radius_mm',
                                                'distance_rms_px','max_distance_px')}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
