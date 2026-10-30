from pathlib import Path
import sys
sys.path.insert(0,str(Path('tools').resolve()))
import FreeCAD as App
from drone_nozzle_interior import interior_parts,loft
from drone_nozzle_root_profile import root_sections
parts=interior_parts(True)
rows=root_sections([(96.8067,48.8215,-1.149,0),(104,47.35,.05,-1),(112,44.7666666667,1.4,-2)],1)
outer=loft([(z,r-.1,dy,t) for z,r,dy,t in rows],True);inner=loft([(z,r-2.6,dy,t) for z,r,dy,t in rows],True);parts['RuledThroat']=outer.cut(inner)
for n in ['BassInnerThroat','RuledThroat']:
 s=parts[n];print(n,s.Volume,s.isValid(),s.Orientation,[(p,s.isInside(App.Vector(*p),1e-5,False)) for p in [(0,0,0),(0,0,100),(1000,1000,1000),(47,5,100)]],flush=True);print('cone intersection',s.common(parts['BassVisualCone']).Volume,flush=True)
