"""
HDL source code parsers for JanusTrace.
"""
# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-exception-caught,too-few-public-methods,missing-class-docstring

import logging
import re
import os
import collections
from typing import List, Dict
from trace_framework.core.models import TraceObject, ValidationStatus
from trace_framework.parsers.base import SourceParser

logger = logging.getLogger(__name__)

class SourceCodeParser(SourceParser):
    """
    Generic parser for source code files.
    Loads language definitions (extensions, comments) from config.
    Handles extension contention by merging comment styles.
    """
    def __init__(self, config: dict):
        self.config = config
        self.extension_map = self._build_extension_map()

    def _build_extension_map(self) -> Dict[str, List[dict]]:
        """
        Builds a map of extension -> list of language configs.
        Example: {'h': [{'name': 'C', 'line_comment': '//'},
                         {'name': 'Verilog', 'line_comment': '//'}]}
        """
        ext_map = collections.defaultdict(list)

        # Load languages from config, or default if missing
        languages = self.config.get('languages', [])

        # If no languages defined, fall back to standard HDL defaults
        # for backward compatibility with configs that only define tag patterns
        if not languages:
            languages = [
                {
                    'name': 'Verilog',
                    'enabled': True,
                    'extensions': ['v', 'vh'],
                    'line_comment': '//',
                    'block_comment_start': '/*',
                    'block_comment_end': '*/'
                },
                {
                    'name': 'SystemVerilog',
                    'enabled': True,
                    'extensions': ['sv', 'svh'],
                    'line_comment': '//',
                    'block_comment_start': '/*',
                    'block_comment_end': '*/'
                },
                {
                    'name': 'VHDL',
                    'enabled': True,
                    'extensions': ['vhd', 'vhdl'],
                    'line_comment': '--',
                    'block_comment_start': None,
                    'block_comment_end': None
                }
            ]

        for lang in languages:
            if not lang.get('enabled', True):
                continue

            extensions = lang.get('extensions', [])

            # Normalize extensions (remove dot, lower case)
            for ext in extensions:
                clean_ext = ext.strip().lower().replace('.', '')
                if clean_ext:
                    ext_map[clean_ext].append(lang)

        return ext_map

    def scan_for_tags(self, file_path: str, regex_pattern: str) -> List[TraceObject]:
        traces = []

        _, ext = os.path.splitext(file_path)
        ext = ext.lower().replace('.', '')

        lang_configs = self.extension_map.get(ext)
        if not lang_configs:
            return []

        # Compile tag regex
        try:
            tag_re = re.compile(regex_pattern)
        except re.error as e:
            logger.error("Invalid regex pattern: %s", e)
            return []

        try:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        except Exception as e:
            logger.error("Error reading file %s: %s", file_path, e)
            return []

        # Merge comment patterns from all conflicting languages for this extension
        # to ensure we capture everything safely.
        comment_patterns = set()

        for lang in lang_configs:
            # Line comments
            lc = lang.get('line_comment')
            if lc:
                # Escape the token
                esc_lc = re.escape(lc)
                comment_patterns.add(f'{esc_lc}.*')

            # Block comments
            bs = lang.get('block_comment_start')
            be = lang.get('block_comment_end')
            if bs and be:
                esc_bs = re.escape(bs)
                esc_be = re.escape(be)
                # Non-greedy match for block
                comment_patterns.add(f'{esc_bs}[\\s\\S]*?{esc_be}')

        if not comment_patterns:
            return []

        full_comment_pattern = '|'.join(f'({p})' for p in comment_patterns)

        # Find all comments
        comment_matches = re.finditer(full_comment_pattern, content, re.MULTILINE)

        # Get delimiters
        tags_config = self.config.get('tags', {})
        start_token = tags_config.get('start_token', '[')
        end_token = tags_config.get('end_token', ']')

        # Regex to find candidates between tokens
        candidate_pattern = re.escape(start_token) + r'(?P<content>.*?)' + re.escape(end_token)
        candidate_re = re.compile(candidate_pattern)

        for match in comment_matches:
            comment_text = match.group(0)
            start_pos = match.start()

            # Find all candidates within this comment
            for tag_match in candidate_re.finditer(comment_text):
                candidate = tag_match.group('content').strip()
                if not candidate:
                    continue

                # Calculate approximate line number
                tag_start_offset = tag_match.start()
                lines_before = comment_text[:tag_start_offset].count('\n')
                line_number = content.count('\n', 0, start_pos) + 1 + lines_before

                if tag_re.fullmatch(candidate):
                    status = ValidationStatus.VALID
                    error_msg = None
                else:
                    status = ValidationStatus.INVALID_FORMAT
                    error_msg = f"Tag content '{candidate}' does not match pattern."

                trace = TraceObject(
                    req_id=candidate,
                    source_file=file_path,
                    line_number=line_number,
                    context=comment_text.strip().replace('\n', ' '),
                    status=status,
                    error_message=error_msg
                )
                traces.append(trace)

        return traces

# For backward compatibility import
class HDLParser(SourceCodeParser):
    pass
