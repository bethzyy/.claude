"""DESIGN.md theme index builder and loader.

Pre-builds a JSON index of all DESIGN.md theme signals for fast matching.
Auto-detects staleness and rebuilds when source files change.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_CLASSIFICATIONS_PATH = _SCRIPT_DIR / "references" / "classifications.json"
_DEFAULT_INDEX_PATH = _SCRIPT_DIR / "references" / "design_index.json"

# Auto-detect DESIGN.md library: look for codedb/awesome-design-md relative to project root
def _auto_detect_design_md_root() -> Path:
    # Walk up from .claude/skills/ui-design/ to find project root, then check codedb/
    candidate = _SCRIPT_DIR
    for _ in range(5):  # .claude/skills/ui-design/ → .claude/skills/ → .claude/ → project_root
        candidate = candidate.parent
        codedb_path = candidate / "codedb" / "awesome-design-md" / "design-md"
        if codedb_path.exists():
            return codedb_path
    # Fallback: hardcoded default
    return Path(r"C:\D\CAIE_tool\MyAIProduct\codedb\awesome-design-md\design-md")

_DEFAULT_DESIGN_MD_ROOT = _auto_detect_design_md_root()


@dataclass
class ThemeProfile:
    name: str = ""
    source_file: str = ""
    industries: list[str] = field(default_factory=list)
    color_temperature: str = "neutral"
    mode_preference: str = "light-first"
    brand_personality: list[str] = field(default_factory=list)
    geometric_language: str = "moderate"
    complexity: str = "medium"
    typography_style: str = "custom-font"
    one_line: str = ""
    accent_colors: list[str] = field(default_factory=list)
    primary_colors: list[str] = field(default_factory=list)
    design_md_path: str = ""
    user_scenarios: list[str] = field(default_factory=list)
    emotional_goals: list[str] = field(default_factory=list)
    domain_tags: list[str] = field(default_factory=list)


_HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
_FONT_RE = re.compile(r"font-family\s*:\s*([^;}{,\n]+)", re.IGNORECASE)


def _extract_colors_from_design_md(content: str) -> tuple[list[str], list[str]]:
    """Extract primary and accent colors from a DESIGN.md file.

    Returns (primary_colors, accent_colors) based on section context.
    """
    all_colors = list(dict.fromkeys(_HEX_RE.findall(content)))
    primary = []
    accent = []
    for c in all_colors:
        if len(c) in (3, 6):
            # Find context around this color
            idx = content.find(f"#{c}")
            if idx > 0:
                context = content[max(0, idx - 80):idx + 80].lower()
                if any(kw in context for kw in ["accent", "brand", "cta", "primary"]):
                    accent.append(f"#{c}")
                elif any(kw in context for kw in ["background", "surface", "canvas", "page"]):
                    primary.append(f"#{c}")
    return primary[:10], accent[:10]


def _extract_fonts_from_design_md(content: str) -> list[str]:
    fonts = _FONT_RE.findall(content)
    cleaned = []
    for f in fonts:
        name = f.strip().strip("'\"")
        if name and name.lower() not in ("sans-serif", "serif", "monospace", "system-ui"):
            cleaned.append(name)
    return list(dict.fromkeys(cleaned))[:10]


def _load_classifications() -> dict:
    if _CLASSIFICATIONS_PATH.exists():
        try:
            return json.loads(_CLASSIFICATIONS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def build_index(
    design_md_root: Path = _DEFAULT_DESIGN_MD_ROOT,
    output_path: Path = _DEFAULT_INDEX_PATH,
) -> list[ThemeProfile]:
    """Build theme index from DESIGN.md files + classifications.json."""
    classifications = _load_classifications()
    themes = []

    if not design_md_root.exists():
        print(f"[WARNING] Design MD root not found: {design_md_root}", file=__import__("sys").stderr)
        return themes

    for theme_dir in sorted(design_md_root.iterdir()):
        if not theme_dir.is_dir():
            continue
        design_md = theme_dir / "DESIGN.md"
        if not design_md.exists():
            continue

        theme_name = theme_dir.name
        content = design_md.read_text(encoding="utf-8", errors="ignore")

        # Get manual classifications
        cls = classifications.get(theme_name, {})

        # Extract auto signals
        primary_colors, accent_colors = _extract_colors_from_design_md(content)

        theme = ThemeProfile(
            name=theme_name,
            source_file=str(design_md),
            industries=cls.get("industries", []),
            color_temperature=cls.get("color_temperature", "neutral"),
            mode_preference=cls.get("mode_preference", "light-first"),
            brand_personality=cls.get("brand_personality", []),
            geometric_language=cls.get("geometric_language", "moderate"),
            complexity=cls.get("complexity", "medium"),
            typography_style=cls.get("typography_style", "custom-font"),
            one_line=cls.get("one_line", ""),
            accent_colors=accent_colors,
            primary_colors=primary_colors,
            design_md_path=str(design_md),
            user_scenarios=cls.get("user_scenarios", []),
            emotional_goals=cls.get("emotional_goals", []),
            domain_tags=cls.get("domain_tags", []),
        )
        themes.append(theme)

    # Write index
    output_path.parent.mkdir(parents=True, exist_ok=True)
    index_data = [asdict(t) for t in themes]
    output_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] Built index with {len(themes)} themes → {output_path}", file=__import__("sys").stderr)
    return themes


def is_index_stale(
    design_md_root: Path = _DEFAULT_DESIGN_MD_ROOT,
    index_path: Path = _DEFAULT_INDEX_PATH,
) -> bool:
    """Check if the index needs rebuilding."""
    if not index_path.exists():
        return True
    index_mtime = index_path.stat().st_mtime
    for theme_dir in design_md_root.iterdir():
        if not theme_dir.is_dir():
            continue
        design_md = theme_dir / "DESIGN.md"
        if design_md.exists() and design_md.stat().st_mtime > index_mtime:
            return True
    # Also check classifications
    if _CLASSIFICATIONS_PATH.exists() and _CLASSIFICATIONS_PATH.stat().st_mtime > index_mtime:
        return True
    return False


def load_index(
    index_path: Path = _DEFAULT_INDEX_PATH,
    design_md_root: Path = _DEFAULT_DESIGN_MD_ROOT,
    force_reindex: bool = False,
) -> list[ThemeProfile]:
    """Load theme index, rebuilding if stale."""
    if force_reindex or is_index_stale(design_md_root, index_path):
        themes = build_index(design_md_root, index_path)
    else:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            themes = [ThemeProfile(**d) for d in data]
        except (json.JSONDecodeError, OSError, TypeError):
            themes = build_index(design_md_root, index_path)
    return themes
