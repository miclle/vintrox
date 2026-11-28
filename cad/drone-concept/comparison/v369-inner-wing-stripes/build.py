"""Reconstruct the two inward-facing red-wing markings from frame 150."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import FreeCAD as App
import Part


def camera_band(pose, resolution, left, right, slope):
    """Make a 3D clipping prism between the two back-projected stripe edges."""
    eye = App.Vector(*pose["eye_mm"])
    forward = (App.Vector(*pose["target_mm"]) - eye).normalize()
    horizontal = forward.cross(App.Vector(0, 0, 1)).normalize()
    vertical = horizontal.cross(forward)
    width, height = resolution
    focal = width * pose["lens_mm"] / pose["sensor_width_mm"]
    sections = []
    for depth in (600, 1700):
        corners = []
        for offset, y in ((left, 40), (right, 40), (right, 400), (left, 400)):
            x = offset + slope * y
            ray = forward + horizontal * ((x - width/2) / focal) - vertical * ((y - height/2) / focal)
            corners.append(eye + ray * depth)
        sections.append(Part.makePolygon(corners + corners[:1]))
    return Part.makeLoft(sections, True, True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cameras = json.loads((Path(__file__).resolve().parents[1] / "cameras.json").read_text())
    pose = next(p for p in cameras["views"] if p["source_frame"] == 150)
    doc = App.openDocument(str(args.base.resolve()))
    headless = args.output.with_suffix(".headless.FCStd")
    try:
        carrier = doc.getObject("WingInnerPaintLeft").Shape
        spine = doc.getObject("WingSpineLeft").Shape
        def face_normal(face):
            return face.normalAt(*face.Surface.parameter(face.CenterOfMass))

        face = max((f for f in carrier.Faces if face_normal(f).x > .9), key=lambda f: f.Area)
        surfaces = [face.extrude(App.Vector(.18, 0, 0))]
        # Continue the marking across the raised ridge and both sloped flanks.
        for face in spine.Faces:
            normal = face_normal(face)
            if normal.x > -.9:
                surfaces.append(face.extrude(normal * .18))
        for index, offsets in enumerate(((670, 705), (640, 658))):
            clip = camera_band(pose, cameras["resolution"], *offsets, .4)
            obj = doc.getObject(f"WingStripeLeft{index}")
            coating = [part for surface in surfaces for part in surface.common(clip).Solids if part.Volume > 1e-6]
            if not coating or not all(s.isValid() and s.isClosed() and s.Volume > 0 for s in coating):
                raise ValueError(f"Invalid inner stripe {index}")
            obj.Shape = Part.makeCompound([obj.Shape.copy(), *coating])
            print(obj.Name, len(coating), sum(s.Volume for s in coating))
        doc.recompute()
        doc.saveAs(str(headless.resolve()))
    finally:
        App.closeDocument(doc.Name)
    gui = ("GuiDocument.xml", "ShapeAppearance", "LineColorArray", "PointColorArray")
    with ZipFile(headless) as geometry, ZipFile(args.base) as colors, ZipFile(args.output, "x") as out:
        for archive, use_gui in ((geometry, False), (colors, True)):
            for info in archive.infolist():
                if info.filename.startswith(gui) == use_gui:
                    out.writestr(info, archive.read(info))
    headless.unlink()
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
