"""
Tests for the ConfigValidator.

Verifies that config validation catches missing sections, invalid types,
and provides appropriate ERROR/WARNING levels for various config issues.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trace_framework.utils.config_validator import ConfigValidator


class TestConfigValidator(unittest.TestCase):
    """Test the ConfigValidator with various config scenarios."""

    def _make_valid_config(self):
        """Return a minimal valid configuration dictionary."""
        return {
            'tags': {
                'start_token': '[',
                'end_token': ']',
            },
            'regex_rules': {
                'id_pattern': r'REQ-\d+',
            },
        }

    # ----- Valid configurations -----

    def test_valid_minimal_config(self):
        """A minimal valid config should produce no errors."""
        config = self._make_valid_config()
        errors = ConfigValidator.validate(config)
        error_level = [e for e in errors if e.level == 'ERROR']
        self.assertEqual(len(error_level), 0)

    def test_valid_config_with_tag_structure(self):
        """Config using tag_structure + tokens should be valid."""
        config = {
            'tags': {'start_token': '[', 'end_token': ']'},
            'tag_structure': '{prefix}-{id}',
            'tokens': {
                'prefix': {'regex': '[A-Z]+'},
                'id': {'regex': r'\d+'},
            },
        }
        errors = ConfigValidator.validate(config)
        error_level = [e for e in errors if e.level == 'ERROR']
        self.assertEqual(len(error_level), 0)

    # ----- Missing required sections -----

    def test_missing_tags_section(self):
        """Missing 'tags' section should produce an error."""
        config = {'regex_rules': {'id_pattern': r'REQ-\d+'}}
        errors = ConfigValidator.validate(config)
        tag_errors = [e for e in errors if 'tags' in e.field and e.level == 'ERROR']
        self.assertGreater(len(tag_errors), 0)

    def test_missing_regex_and_tag_structure(self):
        """Missing both regex_rules and tag_structure should produce an error."""
        config = {'tags': {'start_token': '[', 'end_token': ']'}}
        errors = ConfigValidator.validate(config)
        regex_errors = [e for e in errors if 'regex' in e.field.lower() or 'tag_structure' in e.field.lower()]
        self.assertGreater(len(regex_errors), 0)

    # ----- Tags validation -----

    def test_tags_not_dict(self):
        """Tags as non-dict should produce an error."""
        config = self._make_valid_config()
        config['tags'] = 'not a dict'
        errors = ConfigValidator.validate(config)
        self.assertTrue(any(e.level == 'ERROR' and 'tags' in e.field for e in errors))

    def test_missing_start_token_warning(self):
        """Missing start_token should produce a warning."""
        config = self._make_valid_config()
        del config['tags']['start_token']
        errors = ConfigValidator.validate(config)
        warnings = [e for e in errors if e.level == 'WARNING' and 'start_token' in e.field]
        self.assertGreater(len(warnings), 0)

    # ----- Languages validation -----

    def test_languages_not_list(self):
        """Languages as non-list should produce an error."""
        config = self._make_valid_config()
        config['languages'] = 'not a list'
        errors = ConfigValidator.validate(config)
        self.assertTrue(any(e.level == 'ERROR' and 'languages' in e.field for e in errors))

    def test_language_missing_name(self):
        """Language entry without 'name' should produce an error."""
        config = self._make_valid_config()
        config['languages'] = [{'extensions': ['v'], 'line_comment': '//'}]
        errors = ConfigValidator.validate(config)
        self.assertTrue(any(e.level == 'ERROR' and 'name' in e.field for e in errors))

    def test_language_missing_extensions(self):
        """Language entry without 'extensions' should produce an error."""
        config = self._make_valid_config()
        config['languages'] = [{'name': 'Test', 'line_comment': '//'}]
        errors = ConfigValidator.validate(config)
        self.assertTrue(any(e.level == 'ERROR' and 'extensions' in e.field for e in errors))

    def test_language_empty_extensions_warning(self):
        """Language entry with empty extensions list should produce a warning."""
        config = self._make_valid_config()
        config['languages'] = [{'name': 'Test', 'extensions': [], 'line_comment': '//'}]
        errors = ConfigValidator.validate(config)
        warnings = [e for e in errors if e.level == 'WARNING' and 'extensions' in e.field]
        self.assertGreater(len(warnings), 0)

    def test_language_no_comment_style_warning(self):
        """Language without any comment style should produce a warning."""
        config = self._make_valid_config()
        config['languages'] = [{'name': 'Test', 'extensions': ['t']}]
        errors = ConfigValidator.validate(config)
        warnings = [e for e in errors if e.level == 'WARNING']
        self.assertGreater(len(warnings), 0)

    # ----- Non-dict root -----

    def test_non_dict_config(self):
        """Non-dict config should produce an error."""
        errors = ConfigValidator.validate("not a dict")
        self.assertTrue(any(e.level == 'ERROR' for e in errors))

    # ----- validate_or_raise -----

    def test_validate_or_raise_valid(self):
        """Valid config should not raise."""
        config = self._make_valid_config()
        ConfigValidator.validate_or_raise(config)  # Should not raise

    def test_validate_or_raise_invalid(self):
        """Invalid config should raise ValueError."""
        with self.assertRaises(ValueError):
            ConfigValidator.validate_or_raise({})


if __name__ == '__main__':
    unittest.main()
