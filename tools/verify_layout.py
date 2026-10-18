"""Read saved CAD without writing it; reports require an explicit output path."""
from pathlib import Path
import argparse
import hashlib
import json
import FreeCAD as App
import Part

import layout_checks as layout

ROOT = Path(__file__).resolve().parents[1]


LENGTH_TOLERANCE_MM = 1e-6
VOLUME_TOLERANCE_MM3 = 1e-6


def compare_step_geometry(objects: list, step: Part.Shape) -> dict:
    """Match each saved solid in place, independently of STEP entity order."""
    if not step.isValid():
        raise ValueError('STEP contains invalid geometry')
    references = [(obj.Name, solid) for obj in objects for solid in obj.Shape.Solids]
    candidates = list(step.Solids)
    if len(candidates) != len(references):
        raise ValueError('STEP solid count differs from FCStd')
    max_difference = 0.0
    for name, solid in references:
        for index, other in enumerate(candidates):
            if abs(solid.Volume - other.Volume) > VOLUME_TOLERANCE_MM3:
                continue
            if any(
                abs(getattr(solid.BoundBox, key) - getattr(other.BoundBox, key))
                > LENGTH_TOLERANCE_MM
                for key in ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax')
            ):
                continue
            difference = max(solid.cut(other).Volume, other.cut(solid).Volume)
            if difference <= VOLUME_TOLERANCE_MM3:
                max_difference = max(max_difference, difference)
                candidates.pop(index)
                break
        else:
            raise ValueError(f'STEP geometry mismatch: no matching solid for {name}')
    return {
        'matched_solids': len(references),
        'length_tolerance_mm': LENGTH_TOLERANCE_MM,
        'volume_tolerance_mm3': VOLUME_TOLERANCE_MM3,
        'max_bidirectional_difference_mm3': round(max_difference, 12),
    }


def verify(root: Path = ROOT, exercise: bool = False) -> dict:
    """Return fresh evidence and always close the readback document, without saving."""
    doc = App.openDocument(str(root/'cad/vintrox-layout.FCStd'))
    try:
        return _verify_document(doc, root, exercise)
    finally:
        App.closeDocument(doc.Name)


def _verify_document(doc, root, exercise):
    doc.recompute()
    report = layout.validate(doc)
    assert not report['errors'], report
    checks = []
    depth_probes = []
    if exercise:
        # Native expressions must survive save/reopen without a custom Python proxy.
        p = doc.Parameters
        cells = {alias: p.getCellFromAlias(alias) for alias in
                 ('ScreenW', 'ScreenH', 'Depth', 'BatteryH', 'SpeakerT')}
        for alias, delta in [('ScreenW',20),('ScreenH',10),('Depth',15),('BatteryH',10),('SpeakerT',5)]:
            cell = cells[alias]
            old = float(getattr(p,alias))
            before = doc.ScreenPanel.Shape.BoundBox.XLength if alias=='ScreenW' else None
            p.set(cell,str(old+delta))
            doc.recompute()
            changed = layout.validate(doc)
            assert not changed['errors'], (alias,changed)
            if alias=='ScreenW':
                assert abs(float(p.Width)-(report['body_mm']['width']+delta)) < 1e-6
                assert abs(doc.ScreenPanel.Shape.BoundBox.XLength-before-delta) < 1e-6
            if alias=='ScreenH':
                assert abs(float(p.Height)-(report['body_mm']['height']+delta)) < 1e-6
            if alias=='Depth':
                assert abs(doc.Rear.Shape.BoundBox.YMax-(report['body_mm']['depth']+delta)) < 1e-6
            if alias=='BatteryH':
                assert abs(doc.Battery.Shape.BoundBox.ZLength-old-delta) < 1e-6
            if alias=='SpeakerT':
                assert abs(doc.SpeakerRight.Shape.BoundBox.XLength-old-delta) < 1e-6
            checks.append(alias+' + '+str(delta)+' mm: PASS')
            p.set(cell,str(old))
            doc.recompute()
        original_depth = float(p.Depth)
        for candidate in (150,155,160,165):
            p.set(cells['Depth'], str(candidate))
            doc.recompute()
            probe = layout.validate(doc)
            depth_probes.append({'depth_mm':candidate, 'accepted':not probe['errors'], 'errors':probe['errors']})
        p.set(cells['Depth'], str(original_depth))
        doc.recompute()
        assert [q['accepted'] for q in depth_probes] == [False,False,True,True], depth_probes
        checks.append('Depth 150/155 rejected; 160/165 accepted for this fixed layout')
        speaker_before = float(p.SpeakerT)
        p.set(cells['SpeakerT'],'100')
        doc.recompute()
        assert layout.validate(doc)['errors'], 'Deliberate collision was not detected'
        checks.append('SpeakerT=100 mm: intentional collision detected')
        p.set(cells['SpeakerT'], str(speaker_before))
        doc.recompute()
        assert not layout.validate(doc)['errors']
    step = Part.Shape()
    step.read(str(root/'cad/vintrox-layout.step'))
    geometry = compare_step_geometry(layout.physical(doc), step)
    fc_volume = sum(o.Shape.Volume for o in layout.physical(doc))
    assert abs(step.Volume-fc_volume) < 0.01
    report['saved_readback'] = {'freecad_version':'.'.join(App.Version()[:3]),'step_solids':len(step.Solids),'step_valid':step.isValid(),'step_vs_fcstd_volume_difference_mm3':round(step.Volume-fc_volume,8),'step_geometry_comparison':geometry,'parametric_exercise_executed':exercise,'parametric_checks':checks, 'fixed_layout_depth_probes':depth_probes}
    unchanged = {'ScreenPanel':[225,8,170],'ScreenDriver':[80,6,45],'OpticalDrive':[128,13,128],'OpticalBridge':[35,14,18],'SpeakerLeft':[55,105,115],'SpeakerRight':[55,105,115],'Battery':[120,75,32],'RaspberryPi':[85,65,25],'Disk':[100,20,125],'Hub':[50,70,22],'Amplifier':[50,25,20],'DAC':[60,25,16],'PowerManagement':[70,24,28]}
    if exercise:
        for name, original_dimensions in unchanged.items():
            assert sorted(report['hardware_envelopes'][name]['xyz_mm']) == sorted(original_dimensions), name
        report['revision_comparison'] = {'previous_body_mm':[249,222,210], 'depth_reduction_mm':50, 'depth_reduction_percent':round(50/210*100,2), 'hardware_envelope_dimensions_preserved':len(unchanged), 'note':'对照初版13个假设包络，边长不缩小；Pi/Hub仅旋转。未证明真实器件/连接器能装入。'}
    report['sha256'] = {name:hashlib.sha256((root/'cad'/name).read_bytes()).hexdigest() for name in ('vintrox-layout.FCStd','vintrox-layout.step')}
    return report


def main(argv: list[str] | None = None) -> None:
    """Print this run's evidence; only write a report when explicitly requested."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise', action='store_true', help='运行默认布局参数探针')
    parser.add_argument('--output', type=Path, help='验证成功后写入指定 JSON 路径')
    args = parser.parse_args(argv)
    if (args.output is not None
            and args.output.resolve() == (ROOT/'cad/layout-validation.json').resolve()
            and not args.exercise):
        parser.error('更新 cad/layout-validation.json 必须同时指定 --exercise')
    report = verify(exercise=args.exercise)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)+'\n'
    if args.output is not None:
        args.output.write_text(serialized)
    print(serialized, end='')

if __name__=='__main__':
    main()
