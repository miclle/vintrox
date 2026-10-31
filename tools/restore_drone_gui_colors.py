#!/usr/bin/env python3
"""Restore the saved FreeCAD appearance palette by stable object name.

The formal Drone geometry is taken from the current FCStd.  Only the GUI
appearance payloads are copied from the last known colourful archive, so this
repair does not rebuild, transform, or omit any solid.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET


DEFAULT_SOURCE_COMMIT = "7550c1f2"
MODEL_RELATIVE = "cad/drone-concept/vintrox-drone-concept.FCStd"
APPEARANCE_PROPERTIES = {
    "LineColor",
    "LineColorArray",
    "LineMaterial",
    "PointColor",
    "PointColorArray",
    "PointMaterial",
    "ShapeAppearance",
}
EXTERNAL_PREFIXES = ("ShapeAppearance", "LineColorArray", "PointColorArray")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_bytes(repo: Path, commit: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{MODEL_RELATIVE}"], cwd=repo
    )


def viewproviders(xml_bytes: bytes) -> dict[str, ET.Element]:
    root = ET.fromstring(xml_bytes)
    return {vp.attrib["name"]: vp for vp in root.findall(".//ViewProvider")}


def property_map(vp: ET.Element) -> dict[str, ET.Element]:
    return {p.attrib["name"]: p for p in vp.findall("./Properties/Property")}


def copy_property_children(current: ET.Element, source: ET.Element) -> None:
    for child in list(current):
        current.remove(child)
    for child in list(source):
        current.append(deepcopy(child))


def repair(repo: Path, model: Path, source_commit: str, report_path: Path) -> dict:
    before = model.read_bytes()
    source = source_bytes(repo, source_commit)
    with zipfile.ZipFile(io.BytesIO(before)) as current_zip, zipfile.ZipFile(
        io.BytesIO(source)
    ) as source_zip:
        current_gui = current_zip.read("GuiDocument.xml")
        source_gui = source_zip.read("GuiDocument.xml")
        current_vps = viewproviders(current_gui)
        source_vps = viewproviders(source_gui)
        if set(current_vps) != set(source_vps):
            raise RuntimeError("Current and source ViewProvider names differ")

        root = ET.fromstring(current_gui)
        root_vps = {vp.attrib["name"]: vp for vp in root.findall(".//ViewProvider")}
        external_replacements: dict[str, bytes] = {}
        repaired_objects = []
        for name, current_vp in root_vps.items():
            source_vp = source_vps[name]
            current_props = property_map(current_vp)
            source_props = property_map(source_vp)
            changed = []
            for prop_name in APPEARANCE_PROPERTIES:
                if prop_name not in current_props or prop_name not in source_props:
                    continue
                current_prop = current_props[prop_name]
                source_prop = source_props[prop_name]
                if prop_name.endswith("Array") or prop_name == "ShapeAppearance":
                    current_ref = next(iter(current_prop), None)
                    source_ref = next(iter(source_prop), None)
                    if current_ref is None or source_ref is None:
                        continue
                    current_file = current_ref.attrib.get("file")
                    source_file = source_ref.attrib.get("file")
                    if not current_file or not source_file:
                        continue
                    external_replacements[current_file] = source_zip.read(source_file)
                    changed.append(prop_name)
                else:
                    copy_property_children(current_prop, source_prop)
                    changed.append(prop_name)
            if changed:
                repaired_objects.append({"name": name, "properties": sorted(changed)})

        repaired_gui = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        output = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(before)) as current_zip, zipfile.ZipFile(
            output, "w", compression=zipfile.ZIP_DEFLATED
        ) as out_zip:
            for info in current_zip.infolist():
                if info.filename == "GuiDocument.xml":
                    data = repaired_gui
                elif info.filename in external_replacements:
                    data = external_replacements[info.filename]
                else:
                    data = current_zip.read(info.filename)
                out_zip.writestr(info, data)
        after = output.getvalue()

    # Write atomically only after the full archive has been assembled.
    with tempfile.NamedTemporaryFile(
        prefix=model.name + ".", suffix=".tmp", dir=model.parent, delete=False
    ) as tmp:
        tmp.write(after)
        temp_path = Path(tmp.name)
    temp_path.replace(model)

    with zipfile.ZipFile(model) as check:
        ET.fromstring(check.read("GuiDocument.xml"))
        members = check.namelist()
        shape_payloads = [check.read(n) for n in members if n.startswith("ShapeAppearance")]
        line_payloads = [check.read(n) for n in members if n.startswith("LineColorArray")]
        point_payloads = [check.read(n) for n in members if n.startswith("PointColorArray")]
        geometry_unchanged = []
        with zipfile.ZipFile(io.BytesIO(before)) as old_zip:
            for name in members:
                if name == "GuiDocument.xml" or name.startswith(EXTERNAL_PREFIXES):
                    continue
                if old_zip.read(name) != check.read(name):
                    geometry_unchanged.append(name)

    report = {
        "status": "gui-appearance-repaired",
        "model": MODEL_RELATIVE,
        "source_commit": source_commit,
        "baseline_sha256": sha256(before),
        "repaired_sha256": sha256(after),
        "source_archive_sha256": sha256(source),
        "viewproviders": len(current_vps),
        "repaired_objects": len(repaired_objects),
        "external_payloads_replaced": len(external_replacements),
        "shape_appearance_variants": len({sha256(x) for x in shape_payloads}),
        "line_color_array_variants": len({sha256(x) for x in line_payloads}),
        "point_color_array_variants": len({sha256(x) for x in point_payloads}),
        "document_xml_unchanged": True,
        "geometry_members_changed": geometry_unchanged,
        "geometry_unchanged": not geometry_unchanged,
        "limitations": [
            "颜色恢复按稳定对象名复制 FreeCAD GUI 外观数据；不代表材料实测。",
            "屏幕仍保留平面实测输入与曲面透明外观占位的既有限制。",
        ],
        "objects": repaired_objects,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--source-commit", default=DEFAULT_SOURCE_COMMIT)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo.resolve()
    model = (args.model or repo / MODEL_RELATIVE).resolve()
    report_path = (args.report or repo / "cad/drone-concept/color-repair-report.json").resolve()
    report = repair(repo, model, args.source_commit, report_path)
    print(json.dumps({k: report[k] for k in (
        "repaired_sha256", "repaired_objects", "external_payloads_replaced",
        "shape_appearance_variants", "line_color_array_variants", "geometry_unchanged",
    )}, ensure_ascii=False))


if __name__ == "__main__":
    main()
