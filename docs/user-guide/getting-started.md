# Getting Started with JanusTrace

JanusTrace is a professional-grade requirement-to-code traceability tool engineered for safety-critical hardware and software development environments. By seamlessly linking high-level system requirements to low-level implementation logic, JanusTrace ensures compliance with stringent industry standards (such as DO-254 for avionics, ISO 26262 for automotive, and IEC 61508 for industrial systems).

This guide provides a comprehensive walkthrough for installing, configuring, and executing your first compliance scan using JanusTrace.

---

## 1. System Requirements & Installation

JanusTrace is built to be lightweight, portable, and easily integrable into existing CI/CD pipelines or local developer environments.

### 1.1 Prerequisites
Before installing JanusTrace, ensure your system meets the following specifications:
*   **Operating System**: Windows 10/11, macOS 10.15+, or modern Linux distributions (Ubuntu, Fedora, CentOS).
*   **Python Target**: Python 3.10 or higher.
*   **Package Manager**: `pip` (standard with Python installations).
*   **Dependencies**: The application relies on external libraries such as `CustomTkinter` (for the GUI), `pandas` (for scalable document parsing), `openpyxl` (for Excel support), and `PyYAML` (for configuration management).

### 1.2 Installation Steps

**Method A: Cloning the Repository (Recommended for Developers)**
1.  **Clone the Repository**: Use Git to clone the source code to your local machine:
    ```bash
    git clone https://github.com/your-org/JanusTrace.git
    cd JanusTrace
    ```
2.  **Establish a Virtual Environment** (Optional but highly recommended):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

**Method B: Standalone Executable (Windows Only)**
For users who do not wish to install Python, JanusTrace provides a pre-compiled Windows standalone executable generated via PyInstaller.
1. Download `JanusTrace.exe` from the latest GitHub Release.
2. Place the executable in a designated tools directory. No `pip install` or Python environment is required.

---

## 2. Core Concepts of Traceability

To use JanusTrace effectively, it is critical to understand the primary terminology and data flow inherent in traceability compliance.

### 2.1 The Requirement Document
A Requirement is a definitive statement of what the system must do. JanusTrace expects requirements to be stored in structured tabular formats.
*   **Supported Formats**: `.csv`, `.xlsx`, `.xls`
*   **Key Columns**: 
    *   `ID` (Mandatory): The unique identifier for the requirement (e.g., `SYS-REQ-001`).
    *   `Description` (Recommended): Text elaborating on the requirement purpose.
    *   `Parent` (Optional): The ID of a higher-level requirement, used to construct Requirement-to-Requirement (R2R) hierarchies.

### 2.2 The Source Code (Implementation)
The implementation logic resides in your source code repository. JanusTrace supports scanning a wide variety of linguistic environments:
*   **Hardware Description Languages (HDL)**: VHDL (`.vhd`), Verilog (`.v`), SystemVerilog (`.sv`).
*   **Software Languages**: Python (`.py`), C/C++ (`.c`, `.cpp`, `.h`), JavaScript/TypeScript (`.js`, `.ts`).
*   **Configurability**: You can easily define custom file extensions and their corresponding comment syntax via the [`default_rules.yaml`](./configuration.md).

### 2.3 The Trace Tag
A Trace Tag is a specific marker embedded as a comment within the source code. It explicitly declares that the adjacent logic fulfills a specific requirement.
*   **Syntax**: Tags are enclosed within user-defined boundaries, typically brackets `[` and `]`.
*   **Example in C++**:
    ```cpp
    // [SYS-REQ-001]
    // The system shall initialize the primary power bus within 50ms.
    void init_power_bus() {
        power_manager.startup(50);
    }
    ```

---

## 3. Executing Your First Scan

Once your requirements and source code are prepared, you can perform a traceability scan using either the GUI or the CLI.

### 3.1 Using the Graphical User Interface (GUI)

The JanusTrace GUI provides an intuitive, step-by-step wizard for configuring and running scans.

1.  **Launch the Application**:
    ```bash
    python main_gui.py
    ```
    *Note: If using the standalone executable, simply double-click `JanusTrace.exe`.*

![JanusTrace GUI on Startup](../images/gui00.png)

2.  **Trace Mode Selection**: 
    *   Select **Source Code** if tracing from Requirements to HDL/C/Python source files.
    *   Select **Document** if tracing between two different Requirement matrices.
3.  **Configure Input Paths**:
    *   **Config File**: Browse and select `config/default_rules.yaml`. This file dictates exactly how your tags should be formatting (e.g., separating components with hyphens).
    *   **Primary Requirements**: Select your CSV or Excel document.
    *   **Source Directory**: Select the root folder of your source code repository. JanusTrace will recursively scan all compatible subdirectories.
    *   **Output Directory**: Select where the HTML traceability report should be generated.
4.  **Execute the Scan**: Click **START SCAN**. The threaded worker will parse documents, scan code, link traces, and generate the final output. The live log viewer will display real-time parsing statistics.
5.  **Review the Report**: Upon completion, JanusTrace will automatically launch the interactive HTML report in your default web browser.

### 3.2 Using the Command Line Interface (CLI)

For integration into automated build servers (like Jenkins, GitLab CI, or GitHub Actions), use the headless CLI mode.

```bash
python main.py \
  --config config/default_rules.yaml \
  --reqs tests/fixtures/01_Valid_Requirements.csv \
  --source tests/fixtures/02_Valid_Source \
  --output reports/ \
  --verbose
```

The CLI will output the traceability matrix summary directly to standard output (STDOUT) and return a status code of `0` on success.

---

## 4. Understanding the Outcome

JanusTrace evaluates the relationship between Requirements and Traces across several definitive states:

*   🟢 **OK / COVERED**: The requirement ID was found in the source code. The link is validated.
*   🔴 **REQ_MISSING**: The requirement exists in the CSV, but no corresponding Trace Tag was found in the source code. This represents unwritten implementation.
*   🟡 **TRACE_ORPHAN**: A Trace Tag was found in the source code, but the ID does not exist in the Requirements CSV. This represents rogue code or a typo in the tag.
*   ⚫ **REQ_INVALID / TRACE_INVALID**: The ID string violates the formatting rules defined in the YAML configuration (e.g., lowercase letters when uppercase was strictly enforced).
*   🔵 **WAIVED**: The requirement was explicitly waived in `valid_waivers.json`, purposefully bypassing error thresholds for missing logic.

[Next: Configuration Guide](./configuration.md) | [Back to Home](../index.md)
