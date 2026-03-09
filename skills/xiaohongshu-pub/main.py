#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Xiaohongshu Publisher Skill - Wrapper script for publishing to Xiaohongshu

Part of xiaohongshu-pub skill v2.0.0 - Anthropic official standard architecture

This wrapper delegates to the main implementation in scripts/main_publisher.py
(Follows Anthropic's official single-location architecture)
"""

import os
import sys
import subprocess

# Add scripts directory to Python path
# __file__ is at: .claude/skills/xiaohongshu-pub/main.py
# We need to get to: .claude/skills/xiaohongshu-pub/scripts/main_publisher.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "main_publisher.py")

if not os.path.exists(MAIN_SCRIPT):
    print(f"[ERROR] Main implementation not found: {MAIN_SCRIPT}", file=sys.stderr)
    sys.exit(1)

# Execute main script with all arguments
result = subprocess.run([sys.executable, MAIN_SCRIPT] + sys.argv[1:])
sys.exit(result.returncode)
