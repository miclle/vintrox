"""Render exported CAD tessellation in Blender; no generated image geometry.

Usage: Blender --background --python tools/render_drone_concept.py --
  --meshes /tmp/vintrox-drone-render-meshes.json --output cad/drone-concept/renders
The mesh export is made by build-drone-concept.FCMacro in the OS temp folder.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile

import bpy
from mathutils import Vector


def material(color, kind):
    """Make restrained enamel, metal, rubber, screen, or indicator material."""
    key = f'{kind}_{tuple(round(v, 3) for v in color)}'
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    mat = bpy.data.materials.new(key)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    # CAD colours are display sRGB; convert them before the scene transform.
    linear = tuple(((v+.055)/1.055)**2.4 if v > .04045 else v/12.92 for v in color)
    shader.inputs['Base Color'].default_value = (*linear, 1)
    shader.inputs['Metallic'].default_value = .75 if kind == 'metal' else .28 if kind == 'paint' else 0
    shader.inputs['Roughness'].default_value = .34 if kind == 'metal' else .43 if kind == 'paint' else .65
    if kind in ('emission', 'red_light', 'screen'):
        shader.inputs['Emission Color'].default_value = (*linear, 1)
        shader.inputs['Emission Strength'].default_value = 3.3 if kind == 'emission' else .35 if kind == 'screen' else .8
        shader.inputs['Roughness'].default_value = .24
    if kind == 'screen':
        shader.inputs['Coat Weight'].default_value = .65
        shader.inputs['Coat Roughness'].default_value = .16
    if kind == 'paint':
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 180
        noise.inputs['Detail'].default_value = 3
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .18
        ramp.color_ramp.elements[0].color = tuple(c*.68 for c in linear)+(1,)
        ramp.color_ramp.elements[1].position = .8
        ramp.color_ramp.elements[1].color = tuple(min(c*1.17, 1) for c in linear)+(1,)
        links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .13
        bump.inputs['Distance'].default_value = .00018
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return mat


def text_decal(name, text, position, size, color, rotation=(math.pi/2, 0, 0)):
    """Render-only surface lettering; does not imply a CAD engraving."""
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = text
    curve.size = size/1000
    curve.space_character = 1.12
    curve.extrude = .00001
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = Vector(position)/1000
    obj.rotation_euler = rotation
    obj.data.materials.append(material(color, 'paint'))


def area_light(name, position, energy, size, color, target=(0, 80, 175)):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = energy
    light.shape = 'DISK'
    light.size = size
    light.color = color
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = Vector(position)/1000
    obj.rotation_euler = (Vector(target)/1000-obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    """Read saved-model-bound meshes and render four deterministic viewpoints."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--meshes', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--views', nargs='+', default=['hero', 'rear', 'front', 'right'])
    parser.add_argument('--turntable', action='store_true', help='Render a 12 second full camera orbit')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    data = json.loads(args.meshes.read_text())
    root = Path(__file__).resolve().parents[1]
    model = root/'cad/drone-concept/vintrox-drone-concept.FCStd'
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    if digest != data['fcstd_sha256']:
        raise RuntimeError('Render meshes do not match saved FCStd; rebuild the concept.')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for item in data['objects']:
        mesh = bpy.data.meshes.new(item['name'])
        mesh.from_pydata([[c/1000 for c in p] for p in item['vertices']], [], item['faces'])
        mesh.update()
        obj = bpy.data.objects.new(item['name'], mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material(item['color'], item['material']))
        # Preserve real CAD edges while smoothing cylindrical/lofted surfaces.
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        mesh.set_sharp_from_angle(angle=math.radians(35))
        bevel = obj.modifiers.new('SmallEdgeHighlight', 'BEVEL')
        bevel.width = .00028
        bevel.segments = 2
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = .5
        normal = obj.modifiers.new('WeightedNormals', 'WEIGHTED_NORMAL')
        normal.keep_sharp = True
        normal.weight = 30
    cream = (.85, .83, .65)
    text_decal('ControlLegend', 'DISC  /  LIBRARY  /  ONLINE', (-102, -25.3, 53), 2.3, cream)
    # Labels follow the tilted nozzle, instead of floating in the open chassis.
    axis = Vector((0, .83, -.56)).normalized()
    rotation = Vector((0, 0, 1)).rotation_difference(axis)
    from mathutils import Quaternion
    label_rotation = (rotation @ Quaternion(Vector((1, 0, 0)), math.pi/2)).to_euler()
    label_pos = Vector((0, 168, 162)) + rotation @ Vector((-17, -70.5, 51))
    text_decal('RearWarning', 'WARNING', tuple(label_pos), 4, (.035, .035, .025), label_rotation)
    alert_pos = Vector((0, 168, 162)) + rotation @ Vector((-1, -71.3, 71))
    text_decal('RearAlert', '!', tuple(alert_pos), 7, cream, label_rotation)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.world.color = (.065, .065, .065)
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = -.6
    ground_z = min(p[2] for item in data['objects'] for p in item['vertices'])
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, ground_z/1000))
    ground = bpy.context.object
    ground.name = 'StudioGround'
    ground.data.materials.append(material((.075, .084, .092), 'rubber'))
    area_light('KeySoftbox', (420, -470, 740), 24, .65, (1, .86, .65))
    area_light('CoolFill', (-480, -150, 400), 14, .55, (.63, .81, 1))
    area_light('RearRim', (100, 620, 620), 32, .45, (.63, .89, 1))
    area_light('FrontFill', (0, -650, 250), 6, .45, (1, 1, 1))
    camera_data = bpy.data.cameras.new('ConceptCamera')
    camera = bpy.data.objects.new('ConceptCamera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .63
    views = {'hero': ((-650, -1000, 365), (0, 83, 142)),
             'rear': ((510, 820, 380), (0, 105, 142)),
             'closeup': ((-700, -1050, 350), (0, 65, 142)),
             'front': ((0, -1000, 305), (0, 65, 142)),
             'right': ((900, 40, 340), (0, 105, 142))}
    args.output.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name in args.views:
        eye, target = views[name]
        camera.data.ortho_scale = .63
        camera.location = Vector(eye)/1000
        camera.rotation_euler = (Vector(target)/1000-camera.location).to_track_quat('-Z', 'Y').to_euler()
        ground.hide_render = name == 'closeup'
        scene.world.color = (.002, .002, .002) if name == 'closeup' else (.065, .065, .065)
        camera.data.type = 'PERSP' if name == 'closeup' else 'ORTHO'
        camera.data.lens = 88
        if name == 'closeup':
            camera.rotation_euler.rotate_axis('Z', math.radians(11))
        scene.render.filepath = str(args.output/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        outputs.append({'view': name, 'path': name+'.png',
                        'sha256': hashlib.sha256((args.output/(name+'.png')).read_bytes()).hexdigest()})
    video = None
    if args.turntable:
        ground.hide_render = False
        scene.world.color = (.065, .065, .065)
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = .63
        frames = Path(tempfile.mkdtemp(prefix='vintrox-drone-orbit-'))
        scene.render.resolution_x = 900
        scene.render.resolution_y = 900
        scene.cycles.samples = 12
        for i in range(96):
            angle = math.radians(-121+i*360/96)
            camera.location = Vector((960*math.cos(angle), 85+960*math.sin(angle), 365))/1000
            camera.rotation_euler = (Vector((0, 85, 142))/1000-camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(frames/f'{i:03}.png')
            bpy.ops.render.render(write_still=True)
        path = args.output/'turntable.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '8', '-i', str(frames/'%03d.png'),
                        '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', '30',
                        '-movflags', '+faststart', str(path)], check=True)
        # Eight orthogonal/diagonal views are also kept as one review board.
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '8', '-i', str(frames/'%03d.png'),
                        '-vf', "select='not(mod(n,12))',scale=450:450,tile=4x2", '-frames:v', '1',
                        str(args.output/'orbit-board.png')], check=True)
        video = {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'duration_seconds': 12, 'unique_angles': 96}
        for frame in frames.glob('*.png'):
            frame.unlink()
        frames.rmdir()
    board = args.output/'orbit-board.png'
    (args.output/'render-manifest.json').write_text(json.dumps({
        'renderer': 'Blender '+bpy.app.version_string, 'method': 'saved CAD tessellation; Cycles',
        'fcstd_sha256': digest, 'cad_geometry_features': len(data['objects']),
        'render_only': ['studio lighting', 'procedural enamel texture', 'surface lettering'],
        'physical_validation': False, 'images': outputs, 'turntable': video,
        'review_board': {'path': board.name, 'sha256': hashlib.sha256(board.read_bytes()).hexdigest()} if args.turntable else None,
    }, indent=2)+'\n')


if __name__ == '__main__':
    main()
