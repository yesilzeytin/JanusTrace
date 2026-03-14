# Contributing to JanusTrace

JanusTrace is built and maintained as an enterprise-grade compliance and specific systems traceability tool. Because our end-users operate in rigorous, safety-critical environments (DO-254, ISO 26262), the stability, reliability, and accuracy of JanusTrace itself must be beyond reproach.

We welcome contributions from the community—whether adding support for bespoke software languages, fixing graphical anomalies, or optimizing parsing concurrency. This guide outlines our stringent, but necessary, contribution standards.

---

## 1. Code Quality & Formatting Standards

To minimize technical debt and ensure long-term maintainability, all contributions must adhere to the following conventions:

### 1.1 Python Code Assessment (Pylint)
*   **Mandatory Threshold**: JanusTrace aggressively enforces Pylint standards. All core logic modules (`trace_framework/core/`, `parsers/`, `utils/`) must pass with a Pylint score of **9.8/10** or higher. UI components (`trace_framework/ui/`) have slightly relaxed metrics but must still achieve **> 9.0/10** due to standard Tkinter constraints.
*   **Variable Naming**: Strict `snake_case` for variables/functions and `PascalCase` for classes. Avoid abstract acronyms (e.g., use `requirement_index` over `ri`).
*   **Magic Numbers**: Absolutely no magic numbers in parsing logic. All configuration defaults, indexing thresholds, or regex constants must be documented and declared at the top of the module or embedded in `default_rules.yaml`.

### 1.2 Documentation & Type Hinting
*   **Docstrings**: We strictly follow the **Google Python Style Guide** for docstrings. Every module, class, and public function *must* have a comprehensive docstring describing its arguments, return values, and explicit exceptions raised.
*   **Type Hinting**: All new function signatures must leverage Python's `typing` library. E.g., `def parse(self, filepath: str) -> List[Requirement]:`. This ensures static analysis tools like `mypy` can proactively catch bugs.

---

## 2. Multi-Threading & GUI Safety

The JanusTrace GUI (`main_gui.py` and `trace_framework/ui/gui_app.py`) is primarily built using CustomTkinter. 

### The Master Rule of GUI Updates
**Never update a Tkinter/CustomTkinter widget from a background thread.**
When running heavy I/O tasks (like recursively parsing thousands of C++ files), the operation *must* run on a secondary thread (e.g., `threading.Thread`) to keep the main event loop responsive.

If the background thread needs to update the GUI (e.g., logging a message or moving a progress bar), it must marshal the execution back to the main thread via the CustomTkinter `.after(ms, callback)` method. 
*Example implementation can be seen in the `gui_app.py` `log()` and `set_progress()` methods.* Failure to adhere to this will cause unpredictable application deadlocks.

---

## 3. Extending the Application Framework

### 3.1 Adding Language Parsers
JanusTrace's language parser (`HDLParser`) relies on static regex mapping defined in `default_rules.yaml`. To add support for a new programming language (e.g., Rust, Go, Ada):
1.  **Modify YAML**: Add your file extensions and comment styles to the `languages` array in `default_rules.yaml`.
2.  **Visual Builder**: Update the predefined options in the Visual Regex Builder loop if new complex character matching is required.
3.  **Exception Parsing**: If your chosen language supports non-standard block comments (like nested or multiline macro blocks), you MUST extend `hdl_parsers.py` with specific AST-level extraction rather than relying exclusively on sequential line reading.

### 3.2 Adding Report Modifiers
The interactive UI of the Traceability Report is generated natively in `report_gen.py`. If you contribute a new HTML view (like a Data Visualization graph), ensure:
*   The logic relies exclusively on **Vanilla JavaScript (ES6)**.
*   No external dependencies, CDNs, or frameworks (No React, Vue, jQuery) are injected. The HTML report must remain 100% portable and capable of running on air-gapped forensic terminals.

---

## 4. The Pull Request Workflow

1.  **Open an Issue**: Always open a designated Issue ticket mapping out the bug or proposed feature before writing code.
2.  **Branching Strategy**: Fork the repository. Create a descriptive branch (e.g., `feature/ada-parser` or `bugfix/r2r-cycle-crash`).
3.  **Implement & Test**: Write your implementation. Before submission, you *must* run the Pytest suite (see [Testing Guide](./testing.md)).
4.  **Local Pylint Check**: Execute `python -m pylint trace_framework` locally and resolve any `C-`, `R-`, or `W-` class warnings.
5.  **Submit PR**: Open your Pull Request. Your ticket must include screenshots of the GUI (if visually modified) or snippets of the HTML report changes. The maintainers will rigorously audit performance overhead manually before merging.

## 5. Documentation Maintenance

JanusTrace documentation is authored in Markdown within the `docs/` directory and compiled into a static HTML site for distribution.

### 5.1 Authoring Rules
- **Formatting**: Always use standard GitHub Flavored Markdown.
- **Paths**: When linking to other documentation pages, use a relative `.md` suffix (e.g., `[Link](./other.md)`). The generator will automatically convert these to `.html`.
- **Images**: Reference images in `docs/images/`.

### 5.2 Generating the HTML Site
After modifying any Markdown files, you must regenerate the HTML site to verify visual consistency:
1. **Source the Environment**: Ensure `markdown` is installed (`pip install markdown`).
2. **Execute Generator**:
   ```bash
   python scripts/generate_docs.py
   ```
3. **Audit**: Open `docs_html/index.html` and verify that all headings, tables, and images render correctly without layout overflows.

---

[Back to Home](../index.md)
