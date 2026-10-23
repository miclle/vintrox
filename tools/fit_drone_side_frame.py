"""Back-project the visible gold-side frame into the fixed side plate plane.

Manual frame-180 points constrain the Y/Z profile, not the X station. The latter
stays at the existing mounting plane and must be checked in other orbit views.
"""
import hashlib
import json
from pathlib import Path

import numpy as np


OBSERVATIONS = {
    'light': [[263,402],[300,316],[548,322],[558,335],
              [558,488],[438,605],[302,604],[263,561]],
    'outer': [[248,400],[285,306],[550,307],[584,330],
              [584,514],[448,655],[315,648],[248,603]],
    'spine': [[187,290],[281,287],[250,394],[248,625],[196,624]],
    'wire_blue': [[285,355],[297,330],[319,320],[338,324],[345,337],
                  [335,347],[320,342],[323,331],[349,328],[368,341]],
    'wire_red': [[282,540],[285,564],[297,575],[310,558],[328,560],
                 [333,585],[347,596],[357,584],[365,571]],
    'wire_white': [[277,526],[275,553],[285,572],[315,581],[350,591],[378,587]],
}


def main():
    root = Path(__file__).resolve().parents[1]
    cameras = root/'cad/drone-concept/comparison/cameras.json'
    config = json.loads(cameras.read_text())
    pose = config['views'][6]
    origin = np.array(pose['eye_mm'])
    forward = np.array(pose['target_mm'])-origin
    forward /= np.linalg.norm(forward)
    right = np.cross(forward,[0,0,1]); right /= np.linalg.norm(right)
    up = np.cross(right,forward)
    focal = pose['lens_mm']/pose['sensor_width_mm']*940
    result = {'source_frame':180,
              'camera_config_sha256':hashlib.sha256(cameras.read_bytes()).hexdigest(),
              'source_video_sha256':config['reference_video_sha256'],
              'source_pixels':OBSERVATIONS,'profiles':{},
              'limitations':['manual pixels and partially occluded edges',
                             'X mounting planes assumed from existing model',
                             'mirror symmetry assumed for the structural frame',
                             'wire pixels describe visible paths; hidden terminations are inferred',
                             'other views must cross-check the resulting solid']}
    for name,points in OBSERVATIONS.items():
        plane_x = (114 if name == 'spine' else 136 if name in ('wire_red','wire_white')
                   else 142*.84 if name == 'wire_blue' else 139.5*.84)
        world = []
        for x,y in points:
            ray = forward+(x-470)/focal*right+(400-y)/focal*up
            world.append(origin+ray*((plane_x-origin[0])/ray[0]))
        local = [[p[1]/1.25,(p[2]-24)/.84] for p in world]
        result['profiles'][name] = {'plane_x_mm':plane_x,
                                    'world_points_mm':[p.tolist() for p in world],
                                    'pre_transform_yz_mm':local}
        print(name, [[round(v,2) for v in p] for p in
                     ([p[1:] for p in world] if name == 'spine' else local)])
    path = root/'cad/drone-concept/comparison/side-frame-fit.json'
    path.write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
