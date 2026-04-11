"""Theme-project matching algorithm.

10-dimensional weighted scoring to rank design themes by project fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from colorsys import rgb_to_hls

from scanner import ProjectProfile
from indexer import ThemeProfile


@dataclass
class ScoredTheme:
    theme: ThemeProfile
    total_score: float = 0.0
    dimension_scores: dict = field(default_factory=dict)
    match_reasons: list[str] = field(default_factory=list)
    mismatch_warnings: list[str] = field(default_factory=list)


# Weights for each scoring dimension (10 dimensions, sum = 1.0)
_WEIGHTS = {
    "industry_match": 0.15,
    "color_temperature": 0.10,
    "mode_preference": 0.10,
    "personality_match": 0.20,
    "complexity_match": 0.10,
    "geometry_match": 0.05,
    "typography_match": 0.05,
    "color_overlap": 0.05,
    "user_scenario_match": 0.15,
    "domain_keyword_match": 0.10,
}


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


def _score_industry(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    if not project.industry_hint:
        return 50.0, "No industry detected — neutral score"
    if not theme.industries:
        return 40.0, "Theme has no industry tags"
    if project.industry_hint in theme.industries:
        return 100.0, f"Direct industry match: {project.industry_hint}"
    # Fuzzy: check if any theme industry keyword appears in project description
    desc_lower = project.project_description.lower()
    for ind in theme.industries:
        if ind.replace("-", " ") in desc_lower or ind in desc_lower:
            return 70.0, f"Partial industry match via description: {ind}"
    # Check broader category alignment
    category_map = {
        "productivity": ["saas", "enterprise", "automation"],
        "saas": ["productivity", "enterprise", "automation"],
        "developer-tools": ["infrastructure", "ai-ml", "analytics"],
        "ai-ml": ["developer-tools", "enterprise", "entertainment"],
        "fintech": ["enterprise", "saas"],
        "design": ["saas", "developer-tools", "creative-tools"],
    }
    related = category_map.get(project.industry_hint, [])
    if any(r in theme.industries for r in related):
        return 55.0, f"Related industry category: {project.industry_hint} ↔ {theme.industries}"
    return 25.0, f"No industry overlap: project={project.industry_hint}, theme={theme.industries}"


def _score_color_temperature(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    if project.color_temperature == "unknown":
        return 50.0, "No existing colors detected — neutral score"
    if project.color_temperature == theme.color_temperature:
        return 100.0, f"Color temperature match: {project.color_temperature}"
    if project.color_temperature == "neutral" or theme.color_temperature == "neutral":
        return 70.0, f"Neutral flexibility: {project.color_temperature} ↔ {theme.color_temperature}"
    return 30.0, f"Color temperature mismatch: {project.color_temperature} vs {theme.color_temperature}"


def _score_mode(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    if not project.has_ui:
        return 60.0, "No existing UI — slight dark-mode preference for developer tools"
    if theme.mode_preference == "dual-mode":
        return 95.0, "Dual-mode theme — works with any preference"
    if project.has_dark_mode and theme.mode_preference == "dark-first":
        return 100.0, "Dark mode support matches dark-first theme"
    if not project.has_dark_mode and theme.mode_preference == "light-first":
        return 100.0, "Light-only project matches light-first theme"
    if project.has_dark_mode and theme.mode_preference == "light-first":
        return 60.0, "Project has dark mode but theme is light-first — adaptable"
    if not project.has_dark_mode and theme.mode_preference == "dark-first":
        return 40.0, "Light-only project with dark-first theme — needs dark mode addition"
    return 50.0, ""


# Chinese-English personality keyword mappings
_PERSONALITY_KEYWORDS = {
    "professional": ["professional", "enterprise", "business", "企业", "专业", "商务", "正式"],
    "minimal": ["minimal", "clean", "simple", "简洁", "简约", "极简"],
    "warm": ["warm", "friendly", "approachable", "温暖", "友好", "亲切"],
    "playful": ["creative", "design", "art", "创意", "设计", "活泼", "有趣", "趣味"],
    "technical": ["tech", "developer", "code", "技术", "开发", "工程师"],
    "luxurious": ["premium", "luxury", "high-end", "高端", "品质", "精致"],
    "modern": ["modern", "contemporary", "新", "创新", "现代"],
    "confident": ["confident", "bold", "strong", "自信", "大胆", "强烈"],
    "precise": ["precise", "accurate", "exact", "精确", "精准"],
    "clean": ["clean", "tidy", "整洁", "干净"],
    "trustworthy": ["trusted", "reliable", "权威", "可信", "可靠"],
    "calm": ["calm", "quiet", "稳重", "平静", "安静"],
    "energetic": ["energetic", "dynamic", "活力", "动感", "年轻"],
    "elegant": ["elegant", "优雅", "高端", "精致"],
    "approachable": ["approachable", "accessible", "易懂", "平易近人"],
    "immersive": ["immersive", "沉浸", "体验"],
    "dramatic": ["dramatic", "戏剧", "震撼"],
    "editorial": ["editorial", "编辑", "出版", "杂志"],
    "irreverent": ["irreverent", "反叛", "有趣", "幽默"],
    "premium": ["premium", "高级", "优质", "精品"],
    "vibrant": ["vibrant", "鲜艳", "丰富", "多彩"],
}


def _score_personality(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    if not project.has_ui and not project.project_description:
        return 50.0, "No signals for personality matching"
    # Infer project personality from description and content types
    desc_lower = project.project_description.lower()
    project_personality = set()
    for personality, keywords in _PERSONALITY_KEYWORDS.items():
        if any(w in desc_lower for w in keywords):
            project_personality.add(personality)

    if not project_personality:
        # Default personality based on content types
        if "dashboard" in project.content_types or "tables" in project.content_types:
            project_personality = {"professional", "technical"}
        elif "forms" in project.content_types:
            project_personality = {"clean", "professional"}
        elif "editor" in project.content_types:
            project_personality = {"minimal", "modern"}
        else:
            project_personality = {"clean", "modern"}

    theme_personality = set(theme.brand_personality)
    if not theme_personality:
        return 50.0, "Theme has no personality tags"
    overlap = project_personality & theme_personality
    if not overlap:
        return 30.0, f"No personality overlap: {project_personality} vs {theme_personality}"
    score = int((len(overlap) / max(len(theme_personality), 1)) * 100)
    score = min(score, 100)
    return float(score), f"Personality match: {', '.join(overlap)}"


def _score_complexity(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    level_map = {"simple": 1, "medium": 2, "complex": 3}
    p_level = level_map.get(project.complexity_level, 2)
    t_level = level_map.get(theme.complexity, 2)
    diff = abs(p_level - t_level)
    if diff == 0:
        return 100.0, f"Complexity match: {project.complexity_level}"
    elif diff == 1:
        return 65.0, f"Slight complexity gap: {project.complexity_level} vs {theme.complexity}"
    else:
        return 30.0, f"Complexity mismatch: {project.complexity_level} vs {theme.complexity}"


def _score_geometry(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    if project.border_radius_style == "unknown":
        return 50.0, "No existing border-radius detected — neutral score"
    if project.border_radius_style == theme.geometric_language:
        return 100.0, f"Geometry match: {project.border_radius_style}"
    # Adjacent styles
    adjacency = {
        "sharp": ["moderate"],
        "moderate": ["sharp", "rounded"],
        "rounded": ["moderate", "pill"],
        "pill": ["rounded"],
        "mixed": ["moderate", "rounded"],
    }
    if theme.geometric_language in adjacency.get(project.border_radius_style, []):
        return 60.0, f"Adjacent geometry: {project.border_radius_style} ↔ {theme.geometric_language}"
    return 35.0, f"Geometry mismatch: {project.border_radius_style} vs {theme.geometric_language}"


def _score_typography(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    if not project.font_families:
        return 60.0, "No existing fonts detected — theme fonts can be adopted"
    theme_fonts_lower = theme.typography_style.lower()
    # Check if project already uses system fonts and theme is system-font based
    if theme_fonts_lower == "system-font":
        if any(f.lower() in ("inter", "system-ui", "-apple-system") for f in project.font_families):
            return 90.0, "System font alignment detected"
        return 60.0, "Theme uses system fonts — easy adoption"
    if theme_fonts_lower == "mono-heavy":
        if any("mono" in f.lower() for f in project.font_families):
            return 95.0, "Monospace alignment detected"
        return 50.0, "Theme is mono-heavy — may need font adjustment"
    # custom-font theme
    for pf in project.font_families:
        if pf.lower() in ("inter", "geist"):
            return 85.0, f"Compatible font detected: {pf}"
    return 55.0, f"Theme uses custom font — project has {', '.join(project.font_families[:3])}"


def _score_color_overlap(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    if not project.current_colors or not theme.accent_colors:
        return 50.0, "Insufficient color data for overlap analysis"
    # Compare project colors with theme accent colors using HSL distance
    min_distance = 999
    for pc in project.current_colors[:10]:
        ph, pl, ps = _hex_to_hsl(pc)
        if ps < 10:  # skip grays
            continue
        for ac in theme.accent_colors[:5]:
            ah, al, a_s = _hex_to_hsl(ac)
            if a_s < 10:
                continue
            # Hue distance (circular)
            hue_dist = min(abs(ph - ah), 360 - abs(ph - ah))
            sat_dist = abs(ps - a_s)
            dist = hue_dist * 0.7 + sat_dist * 0.3
            min_distance = min(min_distance, dist)

    if min_distance < 30:
        return 90.0, "Strong color palette overlap detected"
    elif min_distance < 60:
        return 65.0, "Moderate color alignment"
    elif min_distance < 120:
        return 45.0, "Different color palettes — significant visual change needed"
    return 25.0, "Very different color palettes"


def _score_user_scenario(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    """Score based on user scenario alignment (e.g., calm_focus, playful_learning)."""
    if not project.user_scenarios:
        return 50.0, "No user scenarios detected — neutral score"
    if not theme.user_scenarios:
        return 50.0, "Theme has no scenario tags"
    overlap = set(project.user_scenarios) & set(theme.user_scenarios)
    if overlap:
        score = min(int((len(overlap) / max(len(project.user_scenarios), 1)) * 100), 100)
        return float(max(score, 70)), f"Scenario match: {', '.join(overlap)}"
    # Check if scenarios are related
    _RELATED_SCENARIOS = {
        "calm_focus": ["self_improvement"],
        "playful_learning": ["self_improvement", "social_collaboration"],
        "professional_growth": ["self_improvement", "calm_focus"],
        "social_collaboration": ["playful_learning"],
        "self_improvement": ["calm_focus", "professional_growth"],
    }
    for ps in project.user_scenarios:
        related = _RELATED_SCENARIOS.get(ps, [])
        if any(r in theme.user_scenarios for r in related):
            return 55.0, f"Related scenario: {ps} ↔ {theme.user_scenarios}"
    return 25.0, f"No scenario overlap: {project.user_scenarios} vs {theme.user_scenarios}"


def _score_domain_keywords(project: ProjectProfile, theme: ThemeProfile) -> tuple[float, str]:
    """Score based on domain keyword overlap."""
    if not project.domain_tags:
        return 50.0, "No domain tags detected — neutral score"
    if not theme.domain_tags:
        return 50.0, "Theme has no domain tags"
    p_tags = set(t.lower() for t in project.domain_tags)
    t_tags = set(t.lower() for t in theme.domain_tags)
    overlap = p_tags & t_tags
    if overlap:
        jaccard = len(overlap) / len(p_tags | t_tags) if (p_tags | t_tags) else 0
        score = max(int(jaccard * 150), 70)  # Boost: any keyword overlap = at least 70
        return float(min(score, 100)), f"Domain match: {', '.join(overlap)}"
    return 25.0, f"No domain keyword overlap: {list(p_tags)[:5]} vs {list(t_tags)[:5]}"


def score_theme(project: ProjectProfile, theme: ThemeProfile) -> ScoredTheme:
    """Score a single theme against a project profile."""
    scoring_fns = {
        "industry_match": _score_industry,
        "color_temperature": _score_color_temperature,
        "mode_preference": _score_mode,
        "personality_match": _score_personality,
        "complexity_match": _score_complexity,
        "geometry_match": _score_geometry,
        "typography_match": _score_typography,
        "color_overlap": _score_color_overlap,
        "user_scenario_match": _score_user_scenario,
        "domain_keyword_match": _score_domain_keywords,
    }

    scored = ScoredTheme(theme=theme)
    for dim_name, fn in scoring_fns.items():
        score, reason = fn(project, theme)
        scored.dimension_scores[dim_name] = score
        if score >= 70:
            scored.match_reasons.append(reason)
        elif score <= 35:
            scored.mismatch_warnings.append(reason)

    # Compute weighted total
    total = sum(
        scored.dimension_scores[dim] * weight
        for dim, weight in _WEIGHTS.items()
    )
    scored.total_score = round(total, 1)
    return scored


def score_and_rank(
    project: ProjectProfile,
    themes: list[ThemeProfile],
    top_n: int = 3,
) -> list[ScoredTheme]:
    """Score all themes and return top N ranked by fit."""
    scored_list = [score_theme(project, t) for t in themes]
    scored_list.sort(key=lambda x: x.total_score, reverse=True)
    return scored_list[:top_n]
