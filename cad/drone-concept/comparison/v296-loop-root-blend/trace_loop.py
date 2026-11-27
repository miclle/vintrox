import argparse
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path.cwd() / "tools"))
from diagnose_drone_petal_occlusion import digest, observation_rays, trace

parser = argparse.ArgumentParser()
for name in ("model", "mesh", "cameras", "samples", "output"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
mesh = json.loads(args.mesh.read_text())
model_hash = digest(args.model)
if mesh["fcstd_sha256"] != model_hash:
    raise ValueError("Mesh does not match saved FCStd")
mesh["objects"] = [
    obj for obj in mesh["objects"]
    if not obj["name"].startswith(("SupportShaft", "SupportFoot", "SupportSocket", "CentralSupportSeat"))
]
scene = bpy.context.scene
camera = bpy.data.objects.new("RayCamera", bpy.data.cameras.new("RayCamera"))
camera.data.type = "PERSP"
config = json.loads(args.cameras.read_text())
samples = json.loads(args.samples.read_text())
views = [{"view": f"video-{row['source_frame']//30:02d}", "reference_px": row["reference_px"]}
         for row in samples["fitted"] if row["source_frame"] == 180]
rays = observation_rays(camera, scene, config, views)
records = []
for (_, xy, _, _), hits in zip(rays, trace(mesh, rays)):
    hits.sort()
    first = hits[0] if hits else None
    loop = next((hit for hit in hits if hit[1] == "UnderbodyLoop1"), None)
    records.append({
        "reference_px": xy,
        "first_hit": first[1] if first else None,
        "right_loop_hit": loop is not None,
        "right_loop_behind_first_hit_mm": loop[0] - first[0] if loop else None,
    })
args.output.write_text(json.dumps({"fcstd_sha256": model_hash,
                                   "camera_sha256": digest(args.cameras), "records": records}, indent=2) + "\n")
