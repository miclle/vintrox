"""Read the saved rear-frame rake, contacts and three legacy appearance traces.

These traces diagnose the outside rear corner. They do not prove hidden surface
continuity, and the projected convex edge does not account for occluding parts.
"""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
import numpy as np
from scipy.spatial import ConvexHull, cKDTree

from fit_drone_lower_pod_outline import project

OBSERVATIONS = [
    (60, 'Left', [[307,420],[308,455],[310,481],[317,503],[337,533],
                  [362,561],[387,590],[416,619],[443,642],[464,654]]),
    (180, 'Right', [[638,420],[638,455],[636,480],[628,505],[608,534],
                    [581,563],[554,592],[526,620],[500,643],[478,654]]),
    (90, 'Left', [[508,501],[526,534],[548,568],[573,604],[594,631],[608,643]]),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output', type=Path, default=folder/'rear-rake-check.json')
    args = parser.parse_args()
    camera_path = folder/'cameras.json'
    cameras = json.loads(camera_path.read_text())
    doc = App.openDocument(str(args.model))
    try:
        observations = []
        for frame, side, reference in OBSERVATIONS:
            shape = doc.getObject('RearArmourCheek'+side).Shape
            points = np.array([list(p) for p in shape.tessellate(.08)[0]])
            pixels = project(points, frame, cameras)
            hull = pixels[ConvexHull(pixels).vertices]
            edge = np.concatenate([a+(b-a)*np.linspace(0,1,200)[:,None]
                                   for a,b in zip(hull,np.roll(hull,-1,axis=0))])
            distance, indices = cKDTree(edge).query(reference)
            observations.append({'source_frame':frame,'object':'RearArmourCheek'+side,
                'reference_px':reference,'saved_nearest_px':edge[indices].tolist(),
                'distance_px':distance.tolist(),'distance_rms_px':float(np.sqrt(np.mean(distance**2))),
                'max_distance_px':float(max(distance))})
        pairs = [('RearServicePanel','RearLowerSlope'),('RearStructuralFrame','RearServicePanel')]
        for side in ('Left','Right'):
            pairs += [('RearArmourCheek'+side,'RearStructuralFrame'),
                      ('RearArmourCheek'+side,'SideGuard'+side)]
        contacts = []
        for first,second in pairs:
            a,b = doc.getObject(first).Shape,doc.getObject(second).Shape
            contacts.append({'objects':[first,second], 'gap_mm':a.distToShape(b)[0],
                             'overlap_mm3':a.common(b).Volume})
        panel = doc.getObject('RearServicePanel').Shape
        probes = []
        for x in (-80,80):
            for z in (90,105,120):
                y=224+(z-126)*78/68
                for kind,depth in [('sloped_panel',y),('behind_sloped_panel',241)]:
                    probe=Part.makeSphere(.5,App.Vector(x,depth,z))
                    probes.append({'kind':kind,'point_mm':[x,depth,z],
                                   'overlap_mm3':panel.common(probe).Volume})
        parts=[]
        for name in ['RearServicePanel','RearStructuralFrame','RearArmourCheekLeft',
                     'RearArmourCheekRight','RearCyanFrame','RearRecessLiner']:
            shape=doc.getObject(name).Shape
            errors=[]
            try:shape.check(True)
            except ValueError as e:errors=str(e).splitlines()
            parts.append({'name':name,'valid':shape.isValid(),'solids':len(shape.Solids),
                          'closed':all(s.isClosed() for s in shape.Solids),
                          'bop_check_passed':not errors,'bop_errors':errors})
        d=np.array([v for o in observations for v in o['distance_px']])
        result={'fcstd_sha256':digest(args.model),'camera_config_sha256':digest(camera_path),
            'source_video_sha256':cameras['reference_video_sha256'],
            'measurement_script_sha256':digest(Path(__file__)),
            'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(d*d))),
            'max_distance_px':float(max(d)),'contacts':contacts,'probes':probes,'parts':parts,
            'limitations':['manual visible rear-corner traces, not measured dimensions',
                'projected convex part outline does not model occlusion by adjacent parts',
                'legacy traces mix visible edges and highlight creases; use rear-transition-check.json for revised boundary observations',
                'local material and contact probes do not establish complete surface continuity',
                'no manufacture, strength or physical assembly validation']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ['fcstd_sha256','distance_rms_px','max_distance_px','contacts','parts']},indent=2))
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
