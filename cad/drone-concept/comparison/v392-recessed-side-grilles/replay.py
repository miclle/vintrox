"""Build ten round-ended grille slots in each side panel of the saved v388."""
import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part


def slotted_strip(index):
    # Build in assembly coordinates on the right, then mirror to the left.
    face_x = 115.4
    length = 42.2
    pitch = 4.256
    radius = 1.24
    middle_y = 10.12
    middle_z = 118.76 + (index - 4.5) * pitch
    ymin = middle_y - length / 2 + radius
    ymax = middle_y + length / 2 - radius
    x = face_x - .55
    z = middle_z
    def vertex(y, h):
        return App.Vector(x - .5, y, h)
    corners = [vertex(ymin,z-radius),vertex(ymax,z-radius),vertex(ymax,z+radius),vertex(ymin,z+radius)]
    wire = Part.Wire([Part.makeLine(corners[0],corners[1]),
                      Part.Arc(corners[1],vertex(ymax+radius,z),corners[2]).toShape(),
                      Part.makeLine(corners[2],corners[3]),
                      Part.Arc(corners[3],vertex(ymin-radius,z),corners[0]).toShape()])
    cutter = Part.Face(wire).extrude(App.Vector(2,0,0))
    panel = Part.makeBox(.55,length+2,pitch,App.Vector(x,middle_y-length/2-1,z-pitch/2))
    return panel.cut(cutter).removeSplitter()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.model.read_bytes()).hexdigest() != '72b9c0673e8d980ff7c779c4cb084fc5f8872c46ec546a81ee3f99d372413e88':
        raise ValueError('Expected v388')
    doc = App.openDocument(str(args.model.resolve()))
    changed = []
    for side in ['Right','Left']:
        back = Part.makeBox(1.35,44.2,42.56,App.Vector(113.5,-11.98,97.48))
        members = {'VentBacking'+side:back}
        for i in range(10):
            members['CheekVentRib'+side+str(i)] = slotted_strip(i)
        for name,shape in members.items():
            if side == 'Left':
                shape = shape.mirror(App.Vector(0,0,0),App.Vector(1,0,0))
            shape.check(True)
            if not shape.isValid() or not shape.isClosed() or len(shape.Solids)!=1:
                raise ValueError(name)
            doc.getObject(name).Shape = shape
            changed.append(name)
    doc.recompute()
    args.output.mkdir(parents=True,exist_ok=True)
    doc.saveAs(str((args.output/'geometry.FCStd').resolve()))
    App.closeDocument(doc.Name)
    doc = App.openDocument(str((args.output/'geometry.FCStd').resolve()))
    for name in changed:
        doc.getObject(name).Shape.check(True)
    measurements = []
    for side in ['Right','Left']:
        backing = doc.getObject('VentBacking'+side).Shape
        cheek = doc.getObject('FrontCheek'+side).Shape
        measurements.append({'side':side,'backing_to_cheek_mm':backing.distToShape(cheek)[0],
                             'rib_backing_gaps_mm':[doc.getObject('CheekVentRib'+side+str(i)).Shape.distToShape(backing)[0] for i in range(10)]})
    App.closeDocument(doc.Name)
    (args.output/'joints.json').write_text(json.dumps(measurements,indent=2)+'\n')

if __name__=='__main__':
    main()
