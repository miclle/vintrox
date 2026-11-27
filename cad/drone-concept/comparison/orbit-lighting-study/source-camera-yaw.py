"""Test a camera-relative studio rig on unchanged CAD and camera projections.

This is a separate lighting hypothesis, never a geometry or silhouette gain.
The official renderer and its defaults remain unchanged. Pass --rig-config in
addition to the normal render_drone_concept arguments after Blender's --.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_drone_concept as renderer


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    index = sys.argv.index('--rig-config')
    config_path = Path(sys.argv[index + 1])
    del sys.argv[index:index + 2]
    config = json.loads(config_path.read_text())
    assert config['mode'] == 'camera-yaw'
    pivot = Vector(config['pivot_mm']) / 1000
    angle_offset = math.radians(config['yaw_offset_degrees'])
    original_light = renderer.area_light
    lights = {}
    poses = []

    def remember_light(name, *args, **kwargs):
        original_light(name, *args, **kwargs)
        obj = bpy.data.objects[name]
        # Compose from properties; matrix_world can be stale until evaluation.
        lights[name] = Matrix.LocRotScale(obj.location.copy(),
                                         obj.rotation_euler.to_quaternion(),
                                         obj.scale.copy())

    def before_render(scene, *unused):
        outward = scene.camera.rotation_euler.to_quaternion() @ Vector((0, 0, 1))
        yaw = math.atan2(outward.x, -outward.y) + angle_offset
        transform = (Matrix.Translation(pivot) @ Matrix.Rotation(yaw, 4, 'Z')
                     @ Matrix.Translation(-pivot))
        for name, matrix in lights.items():
            bpy.data.objects[name].matrix_world = transform @ matrix
        bpy.context.view_layer.update()
        poses.append({'view': Path(scene.render.filepath).stem,
                      'yaw_degrees': math.degrees(yaw),
                      'lights': {name: [list(row) for row in bpy.data.objects[name].matrix_world]
                                 for name in lights}})

    renderer.area_light = remember_light
    bpy.app.handlers.render_pre.append(before_render)
    try:
        renderer.main()
    finally:
        bpy.app.handlers.render_pre.remove(before_render)
        renderer.area_light = original_light
    output = Path(sys.argv[sys.argv.index('--output') + 1])
    manifest_path = output / 'render-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['lighting_experiment'] = {
        'config': config, 'config_path': str(config_path),
        'config_sha256': digest(config_path),
        'wrapper_sha256': digest(Path(__file__)), 'poses': poses,
        'geometry_changed': False, 'camera_changed': False,
        'interpretation': 'unverified studio-rig hypothesis, not geometry improvement'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
