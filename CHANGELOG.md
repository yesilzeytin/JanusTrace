# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] - 2026-03-14

### Added
- **Requirements Waiver Manager**: Introduced a separate GUI window to load unresolved issues (missing/invalid) and mark them as waived with a reason. Generates a `valid_waivers.json` which can be re-loaded for future scans.
- **Traceability Waivers**: The engine now handles a mapping of IDs to waiver reasons, accurately updating coverage and reflecting a "WAIVED" status in reports.
- **Waiver Metrics**: The HTML report summary cards now include a "Waived Items" count with a unique blue visual theme.
- **Static Documentation Hub**: Added a comprehensive multi-page Markdown documentation suite (`docs/`) and a Python generator (`scripts/generate_docs.py`). Features premium responsive styling, automated image scaling, and soft-shadow UI polish.
- **Document-on-Document Tracing**: Added the ability to link two spreadsheets together (e.g. HLR to LLR) using a dedicated "Document" trace mode in CLI or GUI.
- **R2R Hierarchy**: Collapsible parent-child tree view in the HTML report with automatic cycle and orphan detection.
- **Security Audit**: Implemented HTML escaping for all user-supplied requirement IDs, descriptions, and contexts to mitigate XSS risks in generated reports.
- **Code Quality**: Performed a mass Pylint audit, reaching a finalized codebase score of **9.87/10** for core modules.
- **AI Attribution**: Updated branding to acknowledge assistance from Gemini 3.1 Pro & Claude 4.6 Sonnet on Google Antigravity.
- **Professional User/Dev Guides**: Completely rewritten documentation for DO-254/ISO 26262 compliance contexts, including threading models and testing fixtures.

### Changed
- **HTML Layout**: Switched the report to a modern Tabbed interface separating the Requirements Matrix, Trace Log, and R2R Hierarchy.
- **GUI UX**: Standardized colors (Hufflepuff mustard yellow) and added ToolTips to all complex controls.
- **Invalid ID Handling**: Enhanced the engine to keep track of malformed requirement IDs separately instead of mixing them with missing traces.

### Fixed
- **Duplicate Detection**: Fixed an issue where duplicate Requirement IDs in the spreadsheet were incorrectly inflating coverage stats.
- **Icon Visibility**: Improved Windows taskbar and titlebar icon loading reliability using deferred `after()` calls.
- **Encoding Fallback**: Source code parsers now fallback to `latin-1` if `utf-8` decoding fails, improving robustness against non-standard file encodings.

## [1.1.0] - 2026-03-10

### Added
- **Config Validation**: The `ConfigValidator` class now validates `yaml` configurations early.
- **Multiple Requirements**: Support for accumulating requirements from multiple CSV/Excel files.
- **Progress Bar**: Thread-safe UI updates during scan.
- **Interactive Reports**: Rewritten HTML report with sorting, filtering, and search.
- **JSON Export**: Added standalone JSON generation for CI/CD integration.
- **Coverage Percentage**: Prominent coverage math in stats.

### Fixed
- **GUI Thread-Safety**: Fixed critical lock issues by marshalling logs via `after()`.
- **Timestamped Outputs**: Reports no longer overwrite each other.
