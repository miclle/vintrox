"""Render opaque object IDs for contour diagnosis, never as presentation images.

Uses the same saved triangles and cameras. Transparent surfaces are deliberately
opaque here; attribution is approximate at antialiased edges and occlusions.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--meshes',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cameras',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root=Path(__file__).resolve().parents[1]
    model=root/'cad/drone-concept/vintrox-drone-concept.FCStd'
    data=json.loads(args.meshes.read_text())
    digest=hashlib.sha256(model.read_bytes()).hexdigest()
    if digest!=data['fcstd_sha256']:raise ValueError('Stale CAD triangles')
    config=json.loads(args.cameras.read_text())
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    objects=[]
    for item in data['objects']:
        if item['name'].startswith(('SupportShaft','SupportFoot','SupportSocket','CentralSupportSeat')):continue
        i=len(objects)
        rgb=[8+16*(i%16),8+16*((i//16)%16),32+64*(i//256)]
        linear=[c/255/12.92 if c/255<=.04045 else ((c/255+.055)/1.055)**2.4 for c in rgb]
        material=bpy.data.materials.new(item['name']);material.use_nodes=True
        nodes=material.node_tree.nodes;nodes.clear()
        emit=nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(*linear,1)
        output=nodes.new('ShaderNodeOutputMaterial');material.node_tree.links.new(emit.outputs[0],output.inputs['Surface'])
        mesh=bpy.data.meshes.new(item['name'])
        mesh.from_pydata([[c/1000 for c in p] for p in item['vertices']],[],item['faces'])
        mesh.validate(clean_customdata=True);mesh.update()
        obj=bpy.data.objects.new(item['name'],mesh);bpy.context.collection.objects.link(obj)
        mesh.materials.append(material)
        objects.append({'name':item['name'],'rgb':rgb})
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
    scene.cycles.max_bounces=0;scene.cycles.pixel_filter_type='BOX';scene.cycles.filter_width=.01
    scene.render.film_transparent=True
    scene.render.resolution_percentage=100
    scene.render.resolution_x,scene.render.resolution_y=config['resolution']
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.view_settings.exposure=0;scene.view_settings.gamma=1
    camera=bpy.data.objects.new('IDCamera',bpy.data.cameras.new('IDCamera'))
    bpy.context.collection.objects.link(camera);scene.camera=camera
    camera.data.type='PERSP'
    args.output.mkdir(parents=True,exist_ok=True)
    images=[]
    for pose in config['views']:
        camera.data.lens=pose['lens_mm'];camera.data.sensor_width=pose['sensor_width_mm']
        camera.location=Vector(pose['eye_mm'])/1000
        camera.rotation_euler=(Vector(pose['target_mm'])/1000-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.rotation_euler.rotate_axis('Z',math.radians(pose.get('roll_degrees',0)))
        path=args.output/(pose['name']+'.png');scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        images.append({'view':pose['name'],'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'fcstd_sha256':digest,'camera_config_sha256':hashlib.sha256(args.cameras.read_bytes()).hexdigest(),
              'objects':objects,'images':images,'method':'opaque object ID emission; unchanged saved triangles',
              'limitations':['glass is opaque for attribution','edge attribution is approximate',
                             'does not change the primary silhouette score or segmentation']}
    (args.output/'object-id-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
