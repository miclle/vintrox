"""Export render triangles from the current saved Drone FCStd without saving it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree
from zipfile import ZipFile

import FreeCAD as App


def saved_colors(archive: ZipFile) -> dict[str, list[float]]:
    gui = ElementTree.fromstring(archive.read("GuiDocument.xml"))
    colors = {}
    for node in gui.findall(".//ViewProvider"):
        props = node.find("Properties")
        if props is None or props.find('./Property[@name="Visibility"]/Bool[@value="true"]') is None:
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
            # FreeCAD MaterialList v3 stores a count and 36-byte records.
            # The diffuse (ShapeColor) RGBA follows the ambient RGBA.
            if (materials.get("version") != "3" or len(payload) != 40
                    or struct.unpack_from("<I", payload)[0] != 1):
                raise ValueError(f"Expected one FreeCAD v3 display material for {name}")
            rgba = struct.unpack_from("<I", payload, 8)[0]
        colors[name] = [((rgba >> shift) & 255) / 255 for shift in (24, 16, 8)]
    return colors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/vintrox-drone-render-meshes.json"))
    parser.add_argument("--model", type=Path,
                        help="Saved FCStd to export. Defaults to the formal Drone model.")
    parser.add_argument("--manifest", type=Path,
                        help="Feature manifest matching --model. Defaults beside the formal model.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cad = (args.model or root / "cad/drone-concept/vintrox-drone-concept.FCStd").resolve()
    manifest_path = (args.manifest or cad.parent / "concept-manifest.json").resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(cad.read_bytes()).hexdigest()
    if digest != manifest["fcstd_sha256"]:
        raise RuntimeError("concept manifest does not bind the saved FCStd")
    doc = App.openDocument(str(cad))
    try:
        with ZipFile(cad) as archive:
            colors = saved_colors(archive)
        objects = []
        for entry in manifest["features"]:
            obj = doc.getObject(entry["name"])
            if obj is None or obj.Name not in colors or obj.Shape.isNull():
                continue
            vertices, faces = obj.Shape.tessellate(.12)
            objects.append({
                "name": obj.Name,
                "vertices": [[v.x, v.y, v.z] for v in vertices],
                "faces": faces,
                "color": colors[obj.Name],
                "material": getattr(obj, "RenderMaterial", "paint"),
            })
        if {obj["name"] for obj in objects} != colors.keys() or len(objects) != manifest["visible_features"]:
            raise ValueError("Visible geometry differs from the saved display state or concept manifest")
        output = args.output
        data = {"fcstd_sha256": digest, "objects": objects}
        for key in ("bass_axis", "bass_origin_mm", "bass_warning_label_local_mm",
                    "bass_alert_local_mm", "bass_warning_text_size_mm",
                    "bass_alert_text_size_mm"):
            if key in manifest:
                data[key] = manifest[key]
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(json.dumps(data, separators=(",", ":")))
                stream.close()
                temporary.replace(output)
            finally:
                temporary.unlink(missing_ok=True)
        print(json.dumps({"output": str(output), "fcstd_sha256": digest,
                          "visible_features": len(objects)}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
