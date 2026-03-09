#!/usr/bin/env python3
"""
gethtml Skill - Download complete webpages with Feishu support

This skill wraps the Webpage Downloader Tool with Feishu document support.
"""

import sys
import os
import subprocess

# Get the correct path to the main gethtml directory
# From .claude/skills/gethtml/ -> go up 3 levels -> MyAIProduct -> gethtml
current_dir = os.path.dirname(os.path.abspath(__file__))
gethtml_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', 'gethtml'))

# Verify the path
if not os.path.exists(gethtml_dir):
    # Fallback: try relative from MyAIProduct
    gethtml_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', 'gethtml'))

# Add to path
sys.path.insert(0, gethtml_dir)

# Run the main script
if __name__ == '__main__':
    script_path = os.path.join(gethtml_dir, 'gethtml_skill.py')

    if not os.path.exists(script_path):
        print(f"Error: Cannot find gethtml_skill.py at {script_path}")
        sys.exit(1)

    # Execute with all arguments
    result = subprocess.run([sys.executable, script_path] + sys.argv[1:])
    sys.exit(result.returncode)
