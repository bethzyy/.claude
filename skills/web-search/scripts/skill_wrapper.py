#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Search Skill - Skill Wrapper

这是 Claude Code Skill tool 的入口点，用于在 Skill 调用时设置环境变量。
"""
import sys
import os

# 设置 Skill 调用标记
os.environ['SKILL_CALL'] = '1'

# 导入并执行主脚本
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from main import main

if __name__ == "__main__":
    sys.exit(main())
