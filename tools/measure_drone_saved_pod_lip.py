"""Measure saved toroidal lips and verify untouched archive members."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import FreeCAD as App
import Part
import numpy as np
from scipy.spatial import cKDTree

from fit_drone_lower_pod_outline import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['candidate', 'baseline', 'appearance-source', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--geometry-baseline', type=Path,
                        help='Immediate geometry parent, if different from the lip fit baseline')
    args = parser.parse_args()
    folder = args.candidate
    fit = json.loads((folder/'lip-fit.json').read_text())
    report = json.loads((folder/'candidate-check.json').read_text())
    camera_path = args.baseline.parent/'video-comparison/cameras.json'
    cameras = json.loads(camera_path.read_text())
    assert digest(args.baseline) == fit['baseline_fcstd_sha256']
    assert digest(camera_path) == fit['camera_config_sha256']
    changed = set(report['changed_objects'])
    geometry_baseline = args.geometry_baseline or args.baseline
    assert digest(geometry_baseline) == report['baseline_fcstd_sha256']
    with zipfile.ZipFile(folder/'candidate.FCStd') as saved, zipfile.ZipFile(geometry_baseline) as base, zipfile.ZipFile(args.appearance_source) as appearance:
        geometry = [n for n in base.namelist() if n.endswith('.brp') or '.Shape.Map.' in n]
        preserved = [n for n in geometry if n.split('.Shape.')[0] not in changed]
        assert all(saved.read(n) == base.read(n) for n in preserved)
        modified = [n for n in geometry if n not in saved.namelist() or saved.read(n) != base.read(n)]
        assert {n.split('.Shape.')[0] for n in modified} == changed
        gui = [n for n in appearance.namelist() if n == 'GuiDocument.xml' or
               n.startswith(('ShapeAppearance', 'LineColorArray', 'PointColorArray'))]
        assert 'GuiDocument.xml' in gui and all(saved.read(n) == appearance.read(n) for n in gui)
    doc = App.openDocument(str((folder/'candidate.FCStd').resolve()))
    try:
        screen = np.asarray([list(v.Point) for v in doc.getObject('ScreenPanel210x160x2').Shape.Vertexes])
        points, rings = {}, []
        for side, name in [(-1, 'LowerPodRim_1'), (1, 'LowerPodRim_001')]:
            shape = doc.getObject(name).Shape
            local = shape.copy()
            local.Placement = App.Placement()
            torus = local.Faces[0].Surface
            assert isinstance(torus, Part.Toroid)
            center, radius = torus.Center, torus.MajorRadius
            assert abs(center.z-fit['parameters'][0]) < 1e-7
            assert abs(radius-fit['parameters'][1]) < 1e-7
            points[side] = np.asarray([list(shape.Placement.multVec(center+App.Vector(radius*np.cos(a), radius*np.sin(a), 0)))
                                       for a in np.linspace(0, 2*np.pi, 1440, endpoint=False)])
            rings.append({'object': name, 'local_center_mm': list(center),
                          'major_radius_mm': radius, 'minor_radius_mm': torus.MinorRadius})
        rows = []
        for observation in fit['fitted']:
            frame, side = observation['source_frame'], observation['side']
            px = project(points[side], frame, cameras)
            distances, index = cKDTree(px).query(observation['reference_px'])
            span = float(np.ptp(project(screen, frame, cameras)[:, 0]))
            rows.append({'source_frame': frame, 'side': side,
                         'reference_px': observation['reference_px'],
                         'nearest_px': px[index].tolist(), 'distance_px': distances.tolist(),
                         'rms_px': float(np.sqrt(np.mean(distances**2))),
                         'max_fraction_projected_screen_width': float(max(distances)/span)})
    finally:
        App.closeDocument(doc.Name)
    result = {'fcstd_sha256': digest(folder/'candidate.FCStd'), 'script_sha256': digest(Path(__file__)),
              'baseline_fcstd_sha256': digest(args.baseline), 'fit_sha256': digest(folder/'lip-fit.json'),
              'geometry_baseline_fcstd_sha256': digest(geometry_baseline),
              'camera_config_sha256': digest(camera_path), 'saved_lips': rings, 'observations': rows,
              'unchanged_geometry_archive_members': len(preserved),
              'changed_geometry_archive_members': modified, 'appearance_archive_members_equal': len(gui),
              'limitations': ['saved torus centreline only; opaque visible boundary is a separate check',
                             'same manual observations as fitting; no fresh held-out data',
                             'no full-part contour or manufacturing acceptance']}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('unchanged archive members', len(preserved), 'GUI members', len(gui))
    print([(r['source_frame'], r['rms_px'], r['max_fraction_projected_screen_width']) for r in rows])


if __name__ == '__main__':
    main()
