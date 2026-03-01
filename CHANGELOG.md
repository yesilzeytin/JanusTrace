# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Config Validation**: The `ConfigValidator` class now validates `yaml` configurations early and provides specific `ERROR` or `WARNING` messages before scans operate.
- **Multiple Requirements**: The CLI (`--reqs` allowing `nargs='+'`) and GUI (multi-select dialog) now support accumulating requirements from multiple CSV/Excel files in a single scan.
- **Progress Bar**: The GUI features a thread-safe progress bar that provides real-time progress updates during the scanning process.
- **Recent Projects**: The GUI automatically saves and loads the most recently used configurations and paths (`config/recent.json`).
- **Interactive Reports**: The HTML report was completely rewritten to include sortable headers, a status-filter dropdown, and text search powered by vanilla JavaScript. The report data is securely embedded via JSON within the HTML document.
- **JSON Export**: Added standalone JSON generation for CI/CD integration. Use the `--json` flag on CLI.
- **Coverage Percentage**: Requirement coverage is now calculated by the `TraceabilityEngine` and displayed prominently on UI and HTML reports.
- **Comprehensive API Exports**: `__all__` exports and module-level docstrings have been added to all `__init__.py` files.
- **`pytest` Support**: Added a comprehensive `test_*.py` suite with 45 passing tests runnable seamlessly via standard `pytest`.

### Changed
- **Parser De-duplication**: Substantial code size reduction by moving `ExcelParser` and `CSVParser` logic into a shared `TabularDocumentParser` base class.
- **CLI Extension Scanning**: CLI and GUI logic unified to derive scanned file extensions from the configuration file (`languages` mapping) rather than hardcoded `.sv` / `.vhd` lists.
- **Logging Integration**: All components now use Python's built-in `logging` module instead of standard `print()` statements for diagnostic output.
- **GUI Thread-Safety**: The GUI logger uses tkinter's `after()` method to marshal logs directly into the main thread, solving critical lock/freeze issues.
- **Timestamped Outputs**: Reports now generate filenames appended with timestamps (e.g., `report_20261022_150000.html`) to prevent accidental overwrites.
- **Dependencies**: Sub-dependencies formally pinned sequentially (`pandas>=2.0,<3.0`, `PyYAML>=6.0,<7.0`) in `requirements.txt`.
- **CI/CD Actions**: Updated GitHub Actions (`release.yml`) to Node20-compatible `v4` steps and set baseline Python array test versions to 3.11.

### Fixed
- **Duplicate Decorators**: Fixed duplicated `@staticmethod` definitions leading to IDE/runtime errors in `trace_framework/ui/config_helper.py`.
- **Duplicate Methods**: Fixed ambiguous duplicate implementations of `generate_regex_logic()` in `trace_framework/ui/gui_app.py`.
- **Bare Exceptions**: Fixed problematic bare `except:` clauses globally, replacing them with `except Exception:`.
- **Graceful Failure**: The `cli.py:load_config()` method now correctly raises custom exceptions mapped cleanly in the `main` loop, eliminating hard `sys.exit(1)` behavior under the hood.
- **Default Languages Compatibility**: Fixed missing configurations in `trace_framework/parsers/hdl_parsers.py` providing backward-compatible definitions when none exist.
- **Incorrect Extensions List**: Fixed `custom_config.yaml` misattributing `.sv` to C/C++ entries.
