"""Read saved channel cavities and protected geometry, without render masks."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
from experiment_drone_petal_detail import petal_detail_parts
from experiment_drone_petal_roll import petal_roll_parts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def difference(first, second):
    return first.cut(second).Volume + second.cut(first).Volume


def main():
    parser = argparse.ArgumentParser()
    for name in ['model', 'baseline', 'candidate-check', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    check = json.loads(args.candidate_check.read_text())
    assert digest(args.model) == check['fcstd_sha256']
    assert digest(args.baseline) == check['baseline_fcstd_sha256']
    generator='experiment_drone_petal_roll.py' if 'root_radius_mm' in check else 'experiment_drone_petal_detail.py'
    assert check['script_sha256'] == digest(Path(__file__).with_name(generator))
    if 'detail_source_sha256' in check:
        assert check['detail_source_sha256']==digest(Path(__file__).with_name('experiment_drone_petal_detail.py'))
    current = App.openDocument(str(args.model))
    baseline = App.openDocument(str(args.baseline))
    axis = App.Vector(0,.574,-.819)
    axis.normalize()
    placement = App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
    parts, probes = [], []
    try:
        for index in range(12):
            source=(petal_roll_parts(index,check['strap_corner_radius_mm'],check['root_radius_mm']) if 'root_radius_mm' in check else petal_detail_parts(index,check['strap_corner_radius_mm']))
            for name, shape in source.items():
                shape.Placement = placement.multiply(shape.Placement)
                saved = current.getObject(name).Shape
                saved.check(True)
                delta = difference(shape, saved)
                assert saved.isValid() and saved.isClosed() and len(saved.Solids)==1 and delta<1e-6
                parts.append({'name':name,'advanced_check_passed':True,'solids':1,
                              'closed':True,'source_symmetric_difference_mm3':delta})
            ridge = current.getObject(f'NozzlePetalRidge{index}').Shape
            assembly = [current.getObject(name).Shape for name in
                        [f'NozzlePetal{index}',f'NozzlePetalInset{index}',*source]]
            theta = math.radians(index*30+30)
            stations = [(111.4,48.44,1.295,-1.925),(120,46,2.8,-3),(123.5,45,3.41,-3.5)]
            for z in [116,118,121]:
                lo,hi = next((lo,hi) for lo,hi in zip(stations,stations[1:]) if lo[0]<=z<=hi[0])
                fraction = (z-lo[0])/(hi[0]-lo[0])
                radius,dy,tilt = [lo[j]+fraction*(hi[j]-lo[j]) for j in [1,2,3]]
                def point(offset):
                    r=radius+offset
                    return placement.multVec(App.Vector(r*math.cos(theta),
                        dy+r*math.sin(theta)*math.cos(math.radians(tilt)),
                        z+r*math.sin(theta)*math.sin(math.radians(tilt))))
                void = not any(shape.isInside(point(-.3),1e-5,False) for shape in assembly)
                floor = ridge.isInside(point(-.95),1e-5,False)
                probes.append({'petal_index':index,'station_mm':z,
                               'channel_centre_is_empty':void,'ridge_backing_is_solid':floor})
                assert void and floor, (index,z,void,floor)
        protected = [o.Name for o in baseline.Objects if o.Name.startswith('SupportShaft')]
        assert len(protected)==4
        protected += [f'NozzlePetal{i}' for i in range(12)]
        preserved = [{'name':name,'symmetric_difference_mm3':difference(
            baseline.getObject(name).Shape,current.getObject(name).Shape)} for name in protected]
        assert all(row['symmetric_difference_mm3']<1e-6 for row in preserved)
        assert all(row['gap_mm']<.01 for row in check['contacts']), 'Disconnected detail part'
        report = {'fcstd_sha256':digest(args.model),'baseline_fcstd_sha256':digest(args.baseline),
                  'measurement_script_sha256':digest(Path(__file__)),
                  'generator_sha256':check['script_sha256'],'parts':parts,'contacts':check['contacts'],'channel_probes':probes,
                  'protected_geometry':preserved,'passed':True,
                  'limitations':['Sparse interior probes verify a backed recess, not its entire thickness field.',
                                 'Guide dimensions are appearance assumptions, not source measurements.']}
        args.output.write_text(json.dumps(report,indent=2)+'\n')
        print(f'{len(parts)} saved/source parts, 36 backed-channel probes, 12 leaves and four shafts passed')
    finally:
        App.closeDocument(current.Name)
        App.closeDocument(baseline.Name)


if __name__=='__main__':
    main()
