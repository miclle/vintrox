"""Recover the saved instrument rim plane and compare fixed source corners.

Also report the rounded roof's projected outer boundary at visible source marks;
this is a local appearance check, not a complete foreground or structural test.
"""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import numpy as np
from scipy.spatial import ConvexHull,cKDTree
from fit_drone_lower_pod_outline import project

from fit_drone_roof_crown import ROOF_OBSERVATIONS


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser();parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'roof-instrument-check.json');args=parser.parse_args()
    fit_path=folder/'roof-instrument-fit.json';fit=json.loads(fit_path.read_text());camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    doc=App.openDocument(str(args.model))
    try:
        rim=doc.getObject('InstrumentRim').Shape;panel=doc.getObject('TopInstrumentPanel').Shape
        candidates=[]
        for f in rim.Faces:
            a,b,c,d=f.ParameterRange;n=f.normalAt((a+b)/2,(c+d)/2)
            if n.z>.5 and abs(n.x)<1e-5:candidates.append((f.Area,np.array(list(n))))
        normal=max(candidates,key=lambda q:q[0])[1];normal/=np.linalg.norm(normal)
        slope=np.array([0,normal[2],-normal[1]])
        verts=np.array([list(v) for v in rim.tessellate(.05)[0]])
        u=verts@slope;h=verts@normal;xs=[verts[:,0].min(),verts[:,0].max()];us=[u.min(),u.max()]
        corners=np.array([np.array([x,0,0])+slope*t+normal*h.max() for x,t in [(xs[0],us[0]),(xs[1],us[0]),(xs[1],us[1]),(xs[0],us[1])]])
        observations=[]
        for o in fit['observations']:
            pp=project(corners,o['source_frame'],cameras)[o['corner_indices']];dist=np.linalg.norm(pp-o['reference_px'],axis=1)
            observations.append({'source_frame':o['source_frame'],'reference_px':o['reference_px'],
                'saved_px':pp.tolist(),'distance_px':dist.tolist()})
        roofs=[o.Shape for o in doc.Objects if o.Name.startswith(('SlopedUpperArmour','RoofSideClosure'))]
        roof_vertices=np.array([list(v) for s in roofs for v in s.tessellate(.1)[0]])
        roof_obs=[]
        for frame,points in ROOF_OBSERVATIONS:
            pp=project(roof_vertices,frame,cameras);hull=pp[ConvexHull(pp).vertices]
            boundary=np.concatenate([a+(b-a)*np.linspace(0,1,200)[:,None] for a,b in zip(hull,np.roll(hull,-1,axis=0))])
            dist,indices=cKDTree(boundary).query(points)
            roof_obs.append({'source_frame':frame,'reference_px':points,'saved_nearest_px':boundary[indices].tolist(),'distance_px':dist.tolist()})
        distances=[v for o in observations for v in o['distance_px']]
        roof_distances=[v for o in roof_obs for v in o['distance_px']]
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'roof_fit_sha256':hashlib.sha256((folder/'roof-crown-fit.json').read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'saved_rim_corners_mm':corners.tolist(),'saved_rim_width_mm':xs[1]-xs[0],
            'saved_rim_slope_length_mm':us[1]-us[0],
            'saved_rim_pitch_deg':float(np.degrees(np.arctan2(-normal[1],normal[2]))),
            'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(np.array(distances)**2))),
            'max_distance_px':max(distances),'roof_observations':roof_obs,
            'roof_distance_rms_px':float(np.sqrt(np.mean(np.array(roof_distances)**2))),
            'roof_max_distance_px':max(roof_distances),
            'rim_panel_overlap_mm3':rim.common(panel).Volume,
            'rim_mount_overlap_mm3':rim.common(doc.getObject('InstrumentMount').Shape).Volume if doc.getObject('InstrumentMount') else None,
            'mount_roof_overlap_mm3':[doc.getObject('InstrumentMount').Shape.common(s).Volume for s in roofs] if doc.getObject('InstrumentMount') else None,
            'rim_roof_overlap_mm3':[rim.common(s).Volume for s in roofs],
            'panel_roof_overlap_mm3':[panel.common(s).Volume for s in roofs],
            'access_roof_overlap_mm3':[doc.getObject('RoofAccessPanel').Shape.common(s).Volume for s in roofs],
            'limitations':['manual border corners and same observations used for instrument fitting',
                'fixed inferred cameras; planar rectangle assumed; ignores corner roll radius',
                'roof convex silhouette measured at visible marks only; occlusion and hidden surfaces not validated',
                'appearance contact only, not structural, display or manufacturing validation']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ['observations','roof_observations']},indent=2))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
