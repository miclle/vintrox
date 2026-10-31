#!/usr/bin/env python3
"""Copy the formal object palette onto a candidate mesh binding by object name.

Candidate geometry remains authoritative: vertices and faces are checked byte for
byte before and after the palette-only update.  The palette source is the saved
formal render cache, so this does not rebuild or transform candidate geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--palette", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    candidate = json.loads(args.candidate.read_text())
    palette = json.loads(args.palette.read_text())
    candidate_objects = {item["name"]: item for item in candidate["objects"]}
    palette_objects = {item["name"]: item for item in palette["objects"]}
    if set(candidate_objects) != set(palette_objects):
        missing = sorted(set(candidate_objects) - set(palette_objects))
        extra = sorted(set(palette_objects) - set(candidate_objects))
        raise SystemExit(f"object names differ; candidate-only={missing[:5]} palette-only={extra[:5]}")

    before_geometry = {
        name: digest({"vertices": obj["vertices"], "faces": obj["faces"]})
        for name, obj in candidate_objects.items()
    }
    restored = 0
    colors = set()
    for name, obj in candidate_objects.items():
        source = palette_objects[name]
        obj["color"] = source["color"]
        if "material" in source:
            obj["material"] = source["material"]
        colors.add(tuple(obj["color"]))
        restored += 1
    after_geometry = {
        name: digest({"vertices": obj["vertices"], "faces": obj["faces"]})
        for name, obj in candidate_objects.items()
    }
    if before_geometry != after_geometry:
        raise SystemExit("geometry changed during palette restoration")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidate, separators=(",", ":")), encoding="utf-8")
    report = {
        "status": "palette-restored-by-stable-object-name",
        "candidate_input": str(args.candidate),
        "palette_source": str(args.palette),
        "output": str(args.output),
        "candidate_fcstd_sha256": candidate["fcstd_sha256"],
        "objects": restored,
        "distinct_rgb_triples": len(colors),
        "geometry_unchanged": True,
        "geometry_binding": "candidate vertices and faces retained byte-for-byte",
        "limitations": ["object-level display palette evidence only; no material or physical acceptance"],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
