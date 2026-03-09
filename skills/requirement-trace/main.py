#!/usr/bin/env python3
"""
Requirement Trace Skill - Main wrapper script

This is the entry point for the requirement-trace skill.
Delegates to the actual implementation in scripts/requirement_manager.py

Usage:
    python main.py --project-dir <path> --action add --requirement "text" [options]
    python main.py --project-dir <path> --action list [options]
    python main.py --project-dir <path> --action search --query "text" [options]
"""

import subprocess
import sys
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
MANAGER_SCRIPT = SCRIPT_DIR / "scripts" / "requirement_manager.py"


def main():
    """Run the requirement manager with all provided arguments."""
    if not MANAGER_SCRIPT.exists():
        print(f"Error: requirement_manager.py not found at {MANAGER_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    # Build the command
    cmd = [sys.executable, str(MANAGER_SCRIPT)] + sys.argv[1:]

    # Run the script
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
