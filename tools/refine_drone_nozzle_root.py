"""Transfer checked v47 BReps, retaining untouched payloads and v46 GUI state.

Run with FreeCAD Python. Candidate document and element-map metadata stay intact.
Unchanged BReps and GUI data come verbatim from the bound v46 checkpoint. Open
the merged archive independently and export STEP without headlessly re-saving it.
"""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import FreeCAD as App
import Import
import Part


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def shape_files(archive):
    result={}
    for obj in ET.fromstring(archive.read('Document.xml')).findall('./ObjectData/Object'):
        part=obj.find("./Properties/Property[@name='Shape']/Part")
        if part is not None:result[obj.get('name')]=part.get('file')
    return result


def main():
    p=argparse.ArgumentParser()
    for name in ['baseline','manifest','base-meshes','candidate','candidate-check','candidate-meshes','output']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();baseline_hash='475c208851231c3c98da53e59c62ad1a18de1bf969f6d0622db8e5f93b03b7e5'
    manifest=json.loads(a.manifest.read_text());base_mesh=json.loads(a.base_meshes.read_text())
    check=json.loads(a.candidate_check.read_text());meshes=json.loads(a.candidate_meshes.read_text())
    if digest(a.baseline)!=baseline_hash or manifest['fcstd_sha256']!=baseline_hash or base_mesh['fcstd_sha256']!=baseline_hash:
        raise ValueError('Expected the verified v46 baseline')
    if check['baseline_fcstd_sha256']!=baseline_hash or digest(a.candidate)!=check['fcstd_sha256'] or meshes['fcstd_sha256']!=check['fcstd_sha256']:
        raise ValueError('Candidate hash mismatch')
    from drone_nozzle_root_profile import root_shifted_leaf_parts, root_shifted_inner_parts, root_shifted_rolls, root_shifted_fairing, ROOT_DELTA, shifted_z
    expected={'RearCyanLowerLeft','RearCyanLowerRight'} | set(root_shifted_inner_parts()) | set(root_shifted_rolls()) | set(root_shifted_fairing())
    for i in range(12): expected.update(root_shifted_leaf_parts(i))
    if set(check['changed_objects'])!=expected:
        raise ValueError('Expected checked nozzle petal hardware candidate')
    changed=set(check['changed_objects']);old={o['name']:o for o in base_mesh['objects']};new={o['name']:o for o in meshes['objects']}
    if len(changed)!=126 or old.keys()!=new.keys() or {n for n in old if old[n]!=new[n]}!=changed:
        raise ValueError('Unexpected mesh/appearance change scope')
    a.output.mkdir(parents=True,exist_ok=True);model=a.output/'vintrox-drone-concept.FCStd';records=[]
    with ZipFile(a.baseline) as base,ZipFile(a.candidate) as candidate:
        old_files=shape_files(base);new_files=shape_files(candidate)
        if old_files.keys()!=new_files.keys():raise ValueError('Candidate object set changed')
        replacements={new_files[n]:base.read(old_files[n]) for n in old_files if n not in changed}
        gui=base.read('GuiDocument.xml');gui_files={n.get('file') for n in ET.fromstring(gui).iter() if n.get('file')}
        replacements['GuiDocument.xml']=gui
        replacements.update({name:base.read(name) for name in gui_files})
        # Candidate maps retain the same BRep-local indices for unchanged parts;
        # retain its complete StringHasher and all element-map metadata together.
        temporary=model.with_suffix('.transfer.tmp')
        with ZipFile(temporary,'w',ZIP_DEFLATED) as out:
            for name in candidate.namelist():out.writestr(name,replacements.pop(name,candidate.read(name)))
            for name,data in replacements.items():out.writestr(name,data)
        temporary.replace(model)
        with ZipFile(model) as saved:
            assert saved.read('GuiDocument.xml')==gui
            for name in old_files:
                expected=candidate.read(new_files[name]) if name in changed else base.read(old_files[name])
                payload=saved.read(new_files[name]);assert payload==expected
                records.append({'name':name,'changed':name in changed,'source':'candidate' if name in changed else 'v46',
                                'payload_sha256':hashlib.sha256(payload).hexdigest(),'exact_payload_match':True})
    doc=App.openDocument(str(model))
    try:
        for name in changed:
            shape=doc.getObject(name).Shape;shape.check(True)
            if not shape.isValid() or not all(s.isClosed() for s in shape.Solids):raise ValueError(name)
        visible=[doc.getObject(o['name']) for o in meshes['objects']]
        Import.export(visible,str(a.output/'vintrox-drone-concept.step'))
        bbox=Part.makeCompound([o.Shape for o in visible]).optimalBoundingBox(False,False)
        manifest.update(revision='v47-coordinated-nozzle-root',fcstd_sha256=digest(model),
                        bbox_mm=[bbox.XLength,bbox.YLength,bbox.ZLength],bbox_min_mm=[bbox.XMin,bbox.YMin,bbox.ZMin],bbox_max_mm=[bbox.XMax,bbox.YMax,bbox.ZMax])
        for key in ['bass_warning_label_local_mm','bass_alert_local_mm']:manifest[key]=meshes[key]
        manifest['petal_recess_stations_mm']=[shifted_z(99.5,1),shifted_z(127,1)]
        lip=manifest['nozzle_lip_parameters_mm']
        for key in ['gold_major_radius','metal_major_radius','gasket_outer_radius']:lip[key]+=ROOT_DELTA[1]
        for key in ['gold_station','metal_station']:lip[key]+=ROOT_DELTA[0]
        manifest['nozzle_root_profile']={'local_delta_z_radius_y_tilt':list(ROOT_DELTA),'guide_span_degrees':5.4,'terminal_circle_preserved':True,'basis':'five fixed video views; manual root centreline observations'}
        for entry in manifest['features']:
            obj=doc.getObject(entry['name']);entry.update(solids=len(obj.Shape.Solids),valid=obj.Shape.isValid())
        (a.output/'concept-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        meshes['fcstd_sha256']=manifest['fcstd_sha256']
        (a.output/'render-meshes.json').write_text(json.dumps(meshes))
        report={'fcstd_sha256':digest(model),'baseline_fcstd_sha256':baseline_hash,'candidate_fcstd_sha256':digest(a.candidate),
                'gui_document_preserved_exactly':True,'shape_payloads':records,'changed_count':len(changed),
                'unchanged_shape_payloads':len(records)-len(changed),'mesh_records_preserved_outside_changed_set':True,
                'method':'candidate document/maps; unchanged BReps and GUI data retained verbatim from v46; independent FreeCAD read and STEP export',
                'passed':True}
        (a.output/'comparison').mkdir(exist_ok=True)
        (a.output/'comparison/archive-transfer.json').write_text(json.dumps(report,indent=2)+'\n')
        print(manifest['fcstd_sha256'],flush=True)
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
