"""
Configuration validator for JanusTrace YAML configuration files.

Validates the structure and content of configuration dictionaries,
providing clear, actionable error messages for missing or invalid fields.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class ConfigValidationError:
    # pylint: disable=too-few-public-methods
    """Represents a single validation error with severity and context.

    Attributes:
        level: Severity level ('ERROR' or 'WARNING').
        field: Dot-separated path to the invalid field (e.g. 'tags.start_token').
        message: Human-readable description of the issue.
    """

    def __init__(self, level: str, field: str, message: str):
        self.level = level
        self.field = field
        self.message = message

    def __repr__(self):
        return f"[{self.level}] {self.field}: {self.message}"


class ConfigValidator:
    """Validates JanusTrace configuration dictionaries.

    Checks for required fields, correct types, and semantic consistency.
    Returns a list of ConfigValidationError objects.
    """

    # Required top-level sections and their expected types
    REQUIRED_SECTIONS = {
        'tags': dict,
    }

    # At least one of these must be present for regex compilation
    REGEX_SOURCES = ['regex_rules', 'tag_structure']

    @staticmethod
    def validate(config: dict) -> List[ConfigValidationError]:
        """Validate a configuration dictionary.

        Args:
            config: Parsed YAML configuration dictionary.

        Returns:
            List of ConfigValidationError objects. Empty list means valid config.
        """
        errors: List[ConfigValidationError] = []

        if not isinstance(config, dict):
            errors.append(ConfigValidationError(
                'ERROR', 'root', 'Configuration must be a YAML dictionary.'
            ))
            return errors

        # --- Tags section ---
        ConfigValidator._validate_tags(config, errors)

        # --- Regex source ---
        ConfigValidator._validate_regex_source(config, errors)

        # --- Languages section (optional but validated if present) ---
        ConfigValidator._validate_languages(config, errors)

        # --- Columns section (optional but validated if present) ---
        ConfigValidator._validate_columns(config, errors)

        return errors

    @staticmethod
    def validate_or_raise(config: dict) -> None:
        """Validate config and raise ValueError if there are errors.

        Args:
            config: Parsed YAML configuration dictionary.

        Raises:
            ValueError: If any ERROR-level issues are found, with all
                        errors listed in the exception message.
        """
        errors = ConfigValidator.validate(config)
        error_messages = [e for e in errors if e.level == 'ERROR']
        if error_messages:
            details = '\n'.join(f"  - {e}" for e in error_messages)
            raise ValueError(f"Invalid configuration:\n{details}")

        # Log warnings
        for e in errors:
            if e.level == 'WARNING':
                logger.warning("%s", e)

    # ------------------------------------------------------------------
    # Private validators
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_tags(config: dict, errors: List[ConfigValidationError]):
        """Validate the 'tags' section."""
        tags = config.get('tags')
        if tags is None:
            errors.append(ConfigValidationError(
                'ERROR', 'tags', "Missing required section 'tags'."
            ))
            return

        if not isinstance(tags, dict):
            errors.append(ConfigValidationError(
                'ERROR', 'tags', "'tags' must be a dictionary."
            ))
            return

        # start_token and end_token
        for token_key in ('start_token', 'end_token'):
            val = tags.get(token_key)
            if val is None:
                errors.append(ConfigValidationError(
                    'WARNING', f'tags.{token_key}',
                    f"Missing '{token_key}'. Defaults to empty string (no enclosure)."
                ))
            elif not isinstance(val, str):
                errors.append(ConfigValidationError(
                    'ERROR', f'tags.{token_key}',
                    f"'{token_key}' must be a string, got {type(val).__name__}."
                ))

    @staticmethod
    def _validate_regex_source(config: dict, errors: List[ConfigValidationError]):
        """Validate that at least one regex source exists."""
        has_regex_rules = (
            isinstance(config.get('regex_rules'), dict)
            and 'id_pattern' in config.get('regex_rules', {})
        )
        has_tag_structure = (
            'tag_structure' in config
            and 'tokens' in config
        )

        if not has_regex_rules and not has_tag_structure:
            errors.append(ConfigValidationError(
                'ERROR', 'regex_rules / tag_structure',
                "Configuration must define either 'regex_rules.id_pattern' "
                "or both 'tag_structure' and 'tokens'."
            ))

        # Validate tokens if tag_structure is used
        if has_tag_structure:
            tokens = config.get('tokens', {})
            if not isinstance(tokens, dict):
                errors.append(ConfigValidationError(
                    'ERROR', 'tokens',
                    "'tokens' must be a dictionary mapping token names to regex patterns."
                ))

    @staticmethod
    def _validate_languages(config: dict, errors: List[ConfigValidationError]):
        """Validate the 'languages' section if present."""
        languages = config.get('languages')
        if languages is None:
            return  # Optional section, will use defaults

        if not isinstance(languages, list):
            errors.append(ConfigValidationError(
                'ERROR', 'languages', "'languages' must be a list."
            ))
            return

        for i, lang in enumerate(languages):
            prefix = f'languages[{i}]'

            if not isinstance(lang, dict):
                errors.append(ConfigValidationError(
                    'ERROR', prefix, "Each language entry must be a dictionary."
                ))
                continue

            # Required fields
            if 'name' not in lang:
                errors.append(ConfigValidationError(
                    'ERROR', f'{prefix}.name', "Missing required field 'name'."
                ))

            if 'extensions' not in lang:
                errors.append(ConfigValidationError(
                    'ERROR', f'{prefix}.extensions', "Missing required field 'extensions'."
                ))
            elif not isinstance(lang['extensions'], list):
                errors.append(ConfigValidationError(
                    'ERROR', f'{prefix}.extensions', "'extensions' must be a list of strings."
                ))
            elif len(lang['extensions']) == 0:
                errors.append(ConfigValidationError(
                    'WARNING', f'{prefix}.extensions',
                    f"Language '{lang.get('name', '?')}' has no extensions defined."
                ))

            # Comment style validation
            if 'line_comment' not in lang and 'block_comment_start' not in lang:
                errors.append(ConfigValidationError(
                    'WARNING', f'{prefix}',
                    f"Language '{lang.get('name', '?')}' has no comment style defined. "
                    "Tags can only be found inside comments."
                ))

    @staticmethod
    def _validate_columns(config: dict, errors: List[ConfigValidationError]):
        """Validate the 'columns' section if present."""
        columns = config.get('columns')
        if columns is None:
            return  # Optional, will use defaults

        if not isinstance(columns, dict):
            errors.append(ConfigValidationError(
                'ERROR', 'columns', "'columns' must be a dictionary."
            ))
