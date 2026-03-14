"""
Core traceability logic for the JanusTrace framework.

This module provides the TraceabilityEngine, which acts as the central
hub for reconciling parsed requirements with discovered source code traces.
"""
from typing import List, Dict, Any
from trace_framework.core.models import Requirement, TraceObject, ValidationStatus
import logging

logger = logging.getLogger(__name__)

class TraceabilityEngine:
    """
    Links Requirements to Source Code Traces and calculates coverage statistics.

    The engine matches traces to requirements based on their IDs and
    identifies orphaned traces (tags with no matching requirement) as well
    as missing requirements (requirements with no tags in the code).
    """
    def __init__(self):
        pass

    def link(
        self,
        requirements: List[Requirement],
        traces: List[TraceObject],
        waivers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Compares requirements against traces to produce a traceability matrix.

        Args:
            requirements: A list of Requirement objects parsed from documentation.
            traces: A list of TraceObject objects discovered in source code.
            waivers: Optional dictionary mapping item IDs to a waiver reason.

        Returns:
            A dictionary containing:
            - 'matrix': List of dicts mapping each requirement to its linked traces and status ('OK' or 'REQ_MISSING').
            - 'orphans': List of traces that did not match any requirement ID.
            - 'invalid_reqs': List of requirements with invalid format errors.
            - 'invalid_traces': List of traces with formatting validation errors.
            - 'waived_items': List of traces and requirements that were waived.
            - 'stats': A dictionary containing counts and coverage_percentage.
        """
        if waivers is None:
            waivers = {}
        # Map req_id to Requirement object for O(1) lookup.
        # Detect and warn about duplicate IDs — the first occurrence wins.
        req_map = {}
        duplicate_reqs = []
        for req in requirements:
            if req.id in req_map:
                logger.warning(
                    "Duplicate requirement ID '%s' found at %s line %s. "
                    "Only the first occurrence will be used.",
                    req.id, req.source_file, req.line_number
                )
                duplicate_reqs.append(req)
            else:
                req_map[req.id] = req

        # Map req_id to list of TraceObjects
        trace_map = {}
        orphans = []
        invalid_traces = []
        waived_items = []

        for trace in traces:
            if trace.status == ValidationStatus.INVALID_FORMAT:
                if trace.req_id in waivers:
                    trace.status = ValidationStatus.WAIVED
                    trace.waiver_reason = waivers[trace.req_id]
                    waived_items.append(trace)
                else:
                    invalid_traces.append(trace)
                continue

            if trace.req_id in req_map:
                if trace.req_id not in trace_map:
                    trace_map[trace.req_id] = []
                trace_map[trace.req_id].append(trace)
            else:
                if trace.req_id in waivers:
                    trace.status = ValidationStatus.WAIVED
                    trace.waiver_reason = waivers[trace.req_id]
                    waived_items.append(trace)
                else:
                    orphans.append(trace)

        # Build the matrix
        matrix = []
        invalid_reqs = []

        for req_id, req in req_map.items():
            if req.status == ValidationStatus.INVALID_FORMAT:
                if req_id in waivers:
                    req.status = ValidationStatus.WAIVED
                    req.waiver_reason = waivers[req_id]
                    waived_items.append(req)
                else:
                    invalid_reqs.append(req)
                continue

            linked_traces = trace_map.get(req_id, [])

            # Determine status
            if linked_traces:
                status = "OK"
            elif req_id in waivers:
                status = "WAIVED"
                req.status = ValidationStatus.WAIVED
                req.waiver_reason = waivers[req_id]
                waived_items.append(req)
            else:
                status = "REQ_MISSING"

            matrix.append({
                "req": req,
                "traces": linked_traces,
                "status": status
            })

        # Calculate coverage statistics
        covered_count = len([m for m in matrix if m['status'] == 'OK'])
        # valid_req_count excludes invalid-format, duplicate reqs, AND waived requirements
        waived_reqs_count = len([m for m in matrix if m['status'] == 'WAIVED'])
        valid_req_count = len(requirements) - len(invalid_reqs) - len(duplicate_reqs) - waived_reqs_count
        missing_count = len([m for m in matrix if m['status'] == 'REQ_MISSING'])

        # Coverage percentage: covered / valid requirements (avoid division by zero)
        coverage_pct = (covered_count / valid_req_count * 100) if valid_req_count > 0 else 0.0

        return {
            "matrix": matrix,
            "orphans": orphans,
            "invalid_reqs": invalid_reqs,
            "invalid_traces": invalid_traces,
            "duplicate_reqs": duplicate_reqs,
            "waived_items": waived_items,
            "stats": {
                "total_reqs": len(requirements),
                "valid_reqs": valid_req_count,
                "covered_reqs": covered_count,
                "missing_reqs": missing_count,
                "orphaned_traces": len(orphans),
                "invalid_reqs_count": len(invalid_reqs),
                "invalid_traces_count": len(invalid_traces),
                "duplicate_reqs_count": len(duplicate_reqs),
                "waived_items_count": len(waived_items),
                "coverage_percentage": round(coverage_pct, 1)
            }
        }
    def link_r2r(self, requirements: List[Requirement]) -> Dict[str, Any]:
        """
        Builds a requirement-to-requirement (R2R) hierarchy from parent_id fields.

        Identifies which requirements have parent IDs, constructs the parent→children
        map, detects orphaned parent references, and detects circular dependencies.

        Args:
            requirements: A list of Requirement objects (same list passed to link()).

        Returns:
            A dictionary containing:
            - 'hierarchy': Dict mapping each parent_id to its list of child req IDs.
            - 'orphaned_parents': List of req IDs whose parent_id doesn't exist.
            - 'cycles': List of lists, each being a cycle path (e.g. ['A','B','A']).
            - 'has_r2r': Boolean, True if any requirement has a parent_id defined.
        """
        # Build set of all valid requirement IDs for O(1) orphan detection
        all_ids = {req.id for req in requirements if req.status.value == "VALID"}

        # Build the parent -> children map
        hierarchy: Dict[str, List[str]] = {}
        orphaned_parents = []

        for req in requirements:
            if not req.parent_id:
                continue
            parent_id = req.parent_id
            if parent_id not in all_ids:
                orphaned_parents.append({
                    "child_id": req.id,
                    "missing_parent_id": parent_id
                })
            else:
                if parent_id not in hierarchy:
                    hierarchy[parent_id] = []
                hierarchy[parent_id].append(req.id)

        # Detect cycles using iterative DFS
        # Build child -> parent map for traversal
        child_to_parent = {
            req.id: req.parent_id
            for req in requirements
            if req.parent_id and req.parent_id in all_ids
        }

        cycles = []
        visited_global = set()

        for start_id in child_to_parent:
            if start_id in visited_global:
                continue
            # Walk the chain from start_id upward
            path = []
            visited_chain = {}
            current = start_id
            while current and current not in visited_global:
                if current in visited_chain:
                    # Found a cycle — extract just the cycle portion
                    cycle_start_index = path.index(current)
                    cycle = path[cycle_start_index:] + [current]
                    cycles.append(cycle)
                    break
                visited_chain[current] = len(path)
                path.append(current)
                current = child_to_parent.get(current)

            visited_global.update(path)

        has_r2r = any(req.parent_id for req in requirements)

        return {
            "hierarchy": hierarchy,
            "orphaned_parents": orphaned_parents,
            "cycles": cycles,
            "has_r2r": has_r2r,
        }

