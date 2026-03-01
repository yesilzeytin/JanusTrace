"""
Document parsers for reading requirements from Excel and CSV files.

Provides a shared base class (TabularDocumentParser) with format-specific
subclasses for Excel (.xlsx/.xls) and CSV file formats. All parsers validate
requirement IDs against the configured regex pattern.
"""

import logging
import re
from typing import List

import pandas as pd

from trace_framework.core.models import Requirement, ValidationStatus
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

            req_id = str(row[id_col]).strip()
            description = str(row.get(desc_col, "")).strip()
            category = str(row.get(cat_col, "")).strip()

            # Validate the requirement ID against the configured pattern
            status = ValidationStatus.VALID
            error_msg = None

            if not self.id_pattern.fullmatch(req_id):
                status = ValidationStatus.INVALID_FORMAT
                error_msg = f"ID '{req_id}' does not match pattern."

            requirement = Requirement(
                id=req_id,
                description=description,
                category=category,
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
