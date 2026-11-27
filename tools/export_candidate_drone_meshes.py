"""Export render triangles from an arbitrary saved Drone FCStd candidate.

The candidate's saved GUI document supplies visibility and colors. The source
FCStd is read only and is never rewritten by this exporter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree
from zipfile import ZipFile

import FreeCAD as App


def saved_colors(archive: ZipFile) -> dict[str, list[float]]:
    gui = ElementTree.fromstring(archive.read("GuiDocument.xml"))
    colors: dict[str, list[float]] = {}
    for node in gui.findall(".//ViewProvider"):
        props = node.find("Properties")
        if props is None:
            continue
        visible = props.find('./Property[@name="Visibility"]/Bool[@value="true"]')
        if visible is None:
            continue
        name = node.attrib["name"]
        materials = props.find('./Property[@name="ShapeAppearance"]/MaterialList')
        if materials is None:
            legacy = props.find('./Property[@name="ShapeColor"]/PropertyColor')
            if legacy is None:
                raise ValueError(f"Missing saved display color for {name}")
            rgba = int(legacy.attrib["value"])
        else:
            payload = archive.read(materials.attrib["file"])
            if (materials.get("version") != "3" or len(payload) != 40
                    or struct.unpack_from("<I", payload)[0] != 1):
                raise ValueError(f"Expected one FreeCAD v3 display material for {name}")
            rgba = struct.unpack_from("<I", payload, 8)[0]
        colors[name] = [((rgba >> shift) & 255) / 255 for shift in (24, 16, 8)]
    return colors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--color-source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = args.model.resolve()
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    color_source = (args.color_source or model).resolve()
    with ZipFile(color_source) as archive:
        colors = saved_colors(archive)
    doc = App.openDocument(str(model))
    try:
        objects = []
        for name, color in colors.items():
            obj = doc.getObject(name)
            if obj is None or obj.Shape.isNull():
                continue
            vertices, faces = obj.Shape.tessellate(.12)
            objects.append({
                "name": name,
                "vertices": [[vertex.x, vertex.y, vertex.z] for vertex in vertices],
                "faces": faces,
                "color": color,
                "material": getattr(obj, "RenderMaterial", "paint"),
            })
        if len(objects) != len(colors):
            raise ValueError("Saved visible geometry differs from the GUI display state")
        data = {"fcstd_sha256": digest, "objects": objects}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent,
                                delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, separators=(",", ":"))
        temporary.replace(args.output)
        print(json.dumps({"output": str(args.output), "fcstd_sha256": digest,
                          "visible_features": len(objects)}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
