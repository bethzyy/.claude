#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Toutiao Content Skill - Wrapper script for Toutiao article management

Part of toutiao-cnt skill v5.0.0 - 基于事实生成，杜绝编造

This wrapper delegates to the main implementation in scripts/toutiao_content.py
(Follows Anthropic's official single-location architecture)

New in v5.0.0:
- --content parameter for user-provided facts
- --strict mode to reject generation without facts
- Adaptive word count based on fact materials
"""

import os
import sys
import subprocess

# Add scripts directory to Python path
# __file__ is at: .claude/skills/toutiao-cnt/main.py
# We need to get to: .claude/skills/toutiao-cnt/scripts/toutiao_content.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "scripts", "toutiao_content.py")

if not os.path.exists(MAIN_SCRIPT):
    print(f"[ERROR] Main implementation not found: {MAIN_SCRIPT}", file=sys.stderr)
    sys.exit(1)

# Execute main script with all arguments
result = subprocess.run([sys.executable, MAIN_SCRIPT] + sys.argv[1:])
sys.exit(result.returncode)
