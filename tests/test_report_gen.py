"""
Tests for the ReportGenerator.

Verifies HTML and JSON report generation, timestamped filenames,
data serialization, and proper embedding of JSON data in HTML output.
"""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trace_framework.core.models import Requirement, TraceObject
from trace_framework.core.engine import TraceabilityEngine
from trace_framework.utils.report_gen import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    """Tests for report generation, timestamping, and data serialization."""

    def setUp(self):
        """Create temp output dir and sample engine results."""
        self.output_dir = tempfile.mkdtemp(prefix="janustrace_report_test_")
        self.gen = ReportGenerator(output_dir=self.output_dir)

        # Build sample traceability results from engine
        reqs = [
            Requirement(id="REQ-001", description="First requirement"),
            Requirement(id="REQ-002", description="Second requirement"),
            Requirement(id="REQ-003", description="Uncovered requirement"),
        ]
        traces = [
            TraceObject(req_id="REQ-001", source_file="a.sv", line_number=10, context="// [REQ-001]"),
            TraceObject(req_id="REQ-002", source_file="b.vhd", line_number=20, context="-- [REQ-002]"),
            TraceObject(req_id="REQ-999", source_file="c.v", line_number=30, context="// [REQ-999]"),
        ]
        engine = TraceabilityEngine()
        self.results = engine.link(reqs, traces)

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.output_dir, ignore_errors=True)

    # ----- Timestamped Filenames -----

    def test_timestamped_filename_format(self):
        """Timestamped filenames should include YYYYMMDD_HHMMSS."""
        name = ReportGenerator._timestamped_filename("report.html")
        # Pattern: report_YYYYMMDD_HHMMSS.html
        self.assertRegex(name, r"report_\d{8}_\d{6}\.html")

    def test_timestamped_preserves_extension(self):
        """File extension should be preserved in timestamped filenames."""
        self.assertTrue(ReportGenerator._timestamped_filename("data.json").endswith(".json"))
        self.assertTrue(ReportGenerator._timestamped_filename("output.html").endswith(".html"))

    # ----- HTML Report -----

    def test_html_report_created(self):
        """HTML report file should be created in the output directory."""
        path = self.gen.generate_html(self.results)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".html"))

    def test_html_contains_embedded_json(self):
        """HTML report should contain a <script type='application/json'> with report data."""
        path = self.gen.generate_html(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('application/json', content)
        self.assertIn('report-data', content)

        # Extract the JSON blob and verify it parses
        match = re.search(
            r'<script type="application/json" id="report-data">\s*({.*?})\s*</script>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "Should find embedded JSON blob")
        data = json.loads(match.group(1))
        self.assertIn('stats', data)
        self.assertIn('matrix', data)

    def test_html_contains_sort_controls(self):
        """HTML report should have interactive sorting controls."""
        path = self.gen.generate_html(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('sortReqTable', content)
        self.assertIn('renderReqTable', content)
        self.assertIn('search-req', content)
        self.assertIn('filter-status', content)

    def test_html_contains_coverage_percentage(self):
        """HTML report should display coverage percentage prominently."""
        path = self.gen.generate_html(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('coverage_percentage', content)

    # ----- JSON Report -----

    def test_json_report_created(self):
        """JSON report file should be created in the output directory."""
        path = self.gen.generate_json(self.results)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".json"))

    def test_json_report_parseable(self):
        """JSON report should be valid, parseable JSON."""
        path = self.gen.generate_json(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_json_report_structure(self):
        """JSON report should contain expected top-level keys."""
        path = self.gen.generate_json(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        expected_keys = {
            'generated_at', 'stats', 'matrix',
            'invalid_reqs', 'orphans', 'invalid_traces',
            'duplicate_reqs', 'r2r',
        }
        self.assertEqual(set(data.keys()), expected_keys)

    def test_json_report_stats(self):
        """JSON stats should reflect correct values from engine results."""
        path = self.gen.generate_json(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stats = data['stats']
        self.assertEqual(stats['total_reqs'], 3)
        self.assertEqual(stats['covered_reqs'], 2)
        self.assertEqual(stats['missing_reqs'], 1)
        self.assertEqual(stats['orphaned_traces'], 1)
        self.assertAlmostEqual(stats['coverage_percentage'], 66.7, places=1)

    def test_json_matrix_entries(self):
        """JSON matrix should contain entries for all valid requirements."""
        path = self.gen.generate_json(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        matrix_ids = [row['id'] for row in data['matrix']]
        self.assertIn('REQ-001', matrix_ids)
        self.assertIn('REQ-002', matrix_ids)
        self.assertIn('REQ-003', matrix_ids)

    def test_json_orphans(self):
        """Orphaned traces should appear in the orphans list."""
        path = self.gen.generate_json(self.results)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        orphan_tags = [o['tag'] for o in data['orphans']]
        self.assertIn('REQ-999', orphan_tags)

    # ----- Multiple Reports Don't Overwrite -----

    def test_multiple_reports_unique_names(self):
        """Generating two reports rapidly should produce unique filenames."""
        import time
        path1 = self.gen.generate_html(self.results)
        time.sleep(1.1)  # Ensure different second
        path2 = self.gen.generate_html(self.results)
        self.assertNotEqual(path1, path2)
        self.assertTrue(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))


if __name__ == '__main__':
    unittest.main()
