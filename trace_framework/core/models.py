"""
Core data models for the JanusTrace framework.

This module defines the primary data structures used throughout the tool
to represent parsed requirements and discovered source code traces.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class ValidationStatus(Enum):
    """Indicates the validation state of a requirement or trace."""
    VALID = "VALID"
    INVALID_FORMAT = "INVALID_FORMAT"

@dataclass
class Requirement:
    """Represents a requirement parsed from a source document (Excel/CSV).

    Attributes:
        id: The unique identifier for the requirement (e.g., 'REQ-001').
        description: A human-readable description of the requirement text.
        category: Optional grouping category.
        source_file: The path to the file where this requirement is defined.
        line_number: The row number in the source file.
        status: Validation status of the requirement ID format.
        error_message: Detailed error string if validation fails.
    """
    id: str
    description: str
    category: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    status: ValidationStatus = ValidationStatus.VALID
    error_message: Optional[str] = None

@dataclass
class TraceObject:
    """Represents a requirement tag found within source code files.

    Attributes:
        req_id: The ID of the requirement this trace claims to implement.
        source_file: The relative or absolute path to the source code file.
        line_number: The line number where the tag was found.
        context: The surrounding code/comment text where the tag appeared.
        status: Validation status of the trace tag format.
        error_message: Detailed error string if validation fails.
    """
    req_id: str
    source_file: str
    line_number: int
    context: str = ""
    status: ValidationStatus = ValidationStatus.VALID
    error_message: Optional[str] = None
