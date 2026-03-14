"""
Main Application GUI for JanusTrace.
"""
# pylint: disable=wrong-import-position,wrong-import-order,too-many-instance-attributes,too-many-statements,too-many-branches,too-many-locals,broad-exception-caught,attribute-defined-outside-init,too-many-public-methods,missing-function-docstring

import os
import sys
import threading
import json
import webbrowser
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Backend imports (Mock or Real)
# We will use subprocess to run the actual logic to keep GUI responsive
# and avoid complex threading with the existing classes for now,
# OR import classes directly. Direct import is better for distribution.
from trace_framework.ui.cli import load_config
from trace_framework.utils.regex_builder import RegexBuilder
from trace_framework.parsers.doc_parsers import ExcelParser, CSVParser, DocumentTracer
from trace_framework.parsers.hdl_parsers import HDLParser
from trace_framework.core.engine import TraceabilityEngine
from trace_framework.utils.report_gen import ReportGenerator
from trace_framework.utils.config_validator import ConfigValidator
from trace_framework.ui.waiver_manager import WaiverManagerWindow
import json

RECENT_FILE = os.path.join("config", "recent.json")

ctk.set_appearance_mode("Dark")  # Force Dark Mode
ctk.set_default_color_theme("blue")  # We'll override button colors inline

# Define Theme Colors
THEME_BG = "#1b1b1b"
THEME_PRIMARY = "#fcba03"
THEME_PRIMARY_HOVER = "#e6a800"
THEME_TEXT_ON_PRIMARY = "#1b1b1b"

class ToolTip:
    current_window = None

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.schedule_id = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Button-1>", self.hide_tooltip)

    def schedule_tooltip(self, event=None):
        # Cancel any existing schedule
        self.cancel_schedule()
        # Schedule show after 300ms
        self.schedule_id = self.widget.after(300, self.show_tooltip)

    def cancel_schedule(self):
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None

    def show_tooltip(self):
        # Close any active global tooltip specifically
        if ToolTip.current_window:
            try:
                ToolTip.current_window.destroy()
            except Exception:
                pass
            ToolTip.current_window = None

        if not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes('-topmost', True)

        label = ctk.CTkLabel(self.tooltip_window, text=self.text, justify="left",
                           bg_color="transparent", corner_radius=6,
                           fg_color=("gray90", "gray20"), text_color=("black", "white"))
        label.pack(ipadx=8, ipady=4)

        ToolTip.current_window = self.tooltip_window

    def hide_tooltip(self, event=None):
        self.cancel_schedule()
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            ToolTip.current_window = None

class JanusTraceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JanusTrace - Requirement Traceability Tool")
        self.geometry("1080x760")
        self.configure(fg_color=THEME_BG)

        # Defer the icon call: CustomTkinter sets its own quill icon during
        # internal setup after super().__init__(). Using after() guarantees
        # our icon override runs last, fixing both titlebar and taskbar.
        def _set_icon():
            try:
                icon_path = resource_path("janustrace_icon.ico")
                if sys.platform == "win32":
                    self.iconbitmap(icon_path)
                else:
                    icon_img = ImageTk.PhotoImage(Image.open(icon_path))
                    self.wm_iconphoto(True, icon_img)
            except Exception as e:
                print(f"Failed to load main icon: {e}")
        self.after(200, _set_icon)


        # Layout: Grid 1x2 (Sidebar, Main Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_frames()
        self.show_frame("scan")

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0, fg_color="#121212")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="JanusTrace", font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME_PRIMARY)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_scan = ctk.CTkButton(self.sidebar_frame, text="Scan Project", command=lambda: self.show_frame("scan"),
                                      fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        self.btn_scan.grid(row=1, column=0, padx=20, pady=10)

        self.btn_config = ctk.CTkButton(self.sidebar_frame, text="Configuration", command=lambda: self.show_frame("config"),
                                        fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        self.btn_config.grid(row=2, column=0, padx=20, pady=10)
        ToolTip(self.btn_config, "Configure ID patterns and project rules.")

        self.btn_help = ctk.CTkButton(self.sidebar_frame, text="Help", command=lambda: self.show_frame("help"),
                                      fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        self.btn_help.grid(row=3, column=0, padx=20, pady=10)
        ToolTip(self.btn_help, "View documentation.")

        self.btn_about = ctk.CTkButton(self.sidebar_frame, text="About Developer", command=self.show_about,
                                      fg_color="transparent", text_color=THEME_PRIMARY, hover_color="#332b00", border_width=1, border_color=THEME_PRIMARY)
        self.btn_about.grid(row=4, column=0, padx=20, pady=10)

        # Appearance Mode
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "System"],
                                                                       command=self.change_appearance_mode_event,
                                                                       fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY,
                                                                       button_color=THEME_PRIMARY_HOVER, button_hover_color="#c99502")
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_optionemenu.set("Dark")

    def create_main_frames(self):
        # Scan Frame
        self.scan_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.build_scan_ui()

        # Config Frame
        self.config_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.build_config_ui()

        # Help Frame
        self.help_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.build_help_ui()

    def show_frame(self, name):
        # Hide all
        self.scan_frame.grid_forget()
        self.config_frame.grid_forget()
        self.help_frame.grid_forget()

        # Show selected
        if name == "scan":
            self.scan_frame.grid(row=0, column=1, sticky="nsew")
        elif name == "config":
            self.config_frame.grid(row=0, column=1, sticky="nsew")
        elif name == "help":
            self.help_frame.grid(row=0, column=1, sticky="nsew")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def show_about(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title("About JanusTrace")
        about_win.geometry("300x200")
        about_win.attributes("-topmost", True)
        about_win.configure(fg_color=THEME_BG)

        try:
            icon_path = resource_path("janustrace_icon.ico")
            if sys.platform == "win32":
                about_win.iconbitmap(icon_path)
            else:
                icon_img = ImageTk.PhotoImage(Image.open(icon_path))
                about_win.wm_iconphoto(False, icon_img)
        except Exception as e:
            print(f"Failed to load about icon: {e}")

        ctk.CTkLabel(about_win, text="JanusTrace", font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME_PRIMARY).pack(pady=(20, 5))
        ctk.CTkLabel(about_win, text="Author: Ugur Nezir", text_color=THEME_TEXT_ON_PRIMARY).pack(pady=5)

        link = ctk.CTkLabel(about_win, text="github.com/yesilzeytin", text_color="#fcba03", font=ctk.CTkFont(underline=True), cursor="hand2")
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/yesilzeytin"))

    # --- SCAN UI ---
    def build_scan_ui(self):
        # Header
        lbl = ctk.CTkLabel(self.scan_frame, text="Run Traceability Scan", font=ctk.CTkFont(size=24, weight="bold"))
        lbl.pack(pady=20, padx=20, anchor="w")

        # Form
        form_frame = ctk.CTkFrame(self.scan_frame)
        form_frame.pack(fill="x", padx=20, pady=10)

        # Trace Mode
        ctk.CTkLabel(form_frame, text="Trace Mode:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.trace_mode = ctk.CTkSegmentedButton(form_frame, values=["Source Code", "Document"], command=self.toggle_trace_mode)
        self.trace_mode.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.trace_mode.set("Source Code")

        # Config File
        ctk.CTkLabel(form_frame, text="Config File (.yaml):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_config = ctk.CTkEntry(form_frame, width=300)
        self.entry_config.grid(row=1, column=1, padx=10, pady=5)
        self.entry_config.insert(0, "config/default_rules.yaml")
        btn_browse_cfg = ctk.CTkButton(form_frame, text="Browse", width=80, command=lambda: self.browse_file(self.entry_config, "yaml"), fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        btn_browse_cfg.grid(row=1, column=2, padx=10)
        ToolTip(btn_browse_cfg, "Select the YAML configuration file.")

        # Reqs File (Primary)
        ctk.CTkLabel(form_frame, text="Primary Tool Requirements (.csv/xlsx):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_reqs = ctk.CTkEntry(form_frame, width=300)
        self.entry_reqs.grid(row=2, column=1, padx=10, pady=5)
        btn_browse_req = ctk.CTkButton(form_frame, text="Browse", width=80, command=lambda: self.browse_file(self.entry_reqs, "file"), fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        btn_browse_req.grid(row=2, column=2, padx=10)
        ToolTip(btn_browse_req, "Select the Target Requirements file (CSV or Excel).")

        # Source / Document
        self.lbl_source = ctk.CTkLabel(form_frame, text="Source Directory:")
        self.lbl_source.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_source = ctk.CTkEntry(form_frame, width=300)
        self.entry_source.grid(row=3, column=1, padx=10, pady=5)
        self.btn_browse_src = ctk.CTkButton(form_frame, text="Browse", width=80, command=lambda: self.browse_file(self.entry_source, "dir"), fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        self.btn_browse_src.grid(row=3, column=2, padx=10)

        # Document Mode Specific Fields
        self.lbl_link_col = ctk.CTkLabel(form_frame, text="Link Column Name:")
        self.entry_link_col = ctk.CTkEntry(form_frame, width=300)
        self.entry_link_col.insert(0, "Parent")

        self.lbl_source_id_col = ctk.CTkLabel(form_frame, text="Source ID Column:")
        self.entry_source_id_col = ctk.CTkEntry(form_frame, width=300)
        self.entry_source_id_col.insert(0, "ID")

        # Output Dir
        ctk.CTkLabel(form_frame, text="Output Directory:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.entry_output = ctk.CTkEntry(form_frame, width=300)
        self.entry_output.grid(row=6, column=1, padx=10, pady=5)
        self.entry_output.insert(0, "reports")
        btn_browse_out = ctk.CTkButton(form_frame, text="Browse", width=80, command=lambda: self.browse_file(self.entry_output, "dir"), fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        btn_browse_out.grid(row=6, column=2, padx=10)
        ToolTip(btn_browse_out, "Select where the HTML report will be saved.")

        # Waivers File (Optional)
        ctk.CTkLabel(form_frame, text="Waivers File (Optional):").grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.entry_waivers = ctk.CTkEntry(form_frame, width=300, placeholder_text="e.g. valid_waivers.json")
        self.entry_waivers.grid(row=7, column=1, padx=10, pady=5)
        btn_browse_wv = ctk.CTkButton(form_frame, text="Browse", width=80, command=lambda: self.browse_file(self.entry_waivers, "json"), fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        btn_browse_wv.grid(row=7, column=2, padx=10)
        ToolTip(btn_browse_wv, "Select an exported valid_waivers.json list.")

        # Action
        action_frame = ctk.CTkFrame(self.scan_frame, fg_color="transparent")
        action_frame.pack(pady=20)

        self.btn_run = ctk.CTkButton(action_frame, text="START SCAN", height=40, font=ctk.CTkFont(size=16, weight="bold"), command=self.run_scan_thread, fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER)
        self.btn_run.pack(side="left", padx=10)
        ToolTip(self.btn_run, "Run the traceability analysis.")

        self.btn_manage_waivers = ctk.CTkButton(action_frame, text="Manage Waivers", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.open_waiver_manager, fg_color="#2a4365", text_color="#90cdf4", hover_color="#1a365d")
        self.btn_manage_waivers.pack(side="left", padx=10)
        ToolTip(self.btn_manage_waivers, "Open the Waiver Manager GUI to process unresolved issues.")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.scan_frame, progress_color=THEME_PRIMARY)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 20))
        self.progress_bar.set(0)

        # Log
        self.log_box = ctk.CTkTextbox(self.scan_frame, height=200)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log("Ready to scan. Please select files.\nCWD: " + os.getcwd())

        self.load_recent_projects()

    def open_waiver_manager(self):
        w = WaiverManagerWindow(self)
        w.focus()

    def toggle_trace_mode(self, mode):
        if mode == "Document":
            self.lbl_source.configure(text="Source Document (.csv/.xlsx):")
            self.btn_browse_src.configure(command=lambda: self.browse_file(self.entry_source, "file"))
            self.lbl_link_col.grid(row=4, column=0, padx=10, pady=5, sticky="w")
            self.entry_link_col.grid(row=4, column=1, padx=10, pady=5)
            self.lbl_source_id_col.grid(row=5, column=0, padx=10, pady=5, sticky="w")
            self.entry_source_id_col.grid(row=5, column=1, padx=10, pady=5)
        else:
            self.lbl_source.configure(text="Source Directory:")
            self.btn_browse_src.configure(command=lambda: self.browse_file(self.entry_source, "dir"))
            self.lbl_link_col.grid_forget()
            self.entry_link_col.grid_forget()
            self.lbl_source_id_col.grid_forget()
            self.entry_source_id_col.grid_forget()

    def load_recent_projects(self):
        """Loads last-used paths into the GUI inputs."""
        try:
            if os.path.exists(RECENT_FILE):
                with open(RECENT_FILE, 'r') as f:
                    data = json.load(f)

                if 'config' in data:
                    self.entry_config.delete(0, 'end')
                    self.entry_config.insert(0, data['config'])
                if 'reqs' in data:
                    self.entry_reqs.delete(0, 'end')
                    self.entry_reqs.insert(0, data['reqs'])
                if 'source' in data:
                    self.entry_source.delete(0, 'end')
                    self.entry_source.insert(0, data['source'])
                if 'output' in data:
                    self.entry_output.delete(0, 'end')
                    self.entry_output.insert(0, data['output'])
                if 'waivers' in data:
                    self.entry_waivers.delete(0, 'end')
                    self.entry_waivers.insert(0, data['waivers'])
        except Exception as e:
            self.log(f"Warning: Could not load recent projects: {e}")

    def save_recent_projects(self):
        """Saves current paths to recent projects config."""
        try:
            os.makedirs(os.path.dirname(RECENT_FILE), exist_ok=True)
            data = {
                'config': self.entry_config.get(),
                'reqs': self.entry_reqs.get(),
                'source': self.entry_source.get(),
                'output': self.entry_output.get(),
                'waivers': self.entry_waivers.get()
            }
            with open(RECENT_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.log(f"Warning: Could not save recent projects: {e}")

    def browse_file(self, entry_widget, mode):
        if mode == "file":
             filenames = filedialog.askopenfilenames(title="Select Requirements Files", filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("All", "*.*")])
             filename = "; ".join(filenames)
        elif mode == "yaml":
             filename = filedialog.askopenfilename(filetypes=[("YAML", "*.yaml"), ("All", "*.*")])
        elif mode == "json":
             filename = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        else:
             filename = filedialog.askdirectory()

        if filename:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filename)

    def log(self, msg):
        """Thread-safe logging to the GUI text widget.

        Uses self.after() to marshal widget updates to the main thread,
        preventing tkinter thread-safety violations.
        """
        def _append_log():
            self.log_box.insert("end", str(msg) + "\n")
            self.log_box.see("end")
        self.after(0, _append_log)

    def set_progress(self, value):
        """Thread-safe progress bar update."""
        self.after(0, lambda: self.progress_bar.set(value))

    def run_scan_thread(self):
        # Disable button
        self.btn_run.configure(state="disabled")
        self.log_box.delete("1.0", "end")

        # Run in thread to keep GUI alive
        thread = threading.Thread(target=self.run_logic)
        thread.start()

    def run_logic(self):
        try:
            config_path = self.entry_config.get()
            reqs_paths_raw = self.entry_reqs.get()
            source_path = self.entry_source.get()
            output_path = self.entry_output.get()
            waivers_path = self.entry_waivers.get().strip()

            # Load Waivers if provided
            waiver_dict = {}
            if waivers_path:
                if not os.path.exists(waivers_path):
                    self.log(f"Warning: Waivers file not found: {waivers_path}")
                else:
                    try:
                        with open(waivers_path, 'r', encoding='utf-8') as f:
                            waiver_dict = json.load(f)
                            self.log(f"Loaded {len(waiver_dict)} waivers.")
                    except Exception as we:
                        self.log(f"Warning: Could not parse waivers file: {we}")

            # Validation
            if not os.path.exists(config_path):
                self.log(f"Error: Config not found: {config_path}")
                return

            reqs_paths = [p.strip() for p in reqs_paths_raw.split(';') if p.strip()]
            if not reqs_paths:
                self.log("Error: No requirements files specified.")
                return

            for p in reqs_paths:
                if not os.path.exists(p):
                    self.log(f"Error: Requirements file not found: {p}")
                    return

            if not os.path.exists(source_path):
                self.log(f"Error: Source dir not found: {source_path}")
                return

            self.set_progress(0.0)

            self.log("Loading and validating configuration...")
            config = load_config(config_path)
            ConfigValidator.validate_or_raise(config)
            self.save_recent_projects()
            self.set_progress(0.1)

            self.log("Building Regex...")
            regex_builder = RegexBuilder(config)
            pattern = regex_builder.compile_pattern()
            self.log(f"Pattern: {pattern}")
            self.set_progress(0.15)

            self.log("Parsing requirements...")
            reqs = []
            for path in reqs_paths:
                self.log(f"  - Reading {os.path.basename(path)}...")
                if path.endswith('.csv'):
                    doc_parser = CSVParser(config)
                else:
                    doc_parser = ExcelParser(config)
                file_reqs = doc_parser.parse_requirements(path)
                reqs.extend(file_reqs)

            self.log(f"Found {len(reqs)} requirements total.")

            self.set_progress(0.3)

            all_traces = []
            if self.trace_mode.get() == "Document":
                self.log(f"Scanning source document: {source_path}")
                link_col = self.entry_link_col.get()
                source_id_col = self.entry_source_id_col.get()

                doc_tracer = DocumentTracer(config)
                traces = doc_tracer.scan_for_tags(source_path, link_col, source_id_col)
                if traces:
                    self.log(f"  - Found {len(traces)} traces in document.")
                all_traces.extend(traces)
            else:
                self.log(f"Scanning source directory...")
                hdl_parser = HDLParser(config)

                supported_extensions = tuple(f".{ext}" for ext in hdl_parser.extension_map.keys())
                self.log(f"Scanning for extensions: {supported_extensions}")

                files_to_scan = []
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        if file.lower().endswith(supported_extensions):
                            files_to_scan.append(os.path.join(root, file))

                total_files = len(files_to_scan)
                for i, path in enumerate(files_to_scan):
                    traces = hdl_parser.scan_for_tags(path, pattern)
                    if traces:
                         self.log(f"  - {os.path.basename(path)}: Found {len(traces)}")
                    all_traces.extend(traces)

                    # Update progress from 30% to 80% during scan
                    progress = 0.3 + 0.5 * ((i + 1) / (total_files if total_files > 0 else 1))
                    self.set_progress(progress)

            self.log(f"Total traces found: {len(all_traces)}")
            self.set_progress(0.8)

            self.log("Linking requirements...")
            engine = TraceabilityEngine()
            results = engine.link(reqs, all_traces, waivers=waiver_dict)

            # R2R Hierarchy analysis (runs only if any req has a parent_id)
            r2r = engine.link_r2r(reqs)
            results['r2r'] = r2r
            if r2r['has_r2r']:
                self.log(f"R2R hierarchy detected: {len(r2r['hierarchy'])} parent(s), "
                         f"{len(r2r['orphaned_parents'])} orphaned reference(s), "
                         f"{len(r2r['cycles'])} cycle(s).")
            self.set_progress(0.9)

            self.log("Generating HTML Report...")
            gen = ReportGenerator(output_dir=output_path)
            report_path = gen.generate_html(results)
            self.set_progress(1.0)

            self.log("SUCCESS!")
            self.log(f"Report saved to: {report_path}")

            # Open report if on Windows
            if os.name == 'nt':
                os.startfile(report_path)

        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            # Guard against accessing widgets if the window was closed during scan
            try:
                self.btn_run.configure(state="normal")
            except Exception:
                pass

    # --- CONFIG UI ---
    def build_config_ui(self):
        lbl = ctk.CTkLabel(self.config_frame, text="Generate Configuration", font=ctk.CTkFont(size=24, weight="bold"))
        lbl.pack(pady=20, padx=20, anchor="w")

        # Main Container - Split into Top (Input) and Bottom (Result/Settings)
        # Top: Tabview for Input Source
        self.config_tabs = ctk.CTkTabview(self.config_frame, height=250)
        self.config_tabs.pack(fill="x", padx=20, pady=10)

        self.tab_manual = self.config_tabs.add("Visual Builder")
        self.tab_regex = self.config_tabs.add("Manual Regex")
        self.tab_languages = self.config_tabs.add("Source Languages")

        # --- TAB 1: VISUAL BUILDER (Renamed in setup) ---
        self.setup_manual_tab()

        # --- TAB 2: MANUAL REGEX ---
        self.setup_regex_tab()

        # --- TAB 3: LANGUAGES ---
        self.setup_languages_tab()

        # --- SETTINGS AREA ---
        settings_frame = ctk.CTkFrame(self.config_frame)
        settings_frame.pack(fill="x", padx=20, pady=10)

        # Enclosement
        lbl_enc = ctk.CTkLabel(settings_frame, text="Tag Enclosement ⓘ:", font=ctk.CTkFont(underline=True))
        lbl_enc.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ToolTip(lbl_enc, "Characters wrapping the ID in source code (e.g. [ID] or {ID}).\nThe parser looks for content between these tokens.")
        self.entry_enc_start = ctk.CTkEntry(settings_frame, width=50, placeholder_text="[")
        self.entry_enc_start.grid(row=0, column=1, padx=5, pady=5)
        self.entry_enc_start.insert(0, "[")

        self.entry_enc_end = ctk.CTkEntry(settings_frame, width=50, placeholder_text="]")
        self.entry_enc_end.grid(row=0, column=2, padx=5, pady=5)
        self.entry_enc_end.insert(0, "]")

        # Prefix / Separator (Removed as per request)
        # ctk.CTkLabel(settings_frame, text="Ignore Prefix (e.g. PROJ-):").grid(row=0, column=3, padx=10, pady=5, sticky="w")
        # self.entry_prefix = ctk.CTkEntry(settings_frame, width=150, placeholder_text="PROJ-")
        # self.entry_prefix.grid(row=0, column=4, padx=5, pady=5)

        # Result Regex
        ctk.CTkLabel(settings_frame, text="Generated Regex Pattern:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_regex_result = ctk.CTkEntry(settings_frame, width=400)
        self.entry_regex_result.grid(row=1, column=1, columnspan=4, padx=10, pady=10, sticky="ew")

        # Save Button
        self.btn_save_config = ctk.CTkButton(self.config_frame, text="SAVE CONFIGURATION", fg_color="green", hover_color="darkgreen", command=self.save_configuration)
        self.btn_save_config.pack(pady=20)
        ToolTip(self.btn_save_config, "Save the current settings and regex to a YAML file.")



    def setup_manual_tab(self):
        # Renaming done in initialization now
        # self.config_tabs._segmented_button._buttons_dict["Manual Example"].configure(text="Visual Builder")

        # Container for controls
        ctrl_frame = ctk.CTkFrame(self.tab_manual, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=5)

        # 1. FIXED
        frame_fixed = ctk.CTkFrame(ctrl_frame)
        frame_fixed.pack(side="left", padx=5, fill="y")
        lbl_fixed = ctk.CTkLabel(frame_fixed, text="Fixed Text ⓘ", font=ctk.CTkFont(underline=True))
        lbl_fixed.pack(pady=2)
        ToolTip(lbl_fixed, "Static text parts (e.g. 'REQ', 'PROJ') that do not change.")
        self.entry_vb_fixed = ctk.CTkEntry(frame_fixed, width=80, placeholder_text="e.g. REQ")
        self.entry_vb_fixed.pack(padx=5, pady=2)
        ctk.CTkButton(frame_fixed, text="+ Add", width=60, command=self.vb_add_fixed, fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER).pack(pady=5)

        # 2. SEPARATOR
        frame_sep = ctk.CTkFrame(ctrl_frame)
        frame_sep.pack(side="left", padx=5, fill="y")
        lbl_sep = ctk.CTkLabel(frame_sep, text="Separator ⓘ", font=ctk.CTkFont(underline=True))
        lbl_sep.pack(pady=2)
        ToolTip(lbl_sep, "Delimiters between ID parts (e.g. '-', '_').")
        self.opt_vb_sep = ctk.CTkComboBox(frame_sep, width=80, values=["-", "_", ":", "."])
        self.opt_vb_sep.pack(padx=5, pady=2)
        self.opt_vb_sep.set("-")
        ctk.CTkButton(frame_sep, text="+ Add", width=60, command=self.vb_add_sep, fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER).pack(pady=5)

        # 3. VARIABLE
        frame_var = ctk.CTkFrame(ctrl_frame)
        frame_var.pack(side="left", padx=5, fill="y")
        lbl_var = ctk.CTkLabel(frame_var, text="Variable ⓘ", font=ctk.CTkFont(underline=True))
        lbl_var.pack(pady=2)
        ToolTip(lbl_var, "Dynamic parts like Digits or Letters.\nSet count to Fixed (e.g. 3) or Any (+).")
        self.opt_vb_var_type = ctk.CTkComboBox(frame_var, width=110, values=["Digits (D)", "Letters (L)", "Alphanumeric (A)"])
        self.opt_vb_var_type.pack(padx=5, pady=2)

        # Count frame
        f_count = ctk.CTkFrame(frame_var, fg_color="transparent")
        f_count.pack(pady=2)
        self.opt_vb_count_mode = ctk.CTkSegmentedButton(f_count, values=["Fixed", "Any (+)"], command=self.vb_toggle_count)
        self.opt_vb_count_mode.pack(side="left")
        self.opt_vb_count_mode.set("Any (+)")
        self.entry_vb_count = ctk.CTkEntry(f_count, width=40, placeholder_text="3")
        self.entry_vb_count.pack(side="left", padx=5)
        self.entry_vb_count.configure(state="disabled") # Start disabled

        ctk.CTkButton(frame_var, text="+ Add", width=60, command=self.vb_add_var, fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER).pack(pady=5)

        # BLOCKS DISPLAY (Scrollable)
        ctk.CTkLabel(self.tab_manual, text="Pattern Structure:").pack(anchor="w", pady=(10,0))
        self.vb_blocks_frame = ctk.CTkScrollableFrame(self.tab_manual, height=110, orientation="horizontal")
        self.vb_blocks_frame.pack(fill="x", pady=5)

        # Reset
        action_row = ctk.CTkFrame(self.tab_manual, fg_color="transparent")
        action_row.pack(fill="x", pady=5)

        btn_clear = ctk.CTkButton(action_row, text="Clear All", width=80, fg_color="red", hover_color="darkred", command=self.vb_clear)
        btn_clear.pack(side="right", padx=5)
        ToolTip(btn_clear, "Remove all blocks and start over.")

        # Description
        self.lbl_vb_desc = ctk.CTkLabel(self.tab_manual, text="No pattern defined.", text_color="gray", wraplength=500, font=ctk.CTkFont(size=12, slant="italic"))
        self.lbl_vb_desc.pack(pady=5)

        # State
        self.vb_components = []

    def vb_toggle_count(self, value):
        if value == "Fixed":
            self.entry_vb_count.configure(state="normal")
        else:
            self.entry_vb_count.configure(state="disabled")

    def vb_add_fixed(self):
        val = self.entry_vb_fixed.get()
        if val:
            self.vb_add_component({'type': 'fixed', 'value': val})
            self.entry_vb_fixed.delete(0, "end")

    def vb_add_sep(self):
        val = self.opt_vb_sep.get()
        if val:
            self.vb_add_component({'type': 'separator', 'value': val})

    def vb_add_var(self):
        vtype = self.opt_vb_var_type.get()
        mode = self.opt_vb_count_mode.get()
        # default to 1 if not specified for parsing safety? No + is fine.
        count = "+"
        if mode == "Fixed":
            count = self.entry_vb_count.get()
            if not count.isdigit():
                messagebox.showerror("Error", "Count must be a number")
                return

        self.vb_add_component({'type': 'var', 'value': vtype, 'extra': count})

    def vb_add_component(self, comp):
        self.vb_components.append(comp)
        self.vb_refresh_ui()

    def vb_remove_component(self, index):
        if 0 <= index < len(self.vb_components):
            self.vb_components.pop(index)
            self.vb_refresh_ui()

    def vb_move_component(self, index, direction):
        # Direction: -1 (Left), 1 (Right)
        new_index = index + direction
        if 0 <= new_index < len(self.vb_components):
            # Swap
            self.vb_components[index], self.vb_components[new_index] = self.vb_components[new_index], self.vb_components[index]
            self.vb_refresh_ui()

    def vb_clear(self):
        self.vb_components = []
        self.vb_refresh_ui()

    def vb_refresh_ui(self):
        # 1. Clear blocks
        for widget in self.vb_blocks_frame.winfo_children():
            widget.destroy()

        # 2. Rebuild blocks
        count = len(self.vb_components)
        for i, comp in enumerate(self.vb_components):
            # Block Card style
            f = ctk.CTkFrame(self.vb_blocks_frame,
                             fg_color=("gray85", "gray25"),
                             corner_radius=8,
                             border_width=1,
                             border_color=("gray70", "gray40"))
            f.pack(side="left", padx=4, pady=3) # Reduced padding

            # Label
            header_txt = ""
            detail_txt = ""

            if comp['type'] == 'fixed':
                header_txt = "FIXED"
                detail_txt = comp['value']
            elif comp['type'] == 'separator':
                header_txt = "SEP"
                detail_txt = comp['value']
            elif comp['type'] == 'var':
                c = comp['extra']
                t = comp['value'][0] # D, L, A
                header_txt = "VAR"
                detail_txt = f"{c}{t}"

            # Header
            ctk.CTkLabel(f, text=header_txt, font=ctk.CTkFont(size=9, weight="bold"), text_color=("gray40", "gray70")).pack(padx=5, pady=(2,0))
            # Detail
            ctk.CTkLabel(f, text=detail_txt, font=ctk.CTkFont(size=12, weight="bold")).pack(padx=5, pady=(0, 2))

            # Action Buttons Row
            actions = ctk.CTkFrame(f, fg_color="transparent", height=20)
            actions.pack(pady=(0,3), padx=2, fill="x")

            # Left Button
            state_l = "normal" if i > 0 else "disabled"
            btn_l = ctk.CTkButton(actions, text="<", width=20, height=18,
                          fg_color="transparent",
                          border_width=1,
                          border_color=("gray60", "gray50"),
                          text_color=("black", "white"),
                          font=ctk.CTkFont(size=10),
                          state=state_l,
                          command=lambda idx=i: self.vb_move_component(idx, -1))
            btn_l.pack(side="left", padx=1)

            # Delete Button
            btn_del = ctk.CTkButton(actions, text="✕", width=20, height=18,
                          fg_color=("mistyrose", "#4a2a2a"),
                          hover_color=("salmon", "darkred"),
                          text_color="red",
                          font=ctk.CTkFont(size=10),
                          command=lambda idx=i: self.vb_remove_component(idx))
            btn_del.pack(side="left", padx=1)

            # Right Button
            state_r = "normal" if i < count - 1 else "disabled"
            btn_r = ctk.CTkButton(actions, text=">", width=20, height=18,
                          fg_color="transparent",
                          border_width=1,
                          border_color=("gray60", "gray50"),
                          text_color=("black", "white"),
                          font=ctk.CTkFont(size=10),
                          state=state_r,
                          command=lambda idx=i: self.vb_move_component(idx, 1))
            btn_r.pack(side="left", padx=1)


        # 3. Update Description & Regex
        from trace_framework.ui.config_helper import VisualBuilder

        # Desc
        desc = VisualBuilder.generate_description(self.vb_components)
        self.lbl_vb_desc.configure(text=desc)

        # Regex (Core)
        core_regex = VisualBuilder.compile_regex(self.vb_components)
        self.entry_regex_result.delete(0, "end")
        self.entry_regex_result.insert(0, core_regex)

    def setup_regex_tab(self):
        ctk.CTkLabel(self.tab_regex, text="Enter your regex manually below (overrides generation):").pack(anchor="w", pady=5)
        # This tab just instructs the user to use the main result box
        ctk.CTkLabel(self.tab_regex, text="Use the 'Generated Regex Pattern' box below to edit manually.").pack(pady=(20, 0))



    def generate_regex_logic(self, example_id):
        from trace_framework.ui.config_helper import ConfigHelper

        # prefix = self.entry_prefix.get() - deprecated
        # enc_start = self.entry_enc_start.get()
        # enc_end = self.entry_enc_end.get()

        # 1. Generate Core Regex from ID
        core_regex = ConfigHelper.generate_regex_from_id(example_id)

        # 2. Do NOT Add Enclosement (Parser logic handles tokens separate from ID pattern)
        # final_regex = ConfigHelper.wrap_with_enclosement(core_regex, enc_start, enc_end)

        self.entry_regex_result.delete(0, "end")
        self.entry_regex_result.insert(0, core_regex)

    def save_configuration(self):
        # Save to yaml
        regex = self.entry_regex_result.get()
        if not regex:
            messagebox.showwarning("Warning", "Regex pattern is empty!")
            return

        config_data = {
            "regex_rules": {
                "id_pattern": regex
            },
            "tags": {
                "start_token": self.entry_enc_start.get(),
                "end_token": self.entry_enc_end.get()
            },
            # We save prefix in parser_settings for UI recovery or logic
            "parser_settings": {
                "ignore_prefix": "" # self.entry_prefix.get() - deprecated
            },
            "languages": self.get_configured_languages()
        }

        # Validate Contentions
        warnings = self.check_language_contentions(config_data["languages"])
        if warnings:
            if not messagebox.askyesno("Extension Conflicts", f"The following file extensions are used by multiple languages:\n\n{warnings}\n\nThe parser will combine comment styles for these files. Do you want to proceed?"):
                return

        # Ask where to save
        target_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            initialfile="custom_config.yaml",
            initialdir="config",
            title="Save Configuration As"
        )

        if not target_path:
            return # Cancelled

        try:
            import yaml
            # Try to read existing file if it exists to preserve other keys,
            # OR if selecting a new file, maybe start fresh or copy defaults?
            # Let's simple merge if exists, else write new.

            if os.path.exists(target_path):
                with open(target_path, 'r') as f:
                   try:
                       existing = yaml.safe_load(f) or {}
                   except Exception:
                       existing = {}
            else:
                existing = {}

            if "regex_rules" not in existing: existing["regex_rules"] = {}
            existing["regex_rules"]["id_pattern"] = regex

            if "tags" not in existing: existing["tags"] = {}
            existing["tags"]["start_token"] = self.entry_enc_start.get()
            existing["tags"]["end_token"] = self.entry_enc_end.get()

            if "parser_settings" not in existing: existing["parser_settings"] = {}
            existing["parser_settings"]["ignore_prefix"] = "" # self.entry_prefix.get() deprecated

            # Save Languages
            existing["languages"] = self.get_configured_languages()

            with open(target_path, 'w') as f:
                yaml.dump(existing, f)

            messagebox.showinfo("Success", f"Configuration saved to {target_path}\n\nMake sure to select this file in the 'Scan Project' tab!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    # --- LANGUAGES UI ---
    def setup_languages_tab(self):
        # Tools row
        tools = ctk.CTkFrame(self.tab_languages, fg_color="transparent")
        tools.pack(fill="x", pady=5)

        ctk.CTkButton(tools, text="+ Add Language", width=120, command=self.add_language, fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER).pack(side="left")

        # Scrollable list
        self.lang_scroll = ctk.CTkScrollableFrame(self.tab_languages)
        self.lang_scroll.pack(fill="both", expand=True, pady=10)

        # Initialize default languages to match default_rules.yaml structure
        if not hasattr(self, 'languages'):
            self.languages = [
                {'name': 'Verilog', 'enabled': True, 'extensions': ['v', 'vh'], 'line_comment': '//', 'block_comment_start': '/*', 'block_comment_end': '*/'},
                {'name': 'SystemVerilog', 'enabled': True, 'extensions': ['sv', 'svh'], 'line_comment': '//', 'block_comment_start': '/*', 'block_comment_end': '*/'},
                {'name': 'VHDL', 'enabled': True, 'extensions': ['vhd', 'vhdl'], 'line_comment': '--', 'block_comment_start': '', 'block_comment_end': ''},
                {'name': 'C/C++', 'enabled': True, 'extensions': ['c', 'cpp', 'h', 'hpp', 'cc'], 'line_comment': '//', 'block_comment_start': '/*', 'block_comment_end': '*/'},
                {'name': 'Python', 'enabled': True, 'extensions': ['py'], 'line_comment': '#', 'block_comment_start': '', 'block_comment_end': ''},
                {'name': 'Java/C#/Rust', 'enabled': True, 'extensions': ['java', 'cs', 'rs'], 'line_comment': '//', 'block_comment_start': '/*', 'block_comment_end': '*/'},
                {'name': 'MATLAB', 'enabled': True, 'extensions': ['m'], 'line_comment': '%', 'block_comment_start': '%{', 'block_comment_end': '%}'},
                {'name': 'Ada', 'enabled': True, 'extensions': ['adb', 'ads'], 'line_comment': '--', 'block_comment_start': '', 'block_comment_end': ''},
            ]

        self.refresh_languages_ui()

    def refresh_languages_ui(self):
        for widget in self.lang_scroll.winfo_children():
            widget.destroy()

        for i, lang in enumerate(self.languages):
            row = ctk.CTkFrame(self.lang_scroll, fg_color=("gray90", "gray20"))
            row.pack(fill="x", pady=2, padx=5)

            # Checkbox
            var = ctk.BooleanVar(value=lang.get('enabled', True))
            cb = ctk.CTkCheckBox(row, text=lang['name'], variable=var, command=lambda idx=i, v=var: self.toggle_language(idx, v))
            cb.pack(side="left", padx=10, pady=5)

            # Info
            exts = ", ".join(lang['extensions'])
            info_lbl = ctk.CTkLabel(row, text=f"[{exts}]", text_color="gray")
            info_lbl.pack(side="left", padx=10)
            ToolTip(info_lbl, f"Line: {lang['line_comment']} | Block: {lang['block_comment_start']}...{lang['block_comment_end']}")

            # Edit
            ctk.CTkButton(row, text="Edit", width=60, height=24, command=lambda idx=i: self.edit_language(idx), fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER).pack(side="right", padx=5)
            # Remove
            ctk.CTkButton(row, text="X", width=30, height=24, fg_color="red", command=lambda idx=i: self.remove_language(idx)).pack(side="right", padx=5)

    def toggle_language(self, index, var):
        self.languages[index]['enabled'] = var.get()

    def remove_language(self, index):
        if messagebox.askyesno("Confirm", "Remove this language?"):
            self.languages.pop(index)
            self.refresh_languages_ui()

    def add_language(self):
        self.open_lang_dialog()

    def edit_language(self, index):
        self.open_lang_dialog(index)

    def open_lang_dialog(self, index=None):
        win = ctk.CTkToplevel(self)
        win.title("Edit Language" if index is not None else "Add Language")
        win.geometry("400x500")

        lang = self.languages[index] if index is not None else {}

        ctk.CTkLabel(win, text="Language Name:").pack(anchor="w", padx=20, pady=(20,5))
        e_name = ctk.CTkEntry(win)
        e_name.pack(fill="x", padx=20)
        e_name.insert(0, lang.get('name', ''))

        ctk.CTkLabel(win, text="Extensions (comma separated, no dots):").pack(anchor="w", padx=20, pady=(10,5))
        e_ext = ctk.CTkEntry(win)
        e_ext.pack(fill="x", padx=20)
        e_ext.insert(0, ", ".join(lang.get('extensions', [])))

        ctk.CTkLabel(win, text="Line Comment (e.g. //):").pack(anchor="w", padx=20, pady=(10,5))
        e_lc = ctk.CTkEntry(win)
        e_lc.pack(fill="x", padx=20)
        e_lc.insert(0, lang.get('line_comment', ''))

        ctk.CTkLabel(win, text="Block Comment Start (e.g. /*):").pack(anchor="w", padx=20, pady=(10,5))
        e_bs = ctk.CTkEntry(win)
        e_bs.pack(fill="x", padx=20)
        e_bs.insert(0, lang.get('block_comment_start', ''))

        ctk.CTkLabel(win, text="Block Comment End (e.g. */):").pack(anchor="w", padx=20, pady=(10,5))
        e_be = ctk.CTkEntry(win)
        e_be.pack(fill="x", padx=20)
        e_be.insert(0, lang.get('block_comment_end', ''))

        def save():
            name = e_name.get().strip()
            if not name:
                messagebox.showerror("Error", "Name required")
                return

            exts = [x.strip() for x in e_ext.get().split(',') if x.strip()]

            new_data = {
                'name': name,
                'enabled': True,
                'extensions': exts,
                'line_comment': e_lc.get(),
                'block_comment_start': e_bs.get(),
                'block_comment_end': e_be.get()
            }

            if index is not None:
                self.languages[index] = new_data
            else:
                self.languages.append(new_data)

            self.refresh_languages_ui()
            win.destroy()

        ctk.CTkButton(win, text="Save", command=save, fg_color=THEME_PRIMARY, text_color=THEME_TEXT_ON_PRIMARY, hover_color=THEME_PRIMARY_HOVER).pack(pady=30)

    def get_configured_languages(self):
        if not hasattr(self, 'languages'):
            return []
        return self.languages

    def check_language_contentions(self, languages):
        import collections
        ext_map = collections.defaultdict(list)

        for lang in languages:
            if not lang.get('enabled', True): continue
            for ext in lang.get('extensions', []):
                ext_map[ext.lower()].append(lang['name'])

        # Find duplicates
        warnings = []
        for ext, names in ext_map.items():
            if len(names) > 1:
                warnings.append(f".{ext} -> {', '.join(names)}")

        if warnings:
            return "\n".join(warnings)
        return None

    # --- HELP UI ---
    def build_help_ui(self):
        lbl = ctk.CTkLabel(self.help_frame, text="Help & Documentation", font=ctk.CTkFont(size=24, weight="bold"))
        lbl.pack(pady=20, padx=20, anchor="w")

        # Create a scrollable textbox for rich help content
        help_box = ctk.CTkTextbox(self.help_frame, wrap="word", font=ctk.CTkFont(size=13))
        help_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        help_text = """JanusTrace - Requirement Traceability Tool
=========================================
JanusTrace is designed to scan your source code for Requirement IDs and link them to your Requirements Documents (Excel or CSV). It generates interactive HTML and JSON reports.

🚀 Quick Start:
-----------------------------------------
1. Go to the 'Scan Project' tab.
2. Trace Mode: Choose "Source Code" (for parsing comments) or "Document" (for tracing between two requirement CSVs/Excels).
3. Config File: Select your configuration YAML file (e.g., config/default_rules.yaml).
4. Requirements: Select one or more CSV/Excel files containing your target/primary requirements.
5. Provide your Source Code Directory (or secondary Source Document if using Document Mode).
6. Output Directory: Select where the reports will be saved.
7. Click START SCAN.

Your recent paths are automatically saved and reloaded when you launch the app!

🛠 Configuration:
-----------------------------------------
Use the 'Configuration' tab to build custom parsing rules:
• Visual Builder: Visually arrange prefixes, separators, and numeric IDs to build your tags.
• Manual Regex: For complex parsing, input a raw regex pattern directly.
• Source Languages: Define which file extensions are scanned and how comments are structured in those languages. JanusTrace ONLY finds tags inside comments.

Your configuration will be validated for correctness before any scan begins.

📊 Output Reports:
-----------------------------------------
• Traceability Report (HTML): An interactive, searchable, and filterable table showing test coverage and orphaned traces.
• JSON Data (JSON): Machine-readable export of all scan results and statistics for CI/CD integration.
"""
        help_box.insert("1.0", help_text)
        help_box.configure(state="disabled") # Make it read-only

if __name__ == "__main__":
    app = JanusTraceApp()
    app.mainloop()
