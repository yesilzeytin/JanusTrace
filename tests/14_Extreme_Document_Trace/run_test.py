import os
import sys
import time

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

    if not os.path.exists(target_reqs_path):
        import generate
        generate.main()

    print("Running Extreme Document Trace Performance Test...")
    start_time = time.time()

    config = load_config(config_path)

    target_parser = CSVParser(config)
    reqs = target_parser.parse_requirements(target_reqs_path)

    doc_tracer = DocumentTracer(config)
    traces = doc_tracer.scan_for_tags(source_reqs_path, 'Parent_HLR', 'ID')

    parse_time = time.time() - start_time
    print(f"Parsing OK ({parse_time:.4f}s): {len(reqs)} reqs, {len(traces)} traces")

    # 3. Link them together
    link_start = time.time()
    engine = TraceabilityEngine()
    results = engine.link(reqs, traces)
    link_time = time.time() - link_start
    print(f"Linking OK ({link_time:.4f}s)")

    # Assertions based on data generation patterns
    stats = results['stats']
    assert stats['total_reqs'] == 500, f"Expected 500 reqs, got {stats['total_reqs']}"
    assert stats['covered_reqs'] == 450, f"Expected 450 covered, got {stats['covered_reqs']}"
    assert stats['missing_reqs'] == 50, f"Expected 50 missing, got {stats['missing_reqs']}"
    assert stats['orphaned_traces'] == 10, f"Expected 10 orphaned, got {stats['orphaned_traces']}"
    assert stats['invalid_traces_count'] == 15, f"Expected 15 invalid, got {stats['invalid_traces_count']}"

    print("Performance & Validation PASSED!")

if __name__ == '__main__':
    main()
