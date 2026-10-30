"""Create an exploratory saved-CAD candidate with narrower rear nozzle petals.

The transform acts in each saved nozzle-local frame and preserves the root band.
It is a geometry candidate only; rendering and fixed-camera comparison decide
whether the change is retained.
"""
import argparse, hashlib, json
from pathlib import Path
import FreeCAD as App
from drone_concept import contract_nozzle_petal_tangential


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-model',type=Path,required=True)
    p.add_argument('--base-meshes',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--factor',type=float,required=True)
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()): raise ValueError('Use a new empty candidate directory')
    mesh=json.loads(a.base_meshes.read_text())
    base_hash=digest(a.base_model)
    if mesh.get('fcstd_sha256')!=base_hash: raise ValueError('Baseline model/mesh hash mismatch')
    a.output.mkdir(parents=True,exist_ok=True)
    d=App.openDocument(str(a.base_model))
    changed=[]; original={}
    try:
        for item in mesh['objects']:
            n=item['name']
            if n.startswith('NozzlePetal') or n.startswith('NozzlePetalHinge'):
                o=d.getObject(n)
                if o is None: raise ValueError('Missing '+n)
                original[n]=o.Shape.copy()
                index=int(''.join(c for c in n.split('NozzlePetal',1)[1] if c.isdigit()) or 0)
                # Handle suffixes such as NozzlePetalHinge10 and NozzlePetalRidge10.
                if 'Hinge' in n:
                    index=int(n[len('NozzlePetalHinge'):])
                else:
                    tail=n.split('NozzlePetal',1)[1]
                    index=int(''.join(c for c in tail if c.isdigit()) or 0)
                o.Shape=contract_nozzle_petal_tangential(o.Shape,index,factor=a.factor,preserve_root=True)
                if not o.Shape.isValid() or not o.Shape.Solids: raise ValueError('Invalid '+n)
                changed.append(n)
        d.recompute(); model=a.output/'candidate.FCStd'; d.saveAs(str(model))
    finally: App.closeDocument(d.Name)
    # Re-open, tessellate the candidate and verify protected supports exactly.
    d=App.openDocument(str(model)); base=App.openDocument(str(a.base_model))
    try:
        for n,old in original.items():
            if not d.getObject(n).Shape.isValid(): raise ValueError('Invalid saved '+n)
        for n in ['SupportShaftFrontLeft','SupportShaftRearLeft','SupportShaftFrontRight','SupportShaftRearRight','SupportFootFrontLeft','SupportFootRearLeft','SupportFootFrontRight','SupportFootRearRight']:
            a1=d.getObject(n).Shape; a2=base.getObject(n).Shape
            if a1.cut(a2).Volume+a2.cut(a1).Volume>1e-6: raise ValueError('Protected support changed '+n)
        for item in mesh['objects']:
            o=d.getObject(item['name'])
            if o is None: raise ValueError('Missing saved '+item['name'])
            if item['name'] in changed:
                verts,faces=o.Shape.tessellate(.12)
                item['vertices']=[list(v) for v in verts]; item['faces']=faces
        mesh['fcstd_sha256']=digest(model)
        (a.output/'meshes.json').write_text(json.dumps(mesh))
        check={'base_fcstd_sha256':base_hash,'fcstd_sha256':mesh['fcstd_sha256'],
               'tangential_factor':a.factor,'changed_objects':changed,
               'protected_supports_unchanged':True,
               'status':'exploratory; fixed-camera review pending'}
        (a.output/'candidate-check.json').write_text(json.dumps(check,indent=2)+'\n')
        print(model)
    finally:
        App.closeDocument(d.Name); App.closeDocument(base.Name)

if __name__=='__main__': main()
