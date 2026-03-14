import sys
import os
sys.path.append(os.getcwd())
from trace_framework.parsers.hdl_parsers import SourceCodeParser

def test_language_support():
    print("Testing SourceCodeParser...")

    # 1. Config with contention
    config = {
        'languages': [
            {
                'name': 'LangA',
                'enabled': True,
                'extensions': ['test'],
                'line_comment': '//A',
                'block_comment_start': '/*',
                'block_comment_end': '*/'
            },
            {
                'name': 'LangB',
                'enabled': True,
                'extensions': ['test'],
                'line_comment': '#B',
                'block_comment_start': None,
                'block_comment_end': None
            }
        ],
        'tags': {'start_token': '[', 'end_token': ']'}
    }

    parser = SourceCodeParser(config)

    # Check map
    print("Extension Map:", parser.extension_map.keys())

    test_file_path = os.path.join(os.path.dirname(__file__), 'start.test')
    # Create test file
    with open(test_file_path, 'w') as f:
        f.write("//A [REQ-001] Valid A\n")
        f.write("#B [REQ-002] Valid B\n")
        f.write("/* [REQ-003] Valid Block */\n")
        f.write("//B [REQ-004] Invalid B comment in A file?\n") # Invalid for LangA, invalid for LangB (LangB uses #)

    # Scan
    regex = r"REQ-\d+"
    traces = parser.scan_for_tags(test_file_path, regex)

    found_ids = sorted([t.req_id for t in traces])
    print("Found IDs:", found_ids)

    assert 'REQ-001' in found_ids
    assert 'REQ-002' in found_ids
    assert 'REQ-003' in found_ids
    assert 'REQ-004' not in found_ids # //B is not valid comment start for LangA (//A) or LangB (#B)

    print("SUCCESS: Contention handled, both styles detected.")

    if os.path.exists(test_file_path):
        os.remove(test_file_path)

if __name__ == "__main__":
    test_language_support()
