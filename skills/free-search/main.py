#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web Search Skill - Wrapper script for multi-level fallback web search

Part of web-search skill v3.0.0 - Anthropic official standard architecture

This wrapper delegates to the main implementation in scripts/main.py
(Follows Anthropic's official single-location architecture)
"""

import os
import sys
import subprocess

# Add scripts directory to Python path
# __file__ is at: .claude/skills/web-search/main.py
# We need to get to: .claude/skills/web-search/scripts/main.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "main.py")

if not os.path.exists(MAIN_SCRIPT):
    print(f"[ERROR] Main implementation not found: {MAIN_SCRIPT}", file=sys.stderr)
    sys.exit(1)

# Execute main script with all arguments
result = subprocess.run([sys.executable, MAIN_SCRIPT] + sys.argv[1:])
sys.exit(result.returncode)
