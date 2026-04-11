---
name: ui-design
description: "UI设计匹配与推荐skill - 分析项目UI特征，从58个真实网站设计系统（DESIGN.md）中推荐最佳匹配并指导应用。ALWAYS use this skill when user wants to 'design UI', 'pick a design theme', 'recommend a design system', 'match design style', 'apply design', 'choose colors and fonts', 'create visual identity', 'what design style should I use', 'find matching design', 'style the frontend', 'pick a color palette', 'suggest a UI theme', 'apply DESIGN.md', '设计界面', '选择设计主题', '推荐设计风格', '匹配设计系统', '美化界面', '选择配色', '选择字体', '应用设计规范', '项目该用什么设计', '找一个匹配的设计', '推荐界面风格', '界面改版', '提升界面设计', '应该用什么设计风格', or discusses UI design, visual identity, theme selection, design system application, color palette, typography, or interface styling."
version: 1.0.0
entry_point: main.py
author: Claude Code
tags: [ui, design, theme, recommendation, css, visual, styling]
---

# UI Design Skill

Analyze a project's UI characteristics and recommend the best-matching design theme from a curated library of 58 real-world design systems.

## What It Does

1. **Scans** the target project: tech stack, CSS colors/fonts/radius, dark mode, domain, content types
2. **Scores** all 58 themes using 8-dimensional weighted matching (industry, color temperature, mode, personality, complexity, geometry, typography, color overlap)
3. **Recommends** top N themes with detailed reasoning and CSS variable previews
4. **Guides** application of the chosen design to the project

## When to Use

- User wants to improve or establish the visual design of a project
- User is starting a new project and needs a design direction
- User asks about colors, typography, or overall visual style
- User wants to "make it look professional" or "match a design system"

## How to Invoke

### Full Analysis (recommend themes for a project)
```bash
python <skill_path>/main.py <project_directory> --top 3
```

### With Hints (bias toward a specific style)
```bash
python <skill_path>/main.py <project_directory> --industry fintech --style dark
```

### Human-readable report
```bash
python <skill_path>/main.py <project_directory> --output markdown
```

### CSS Variables only (from top recommendation)
```bash
python <skill_path>/main.py <project_directory> --output css-variables
```

### List All Available Themes
```bash
python <skill_path>/main.py --list-themes
```

### Force Rebuild Theme Index
```bash
python <skill_path>/main.py <project_directory> --force-reindex
```

## Understanding the Output

The JSON output contains:

- `project_profile`: What the scanner detected about the project
  - `tech_stack`: Detected frameworks (flask, react, tailwind, etc.)
  - `industry`: Detected industry domain
  - `color_temperature`: warm/cool/neutral
  - `has_dark_mode`: Whether dark mode CSS exists
  - `font_families`: Fonts found in CSS
  - `border_radius_style`: sharp/moderate/rounded/pill
  - `content_types`: forms/tables/cards/dashboard/editor
  - `complexity`: simple/medium/complex

- `recommendations`: Ranked list of theme matches
  - `score`: 0-100 fit score (weighted across 8 dimensions)
  - `match_reasons`: Why this theme fits (scores ≥ 70)
  - `mismatch_warnings`: Potential friction points (scores ≤ 35)
  - `design_md_path`: Absolute path to the full DESIGN.md file
  - `quick_colors`: Key colors for immediate use
  - `css_variables_preview`: Ready-to-use CSS custom properties
  - `theme_details`: Full theme signal breakdown

## Applying a Recommended Theme

After running the skill and presenting recommendations to the user:

### Step 1: Let the user choose
Show the top 3 recommendations with scores and let the user pick.

### Step 2: Read the full DESIGN.md
Read the DESIGN.md from `design_md_path`. Pay special attention to:
- **Section 2 (Color Palette)**: Complete color system with semantic roles
- **Section 3 (Typography)**: Font families, hierarchy table, size/weight/spacing
- **Section 4 (Component Stylings)**: Buttons, cards, inputs, navigation specifics
- **Section 9 (Agent Prompt Guide)**: Ready-to-use component prompts — USE THESE

### Step 3: Generate CSS variables
Create or update the project's CSS with `:root { }` custom properties based on the theme's color palette.

### Step 4: Apply component styles
Use the DESIGN.md Section 4 specifications to update:
- Buttons (background, text, padding, radius, shadow, hover/focus states)
- Cards (background, border, radius, shadow)
- Inputs (background, border, radius, focus ring)
- Navigation (layout, link styles, CTA buttons)

### Step 5: Apply typography
Set font-family, font-size hierarchy, line-height, and letter-spacing per Section 3.

### Step 6: Apply layout
Implement spacing system, grid, and whitespace philosophy per Section 5.

### Important Rules
- **Always show recommendations before making changes** — let the user choose
- **Respect existing tech stack** — don't introduce React/Vue into Flask projects
- **Read Section 9 (Agent Prompt Guide)** first — it has ready-to-use prompts
- **Reference specific color names and hex values** from the DESIGN.md
- **For Flask/Jinja2 projects**: modify CSS files and template layouts
- **If project has no UI**: still provide recommendations based on domain
- **The skill works for ANY project directory**, not just under MyAIProduct
