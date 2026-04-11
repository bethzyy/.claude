"""
_paths.py — 集中管理 skill 内部路径和 sys.path

所有模块统一从此处导入 SKILL_DIR 和 ensure_skill_path()，
避免 17 个文件各自重复 3 行样板代码。
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"


def ensure_skill_path():
    """确保 SKILL_DIR 在 sys.path 中（仅插入一次）"""
    skill_path = str(SKILL_DIR)
    if skill_path not in sys.path:
        sys.path.insert(0, skill_path)
