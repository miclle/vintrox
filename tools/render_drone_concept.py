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
    shader.inputs['Metallic'].default_value = .75 if kind == 'metal' else .52 if kind == 'paint' else 0
    shader.inputs['Roughness'].default_value = .3 if kind == 'metal' else .38 if kind == 'paint' else .65
    if kind == 'cast_metal':
        shader.inputs['Metallic'].default_value = .6
        shader.inputs['Roughness'].default_value = .48
    if kind == 'ink':
        shader.inputs['Specular IOR Level'].default_value = 0
        shader.inputs['Roughness'].default_value = 1
    if kind == 'cable':
        shader.inputs['Roughness'].default_value = .25
        shader.inputs['Coat Weight'].default_value = .25
        shader.inputs['Coat Roughness'].default_value = .15
    if kind == 'glass':
        shader.inputs['Base Color'].default_value = (.94, 1, .94, 1)
        shader.inputs['Transmission Weight'].default_value = 1
        # Effective display shading for reduced glare, not a specified glass IOR.
        shader.inputs['IOR'].default_value = 1.10
        shader.inputs['Roughness'].default_value = .09
        shader.inputs['Specular IOR Level'].default_value = .02
    if kind in ('emission', 'red_light', 'screen'):
        shader.inputs['Emission Color'].default_value = (*linear, 1)
        shader.inputs['Emission Strength'].default_value = 3.3 if kind == 'emission' else .35 if kind == 'screen' else .8
        shader.inputs['Roughness'].default_value = .24
    if kind == 'screen':
        shader.inputs['Coat Weight'].default_value = .05
        shader.inputs['Specular IOR Level'].default_value = .05
        shader.inputs['Coat Roughness'].default_value = .16
        if color[1] > color[0]*1.4:
            # Display shading only; the screen and expression stay actual CAD.
            coordinate = nodes.new('ShaderNodeTexCoord')
            flat = nodes.new('ShaderNodeVectorMath'); flat.operation = 'MULTIPLY'
            flat.inputs[1].default_value = (1, 0, 1)
            links.new(coordinate.outputs['Generated'], flat.inputs[0])
            distance = nodes.new('ShaderNodeVectorMath'); distance.operation = 'DISTANCE'
            distance.inputs[1].default_value = (.46, 0, .57)
            links.new(flat.outputs['Vector'], distance.inputs[0])
            vignette = nodes.new('ShaderNodeValToRGB')
            vignette.color_ramp.elements[0].position = .05
            vignette.color_ramp.elements[0].color = (linear[0]*3,linear[1]*1.5,linear[2]*3,1)
            vignette.color_ramp.elements[1].position = .73
            vignette.color_ramp.elements[1].color = tuple(v*.24 for v in linear)+(1,)
            middle = vignette.color_ramp.elements.new(.48)
            middle.color = tuple(v*1.15 for v in linear)+(1,)
            links.new(distance.outputs['Value'], vignette.inputs['Fac'])
            wave = nodes.new('ShaderNodeTexWave'); wave.bands_direction = 'DIAGONAL'
            wave.inputs['Scale'].default_value = 240
            links.new(coordinate.outputs['Generated'],wave.inputs['Vector'])
            grid = nodes.new('ShaderNodeMixRGB'); grid.blend_type = 'MULTIPLY'
            grid.inputs[0].default_value = .12
            links.new(vignette.outputs['Color'],grid.inputs[1])
            links.new(wave.outputs['Color'],grid.inputs[2])
            links.new(grid.outputs['Color'],shader.inputs['Base Color'])
            links.new(grid.outputs['Color'],shader.inputs['Emission Color'])
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
        stain = nodes.new('ShaderNodeTexNoise')
        stain.inputs['Scale'].default_value = 4
        stain.inputs['Detail'].default_value = 4
        patina = nodes.new('ShaderNodeValToRGB')
        patina.color_ramp.elements[0].position = .22
        patina.color_ramp.elements[0].color = (.28,.24,.19,1)
        patina.color_ramp.elements[1].position = .72
        patina.color_ramp.elements[1].color = (1,1,1,1)
        links.new(stain.outputs['Fac'],patina.inputs['Fac'])
        finish = nodes.new('ShaderNodeMixRGB'); finish.blend_type = 'MULTIPLY'
        finish.inputs[0].default_value = .3
        links.new(ramp.outputs['Color'],finish.inputs[1])
        links.new(patina.outputs['Color'],finish.inputs[2])
        links.new(finish.outputs['Color'], shader.inputs['Base Color'])
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
    obj.data.materials.append(material(color, 'ink'))


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
    """Read saved-model-bound meshes and render deterministic review viewpoints."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--meshes', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--views', nargs='+', default=['hero', 'rear', 'front', 'right'])
    parser.add_argument('--turntable', action='store_true', help='Render a 12 second full camera orbit')
    parser.add_argument('--comparison', type=Path, help='Calibrated camera poses for reference comparison')
    parser.add_argument('--model', type=Path, help='Saved FCStd bound to the supplied meshes')
    parser.add_argument('--device', choices=('CPU', 'METAL'), default='CPU',
                        help='CPU for comparison reproducibility; optional Apple Metal for display renders')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    renderer_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.device == 'METAL':
        preferences = bpy.context.preferences.addons['cycles'].preferences
        preferences.compute_device_type = 'METAL'
        preferences.get_devices()
        if not any(device.type == 'METAL' for device in preferences.devices):
            raise RuntimeError('No Metal device is available')
        for device in preferences.devices:
            device.use = device.type == 'METAL'
    data = json.loads(args.meshes.read_text())
    root = Path(__file__).resolve().parents[1]
    model = args.model or root/'cad/drone-concept/vintrox-drone-concept.FCStd'
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    if digest != data['fcstd_sha256']:
        raise RuntimeError('Render meshes do not match saved FCStd; rebuild the concept.')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    validated_meshes = []
    for item in data['objects']:
        if args.comparison and item['name'].startswith(('SupportShaft','SupportFoot','SupportSocket','CentralSupportSeat')):
            continue
        mesh = bpy.data.meshes.new(item['name'])
        mesh.from_pydata([[c/1000 for c in p] for p in item['vertices']], [], item['faces'])
        if mesh.validate(clean_customdata=True):
            validated_meshes.append(item['name'])
        mesh.update()
        obj = bpy.data.objects.new(item['name'], mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material(item['color'], item['material']))
        # Preserve real CAD edges while smoothing cylindrical/lofted surfaces.
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        mesh.set_sharp_from_angle(angle=math.radians(35))
        # Keep the saved CAD silhouette. Render-only bevels can also crash on
        # trimmed B-spline tessellation after affine proportion adjustments.
    bpy.context.view_layer.update()
    cream = (.85, .83, .65)
    for side,suffix in ((-1,'Left'),(1,'Right')):
        plaque=bpy.data.objects.get('CheekUtilityLabel'+suffix)
        if plaque:
            corners=[plaque.matrix_world@Vector(corner)*1000 for corner in plaque.bound_box]
            x=(max(p.x for p in corners)+.25) if side>0 else (min(p.x for p in corners)-.25)
            y=(min(p.y for p in corners)+1) if side>0 else (max(p.y for p in corners)-1)
            z=max(p.z for p in corners)-4.8
            orientation=(math.pi/2,0,side*math.pi/2)
            text_decal('UtilityInitials'+suffix,'G\nU\nS',(x,y,z),4.7,cream,orientation)
            text_decal('UtilityLegend'+suffix,'ENERAL\nTILITY\nYSTEM',(x,y+side*4.2,z),4.7,(.035,.035,.025),orientation)
    # Labels follow the tilted nozzle, instead of floating in the open chassis.
    axis = Vector(data.get('bass_axis', (0, .83, -.56))).normalized()
    bass_origin = Vector(data.get('bass_origin_mm', (0, 168, 162)))
    rotation = Vector((0, 0, 1)).rotation_difference(axis)
    from mathutils import Quaternion
    label_rotation = (rotation @ Quaternion(Vector((1, 0, 0)), math.pi/2)
                      @ Quaternion(Vector((0, 0, 1)), math.pi)).to_euler()
    label_pos = bass_origin + rotation @ Vector(data.get('bass_warning_label_local_mm', (12, -73.5, 57)))
    text_decal('RearWarning', 'WARNING', tuple(label_pos), data.get('bass_warning_text_size_mm',6.2), (.035, .035, .025), label_rotation)
    alert_local = data.get('bass_alert_local_mm', (1, -66.3, 25) if 'bass_axis' in data else (1, -71.3, 78))
    alert_pos = bass_origin + rotation @ Vector(alert_local)
    text_decal('RearAlert', '!', tuple(alert_pos), data.get('bass_alert_text_size_mm',7), cream, label_rotation)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU' if args.device == 'METAL' else 'CPU'
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
    area_light('ScreenReflection', (400, -800, 350), 2, .12, (1, 1, 1), target=(0,0,150))
    area_light('LowerSoftbox', (0,-420,20),3,.45,(.8,.9,1),target=(0,100,30))
    area_light('UndersideInspection', (80, -220, -420), 14, .5, (.8, .9, 1), target=(0,90,15))
    underside_light = bpy.data.objects['UndersideInspection']
    underside_light.hide_render = True
    camera_data = bpy.data.cameras.new('ConceptCamera')
    camera = bpy.data.objects.new('ConceptCamera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .63
    if args.comparison:
        config = json.loads(args.comparison.read_text())
        scene.render.resolution_x, scene.render.resolution_y = config['resolution']
        scene.render.film_transparent = True
        scene.cycles.samples = 16
        ground.hide_render = True
        args.output.mkdir(parents=True, exist_ok=True)
        outputs = []
        for pose in config['views']:
            scene.render.resolution_x, scene.render.resolution_y = pose.get('resolution', config['resolution'])
            camera.data.type = pose.get('projection','ORTHO')
            camera.data.ortho_scale = pose['ortho_scale_mm']/1000
            camera.data.lens = pose.get('lens_mm', 59.2)
            camera.data.sensor_width = pose.get('sensor_width_mm', 36)
            camera.location = Vector(pose['eye_mm'])/1000
            camera.rotation_euler = (Vector(pose['target_mm'])/1000-camera.location).to_track_quat('-Z','Y').to_euler()
            camera.rotation_euler.rotate_axis('Z', math.radians(pose.get('roll_degrees', 0)))
            path = args.output/(pose['name']+'.png')
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            outputs.append({'view':pose['name'],'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        (args.output/'render-manifest.json').write_text(json.dumps({
            'fcstd_sha256':digest,'camera_config_sha256':hashlib.sha256(args.comparison.read_bytes()).hexdigest(),
            'renderer_script_sha256':renderer_digest, 'compute_device':args.device,
            'mesh_validation_repairs':validated_meshes,
            'excluded_added_support_prefixes':['SupportShaft','SupportFoot','SupportSocket','CentralSupportSeat'],
            'images':outputs,'method':'unaltered CAD tessellation; calibrated camera; transparent background',
        },indent=2)+'\n')
        return
    views = {'hero': ((-650, -1000, 365), (0, 83, 142)),
             'rear': ((510, 820, 380), (0, 105, 142)),
             'closeup': ((-700, -1050, 350), (0, 65, 142)),
             'front': ((0, -1000, 305), (0, 65, 142)),
             'right': ((900, 40, 340), (0, 105, 142)),
             'armour-detail': ((-650, -450, 420), (-70, 95, 230)),
             'nozzle-detail': ((380, 780, 280), (0, 205, 163)),
             'top': ((360, -480, 820), (0, 90, 270)),
             'underside': ((420, -560, -380), (0, 90, 5))}
    args.output.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name in args.views:
        eye, target = views[name]
        camera.data.ortho_scale = .35 if name in ('armour-detail','nozzle-detail','top','underside') else .63
        camera.location = Vector(eye)/1000
        camera.rotation_euler = (Vector(target)/1000-camera.location).to_track_quat('-Z', 'Y').to_euler()
        ground.hide_render = name in ('closeup','underside')
        underside_light.hide_render = name != 'underside'
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
        underside_light.hide_render = True
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
        'renderer_script_sha256': renderer_digest, 'compute_device':args.device,
        'mesh_validation_repairs': validated_meshes,
        'fcstd_sha256': digest, 'cad_geometry_features': len(data['objects']),
        'render_only': ['studio lighting', 'procedural enamel texture', 'surface lettering'],
        'physical_validation': False, 'images': outputs, 'turntable': video,
        'review_board': {'path': board.name, 'sha256': hashlib.sha256(board.read_bytes()).hexdigest()} if args.turntable else None,
    }, indent=2)+'\n')


if __name__ == '__main__':
    main()
