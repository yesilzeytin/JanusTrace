import re
import unittest

class TestRegexFix(unittest.TestCase):
    def test_csv_validation(self):
        # Scenario: User has ID "PROJ-REQ-001"
        # Regex should NOT have brackets
        regex = r"(?P<id>PROJ\-REQ\-\d+)"
        pattern = re.compile(regex)

        req_id = "PROJ-REQ-001"
        self.assertTrue(pattern.fullmatch(req_id), "CSV ID should match match clean regex")

        # Scenario: ID with brackets (should NOT happen in CSV usually, but if user put brackets in CSV, it fails unless regex has them)
        # Typically CSV ID is clean.

    def test_hdl_extraction(self):
        # Scenario: Source code has "{PROJ-REQ-001}"
        # Config has tags: start="{", end="}"
        content = "   // {PROJ-REQ-001} Supported"

        start_token = "{"
        end_token = "}"
        regex = r"(?P<id>PROJ\-REQ\-\d+)"
        pattern = re.compile(regex)

        # Logic from hdl_parsers.py
        candidate_pattern = re.escape(start_token) + r'(?P<content>.*?)' + re.escape(end_token)
        matches = list(re.finditer(candidate_pattern, content))

        self.assertTrue(len(matches) > 0, "Should find candidate tag")
        candidate = matches[0].group('content').strip()
        self.assertEqual(candidate, "PROJ-REQ-001")

        # Validate candidate
        self.assertTrue(pattern.fullmatch(candidate), "Extracted content should match clean regex")

if __name__ == '__main__':
    unittest.main()
