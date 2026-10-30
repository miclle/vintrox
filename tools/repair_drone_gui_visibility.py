#!/usr/bin/env python3
"""Repair the saved FreeCAD view state without changing CAD geometry.

The Drone FCStd is a GUI-state-sensitive artifact.  This tool changes only
the Visibility boolean in GuiDocument.xml, keeps the two research envelopes
hidden, and verifies that every other archive member is byte-for-byte stable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path


VIEW_PROVIDER_RE = re.compile(
    r'(<ViewProvider\s+name="(?P<name>[^"]+)"[^>]*>.*?'
    r'<Property\s+name="Visibility"[^>]*>\s*'
    r'<Bool\s+value=")(?P<value>[^"]+)(?P<suffix>"\s*/>\s*</Property>)',
    re.DOTALL,
)
OBJECT_RE = re.compile(r'<Object\s+type="([^"]+)"\s+name="([^"]+)"')

HIDDEN_RESEARCH = {"WooferEnvelope_D88_Depth40", "CDInsertionStudy_D120"}
GEOMETRY_TYPES = {"Part::Feature", "Part::Box"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repair(path: Path, report_path: Path) -> dict:
    with zipfile.ZipFile(path, "r") as source:
        original_members = {info.filename: source.read(info) for info in source.infolist()}
        infos = {info.filename: info for info in source.infolist()}

    if "GuiDocument.xml" not in original_members:
        raise RuntimeError(f"{path} has no GuiDocument.xml; refuse geometry-only repair")
    members = dict(original_members)
    document = original_members["Document.xml"].decode("utf-8")
    gui_before = original_members["GuiDocument.xml"].decode("utf-8")
    # Recover a prior interrupted repair that wrote an invalid value suffix.
    gui_before = re.sub(
        r'(<Bool\s+value=")(true|false)(true|false)\s*\n(\s*</Properties>)',
        r'\1\3"/>\n                </Property>\n\4',
        gui_before,
    )
    object_types = {name: kind for kind, name in OBJECT_RE.findall(document)}

    before = {}
    after = {}

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        old = match.group("value")
        before[name] = old
        # Geometry objects are the formal appearance model.  The two named
        # envelopes are deliberately retained as hidden study placeholders.
        visible = object_types.get(name) in GEOMETRY_TYPES and name not in HIDDEN_RESEARCH
        new = "true" if visible else "false"
        after[name] = new
        return f"{match.group(1)}{new}{match.group('suffix')}"

    gui_after, replacements = VIEW_PROVIDER_RE.subn(replace, gui_before)
    if replacements != len(before):
        raise RuntimeError(f"unexpected GuiDocument replacement count: {replacements}")
    if set(before) != set(after):
        raise RuntimeError("visibility map changed during repair")

    members["GuiDocument.xml"] = gui_after.encode("utf-8")
    with tempfile.NamedTemporaryFile(prefix=path.name + ".", suffix=".tmp", dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(temp_path, "w") as target:
            for info in infos.values():
                target.writestr(info, members[info.filename])
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)

    unchanged = []
    changed = []
    with zipfile.ZipFile(path, "r") as check:
        for name, old_bytes in original_members.items():
            current = check.read(name)
            if name == "GuiDocument.xml":
                changed.append(name)
            elif current == old_bytes:
                unchanged.append(name)
            else:
                raise RuntimeError(f"archive member changed unexpectedly: {name}")

    report = {
        "tool": "tools/repair_drone_gui_visibility.py",
        "path": str(path),
        "geometry_unchanged": True,
        "archive_members": len(members),
        "changed_members": changed,
        "unchanged_members": len(unchanged),
        "view_providers": replacements,
        "before_visibility": {"true": sum(v == "true" for v in before.values()), "false": sum(v == "false" for v in before.values())},
        "after_visibility": {"true": sum(v == "true" for v in after.values()), "false": sum(v == "false" for v in after.values())},
        "hidden_research": sorted(HIDDEN_RESEARCH),
        "hidden_research_after": sorted(name for name in HIDDEN_RESEARCH if after.get(name) == "false"),
        "fcstd_sha256": sha256(path.read_bytes()),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fcstd", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(repair(args.fcstd, args.report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
