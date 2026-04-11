"""Project UI characteristic scanner.

Detects tech stack, CSS signals, domain, and content types from a project directory.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from colorsys import rgb_to_hls


@dataclass
class ProjectProfile:
    tech_stack: list[str] = field(default_factory=list)
    industry_hint: str | None = None
    project_name: str = ""
    project_description: str = ""
    current_colors: list[str] = field(default_factory=list)
    color_temperature: str = "unknown"  # warm/cool/neutral/unknown
    has_dark_mode: bool = False
    font_families: list[str] = field(default_factory=list)
    border_radius_style: str = "unknown"  # sharp/moderate/rounded/pill/unknown
    content_types: list[str] = field(default_factory=list)
    complexity_level: str = "simple"  # simple/medium/complex
    has_ui: bool = False
    user_scenarios: list[str] = field(default_factory=list)
    emotional_goals: list[str] = field(default_factory=list)
    domain_tags: list[str] = field(default_factory=list)
    is_ai_tool: bool = False


# --- Tech stack detection ---

_FRAMEWORK_MARKERS = {
    "flask": ["flask"],
    "django": ["django"],
    "fastapi": ["fastapi"],
    "react": ["react", "react-dom", "next"],
    "vue": ["vue"],
    "tailwind": ["tailwindcss"],
    "bootstrap": ["bootstrap"],
    "svelte": ["svelte"],
    "express": ["express"],
}

_CSS_FRAMEWORK_MARKERS = {
    "tailwind": ["tailwind"],
    "bootstrap": ["bootstrap"],
    "bulma": ["bulma"],
    "foundation": ["foundation"],
}


def _read_file(path: Path, max_bytes: int = 50_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
    except Exception:
        return ""


def _detect_tech_stack(project_path: Path) -> list[str]:
    stack = []
    for dep_file in ["requirements.txt", "Pipfile", "pyproject.toml"]:
        content = _read_file(project_path / dep_file)
        if content:
            for name, markers in _FRAMEWORK_MARKERS.items():
                if any(m in content.lower() for m in markers):
                    stack.append(name)

    pkg_json = project_path / "package.json"
    content = _read_file(pkg_json)
    if content:
        try:
            deps = json.loads(content)
            all_deps = list(deps.get("dependencies", {}).keys()) + list(deps.get("devDependencies", {}).keys())
            for name, markers in _FRAMEWORK_MARKERS.items():
                if any(m in " ".join(all_deps).lower() for m in markers):
                    stack.append(name)
        except json.JSONDecodeError:
            pass
    return list(dict.fromkeys(stack))


def _detect_css_framework(project_path: Path) -> str | None:
    for css_dir in [project_path / "static" / "css", project_path / "styles", project_path / "css"]:
        if not css_dir.exists():
            continue
        for f in css_dir.iterdir():
            if f.suffix in (".css", ".scss", ".less"):
                content = _read_file(f)
                for name, markers in _CSS_FRAMEWORK_MARKERS.items():
                    if any(m in content.lower() for m in markers):
                        return name
    return None


# --- CSS signal extraction ---

_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_FONT_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)
_RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.IGNORECASE)
_DARK_MODE_RE = re.compile(r"prefers-color-scheme\s*:\s*dark|\.dark\s*\{|dark-mode|dark-theme", re.IGNORECASE)
_CSS_VAR_RE = re.compile(r"--[\w-]+\s*:", re.IGNORECASE)


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        h, l, s = rgb_to_hls(r, g, b)
        return h * 360, l * 100, s * 100
    except (ValueError, IndexError):
        return 0, 50, 0


def _classify_color_temperature(colors: list[str]) -> str:
    if not colors:
        return "unknown"
    warm_score = 0
    cool_score = 0
    for c in colors:
        h, l, s = _hex_to_hsl(c)
        if s < 10:  # desaturated = neutral
            continue
        if (0 <= h <= 60) or (300 <= h <= 360):
            warm_score += s
        elif (120 <= h <= 270):
            cool_score += s
    total = warm_score + cool_score
    if total == 0:
        return "neutral"
    ratio = warm_score / total
    if ratio > 0.6:
        return "warm"
    elif ratio < 0.4:
        return "cool"
    return "neutral"


def _classify_border_radius(css_content: str) -> str:
    matches = _RADIUS_RE.findall(css_content)
    if not matches:
        return "unknown"
    values = []
    for m in matches:
        nums = re.findall(r"(\d+(?:\.\d+)?)", m)
        for n in nums:
            values.append(float(n))
    if not values:
        if "9999" in css_content or "pill" in css_content.lower():
            return "pill"
        return "unknown"
    max_val = max(values)
    avg_val = sum(values) / len(values)
    if max_val >= 9000 or avg_val >= 9000:
        return "pill"
    elif avg_val >= 13:
        return "rounded"
    elif avg_val >= 5:
        return "moderate"
    else:
        return "sharp"


_EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".tox", "venv", ".venv", "env", "dist", "build", ".next", ".nuxt", "target"}


def _is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in _EXCLUDED_DIRS:
            return True
    return False


def _extract_css_signals(project_path: Path) -> dict:
    colors = []
    fonts = []
    has_dark = False
    has_css_vars = False
    radius_style = "unknown"
    css_content_combined = ""

    css_dirs = [
        project_path / "static" / "css",
        project_path / "static",
        project_path / "styles",
        project_path / "css",
        project_path / "assets" / "css",
    ]
    # Only scan project root if no subdirectory found any CSS
    has_subdirs = any(d.exists() for d in css_dirs)
    if not has_subdirs:
        css_dirs.append(project_path)

    seen_dirs = set()
    for css_dir in css_dirs:
        css_dir = css_dir.resolve()
        if css_dir in seen_dirs or not css_dir.exists():
            continue
        seen_dirs.add(css_dir)
        for f in css_dir.rglob("*"):
            if not f.is_file() or f.suffix not in (".css", ".scss", ".less"):
                continue
            if _is_excluded(f):
                continue
            content = _read_file(f)
            css_content_combined += content + "\n"
            colors.extend(_HEX_RE.findall(content))
            fonts.extend(_FONT_RE.findall(content))
            if _DARK_MODE_RE.search(content):
                has_dark = True
            if _CSS_VAR_RE.search(content):
                has_css_vars = True

    if css_content_combined:
        radius_style = _classify_border_radius(css_content_combined)

    # Deduplicate and clean
    colors = list(dict.fromkeys(colors))[:50]
    fonts_cleaned = []
    for f in fonts:
        for name in f.replace("'", "").replace('"', "").split(","):
            name = name.strip()
            if name and name.lower() not in ("sans-serif", "serif", "monospace", "system-ui", "inherit", "initial"):
                fonts_cleaned.append(name)
    fonts = list(dict.fromkeys(fonts_cleaned))[:20]

    return {
        "colors": colors,
        "fonts": fonts,
        "has_dark_mode": has_dark,
        "has_css_vars": has_css_vars,
        "border_radius_style": radius_style,
    }


# --- Domain detection ---

_INDUSTRY_KEYWORDS = {
    "fintech": ["fintech", "payment", "pay", "bank", "finance", "crypto", "trading", "wallet", "交易", "支付", "金融"],
    "ai-ml": ["ai", "ml", "machine learning", "deep learning", "llm", "gpt", "model", "agent", "人工智能", "机器学习"],
    "developer-tools": ["developer", "devtools", "cli", "api", "sdk", "terminal", "debug", "deploy", "开发工具"],
    "productivity": ["productivity", "task", "todo", "calendar", "schedule", "resume", "cv", "简历", "效率"],
    "saas": ["saas", "platform", "subscription", "tenant", "multi-tenant"],
    "design": ["design", "figma", "sketch", "creative", "brand", "设计"],
    "e-commerce": ["ecommerce", "e-commerce", "shop", "store", "cart", "product", "商城", "电商", "购物"],
    "education": ["education", "learn", "course", "tutorial", "teach", "tutor", "student", "study",
                  "lesson", "curriculum", "quiz", "exam", "practice", "exercise", "homework",
                  "skill", "knowledge", "growth", "training", "diagnosis", "学习计划", "辅导",
                  "教育", "学习", "课程", "教程", "练习", "测验", "知识", "技能", "成长", "训练", "诊断"],
    "entertainment": ["entertainment", "music", "video", "game", "streaming", "media", "娱乐", "音乐", "视频"],
    "healthcare": ["health", "medical", "doctor", "patient", "clinic", "健康", "医疗"],
    "travel-hospitality": ["travel", "hotel", "booking", "flight", "旅游", "酒店", "预订"],
    "social-media": ["social", "chat", "message", "feed", "post", "社区", "社交"],
    "food-beverage": ["food", "recipe", "restaurant", "diet", "nutrition", "food", "饮食", "食谱", "养生"],
    "automotive": ["car", "auto", "vehicle", "汽车"],
    "infrastructure": ["infrastructure", "database", "cloud", "server", "infra", "基础设施"],
    "analytics": ["analytics", "metrics", "monitoring", "dashboard", "统计", "分析", "监控"],
    "content": ["content", "cms", "blog", "article", "内容", "博客"],
}


def _detect_domain(project_path: Path) -> tuple[str | None, str, str, bool]:
    """Detect industry domain. Returns (industry, project_name, description, is_ai_tool)."""
    description = ""
    for doc_file in ["CLAUDE.md", "README.md", "readme.md", "README.rst"]:
        content = _read_file(project_path / doc_file)
        if content:
            description += content + "\n"

    # Also scan component files for domain signals
    component_content = ""
    src_dir = project_path / "src"
    if src_dir.exists():
        for f in src_dir.rglob("*"):
            if not f.is_file() or f.suffix not in (".jsx", ".tsx", ".vue", ".js", ".ts"):
                continue
            if _is_excluded(f):
                continue
            component_content += _read_file(f, max_bytes=5_000) + "\n"
            if len(component_content) > 30_000:
                break

    full_text = description + "\n" + component_content

    if not full_text.strip():
        return None, project_path.name, "", False

    desc_lower = full_text.lower()

    # Detect AI-tool cross-cutting tag
    _AI_TOOL_KEYWORDS = ["zhipu", "openai", "anthropic", "llm", "gpt", "glm", "ai-powered",
                         "ai assistant", "智能", "人工智能", "大模型"]
    is_ai_tool = any(kw in desc_lower for kw in _AI_TOOL_KEYWORDS)

    industry_scores = {}
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        if score > 0:
            industry_scores[industry] = score

    best = None
    if industry_scores:
        best = max(industry_scores, key=industry_scores.get)

    return best, project_path.name, description[:500] if description.strip() else component_content[:500], is_ai_tool


# --- Content type detection ---

_CONTENT_PATTERNS = {
    "forms": [r"<form", r'<input', r'<select', r'<textarea', r"type=\"submit\"",
              r"<Form", r"<Input", r"<Select", r"<Textarea", r"onChange"],
    "tables": [r"<table", r"<thead", r"<tbody", r"<tr>", r"<td"],
    "cards": [r"class=\"[^\"]*card", r"class='[^']*card", r"grid.*card",
              r"className=\"[^\"]*card", r"className='[^']*card", r"<Card"],
    "dashboard": [r"dashboard", r"metric", r"chart", r"analytics", r"stat",
                  r"<Chart", r"<Metric", r"<Stat"],
    "editor": [r"contenteditable", r"<textarea", r"rich-text", r"wysiwyg", r"editor"],
    "navigation": [r"<nav", r"navbar", r"sidebar", r"header.*nav"],
}


def _detect_content_types(project_path: Path) -> list[str]:
    types = []
    html_dirs = [project_path / "templates", project_path / "static", project_path / "src"]
    # Only scan project root if no subdirectory found any HTML
    has_subdirs = any(d.exists() for d in html_dirs)
    if not has_subdirs:
        html_dirs.append(project_path)

    seen = set()
    for d in html_dirs:
        d = d.resolve()
        if d in seen or not d.exists():
            continue
        seen.add(d)
        for f in d.rglob("*"):
            if not f.is_file() or f.suffix not in (".html", ".htm", ".jinja", ".jinja2", ".j2", ".jsx", ".tsx", ".vue"):
                continue
            if _is_excluded(f):
                continue
            content = _read_file(f)
            for ctype, patterns in _CONTENT_PATTERNS.items():
                if any(re.search(p, content, re.IGNORECASE) for p in patterns):
                    if ctype not in types:
                        types.append(ctype)
    return types


# --- User scenario detection ---

_USER_SCENARIO_KEYWORDS = {
    "calm_focus": ["冥想", "专注", "番茄", "pomodoro", "focus", "meditation", "breathing"],
    "playful_learning": ["游戏", "game", "gamification", "badge", "reward", "achievement", "积分", "关卡"],
    "professional_growth": ["职业", "career", "professional", "成长", "提升", "发展", "progress", "growth"],
    "social_collaboration": ["社区", "community", "social", "team", "协作", "collaborate", "分享", "share"],
    "self_improvement": ["习惯", "habit", "goal", "目标", "复盘", "reflection", "journal", "日记", "自我提升"],
}


def _detect_user_scenarios(text: str) -> list[str]:
    text_lower = text.lower()
    matched = []
    for scenario, keywords in _USER_SCENARIO_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(scenario)
    return matched


# --- Emotional goal detection ---

_EMOTIONAL_GOAL_KEYWORDS = {
    "trust": ["专业", "可靠", "安全", "professional", "reliable", "trusted", "权威", "expert"],
    "delight": ["惊喜", "有趣", "fun", "delight", "wonderful", "amazing", "creative"],
    "calm": ["平静", "安静", "简洁", "calm", "minimal", "clean", "peaceful", "禅"],
    "motivation": ["激励", "动力", "motivation", "inspire", "encourage", "进步", "成就"],
    "clarity": ["清晰", "直观", "clarity", "intuitive", "simple", "易懂", "明了"],
}


def _detect_emotional_goals(text: str) -> list[str]:
    text_lower = text.lower()
    matched = []
    for goal, keywords in _EMOTIONAL_GOAL_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(goal)
    return matched


# --- Domain keyword extraction ---

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "and", "but", "or", "nor",
    "not", "so", "yet", "both", "either", "neither", "each", "every",
    "all", "any", "few", "more", "most", "other", "some", "such", "no",
    "only", "own", "same", "than", "too", "very", "just", "because",
    "if", "when", "where", "how", "what", "which", "who", "whom",
    "this", "that", "these", "those", "it", "its", "i", "me", "my",
    "we", "our", "you", "your", "he", "she", "they", "them", "his",
    "her", "their", "about", "up", "also", "new", "use", "using",
    "used", "make", "like", "get", "set", "one", "two", "data",
    "file", "path", "url", "api", "app", "web", "page", "component",
    "function", "return", "import", "export", "default", "const",
    "let", "var", "true", "false", "null", "undefined", "string",
    "number", "object", "array", "class", "style", "div", "span",
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
    "会", "着", "没有", "看", "好", "自己", "这",
}


def _extract_domain_tags(text: str, max_tags: int = 10) -> list[str]:
    """Extract meaningful domain-specific keywords from project text."""
    # Extract words (both English and CJK)
    # English words: 2+ chars, alphanumeric
    english_words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
    # CJK words: consecutive CJK characters (2-4 char segments)
    cjk_segments = re.findall(r"[\u4e00-\u9fff]{2,4}", text)

    all_words = english_words + cjk_segments

    # Count frequencies
    freq = {}
    for w in all_words:
        if w in _STOP_WORDS:
            continue
        if len(w) < 2:
            continue
        freq[w] = freq.get(w, 0) + 1

    # Sort by frequency and return top N
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:max_tags]]


# --- Tailwind signal extraction ---

# Common Tailwind color name to hex mapping
_TAILWIND_COLOR_MAP = {
    "slate": ["#64748b", "#475569", "#334155"],
    "gray": ["#6b7280", "#4b5563", "#374151"],
    "zinc": ["#71717a", "#52525b", "#3f3f46"],
    "neutral": ["#737373", "#525252", "#404040"],
    "stone": ["#78716c", "#57534e", "#44403c"],
    "red": ["#ef4444", "#dc2626", "#b91c1c"],
    "orange": ["#f97316", "#ea580c", "#c2410c"],
    "amber": ["#f59e0b", "#d97706", "#b45309"],
    "yellow": ["#eab308", "#ca8a04", "#a16207"],
    "lime": ["#84cc16", "#65a30d", "#4d7c0f"],
    "green": ["#22c55e", "#16a34a", "#15803d"],
    "emerald": ["#10b981", "#059669", "#047857"],
    "teal": ["#14b8a6", "#0d9488", "#0f766e"],
    "cyan": ["#06b6d4", "#0891b2", "#0e7490"],
    "sky": ["#0ea5e9", "#0284c7", "#0369a1"],
    "blue": ["#3b82f6", "#2563eb", "#1d4ed8"],
    "indigo": ["#6366f1", "#4f46e5", "#4338ca"],
    "violet": ["#8b5cf6", "#7c3aed", "#6d28d9"],
    "purple": ["#a855f7", "#9333ea", "#7e22ce"],
    "fuchsia": ["#d946ef", "#c026d3", "#a21caf"],
    "pink": ["#ec4899", "#db2777", "#be185d"],
    "rose": ["#f43f5e", "#e11d48", "#be123c"],
}

# Regex for Tailwind color classes: bg-blue-500, text-red-600, border-green, etc.
_TW_COLOR_CLASS_RE = re.compile(
    r"(?:bg|text|border|ring|outline|from|via|to)-"
    r"(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|"
    r"cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)"
    r"-(?:50|100|200|300|400|500|600|700|800|900|950)"
)
_TW_DARK_RE = re.compile(r"\bdark:", re.IGNORECASE)
_TW_ROUNDED_RE = re.compile(r"\brounded-(?:none|sm|md|lg|xl|2xl|3xl|full)\b")


def _extract_tailwind_signals(project_path: Path) -> dict:
    """Extract design signals from Tailwind CSS utility classes in component files."""
    colors = []
    has_dark = False
    radius_classes = []

    # Scan src/ directory for component files
    src_dir = project_path / "src"
    scan_dirs = [src_dir] if src_dir.exists() else [project_path]

    for scan_dir in scan_dirs:
        for f in scan_dir.rglob("*"):
            if not f.is_file() or f.suffix not in (".jsx", ".tsx", ".vue", ".html", ".htm"):
                continue
            if _is_excluded(f):
                continue
            content = _read_file(f, max_bytes=20_000)

            # Extract color classes
            color_matches = _TW_COLOR_CLASS_RE.findall(content)
            for color_name in color_matches:
                # Parse: "bg-blue-500" → color_name="blue-500" → name="blue", shade="500"
                parts = color_name.rsplit("-", 1)
                if len(parts) == 2:
                    name, shade = parts
                    hex_colors = _TAILWIND_COLOR_MAP.get(name, [])
                    if hex_colors:
                        colors.append(hex_colors[0])

            if _TW_DARK_RE.search(content):
                has_dark = True

            radius_matches = _TW_ROUNDED_RE.findall(content)
            radius_classes.extend(radius_matches)

    # Convert radius classes to style
    radius_style = "unknown"
    if radius_classes:
        rc_set = set(radius_classes)
        if "rounded-full" in rc_set or "rounded-3xl" in rc_set:
            radius_style = "pill"
        elif "rounded-xl" in rc_set or "rounded-2xl" in rc_set:
            radius_style = "rounded"
        elif "rounded-lg" in rc_set or "rounded-md" in rc_set:
            radius_style = "moderate"
        elif "rounded-none" in rc_set or "rounded-sm" in rc_set:
            radius_style = "sharp"

    return {
        "colors": list(dict.fromkeys(colors))[:30],
        "has_dark_mode": has_dark,
        "border_radius_style": radius_style,
    }


# --- Main scan function ---

def scan_project(project_path: str | Path, industry_hint: str | None = None) -> ProjectProfile:
    project_path = Path(project_path).resolve()
    if not project_path.exists():
        return ProjectProfile(project_name=str(project_path))

    # Tech stack
    tech_stack = _detect_tech_stack(project_path)
    css_framework = _detect_css_framework(project_path)
    if css_framework and css_framework not in tech_stack:
        tech_stack.append(css_framework)

    # CSS signals
    css_signals = _extract_css_signals(project_path)

    # Tailwind signals (supplement CSS signals)
    tw_signals = _extract_tailwind_signals(project_path)

    # Merge colors: CSS first, then Tailwind additions
    merged_colors = list(dict.fromkeys(css_signals["colors"] + tw_signals["colors"]))[:50]

    # Domain (now returns is_ai_tool)
    detected_industry, project_name, description, is_ai_tool = _detect_domain(project_path)
    if industry_hint:
        detected_industry = industry_hint

    # Content types
    content_types = _detect_content_types(project_path)

    # Determine if project has UI
    has_ui = bool(content_types) or bool(merged_colors) or bool(
        any(project_path.rglob(f"*.{ext}")) for ext in [".html", ".htm", ".vue", ".jsx", ".tsx"]
    )

    # Complexity
    type_count = len(content_types)
    css_size = len(merged_colors)
    if type_count >= 4 or css_size > 20:
        complexity = "complex"
    elif type_count >= 2 or css_size > 5:
        complexity = "medium"
    else:
        complexity = "simple"

    # Build full text for scenario/emotion/tag detection
    full_text = description
    # Also read component files for richer context
    src_dir = project_path / "src"
    if src_dir.exists():
        for f in list(src_dir.rglob("*"))[:30]:
            if not f.is_file() or f.suffix not in (".jsx", ".tsx", ".vue", ".js", ".ts"):
                continue
            if _is_excluded(f):
                continue
            full_text += "\n" + _read_file(f, max_bytes=3_000)

    # New detections
    user_scenarios = _detect_user_scenarios(full_text)
    emotional_goals = _detect_emotional_goals(full_text)
    domain_tags = _extract_domain_tags(full_text)

    # Use better border radius from Tailwind if CSS was unknown
    border_radius = css_signals["border_radius_style"]
    if border_radius == "unknown" and tw_signals["border_radius_style"] != "unknown":
        border_radius = tw_signals["border_radius_style"]

    # Use better dark mode from Tailwind if CSS didn't detect it
    has_dark = css_signals["has_dark_mode"] or tw_signals["has_dark_mode"]

    return ProjectProfile(
        tech_stack=tech_stack,
        industry_hint=detected_industry,
        project_name=project_name,
        project_description=description,
        current_colors=merged_colors,
        color_temperature=_classify_color_temperature(merged_colors),
        has_dark_mode=has_dark,
        font_families=css_signals["fonts"],
        border_radius_style=border_radius,
        content_types=content_types,
        complexity_level=complexity,
        has_ui=has_ui,
        user_scenarios=user_scenarios,
        emotional_goals=emotional_goals,
        domain_tags=domain_tags,
        is_ai_tool=is_ai_tool,
    )
