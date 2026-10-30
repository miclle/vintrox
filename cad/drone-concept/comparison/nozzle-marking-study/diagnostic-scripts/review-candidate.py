"""Render and inspect a saved v51-based depth candidate at frozen cameras."""
import argparse,concurrent.futures,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[5];os.chdir(root);b=Path('cad/drone-concept/comparison');out=a.candidate
py='/Applications/FreeCAD.app/Contents/Resources/bin/python';bl='/Applications/Blender.app/Contents/MacOS/Blender'
env=os.environ|{'PYTHONPATH':'/Applications/FreeCAD.app/Contents/Resources/lib','PYTHONDONTWRITEBYTECODE':'1'}
def run(name,args):
 with (out/(name+'.log')).open('w') as log:subprocess.run(list(map(str,args)),env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 print(name,'done',flush=True)
def render(kind,camera):
 run(kind,[bl,'--background','--threads','4','--python-exit-code','1','--python','tools/render_drone_concept.py','--','--meshes',out/'meshes.json','--model',out/'candidate.FCStd','--comparison',camera,'--output',out/(kind+'-renders')])
 run(kind+'-compare',[py,'tools/compare_drone_reference.py','--renders',out/(kind+'-renders'),'--output',out/kind,'--cameras',camera])
def ids():
 run('ids',[bl,'--background','--threads','4','--python-exit-code','1','--python','tools/render_drone_object_ids.py','--','--meshes',out/'meshes.json','--model',out/'candidate.FCStd','--cameras',b/'cameras.json','--output',out/'ids'])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 fs=[ex.submit(render,'video',b/'cameras.json'),ex.submit(render,'stills',b/'stills-56/cameras.json'),ex.submit(ids)]
 for f in fs:f.result()
jobs=[('side','measure_drone_nozzle_side.py',['--ids',out/'ids','--renders',out/'video-renders','--comparison',out/'video','--output',out/'side-check.json']),('upper','measure_drone_nozzle_fairing.py',['--ids',out/'ids','--renders',out/'video-renders','--comparison',out/'video','--output',out/'upper-check.json']),('surface','measure_drone_nozzle_surfaces.py',['--fitted-markings','--model',out/'candidate.FCStd','--output',out/'surface-check.json']),('emitters','measure_drone_cavity_emitters.py',['--model',out/'candidate.FCStd','--output',out/'emitter-check.json']),('cavity','measure_drone_rear_cavity.py',['--model',out/'candidate.FCStd','--baseline-model',b.parent/'vintrox-drone-concept.FCStd','--output',out/'cavity-check.json'])]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 fs=[ex.submit(run,n,[py,'tools/'+script,*args]) for n,script,args in jobs]
 for f in fs:f.result()
for kind,base in [('video','iteration-85'),('stills','stills-56')]:
 n=json.loads((out/kind/'comparison-report.json').read_text());o=json.loads((b/base/'comparison-report.json').read_text());assert n['camera_config_sha256']==o['camera_config_sha256'];print(kind,n['mean_silhouette_iou'],100*(n['mean_silhouette_iou']-o['mean_silhouette_iou']))
