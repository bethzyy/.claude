"""
ExperienceWriter — expert-review 与 bug-retro 共享的经验沉淀模块

职责：
1. 统一的项目 memory 目录查找
2. bug-retro 四维度格式化
3. 经验文件写入 + MEMORY.md 索引维护

所有经验写入逻辑集中在此，bug-retro 和 expert-review 都调用它，
消除重复代码，保证格式一致。
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============ 项目 Memory 目录查找 ============

def get_project_memory_dir(project_dir: str) -> Optional[Path]:
    """
    查找项目对应的 Claude 项目 memory 目录。

    匹配规则：遍历 ~/.claude/projects/，找包含项目名的子目录。
    返回 {matched_dir}/memory/ 或 None。
    """
    memory_base = Path.home() / ".claude" / "projects"
    if not memory_base.exists():
        return None

    project_name = Path(project_dir).name.lower()

    # 精确匹配优先：目录名包含项目名
    candidates = []
    for d in memory_base.iterdir():
        if not d.is_dir():
            continue
        if project_name in d.name.lower():
            mem_dir = d / "memory"
            if mem_dir.exists():
                candidates.append(mem_dir)

    if candidates:
        # 如果有多个匹配，优先选名字最短的（最精确的）
        candidates.sort(key=lambda p: len(str(p)))
        return candidates[0]

    return None


# ============ bug-retro 四维度格式化 ============

def card_to_bug_retro_format(card_data: dict) -> str:
    """
    将标准化的经验字典转为 bug-retro 四维度 markdown 格式。

    输入格式:
    {
        "problem_pattern": str,      # 问题模式描述
        "root_cause": str,            # 根因分类（Category — Specific cause）
        "solution_techniques": list,  # 解决技巧列表
        "reusable_insight": str,      # 一句话可复用洞察
        "keywords": list,             # 搜索关键词
        "date": str,                  # YYYY-MM-DD
        "source": str,                # 来源标识
        "file_path": str,             # 相关文件（可选）
        "cwe_id": str,                # CWE ID（可选）
    }

    输出: bug-retro 四维度 markdown
    """
    problem = card_data.get("problem_pattern", "未描述")
    root_cause = card_data.get("root_cause", "未分类")
    techniques = card_data.get("solution_techniques", [])
    insight = card_data.get("reusable_insight", "未提炼")
    keywords = card_data.get("keywords", [])
    date = card_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    source = card_data.get("source", "unknown")
    file_path = card_data.get("file_path", "")
    cwe_id = card_data.get("cwe_id", "")

    # 生成 frontmatter name
    slug = _generate_slug(problem)
    description = insight if len(insight) <= 80 else insight[:77] + "..."

    # 技巧列表
    tech_lines = []
    for i, tech in enumerate(techniques, 1):
        tech_lines.append(f"{i}. {tech}")
    techniques_text = "\n".join(tech_lines) if tech_lines else "1. 见可复用洞察"

    # CWE 引用
    cwe_line = f"\n**CWE**: {cwe_id}" if cwe_id else ""

    # 文件引用
    file_line = f"\n**文件**: `{file_path}`" if file_path else ""

    return f"""---
name: exp-{slug}
description: {description}
type: project
source: {source}
---

## 问题模式
{problem}{cwe_line}{file_line}

## 根因分类
{root_cause}

## 解决技巧
{techniques_text}

## 可复用洞察
> {insight}

## 关键词
{', '.join(keywords)}

## 日期
{date}
"""


def _generate_slug(text: str, keywords: list = None) -> str:
    """
    从文本生成 kebab-case slug。

    策略：
    1. 优先从 text 中提取英文/数字片段
    2. 若 text 为纯中文（无英文），使用 keywords 中的英文词拼接
    3. 最终 fallback: "unnamed"
    """
    cleaned = text.lower().strip()
    # 移除 OWASP 前缀
    cleaned = re.sub(r'^owasp\s+\w[- ]*:\s*', '', cleaned)
    # 移除常见中文前缀
    for prefix in ["检查", "缺失", "缺少", "未", "不正确", "不安全"]:
        cleaned = re.sub(rf'^{prefix}', '', cleaned)
    cleaned = cleaned.strip(" :")

    # 提取英文/数字片段
    en_parts = re.findall(r'[a-z0-9]+', cleaned)
    if en_parts:
        slug = "-".join(en_parts[:5])  # 最多取 5 个英文片段
        return slug[:50].strip("-")

    # 纯中文：使用 keywords 中的英文词
    if keywords:
        en_keywords = [k.lower() for k in keywords if re.search(r'[a-z0-9]', k)]
        if en_keywords:
            slug = "-".join(en_keywords[:4])
            return slug[:50].strip("-")

    return "unnamed"


# ============ 经验文件写入 + 索引维护 ============

def write_experience_card(card_data: dict, project_dir: str) -> Optional[str]:
    """
    将经验卡片写入项目 memory 目录，并更新 MEMORY.md 索引。

    Args:
        card_data: 标准化的经验字典（同 card_to_bug_retro_format 输入格式）
        project_dir: 项目目录路径

    Returns:
        写入的文件路径，或 None（如果写入失败或 memory 目录不存在）
    """
    mem_dir = get_project_memory_dir(project_dir)
    if not mem_dir:
        return None

    # 生成文件名
    slug = _generate_slug(
        card_data.get("problem_pattern", ""),
        keywords=card_data.get("keywords", []),
    )
    filepath = mem_dir / f"exp-{slug}.md"

    # 不覆盖已有文件
    if filepath.exists():
        return None

    # 格式化内容
    content = card_to_bug_retro_format(card_data)

    # 写入文件
    try:
        filepath.write_text(content, encoding="utf-8")
    except Exception:
        return None

    # 更新 MEMORY.md 索引
    _update_memory_index(mem_dir, card_data, slug)

    return str(filepath)


def _update_memory_index(mem_dir: Path, card_data: dict, slug: str):
    """
    在 MEMORY.md 中追加经验索引条目。

    格式: - [经验标题](exp-file-name.md) — 一句话核心洞察
    """
    memory_file = mem_dir / "MEMORY.md"
    if not memory_file.exists():
        return

    try:
        content = memory_file.read_text(encoding="utf-8")
    except Exception:
        return

    # 构建索引行
    insight = card_data.get("reusable_insight", "")
    if len(insight) > 80:
        insight = insight[:77] + "..."
    index_line = f"- [exp-{slug}](exp-{slug}.md) — {insight}"

    # 检查是否已存在（避免重复）
    if f"exp-{slug}" in content:
        return

    # 追加到文件末尾（在 currentDate 之前，如果有）
    lines = content.split("\n")
    insert_pos = len(lines)

    # 找到 "# currentDate" 的位置，在其前面插入
    for i, line in enumerate(lines):
        if line.strip().startswith("# currentDate"):
            insert_pos = i
            break

    # 确保前面有空行
    if insert_pos > 0 and lines[insert_pos - 1].strip():
        lines.insert(insert_pos, "")
        insert_pos += 1

    lines.insert(insert_pos, index_line)

    memory_file.write_text("\n".join(lines), encoding="utf-8")


# ============ 批量写入 ============

def write_experience_cards(cards: List[dict], project_dir: str) -> List[str]:
    """
    批量写入经验卡片。

    Args:
        cards: 标准化经验字典列表
        project_dir: 项目目录路径

    Returns:
        成功写入的文件路径列表
    """
    written = []
    for card in cards:
        result = write_experience_card(card, project_dir)
        if result:
            written.append(result)
    return written
