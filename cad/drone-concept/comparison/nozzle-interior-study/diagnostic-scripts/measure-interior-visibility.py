from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
b=Path('cad/drone-concept/comparison');s=b/'nozzle-interior-study';old=b/'object-ids-v47';meta=json.load(open(old/'object-id-manifest.json'));oldrgb={o['name']:o['rgb'] for o in meta['objects']};names=['BassVisualCone','BassDustCap','BassInnerThroat'];reports=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for candidate in ['bowl','recessed']:
 new=s/candidate/'ids';metadata=json.load(open(new/'object-id-manifest.json'));rgb={o['name']:o['rgb'] for o in metadata['objects']};rows=[]
 assert metadata['camera_config_sha256']==meta['camera_config_sha256']
 for view in ['video-02','video-03','video-04','video-05','video-06']:
  before=np.asarray(Image.open(old/(view+'.png')).convert('RGB'));after=np.asarray(Image.open(new/(view+'.png')).convert('RGB'))
  formerly_inner=np.zeros(before.shape[:2],bool)
  for n in names:formerly_inner|=np.all(before==oldrgb[n],axis=2)
  exposed=np.zeros(before.shape[:2],bool)
  for i in range(12):exposed|=np.all(after==rgb[f'NozzlePetal{i}'],axis=2)
  rows.append({'view':view,'baseline_interior_pixels':int(formerly_inner.sum()),'new_primary_leaf_pixels_in_baseline_interior':int((formerly_inner & exposed).sum()),'interior_object_visibility':[{'name':n,'before_pixels':int(np.all(before==oldrgb[n],axis=2).sum()),'after_pixels':int(np.all(after==rgb[n],axis=2).sum())} for n in names]})
 reports.append({'candidate':candidate,'fcstd_sha256':metadata['fcstd_sha256'],'id_manifest_sha256':sha(new/'object-id-manifest.json'),'views':rows})
report={'baseline_fcstd_sha256':meta['fcstd_sha256'],'baseline_id_manifest_sha256':sha(old/'object-id-manifest.json'),'camera_sha256':meta['camera_config_sha256'],'candidates':reports,'method':'count primary-leaf object IDs within baseline inner-part pixel mask using identical cameras','limitations':['Visibility attribution, not reference similarity or shape accuracy.','Reference shadow is not segmented as an opaque cap.']};(s/'interior-visibility.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(reports))
