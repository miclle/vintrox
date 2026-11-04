"""Recheck final saved loop lofts, contacts, support clearance and projections.

Centreline observations are the same manual fitting pixels, not independent
source data or complete visible boundaries. Final FCStd geometry is read anew.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import numpy as np
import Part
from scipy.spatial import cKDTree

from experiment_drone_petal_axial import advanced_errors
from fit_drone_lower_pod_outline import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['model', 'baseline', 'appearance-source', 'fit', 'cameras', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    fit = json.loads(args.fit.read_text())
    cameras = json.loads(args.cameras.read_text())
    assert digest(args.baseline) == fit['baseline_fcstd_sha256']
    assert digest(args.cameras) == fit['camera_config_sha256']
    changed = {'UnderbodyLoop0', 'UnderbodyLoop1'}
    with zipfile.ZipFile(args.model) as saved, zipfile.ZipFile(args.baseline) as baseline, zipfile.ZipFile(args.appearance_source) as appearance:
        geometry = [n for n in baseline.namelist() if n.endswith('.brp') or '.Shape.Map.' in n]
        preserved = [n for n in geometry if n.split('.Shape.')[0] not in changed]
        assert all(saved.read(n) == baseline.read(n) for n in preserved)
        modified = [n for n in geometry if saved.read(n) != baseline.read(n)]
        assert {n.split('.Shape.')[0] for n in modified} == changed
        gui = [n for n in appearance.namelist() if n == 'GuiDocument.xml' or
               n.startswith(('ShapeAppearance', 'LineColorArray', 'PointColorArray'))]
        assert 'GuiDocument.xml' in gui
        assert all(saved.read(n) == appearance.read(n) for n in gui)
    doc = App.openDocument(str(args.model.resolve()))
    try:
        screen = np.asarray([list(v.Point) for v in doc.getObject('ScreenPanel210x160x2').Shape.Vertexes])
        supports = [o for o in doc.Objects if o.Name.startswith(
                    ('SupportShaft', 'SupportSocket', 'SupportFoot', 'CentralSupportSeat'))]
        belly = doc.getObject('ClosedBellyPan').Shape
        paths, checks = {}, []
        for name in sorted(changed):
            shape = doc.getObject(name).Shape
            assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
            errors = advanced_errors(shape)
            assert not errors, (name, errors)
            face = max(shape.Faces, key=lambda f: f.Area)
            u0, u1, v0, v1 = face.ParameterRange
            assert all((face.valueAt(u0, float(v))-face.valueAt(u1, float(v))).Length < 1e-6
                       for v in np.linspace(v0, v1, 9))
            points = np.asarray([np.mean([list(face.valueAt(float(u), float(v)))
                               for u in np.linspace(u0, u1, 128, endpoint=False)], axis=0)
                               for v in np.linspace(v0, v1, 1000)])
            paths[name] = points
            expected = np.asarray(fit['centreline_paths_mm'][name])[[0, -1]]
            endpoint_error = np.linalg.norm(points[[0, -1]]-expected, axis=1)
            assert max(endpoint_error) < .01, (name, endpoint_error)
            contacts = [shape.common(Part.makeSphere(3, App.Vector(*p))).common(belly).Volume
                        for p in expected]
            assert min(contacts) > 0, (name, contacts)
            overlaps = {o.Name: shape.common(o.Shape).Volume for o in supports}
            assert max(overlaps.values()) < 1e-6, (name, overlaps)
            checks.append({'object': name, 'advanced_errors': errors,
                           'valid_closed_single_solid': True,
                           'endpoint_centre_error_mm': endpoint_error.tolist(),
                           'actual_loop_endpoint_belly_overlap_mm3': contacts,
                           'support_overlap_mm3': overlaps})
        observations = []
        for row in ([] if fit.get('observation_kind') else fit['fitted']):
            frame = row['source_frame']
            px = project(paths['UnderbodyLoop1' if row['side'] == 1 else 'UnderbodyLoop0'], frame, cameras)
            distances, indices = cKDTree(px).query(row['reference_px'])
            screen_span = float(np.ptp(project(screen, frame, cameras)[:, 0]))
            observations.append({'source_frame': frame, 'side': row['side'],
                                 'reference_px': row['reference_px'],
                                 'saved_nearest_px': px[indices].tolist(),
                                 'distance_px': distances.tolist(),
                                 'rms_px': float(np.sqrt(np.mean(distances**2))),
                                 'max_px': float(max(distances)),
                                 'projected_screen_horizontal_span_px': screen_span,
                                 'max_fraction_projected_screen_width': float(max(distances)/screen_span)})
    finally:
        App.closeDocument(doc.Name)
    result = {'status': 'final-saved-loop-geometry-checked',
              'fcstd_sha256': digest(args.model), 'baseline_fcstd_sha256': digest(args.baseline),
              'fit_sha256': digest(args.fit), 'camera_config_sha256': digest(args.cameras),
              'script_sha256': digest(Path(__file__)),
              'unchanged_geometry_archive_members': len(preserved),
              'changed_geometry_archive_members': modified,
              'appearance_archive_members_equal': len(gui),
              'solid_checks': checks, 'observations': observations,
              'rms_px': float(np.sqrt(np.mean(np.concatenate([r['distance_px'] for r in observations])**2))) if observations else None,
              'observation_kind': fit.get('observation_kind', 'manual centreline samples'),
              'limitations': ['1000 by 128 surface-parameter samples; finite centreline sampling',
                             'same uncertain manual observations as fitting; no fresh held-out evidence',
                             'centreline errors do not prove complete visible contour within 5 percent',
                             'no physical, manufacturing, optical or electrical acceptance']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('saved centreline RMS', result['rms_px'])
    print([(r['source_frame'], r['side'], r['max_fraction_projected_screen_width']) for r in observations])


if __name__ == '__main__':
    main()
