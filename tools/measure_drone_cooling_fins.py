"""Compare saved fin spacing with repeated highlights in the rear video frame.

The count is inferred from visible periodic bands; it is not source mesh data.
"""
import hashlib
import json
from pathlib import Path
import re

import FreeCAD as App
import numpy as np

from measure_drone_landmarks import project


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    camera_path = folder/'camera-fit.json'
    camera = json.loads(camera_path.read_text())
    model = root/'cad/drone-concept/vintrox-drone-concept.FCStd'
    video = root/'references/alexander-shevchuk-drone/video-cam.mp4'
    # Repeated bright bands around row 228, ignoring the antenna occlusion.
    bands = [[332,354,377,400,422,445], [512,534,557,579,601,624]]
    reference_pitch = float(np.median(np.concatenate([np.diff(b) for b in bands])))
    doc = App.openDocument(str(model))
    try:
        fins = sorted([o for o in doc.Objects if re.fullmatch(r'RearCoolingFin\d+',o.Name)],
                      key=lambda o:o.Shape.CenterOfMass.x)
        points = []
        for fin in fins:
            bb = fin.Shape.optimalBoundingBox(False,False)
            # This station lies on the straight part of the saved rear edge.
            point = [(bb.XMin+bb.XMax)/2,bb.YMax,bb.ZMin+8]
            points.append({'name':fin.Name,'rear_edge_station_mm':point,
                           'projected_px':project(point,4,camera['parameters']).tolist(),
                           'thickness_mm':bb.XLength,'height_mm':bb.ZLength})
        projected = sorted(p['projected_px'][0] for p in points)
        pitch = float(np.median(np.diff(projected)))
        wraps = [o for o in doc.Objects if re.fullmatch(r'GripBand\d+',o.Name)]
        wrap_pixels = np.array([project(list(v),4,camera['parameters']) for o in wraps
                                for v in o.Shape.tessellate(.3)[0]])
        wrap_bounds = [*wrap_pixels.min(axis=0),*wrap_pixels.max(axis=0)]
        reference_wrap_bounds = [272,104,672,180]
        report = {'fcstd_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
                  'camera_fit_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
                  'source_video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
                  'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'source_frame':120,'source_row_approx_px':228,'source_bands_x_px':bands,
                  'reference_pitch_px':reference_pitch,'inferred_reference_count':15,
                  'saved_fin_count':len(fins),'saved_pitch_px':pitch,
                  'pitch_difference_px':abs(pitch-reference_pitch),'saved_fins':points,
                  'grip_wrap_parts':len(wraps),
                  'grip_wrap_solids':sum(len(o.Shape.Solids) for o in wraps),
                  'grip_wrap_volume_mm3':[o.Shape.Volume for o in wraps],
                  'reference_wrap_bounds_px':reference_wrap_bounds,
                  'saved_wrap_bounds_px':wrap_bounds,
                  'wrap_bounds_max_difference_px':float(np.max(abs(np.array(wrap_bounds)-reference_wrap_bounds))),
                  'limitations':['source highlights approximate periodic fin positions',
                                 'pitch depends on visible surface depth; not complete profile validation',
                                 'manual source marks and inferred count, not original mesh or hardware measurements',
                                 'wrap bounds are manually read to approximately two pixels; not wrinkle correspondence',
                                 'grip folds are modeled approximations, not recovered cloth topology']}
        (folder/'cooling-fin-check.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('saved_fin_count','reference_pitch_px','saved_pitch_px',
                                               'pitch_difference_px','grip_wrap_solids')}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
