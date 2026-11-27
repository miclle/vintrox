"""Read saved rear panel bounds, recesses and circular lamp silhouettes.

Panel corners reuse the fitting observations; lamps use manual rear-view marks.
No check establishes the hidden function, sealing, light output or manufacture.
"""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
import numpy as np
from scipy.spatial import ConvexHull,cKDTree
from fit_drone_lower_pod_outline import project

BEACON_OBSERVATIONS=[(1,[[238,280],[242,264],[252,252],[268,249],[285,253],[297,266],
                       [300,280],[296,295],[283,307],[266,311],[250,305],[241,293]]),
    (-1,[[648,279],[652,263],[664,251],[680,248],[696,253],[708,265],
          [712,280],[708,295],[695,307],[680,310],[663,304],[652,294]])]


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser();parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'rear-rail-check.json');args=parser.parse_args()
    fit_path=folder/'rear-rail-fit.json';fit=json.loads(fit_path.read_text());camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    doc=App.openDocument(str(args.model))
    try:
        rail=doc.getObject('RearPortRail').Shape;b=rail.optimalBoundingBox(False,False)
        corners=np.array([[x,b.YMax,z] for x,z in [(b.XMax,b.ZMax),(b.XMin,b.ZMax),(b.XMin,b.ZMin),(b.XMax,b.ZMin)]])
        observations=[]
        for o in fit['observations']:
            pp=project(corners,o['source_frame'],cameras);dist=np.linalg.norm(pp-o['reference_px'],axis=1)
            observations.append({'source_frame':o['source_frame'],'reference_px':o['reference_px'],'saved_px':pp.tolist(),'distance_px':dist.tolist()})
        lamps=[]
        for side,px in BEACON_OBSERVATIONS:
            objects=[o for o in doc.Objects if o.Name.startswith('RearBeacon') and not o.Name.startswith('RearBeaconBase')
                     and o.Shape.optimalBoundingBox(False,False).Center.x*side>0]
            points=np.array([list(v) for o in objects for v in o.Shape.tessellate(.06)[0]])
            pp=project(points,120,cameras);hull=pp[ConvexHull(pp).vertices]
            boundary=np.concatenate([a+(b-a)*np.linspace(0,1,150)[:,None] for a,b in zip(hull,np.roll(hull,-1,axis=0))])
            dist,indices=cKDTree(boundary).query(px)
            lamps.append({'source_frame':120,'side':side,'reference_px':px,'saved_nearest_px':boundary[indices].tolist(),
                          'distance_px':dist.tolist()})
        probes=[]
        for i in range(7):
            p=App.Vector(42+i*2.25,b.YMax-.2,(b.ZMin+b.ZMax)/2)
            probes.append({'position_mm':list(p),'plate_overlap_mm3':rail.common(Part.makeSphere(.15,p)).Volume})
        distances=[v for o in observations for v in o['distance_px']]
        lamp_distances=[v for o in lamps for v in o['distance_px']]
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'saved_panel_corners_mm':corners.tolist(),'saved_panel_dimensions_mm':[b.XLength,b.ZLength,b.YLength],
            'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(np.array(distances)**2))),
            'max_distance_px':max(distances),'beacon_observations':lamps,
            'beacon_distance_rms_px':float(np.sqrt(np.mean(np.array(lamp_distances)**2))),
            'beacon_max_distance_px':max(lamp_distances),'vent_cavity_probes':probes,
            'limitations':['panel rectangle bounds extrapolate small rounded corners; same points fit placement',
                'lamp silhouettes use only a rear view and manually read dark borders',
                'convex silhouette excludes gold lamp bases; no physical or lighting validation',
                'cavity probes only show local recessed material; no functional ventilation claim']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ['saved_panel_dimensions_mm','distance_rms_px','max_distance_px','beacon_distance_rms_px','beacon_max_distance_px','vent_cavity_probes']},indent=2))
    finally:App.closeDocument(doc.Name)
if __name__=='__main__':main()
