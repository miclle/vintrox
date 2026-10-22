"""Read saved appearance CAD and STEP independently; never save through headless.

Run with FreeCAD's bundled Python and library PYTHONPATH, as documented in
docs/drone-concept.md. This checks static deliverables, not manufacturing fit.
"""
from pathlib import Path
import hashlib
import json
import re
from xml.etree import ElementTree
from zipfile import ZipFile

import FreeCAD as App
import Part


def verify(root):
    """Validate saved solids, screen inputs, bass reservation, and STEP parity."""
    out = Path(root)/'cad/drone-concept'
    cad = out/'vintrox-drone-concept.FCStd'
    step = out/'vintrox-drone-concept.step'
    manifest = json.loads((out/'concept-manifest.json').read_text())
    errors = []
    digest = hashlib.sha256(cad.read_bytes()).hexdigest()
    if digest != manifest['fcstd_sha256']:
        errors.append('Saved FCStd hash differs from concept manifest')
    with ZipFile(cad) as archive:
        gui = ElementTree.fromstring(archive.read('GuiDocument.xml'))
        visible_names = {node.attrib['name'] for node in gui.findall('.//ViewProvider')
                         if node.find('./Properties/Property[@name="Visibility"]/Bool') is not None
                         and node.find('./Properties/Property[@name="Visibility"]/Bool').get('value') == 'true'}
    doc = App.openDocument(str(cad))
    try:
        objects = [doc.getObject(entry['name']) for entry in manifest['features']]
        invalid = [entry['name'] for entry, obj in zip(manifest['features'], objects)
                   if obj is None or not obj.Shape.isValid() or not obj.Shape.Solids]
        if invalid:
            raise RuntimeError('Invalid saved features: '+str(invalid))
        visible = [obj for obj in objects if obj.Name in visible_names]
        if len(visible) != manifest['visible_features']:
            errors.append('Saved GUI visibility count differs from manifest')
        groups = [o.Name for o in doc.Objects if o.TypeId == 'App::DocumentObjectGroup']
        non_chinese = [o.Name for o in doc.Objects if not re.search(r'[\u4e00-\u9fff]', o.Label)]
        if groups or non_chinese:
            errors.append('Expected a flat tree and Chinese labels for all objects')
        panel = doc.getObject('ScreenPanel210x160x2')
        screen_dims = [panel.Length.Value, panel.Height.Value, panel.Width.Value]
        if screen_dims != [210, 160, 2]:
            errors.append('Measured screen dimensions changed')
        active = doc.getObject('ActiveArea200x150')
        if [active.Length.Value, active.Height.Value] != [200, 150]:
            errors.append('Specified active area changed')
        reserve = doc.getObject('WooferEnvelope_D88_Depth40')
        if [reserve.AssumedDiameter.Value, reserve.AssumedDepth.Value] != [88, 40]:
            errors.append('Bass placeholder dimensions changed')
        reserve_shell_overlap = reserve.Shape.common(doc.getObject('BassNozzleShell').Shape).Volume
        if reserve_shell_overlap > .01:
            errors.append('Bass placeholder intersects nozzle shell')
        forbidden = [obj.Name for obj in objects if obj.Name.startswith(('FrontCheek', 'CheekDial', 'VentBacking', 'FaceFastener'))]
        if forbidden:
            errors.append('Unwanted screen-side details remain: '+str(forbidden))
        removed_pods = [o.Name for o in doc.Objects
                        if o.Name.startswith(('Utility', 'SideUtilityPod', 'SideCable'))]
        if removed_pods:
            errors.append('Removed external utility pods or their cables were regenerated')
        # Targeted regressions for the reported open side/back surfaces. These
        # samples do not claim airtightness, waterproofing, or a fitted assembly.
        closure_samples = []
        shell = doc.getObject('MainEnclosureShell')
        for side in (-1, 1):
            for y in (50, 100, 150):
                for z in (90, 160, 230):
                    point = App.Vector(side*118, y, z)
                    closure_samples.append(shell.Shape.isInside(point, .01, True))
        back = doc.getObject('RearServicePanel')
        for x in (-95, 95):
            for z in (75, 150, 220):
                closure_samples.append(back.Shape.isInside(App.Vector(x, 179, z), .01, True))
        if not all(closure_samples):
            errors.append('Missing side/back shell material at a closure probe')
        nozzle = doc.getObject('BassNozzleShell')
        curved_faces = sum(type(face.Surface).__name__ == 'BSplineSurface' for face in nozzle.Shape.Faces)
        if curved_faces == 0:
            errors.append('Nozzle lost its smooth lofted fairing')
        petals = [obj for obj in objects if obj.Name.startswith('NozzlePetal') and not obj.Name.startswith('NozzlePetalRidge')]
        if len(petals) != 24:
            errors.append('Expected 24 separately modelled curved nozzle petals')
        shape = Part.read(str(step))
        step_names = re.findall(r"PRODUCT\(\s*'([^']*)'", step.read_text())
        chinese_step_names = [name for name in step_names if re.search(r'[\u4e00-\u9fff]', name)]
        if len(chinese_step_names) != len(visible):
            errors.append('STEP does not preserve every visible Chinese part label')
        compound = Part.makeCompound([obj.Shape for obj in visible])
        solid_count = sum(len(obj.Shape.Solids) for obj in visible)
        if len(shape.Solids) != solid_count or not shape.isValid():
            errors.append('STEP solid count or validity differs')
        relative_volume_error = abs(shape.Volume-compound.Volume)/max(compound.Volume, 1)
        if relative_volume_error > 1e-6:
            errors.append('STEP volume differs from saved visible CAD')
        bbox = compound.BoundBox
        step_bbox = shape.BoundBox
        bbox_delta = max(abs(getattr(bbox, k)-getattr(step_bbox, k)) for k in
                         ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax'))
        if bbox_delta > .01:
            errors.append('STEP bounds differ from saved visible CAD')
        report = {'passed': not errors, 'scope': 'saved static appearance study only',
                  'physical_validation': False, 'errors': errors,
                  'visible_features': len(visible), 'step_solids': len(shape.Solids),
                  'group_count': len(groups), 'non_chinese_labels': non_chinese,
                  'chinese_named_objects': len(doc.Objects)-len(non_chinese),
                  'chinese_step_part_names': len(chinese_step_names),
                  'screen_panel_mm': screen_dims, 'active_area_mm': [200, 150],
                  'woofer_reservation_mm': [88, 40],
                  'woofer_shell_overlap_mm3': reserve_shell_overlap,
                  'screen_side_unwanted_features': forbidden,
                  'removed_external_pod_parts_present': removed_pods,
                  'closure_probes_passed': sum(closure_samples), 'closure_probe_count': len(closure_samples),
                  'nozzle_loft_surface_count': curved_faces, 'curved_nozzle_petals': len(petals),
                  'step_relative_volume_error': relative_volume_error,
                  'step_bbox_max_delta_mm': bbox_delta,
                  'bbox_mm': [bbox.XLength, bbox.YLength, bbox.ZLength],
                  'fcstd_sha256': digest, 'step_sha256': hashlib.sha256(step.read_bytes()).hexdigest()}
        (out/'readback-verification.json').write_text(json.dumps(report, indent=2)+'\n')
        if not errors:
            manifest['bbox_mm'] = report['bbox_mm']
            manifest['bbox_min_mm'] = [bbox.XMin, bbox.YMin, bbox.ZMin]
            manifest['bbox_max_mm'] = [bbox.XMax, bbox.YMax, bbox.ZMax]
            manifest['bounds_basis'] = 'saved FCStd independent readback'
            (out/'concept-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
        print(json.dumps(report, indent=2))
        if errors:
            raise RuntimeError('Appearance package verification failed')
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[1])
