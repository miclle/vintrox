"""Screen a small rearward Y-length change to ClosedBellyPan."""
import argparse
import hashlib
import json
from pathlib import Path
import FreeCAD as App
import Import


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--scale', type=float, required=True)
    a = p.parse_args()
    if not .97 <= a.scale <= 1.03:
        raise ValueError('Use a small ClosedBellyPan Y scale')
    a.base = a.base.resolve(); a.output = a.output.resolve(); a.output.mkdir(parents=True, exist_ok=True)
    base_hash = hashlib.sha256(a.base.read_bytes()).hexdigest()
    d = App.openDocument(str(a.base)); source = d.getObject('ClosedBellyPan').Shape
    b = source.BoundBox; m = App.Matrix(); m.A22 = a.scale; m.A24 = b.YMin * (1-a.scale)
    shape = source.transformGeometry(m); shape.check(True)
    if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1:
        raise ValueError('Invalid ClosedBellyPan candidate')
    d.getObject('ClosedBellyPan').Shape = shape; d.recompute(); model = a.output/'candidate.FCStd'; d.saveAs(str(model)); App.closeDocument(d.Name)
    d = App.openDocument(str(model))
    try:
        with __import__('zipfile').ZipFile(a.base) as z:
            from xml.etree import ElementTree
            gui = ElementTree.fromstring(z.read('GuiDocument.xml'))
            names = [n.attrib['name'] for n in gui.findall('.//ViewProvider') if n.find('./Properties/Property[@name="Visibility"]/Bool[@value="true"]') is not None]
        visible = [d.getObject(n) for n in names]
        step = a.output/'candidate.step'; Import.export(visible, str(step))
        report = {'revision': a.output.name, 'baseline_fcstd_sha256': base_hash, 'fcstd_sha256': hashlib.sha256(model.read_bytes()).hexdigest(), 'step_sha256': hashlib.sha256(step.read_bytes()).hexdigest(), 'changed_objects':['ClosedBellyPan'], 'y_scale':a.scale, 'fixed_y_min_mm':b.YMin, 'visible_features':len(visible), 'status':'saved candidate; fixed-camera screening pending'}
        (a.output/'candidate-check.json').write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report))
    finally: App.closeDocument(d.Name)


if __name__ == '__main__': main()
