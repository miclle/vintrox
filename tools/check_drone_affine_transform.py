"""Measure FreeCAD's default and geometric affine transforms on known solids."""
import argparse
import json
from pathlib import Path

import FreeCAD as App
import Part

from drone_concept import nozzle_leaf_parts


def bounds(shape):
    box = shape.optimalBoundingBox(False, False)
    return [box.XMin, box.XMax, box.YMin, box.YMax, box.ZMin, box.ZMax]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    matrix = App.Matrix()
    matrix.A11 = matrix.A22 = .9
    matrix.A33 = 1
    records = []
    for name, original in [('box', Part.makeBox(10, 20, 30)),
                           ('petal', nozzle_leaf_parts(0)['NozzlePetal0'])]:
        for method in ['transformShape', 'transformGeometry']:
            result = getattr(original.copy(), method)(matrix)
            records.append({'name': name, 'method': method,
                            'before': bounds(original), 'after': bounds(result),
                            'volume_ratio': result.Volume/original.Volume})
    corrected_box = records[1]['after']
    assert all(abs(value-expected) < 1e-5 for value, expected in
               zip(corrected_box, [0, 9, 0, 18, 0, 30]))
    assert abs(records[0]['after'][-1]-30) > 1
    assert abs(records[3]['after'][-1]-records[3]['before'][-1]) < 1e-5
    args.output.write_text(json.dumps({'freecad_version': App.Version(),
                                     'records': records}, indent=2)+'\n')
    print('Affine transform discrepancy reproduced on box and real source leaf')


if __name__ == '__main__':
    main()
