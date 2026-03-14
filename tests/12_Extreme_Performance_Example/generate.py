#!/usr/bin/env python3
"""
12_Extreme_Performance_Example: Synthetic large-scale traceability test.

Generates:
  - 2000 synthetic requirements in a CSV file
  - 20 SystemVerilog (.sv) files with trace tags
  - An expected_outcomes.txt describing the deliberate failures

This test is designed to:
  1. Validate JanusTrace performance at scale (thousands of reqs, many files)
  2. Verify that the engine correctly identifies mixed OK/MISSING/ORPHAN outcomes
  3. Serve as a regression baseline for large-project workflows

Usage:
    cd tests/12_Extreme_Performance_Example
    python generate.py          # Create all test artifacts
    python run_test.py          # Run the scan and verify outcomes
    python run_test.py --clean  # Remove generated artifacts
"""

import os
import random
import csv
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TOTAL_REQS          = 2000   # Total rows in requirements CSV
FILES               = 20     # Number of .sv files to generate
MISSING_PCT         = 0.08   # 8% of reqs deliberately not tagged in code
ORPHAN_COUNT        = 30     # Tags in code that reference non-existent req IDs
MULTI_PARENT_COUNT  = 50     # Reqs that have a Parent (R2R hierarchy)
INVALID_REQ_COUNT   = 15     # Requirements with malformed IDs in CSV

random.seed(42)   # Reproducible output

OUT_DIR   = os.path.dirname(os.path.abspath(__file__))
SRC_DIR   = os.path.join(OUT_DIR, "src_generated")
REQ_CSV   = os.path.join(OUT_DIR, "requirements_generated.csv")
YAML_CFG  = os.path.join(OUT_DIR, "custom_rules.yaml")
EXPECTED  = os.path.join(OUT_DIR, "expected_outcomes.txt")

def generate():
    os.makedirs(SRC_DIR, exist_ok=True)

    # -----------------------------------------------------------------------
    # 1. Determine which req IDs will be MISSING (no code tag)
    # -----------------------------------------------------------------------
    all_req_ids   = [f"XTRACE-{i:04d}" for i in range(1, TOTAL_REQS + 1)]
    missing_count = int(TOTAL_REQS * MISSING_PCT)
    missing_ids   = set(random.sample(all_req_ids, missing_count))
    covered_ids   = [r for r in all_req_ids if r not in missing_ids]

    # Assign parents to MULTI_PARENT_COUNT of the covered IDs
    # (only to reqs 501+ so the parents 1-100 are always top-level SYS reqs)
    sys_reqs       = all_req_ids[:100]   # SYS-level: XTRACE-0001…XTRACE-0100
    child_pool     = all_req_ids[100:]   # all derived reqs
    r2r_children   = random.sample(child_pool, MULTI_PARENT_COUNT)
    r2r_parent_map = {child: random.choice(sys_reqs) for child in r2r_children}

    # Add invalid requirement IDs to the CSV (format violation)
    bad_req_ids = [f"XTRACE_BAD_{i:02d}" for i in range(1, INVALID_REQ_COUNT + 1)]

    # -----------------------------------------------------------------------
    # 2. Write requirements CSV
    # -----------------------------------------------------------------------
    with open(REQ_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Description", "Category", "Parent"])
        categories = ["Timing", "Safety", "Reset", "Data", "Control",
                      "Memory", "Interface", "Power", "Clock", "Integrity"]
        for req_id in all_req_ids:
            cat    = random.choice(categories)
            desc   = f"The design shall satisfy constraint {req_id} under {cat} domain."
            parent = r2r_parent_map.get(req_id, "")
            writer.writerow([req_id, desc, cat, parent])

        # Write the invalid ones too
        for bad_id in bad_req_ids:
            writer.writerow([bad_id, "This requirement has an invalid ID format.", "Safety", ""])

    print(f"[generate] Written {TOTAL_REQS + INVALID_REQ_COUNT} requirements to {REQ_CSV}")

    # -----------------------------------------------------------------------
    # 3. Distribute covered IDs across FILES, then write .sv files
    # -----------------------------------------------------------------------
    random.shuffle(covered_ids)
    chunks = [covered_ids[i::FILES] for i in range(FILES)]   # round-robin split

    # Orphan tags: IDs that ARE valid format but NOT in the requirements CSV
    # Using range 9001-9999 which is outside the 1-2000 requirements range
    orphan_ids = [f"XTRACE-{9000 + i:04d}" for i in range(1, ORPHAN_COUNT + 1)]

    for file_idx in range(FILES):
        sv_path = os.path.join(SRC_DIR, f"block_{file_idx:02d}.sv")
        file_ids = chunks[file_idx] if file_idx < len(chunks) else []

        # Sprinkle some orphans into the first two files
        extras = []
        if file_idx == 0:
            extras += [(oid, "orphan") for oid in orphan_ids[:15]]
        elif file_idx == 1:
            extras += [(oid, "orphan") for oid in orphan_ids[15:]]

        with open(sv_path, "w", encoding="utf-8") as sv:
            sv.write(f"// Synthetic RTL block {file_idx:02d} — auto-generated for JanusTrace extreme test\n")
            sv.write(f"// This file is NOT synthesizable or functionally meaningful.\n\n")
            sv.write(f"module block_{file_idx:02d} (\n")
            sv.write(f"    input  logic clk,\n")
            sv.write(f"    input  logic rstn,\n")
            sv.write(f"    output logic out_{file_idx:02d}\n")
            sv.write(f");\n\n")

            for req_id in file_ids:
                sv.write(f"    // [{ req_id }] Implements requirement {req_id}\n")
                sv.write(f"    logic sig_{req_id.replace('-','_')};\n")
                sv.write(f"    assign sig_{req_id.replace('-','_')} = clk & rstn;\n\n")

            for tag_id, tag_type in extras:
                if tag_type == "orphan":
                    sv.write(f"    // [{tag_id}] Orphan: references a non-existent requirement\n")
                    sv.write(f"    logic orphan_{tag_id.replace('-','_')};\n\n")

            sv.write(f"\n    assign out_{file_idx:02d} = 1'b0;\n")
            sv.write(f"endmodule\n")

    print(f"[generate] Written {FILES} .sv files to {SRC_DIR}/")

    # -----------------------------------------------------------------------
    # 4. Write YAML config
    # -----------------------------------------------------------------------
    yaml_content = """# Configuration for the extreme performance test
regex_rules:
  id_pattern: "XTRACE-\\\\d{4}"
tags:
  start_token: "["
  end_token: "]"
columns:
  id: ID
  description: Description
  category: Category
  parent: Parent
languages:
  - name: SystemVerilog
    enabled: true
    extensions: [sv, svh]
    line_comment: "//"
    block_comment_start: "/*"
    block_comment_end: "*/"
"""
    with open(YAML_CFG, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"[generate] Written config to {YAML_CFG}")

    # -----------------------------------------------------------------------
    # 5. Write expected outcome file (ground truth for run_test.py)
    # -----------------------------------------------------------------------
    with open(EXPECTED, "w", encoding="utf-8") as f:
        f.write("# Expected outcomes for the JanusTrace extreme performance test\n")
        f.write(f"# Generated by generate.py — do not edit by hand\n\n")
        f.write(f"TOTAL_REQS={TOTAL_REQS + INVALID_REQ_COUNT}\n")
        f.write(f"MISSING_COUNT={len(missing_ids)}\n")
        f.write(f"ORPHAN_COUNT={ORPHAN_COUNT}\n")
        f.write(f"INVALID_REQ_COUNT={INVALID_REQ_COUNT}\n")
        f.write(f"R2R_PARENTS=100\n")   # sys_reqs are the potential parents
        f.write(f"R2R_CHILDREN={MULTI_PARENT_COUNT}\n")
        f.write(f"\n# Missing requirement IDs (REQ_MISSING in report)\n")
        for mid in sorted(missing_ids):
            f.write(f"MISSING={mid}\n")
        f.write(f"\n# Orphan tag IDs (TRACE_ORPHAN in report)\n")
        for oid in orphan_ids:
            f.write(f"ORPHAN={oid}\n")
        f.write(f"\n# Malformed requirement IDs (REQ_INVALID in report)\n")
        for bt in bad_req_ids:
            f.write(f"INVALID={bt}\n")

    print(f"[generate] Written expected outcomes to {EXPECTED}")
    print(f"\n[generate] Done. Summary:")
    print(f"  Total valid requirements : {TOTAL_REQS}")
    print(f"  Malformed requirements   : {INVALID_REQ_COUNT}")
    print(f"  Covered valid reqs       : {TOTAL_REQS - len(missing_ids)}")
    print(f"  Missing reqs             : {len(missing_ids)}  (~{MISSING_PCT*100:.0f}%)")
    print(f"  Orphan tags              : {ORPHAN_COUNT}")
    print(f"  R2R children             : {MULTI_PARENT_COUNT}")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        import shutil
        for path in [SRC_DIR, REQ_CSV, YAML_CFG, EXPECTED]:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"[clean] Removed {path}")
            elif os.path.isfile(path):
                os.remove(path)
                print(f"[clean] Removed {path}")
    else:
        generate()
