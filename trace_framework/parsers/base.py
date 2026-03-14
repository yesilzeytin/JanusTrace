"""
Base parser interfaces for JanusTrace.
"""
# pylint: disable=too-few-public-methods

from abc import ABC, abstractmethod
from typing import List
from trace_framework.core.models import Requirement, TraceObject

class DocumentParser(ABC):
    """Abstract interface for parsing Requirements from specifications."""
    @abstractmethod
    def parse_requirements(self, file_path: str) -> List[Requirement]:
        """Reads the source of truth (Excel/CSV) and returns Req objects."""
        raise NotImplementedError

class SourceParser(ABC):
    """Abstract interface for parsing TraceObjects from source files."""
    @abstractmethod
    def scan_for_tags(self, file_path: str, regex_pattern: str) -> List[TraceObject]:
        """Scans HDL files for the generated regex pattern."""
        raise NotImplementedError
