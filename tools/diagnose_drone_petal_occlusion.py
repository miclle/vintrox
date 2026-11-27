"""Trace fixed-camera rays through saved CAD at annotated nozzle tip pixels.

Run as a background Blender script. Each ray sees the full saved model and
also records the nearest leaf hit behind any foreground geometry.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def observation_rays(camera, scene, config, observations):
    poses = {pose['name']: pose for pose in config['views']}
    rays = []
    for observation in observations:
        pose = poses[observation['view']]
        width, height = pose.get('resolution', config['resolution'])
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        camera.data.lens = pose['lens_mm']
        camera.data.sensor_width = pose['sensor_width_mm']
        camera.location = Vector(pose['eye_mm'])
        direction = Vector(pose['target_mm']) - camera.location
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        camera.rotation_euler.rotate_axis('Z', math.radians(pose.get('roll_degrees', 0)))
        top_right, bottom_right, bottom_left, top_left = camera.data.view_frame(scene=scene)
        down = bottom_left - top_left
        right = top_right - top_left
        for x, y in observation['reference_px']:
            local = top_left + right * ((x + .5) / width) + down * ((y + .5) / height)
            world = camera.rotation_euler.to_matrix() @ local.normalized()
            rays.append((observation['view'], [x, y], camera.location.copy(), world))
    return rays


def trace(mesh, rays):
    hits = [[] for _ in rays]
    for obj in mesh['objects']:
        tree = BVHTree.FromPolygons(obj['vertices'], obj['faces'], all_triangles=True)
        for result, (_, _, eye, direction) in zip(hits, rays):
            location, _, _, distance = tree.ray_cast(eye, direction)
            if location is not None:
                result.append((distance, obj['name']))
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('model', 'meshes', 'video-cameras', 'still-cameras',
                 'observations', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    mesh = json.loads(args.meshes.read_text())
    model_hash = digest(args.model)
    if mesh['fcstd_sha256'] != model_hash:
        raise ValueError('mesh does not match saved model')
    observations = json.loads(args.observations.read_text())['views']
    scene = bpy.context.scene
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    camera = bpy.data.objects.new('RayCamera', bpy.data.cameras.new('RayCamera'))
    camera.data.type = 'PERSP'
    rays = []
    for prefix, path in [('video-', args.video_cameras), ('still-', args.still_cameras)]:
        config = json.loads(path.read_text())
        selected = [view for view in observations if view['view'].startswith(prefix)]
        rays.extend(observation_rays(camera, scene, config, selected))
    records = []
    for (view, xy, _, _), hits in zip(rays, trace(mesh, rays)):
        ordered = sorted(hits)
        first = ordered[0] if ordered else None
        leaf = next((hit for hit in ordered if hit[1].startswith('NozzlePetal')), None)
        records.append({
            'view': view, 'reference_px': xy,
            'first_hit': first[1] if first else None,
            'first_petal_hit': leaf[1] if leaf else None,
            'petal_depth_behind_first_hit_mm': leaf[0] - first[0] if leaf else None,
        })
    result = {
        'fcstd_sha256': model_hash,
        'mesh_sha256': digest(args.meshes),
        'video_camera_sha256': digest(args.video_cameras),
        'still_camera_sha256': digest(args.still_cameras),
        'observations_sha256': digest(args.observations),
        'script_sha256': digest(Path(__file__)),
        'records': records,
        'limitations': [
            'Rays use pixel centers and saved tessellation, with opaque intersections.',
            'A miss does not establish where an observed tip belongs in 3D.',
            'These are local diagnostics on existing annotations.',
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
