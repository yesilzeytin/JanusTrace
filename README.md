# JanusTrace

A requirement-code traceability tool for safety-critical and quality-assured development projects.

Requirement-based development workflows — whether under **DO-178C**, **DO-254**, **ISO 26262**, or similar standards — demand that every requirement can be pointed to somewhere in the source code, and that every code tag corresponds to a real, documented requirement. Keeping that link alive manually, across hundreds of files and thousands of lines, is slow and error-prone. JanusTrace automates this: point it at your requirements spreadsheet and your source directory, and it produces an interactive HTML report showing exactly what is covered, what is missing, and what doesn't belong.

> ⚠️ JanusTrace helps you gather and present traceability evidence — it does not guarantee tool qualification. Your process team is responsible for satisfying the applicable tool qualification criteria (e.g. DO-330, ISO 26262 Part 8). The bundled pytest test suite is intended to significantly support that effort.

---

## Features

- **Parses requirements from Excel (.xlsx/.xls) and CSV files** — configurable column mappings for ID, Description, Category, and Parent
- **Scans source code for trace tags** — comment-based tags in any supported language (e.g. `// [REQ-001]`)
- **Flexible ID pattern matching** — visual regex builder in the GUI, or supply your own regex in a YAML config file
- **Interactive HTML reports** — sortable matrix, status filters, full-text search, coverage percentage, color-coded status rows
- **Requirement-to-Requirement (R2R) hierarchy** — optional `Parent` column links derived requirements to their parents; the report shows a collapsible tree with cycle and orphan detection
- **Orphan + invalid trace detection** — tags that reference non-existent IDs or don't match the configured pattern are flagged separately
- **Duplicate requirement ID warnings** — duplicate rows in the requirements file are detected and excluded from coverage math
- **JSON export** — standalone JSON output for CI/CD pipeline integration
- **Recent projects** — the GUI remembers your last-used paths across sessions
- **Multi-file requirements** — combine requirements from multiple CSVs or Excel files in a single scan
- **CLI and GUI** — run headlessly with `main.py` or use the full GUI with `main_gui.py`

---

## Screenshots

Scan your source files to be traced with your requirements
![GUI Code Trace](docs/images/gui00.png)

Or scan different levels of requirement files to be traced with each other
![GUI Requirement Level Trace](docs/images/gui02.png)

Visual regex generator for any requirement ID format  
![Configuration REGEX generation with GUI](docs/images/gui01.png)

Each report generates a JSON file for "unresolved issues". Just load them to waive anything you want
![Waiver Management](docs/waiver.png)

An example traceability report  
![An example report](docs/images/report00.png)

Searching requirements inside the report  
![Search functionality in report](docs/images/report01.png)

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare your requirements file

Create a CSV or Excel file with at least an `ID` column:

| ID | Description | Category | Parent |
|----|-------------|----------|--------|
| SYS-001 | System shall boot in under 5 seconds | Performance | |
| REQ-001 | Boot sequence shall initialize memory controller | Startup | SYS-001 |
| REQ-002 | Watchdog timer shall be enabled before main loop | Safety | SYS-001 |

The `Parent` column is optional — add it to enable [requirement hierarchy tracking](#requirement-to-requirement-r2r-hierarchy).

### 3. Tag your source code

Inside a comment, wrap the requirement ID with `[` and `]` (configurable):

```systemverilog
// [REQ-001] Initialize memory controller at reset
always_ff @(posedge clk or negedge rstn) begin
    if (!rstn) mem_ctrl_en <= 1'b0;
    else       mem_ctrl_en <= 1'b1;
end
```

```vhdl
-- [REQ-002] Enable watchdog before main loop
watchdog_en <= '1';
```

### 4. Run the GUI

```bash
python main_gui.py
```

Select your config file, requirements file, and source directory — then click **START SCAN**. The HTML report opens automatically when the scan completes.

### 5. Run from the command line

```bash
python main.py --config config/default_rules.yaml \
               --reqs requirements.csv \
               --source src/ \
               --output reports/
```

---

## Two-Document Requirement Tracing

JanusTrace can also link two separate requirements documents together (e.g., Low-Level Requirements (LLR) tracing to High-Level Requirements (HLR)). In the GUI, set **Trace Mode** to **Document**, and select your source CSV/Excel file instead of a source code directory. You will be prompted to enter:
- **Link Column Name:** The column in the source document containing the target requirement IDs (e.g., `HLR_Parent`).
- **Source ID Column:** The column identifying the source requirement, used for logging trace context.

This behaves exactly like source code tracing: missing links, orphans, and malformed tags are all validated and reported identically.

---

## Configuration

Configuration is stored in a YAML file. A default is provided at `config/default_rules.yaml`. The GUI can generate and save configurations using the **Visual Builder** tab.

### Key fields

```yaml
# Regex pattern that requirement IDs must match
regex_rules:
  id_pattern: (?P<id>REQ\-\d+)

# Characters that wrap the ID tag inside comments
tags:
  start_token: '['
  end_token: ']'

# Column names in your requirements file (all optional, shown with defaults)
# columns:
#   id: ID
#   description: Description
#   category: Category
#   parent: Parent        # <-- enables R2R hierarchy tracking

# Languages to scan (enabled/disabled per language)
languages:
  - name: SystemVerilog
    enabled: true
    extensions: [sv, svh]
    line_comment: "//"
    block_comment_start: "/*"
    block_comment_end: "*/"

# Map of specific IDs to waiver reasons
# Typically loaded from a valid_waivers.json file exported by the Waiver Manager
# waivers:
#   REQ-001: "Covered by legacy test results in Document X"
#   REQ-002: "Functionality deprecated but requirement remains active"
```

Use the **Visual Builder** tab in the GUI to compose patterns like `REQ-NNN`, `PROJ-SYS-NNN`, or custom formats without writing regex by hand.

---

## Requirements Waiver Manager

In complex projects, some requirements might be impossible to trace in code (e.g. legacy logic) or represent false positives. JanusTrace provides an integrated **Waiver Manager** to handle these cases professionally:

1. **Scan and Export**: Every time you run a scan, JanusTrace generates an `unresolved_issues.json` file in your output directory.
2. **Open Manager**: Click **Manage Waivers** in the main GUI.
3. **Load and Waive**: Load the `unresolved_issues.json`, check the **Waive?** box for items you wish to ignore, and type a mandatory **Waiver Reason**.
4. **Save**: Export the result as `valid_waivers.json`.
5. **Apply**: Select this file in the **Waivers File** input on the main form for your next scan.

Waived items will appear in **blue** in the HTML report, will not penalize your coverage metrics, and will display your provided reason directly in the requirements matrix.

---

## Language Support
| SystemVerilog | `.sv`, `.svh` | `//` | `/* */` |
| Verilog | `.v`, `.vh` | `//` | `/* */` |
| VHDL | `.vhd`, `.vhdl` | `--` | *(none)* |
| C / C++ | `.c`, `.cpp`, `.h`, `.hpp`, `.cc` | `//` | `/* */` |
| Python | `.py` | `#` | *(none)* |
| Java / C# / Rust | `.java`, `.cs`, `.rs` | `//` | `/* */` |
| MATLAB | `.m` | `%` | `%{ %}` |
| Ada | `.adb`, `.ads` | `--` | *(none)* |

Adding a new language requires only a few lines in the YAML `languages` list — no code changes needed.

---

## Requirement-to-Requirement (R2R) Hierarchy

When your requirements document has a `Parent` column, JanusTrace builds a hierarchy tree that maps high-level system requirements to their derived children.

To enable it, either add a `Parent` column to your spreadsheet, or configure the column name in your YAML:

```yaml
columns:
  parent: Parent   # or whatever your column is named
```

The HTML report will then show a **Requirement Hierarchy (R2R)** section with:
- A collapsible, expandable tree of parent → child relationships
- **Orphaned parent warnings** — a child references a parent ID that doesn't exist in the document
- **Cycle warnings** — circular parent references (e.g. A → B → A) are detected and flagged

---

## Report Overview

The generated HTML report is fully self-contained (no external CDN or network needed) and includes:

| Section | Description |
|---|---|
| **Summary Cards** | Coverage %, total/valid/covered/missing requirement counts, orphaned and invalid trace counts |
| **Requirements Matrix** | One row per requirement — sortable by ID, Description, or Status; filterable by status; text-searchable |
| **Code Traces** | Orphaned tags and malformed tags with their file, line, and context |
| **R2R Hierarchy** | *(shown when Parent column is present)* Expandable tree of requirement parents and their children |

---

## Test Suite

JanusTrace ships with a pytest suite covering the engine, parsers, config validation, report generation, and CLI behavior.

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific module
python -m pytest tests/test_engine.py -v
```

The test suite currently contains **50 passing tests** and was designed with tool qualification (DO-330 / IEC 62304 guidance) in mind.

---

## Project Structure

```
JanusTrace/
├── main.py               # CLI entry point
├── main_gui.py           # GUI entry point
├── JanusTrace.spec       # PyInstaller build spec (Windows exe)
├── config/               # Example YAML configuration files
├── docs/                 # Screenshots and documentation assets
├── tests/                # Pytest test suite (50 tests)
└── trace_framework/
    ├── core/
    │   ├── engine.py     # Traceability engine: link(), link_r2r()
    │   └── models.py     # Requirement and TraceObject dataclasses
    ├── parsers/
    │   ├── doc_parsers.py  # Excel/CSV requirement parsers
    │   └── hdl_parsers.py  # Source code tag scanner
    ├── ui/
    │   ├── gui_app.py    # CustomTkinter GUI (1000+ lines)
    │   └── cli.py        # argparse CLI
    └── utils/
        ├── config_validator.py  # YAML config validation
        ├── regex_builder.py     # Pattern compilation
        └── report_gen.py        # HTML + JSON report generator
```

---

## Building the Windows Executable

```bash
pyinstaller JanusTrace.spec
```

The output EXE will be in `dist/JanusTrace.exe`. The icon, config directory, and all dependencies are bundled automatically.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT License](LICENSE) — Ugur Nezir

---

*This project was built with the assistance of agentic AI tools (Gemini 2.5 Pro & Claude 3.7 Sonnet). All design decisions, architecture choices, and final code review were performed by the author.*
