"""Build two swept decorative loop paths from a fixed-camera fit record."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
import numpy as np
from scipy.spatial import cKDTree

from experiment_drone_petal_axial import advanced_errors, signature
from fit_drone_lower_pod_outline import project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loop_loft(points, parameters=None, radius=2.2):
    curve = Part.BSplineCurve()
    keywords = {'Parameters': parameters} if parameters is not None else {}
    curve.interpolate([App.Vector(*p) for p in points], **keywords)
    # The 3D pipe-shell sweep reports GeomAbs_C0 in OCCT even with a C2
    # centreline. Smooth circular-section lofts avoid that surface failure.
    sections = []
    for value in np.linspace(curve.FirstParameter, curve.LastParameter, 40):
        sections.append(Part.Wire([Part.makeCircle(radius, curve.value(float(value)),
                                                  curve.tangent(float(value))[0])]))
    return Part.makeLoft(sections, True, False)


def main():
    parser = argparse.ArgumentParser()
    for name in ['base', 'mesh', 'fit', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--radius', type=float, default=2.2)
    args = parser.parse_args()
    if not np.isfinite(args.radius) or args.radius <= 0:
        raise ValueError('radius must be finite and positive')
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('output must be empty')
    mesh = json.loads(args.mesh.read_text())
    fit = json.loads(args.fit.read_text())
    base_hash = digest(args.base)
    if mesh['fcstd_sha256'] != base_hash or fit['baseline_fcstd_sha256'] != base_hash:
        raise ValueError('baseline hashes differ')
    doc = App.openDocument(str(args.base.resolve()))
    changed = ['UnderbodyLoop0', 'UnderbodyLoop1']
    baseline_loops = {n: doc.getObject(n).Shape.copy() for n in changed}
    before = {o.Name: signature(o.Shape) for o in doc.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()}
    try:
        for name in changed:
            parameters = fit.get('source_control_parameters') if fit.get('method', '').startswith('11 chord-parameter') else None
            shape = loop_loft(fit['centreline_paths_mm'][name], parameters, args.radius)
            if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1 or advanced_errors(shape):
                raise ValueError('invalid swept loop: '+name)
            doc.getObject(name).Shape = shape
        doc.recompute()
        args.output.mkdir(parents=True, exist_ok=True)
        doc.saveAs(str((args.output/'candidate.FCStd').resolve()))
    finally:
        App.closeDocument(doc.Name)
    model = args.output/'candidate.FCStd'
    doc = App.openDocument(str(model.resolve()))
    try:
        preserved = [name for name in before if name not in changed]
        for name in preserved:
            assert signature(doc.getObject(name).Shape) == before[name], name
        contacts, collisions, paths = [], [], {}
        belly = doc.getObject('ClosedBellyPan').Shape
        supports = [n for n in preserved if n.startswith(('SupportShaft', 'SupportSocket', 'SupportFoot', 'CentralSupportSeat'))]
        for name in changed:
            shape = doc.getObject(name).Shape
            assert not advanced_errors(shape)
            for endpoint in (fit['centreline_paths_mm'][name][0], fit['centreline_paths_mm'][name][-1]):
                probe = Part.makeSphere(args.radius, App.Vector(*endpoint))
                overlap = probe.common(belly).Volume
                contacts.append({'name': name, 'endpoint_mm': endpoint, 'belly_overlap_mm3': overlap})
                assert overlap > 0, (name, endpoint)
            for support in supports:
                overlap = shape.common(doc.getObject(support).Shape).Volume
                previous = baseline_loops[name].common(doc.getObject(support).Shape).Volume
                collisions.append({'objects': [name, support], 'overlap_mm3': overlap,
                                   'baseline_overlap_mm3': previous,
                                   'regressed': overlap > previous+1e-6})
                assert overlap <= previous+1e-6, (name, support, overlap, previous)
            # OCCT lofts store a closed U seam without the periodic flag.
            # Select the lateral surface and verify its seam at several V
            # stations before averaging the circular sections.
            face = max(shape.Faces, key=lambda f: f.Area)
            u0, u1, v0, v1 = face.ParameterRange
            assert all((face.valueAt(u0, float(v))-face.valueAt(u1, float(v))).Length < 1e-6
                       for v in np.linspace(v0, v1, 9)), name
            paths[name] = np.asarray([np.mean([list(face.valueAt(float(u),float(v)))
                          for u in np.linspace(u0,u1,16,endpoint=False)],axis=0)
                          for v in np.linspace(v0,v1,500)])
            vertices, faces = shape.tessellate(.12)
            item = next(o for o in mesh['objects'] if o['name'] == name)
            item.update(vertices=[list(v) for v in vertices], faces=faces)
        root = Path(__file__).resolve().parents[1]
        cameras = json.loads((root/'cad/drone-concept/comparison/v69-underbody-loop-radius2p2/video-comparison/cameras.json').read_text())
        observations = []
        for obs in ([] if fit.get('observation_kind') else fit['fitted']):
            name = 'UnderbodyLoop1' if obs['side'] == 1 else 'UnderbodyLoop0'
            px = project(paths[name], obs['source_frame'], cameras)
            distance, index = cKDTree(px).query(obs['reference_px'])
            observations.append({**obs, 'saved_nearest_px': px[index].tolist(),
                                 'saved_distance_px': distance.tolist(),
                                 'saved_rms_px': float(np.sqrt(np.mean(distance**2)))})
        report = {'status': 'saved path candidate; full-view image and export checks pending',
                  'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': digest(model),
                  'script_sha256': digest(Path(__file__)), 'fit_sha256': digest(args.fit),
                  'changed_objects': changed, 'preserved_objects': preserved,
                  'new_advanced_check_failures': [], 'contact_regressions': [],
                  'radius_mm': args.radius, 'centreline_paths_mm': fit['centreline_paths_mm'],
                  'construction': 'smooth loft through 40 circular normal sections; pipe-shell sweep rejected for advanced C0 errors',
                  'endpoint_belly_contacts': contacts, 'support_collisions': collisions,
                  'saved_centreline_observations': observations,
                  'saved_centreline_rms_px': float(np.sqrt(np.mean(np.concatenate([o['saved_distance_px'] for o in observations])**2))) if observations else None,
                  'limitations': ['manually inferred decorative cable shape; no electrical specification',
                                 'no fresh held-out fitting observations', 'no physical or manufacturing acceptance']}
        (args.output/'candidate-check.json').write_text(json.dumps(report,indent=2)+'\n')
        mesh['fcstd_sha256'] = digest(model)
        (args.output/'meshes.json').write_text(json.dumps(mesh,separators=(',',':')))
        print('saved path rms',report['saved_centreline_rms_px'])
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
