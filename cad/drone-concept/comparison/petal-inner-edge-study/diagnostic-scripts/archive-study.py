from pathlib import Path
import json,hashlib,re,shutil
from PIL import Image
root=Path(__file__).resolve().parents[5];b=root/'cad/drone-concept/comparison';s=b/'petal-inner-edge-study';cache=Path('/Users/miclle/.codex/visualizations/2026/10/22/01a163d7-dc98-7ce1-af6b-9aa3d7bf5546/drone-petal-inner-edge-cache');cache.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();entries=[]
review=json.loads((s/'review.json').read_text());assert review['passed'] and review['formal_model_unchanged'];assert sha(b.parent/'vintrox-drone-concept.FCStd')==review['baseline_fcstd_sha256']
for name in ['bevel065','return15']:
 check=json.loads((s/name/'candidate-check.json').read_text());assert check['script_sha256']==sha(s/name/'source-experiment_drone_petal_inner_edge.py') and check['source_sha256']==sha(s/name/'source-drone_petal_inner_edge.py')
 for kind in ['video','stills']:
  render=json.loads((s/name/(kind+'-renders')/'render-manifest.json').read_text());compare=json.loads((s/name/kind/'comparison-report.json').read_text());assert render['fcstd_sha256']==compare['fcstd_sha256']==check['fcstd_sha256'];assert render['camera_config_sha256']==compare['camera_config_sha256'];assert compare['render_manifest_sha256']==sha(s/name/(kind+'-renders')/'render-manifest.json')
 src=s/name/'meshes.json';dest=cache/(name+'-meshes.json');h=sha(src);shutil.move(src,dest);assert sha(dest)==h;entries.append({'role':name,'path':str(dest),'sha256':h})
 for p in (s/name).glob('detail-*.json'):
  d=json.loads(p.read_text());assert d['fcstd_sha256']==check['fcstd_sha256'] and sha(root/d['image_path'])==d['image_sha256']
  for f in d['source_files']:assert sha(root/f['path'])==f['sha256']
pngs=list(s.rglob('*.png'))
for p in pngs:
 with Image.open(p) as im:im.verify()
sources=list((s/'diagnostic-scripts').glob('*.py'))+[root/'tools/drone_petal_inner_edge.py',root/'tools/experiment_drone_petal_inner_edge.py']
for p in sources:compile(p.read_text(),str(p),'exec')
for f in ['/tmp/vintrox-inner-edge065.log','/tmp/vintrox-inner-return15.log','/tmp/vintrox-inner-edge-verify.log']:
 p=Path(f)
 if p.exists():shutil.copy2(p,cache/p.name)
(s/'mesh-cache.json').write_text(json.dumps({'mesh_files':entries,'baseline_checkpoint':str(cache.parent/'drone-nozzle-marking-cache/checkpoint-v52/checkpoint.json'),'baseline_render_meshes':str(cache.parent/'drone-nozzle-marking-cache/formal/render-meshes.json'),'execution_logs':str(cache),'reproduction':'Restore candidate meshes.json from matching hashed cache. Frozen source files preserve generated candidate provenance.'},indent=2)+'\n')
for p in [s/'README.md',root/'docs/drone-concept.md',root/'docs/drone-overlay-comparison.md',root/'docs/validation.md',root/'docs/roadmap.md',b/'README.md']:
 missing=[x for x in re.findall(r'\]\(([^)]+)\)',p.read_text()) if not x.startswith(('http:','https:','#','mailto:')) and not (p.parent/x.split('#')[0]).exists()];assert not missing,(p,missing)
delivery=json.loads((b.parent/'delivery-verification.json').read_text());assert delivery['passed'] and delivery['fcstd_sha256']==review['baseline_fcstd_sha256']
(s/'study-validation.json').write_text(json.dumps({'passed':True,'formal_fcstd_sha256':review['baseline_fcstd_sha256'],'formal_delivery_unchanged':True,'candidate_count':2,'verified_pngs':len(pngs),'compiled_scripts':len(sources),'source_and_render_bindings_verified':True,'detail_input_hashes_verified':True,'mesh_cache_hashes_verified':True,'markdown_links_verified':True,'adopted_candidates':[],'visual_goal_met':False},indent=2)+'\n');print('Two-candidate study verified and archived',len(pngs),'PNGs')
