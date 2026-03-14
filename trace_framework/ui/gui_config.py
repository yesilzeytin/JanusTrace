"""
Configuration generator wizard GUI.
"""
import os
import tkinter as tk
from tkinter import messagebox, filedialog
import yaml

class ConfigWizard:
    """GUI Tool to create custom_rules.yaml"""
    def __init__(self, root):
        self.root = root
        self.root.title("JanusTrace Configuration Wizard")
        self.root.geometry("600x500")

        # Header
        tk.Label(root, text="Requirement Traceability Configuration", font=("Helvetica", 16)).pack(pady=10)

        # Tag Structure
        tk.Label(root, text="Tag Structure (e.g., {project}-{id})", anchor="w").pack(fill="x", padx=20)
        self.tag_entry = tk.Entry(root)
        self.tag_entry.pack(fill="x", padx=20, pady=5)
        self.tag_entry.insert(0, "{project_id}-{req_type}-{id_num}")

        # Tokens
        tk.Label(root, text="Tokens (YAML format: key: regex)", anchor="w").pack(fill="x", padx=20)
        tk.Label(root, text="Example:\nproject_id: \"[A-Z]{3}\"", justify="left", fg="gray").pack(fill="x", padx=20)

        self.tokens_text = tk.Text(root, height=10)
        self.tokens_text.pack(fill="both", expand=True, padx=20, pady=5)
        self.tokens_text.insert(tk.END, "project_id: \"[A-Z]{3}\"\nreq_type: \"(SRS|HLR)\"\nid_num: \"\\\\d{3,5}\"")

        # Save Button
        tk.Button(root, text="Save Configuration", command=self.save_config, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold")).pack(pady=20)

    def save_config(self):
        """Validates and saves tokens to YAML."""
        tag_structure = self.tag_entry.get()
        tokens_raw = self.tokens_text.get("1.0", tk.END)

        try:
            tokens = yaml.safe_load(tokens_raw)
        except yaml.YAMLError as e:
            messagebox.showerror("Error", f"Invalid YAML in tokens:\n{e}")
            return

        if not isinstance(tokens, dict):
            messagebox.showerror("Error", "Tokens must be a dictionary (key: value).")
            return

        config = {
            "tag_structure": tag_structure,
            "tokens": tokens,
            "comment_style": {
                "vhdl": "-- @req ",
                "verilog": "// @req ",
                "systemverilog": "// @req "
            }
        }

        # Default to config directory if it exists
        initial_dir = os.path.join(os.getcwd(), "config")
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml")],
            initialfile="custom_rules.yaml",
            initialdir=initial_dir,
            title="Save Configuration File"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False)
                messagebox.showinfo("Success", f"Configuration saved to:\n{file_path}")
            # pylint: disable=broad-exception-caught
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

if __name__ == "__main__":
    main_root = tk.Tk()
    app = ConfigWizard(main_root)
    main_root.mainloop()
