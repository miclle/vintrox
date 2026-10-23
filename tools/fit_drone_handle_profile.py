"""Back-project visible handle-arm edges onto the retained outer mounting plane.

Frame 180 constructs the profile. Opposite-side frame 60 is held out for a
mirrored-profile check; both use the existing inferred camera calibration.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

CONSTRUCTION = [[467,106],[516,163],[351,303],[318,313],[291,290],
                [288,270],[300,246],[444,117],[455,110]]
MARKS = [ [[417,158],[425,151],[457,186],[449,193]],
          [[405,170],[413,163],[443,197],[435,204]],
          [[394,185],[405,176],[430,207],[402,213]] ]
OBSERVATIONS = [[467,106],[478,119],[491,134],[504,149],[516,163],
                [477,197],[438,230],[398,263],[351,303],[334,312],
                [318,313],[301,304],[291,290],[288,270],[292,257],
                [300,246],[333,216],[369,185],[407,150],[444,117],[455,110]]
ADDITIONAL = [[490,108],[510,122],[540,149],[571,178],[603,208],
              [635,239],[651,260],[658,279],[654,294],[641,307],[625,313],[609,312]]


def backproject(pixels, cameras, x=121.68):
    pose=cameras['views'][6];origin=np.array(pose['eye_mm'])
    forward=np.array(pose['target_mm'])-origin;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    focal=pose['lens_mm']/pose['sensor_width_mm']*940
    result=[]
    for px,py in pixels:
        ray=forward+(px-470)/focal*right+(400-py)/focal*up
        result.append((origin+ray*((x-origin[0])/ray[0])).tolist())
    return result


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    path=folder/'cameras.json';cameras=json.loads(path.read_text())
    result={'source_frame':180,'outer_plane_x_mm':121.68,'construction_px':CONSTRUCTION,
        'world_profile_mm':backproject(CONSTRUCTION,cameras),'mark_pixels':MARKS,
        'world_marks_mm':[backproject(p,cameras) for p in MARKS],
        'reference_outline_px':OBSERVATIONS,'additional_source_frame':60,
        'additional_reference_px':ADDITIONAL,
        'camera_config_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_video_sha256':cameras['reference_video_sha256'],
        'fit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['manual visible edge observations and fixed X mounting plane',
            'opposite-side symmetry and hidden grip joint inferred',
            'frame 60 held out from construction but shares inferred cameras',
            'appearance only; neither original topology nor physical measurements']}
    (folder/'handle-profile-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('profile',[[round(v,4) for v in p[1:]] for p in result['world_profile_mm']])
    print('marks',[[[round(v,4) for v in p[1:]] for p in m] for m in result['world_marks_mm']])

if __name__=='__main__':main()
