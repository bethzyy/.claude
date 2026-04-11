"""Output formatters for UI design recommendations.

Supports JSON (machine-readable), Markdown (human-readable), and CSS Variables formats.
"""

from __future__ import annotations

import json
from scanner import ProjectProfile
from scorer import ScoredTheme


def _quick_colors_from_theme(theme) -> dict:
    """Extract quick color reference from theme data."""
    colors = {}
    if theme.primary_colors:
        colors["background"] = theme.primary_colors[0]
    if theme.accent_colors:
        colors["accent"] = theme.accent_colors[0]
    return colors


def _css_variables_from_theme(theme) -> str:
    """Generate CSS custom properties from theme colors."""
    lines = [":root {"]
    if theme.primary_colors:
        lines.append(f'  --bg-primary: {theme.primary_colors[0]};')
        if len(theme.primary_colors) > 1:
            lines.append(f'  --bg-secondary: {theme.primary_colors[1]};')
        if len(theme.primary_colors) > 2:
            lines.append(f'  --bg-tertiary: {theme.primary_colors[2]};')
    if theme.accent_colors:
        lines.append(f'  --color-accent: {theme.accent_colors[0]};')
        if len(theme.accent_colors) > 1:
            lines.append(f'  --color-accent-hover: {theme.accent_colors[1]};')
    # Mode hint
    if theme.mode_preference == "dark-first":
        lines.append("  /* Dark-mode-first theme */")
    elif theme.mode_preference == "light-first":
        lines.append("  /* Light-mode-first theme */")
    else:
        lines.append("  /* Dual-mode theme */")
    lines.append("}")
    return "\n".join(lines)


def format_json(
    recommendations: list[ScoredTheme],
    project: ProjectProfile,
) -> str:
    """Format output as structured JSON."""
    project_data = {
        "name": project.project_name,
        "tech_stack": project.tech_stack,
        "industry": project.industry_hint,
        "color_temperature": project.color_temperature,
        "has_dark_mode": project.has_dark_mode,
        "font_families": project.font_families[:5],
        "border_radius_style": project.border_radius_style,
        "content_types": project.content_types,
        "complexity": project.complexity_level,
        "has_ui": project.has_ui,
        "user_scenarios": project.user_scenarios,
        "emotional_goals": project.emotional_goals,
        "domain_tags": project.domain_tags[:10],
        "is_ai_tool": project.is_ai_tool,
    }

    recs = []
    for i, rec in enumerate(recommendations, 1):
        theme = rec.theme
        rec_data = {
            "rank": i,
            "theme_name": theme.name,
            "score": rec.total_score,
            "one_line": theme.one_line,
            "match_reasons": rec.match_reasons[:5],
            "mismatch_warnings": rec.mismatch_warnings[:3],
            "dimension_scores": rec.dimension_scores,
            "design_md_path": theme.design_md_path,
            "quick_colors": _quick_colors_from_theme(theme),
            "css_variables_preview": _css_variables_from_theme(theme),
            "theme_details": {
                "industries": theme.industries,
                "color_temperature": theme.color_temperature,
                "mode_preference": theme.mode_preference,
                "brand_personality": theme.brand_personality,
                "geometric_language": theme.geometric_language,
                "complexity": theme.complexity,
                "typography_style": theme.typography_style,
                "user_scenarios": theme.user_scenarios,
                "emotional_goals": theme.emotional_goals,
                "domain_tags": theme.domain_tags,
            },
        }
        recs.append(rec_data)

    output = {
        "project_profile": project_data,
        "recommendations": recs,
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


def format_markdown(
    recommendations: list[ScoredTheme],
    project: ProjectProfile,
) -> str:
    """Format output as human-readable Markdown."""
    lines = []

    # Header
    lines.append(f"# UI Design Theme Recommendations for: {project.project_name}")
    lines.append("")

    # Project profile
    lines.append("## Project Profile")
    lines.append("")
    lines.append(f"- **Tech Stack**: {', '.join(project.tech_stack) if project.tech_stack else 'Unknown'}")
    lines.append(f"- **Industry**: {project.industry_hint or 'Not detected'}")
    lines.append(f"- **Color Temperature**: {project.color_temperature}")
    lines.append(f"- **Dark Mode**: {'Yes' if project.has_dark_mode else 'No'}")
    lines.append(f"- **Fonts**: {', '.join(project.font_families[:3]) if project.font_families else 'Not detected'}")
    lines.append(f"- **Border Radius**: {project.border_radius_style}")
    lines.append(f"- **Content Types**: {', '.join(project.content_types) if project.content_types else 'None detected'}")
    lines.append(f"- **Complexity**: {project.complexity_level}")
    lines.append(f"- **Has UI**: {'Yes' if project.has_ui else 'No'}")
    if project.user_scenarios:
        lines.append(f"- **User Scenarios**: {', '.join(project.user_scenarios)}")
    if project.emotional_goals:
        lines.append(f"- **Emotional Goals**: {', '.join(project.emotional_goals)}")
    if project.domain_tags:
        lines.append(f"- **Domain Tags**: {', '.join(project.domain_tags[:8])}")
    if project.is_ai_tool:
        lines.append("- **AI-Powered**: Yes")
    lines.append("")

    if not project.has_ui:
        lines.append("> **Note**: No existing UI detected. Recommendations are based on project domain and purpose.")
        lines.append("")

    # Recommendations
    lines.append(f"## Top {len(recommendations)} Recommended Themes")
    lines.append("")

    for rank, rec in enumerate(recommendations, 1):
        theme = rec.theme
        lines.append(f"### {rank}. {theme.name} (Score: {rec.total_score}/100)")
        lines.append("")
        lines.append(f"**{theme.one_line}**")
        lines.append("")
        lines.append("**Why it matches:**")
        for reason in rec.match_reasons:
            lines.append(f"- {reason}")
        if rec.mismatch_warnings:
            lines.append("")
            lines.append("**Potential friction:**")
            for warning in rec.mismatch_warnings:
                lines.append(f"- ⚠️ {warning}")
        lines.append("")
        lines.append("**Theme signals:**")
        lines.append(f"- Industries: {', '.join(theme.industries)}")
        lines.append(f"- Color: {theme.color_temperature} | Mode: {theme.mode_preference}")
        lines.append(f"- Personality: {', '.join(theme.brand_personality)}")
        lines.append(f"- Geometry: {theme.geometric_language} | Complexity: {theme.complexity}")
        if theme.user_scenarios:
            lines.append(f"- Scenarios: {', '.join(theme.user_scenarios)}")
        if theme.emotional_goals:
            lines.append(f"- Emotional Goals: {', '.join(theme.emotional_goals)}")
        if theme.domain_tags:
            lines.append(f"- Domain: {', '.join(theme.domain_tags[:8])}")
        lines.append("")

        # CSS Variables preview
        css_vars = _css_variables_from_theme(theme)
        lines.append("**CSS Variables Preview:**")
        lines.append("```css")
        lines.append(css_vars)
        lines.append("```")
        lines.append("")

        # Dimension scores
        lines.append("**Dimension Scores:**")
        for dim, score in rec.dimension_scores.items():
            bar_len = int(score / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"- {dim}: {bar} {score:.0f}")
        lines.append("")
        lines.append(f"**Full DESIGN.md**: `{theme.design_md_path}`")
        lines.append("")

    return "\n".join(lines)


def format_css_variables(
    recommendations: list[ScoredTheme],
    project: ProjectProfile,
) -> str:
    """Format output as CSS custom properties from the top recommendation."""
    if not recommendations:
        return "/* No recommendations available */"

    theme = recommendations[0].theme
    lines = []
    lines.append(f"/* UI Design Theme: {theme.name} */")
    lines.append(f"/* {theme.one_line} */")
    lines.append(f"/* Score: {recommendations[0].total_score}/100 */")
    lines.append("")
    lines.append(_css_variables_from_theme(theme))
    lines.append("")

    if len(recommendations) > 1:
        lines.append("/* Alternative themes: */")
        for rec in recommendations[1:]:
            lines.append(f"/* - {rec.theme.name}: {rec.total_score}/100 — {rec.theme.one_line} */")

    return "\n".join(lines)
