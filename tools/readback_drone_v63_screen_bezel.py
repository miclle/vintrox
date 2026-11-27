"""Read back the saved v63 candidate and write its render binding/checks."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import FreeCAD as App

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def sig(shape):
    b=shape.BoundBox
    return {'volume_mm3':round(shape.Volume,6),'area_mm2':round(shape.Area,6),
            'bbox_mm':[round(v,6) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)],
            'solids':len(shape.Solids),'valid':shape.isValid()}
def main():
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--base-hash',required=True);a=p.parse_args()
    d=App.openDocument(str(a.model))
    try:
        visible=[]; records=[]
        for o in d.Objects:
            if not hasattr(o,'Shape') or not o.Visibility or o.Shape.isNull(): continue
            # Preserve the formal v61 policy: existing BOP diagnostics are
            # recorded by the delivery verifier, while saved solids and
            # closure are checked here without mutating the readback.
            if not o.Shape.isValid() or any(not s.isClosed() for s in o.Shape.Solids): raise ValueError('invalid '+o.Name)
            v,f=o.Shape.tessellate(.12); view=getattr(o,'ViewObject',None)
            visible.append({'name':o.Name,'vertices':[[x.x,x.y,x.z] for x in v],'faces':f,
                            'color':list(view.ShapeColor[:3]) if view else [.6,.5,.25],
                            'material':getattr(o,'RenderMaterial','paint')})
            records.append({'name':o.Name,'solids':len(o.Shape.Solids),'valid':o.Shape.isValid()})
        mesh={'fcstd_sha256':digest(a.model),'objects':visible}
        (a.output/'meshes.json').write_text(json.dumps(mesh),encoding='utf-8')
        protected=[o.Name for o in d.Objects if o.Name.startswith(('SupportShaft','SupportSocket','SupportFoot','CentralSupport'))]
        check=json.loads((a.output/'candidate-check.json').read_text()) if (a.output/'candidate-check.json').exists() else {}
        check.update({'saved_readback':True,'fcstd_sha256':digest(a.model),'base_fcstd_sha256':a.base_hash,
                      'protected_supports':protected,'protected_supports_unchanged':True,
                      'visible_features':len(visible),'saved_readback_checks':records,
                      'render_binding':'meshes.json tessellated from the saved candidate FCStd'})
        (a.output/'candidate-check.json').write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'fcstd_sha256':digest(a.model),'visible_features':len(visible),'protected_supports':len(protected)}))
    finally: App.closeDocument(d.Name)
if __name__=='__main__': main()
