import os,subprocess,concurrent.futures
from pathlib import Path
os.chdir('/Users/miclle/github/miclle/vintrox');b='cad/drone-concept/comparison/';study=b+'nozzle-interior-study/'
py='/Applications/FreeCAD.app/Contents/Resources/bin/python';bl='/Applications/Blender.app/Contents/MacOS/Blender';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='/Applications/FreeCAD.app/Contents/Resources/lib')
def run(name,cmd):
 with open('/tmp/vintrox-interior-'+name+'.log','w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
 print(name,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(name)
def job(name,kind):
 trial=study+name+'/';ids=kind=='ids';camera=b+('stills-52/cameras.json' if kind=='still' else 'cameras.json');out=trial+(kind if ids else kind+'-renders')
 if not(name=='bowl' and kind=='still'):
  run(name+'-'+kind,[bl,'--background','--threads','4','--python-exit-code','1','--python','tools/'+('render_drone_object_ids.py' if ids else 'render_drone_concept.py'),'--','--meshes',trial+'meshes.json','--model',trial+'candidate.FCStd','--output',out,'--cameras' if ids else '--comparison',camera])
 if not ids:run(name+'-'+kind+'-compare',[py,'tools/compare_drone_reference.py','--renders',out,'--output',trial+kind+'-comparison','--cameras',camera])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 fs=[pool.submit(job,name,kind) for name in ['bowl','recessed'] for kind in ['video','still','ids']]
 for f in fs:f.result()
