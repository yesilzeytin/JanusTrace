# Usage Modes: Source Code vs Document

JanusTrace is uniquely capable of working in two distinct "Flows": Code-to-Requirement and Requirement-to-Requirement.

## Trace Mode: Source Code

This is the standard mode for engineering. It scans your directory of HDL or Software source files for comment-based tags.

-   **Input**: A folder path.
-   **Logic**: Parses every file matching the configured extensions. Extracts tags from comments.
-   **Use Case**: Verifying that your implementation satisfies your requirements.

## Trace Mode: Document

This mode allows you to link two requirement documents together (e.g., tracing a Low-Level Requirement to a High-Level Requirement).

-   **Input**: A secondary CSV or Excel file.
-   **Required Fields**:
    -   **Link Column Name**: The column in your source document that contains parent IDs (e.g., `HLR_Ref`).
    -   **Source ID Column**: The column identifying the child requirement itself.
-   **Logic**: Treats each row in the spreadsheet as a "trace point".
-   **Use Case**: Document alignment, system-level traceability audits, and LLR-to-HLR mapping.

### Mode Summary Table
![GUI Requirement Level Trace](../images/gui02.png)

| Feature | Source Code Mode | Document Mode |
|---|---|---|
| Primary Input | Directory | File (.xlsx/.csv) |
| Scanning Target | Comments (`// [ID]`) | Spreadsheet Cells |
| Context Extraction | Filename & Line Number | Source ID & Column Value |
| Regex Applied | Yes | Yes (to cell content) |

## Requirement-to-Requirement (R2R) Deep Dive

When `parent` column is configured, the engine performs secondary linking.

### Data Model
- **Req A** (Parent) -> **Req B** (Child)
- **Req B** (Parent) -> **Req C** (Child)

### Logic Engine Highlights:
- **Cycle Detection**: The system uses a DFS-based cycle detector. If Requirement A points to B, and B points to A, both are flagged with a **! CYCLE** badge in the report and excluded from the tree to prevent infinite recursion in the UI.
- **Orphanage**: If a child references a parent ID that doesn't exist in the current requirement set, it is marked as an **Orphan Parent**.

### Document Mode Example
Imagine tracing High-Level (HLR) to Low-Level (LLR):
1.  **Requirement File**: `HLR_List.csv`
2.  **Source "Code" File**: `LLR_List.csv`
3.  **Link Column**: Set to `HLR_Parent` (the column in LLR file).
4.  **Source ID Column**: Set to `LLR_ID`.

The report will show how many HLRs are satisfied by LLRs, including full coverage percentage math.

[Next: Waiver Management](./waiver-management.md) | [Back to Home](../index.md)
