"""
Waiver Manager GUI for JanusTrace.
Allows users to load unresolved_issues.json, mark items as waived,
and export a valid_waivers.json file.
"""
# pylint: disable=broad-exception-caught

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk


class WaiverManagerWindow(ctk.CTkToplevel):
    """Secondary window to manage requirement waivers."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("JanusTrace Waiver Manager")
        self.geometry("800x600")
        
        self.issues = []
        self.row_widgets = []

        # ---------------------
        # Top Bar
        # ---------------------
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(fill="x", padx=10, pady=10)

        self.btn_load = ctk.CTkButton(
            self.top_frame,
            text="Load Unresolved Issues (JSON)",
            command=self.load_issues
        )
        self.btn_load.pack(side="left", padx=10)

        self.lbl_status = ctk.CTkLabel(self.top_frame, text="No issues loaded.", text_color="gray")
        self.lbl_status.pack(side="left", padx=10)

        self.btn_save = ctk.CTkButton(
            self.top_frame,
            text="Save Waivers to JSON",
            command=self.save_waivers,
            fg_color="#fcba03",
            text_color="black",
            hover_color="#e6a800"
        )
        self.btn_save.pack(side="right", padx=10)
        self.btn_save.configure(state="disabled")

        # ---------------------
        # List Container
        # ---------------------
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header Row
        header_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Waive?", width=60, anchor="center", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Item ID", width=120, anchor="w", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Type", width=150, anchor="w", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Description", width=200, anchor="w", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Waiver Reason", expand=True, anchor="w", font=("Helvetica", 12, "bold")).pack(side="left", padx=5, fill="x")


    def load_issues(self):
        """Prompt user for unresolved_issues.json and render it."""
        initial_dir = os.path.join(os.getcwd(), "reports")
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        filepath = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Unresolved Issues File",
            filetypes=(("JSON Files", "*.json"), ("All Files", "*.*"))
        )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Expected a JSON list of issues.")

            self.issues = data
            self.lbl_status.configure(text=f"Loaded {len(data)} issues from {os.path.basename(filepath)}")
            self.render_issues()
            self.btn_save.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Failed to Load", f"Could not parse issues JSON:\n{e}")

    def render_issues(self):
        """Render the rows for each issue loaded."""
        # Clear existing
        for widget_dict in self.row_widgets:
            widget_dict['frame'].destroy()
        self.row_widgets.clear()

        for idx, issue in enumerate(self.issues):
            item_id = issue.get("id", "Unknown")
            item_type = issue.get("type", "Unknown")
            desc = issue.get("description", "")

            # truncate desc if too long
            short_desc = (desc[:40] + '..') if len(desc) > 40 else desc

            row_frame = ctk.CTkFrame(self.list_frame)
            row_frame.pack(fill="x", pady=2)

            waive_var = tk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(row_frame, text="", variable=waive_var, width=60)
            chk.pack(side="left", padx=5)
            
            lbl_id = ctk.CTkLabel(row_frame, text=item_id, width=120, anchor="w")
            lbl_id.pack(side="left", padx=5)

            lbl_type = ctk.CTkLabel(row_frame, text=item_type, width=150, anchor="w", text_color="#f5b7b1")
            lbl_type.pack(side="left", padx=5)
            
            lbl_desc = ctk.CTkLabel(row_frame, text=short_desc, width=200, anchor="w")
            lbl_desc.pack(side="left", padx=5)

            entry_reason = ctk.CTkEntry(row_frame, placeholder_text="Required if waiving...")
            entry_reason.pack(side="left", padx=5, fill="x", expand=True)

            # Link toggling
            def on_toggle(var=waive_var, entry=entry_reason):
                if var.get():
                    entry.configure(border_color="#fcba03")
                else:
                    entry.configure(border_color="gray")

            chk.configure(command=on_toggle)

            self.row_widgets.append({
                "frame": row_frame,
                "id": item_id,
                "var": waive_var,
                "entry": entry_reason
            })

    def save_waivers(self):
        """Gather checked items and save to valid_waivers.json."""
        waiver_dict = {}
        for w in self.row_widgets:
            if w['var'].get():
                reason = w['entry'].get().strip()
                if not reason:
                    messagebox.showerror(
                        "Validation Error", 
                        f"Please provide a waiver reason for ID: {w['id']} in order to waive it."
                    )
                    return
                waiver_dict[w['id']] = reason

        if not waiver_dict:
            messagebox.showinfo("Nothing to Save", "You haven't checked 'Waive?' on any items.")
            return

        initial_dir = os.path.join(os.getcwd(), "config")
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir, exist_ok=True)

        filepath = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            title="Save Waivers File",
            initialfile="valid_waivers.json",
            filetypes=(("JSON Files", "*.json"),)
        )

        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(waiver_dict, f, indent=4)
            messagebox.showinfo("Success", f"{len(waiver_dict)} waivers saved successfully to:\n{filepath}")
            self.destroy() # Close window
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save waivers:\n{e}")
