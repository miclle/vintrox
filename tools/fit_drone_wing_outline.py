"""Back-project the reference wing boundary to its inclined 3D face plane.

Manual pixels are from original video frame 30. This constructs a CAD profile;
it does not warp a rendered image. Other camera angles must cross-check the fit.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

OUTLINE_PIXELS = [
    (117,11),(135,31),(225,133),(290,226),(378,351),(464,450),
    (479,478),(474,510),(456,534),(421,551),(389,549),(360,532),
    (339,510),(328,478),(318,442),(303,408),(278,377),(244,341),
    (211,294),(180,251),(148,207),(121,159),(105,118),(108,76),
]
DETAIL_PIXELS = {
    'crease':[(106,81),(198,189),(270,275),(300,330),(318,400),(328,478)],
    'stripe_1':[(225,145),(253,183),(212,275),(181,232)],
    'stripe_2':[(271,196),(286,216),(242,322),(221,292)],
}


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path,
                        default=root/'cad/drone-concept/comparison/wing-outline-fit.json')
    args = parser.parse_args()
    config_path = root/'cad/drone-concept/comparison/cameras.json'
    config = json.loads(config_path.read_text())
    pose = next(p for p in config['views'] if p['source_frame'] == 30)
    width, height = config['resolution']
    focal = pose['lens_mm']/pose['sensor_width_mm']*width
    origin = np.array(pose['eye_mm'])
    forward = np.array(pose['target_mm'])-origin
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0,0,1]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    # Existing wing inclination and outer paint face; fits to tips/hubs from
    # multiple video frames constrain this plane independently of the outline.
    normal = np.array([1,0,-.04/1.01])
    offset = -(173.5*.817+6-.04*8.8/1.01)
    points = []
    for x, y in OUTLINE_PIXELS:
        ray = forward+(x-width/2)/focal*right+(height/2-y)/focal*up
        point = origin+ray*(offset-normal@origin)/(normal@ray)
        points.append(point.tolist())
    local = [[(p[1]-33)/1.12, (p[2]+8.8)/1.01] for p in points]
    details = {}
    for name, pixels in DETAIL_PIXELS.items():
        coordinates = []
        for x, y in pixels:
            ray = forward+(x-width/2)/focal*right+(height/2-y)/focal*up
            point = origin+ray*(offset-normal@origin)/(normal@ray)
            coordinates.append([(point[1]-33)/1.12,(point[2]+8.8)/1.01])
        details[name] = {'source_pixels':pixels,'local_yz':coordinates}
    result = {
        'source_frame':30, 'source_outline_px':OUTLINE_PIXELS,
        'reference_video_sha256':config['reference_video_sha256'],
        'camera_config_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest(),
        'wing_plane_normal':normal.tolist(), 'wing_plane_offset':offset,
        'world_points_mm':points, 'local_yz':local,
        'fold_and_markings':details,
        'limitations':['manual boundary uncertainty', 'inclined planar face assumption',
                       'one-view outline requires multi-view cross-validation'],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'local_yz':[[round(v,2) for v in point] for point in local]}))


if __name__ == '__main__':
    main()
