import sys, json
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
import FreeCAD as App
base,donor,out=map(Path,sys.argv[1:])
a,b=[App.openDocument(str(p.resolve())) for p in (base,donor)]
import re
for obj in a.Objects:
    m=re.fullmatch(r'NozzlePetal(?:EdgeRail|EndHem|Inset|Ridge|Guide|Hinge)?(\d+)(?:_\d+)?',obj.Name)
    if m and int(m[1]) in {0,4,5,11}:
        obj.Shape=b.getObject(obj.Name).Shape.copy()
a.recompute()
tmp=out.with_suffix('.headless.FCStd')
a.saveAs(str(tmp))
App.closeDocument(a.Name)
App.closeDocument(b.Name)
with ZipFile(tmp) as saved, ZipFile(base) as appearance, ZipFile(out,'x',ZIP_DEFLATED) as z:
    for n in saved.namelist():
        if n!='GuiDocument.xml' and not n.startswith(('ShapeAppearance','LineColorArray','PointColorArray')):
            z.writestr(n,saved.read(n))
    for n in appearance.namelist():
        if n=='GuiDocument.xml' or n.startswith(('ShapeAppearance','LineColorArray','PointColorArray')):
            z.writestr(n,appearance.read(n))
tmp.unlink()
