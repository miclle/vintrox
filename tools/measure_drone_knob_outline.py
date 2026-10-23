"""Project the saved first-knob cap boundary into the original fitting views."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import numpy as np
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    p.add_argument('--output',type=Path,default=folder/'knob-outline-check.json');args=p.parse_args()
    fit_path=folder/'knob-outline-fit.json';fit=json.loads(fit_path.read_text())
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text());doc=App.openDocument(str(args.model))
    try:
        shape=doc.getObject('KnobFace0').Shape
        face=min([f for f in shape.Faces if type(f.Surface).__name__=='Plane'],key=lambda f:f.CenterOfMass.y)
        points=np.array([list(v) for e in face.OuterWire.Edges for v in e.discretize(Number=1440)])
        observations=[]
        for o in fit['observations']:
            pp=project(points,o['source_frame'],cameras);dd,ii=cKDTree(pp).query(o['reference_px'])
            observations.append({'source_frame':o['source_frame'],'reference_px':o['reference_px'],
                'saved_nearest_px':pp[ii].tolist(),'distance_px':dd.tolist()})
        dd=[d for o in observations for d in o['distance_px']]
        axis=face.normalAt(0,0)
        if axis.y>0:axis=-axis
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'saved_cap_center_mm':list(face.CenterOfMass),'saved_cap_area_mm2':face.Area,
            'saved_cap_axis':list(axis),'observations':observations,
            'distance_rms_px':float(np.sqrt(np.mean(np.array(dd)**2))),'max_distance_px':max(dd),
            'limitations':fit['limitations']}
        args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['saved_cap_center_mm','saved_cap_axis','distance_rms_px','max_distance_px']}))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
