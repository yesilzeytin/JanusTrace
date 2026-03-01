"""
Report generator for requirement traceability results.

Produces three output formats:
  1. Interactive HTML report with embedded JSON data, sorting, filtering, search
  2. Standalone JSON data file for programmatic consumption
  3. All reports use timestamped filenames to prevent overwrites
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates traceability reports in HTML and JSON formats.

    Args:
        output_dir: Directory to write report files into.
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_html(
        self,
        data: Dict[str, Any],
        filename: str = "traceability_report.html",
    ) -> str:
        """Generate an interactive HTML traceability report.

        The report embeds all data as JSON and renders it client-side
        using vanilla JavaScript, providing sorting, filtering, and
        search capabilities.

        Args:
            data: Traceability results from TraceabilityEngine.link().
            filename: Base filename for the report.

        Returns:
            Absolute path to the generated HTML file.
        """
        # Build a timestamped filename to prevent overwrites
        timestamped_name = self._timestamped_filename(filename)
        report_data = self._serialize_report_data(data)
        html_content = self._build_interactive_html(report_data)

        output_path = os.path.join(self.output_dir, timestamped_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info("HTML report written to %s", output_path)
        return output_path

    def generate_json(
        self,
        data: Dict[str, Any],
        filename: str = "traceability_report.json",
    ) -> str:
        """Generate a standalone JSON traceability report.

        Args:
            data: Traceability results from TraceabilityEngine.link().
            filename: Base filename for the JSON file.

        Returns:
            Absolute path to the generated JSON file.
        """
        timestamped_name = self._timestamped_filename(filename)
        report_data = self._serialize_report_data(data)

        output_path = os.path.join(self.output_dir, timestamped_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        logger.info("JSON report written to %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_report_data(data: Dict[str, Any]) -> dict:
        """Convert engine results into a JSON-serializable dictionary."""
        matrix_rows = []
        for item in data['matrix']:
            req = item['req']
            traces_list = [
                {
                    "file": t.source_file,
                    "line": t.line_number,
                    "context": t.context,
                }
                for t in item['traces']
            ]
            matrix_rows.append({
                "id": req.id,
                "description": req.description,
                "category": req.category or "",
                "status": item['status'],
                "traces": traces_list,
            })

        invalid_reqs_list = [
            {
                "id": r.id,
                "description": r.description,
                "error": r.error_message or "",
            }
            for r in data['invalid_reqs']
        ]

        orphans_list = [
            {
                "tag": t.req_id,
                "file": t.source_file,
                "line": t.line_number,
                "context": t.context,
            }
            for t in data['orphans']
        ]

        invalid_traces_list = [
            {
                "tag": t.req_id,
                "file": t.source_file,
                "line": t.line_number,
                "context": t.context,
                "error": t.error_message or "",
            }
            for t in data['invalid_traces']
        ]

        return {
            "generated_at": datetime.now().isoformat(),
            "stats": data['stats'],
            "matrix": matrix_rows,
            "invalid_reqs": invalid_reqs_list,
            "orphans": orphans_list,
            "invalid_traces": invalid_traces_list,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _timestamped_filename(base_filename: str) -> str:
        """Insert a timestamp before the file extension.

        Example: 'report.html' -> 'report_20260301_194500.html'
        """
        name, ext = os.path.splitext(base_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_{timestamp}{ext}"

    # ------------------------------------------------------------------
    # HTML Template
    # ------------------------------------------------------------------

    @staticmethod
    def _build_interactive_html(report_data: dict) -> str:
        """Build a fully self-contained interactive HTML report.

        The HTML embeds the report data as a JSON blob and renders it
        with vanilla JavaScript, providing:
          - Summary statistics with coverage percentage
          - Requirements matrix with sort, filter, and search
          - Code traces table with orphan and invalid markers
          - Color-coded status indicators
        """
        json_blob = json.dumps(report_data, indent=2)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traceability Report</title>
    <style>
        :root {{
            --color-ok: #1e3a29;           /* Dark green for OK */
            --color-ok-text: #82e0aa;      /* Light green text */
            --color-missing: #4a1c1d;      /* Dark red for missing */
            --color-missing-text: #f5b7b1; /* Light red text */
            --color-orphan: #4d4420;       /* Dark yellow/brown for orphan */
            --color-orphan-text: #f9e79f;  /* Light yellow text */
            --color-invalid-req: #333333;  /* Dark gray for invalid req */
            --color-invalid-req-text: #cccccc;
            --color-invalid-trace: #4a1c1d;
            --color-invalid-trace-text: #f5b7b1;
            
            --color-bg: #1b1b1b;           /* Hufflepuff dark background */
            --color-surface: #262626;      /* Slightly lighter surface */
            --color-border: #404040;       /* Border color */
            --color-text: #e0e0e0;         /* Primary text */
            --color-muted: #888888;        /* Muted text */
            --color-primary: #fcba03;      /* Hufflepuff mustard yellow */
            --color-primary-dark: #b58502; /* Hover color for primary */
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: var(--color-text);
            background: var(--color-bg);
            padding: 24px;
            line-height: 1.5;
        }}

        h1 {{
            font-size: 1.8rem;
            margin-bottom: 8px;
        }}

        .timestamp {{
            color: var(--color-muted);
            font-size: 0.85rem;
            margin-bottom: 24px;
        }}

        /* --------- Stats Cards --------- */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 1.6rem;
            font-weight: 700;
        }}
        .stat-card .label {{
            font-size: 0.8rem;
            color: var(--color-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-card.coverage {{
            border-color: var(--color-primary);
            background: #332b00;
        }}
        .stat-card.coverage .value {{
            color: var(--color-primary);
            font-size: 2rem;
        }}

        /* --------- Legend --------- */
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 24px;
            font-size: 0.85rem;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .legend-swatch {{
            width: 14px;
            height: 14px;
            border-radius: 3px;
            border: 1px solid var(--color-border);
            flex-shrink: 0;
        }}

        /* --------- Toolbar --------- */
        .toolbar {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            margin-bottom: 12px;
        }}
        .toolbar input[type="text"] {{
            padding: 6px 12px;
            border: 1px solid var(--color-border);
            border-radius: 6px;
            font-size: 0.9rem;
            width: 260px;
            background: var(--color-surface);
            color: var(--color-text);
        }}
        .toolbar select {{
            padding: 6px 10px;
            border: 1px solid var(--color-border);
            border-radius: 6px;
            font-size: 0.9rem;
            background: var(--color-surface);
            color: var(--color-text);
        }}

        /* --------- Tables --------- */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 32px;
            font-size: 0.9rem;
        }}
        th, td {{
            border: 1px solid var(--color-border);
            padding: 10px 12px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: var(--color-surface);
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}
        th:hover {{
            background: #333333;
        }}
        th .sort-arrow {{
            margin-left: 4px;
            font-size: 0.7rem;
            color: var(--color-muted);
        }}
        tr.ok              {{ background: var(--color-ok); color: var(--color-ok-text); }}
        tr.req_missing     {{ background: var(--color-missing); color: var(--color-missing-text); }}
        tr.trace_orphan    {{ background: var(--color-orphan); color: var(--color-orphan-text); }}
        tr.req_invalid     {{ background: var(--color-invalid-req); color: var(--color-invalid-req-text); }}
        tr.trace_invalid   {{ background: var(--color-invalid-trace); color: var(--color-invalid-trace-text); }}

        code {{
            background: rgba(255,255,255,0.1);
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.85em;
        }}

        h2 {{
            margin-bottom: 8px;
            font-size: 1.3rem;
        }}

        .no-results {{
            text-align: center;
            padding: 24px;
            color: var(--color-muted);
            font-style: italic;
        }}
    </style>
</head>
<body>

<h1>Traceability Report</h1>
<div class="timestamp" id="timestamp"></div>

<!-- Stats -->
<div class="stats-grid" id="stats-grid"></div>

<!-- Legend -->
<div class="legend">
    <div class="legend-item"><span class="legend-swatch" style="background:var(--color-ok)"></span> OK: Covered</div>
    <div class="legend-item"><span class="legend-swatch" style="background:var(--color-missing)"></span> REQ_MISSING: Not in code</div>
    <div class="legend-item"><span class="legend-swatch" style="background:var(--color-orphan)"></span> TRACE_ORPHAN: No matching req</div>
    <div class="legend-item"><span class="legend-swatch" style="background:var(--color-invalid-req)"></span> REQ_INVALID: Bad ID format</div>
    <div class="legend-item"><span class="legend-swatch" style="background:var(--color-invalid-trace)"></span> TRACE_INVALID: Bad tag format</div>
</div>

<!-- Requirements Matrix -->
<h2>Requirements Matrix</h2>
<div class="toolbar">
    <input type="text" id="search-req" placeholder="Search by ID or description..." oninput="renderReqTable()">
    <select id="filter-status" onchange="renderReqTable()">
        <option value="ALL">All Statuses</option>
        <option value="OK">OK</option>
        <option value="REQ_MISSING">Missing</option>
        <option value="REQ_INVALID">Invalid</option>
    </select>
</div>
<table id="req-table">
    <thead>
        <tr>
            <th onclick="sortReqTable('id')">ID <span class="sort-arrow" id="sort-id"></span></th>
            <th onclick="sortReqTable('description')">Description <span class="sort-arrow" id="sort-description"></span></th>
            <th onclick="sortReqTable('status')">Status <span class="sort-arrow" id="sort-status"></span></th>
            <th>Source Files</th>
        </tr>
    </thead>
    <tbody id="req-tbody"></tbody>
</table>

<!-- Code Traces -->
<h2>Code Traces</h2>
<div class="toolbar">
    <input type="text" id="search-trace" placeholder="Search traces..." oninput="renderTraceTable()">
</div>
<table id="trace-table">
    <thead>
        <tr>
            <th>Tag</th>
            <th>File</th>
            <th>Line</th>
            <th>Status</th>
            <th>Context</th>
        </tr>
    </thead>
    <tbody id="trace-tbody"></tbody>
</table>

<!-- Embedded JSON data -->
<script type="application/json" id="report-data">
{json_blob}
</script>

<script>
// ========================
// Data Loading
// ========================
const DATA = JSON.parse(document.getElementById('report-data').textContent);

// ========================
// Stats Rendering
// ========================
(function renderStats() {{
    const s = DATA.stats;
    document.getElementById('timestamp').textContent = 'Generated: ' + DATA.generated_at;

    const grid = document.getElementById('stats-grid');
    const cards = [
        {{ label: 'Coverage', value: s.coverage_percentage + '%', cls: 'coverage' }},
        {{ label: 'Total Reqs', value: s.total_reqs }},
        {{ label: 'Valid Reqs', value: s.valid_reqs }},
        {{ label: 'Covered', value: s.covered_reqs }},
        {{ label: 'Missing', value: s.missing_reqs }},
        {{ label: 'Orphaned Traces', value: s.orphaned_traces }},
        {{ label: 'Invalid Reqs', value: s.invalid_reqs_count }},
        {{ label: 'Invalid Traces', value: s.invalid_traces_count }},
    ];
    grid.innerHTML = cards.map(c =>
        `<div class="stat-card ${{c.cls || ''}}">
            <div class="value">${{c.value}}</div>
            <div class="label">${{c.label}}</div>
        </div>`
    ).join('');
}})();

// ========================
// Requirements Table
// ========================
let reqSortKey = 'id';
let reqSortAsc = true;

function getAllRows() {{
    // Combine matrix + invalid reqs for unified view
    const rows = DATA.matrix.map(r => ({{ ...r }}));
    DATA.invalid_reqs.forEach(r => {{
        rows.push({{ id: r.id, description: r.description, status: 'REQ_INVALID', traces: [], error: r.error }});
    }});
    return rows;
}}

function sortReqTable(key) {{
    if (reqSortKey === key) {{
        reqSortAsc = !reqSortAsc;
    }} else {{
        reqSortKey = key;
        reqSortAsc = true;
    }}
    renderReqTable();
}}

function renderReqTable() {{
    const search = document.getElementById('search-req').value.toLowerCase();
    const filterStatus = document.getElementById('filter-status').value;

    let rows = getAllRows();

    // Filter
    if (filterStatus !== 'ALL') {{
        rows = rows.filter(r => r.status === filterStatus);
    }}
    if (search) {{
        rows = rows.filter(r =>
            r.id.toLowerCase().includes(search) ||
            r.description.toLowerCase().includes(search)
        );
    }}

    // Sort
    rows.sort((a, b) => {{
        const va = (a[reqSortKey] || '').toString().toLowerCase();
        const vb = (b[reqSortKey] || '').toString().toLowerCase();
        if (va < vb) return reqSortAsc ? -1 : 1;
        if (va > vb) return reqSortAsc ? 1 : -1;
        return 0;
    }});

    // Sort arrows
    ['id', 'description', 'status'].forEach(k => {{
        const el = document.getElementById('sort-' + k);
        if (el) el.textContent = (reqSortKey === k) ? (reqSortAsc ? '▲' : '▼') : '';
    }});

    // Render
    const tbody = document.getElementById('req-tbody');
    if (rows.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="4" class="no-results">No matching requirements</td></tr>';
        return;
    }}
    tbody.innerHTML = rows.map(r => {{
        const css = r.status.toLowerCase();
        const files = r.traces && r.traces.length > 0
            ? r.traces.map(t => t.file + ' (Line ' + t.line + ')').join('<br>')
            : (r.error || '-');
        return `<tr class="${{css}}">
            <td>${{r.id}}</td>
            <td>${{r.description}}</td>
            <td>${{r.status}}</td>
            <td>${{files}}</td>
        </tr>`;
    }}).join('');
}}

renderReqTable();

// ========================
// Traces Table
// ========================
function renderTraceTable() {{
    const search = document.getElementById('search-trace').value.toLowerCase();
    const tbody = document.getElementById('trace-tbody');

    // Combine orphans and invalid traces
    let rows = [];
    DATA.orphans.forEach(t => {{
        rows.push({{ tag: t.tag, file: t.file, line: t.line, status: 'TRACE_ORPHAN', context: t.context, error: '' }});
    }});
    DATA.invalid_traces.forEach(t => {{
        rows.push({{ tag: t.tag, file: t.file, line: t.line, status: 'TRACE_INVALID', context: t.context, error: t.error }});
    }});

    // Filter
    if (search) {{
        rows = rows.filter(r =>
            r.tag.toLowerCase().includes(search) ||
            r.file.toLowerCase().includes(search) ||
            r.context.toLowerCase().includes(search)
        );
    }}

    if (rows.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="5" class="no-results">No orphan or invalid traces</td></tr>';
        return;
    }}

    tbody.innerHTML = rows.map(r => {{
        const css = r.status.toLowerCase();
        const ctx = r.error
            ? `<code>${{r.context}}</code><br><small>${{r.error}}</small>`
            : `<code>${{r.context}}</code>`;
        return `<tr class="${{css}}">
            <td>${{r.tag}}</td>
            <td>${{r.file}}</td>
            <td>${{r.line}}</td>
            <td>${{r.status}}</td>
            <td>${{ctx}}</td>
        </tr>`;
    }}).join('');
}}

renderTraceTable();
</script>

</body>
</html>'''
