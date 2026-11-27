"""Project saved exit/lip circles using the renderer's exact Blender camera setup."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ['circles','cameras','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);circles=json.loads(a.circles.read_text());config=json.loads(a.cameras.read_text())
    scene=bpy.context.scene;scene.render.resolution_percentage=100
    camera=bpy.data.objects.new('ExitDiagnosticCamera',bpy.data.cameras.new('ExitDiagnosticCamera'));scene.collection.objects.link(camera);scene.camera=camera
    camera.data.type='PERSP';rows=[]
    shapes={'terminal':{'center_mm':circles['saved_center_mm'],'axis':circles['saved_axis'],'radius_mm':circles['saved_radius_mm']},'gold_lip':circles['gold_lip']}
    for pose in config['views']:
        w,h=pose.get('resolution',config['resolution']);scene.render.resolution_x=w;scene.render.resolution_y=h
        camera.data.lens=pose['lens_mm'];camera.data.sensor_width=pose['sensor_width_mm']
        camera.location=Vector(pose['eye_mm'])/1000
        camera.rotation_euler=(Vector(pose['target_mm'])/1000-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.rotation_euler.rotate_axis('Z',math.radians(pose.get('roll_degrees',0)));bpy.context.view_layer.update()
        record={'view':pose['name'],'resolution':[w,h],'circles':{}}
        for label,shape in shapes.items():
            normal=Vector(shape['axis']).normalized();u=normal.cross(Vector((0,0,1))).normalized();v=normal.cross(u)
            center=Vector(shape['center_mm']);points=[]
            for i in range(720):
                angle=i*math.tau/720;q=(center+shape['radius_mm']*(math.cos(angle)*u+math.sin(angle)*v))/1000
                p=world_to_camera_view(scene,camera,q);points.append([p.x*w,(1-p.y)*h])
            record['circles'][label]=points
        rows.append(record)
    result={'fcstd_sha256':circles['model_sha256'],'saved_circle_source_sha256':digest(a.circles),'camera_config_sha256':digest(a.cameras),'projection_script_sha256':digest(Path(__file__)),'views':rows,'limitations':['Full mathematical circles include hidden portions and gaps between leaves.','Gold lip curve is tube centreline, not an observed silhouette edge.']}
    a.output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
