from pathlib import Path
import sys,json,hashlib,math
import bpy
from mathutils import Vector,Quaternion
root=Path(__file__).resolve().parents[5];sys.path.insert(0,str(root/'tools'));import render_drone_concept as renderer
b=root/'cad/drone-concept/comparison';s=b/'orbit-lighting-study';meshpath=Path('/Users/miclle/.codex/visualizations/2026/10/22/01a163d7-dc98-7ce1-af6b-9aa3d7bf5546/drone-belly-relief-cache/formal/render-meshes.json');data=json.loads(meshpath.read_text());bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for item in data['objects']:
 if item['name'].startswith(('SupportShaft','SupportFoot','SupportSocket','CentralSupportSeat')):continue
 mesh=bpy.data.meshes.new(item['name']);mesh.from_pydata([[c/1000 for c in p] for p in item['vertices']],[],item['faces']);mesh.validate(clean_customdata=True);mesh.update();obj=bpy.data.objects.new(item['name'],mesh);bpy.context.collection.objects.link(obj)
axis=Vector(data['bass_axis']).normalized();rotation=Vector((0,0,1)).rotation_difference(axis);pos=Vector(data['bass_origin_mm'])+rotation@Vector(data['bass_warning_label_local_mm']);orient=(rotation@Quaternion(Vector((1,0,0)),math.pi/2)@Quaternion(Vector((0,0,1)),math.pi)).to_euler();renderer.text_decal('RearWarning','WARNING',tuple(pos),data['bass_warning_text_size_mm'],(.035,.035,.025),orient)
bpy.context.view_layer.update();scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();obj=bpy.data.objects['RearWarning'];ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();samples=[]
for t in mesh.loop_triangles:
 ps=[obj.matrix_world@mesh.vertices[i].co for i in t.vertices];center=sum(ps,Vector())/3;n=(ps[1]-ps[0]).cross(ps[2]-ps[0]);area=n.length/2
 if area>1e-14:samples.append((center,n.normalized(),area))
rows=[]
for name in ['cameras.json','stills-58/cameras.json']:
 cfg=json.loads((b/name).read_text())
 for pose in cfg['views']:
  eye=Vector(pose['eye_mm'])/1000;areas={};total=0;front=0
  for point,normal,area in samples:
   if normal.dot(eye-point)<=0:continue
   front+=1;direction=point-eye;total+=area
   hit,location,n,idx,target,matrix=scene.ray_cast(deps,eye,direction.normalized(),distance=direction.length+.000001)
   key=target.name if hit else 'NO_HIT';areas[key]=areas.get(key,0)+area
  rows.append({'view':pose['name'],'front_facing_triangles':front,'visible_area_fraction':areas.get('RearWarning',0)/total if total else 0,'first_hit_area_fractions':{n:a/total for n,a in areas.items()}})
ev.to_mesh_clear();report={'fcstd_sha256':data['fcstd_sha256'],'mesh_sha256':hashlib.sha256(meshpath.read_bytes()).hexdigest(),'renderer_sha256':hashlib.sha256((root/'tools/render_drone_concept.py').read_bytes()).hexdigest(),'method':'Camera rays to front-facing text triangle centroids; area-weighted diagnostic, not raster pixel coverage. Lighting cannot change ray visibility.','views':rows};(s/'letter-visibility.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
