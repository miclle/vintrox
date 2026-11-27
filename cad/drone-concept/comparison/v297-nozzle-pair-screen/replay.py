"""Rebuild the v297 mirrored nozzle-pair candidates from the v292 FCStd."""

import argparse
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

import FreeCAD as App

from experiment_drone_petal_axial import advanced_errors, digest, extend_tip


SETTINGS = {"outer": ((6, 10), -1.5), "inner": ((7, 9), -1.5), "inward": ((7, 9), -3.0)}
BASIS = "17f9f587f9148cb7e7b2abf2056c3522148db12937fab3eed2068b3372c52c58"
PETAL = re.compile(r"NozzlePetal(?:Inset|EdgeRail|EndHem|Ridge)?(\d+)(?:_\d+)?")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "mesh", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--variant", choices=SETTINGS, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output directory must be empty")
    if digest(args.base) != BASIS:
        raise ValueError("The input must be the saved v292 model")
    mesh = json.loads(args.mesh.read_text())
    if mesh["fcstd_sha256"] != BASIS:
        raise ValueError("The mesh must come from the saved v292 model")

    indices, radial_shift = SETTINGS[args.variant]
    axis = App.Vector(0, .574, -.819)
    axis.normalize()
    frame = App.Placement(App.Vector(0, 180, 173), App.Rotation(App.Vector(0, 0, 1), axis))
    replacements = {}
    base = App.openDocument(str(args.base.resolve()))
    saved = None
    try:
        for item in mesh["objects"]:
            name = item["name"]
            match = PETAL.fullmatch(name)
            if match and int(match[1]) in indices:
                shape, _ = extend_tip(base.getObject(name).Shape, frame, 1.5, 105,
                                      radial_shift, 0, int(match[1]))
                replacements[name + ".Shape.brp"] = shape.exportBrepToString()
        if len(replacements) != 12:
            raise ValueError("Expected twelve shapes for the mirrored pair")
        args.output.mkdir(parents=True, exist_ok=True)
        model = args.output / "candidate.FCStd"
        with ZipFile(args.base) as source, ZipFile(model, "w", ZIP_DEFLATED) as output:
            if not replacements.keys() <= set(source.namelist()):
                raise ValueError("Missing petal BRep in v292")
            for name in source.namelist():
                contents = replacements[name] if name in replacements else source.read(name)
                output.writestr(name, contents)
        saved = App.openDocument(str(model.resolve()))
        for item in mesh["objects"]:
            name = item["name"]
            if name + ".Shape.brp" in replacements:
                old = base.getObject(name).Shape
                shape = saved.getObject(name).Shape
                if (not shape.isValid() or not shape.isClosed()
                        or len(shape.Solids) != len(old.Solids)
                        or advanced_errors(shape) != advanced_errors(old)):
                    raise ValueError(f"Invalid saved shape: {name}")
                vertices, faces = shape.tessellate(.12)
                item.update(vertices=[list(vertex) for vertex in vertices], faces=faces)
    finally:
        if saved is not None:
            App.closeDocument(saved.Name)
        App.closeDocument(base.Name)
    mesh["fcstd_sha256"] = digest(model)
    (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))


if __name__ == "__main__":
    main()
