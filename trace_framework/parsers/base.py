from abc import ABC, abstractmethod
from typing import List
from trace_framework.core.models import Requirement, TraceObject

class DocumentParser(ABC):
    @abstractmethod
    def parse_requirements(self, file_path: str) -> List[Requirement]:
        """Reads the source of truth (Excel/CSV) and returns Req objects."""
        pass

class SourceParser(ABC):
    @abstractmethod
    def scan_for_tags(self, file_path: str, regex_pattern: str) -> List[TraceObject]:
        """Scans HDL files for the generated regex pattern."""
        pass
