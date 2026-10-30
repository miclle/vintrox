"""Check the source-leaf assembly chain and independent STEP readback."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part

from experiment_drone_petal_axial import advanced_errors


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate-dir', type=Path, required=True)
    args = parser.parse_args()
    folder = args.candidate_dir
    model = folder/'candidate.FCStd'
    check = json.loads((folder/'candidate-check.json').read_text())
    mesh = json.loads((folder/'meshes.json').read_text())
    assert digest(model) == check['fcstd_sha256'] == mesh['fcstd_sha256']
    doc = App.openDocument(str(model))
    contacts = []
    try:
        def contact(first, second):
            left, right = doc.getObject(first).Shape, doc.getObject(second).Shape
            gap = left.distToShape(right)[0]
            assert gap < .01, (first, second, gap)
            contacts.append({'objects': [first, second], 'gap_mm': gap,
                             'overlap_mm3': left.common(right).Volume})
        for index in range(12):
            for name in [f'NozzlePetalInset{index}', f'NozzlePetalRidge{index}',
                         f'NozzlePetalEndHem{index}', f'NozzlePetalHinge{index}',
                         'BassNozzleMouthRing']:
                contact(f'NozzlePetal{index}', name)
            for rail in [0, 1]:
                contact(f'NozzlePetalGuide{index}_{rail}', f'NozzlePetalRidge{index}')
        contact('BassNozzleMouthRing', 'BassNozzleRolledLip')
        contact('BassNozzleRolledLip', 'BassNozzleShell')
        contact('BassNozzleRearCollar', 'BassNozzleShell')
        features = [doc.getObject(item['name']) for item in mesh['objects']]
        assert len(features) == 696
        assert all(obj.Shape.isValid() and obj.Shape.isClosed() for obj in features)
        for name in check['changed_objects']:
            assert not advanced_errors(doc.getObject(name).Shape), name
        step_path = folder/'candidate.step'
        Part.export(features, str(step_path))
        step = Part.read(str(step_path))
        assert step.isValid() and all(solid.isClosed() for solid in step.Solids)
        compound = Part.makeCompound([obj.Shape for obj in features])
        assert len(step.Solids) == len(compound.Solids)
        relative_error = abs(compound.Volume-step.Volume)/compound.Volume
        assert relative_error < 1e-6, relative_error
        expected_box = compound.optimalBoundingBox(False, False)
        actual_box = step.optimalBoundingBox(False, False)
        bbox_delta = max(abs(getattr(expected_box, key)-getattr(actual_box, key))
                         for key in ['XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax'])
        assert bbox_delta < .01, bbox_delta
        report = {'status': 'appearance only; topology and STEP checked; visual adoption pending',
                  'fcstd_sha256': digest(model), 'step_sha256': digest(step_path),
                  'script_sha256': digest(Path(__file__)), 'visible_objects': len(features),
                  'step_solids': len(step.Solids), 'step_valid': True,
                  'cad_volume_mm3': compound.Volume, 'step_volume_mm3': step.Volume,
                  'relative_volume_error': relative_error, 'bbox_max_delta_mm': bbox_delta,
                  'changed_parts_advanced_check_passed': True, 'assembly_contacts': contacts,
                  'contact_interpretation': 'guides to raised ridges; leaves to mouth ring and hinges; mouth ring to rolled lip to shell',
                  'limitations': ['static CAD only', 'no manufacturing or physical acceptance']}
        (folder/'assembly-step-check.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'step_solids': len(step.Solids), 'relative_volume_error': relative_error,
                          'bbox_max_delta_mm': bbox_delta}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
