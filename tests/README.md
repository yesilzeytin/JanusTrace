# JanusTrace Examples

This directory contains executable examples demonstrating various features and error handling capabilities of JanusTrace.

## Usage
Run the global runner scripts to execute all examples and generate reports in `test_outputs/`:
- **Windows**: `run_all.bat`
- **Linux**: `./run_all.sh` (ensure `chmod +x` is set on scripts)

## Examples List
1.  **SystemVerilog**: Basic usage with .sv files.
2.  **VHDL**: Basic usage with .vhd files.
3.  **Mixed Language**: Combined SV/VHDL project.
4.  **Nested Hierarchy**: Recursive scanning of source folders.
5.  **Custom Rules**: Using `custom_rules.yaml` for non-standard delimiters.
6.  **Missing Req**: Report shows `REQ_MISSING` for unimplemented requirements.
7.  **Orphan Trace**: Report shows `TRACE_ORPHAN` for tags with no matching requirement.
8.  **Invalid Req**: Report shows `REQ_INVALID` for malformed IDs in CSV.
9.  **Invalid Trace**: Report shows `TRACE_INVALID` for malformed tags in code (strict mode).
10. **All Errors**: A chaos scenario with multiple error types.
11. **IBM DOORS**: Variable digit lengths (e.g., `ID-1` vs `ID-135`) and extra CSV columns. Note that this tool scans ALL rows, not just 'Requirement' type. If you have exported DOORS data or similar, you would need to filter the data before running JanusTrace, which can be easily done with Excel or similar tools.
