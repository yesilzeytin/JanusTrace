# Configuration Guide

The behavior of JanusTrace is governed by a YAML configuration file. While the GUI provides a **Visual Builder** to generate this for you, understanding the underlying structure is key to advanced usage.

## YAML Structure Breakdown

### `regex_rules`
Defines how the tool identifies requirement IDs.
```yaml
regex_rules:
  id_pattern: (?P<id>REQ\-\d+)
```
-   **id_pattern**: A regular expression. It *must* include a named capture group `(?P<id>...)`.

### `tags`
Defines how the tag is wrapped in source code comments.
```yaml
tags:
  start_token: '['
  end_token: ']'
```
With these settings, the parser looks for `[ID]` inside comments.

### `columns` (Optional)
Maps spreadsheet column headers to requirement attributes.
```yaml
columns:
  id: ID
  description: Description
  category: Category
  parent: Parent  # Enables R2R Hierarchy
```

### `languages`
A list of language definitions that JanusTrace uses to identify where to look for tags.
```yaml
languages:
  - name: SystemVerilog
    enabled: true
    extensions: [sv, svh]
    line_comment: "//"
    block_comment_start: "/*"
    block_comment_end: "*/"
```
You can add your own custom language entry here to support proprietary extensions or niche languages.

## Using the Visual Builder

In the GUI's **Configuration** tab, you can "compose" an ID pattern visually:
1.  **Add Fixed Text**: e.g., "REQ"
2.  **Add Separator**: e.g., "-"
3.  **Add Numeric Field**: Set digit count (e.g., 3 for REQ-001) or variable length.
4.  **Save Config**: Browse to a path and save the resulting YAML.

![Visual Regex Builder](../images/gui01.png)

## Advanced ID Patterns

While the Visual Builder handles standard cases, you can manually edit the YAML for complex scenarios.

### Anchors and Boundaries
Use `\b` to ensure your ID doesn't match a substring of a larger word:
```yaml
id_pattern: \b(?P<id>REQ\-\d+)\b
```

### Negative Lookahead
If you want to exclude specific IDs (e.g., exclude `REQ-000`):
```yaml
id_pattern: \b(?P<id>REQ\-(?!000)\d+)\b
```

## Overlapping File Extensions

If two languages share an extension (e.g., `.h` used by both C and C++), JanusTrace processes them using the *first* configuration in the list that matches the extension.

**Best Practice**: 
1.  Group shared extensions into a generic "C-Style" language entry.
2.  Alternatively, ensure `enabled: true` is only set for the specific language variant you are auditing.

## Manual YAML Editing

You can bypass the GUI entirely and maintain your configuration in Git. 

### Adding Custom Columns
If your spreadsheet has extra columns like "Priority" or "Verification Method", you can map them here:
```yaml
columns:
  id: "Requirement Number" # Matches "Requirement Number" header
  description: "What it does"
```
*Note: Column names are case-sensitive.*

[Next: Usage Modes](./usage-modes.md) | [Back to Home](../index.md)
