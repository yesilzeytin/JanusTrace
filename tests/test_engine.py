"""
Tests for the TraceabilityEngine coverage calculation.

Verifies that the engine correctly calculates coverage percentage,
handles edge cases (empty inputs, all invalid), and produces
accurate statistics.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trace_framework.core.models import Requirement, TraceObject, ValidationStatus
from trace_framework.core.engine import TraceabilityEngine


class TestTraceabilityEngine(unittest.TestCase):
    """Test the TraceabilityEngine linking and stats calculation."""

    def setUp(self):
        """Initialize the engine."""
        self.engine = TraceabilityEngine()

    def test_full_coverage(self):
        """100% coverage when all requirements have matching traces."""
        reqs = [
            Requirement(id="REQ-001", description="First requirement"),
            Requirement(id="REQ-002", description="Second requirement"),
        ]
        traces = [
            TraceObject(req_id="REQ-001", source_file="a.sv", line_number=1),
            TraceObject(req_id="REQ-002", source_file="b.sv", line_number=5),
        ]

        results = self.engine.link(reqs, traces)
        stats = results['stats']

        self.assertEqual(stats['coverage_percentage'], 100.0)
        self.assertEqual(stats['covered_reqs'], 2)
        self.assertEqual(stats['missing_reqs'], 0)

    def test_partial_coverage(self):
        """Partial coverage when some requirements lack traces."""
        reqs = [
            Requirement(id="REQ-001", description="First"),
            Requirement(id="REQ-002", description="Second"),
            Requirement(id="REQ-003", description="Third"),
        ]
        traces = [
            TraceObject(req_id="REQ-001", source_file="a.sv", line_number=1),
        ]

        results = self.engine.link(reqs, traces)
        stats = results['stats']

        self.assertAlmostEqual(stats['coverage_percentage'], 33.3, places=1)
        self.assertEqual(stats['covered_reqs'], 1)
        self.assertEqual(stats['missing_reqs'], 2)

    def test_zero_coverage(self):
        """0% coverage when no requirements have traces."""
        reqs = [
            Requirement(id="REQ-001", description="Uncovered"),
        ]
        traces = []

        results = self.engine.link(reqs, traces)
        stats = results['stats']

        self.assertEqual(stats['coverage_percentage'], 0.0)
        self.assertEqual(stats['covered_reqs'], 0)
        self.assertEqual(stats['missing_reqs'], 1)

    def test_no_requirements(self):
        """Edge case: no requirements at all should give 0.0% (no division by zero)."""
        results = self.engine.link([], [])
        stats = results['stats']

        self.assertEqual(stats['coverage_percentage'], 0.0)
        self.assertEqual(stats['total_reqs'], 0)

    def test_orphan_traces_detected(self):
        """Traces with no matching requirement should be flagged as orphans."""
        reqs = [
            Requirement(id="REQ-001", description="Known requirement"),
        ]
        traces = [
            TraceObject(req_id="REQ-001", source_file="a.sv", line_number=1),
            TraceObject(req_id="REQ-999", source_file="b.sv", line_number=10),
        ]

        results = self.engine.link(reqs, traces)

        self.assertEqual(len(results['orphans']), 1)
        self.assertEqual(results['orphans'][0].req_id, "REQ-999")
        self.assertEqual(results['stats']['orphaned_traces'], 1)

    def test_invalid_requirements_excluded_from_coverage(self):
        """Invalid requirements should not count toward coverage percentage."""
        reqs = [
            Requirement(id="REQ-001", description="Valid", status=ValidationStatus.VALID),
            Requirement(id="BAD", description="Invalid", status=ValidationStatus.INVALID_FORMAT),
        ]
        traces = [
            TraceObject(req_id="REQ-001", source_file="a.sv", line_number=1),
        ]

        results = self.engine.link(reqs, traces)
        stats = results['stats']

        # Only 1 valid req covered out of 1 valid total -> 100%
        self.assertEqual(stats['coverage_percentage'], 100.0)
        self.assertEqual(stats['valid_reqs'], 1)
        self.assertEqual(stats['invalid_reqs_count'], 1)

    def test_invalid_traces_excluded(self):
        """Invalid traces should be collected but not linked to requirements."""
        reqs = [
            Requirement(id="REQ-001", description="Valid req"),
        ]
        traces = [
            TraceObject(
                req_id="REQ-001",
                source_file="a.sv",
                line_number=1,
                status=ValidationStatus.INVALID_FORMAT,
                error_message="Bad format"
            ),
        ]

        results = self.engine.link(reqs, traces)
        stats = results['stats']

        # The trace is invalid, so REQ-001 is NOT covered
        self.assertEqual(stats['covered_reqs'], 0)
        self.assertEqual(stats['invalid_traces_count'], 1)
        self.assertEqual(stats['coverage_percentage'], 0.0)

    def test_multiple_traces_per_requirement(self):
        """A requirement traced in multiple files should still count once."""
        reqs = [
            Requirement(id="REQ-001", description="Multi-traced"),
        ]
        traces = [
            TraceObject(req_id="REQ-001", source_file="a.sv", line_number=1),
            TraceObject(req_id="REQ-001", source_file="b.sv", line_number=5),
            TraceObject(req_id="REQ-001", source_file="c.vhd", line_number=10),
        ]

        results = self.engine.link(reqs, traces)
        stats = results['stats']

        self.assertEqual(stats['covered_reqs'], 1)
        self.assertEqual(stats['coverage_percentage'], 100.0)
        # All 3 traces should be linked
        self.assertEqual(len(results['matrix'][0]['traces']), 3)


if __name__ == '__main__':
    unittest.main()
