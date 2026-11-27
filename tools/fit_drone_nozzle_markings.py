"""Fit curved marking masks to fixed rear-video observations; camera stays fixed."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project
root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison';out=folder/'nozzle-marking-study'
# Plaque points follow unoccluded straight edges; bright rightmost edge at 150 is excluded.
OBS=[{'source_frame':90,'triangle':[[334,397],[294,448],[344,456]],'plaque':[[283,466],[310,469],[338,472],[273,484],[281,500],[310,503],[338,506],[354,489]]},
 {'source_frame':120,'triangle':[[474,402],[443,459],[506,460]],'plaque':[[432,477],[470,477],[510,477],[525,495],[510,514],[470,514],[432,514],[421,495]]},
 {'source_frame':150,'triangle':[[611,398],[603,453],[653,447]],'plaque':[[598,474],[625,470],[650,467],[596,490],[607,506],[635,502],[663,499]]}]

def boundary(p,kind,n=200):
 x,z,w,h=p
 if kind=='triangle':return np.array([[x,z],[x+w/2,z+h],[x-w/2,z+h]]) # reversed world X in back view
 u=np.linspace(0,1,n)
 return np.r_[np.column_stack([x-w/2+u*w,np.full(n,z)]),np.column_stack([np.full(n,x+w/2),z+u*h]),np.column_stack([x+w/2-u*w,np.full(n,z+h)]),np.column_stack([np.full(n,x-w/2),z+h-u*h])]

def main():
 surface=json.loads((out/'surface-grid.json').read_text());ys=np.array(surface['front_y_mm'],dtype=float);assert np.isfinite(ys).all()
 interp=RegularGridInterpolator((surface['x_mm'],surface['z_mm']),ys,bounds_error=True)
 # FreeCAD minimal rotation from +Z to the fixed rear-down axis: X rotates ~145 degrees.
 axis=np.array(surface['frame_axis']);c=axis[2];s=-axis[1];rot=np.array([[1,0,0],[0,c,-s],[0,s,c]])
 cameras=json.loads((folder/'cameras.json').read_text())
 def pixels(p,kind,frame):
  xz=boundary(p,kind);local=np.c_[xz[:,0],interp(xz)-.65,xz[:,1]];world=local@rot.T+surface['frame_origin_mm'];return project(world,frame,cameras)
 result=[]
 for kind,initial,bounds in [('triangle',[0,34,28,25],([-5,20,20,15],[5,55,38,35])),('plaque',[0,70,44,15],([-5,55,30,10],[5,75,58,22]))]:
  def residual(p,rows=OBS):
   values=[]
   for o in rows:
    pred=pixels(p,kind,o['source_frame']);ref=np.array(o[kind]);values.extend((pred-ref).ravel() if kind=='triangle' else cKDTree(pred).query(ref)[0])
   return np.array(values)
  fit=least_squares(residual,initial,bounds=bounds,diff_step=1e-5,max_nfev=1500,x_scale='jac')
  rows=[]
  for o in OBS:
   pred=pixels(fit.x,kind,o['source_frame']);ref=np.array(o[kind]);dist=np.linalg.norm(pred-ref,axis=1) if kind=='triangle' else cKDTree(pred).query(ref)[0]
   rows.append({'source_frame':o['source_frame'],'reference_px':o[kind],'distance_px':dist.tolist(),'projected_boundary_px':pred.tolist() if kind=='triangle' else pred[::20].tolist()})
  loo=[]
  for i,o in enumerate(OBS):
   f=least_squares(lambda p:residual(p,OBS[:i]+OBS[i+1:]),fit.x,bounds=bounds,diff_step=1e-5,max_nfev=1000,x_scale='jac');pred=pixels(f.x,kind,o['source_frame']);ref=np.array(o[kind]);dist=np.linalg.norm(pred-ref,axis=1) if kind=='triangle' else cKDTree(pred).query(ref)[0];loo.append({'held_out_frame':o['source_frame'],'parameters':f.x.tolist(),'rms_px':float(np.sqrt(np.mean(dist**2)))})
  dist=np.concatenate([r['distance_px'] for r in rows]);result.append({'kind':kind,'parameter_names':['center_x_mm','top_station_mm','width_mm','height_mm'],'parameters':fit.x.tolist(),'rms_px':float(np.sqrt(np.mean(dist**2))),'max_px':float(max(dist)),'views':rows,'leave_one_view_out':loo})
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'baseline_fcstd_sha256':surface['fcstd_sha256'],'fit_script_sha256':sha(Path(__file__)),'surface_grid_sha256':sha(out/'surface-grid.json'),'camera_sha256':sha(folder/'cameras.json'),'video_sha256':cameras['reference_video_sha256'],'fits':result,'limitations':['Manual low-resolution boundary points, roughly 2-4px uncertainty.','Plaque sample points deliberately omit bright/occluded right edge in frame150.','Fit assumes masks in local XZ plane projected onto curved shell; no camera fit.','Surface grid interpolation and 0.65mm offset are fitting approximations, saved CAD must be checked independently.','Leave-one-view-out is sensitivity, not reconstruction uniqueness or manufacturing acceptance.']};(out/'fit.json').write_text(json.dumps(report,indent=2)+'\n');(out/'observations.json').write_text(json.dumps(OBS,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['kind','parameters','rms_px','max_px']} for r in result]))
if __name__=='__main__':main()
