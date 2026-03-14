# Troubleshooting & FAQ

This page addresses common pitfalls and technical troubleshooting steps for JanusTrace.

## Common Issues

### 1. "No traces found" in Source Directory
**Symptoms**: The scan completes successfully, but the report shows 0 traces and all requirements are marked as "Missing".
- **Check File Extensions**: Ensure your configuration's `languages` list includes the extensions of your files (e.g., `.sv`, `.c`).
- **Check Tag Format**: Verify that your tags match both the `regex_rules` and the `tags` tokens. If your pattern is `REQ-\d+` and your tokens are `[` and `]`, then `// [REQ-001]` will match, but `// REQ-001` will not.
- **Check Search Directory**: Double-check that you selected the correct root folder. JanusTrace scans recursively, but the root must be accurate.

### 2. Character Encoding Errors
**Symptoms**: "Warning: Could not decode file X with utf-8".
- **Explanation**: JanusTrace defaults to UTF-8. If a file contains non-standard characters (often in legacy VHDL or C comments), it may fail to decode.
- **Solution**: The tool has a built-in fallback to `latin-1`. If you still see errors, consider converting your source files to UTF-8 using an editor like VS Code or Notepad++.

### 3. GUI Freezing during Scan
**Symptoms**: The progress bar stops moving, and the "Not Responding" windows alert appears.
- **Cause**: This usually happens if the main thread is blocked by a synchronous operation. 
- **Solution**: JanusTrace v1.2.0 uses a separate thread for the engine. If the freeze persists, it may be due to the OS file system lock (especially on network drives). Try running the scan on a local SSD.

### 4. Excel Parsing Failures
**Symptoms**: "Error: Header 'ID' not found in spreadsheet".
- **Check Column Mapping**: Ensure the `columns:` section in your YAML matches your spreadsheet exactly. Headers are case-sensitive.
- **Hidden Rows**: JanusTrace ignores hidden rows in some versions. Ensure your IDs are on visible, non-filtered rows.

## Frequently Asked Questions (FAQ)

### Q: Can I use one config for multiple projects?
Yes. It is recommended to keep a `default_rules.yaml` in your project root and share it with your team to ensure consistent traceability metrics.

### Q: How do I handle overlapping requirement IDs?
If you have multiple documents with conflicting IDs (e.g., two REQ-001s), we recommend using a prefix in the configuration (e.g., `(?P<id>SYS-REQ-\d+)`) or splitting the scans.

### Q: Does JanusTrace store my source code?
No. JanusTrace is a local-only tool. It reads your files into memory, extracts matches, and discards the pointers. Nothing is uploaded to a cloud.

[Back to Home](../index.md)
