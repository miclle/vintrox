"""Compare tracked reference corners with visible terminal edges for two models."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw
from scipy.spatial import cKDTree

comparison = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(comparison / "v334-nozzle-video-tracks"))
from track import visible_boundary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "candidate", "output"):
        parser.add_argument(name, type=Path, help="Directory")
    parser.add_argument("--labels", nargs=2, default=("v371", "v372"))
    args = parser.parse_args()
    tracks = json.loads((comparison / "v334-nozzle-video-tracks/tracks.json").read_text())
    board = Image.new("RGB", (780, 540), "#171717")
    draw = ImageDraw.Draw(board)
    rows = []
    for row, item in enumerate(tracks["observations"]):
        frame = item["source_frame"]
        anchor = item["manual_anchor_px"]
        view = f"video-{frame//30:02}"
        result = dict(frame=frame, reference_px=anchor, width_px=item["screen_width_px"])
        left, top = anchor[0]-65, anchor[1]-35
        crop = (left, top, left+130, top+76)
        reference = args.baseline / "video-comparison/reference-frames" / f"frame-{frame//30+1:02}.png"
        panels = [("Source", reference, anchor)]
        for name, folder in zip(args.labels, (args.baseline, args.candidate)):
            id_path = folder / "video-ids"
            manifest = json.loads((id_path / "object-id-manifest.json").read_text())
            renders = json.loads((folder / "video-renders/render-manifest.json").read_text())
            if (manifest["fcstd_sha256"] != renders["fcstd_sha256"]
                    or manifest["camera_config_sha256"] != tracks["camera_config_sha256"]
                    or renders["camera_config_sha256"] != tracks["camera_config_sha256"]):
                raise ValueError("IDs, rendered model or tracked camera do not match")
            edge, ids = visible_boundary(id_path, view, manifest)
            distance, index = cKDTree(edge).query(anchor)
            x, y = map(int, edge[index])
            result[name] = dict(fcstd_sha256=manifest["fcstd_sha256"], nearest_px=[x,y],
                                name=manifest["objects"][ids[y,x]]["name"], distance_px=float(distance),
                                percent_screen_width=float(100*distance/item["screen_width_px"]))
            info = next(im for im in renders["images"] if im["view"] == view)
            path = folder / "video-renders" / info["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
                raise ValueError(f"Changed render {path}")
            panels.append((name, path, [x, y]))
        for col, (label, path, point) in enumerate(panels):
            im = Image.open(path).convert("RGB").crop(crop).resize((260,152),Image.Resampling.NEAREST)
            board.paste(im,(col*260,row*180+22))
            draw.text((col*260+4,row*180+3),f"{label}  frame {frame}",fill="white")
            px,py=(point[0]-left)*2+col*260,(point[1]-top)*2+row*180+22
            draw.ellipse((px-5,py-5,px+5,py+5),outline="cyan")
        rows.append(result)
    args.output.mkdir(exist_ok=True)
    board.save(args.output/"tracked-corners.jpg", quality=93)
    (args.output/"tracked-corners.json").write_text(json.dumps(rows, indent=2)+"\n")


if __name__ == "__main__":
    main()
