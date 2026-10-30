"""Review a saved inner bevel at the frozen v52 cameras and rendering settings."""
from pathlib import Path
import os,sys,json,subprocess,concurrent.futures,argparse
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[5];os.chdir(root);b=Path('cad/drone-concept/comparison');out=a.candidate
py='/Applications/FreeCAD.app/Contents/Resources/bin/python';bl='/Applications/Blender.app/Contents/MacOS/Blender';env=os.environ|{'PYTHONPATH':'/Applications/FreeCAD.app/Contents/Resources/lib','PYTHONDONTWRITEBYTECODE':'1'}
def run(n,args):
 with (out/(n+'.log')).open('w') as log:subprocess.run(list(map(str,args)),env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 print(n,'done',flush=True)
def view(kind,camera):
 run(kind,[bl,'--background','--threads','4','--python-exit-code','1','--python','tools/render_drone_concept.py','--','--meshes',out/'meshes.json','--model',out/'candidate.FCStd','--comparison',camera,'--output',out/(kind+'-renders')])
 run(kind+'-comparison',[py,'tools/compare_drone_reference.py','--renders',out/(kind+'-renders'),'--output',out/kind,'--cameras',camera])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 fs=[ex.submit(view,'video',b/'cameras.json'),ex.submit(view,'stills',b/'stills-57/cameras.json'),ex.submit(run,'outline',[py,'tools/measure_drone_nozzle_outline.py','--model',out/'candidate.FCStd','--output',out/'outline-check.json'])]
 for f in fs:f.result()
for name,i,crop in [('left',3,[210,510,510,700]),('back',4,[325,510,625,700]),('right',5,[475,510,775,700])]:
 run('detail-'+name,[py,'tools/compare_drone_side_detail.py','--before',b/'iteration-86-renders','--after',out/'video-renders','--comparison',out/'video','--output',out/f'detail-{name}.png','--view-index',i,'--crop',*crop,'--display-scale',2])
print('fixed-camera candidate review done',flush=True)
