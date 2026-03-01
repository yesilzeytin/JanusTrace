"""
Tests for CLI extension scanning behavior.

Verifies that the CLI uses config-driven language extensions rather than
hardcoded file suffixes, ensuring parity with the GUI scan path.
"""

import os
import sys
import unittest
import tempfile
import shutil

# Ensure project root is on the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trace_framework.parsers.hdl_parsers import SourceCodeParser


class TestCLIExtensionScanning(unittest.TestCase):
    """Test that source scanning uses config-driven extensions."""

    def setUp(self):
        """Create a temporary source directory with mixed file types."""
        self.test_dir = tempfile.mkdtemp(prefix="janustrace_test_")

        # Create test source files with trace tags
        self._write_file("design.sv", "// [REQ-001] SystemVerilog trace\n")
        self._write_file("top.vhd", "-- [REQ-002] VHDL trace\n")
        self._write_file("module.v", "// [REQ-003] Verilog trace\n")
        self._write_file("helper.py", "# [REQ-004] Python trace\n")
        self._write_file("driver.c", "// [REQ-005] C trace\n")
        self._write_file("notes.txt", "This should be ignored\n")
        self._write_file("readme.md", "# [REQ-FAKE] Not a source file\n")

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_file(self, filename, content):
        """Helper to write a file in the test directory."""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def _build_config_with_languages(self, language_list):
        """Build a config dict with the given language definitions."""
        return {
            'languages': language_list,
            'tags': {'start_token': '[', 'end_token': ']'}
        }

    def test_hdl_extensions_from_config(self):
        """Parser should scan HDL files when languages define HDL extensions."""
        config = self._build_config_with_languages([
            {
                'name': 'SystemVerilog',
                'enabled': True,
                'extensions': ['sv'],
                'line_comment': '//',
                'block_comment_start': '/*',
                'block_comment_end': '*/'
            },
            {
                'name': 'VHDL',
                'enabled': True,
                'extensions': ['vhd'],
                'line_comment': '--',
                'block_comment_start': None,
                'block_comment_end': None
            }
        ])

        parser = SourceCodeParser(config)
        supported_extensions = tuple(f".{ext}" for ext in parser.extension_map.keys())

        # Verify only configured extensions are in the map
        self.assertIn('.sv', supported_extensions)
        self.assertIn('.vhd', supported_extensions)
        self.assertNotIn('.py', supported_extensions)
        self.assertNotIn('.c', supported_extensions)

    def test_non_hdl_extensions_from_config(self):
        """Parser should also scan non-HDL files when configured (e.g., Python, C)."""
        config = self._build_config_with_languages([
            {
                'name': 'Python',
                'enabled': True,
                'extensions': ['py'],
                'line_comment': '#',
                'block_comment_start': None,
                'block_comment_end': None
            },
            {
                'name': 'C/C++',
                'enabled': True,
                'extensions': ['c', 'cpp', 'h'],
                'line_comment': '//',
                'block_comment_start': '/*',
                'block_comment_end': '*/'
            }
        ])

        parser = SourceCodeParser(config)
        supported_extensions = tuple(f".{ext}" for ext in parser.extension_map.keys())

        self.assertIn('.py', supported_extensions)
        self.assertIn('.c', supported_extensions)
        self.assertIn('.cpp', supported_extensions)
        self.assertIn('.h', supported_extensions)

    def test_disabled_languages_excluded(self):
        """Disabled languages should not contribute extensions to the scan."""
        config = self._build_config_with_languages([
            {
                'name': 'SystemVerilog',
                'enabled': True,
                'extensions': ['sv'],
                'line_comment': '//',
                'block_comment_start': '/*',
                'block_comment_end': '*/'
            },
            {
                'name': 'Python',
                'enabled': False,
                'extensions': ['py'],
                'line_comment': '#',
                'block_comment_start': None,
                'block_comment_end': None
            }
        ])

        parser = SourceCodeParser(config)
        supported_extensions = tuple(f".{ext}" for ext in parser.extension_map.keys())

        self.assertIn('.sv', supported_extensions)
        self.assertNotIn('.py', supported_extensions)

    def test_scan_finds_tags_in_configured_files(self):
        """End-to-end: scanning should find tags in all configured file types."""
        config = self._build_config_with_languages([
            {
                'name': 'SystemVerilog',
                'enabled': True,
                'extensions': ['sv'],
                'line_comment': '//',
                'block_comment_start': '/*',
                'block_comment_end': '*/'
            },
            {
                'name': 'Python',
                'enabled': True,
                'extensions': ['py'],
                'line_comment': '#',
                'block_comment_start': None,
                'block_comment_end': None
            }
        ])

        parser = SourceCodeParser(config)
        regex_pattern = r"REQ-\d+"

        # Collect traces from all configured file types
        all_traces = []
        supported_extensions = tuple(f".{ext}" for ext in parser.extension_map.keys())

        for root, _dirs, files in os.walk(self.test_dir):
            for filename in files:
                if filename.lower().endswith(supported_extensions):
                    filepath = os.path.join(root, filename)
                    traces = parser.scan_for_tags(filepath, regex_pattern)
                    all_traces.extend(traces)

        found_ids = {trace.req_id for trace in all_traces}

        # Should find SV and Python tags
        self.assertIn('REQ-001', found_ids, "Should find tag in .sv file")
        self.assertIn('REQ-004', found_ids, "Should find tag in .py file")

        # Should NOT find tags in unconfigured files
        self.assertNotIn('REQ-003', found_ids, "Should not scan .v (not configured)")
        self.assertNotIn('REQ-005', found_ids, "Should not scan .c (not configured)")

    def test_empty_languages_falls_back_to_hdl_defaults(self):
        """An empty languages list should fall back to default HDL extensions."""
        config = self._build_config_with_languages([])

        parser = SourceCodeParser(config)
        supported_extensions = tuple(f".{ext}" for ext in parser.extension_map.keys())

        # Should fall back to default HDL: Verilog (.v, .vh), SV (.sv, .svh), VHDL (.vhd, .vhdl)
        self.assertIn('.sv', supported_extensions)
        self.assertIn('.vhd', supported_extensions)
        self.assertIn('.v', supported_extensions)
        self.assertEqual(len(supported_extensions), 6)


if __name__ == '__main__':
    unittest.main()
