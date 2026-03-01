import unittest
from trace_framework.ui.config_helper import ConfigHelper

class TestConfigHelper(unittest.TestCase):
    def test_simple_numeric(self):
        # REQ-001 -> REQ-\d+
        res = ConfigHelper.generate_regex_from_id("REQ-001")
        # Expected: (?P<id>REQ\-\d+) because - is escaped
        self.assertIn(r"REQ\-\d+", res)
        self.assertIn("(?P<id>", res)

    def test_compound_id(self):
        """Compound ID like PROJ-REQ-123 should produce a valid regex."""
        res = ConfigHelper.generate_regex_from_id("PROJ-REQ-123")
        # Should produce a named group wrapping the full pattern
        self.assertIn("(?P<id>", res)
        # Digits should be generalized to \d+
        self.assertIn(r"\d+", res)
        # Separators should be escaped
        self.assertIn(r"\-", res)
        # Fixed text portions should be preserved
        self.assertIn("PROJ", res)
        self.assertIn("REQ", res)

    def test_enclosement(self):
        regex = r"REQ-\d+"
        res = ConfigHelper.wrap_with_enclosement(regex, "[", "]")
        self.assertEqual(res, r"\[REQ-\d+\]")

if __name__ == '__main__':
    unittest.main()
