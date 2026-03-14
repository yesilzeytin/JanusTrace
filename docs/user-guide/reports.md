# Navigating the Traceability Report

The JanusTrace HTML report is a fully self-contained, interactive Single Page Application (SPA). It is generated dynamically at the end of every scan and is designed to allow engineers, quality assurance teams, and auditors to audit traceability evidence efficiently without requiring any backend web server.

---

## 1. The Global Overview Dashboard

At the very top of the report, a dashboard provides an instant, high-level snapshot of project health and traceability maturity.

### 1.1 Key Performance Indicators (KPIs)
*   **Total Reqs**: The absolute number of requirements parsed from your input documents.
*   **Valid Reqs**: The number of requirements that successfully passed structural validation against your configurations.
*   **Covered**: The subset of valid requirements explicitly linked to at least one trace tag in the source code.
*   **Missing**: Valid requirements lacking any implementation trace.
*   **Orphaned Traces**: Trace tags found in the code that do not correspond to any valid requirement ID.
*   **Invalid Reqs / Invalid Reqs**: Items that failed regex validation and thus cannot be processed.
*   **Waived Items**: Requirements that were explicitly skipped via the `valid_waivers.json` configuration.

![Traceability Report Dashboard](../images/report00.png)

### 1.2 Coverage Metric
The **Coverage Percentage** is the most critical metric. It is calculated as:
`(Covered + Waived) / Valid Reqs * 100`
This metric is visually emphasized. A coverage score of 100% signifies complete traceability compliance for the active scan scope.

---

## 2. Interactive Report Views

The report is partitioned into three specialized tabs, providing different lenses through which to view the traceability data.

### 2.1 The Requirements Matrix
This is the primary interface for exploring traceability status. It lists every parsed requirement alongside its resolution.

**Features**:
*   **Dynamic Filtering**: A dropdown menu allows instant filtering by specific statuses (e.g., viewing only `Missing` or `Waived` requirements).
*   **Real-time Search**: A high-performance text input filters the entire matrix instantaneously by Requirement ID or Description keywords.
*   **Multi-column Sorting**: Clicking any column header (ID, Description, Status) sorts the matrix alphabetically ascending or descending.
*   **Deep Linking (Context Extraction)**: For `Covered` requirements, the "Details / Source Files" column lists the exact absolute file paths and line numbers where the trace was discovered. 

![Search and Filter functionality](../images/report01.png)

### 2.2 The Trace Log
The Trace Log acts as an audit trail for code anomalies. It strictly displays traces that were successfully located in the source code, but failed correlation.

**Trace Scenarios**:
*   **TRACE_ORPHAN**: A tag like `[REQ-001]` was discovered embedded in the source code, but `REQ-001` does not exist in the source Requirements CSV. This frequently indicates legacy code, typos in the tag, or deprecated requirements that were deleted from documentation but not removed from code.
*   **TRACE_INVALID**: A tag was found, but it violates the strict regex pattern rules defined in your YAML configuration.
*   **Context Previews**: The Trace Log provides a raw code snippet (the `Context` column) showing exactly what text surrounded the anomalous tag, dramatically speeding up debugging in large codebases.

### 2.3 The R2R Hierarchy Tree
*Note: This advanced feature tab only appears if a `Parent` column was provided in your requirements matrix.*

The Requirement-to-Requirement (R2R) Hierarchy tab provides a macroscopic view of system decomposition.
*   **Expandable Tree View**: Requirements are grouped under their designated parent. Clicking the directional arrows expands or collapses sub-requirements.
*   **Automated Audit Warnings**: JanusTrace actively analyzes the hierarchical graph and warns you of structural flaws:
    *   **Cycles Detected**: Alerted when a requirement is its own ancestor (e.g., A -> B -> C -> A), which structurally invalidates trace logic.
    *   **Missing Parents (Orphans)**: Alerted when a child declares a parent ID that does not exist in the parsed requirement scope.

---

## 3. Data Extraction and Portability

While the HTML interface is designed for human consumption, JanusTrace ensures your data remains machine-accessible.

### 3.1 Embedded JSON Payload
The entire dataset powering the interactive HTML report is embedded directly into the HTML file as a static `<script type="application/json">` block. 
This means you can easily write custom Python or JavaScript tools to parse the generated `.html` files and extract the raw data for custom dashboards, metrics aggregation, or database ingestion.

### 3.2 System Exits and CI/CD
For automated pipelines, JanusTrace evaluates the coverage metrics before termination. If `Covered + Waived` does not equal `Valid Reqs`, or if there are any orphaned traces, the tool exits with custom failure codes (e.g., `Exit Code 2` or `Exit Code 3`), automatically halting Jenkins/GitLab CI pipelines to prevent unverified code deployment.

[Next: Troubleshooting](./troubleshooting.md) | [Back to Home](../index.md)
