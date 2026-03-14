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


class TestDuplicateRequirements(unittest.TestCase):
    """Tests for duplicate requirement ID detection."""

    def setUp(self):
        self.engine = TraceabilityEngine()

    def test_duplicate_ids_reported(self):
        """Duplicate req IDs should be reported and excluded from coverage."""
        reqs = [
            Requirement(id="REQ-001", description="First"),
            Requirement(id="REQ-001", description="Duplicate"),  # same ID
            Requirement(id="REQ-002", description="Second"),
        ]
        results = self.engine.link(reqs, [])
        self.assertEqual(results['stats']['duplicate_reqs_count'], 1)
        self.assertEqual(len(results['duplicate_reqs']), 1)
        # total_reqs counts all including duplicates
        self.assertEqual(results['stats']['total_reqs'], 3)


class TestR2RLinking(unittest.TestCase):
    """Tests for the R2R (requirement-to-requirement) hierarchy linking."""

    def setUp(self):
        self.engine = TraceabilityEngine()

    def _make_req(self, req_id, parent_id=None):
        return Requirement(id=req_id, description=f"Desc of {req_id}", parent_id=parent_id)

    def test_basic_hierarchy(self):
        """Children should be linked under the correct parent."""
        reqs = [
            self._make_req("SYS-001"),
            self._make_req("SYS-001-A", parent_id="SYS-001"),
            self._make_req("SYS-001-B", parent_id="SYS-001"),
        ]
        result = self.engine.link_r2r(reqs)
        self.assertTrue(result['has_r2r'])
        self.assertIn("SYS-001", result['hierarchy'])
        self.assertCountEqual(result['hierarchy']['SYS-001'], ["SYS-001-A", "SYS-001-B"])
        self.assertEqual(result['orphaned_parents'], [])
        self.assertEqual(result['cycles'], [])

    def test_no_parents_returns_empty(self):
        """When no requirements have parent IDs, has_r2r should be False."""
        reqs = [
            self._make_req("REQ-001"),
            self._make_req("REQ-002"),
        ]
        result = self.engine.link_r2r(reqs)
        self.assertFalse(result['has_r2r'])
        self.assertEqual(result['hierarchy'], {})
        self.assertEqual(result['orphaned_parents'], [])
        self.assertEqual(result['cycles'], [])

    def test_orphaned_parent_reference(self):
        """A child pointing to a non-existent parent should be reported as orphaned."""
        reqs = [
            self._make_req("REQ-001", parent_id="SYS-999"),  # SYS-999 does not exist
        ]
        result = self.engine.link_r2r(reqs)
        self.assertTrue(result['has_r2r'])
        self.assertEqual(len(result['orphaned_parents']), 1)
        self.assertEqual(result['orphaned_parents'][0]['child_id'], "REQ-001")
        self.assertEqual(result['orphaned_parents'][0]['missing_parent_id'], "SYS-999")
        self.assertEqual(result['hierarchy'], {})

    def test_direct_cycle_detected(self):
        """A -> B -> A cycle should be detected and reported."""
        reqs = [
            self._make_req("REQ-A", parent_id="REQ-B"),
            self._make_req("REQ-B", parent_id="REQ-A"),
        ]
        result = self.engine.link_r2r(reqs)
        self.assertTrue(result['has_r2r'])
        self.assertEqual(len(result['cycles']), 1)
        cycle = result['cycles'][0]
        self.assertIn("REQ-A", cycle)
        self.assertIn("REQ-B", cycle)
        self.assertEqual(cycle[0], cycle[-1])

    def test_indirect_cycle_detected(self):
        """A -> B -> C -> A three-node cycle should be detected."""
        reqs = [
            self._make_req("REQ-A", parent_id="REQ-C"),
            self._make_req("REQ-B", parent_id="REQ-A"),
            self._make_req("REQ-C", parent_id="REQ-B"),
        ]
        result = self.engine.link_r2r(reqs)
        self.assertTrue(result['has_r2r'])
        self.assertGreater(len(result['cycles']), 0)

    def test_mixed_valid_and_orphaned(self):
        """Mixed requirements: some with valid parents, some orphaned."""
        reqs = [
            self._make_req("SYS-001"),
            self._make_req("REQ-001", parent_id="SYS-001"),   # valid
            self._make_req("REQ-002", parent_id="SYS-999"),   # orphaned
        ]
        result = self.engine.link_r2r(reqs)
        self.assertTrue(result['has_r2r'])
        self.assertIn("SYS-001", result['hierarchy'])
        self.assertEqual(len(result['orphaned_parents']), 1)
        self.assertEqual(result['cycles'], [])


if __name__ == '__main__':
    unittest.main()
