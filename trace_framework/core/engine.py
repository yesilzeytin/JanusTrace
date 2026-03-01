"""
Core traceability logic for the JanusTrace framework.

This module provides the TraceabilityEngine, which acts as the central
hub for reconciling parsed requirements with discovered source code traces.
"""
from typing import List, Dict, Any
from trace_framework.core.models import Requirement, TraceObject, ValidationStatus

class TraceabilityEngine:
    """
    Links Requirements to Source Code Traces and calculates coverage statistics.
    
    The engine matches traces to requirements based on their IDs and
    identifies orphaned traces (tags with no matching requirement) as well
    as missing requirements (requirements with no tags in the code).
    """
    def __init__(self):
        pass

    def link(self, requirements: List[Requirement], traces: List[TraceObject]) -> Dict[str, Any]:
        """
        Compares requirements against traces to produce a traceability matrix.

        Args:
            requirements: A list of Requirement objects parsed from documentation.
            traces: A list of TraceObject objects discovered in source code.

        Returns:
            A dictionary containing:
            - 'matrix': List of dicts mapping each requirement to its linked traces and status ('OK' or 'REQ_MISSING').
            - 'orphans': List of traces that did not match any requirement ID.
            - 'invalid_reqs': List of requirements with invalid format errors.
            - 'invalid_traces': List of traces with formatting validation errors.
            - 'stats': A dictionary containing counts and coverage_percentage.
        """
        # Map req_id to Requirement object for O(1) lookup
        req_map = {req.id: req for req in requirements}
        
        # Map req_id to list of TraceObjects
        trace_map = {}
        orphans = []
        invalid_traces = []
        
        for trace in traces:
            if trace.status == ValidationStatus.INVALID_FORMAT:
                invalid_traces.append(trace)
                continue
                
            if trace.req_id in req_map:
                if trace.req_id not in trace_map:
                    trace_map[trace.req_id] = []
                trace_map[trace.req_id].append(trace)
            else:
                orphans.append(trace)
                
        # Build the matrix
        matrix = []
        invalid_reqs = []
        
        for req_id, req in req_map.items():
            if req.status == ValidationStatus.INVALID_FORMAT:
                invalid_reqs.append(req)
                continue
                
            linked_traces = trace_map.get(req_id, [])
            
            # Determine status
            if linked_traces:
                status = "OK" 
            else:
                status = "REQ_MISSING" 
            
            matrix.append({
                "req": req,
                "traces": linked_traces,
                "status": status
            })
            
        # Calculate coverage statistics
        covered_count = len([m for m in matrix if m['status'] == 'OK'])
        valid_req_count = len(requirements) - len(invalid_reqs)
        missing_count = len([m for m in matrix if m['status'] == 'REQ_MISSING'])

        # Coverage percentage: covered / valid requirements (avoid division by zero)
        coverage_pct = (covered_count / valid_req_count * 100) if valid_req_count > 0 else 0.0

        return {
            "matrix": matrix,
            "orphans": orphans,
            "invalid_reqs": invalid_reqs,
            "invalid_traces": invalid_traces,
            "stats": {
                "total_reqs": len(requirements),
                "valid_reqs": valid_req_count,
                "covered_reqs": covered_count,
                "missing_reqs": missing_count,
                "orphaned_traces": len(orphans),
                "invalid_reqs_count": len(invalid_reqs),
                "invalid_traces_count": len(invalid_traces),
                "coverage_percentage": round(coverage_pct, 1)
            }
        }
