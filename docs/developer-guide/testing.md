# Testing & Quality Assurance Suite

JanusTrace is deployed in environments where false positives in traceability reporting can lead to compliance failures (e.g., FAA or FDA audits). Consequently, the testing suite is rigorously designed to prove the structural soundness, accuracy, and performance of the tool under extreme conditions.

---

## 1. Automated Unit & Integration Testing (Pytest)

The core logic of JanusTrace is protected by a comprehensive suite of Pytest-driven unit and integration tests.

### 1.1 Running the Protocol
Before submitting any Pull Request, developers must ensure the `pytest` suite passes with zero failures. It is recommended to use the verbose flag and generate a coverage report.

```bash
# Install testing dependencies
pip install pytest pytest-cov

# Execute the test suite with coverage
python -m pytest tests/ -v --cov=trace_framework
```

### 1.2 Core Test Modules
*   **`test_engine.py`**: The most critical test module. It isolates the `TraceabilityEngine` and validates:
    *   One-to-One and One-to-Many generic trace linkages.
    *   Waiver dictionary injection and correct status mutation (e.g., `REQ_MISSING` -> `WAIVED`).
    *   R2R Hierarchy tree creation.
    *   Directed cyclic graph analysis (Cycle detection in Parent-Child relationships).
*   **`test_report_gen.py`**: Validates the Output layer. It creates mock engine payloads and asserts that the resulting `.json` and `.html` files contain the expected data structures without syntax errors.
*   **`test_config_validator.py`**: Validates the ingestion layer. It feeds intentionally malformed `yaml` configurations into the validator to assert that specific `ConfigValidationError` exceptions are correctly raised and formatted.
*   **`test_hdl_parser.py`**: Validates the language parsers against complex string manipulations, ensuring comments are extracted correctly while ignoring literal strings that happen to look like tags.

---

## 2. Real-World Simulation (Test Fixtures)

The `tests/` directory contains numbered fixture folders (`01_SystemVerilog_Example`, `06_Missing_Req`, etc.). These are integration tests designed to simulate realistic user environments.

### 2.1 Anatomy of a Fixture
A standard fixture contains:
1.  **A `requirements.csv`**: The baseline input matrix.
2.  **A source directory**: Several mock `.c`, `.sv`, or `.py` files containing edge-case trace tags (e.g., tags overlapping multiple lines, tags embedded in disabled code blocks).
3.  **A validation script (Optional)**: A `.py` script that utilizes the CLI to run against the fixture and asserts the stdout/stderr matches expectations.

### 2.2 Notable Stress Scenarios
*   **Test 13 / 14 (Document Trace)**: These fixtures assert the performance and accuracy of navigating dual-document traceability (scanning a secondary Excel test matrix instead of raw source code). Test 14 specifically generates 10,000+ mock requirements to stress the DataFrame merging architecture.

---

## 3. Performance & UI Responsiveness

Because parsing large codebases (e.g., a massive Linux Kernel fork) is an I/O and CPU bound task, UI responsiveness is a primary testing criterion.

*   **The Freeze Test**: When analyzing massive repositories, the `gui_app.py` must retain responsiveness. Tests manually simulate long `os.walk` operations to ensure the CustomTkinter event loop is not starved.
*   **Memory Profiling**: Iterative `.append` operations in lists during the regex compilation phase are actively monitored to prevent RAM exhaustion.

---

## 4. Continuous Integration (CI) and Automation

JanusTrace adheres to strict Continuous Integration paradigms.

### 4.1 GitHub Actions Workflow
Every push to the main branch and every Pull Request triggers the workflow defined in `.github/workflows/python-tests.yml`. Placed in a pristine Ubuntu container, this workflow:
1.  Installs the latest dependencies.
2.  Executes `pylint` against the core engine (failing the build if the score drops below 9.0).
3.  Executes `pytest` and uploads the artifact logs.

### 4.2 Integrating JanusTrace into Your Own CI/CD
JanusTrace is meant to be run headlessly in user CI pipelines (Jenkins, GitLab CI).

**Headless Execution Syntax**:
```bash
python main.py \
    --config config/default.yaml \
    --reqs requirements.csv \
    --source ./src \
    --output ./ci-reports \
    --json
```

**Automated Build Auditing**:
Developers can use the generated `traceability_report.json` to halt production deployments if compliance slips:
```python
import json, sys

with open('./ci-reports/traceability_report.json') as f:
    data = json.load(f)
    coverage = data['stats']['coverage_percentage']
    
    if coverage < 100.0:
        print(f"FATAL: Traceability dropped to {coverage}%")
        sys.exit(1)
```

By ensuring zero unexpected errors in the test suite, we guarantee JanusTrace remains a trustworthy audit tool.

[Back to Home](../index.md)
