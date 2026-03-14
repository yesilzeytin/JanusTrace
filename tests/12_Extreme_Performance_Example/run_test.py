#!/usr/bin/env python3
"""
run_test.py — Extreme performance test runner and outcome verifier.

Runs a JanusTrace scan against the generated artifacts and compares the
report stats / orphan / missing lists against the expected_outcomes.txt
ground truth produced by generate.py.

Usage:
    python run_test.py          # Run scan + verify
    python run_test.py --clean  # Delegate to generate.py --clean
    python run_test.py --regen  # Re-generate fixtures then run

Can also be discovered and run by pytest:
    pytest tests/12_Extreme_Performance_Example/run_test.py -v
"""

import os
import sys
import json
import time
import subprocess
import re

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.join(THIS_DIR, "..", "..")
GENERATE   = os.path.join(THIS_DIR, "generate.py")
REQ_CSV    = os.path.join(THIS_DIR, "requirements_generated.csv")
SRC_DIR    = os.path.join(THIS_DIR, "src_generated")
YAML_CFG   = os.path.join(THIS_DIR, "custom_rules.yaml")
EXPECTED_F = os.path.join(THIS_DIR, "expected_outcomes.txt")
REPORT_DIR = os.path.join(THIS_DIR, "reports_generated")

sys.path.insert(0, ROOT_DIR)


def _load_expected():
    """Parse expected_outcomes.txt into a dict."""
    expected = {"MISSING": set(), "ORPHAN": set(), "INVALID": set()}
    with open(EXPECTED_F, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key in ("TOTAL_REQS", "MISSING_COUNT", "ORPHAN_COUNT",
                           "INVALID_REQ_COUNT", "R2R_PARENTS", "R2R_CHILDREN"):
                    expected[key] = int(val)
                elif key in ("MISSING", "ORPHAN", "INVALID"):
                    expected[key].add(val)
    return expected


def _run_scan():
    """Run the JanusTrace scan programmatically using the public API."""
    from trace_framework.ui.cli import load_config
    from trace_framework.utils.config_validator import ConfigValidator
    from trace_framework.utils.regex_builder import RegexBuilder
    from trace_framework.parsers.doc_parsers import CSVParser
    from trace_framework.parsers.hdl_parsers import SourceCodeParser
    from trace_framework.core.engine import TraceabilityEngine
    from trace_framework.utils.report_gen import ReportGenerator

    config = load_config(YAML_CFG)
    ConfigValidator.validate_or_raise(config)

    # Parse requirements
    parser = CSVParser(config)
    reqs   = parser.parse_requirements(REQ_CSV)

    # Scan source files
    src_parser = SourceCodeParser(config)
    pattern    = RegexBuilder(config).compile_pattern()
    exts       = tuple(f".{e}" for e in src_parser.extension_map.keys())

    traces = []
    for fname in os.listdir(SRC_DIR):
        if fname.lower().endswith(exts):
            traces += src_parser.scan_for_tags(os.path.join(SRC_DIR, fname), pattern)

    # Link
    engine  = TraceabilityEngine()
    results = engine.link(reqs, traces)
    r2r     = engine.link_r2r(reqs)
    results["r2r"] = r2r

    # Generate report
    os.makedirs(REPORT_DIR, exist_ok=True)
    gen = ReportGenerator(output_dir=REPORT_DIR)
    report_path = gen.generate_json(results)
    return results, report_path


# ---------------------------------------------------------------------------
# pytest-compatible test functions
# ---------------------------------------------------------------------------

def _ensure_fixtures():
    """Generate fixtures if they don't exist yet."""
    if not os.path.exists(REQ_CSV) or not os.path.exists(SRC_DIR):
        print("[run_test] Fixtures not found — running generate.py ...")
        subprocess.run([sys.executable, GENERATE], check=True, cwd=THIS_DIR)


def test_scan_completes_within_timeout():
    """Scan of 2000 reqs + 20 files must complete in under 60 seconds."""
    _ensure_fixtures()
    t0 = time.time()
    results, _ = _run_scan()
    elapsed = time.time() - t0
    print(f"[run_test] Scan completed in {elapsed:.2f}s")
    assert elapsed < 60.0, f"Scan took {elapsed:.1f}s — exceeds 60s threshold"


def test_total_requirement_count():
    """Engine must parse exactly 2000 requirements."""
    _ensure_fixtures()
    results, _ = _run_scan()
    expected = _load_expected()
    actual   = results["stats"]["total_reqs"]
    assert actual == expected["TOTAL_REQS"], \
        f"Expected {expected['TOTAL_REQS']} reqs, got {actual}"


def test_missing_requirements_match_expected():
    """REQ_MISSING set in the report must match the expected missing IDs."""
    _ensure_fixtures()
    results, _ = _run_scan()
    expected   = _load_expected()

    actual_missing = {
        m["req"].id
        for m in results["matrix"]
        if m["status"] == "REQ_MISSING"
    }
    exp_missing = expected["MISSING"]

    extra   = actual_missing - exp_missing
    missing = exp_missing - actual_missing
    assert not extra,   f"Unexpected REQ_MISSING ids: {sorted(extra)[:10]}"
    assert not missing, f"Expected REQ_MISSING not found: {sorted(missing)[:10]}"


def test_orphan_count():
    """Number of TRACE_ORPHAN entries must match expected orphan count."""
    _ensure_fixtures()
    results, _ = _run_scan()
    expected   = _load_expected()
    actual     = results["stats"]["orphaned_traces"]
    assert actual == expected["ORPHAN_COUNT"], \
        f"Expected {expected['ORPHAN_COUNT']} orphans, got {actual}"


def test_invalid_req_count():
    """Number of REQ_INVALID entries must match expected invalid req count."""
    _ensure_fixtures()
    results, _ = _run_scan()
    expected   = _load_expected()
    actual     = results["stats"]["invalid_reqs_count"]
    assert actual == expected["INVALID_REQ_COUNT"], \
        f"Expected {expected['INVALID_REQ_COUNT']} invalid reqs, got {actual}"


def test_r2r_hierarchy_exists():
    """R2R data must be present and have non-zero hierarchy when Parent column is used."""
    _ensure_fixtures()
    results, _ = _run_scan()
    r2r = results.get("r2r", {})
    assert r2r.get("has_r2r"), "Expected R2R data to be present"
    assert len(r2r.get("hierarchy", {})) > 0, "Expected non-empty hierarchy"


def test_coverage_is_reasonable():
    """Coverage should be between 85% and 99% (8% deliberate missing, some wiggle)."""
    _ensure_fixtures()
    results, _ = _run_scan()
    pct = results["stats"]["coverage_percentage"]
    assert 85.0 <= pct <= 99.0, f"Coverage {pct}% outside expected 85–99% range"


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if "--clean" in sys.argv:
        subprocess.run([sys.executable, GENERATE, "--clean"], cwd=THIS_DIR)
        sys.exit(0)

    if "--regen" in sys.argv:
        subprocess.run([sys.executable, GENERATE, "--clean"], cwd=THIS_DIR)
        subprocess.run([sys.executable, GENERATE], cwd=THIS_DIR)

    _ensure_fixtures()

    print("\n[run_test] Running all verification checks...")
    tests = [
        test_scan_completes_within_timeout,
        test_total_requirement_count,
        test_missing_requirements_match_expected,
        test_orphan_count,
        test_invalid_req_count,
        test_r2r_hierarchy_exists,
        test_coverage_is_reasonable,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__} — {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__} — {e}")
            failed += 1

    print(f"\n[run_test] {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
