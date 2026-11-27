"""Read back the front controls against the three-view fitting observations.

Measurements reuse the fitting points. They test saved geometry and placement,
not independent accuracy, physical clearances or electrical functionality.
"""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import numpy as np
from fit_drone_lower_pod_outline import project


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'front-control-check.json');args=parser.parse_args()
    fit_path=folder/'front-control-fit.json';fit=json.loads(fit_path.read_text())
    camera_path=folder/'cameras.json';cameras=json.loads(camera_path.read_text())
    doc=App.openDocument(str(args.model))
    try:
        shape=lambda name:doc.getObject(name).Shape
        bounds=lambda name:shape(name).optimalBoundingBox(False,False)
        b=bounds('ControlRail');y=bounds('ControlRailLip').YMin
        points={'rail':np.array([[x,y,z] for x,z in [(b.XMin,b.ZMax),(b.XMax,b.ZMax),(b.XMax,b.ZMin),(b.XMin,b.ZMin)]])}
        for group,prefix,count in [('knobs','KnobFace',3),('buttons','RedKey',4)]:
            bb=[bounds(prefix+str(i)) for i in range(count)]
            if group=='knobs':
                caps=[]
                for i in range(count):
                    faces=[f for f in shape(prefix+str(i)).Faces if type(f.Surface).__name__=='Plane']
                    caps.append(list(min(faces,key=lambda f:f.CenterOfMass.y).CenterOfMass))
                points[group]=np.array(caps)
            else:
                points[group]=np.array([[b.Center.x,b.YMin,b.Center.z] for b in bb])
        groups={}
        for name,pp in points.items():
            observations=[]
            for o in fit['groups'][name]['observations']:
                projected=project(pp,o['source_frame'],cameras)
                distances=np.linalg.norm(projected-o['reference_px'],axis=1)
                observations.append({'source_frame':o['source_frame'],'reference_px':o['reference_px'],
                    'saved_px':projected.tolist(),'distance_px':distances.tolist()})
            distances=np.array([v for o in observations for v in o['distance_px']])
            groups[name]={'saved_points_mm':pp.tolist(),'observations':observations,
                'distance_rms_px':float(np.sqrt(np.mean(distances**2))),'max_distance_px':float(max(distances))}
        joints={}
        pairs=[('ControlRailEnd'+side,'ControlRail') for side in ('Left','Right')]
        for i in range(3):
            pairs.extend([(f'KnobBase{i}','ControlInset'),(f'KnobRing{i}',f'KnobBase{i}'),
                          (f'KnobFace{i}',f'ControlKnob{i}'),(f'KnobPointer{i}',f'KnobFace{i}')])
        for i in range(4):pairs.append((f'RedKey{i}',f'KeySocket{i}'))
        if doc.getObject('ControlKeyBed'):
            pairs.extend([('ControlKeyBed','ControlInset'),('StatusKeyLens','ControlKeyBed'),
                          ('StatusKeyFrame','ControlKeyBed')])
        for a,b in pairs:
            joints[a+' / '+b]={'gap_mm':shape(a).distToShape(shape(b))[0],
                              'overlap_mm3':shape(a).common(shape(b)).Volume}
        result={'fcstd_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
            'source_fit_sha256':hashlib.sha256(fit_path.read_bytes()).hexdigest(),
            'camera_config_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
            'source_video_sha256':fit['source_video_sha256'],
            'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'groups':groups,'saved_joints':joints,'limitations':fit['limitations']+[
                'rail corners use body rectangle bounds and lip front plane; small rounded corners extrapolated',
                'legacy knob-center observations are retained for historical comparison; current cap shape uses knob-outline-fit.json',
                'finite contact and overlap are appearance continuity checks, not assembly validation']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({name:{k:v[k] for k in ['distance_rms_px','max_distance_px']} for name,v in groups.items()}))
        print(json.dumps(joints))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
