import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from trace_framework.ui.cli import load_config
from trace_framework.parsers.doc_parsers import CSVParser, DocumentTracer
from trace_framework.core.engine import TraceabilityEngine
from trace_framework.utils.report_gen import ReportGenerator

def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(test_dir, 'custom_rules.yaml')
    target_reqs_path = os.path.join(test_dir, 'target_reqs.csv')
    source_reqs_path = os.path.join(test_dir, 'source_reqs.csv')

    config = load_config(config_path)

    # 1. Parse target requirements (HLRs)
    target_parser = CSVParser(config)
    reqs = target_parser.parse_requirements(target_reqs_path)

    # 2. Parse traces from the source document (LLRs)
    doc_tracer = DocumentTracer(config)
    traces = doc_tracer.scan_for_tags(source_reqs_path, 'Parent_HLR', 'ID')

    # 3. Link them together
    engine = TraceabilityEngine()
    results = engine.link(reqs, traces)
    r2r = engine.link_r2r(reqs)
    results['r2r'] = r2r

    # 4. Assert correctness
    stats = results['stats']
    assert stats['total_reqs'] == 3, f"Expected 3 reqs, got {stats['total_reqs']}"
    assert stats['covered_reqs'] == 2, f"Expected 2 covered reqs, got {stats['covered_reqs']}"
    assert stats['missing_reqs'] == 1, f"Expected 1 missing req, got {stats['missing_reqs']}"
    assert stats['orphaned_traces'] == 1, f"Expected 1 orphaned trace, got {stats['orphaned_traces']}"
    assert stats['invalid_traces_count'] == 1, f"Expected 1 invalid trace, got {stats['invalid_traces_count']}"

    print("Test 13 Document Trace validation passed successfully!")

if __name__ == '__main__':
    main()
