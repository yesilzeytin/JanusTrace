import argparse
import logging
import yaml
import os
import sys
from trace_framework.utils.regex_builder import RegexBuilder
from trace_framework.parsers.doc_parsers import ExcelParser, CSVParser
from trace_framework.parsers.hdl_parsers import HDLParser
from trace_framework.core.engine import TraceabilityEngine
from trace_framework.utils.report_gen import ReportGenerator

logger = logging.getLogger(__name__)

from trace_framework.utils.config_validator import ConfigValidator

def load_config(config_path):
    """Load and parse a YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        dict: Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the YAML is malformed or unreadable.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                raise ValueError(f"Config file is empty: {config_path}")
            return config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file {config_path}: {e}")

def main():
    """Entry point for the CLI requirement traceability tool."""
    parser = argparse.ArgumentParser(description="Requirement Traceability Tool")
    parser.add_argument("--config", required=True, help="Path to configuration YAML")
    parser.add_argument("--reqs", required=True, nargs='+', help="Path(s) to requirements file (Excel/CSV)")
    parser.add_argument("--source", required=True, help="Path to source code directory")
    parser.add_argument("--output", required=False, default="reports", help="Output directory for reports")
    parser.add_argument("--waivers", required=False, help="Path to valid_waivers.json dictionary")
    parser.add_argument("--json", action="store_true", help="Also generate a JSON report alongside HTML")

    args = parser.parse_args()

    # Configure logging for CLI output
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        config = load_config(args.config)
        ConfigValidator.validate_or_raise(config)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 1. Build Regex
    print("Initializing Regex Builder...")
    regex_builder = RegexBuilder(config)
    pattern = regex_builder.compile_pattern()
    print(f"Compiled Regex: {pattern}")

    # 2. Parse Requirements
    reqs = []
    print("Parsing requirements...")
    for req_path in args.reqs:
        if not os.path.exists(req_path):
            print(f"Requirements file not found: {req_path}")
            sys.exit(1)

        if req_path.endswith('.xlsx') or req_path.endswith('.xls'):
            doc_parser = ExcelParser(config)
        elif req_path.endswith('.csv'):
            doc_parser = CSVParser(config)
        else:
            print(f"Unsupported requirements file format: {req_path}. Use .xlsx, .xls, or .csv")
            sys.exit(1)

        print(f" - Reading {req_path}...")
        file_reqs = doc_parser.parse_requirements(req_path)
        reqs.extend(file_reqs)

    print(f"Found {len(reqs)} requirements total.")

    # 3. Scan Source
    hdl_parser = HDLParser(config)
    source_dir = args.source
    if not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")
        sys.exit(1)

    all_traces = []

    # Build supported extension tuple from config-driven language definitions
    supported_extensions = tuple(f".{ext}" for ext in hdl_parser.extension_map.keys())
    print(f"Scanning for extensions: {supported_extensions}")

    print(f"Scanning source code in {source_dir}...")
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(supported_extensions):
                path = os.path.join(root, file)
                traces = hdl_parser.scan_for_tags(path, pattern)
                all_traces.extend(traces)

    print(f"Found {len(all_traces)} traces.")

    # 4. Waivers
    waiver_dict = {}
    if args.waivers:
        if os.path.exists(args.waivers):
            try:
                import json
                with open(args.waivers, 'r', encoding='utf-8') as f:
                    waiver_dict = json.load(f)
                print(f"Loaded {len(waiver_dict)} waivers.")
            except Exception as e:
                print(f"Warning: Could not parse waivers: {e}")
        else:
            print(f"Warning: Waivers file not found: {args.waivers}")

    # 5. Link
    print("Linking requirements to traces...")
    engine = TraceabilityEngine()
    results = engine.link(reqs, all_traces, waivers=waiver_dict)

    # 6. Generate Reports
    gen = ReportGenerator(output_dir=args.output)

    print("Generating HTML report...")
    html_path = gen.generate_html(results)
    print(f"HTML report: {os.path.abspath(html_path)}")

    if args.json:
        print("Generating JSON report...")
        json_path = gen.generate_json(results)
        print(f"JSON report: {os.path.abspath(json_path)}")

if __name__ == "__main__":
    main()

