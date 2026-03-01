import os
import shutil
import argparse
import glob

def clean_directory(path, dry_run=False):
    """Removes a directory and its contents."""
    if os.path.exists(path):
        if dry_run:
            print(f"[DRY RUN] Would delete directory: {path}")
        else:
            try:
                shutil.rmtree(path)
                print(f"Deleted directory: {path}")
            except Exception as e:
                print(f"Failed to delete directory {path}: {e}")
    else:
        print(f"Directory not found (skipping): {path}")

def clean_files(pattern, dry_run=False):
    """Removes files matching a glob pattern."""
    files = glob.glob(pattern, recursive=True)
    if not files:
        print(f"No files found matching (skipping): {pattern}")
        return

    for file_path in files:
        if dry_run:
            print(f"[DRY RUN] Would delete file: {file_path}")
        else:
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Failed to delete file {file_path}: {e}")

def get_project_root():
    return os.path.dirname(os.path.abspath(__file__))

def main():
    parser = argparse.ArgumentParser(description="JanusTrace Cleanup Utility. Removes generated files, builds, and caches.")
    
    parser.add_argument('--reports', action='store_true', help='Clean HTML and JSON reports in reports/ and tests/test_outputs/')
    parser.add_argument('--build', action='store_true', help='Clean PyInstaller build/, dist/, and .spec files')
    parser.add_argument('--cache', action='store_true', help='Clean Python __pycache__ and .pytest_cache directories')
    parser.add_argument('--all', action='store_true', help='Clean everything (reports, build, and cache)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate deletion without actually removing any files')

    args = parser.parse_args()

    if not (args.reports or args.build or args.cache or args.all):
        parser.print_help()
        print("\nNo switches provided. Please specify what to clean (e.g., --all).")
        return

    root = get_project_root()
    os.chdir(root)

    print("--- JanusTrace Cleanup Utility ---")

    if args.reports or args.all:
        print("\nCleaning Reports...")
        clean_directory("reports")
        clean_directory("tests/test_outputs")
        
        # Clean up any loose reports that might accidentally be in the root or test folders
        # Exclude README.html from cleanup
        for html_file in glob.glob("*.html"):
            if "readme" not in html_file.lower():
                clean_files(html_file, args.dry_run)
                
        clean_files("tests/*.html", args.dry_run)
        clean_files("*.json", args.dry_run)
        # Exclude specific non-report json if necessary, but we don't have config json

    if args.build or args.all:
        print("\nCleaning Build Artifacts...")
        clean_directory("build")
        clean_directory("dist")
        clean_files("*.spec", args.dry_run)
        print("Note: If the application icon was modified via PyInstaller, its .ico is kept as source unless explicitly removing.")

    if args.cache or args.all:
        print("\nCleaning Caches...")
        clean_directory(".pytest_cache")
        # Recursively find and remove __pycache__
        pycache_dirs = glob.glob("**/__pycache__", recursive=True)
        pycache_dirs.extend(glob.glob("__pycache__"))
        for d in set(pycache_dirs):
            clean_directory(d, args.dry_run)

    print("\nCleanup finished.")

if __name__ == "__main__":
    main()
