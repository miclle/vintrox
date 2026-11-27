"""Rank saved fixed-camera contour studies against the formal Drone baseline.

This report keeps the ten video views separate so a local improvement cannot
silently promote a candidate that regresses other directions.  It reads only
the saved comparison reports and never changes CAD or image data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def report(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if len(data.get("views", [])) != 10:
        raise ValueError(f"expected ten video views: {path}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline = report(args.baseline)
    base_scores = [row["silhouette_iou"] for row in baseline["views"]]
    rows = []
    for path in args.candidates:
        data = report(path)
        if data.get("camera_config_sha256") != baseline.get("camera_config_sha256"):
            raise ValueError(f"camera mismatch: {path}")
        scores = [row["silhouette_iou"] for row in data["views"]]
        delta = [score - old for score, old in zip(scores, base_scores)]
        rows.append({
            "report": str(path),
            "mean_silhouette_iou": data["mean_silhouette_iou"],
            "delta_mean": data["mean_silhouette_iou"] - baseline["mean_silhouette_iou"],
            "improved_views": sum(value > 0 for value in delta),
            "regressed_views": sum(value < 0 for value in delta),
            "delta_by_view": [
                {"view": row["view"], "delta": value}
                for row, value in zip(data["views"], delta)
            ],
        })
    rows.sort(key=lambda row: (row["delta_mean"], row["improved_views"]), reverse=True)
    result = {
        "baseline": str(args.baseline),
        "baseline_mean_silhouette_iou": baseline["mean_silhouette_iou"],
        "camera_config_sha256": baseline.get("camera_config_sha256"),
        "registration": baseline.get("registration"),
        "candidates": rows,
        "interpretation": "screen-space diagnostic; candidate promotion requires geometry/readback and visual review",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
