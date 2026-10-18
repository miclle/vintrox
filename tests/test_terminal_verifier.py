"""Geometric counterexamples for the modular-terminal STEP matcher."""
from pathlib import Path
from types import SimpleNamespace
import sys
import csv
import hashlib
import shutil
import tempfile
import unittest
import FreeCAD as App
import Part
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import terminal_model as model
from verify_terminal import compare_step_geometry, verify_csv_manifest, readback


def source(name,shape):return SimpleNamespace(Name=name,Shape=shape)


class TerminalMatcherTests(unittest.TestCase):
    def setUp(self):
        self.a=Part.makeBox(10,10,10).cut(Part.makeCylinder(1,10,App.Vector(3,5,0)))
        self.b=Part.makeBox(10,10,10).cut(Part.makeCylinder(1,10,App.Vector(7,5,0)))

    def test_order_is_irrelevant(self):
        result=compare_step_geometry([source('a',self.a),source('b',self.b)],Part.makeCompound([self.b,self.a]))
        self.assertEqual(result['matched_solids'],2)

    def test_translation_rejected(self):
        moved=self.a.copy();moved.translate(App.Vector(.1,0,0))
        with self.assertRaises(ValueError):compare_step_geometry([source('a',self.a)],moved)

    def test_same_volume_same_bounds_wrong_shape_rejected(self):
        self.assertAlmostEqual(self.a.Volume,self.b.Volume,places=6)
        with self.assertRaises(ValueError):compare_step_geometry([source('a',self.a)],self.b)

    def test_duplicate_cannot_replace_missing_solid(self):
        duplicate=Part.makeBox(10,10,10).cut(Part.makeCylinder(1,10,App.Vector(3,5,0)))
        compound=Part.makeCompound([self.a,duplicate])
        self.assertEqual(len(compound.Solids),2)
        with self.assertRaises(ValueError):compare_step_geometry([source('a',self.a),source('b',self.b)],compound)


class CsvManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='vintrox-csv-test-')
        self.addCleanup(self.temporary.cleanup)
        self.path=Path(self.temporary.name)/'parts.csv'
        self.records=[{'id':'P01','name':'Shell','label':'外壳','print_bounds_mm':[10.,20.,3.]},
                      {'id':'P02','name':'Plate','label':'托板','print_bounds_mm':[15.,7.,2.]}]
        self.fields=['ID','Name','Label','X_mm','Y_mm','Z_mm','Status']
        self.rows=[['P01','Shell','外壳','10','20.000','3','ASSUMED / UNTESTED'],
                   ['P02','Plate','托板','15','7','2','ASSUMED / UNTESTED']]

    def write(self,rows,fields=None):
        with self.path.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(self.fields if fields is None else fields);writer.writerows(rows)

    def test_valid_numeric_formats_and_chinese_labels(self):
        self.write(self.rows)
        self.assertEqual(verify_csv_manifest(self.path,self.records)['matched_parts'],2)

    def test_corrupt_rows_rejected(self):
        for case in ('missing','extra','duplicate','reordered','dimension','nonfinite','name','label','status','extra_column'):
            with self.subTest(case=case):
                rows=[row.copy() for row in self.rows]
                if case=='missing':rows.pop()
                elif case=='extra':rows.append(rows[0].copy())
                elif case=='duplicate':rows[1]=rows[0].copy()
                elif case=='reordered':rows.reverse()
                elif case=='dimension':rows[0][3]='99'
                elif case=='nonfinite':rows[0][3]='nan'
                elif case=='name':rows[0][1]='OldShell'
                elif case=='label':rows[0][2]='旧标签'
                elif case=='status':rows[0][6]='VERIFIED'
                elif case=='extra_column':rows[0].append('unexpected')
                self.write(rows)
                with self.assertRaisesRegex(ValueError,'CSV manifest'):verify_csv_manifest(self.path,self.records)

    def test_wrong_header_rejected(self):
        self.write(self.rows,self.fields[:-1])
        with self.assertRaisesRegex(ValueError,'CSV manifest header'):verify_csv_manifest(self.path,self.records)

    def test_readback_rejects_corrupt_csv_without_writing(self):
        root=Path(__file__).resolve().parents[1]
        fixture=Path(self.temporary.name)/'readback';out=fixture/'cad/terminal';out.mkdir(parents=True)
        for name in ('vintrox-terminal.FCStd','vintrox-terminal.step','parts.json','parts.csv'):
            shutil.copyfile(root/'cad/terminal'/name,out/name)
        with (out/'parts.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.reader(stream))
        rows[1][3]='999'
        with (out/'parts.csv').open('w',encoding='utf-8',newline='') as stream:csv.writer(stream).writerows(rows)
        before={p.name:p.read_bytes() for p in out.iterdir()}
        with self.assertRaisesRegex(ValueError,'CSV manifest dimensions'):readback(fixture)
        self.assertEqual({p.name:p.read_bytes() for p in out.iterdir()},before)


class HardwareBoundsTests(unittest.TestCase):
    def setUp(self):
        self.path=Path(__file__).resolve().parents[1]/'cad/terminal/vintrox-terminal.FCStd'
        self.original=hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.doc=App.openDocument(str(self.path));self.doc.recompute()
        self.addCleanup(self.close_document)

    def close_document(self):
        App.closeDocument(self.doc.Name)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),self.original)

    def test_shared_validation_rejects_all_six_body_boundaries(self):
        pi=self.doc.Pi
        for axis in 'xyz':pi.setExpression('Placement.Base.'+axis,None)
        baseline=pi.Placement.Base
        limits=(float(self.doc.Parameters.Width),float(self.doc.Parameters.Depth),float(self.doc.Parameters.Height))
        for index,axis in enumerate('XYZ'):
            for value in (-100,limits[index]+10):
                with self.subTest(axis=axis,value=value):
                    coords=list(baseline);coords[index]=value;pi.Placement.Base=App.Vector(*coords);self.doc.recompute()
                    result=model.validate(self.doc)
                    self.assertIn('硬件超出机身边界',result['errors'])
                    self.assertIn('Pi',[entry['name'] for entry in result['hardware_outside_body']])

    def test_refresh_rejects_high_pi_before_overwriting_exports(self):
        p=self.doc.Parameters;p.set(p.getCellFromAlias('PiZ'),'250');self.doc.recompute()
        with tempfile.TemporaryDirectory(prefix='vintrox-refresh-guard-') as directory:
            root=Path(directory);out=root/'cad/terminal';out.mkdir(parents=True)
            for name in ('vintrox-terminal.FCStd','vintrox-terminal.step','parts.csv','terminal-validation.json'):
                (out/name).write_bytes(b'preserve existing export')
            before={q.relative_to(root):q.read_bytes() for q in root.rglob('*') if q.is_file()}
            with self.assertRaisesRegex(RuntimeError,'硬件超出机身边界'):model.refresh(self.doc,root)
            self.assertEqual({q.relative_to(root):q.read_bytes() for q in root.rglob('*') if q.is_file()},before)


if __name__=='__main__':unittest.main()
