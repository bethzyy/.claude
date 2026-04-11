#!/usr/bin/env python3
"""UI Design Skill — Analyze a project and recommend the best-matching design theme.

Usage:
    python main.py <project_path> [options]

Options:
    --top N           Number of recommendations (default: 3)
    --industry HINT   Industry hint to override auto-detection
    --style HINT      Style hint: dark, minimal, colorful, warm, cool
    --output FORMAT   Output format: json (default), markdown, css-variables
    --force-reindex   Force regeneration of theme index
    --list-themes     List all available themes (no project needed)
"""

from __future__ import annotations

import argparse
import io
import sys
import json
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add skill directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scanner import scan_project, ProjectProfile
from indexer import load_index, build_index, _DEFAULT_DESIGN_MD_ROOT
from scorer import score_and_rank
from formatters import format_json, format_markdown, format_css_variables


def list_themes(design_md_root: Path = _DEFAULT_DESIGN_MD_ROOT) -> None:
    """List all available themes with their key signals."""
    themes = load_index(design_md_root=design_md_root)
    if not themes:
        print("[ERROR] No themes found. Check design_md_root path.", file=sys.stderr)
        sys.exit(1)

    output = []
    for t in themes:
        output.append({
            "name": t.name,
            "industries": t.industries,
            "color_temperature": t.color_temperature,
            "mode_preference": t.mode_preference,
            "brand_personality": t.brand_personality,
            "geometric_language": t.geometric_language,
            "complexity": t.complexity,
            "typography_style": t.typography_style,
            "one_line": t.one_line,
            "design_md_path": t.design_md_path,
        })
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="UI Design Skill — Recommend design themes for your project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ./my-project --top 3
  python main.py ./my-project --industry fintech --style dark
  python main.py ./my-project --output markdown
  python main.py --list-themes
        """,
    )
    parser.add_argument("project_path", nargs="?", help="Path to the project directory")
    parser.add_argument("--top", type=int, default=3, help="Number of recommendations (default: 3)")
    parser.add_argument("--industry", type=str, default=None, help="Industry hint (e.g., fintech, ai-ml, productivity)")
    parser.add_argument("--style", type=str, default=None, help="Style hint: dark, minimal, colorful, warm, cool")
    parser.add_argument("--output", type=str, default="json", choices=["json", "markdown", "css-variables"], help="Output format")
    parser.add_argument("--design-md-root", type=str, default=None, help="Path to DESIGN.md library root (default: auto-detected)")
    parser.add_argument("--force-reindex", action="store_true", help="Force regeneration of theme index")
    parser.add_argument("--list-themes", action="store_true", help="List all available themes")

    args = parser.parse_args()

    if args.list_themes:
        design_md_root = Path(args.design_md_root).resolve() if args.design_md_root else _DEFAULT_DESIGN_MD_ROOT
        list_themes(design_md_root=design_md_root)
        return

    if not args.project_path:
        parser.print_help()
        print("\n[ERROR] project_path is required (unless using --list-themes)", file=sys.stderr)
        sys.exit(1)

    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"[ERROR] Project path does not exist: {project_path}", file=sys.stderr)
        sys.exit(1)

    # Step 1: Scan project
    project = scan_project(project_path, industry_hint=args.industry)

    # Apply style hints
    if args.style:
        style_lower = args.style.lower()
        if style_lower == "dark":
            project.has_dark_mode = True
        elif style_lower == "warm":
            project.color_temperature = "warm"
        elif style_lower == "cool":
            project.color_temperature = "cool"
        elif style_lower == "minimal":
            project.color_temperature = "neutral"
            project.content_types = [ct for ct in project.content_types if ct in ("forms", "navigation")]
            if not project.content_types:
                project.complexity_level = "simple"
        elif style_lower == "colorful":
            project.color_temperature = "warm"
            project.complexity_level = "complex"

    # Step 2: Load theme index
    design_md_root = Path(args.design_md_root).resolve() if args.design_md_root else _DEFAULT_DESIGN_MD_ROOT
    themes = load_index(design_md_root=design_md_root, force_reindex=args.force_reindex)
    if not themes:
        print("[ERROR] No themes loaded. Check DESIGN.md library path.", file=sys.stderr)
        sys.exit(1)

    # Step 3: Score and rank
    recommendations = score_and_rank(project, themes, top_n=args.top)

    # Step 4: Format output
    if args.output == "json":
        print(format_json(recommendations, project))
    elif args.output == "markdown":
        print(format_markdown(recommendations, project))
    elif args.output == "css-variables":
        print(format_css_variables(recommendations, project))


if __name__ == "__main__":
    main()
