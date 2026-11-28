"""Compare the first visible top edge in common x-columns of each cuff."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

# Narrow strips above the grip, clear of wings, antenna and top controls.
STRIPS = ((120, 237, 273), (120, 672, 705), (150, 659, 678), (180, 451, 468))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("references", "baseline", "candidate"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    measurements = []
    for frame, left, right in STRIPS:
        number = frame // 30
        name = f"video-{number:02}.png"
        ref = Image.open(args.references / f"frame-{number+1:02}.png").convert("RGB")
        masks = [np.asarray(ref).max(axis=2) > 18]
        for directory in (args.baseline, args.candidate):
            image = Image.open(directory / name).convert("RGBA")
            masks.append(np.asarray(image)[:, :, 3] > 127)
        edges = []
        for mask in masks:
            strip = mask[85:150, left:right]
            if not strip.any(axis=0).all() or strip[0].any():
                raise ValueError(f"Top boundary outside search strip in frame {frame}")
            edges.append(85 + strip.argmax(axis=0))
        row = dict(frame=frame, x_start=left, x_stop=right, search_y=[85, 150])
        for label, edge in zip(("v369", "v370"), edges[1:]):
            error = abs(edge - edges[0])
            row[label] = dict(mean_absolute_px=float(error.mean()), max_absolute_px=int(error.max()))
        measurements.append(row)
    print(json.dumps(measurements, indent=2))


if __name__ == "__main__":
    main()
