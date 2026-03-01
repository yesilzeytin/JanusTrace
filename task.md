# JanusTrace Improvement Tasks

## Phase 1 — Critical Bug Fixes
- [ ] **1.1** Fix duplicate `@staticmethod` in [config_helper.py](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/tests/test_config_helper.py)
- [ ] **1.2** Fix duplicate [generate_regex_logic](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/gui_app.py#586-588) method in [gui_app.py](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/gui_app.py)
- [ ] **1.3** Fix broken [test_config_helper.py](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/tests/test_config_helper.py) test (unsupported [prefix](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/tests/test_config_helper.py#12-18) param)
- [ ] **1.4** Fix CLI hardcoded file extensions — use config [languages](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/gui_app.py#681-707) like the GUI does

## Phase 2 — Moderate Issues
- [ ] **2.1** Remove dead code: unused [pattern](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/utils/regex_builder.py#10-58) variable in [config_helper.py](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/tests/test_config_helper.py)
- [ ] **2.2** Remove dead method [generate_from_manual](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/gui_app.py#581-585) in [gui_app.py](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/gui_app.py)
- [ ] **2.3** Fix bare `except` clauses in [gui_app.py](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/gui_app.py) (lines 52, 654)
- [ ] **2.4** Fix [load_config()](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/cli.py#11-18) calling `sys.exit()` — make it raise exceptions instead
- [ ] **2.5** Fix GUI thread safety — marshal [log()](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/ui/gui_app.py#220-223) calls to main thread via `self.after()`
- [ ] **2.6** Reconcile GUI default languages list with [default_rules.yaml](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/config/default_rules.yaml)
- [ ] **2.7** Fix [.sv](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/tests/01_SystemVerilog_Example/src/design.sv) extension listed under C/C++ in [custom_config.yaml](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/config/custom_config.yaml)
- [ ] **2.8** Add coverage percentage calculation to engine stats + report

## Phase 3 — Code Quality & Refactoring
- [ ] **3.1** Refactor [ExcelParser](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/parsers/doc_parsers.py#8-54)/[CSVParser](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/parsers/doc_parsers.py#55-100) to eliminate code duplication
- [ ] **3.2** Replace `print()` with Python `logging` module across all library code
- [ ] **3.3** Add `__all__` exports to [__init__.py](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/trace_framework/__init__.py) files
- [ ] **3.4** Pin dependency versions in [requirements.txt](file:///c:/Users/ugurn/OneDrive/Belgeler/Antigravity%20Projects/JanusTrace%20-%20Copy%20%285%29%20-%20Copy/requirements.txt)
- [ ] **3.5** Update GitHub Actions to use latest action versions (v4)

## Phase 4 — Report & Output Improvements
- [ ] **4.1** Add timestamped report filenames to prevent overwrites
- [ ] **4.2** Add coverage percentage display in HTML report (prominent)
- [ ] **4.3** Add JSON report export alongside HTML

## Phase 5 — Feature Enhancements
- [ ] **5.1** Add config validation at load time with clear error messages
- [ ] **5.2** Support multiple requirements files in a single run
- [ ] **5.3** Add progress bar to GUI scan
- [ ] **5.4** Add "Recent Projects" to GUI (remember last-used paths)
- [ ] **5.5** Enhance GUI Help panel with proper documentation

## Phase 6 — Documentation & CI
- [ ] **6.1** Add CHANGELOG.md
- [ ] **6.2** Add LICENSE file
- [ ] **6.3** Add CONTRIBUTING.md
- [ ] **6.4** Improve docstrings across all modules
- [ ] **6.5** Build pytest-based automated test suite
