"""FreeCAD regressions using temporary copies of the saved layout package."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import verify_layout as verifier


class LayoutGeometryTests(unittest.TestCase):
    def setUp(self):
        self.original_documents = set(App.listDocuments())
        self.addCleanup(self.close_test_documents)

    def close_test_documents(self):
        for name in set(App.listDocuments()) - self.original_documents:
            App.closeDocument(name)

    def feature(self, doc, name, shape):
        obj = doc.addObject('Part::Feature', name)
        obj.Shape = shape
        return obj

    def test_equal_volume_and_bounds_do_not_hide_shape_changes(self):
        doc = App.newDocument('LayoutShapeRegression')
        box = Part.makeBox(10, 10, 10)
        left = box.cut(Part.makeCylinder(1, 10, App.Vector(3, 5, 0)))
        right = box.cut(Part.makeCylinder(1, 10, App.Vector(7, 5, 0)))
        self.assertAlmostEqual(left.Volume, right.Volume)
        for key in ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax'):
            self.assertAlmostEqual(getattr(left.BoundBox, key), getattr(right.BoundBox, key))
        obj = self.feature(doc, 'Reference', left)
        with self.assertRaisesRegex(ValueError, 'STEP geometry mismatch'):
            verifier.compare_step_geometry([obj], right)

    def test_step_solid_order_is_irrelevant(self):
        doc = App.newDocument('LayoutOrderRegression')
        first = self.feature(doc, 'First', Part.makeBox(10, 10, 10))
        second = self.feature(doc, 'Second', Part.makeBox(10, 10, 10, App.Vector(20, 0, 0)))
        step = Part.makeCompound([second.Shape, first.Shape])
        result = verifier.compare_step_geometry([first, second], step)
        self.assertEqual(result['matched_solids'], 2)

    def test_step_cannot_reuse_a_duplicate_solid(self):
        doc = App.newDocument('LayoutDuplicateRegression')
        first = self.feature(doc, 'First', Part.makeBox(10, 10, 10))
        second = self.feature(doc, 'Second', Part.makeBox(10, 10, 10, App.Vector(20, 0, 0)))
        # Use fresh topology so OCC retains both coincident solids.
        step = Part.makeCompound([first.Shape, Part.makeBox(10, 10, 10)])
        self.assertEqual(len(step.Solids), 2)
        with self.assertRaisesRegex(ValueError, 'STEP geometry mismatch'):
            verifier.compare_step_geometry([first, second], step)


@unittest.skipUnless(
    all((ROOT/'cad'/name).is_file() for name in
        ('vintrox-layout.FCStd', 'vintrox-layout.step', 'layout-validation.json')),
    'Saved-layout integration tests require the local cad/ package; see docs/layout-verification.md',
)
class SavedLayoutVerifierTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='vintrox-verifier-test-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT/'tools', self.root/'tools',
                        ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT/'cad', self.root/'cad')
        self.original = {
            p.relative_to(self.root): p.read_bytes()
            for p in (self.root/'cad').rglob('*') if p.is_file()
        }
        self.report = self.root/'cad/layout-validation.json'
        self.expected_solids = json.loads(self.report.read_text())['physical_objects']
        self.original_documents = set(App.listDocuments())
        self.addCleanup(self.close_test_documents)

    def close_test_documents(self):
        for name in set(App.listDocuments()) - self.original_documents:
            App.closeDocument(name)

    def run_cli(self, *arguments):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        return subprocess.run(
            [sys.executable, str(self.root/'tools/verify_layout.py'), *arguments],
            cwd=self.root, env=environment, capture_output=True, text=True,
            timeout=90,
        )

    def assert_assets_unchanged(self, except_report=False):
        for name, data in self.original.items():
            if except_report and name == Path('cad/layout-validation.json'):
                continue
            self.assertEqual((self.root/name).read_bytes(), data, str(name))

    def test_default_cli_preserves_complete_report_and_cad(self):
        self.assertTrue(json.loads(self.report.read_text())['saved_readback']['parametric_checks'])
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(result.stdout)
        self.assertFalse(current['saved_readback']['parametric_exercise_executed'])
        self.assertEqual(current['saved_readback']['step_geometry_comparison']['matched_solids'], self.expected_solids)
        self.assert_assets_unchanged()

    def test_explicit_exercise_output_survives_later_default_check(self):
        result = self.run_cli('--exercise', '--output', 'cad/layout-validation.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = self.report.read_bytes()
        report = json.loads(evidence)
        self.assertTrue(report['saved_readback']['parametric_exercise_executed'])
        self.assertTrue(report['saved_readback']['parametric_checks'])
        self.assertEqual(len(report['saved_readback']['fixed_layout_depth_probes']), 4)
        self.assertIn('revision_comparison', report)
        self.assertEqual(report['saved_readback']['step_geometry_comparison']['matched_solids'], self.expected_solids)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.report.read_bytes(), evidence)
        self.assert_assets_unchanged(except_report=True)

    def test_canonical_report_requires_exercise(self):
        result = self.run_cli('--output', 'cad/layout-validation.json')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('--exercise', result.stderr)
        self.assert_assets_unchanged()

    def test_ribbon_on_right_edge_is_rejected(self):
        doc = App.openDocument(str(self.root/'cad/vintrox-layout.FCStd'))
        doc.ScreenRibbonBoard.setExpression(
            'Placement.Base.x',
            'Parameters.SideBorder+Parameters.ScreenW-Parameters.RibbonW',
        )
        doc.recompute()
        with self.assertRaisesRegex(AssertionError, '排线板未靠屏幕左边缘'):
            verifier._verify_document(doc, self.root, exercise=False)
        self.assert_assets_unchanged()

    def test_partial_check_can_write_a_separate_report(self):
        result = self.run_cli('--output', 'readback.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.root/'readback.json').read_text())
        self.assertFalse(report['saved_readback']['parametric_exercise_executed'])
        self.assertNotIn('revision_comparison', report)
        self.assert_assets_unchanged()

    def test_translated_step_fails_without_overwriting_report(self):
        path = self.root/'cad/vintrox-layout.step'
        step = Part.Shape()
        step.read(str(path))
        step.translate(App.Vector(10, 0, 0))
        step.exportStep(str(path))
        before = self.report.read_bytes()
        result = self.run_cli('--exercise', '--output', 'cad/layout-validation.json')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('STEP geometry mismatch', result.stderr)
        self.assertEqual(self.report.read_bytes(), before)
        self.assertEqual((self.root/'cad/vintrox-layout.FCStd').read_bytes(),
                         self.original[Path('cad/vintrox-layout.FCStd')])
        documents = set(App.listDocuments())
        with self.assertRaisesRegex(ValueError, 'STEP geometry mismatch'):
            verifier.verify(self.root)
        self.assertEqual(set(App.listDocuments()), documents)

if __name__ == '__main__':
    unittest.main()
