"""
Document parsers for reading requirements from Excel and CSV files.

Provides a shared base class (TabularDocumentParser) with format-specific
subclasses for Excel (.xlsx/.xls) and CSV file formats. All parsers validate
requirement IDs against the configured regex pattern.
"""
# pylint: disable=too-many-locals,too-few-public-methods,broad-exception-caught,missing-function-docstring

import logging
import re
from typing import List

import pandas as pd
from pandas import isna as pd_isna

from trace_framework.core.models import Requirement, TraceObject, ValidationStatus
from trace_framework.parsers.base import DocumentParser
from trace_framework.utils.regex_builder import RegexBuilder

logger = logging.getLogger(__name__)


class TabularDocumentParser(DocumentParser):
    """Base parser for tabular requirement documents (Excel/CSV).

    Handles shared logic for column mapping, ID validation, and
    Requirement object construction. Subclasses only need to implement
    the _read_dataframe() method for their specific file format.
    """

    def __init__(self, config: dict):
        self.config = config
        # Compile the regex pattern used to validate requirement IDs
        builder = RegexBuilder(config)
        self.id_pattern = re.compile(builder.compile_pattern())

    def _read_dataframe(self, file_path: str) -> pd.DataFrame:
        """Read the file into a pandas DataFrame.

        Args:
            file_path: Path to the requirements file.

        Returns:
            A pandas DataFrame containing the file contents.

        Raises:
            Exception: If the file cannot be read.
        """
        raise NotImplementedError("Subclasses must implement _read_dataframe")

    def parse_requirements(self, file_path: str) -> List[Requirement]:
        """Parse requirements from a tabular document file.

        Reads the file, extracts requirement data from configured columns,
        validates each ID against the compiled regex pattern, and returns
        a list of Requirement objects.

        Args:
            file_path: Path to the requirements file (Excel or CSV).

        Returns:
            List of Requirement objects extracted from the file.
        """
        # Resolve column names from config, with sensible defaults
        col_map = self.config.get('columns', {})
        id_col = col_map.get('id', 'ID')
        desc_col = col_map.get('description', 'Description')
        cat_col = col_map.get('category', 'Category')
        parent_col = col_map.get('parent', 'Parent')  # Optional R2R parent column

        try:
            df = self._read_dataframe(file_path)
        except Exception as e:
            logger.error("Error reading file %s: %s", file_path, e)
            return []

        requirements = []
        for row_index, row in df.iterrows():
            # Skip rows missing the ID column
            if id_col not in row:
                continue

            req_id_raw = row.get(id_col, "")
            if pd_isna(req_id_raw):
                continue  # Skip rows with a missing/nan ID
            req_id = str(req_id_raw).strip()

            desc_raw = row.get(desc_col, "")
            description = "" if pd_isna(desc_raw) else str(desc_raw).strip()

            cat_raw = row.get(cat_col, "")
            category = "" if pd_isna(cat_raw) else str(cat_raw).strip()

            # Validate the requirement ID against the configured pattern
            status = ValidationStatus.VALID
            error_msg = None

            if not self.id_pattern.fullmatch(req_id):
                status = ValidationStatus.INVALID_FORMAT
                error_msg = f"ID '{req_id}' does not match pattern."

            parent_id = None
            if parent_col in row:
                parent_raw = row.get(parent_col, "")
                if not pd_isna(parent_raw):
                    parent_id_str = str(parent_raw).strip()
                    if parent_id_str:
                        parent_id = parent_id_str

            requirement = Requirement(
                id=req_id,
                description=description,
                category=category,
                parent_id=parent_id,
                source_file=file_path,
                line_number=row_index + 2,  # +2: header row + 0-indexed
                status=status,
                error_message=error_msg
            )
            requirements.append(requirement)

        return requirements


class ExcelParser(TabularDocumentParser):
    """Parser for Excel (.xlsx, .xls) requirement documents."""

    def _read_dataframe(self, file_path: str) -> pd.DataFrame:
        """Read an Excel file into a pandas DataFrame."""
        return pd.read_excel(file_path)


class CSVParser(TabularDocumentParser):
    """Parser for CSV requirement documents."""

    def _read_dataframe(self, file_path: str) -> pd.DataFrame:
        """Read a CSV file into a pandas DataFrame."""
        return pd.read_csv(file_path)

class DocumentTracer:
    """Parses a secondary CSV/Excel document to extract requirement traces.

    Treats each row in the document as a source of traces, looking at a specific
    link column, splitting it, and emitting traces pointing back to the primary document.
    """
    def __init__(self, config: dict):
        self.config = config
        builder = RegexBuilder(config)
        self.id_pattern = re.compile(builder.compile_pattern())

    def scan_for_tags(self, file_path: str, link_column: str, source_id_column: str) -> List[TraceObject]:
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            logger.error("Error reading file %s: %s", file_path, e)
            return []

        traces = []
        for row_index, row in df.iterrows():
            if link_column not in row or source_id_column not in row:
                continue

            links_raw = row.get(link_column, "")
            source_id_raw = row.get(source_id_column, "")

            if pd_isna(links_raw) or pd_isna(source_id_raw):
                continue

            source_id = str(source_id_raw).strip()
            links_str = str(links_raw).strip()

            if not links_str:
                continue

            # Split by commas, semicolons, or whitespace
            parts = re.split(r'[,\s;]+', links_str)

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                if self.id_pattern.fullmatch(part):
                    status = ValidationStatus.VALID
                    error_msg = None
                else:
                    status = ValidationStatus.INVALID_FORMAT
                    error_msg = f"Tag content '{part}' does not match pattern."

                trace = TraceObject(
                    req_id=part,
                    source_file=file_path,
                    line_number=row_index + 2, # +2 for header and 0-index
                    context=f"Document trace from: {source_id}",
                    status=status,
                    error_message=error_msg
                )
                traces.append(trace)

        return traces
