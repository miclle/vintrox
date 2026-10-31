"""Export render triangles from the current saved Drone FCStd without saving it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import FreeCAD as App


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cad = root / "cad/drone-concept/vintrox-drone-concept.FCStd"
    manifest = json.loads((cad.parent / "concept-manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(cad.read_bytes()).hexdigest()
    if digest != manifest["fcstd_sha256"]:
        raise RuntimeError("concept manifest does not bind the saved FCStd")
    doc = App.openDocument(str(cad))
    try:
        with ZipFile(cad) as archive:
            gui = ElementTree.fromstring(archive.read("GuiDocument.xml"))
            visible_names = {
                node.attrib["name"] for node in gui.findall(".//ViewProvider")
                if (node.find('./Properties/Property[@name="Visibility"]/Bool') is not None
                    and node.find('./Properties/Property[@name="Visibility"]/Bool').get("value") == "true")
            }
        objects = []
        for entry in manifest["features"]:
            obj = doc.getObject(entry["name"])
            if obj is None or obj.Name not in visible_names or obj.Shape.isNull():
                continue
            vertices, faces = obj.Shape.tessellate(.12)
            view = getattr(obj, "ViewObject", None)
            objects.append({
                "name": obj.Name,
                "vertices": [[v.x, v.y, v.z] for v in vertices],
                "faces": faces,
                "color": list(view.ShapeColor[:3]) if view else [.6, .5, .25],
                "material": getattr(obj, "RenderMaterial", "paint"),
            })
        output = Path("/tmp/vintrox-drone-render-meshes.json")
        data = {"fcstd_sha256": digest, "objects": objects}
        for key in ("bass_axis", "bass_origin_mm", "bass_warning_label_local_mm",
                    "bass_alert_local_mm", "bass_warning_text_size_mm",
                    "bass_alert_text_size_mm"):
            if key in manifest:
                data[key] = manifest[key]
        output.write_text(json.dumps(data), encoding="utf-8")
        print(json.dumps({"output": str(output), "fcstd_sha256": digest,
                          "visible_features": len(objects)}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
