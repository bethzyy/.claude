---
name: toutiao-img
description: This skill should be used when the user asks to "add images to article", "generate article illustrations", "create 配图", "add article pictures", or discusses generating AI images for Toutiao articles. Automatically analyzes article content and generates contextual images with strategic placement.
version: 3.0.0
---

# Toutiao Article Image Generator

Generate AI-powered contextual images for Toutiao articles and automatically insert them at strategic positions.

## What Changed in v3.0.0

- **🏗️ Architecture Migration to Anthropic Official Standard**: Complete migration to single-location architecture
  - **NEW LOCATION**: All code now in `.claude/skills/toutiao-img/scripts/` (official standard)
  - **OLD LOCATION**: `skills/toutiao-img/` (deprecated, dual-location architecture)
  - **Backward Compatible**: Existing commands still work through wrapper script
  - **Command Change**: Use `python .claude/skills/toutiao-img/main.py` or just `/skill toutiao-img`
  - **Benefits**: Unified structure, easier maintenance, consistent with other skills
  - **Migration**: Part of global skills architecture standardization (2026-03-08)
  - **Dependency Update**: Updated image-gen subprocess calls to use new location

## What Changed in v2.1.5

- **Semantic Image Naming**: Images now use position-based filenames `insertion_point_N.jpg`
  - **Problem**: Old naming `img_0_timestamp.jpg` made it impossible to verify which insertion point each image belongs to
  - **Example**: User couldn't tell if `img_0_20260304_145446.jpg` was for insertion point 1, 2, or 3
  - **Solution**: Rename to `insertion_point_1.jpg`, `insertion_point_2.jpg`, `insertion_point_3.jpg`
  - **Benefits**:
    - **Position Clarity**: Filename directly expresses the insertion position
    - **Strict Reuse**: Images are matched by position - no risk of wrong placement
    - **Debug-Friendly**: Opening the folder immediately shows each image's purpose
    - **Better UX**: No need to check HTML to understand image usage
- **Improved Reuse Logic**: Position-based matching is more rigorous than alphabetical sorting
- **New Functions**:
  - `find_existing_images_by_position()`: Finds images by position number
  - `call_image_gen_skill_with_prefixes()`: Generates images with custom filename prefixes
- **Smart Partial Reuse**: When some images exist, only generates missing positions
  - Example: If positions 1 and 3 exist but 2 is missing, only generates position 2

## What Changed in v2.1.4

- **Image Reuse**: AI-generated images are now automatically reused to avoid wasteful regeneration
  - **Problem**: Every run regenerated all images, even when existing images were perfectly usable
  - **Example**: Re-running to update table styles would also regenerate AI images unnecessarily
  - **Solution**: Check `output_dir/img_*.jpg` for existing images before generating
  - **Behavior**:
    - If 3+ images exist: reuse all, skip AI generation entirely
    - If 1-2 images exist: reuse existing, generate only missing ones
    - If 0 images exist: generate all as before
  - **Benefits**:
    - Saves time (skip 30-60 seconds per image)
    - Conserves API quota (Seedream, Gemini, etc.)
    - Faster iteration when updating table styles or re-running for other reasons
  - **Note**: Table images (`table_*.jpg`) are still regenerated each run (style may change)
- **Smart Detection**: Uses `glob('img_*.jpg')` to find existing AI images
- **Efficient Workflow**: Re-running skill is now instant when images already exist

## What Changed in v2.1.3

- **Optimized Table Styling**: Tables now use fixed 600px width instead of 100%
  - **Problem**: Tables with 100% width were too wide with excessive whitespace
  - **Solution**: Fixed width of 600px provides optimal width for mobile and desktop
  - **Result**: Tables are more compact and better proportioned
- **Increased Table Font Size**: Font size increased from 14px to 24px
  - **Problem**: 14px font was too small for comfortable reading
  - **Solution**: 24px font improves readability by 71%
  - **Result**: Table content is now much easier to read on all devices
- **Reduced Table Padding**: Padding reduced from 14px to 8px
  - **Problem**: Excessive padding wasted space and made tables look sparse
  - **Solution**: 8px padding minimizes whitespace while maintaining readability
  - **Result**: Tables are more compact with better content density
- **Summary**: Table images are now mobile-friendly, easier to read, and have minimal wasted space

## What Changed in v2.1.0

- **Table-to-Image Conversion**: Automatically converts HTML `<table>` elements to `<img>` elements to preserve formatting on Toutiao platform
- **Context-Aware Image Prompts**: Uses GLM-4-flash to analyze article content and generate specific, relevant image prompts
- **Improved Image Relevance**: Generated images now match article content (e.g., flowcharts for technical articles, architecture diagrams for framework guides)
- **Removed Generic Prompts**: No longer uses generic default prompts that produced irrelevant images

## What Changed in v2.1.2

- **Bugfix**: Directory names now use readable document names instead of hash values
  - Example: `images/Claude-Code原生Agent完全指南-头条版/` instead of `images/562b34d3/`
  - Windows 10+ has full UTF-8 path support - no more encoding issues
- **Bugfix**: Fixed insertion point 2 failure after table conversion
  - **Root Cause**: Tables were converted to images BEFORE AI images were inserted
  - Insertion point 2 relied on `</table>` tags which were already converted
  - **Fix**: Reversed workflow - insert AI images FIRST, then convert tables
- **Improved**: All AI images now correctly inserted (no more unused images)
  - Before: img_0 ✓, img_1 ✗ (failed), img_2 ✓, img_3 ✗ (extra), img_4 ✗ (extra)
  - After: img_0 ✓, img_1 ✓, img_2 ✓ (all inserted correctly)

## What Changed in v2.1.1

- **Bugfix**: Fixed table image path issue - tables now correctly reference `images/<hash>/` prefix
- **Improved**: Path calculation now uses relative paths from HTML file to image directory
- **Validation**: All generated images (tables + AI) now display correctly in browser
- **Code Fix**: Updated `table_converter.py` to accept `html_file_path` parameter for proper relative path calculation

## What Changed in v2.0.1

- **Battle-Tested**: Successfully generated illustrations for 13,260-character technical article
- **Confirmed Reliability**: All 3 images generated and inserted correctly
- **Validated Output**: Image paths working in generated HTML

## What Changed in v2.0.0

- **Architecture Refactoring**: Image generation delegated to `image-gen` skill for better modularity
- **Improved Code Organization**: HTML processing logic extracted to `article_illustrator.py`
- **Backward Compatible**: Existing command-line usage unchanged
- **Better Reusability**: Other skills can now use `image-gen` independently

## Table-to-Image Conversion

**Problem**: HTML tables render incorrectly when published to Toutiao
- Column misalignment
- Border/style loss
- Cell content overflow

**Solution**: Automatically convert `<table>` elements to `<img>` elements

**Implementation**:
- Uses Selenium WebDriver with Chrome to capture table screenshots
- Applies professional styling (blue headers, alternating row colors)
- **Optimized dimensions**: Fixed 600px width, 24px font size, 8px padding (v2.1.3)
- Pixel-perfect rendering preserves exact formatting
- Fallback: Skips conversion if Chrome not available (keeps original tables)

**Table Styling Configuration** (v2.1.3):
```css
table {
    width: 600px;           /* Fixed width for optimal display */
    font-size: 24px;         /* Large, readable font */
    margin: 10px auto;       /* Centered with spacing */
}
th {
    padding: 8px;            /* Minimal padding */
    background-color: #0e639c;  /* Blue header */
    color: white;
    font-size: 24px;
}
td {
    padding: 8px;            /* Minimal padding */
    font-size: 24px;
}
```

**Example**:
```html
<!-- Before -->
<table>
  <tr><th>Agent</th><th>Description</th></tr>
  <tr><td>Explore</td><td>Fast codebase exploration</td></tr>
</table>

<!-- After -->
<p style="text-align: center;">
  <img src="images/doc_hash/table_0_20260304_120000.jpg" alt="表格 1">
</p>
<p style="text-align: center; color: #888;">表 1</p>
```

## Context-Aware Image Generation

**Problem**: Generic prompts produce irrelevant images
- Old: "Chinese traditional culture main concept visualization"
- Expected: "Agent Teams architecture diagram with workflow"

**Solution**: Two-stage AI content analysis

**Stage 1: Content Analysis** (`extract_content_key_points()`)
```python
# Uses GLM-4-flash to analyze article
{
    "main_topic": "Claude Code's 5 Native Agents",
    "key_concepts": ["Agent Teams", "workflow", "specialized tools"],
    "visual_opportunities": [
        {
            "section": "Agent Teams Architecture",
            "suggested_image_type": "architecture diagram",
            "prompt_hint": "Show 5 agents working together"
        }
    ]
}
```

**Stage 2: Prompt Generation** (`generate_context_aware_prompts()`)
- Generates specific English prompts for each visual opportunity
- Includes technical details (arrows, color-coding, icons)
- Optimized for AI image generation models

**Example Output**:
```
1. "Technical architecture diagram showing Agent Teams system with 5 specialized
    agents (Explore, Plan, General-Purpose, Statusline-Setup, Guide). Central
    coordination hub, workflow arrows showing agent collaboration..."

2. "Split comparison diagram: traditional single AI vs Agent Teams paradigm,
    visual contrast with icons, flow arrows, and efficiency metrics..."
```

## Dependencies

- **Requires**: `image-gen` skill (v2.0.0+) with 7-level fallback chain
- **Environment**: `ZHIPU_API_KEY` environment variable
- **Optional**: `VOLCANO_API_KEY`, `ANTIGRAVITY_API_KEY` for additional fallback levels

## How to Use

**Command Format**:
```
python C:/D/CAIE_tool/MyAIProduct/.claude/skills/toutiao-img/main.py <html_file_path> [style] [count]
```

**Parameters**:
- `html_file_path` (required): Path to article HTML file
- `style` (optional): Image style (realistic/artistic/cartoon/technical)
- `count` (optional): Number of images to generate (default: 3)

**Examples**:
```bash
# Basic usage
python .claude/skills/toutiao-img/main.py article.html

# With style and count
python .claude/skills/toutiao-img/main.py article.html artistic 5

# Real-world example (tested)
python .claude/skills/toutiao-img/main.py \
  "post/article/他山之石/Claude-Code原生Agent完全指南-头条版.html" \
  realistic 3
```

## Output Files

- **HTML**: `{original_name}-images.html` - Article with inserted images
- **Images**: `images/<document_name>/` - Generated image files (readable name, not hash)

## Real-World Usage Example

**Article**: `Claude-Code原生Agent完全指南-头条版.html` (13,260 characters)

**Execution**:
```bash
python .claude/skills/toutiao-img/main.py \
  "post/article/他山之石/Claude-Code原生Agent完全指南-头条版.html" \
  realistic 3
```

**Results**:
- ✅ Generated 3 images (177-214 KB each)
- ✅ Images inserted at lines 132, 193, 294
- ✅ Output file: 24 KB
- ✅ Processing time: ~45 seconds

**Generated Images** (v2.1.5 with semantic naming):
1. `insertion_point_1.jpg` (177-220 KB) - 第1个插入点
2. `insertion_point_2.jpg` (180-215 KB) - 第2个插入点
3. `insertion_point_3.jpg` (175-210 KB) - 第3个插入点

**Note**: v2.1.5 uses position-based filenames for easy identification and reliable reuse.

## Best Practices

1. **File Naming**: Original filenames with Chinese characters work correctly
2. **Path Handling**: Both relative and absolute paths supported
3. **Long Articles**: Tested with 13,260+ characters - no issues
4. **Image Quality**: CogView-3-flash produces consistent results
5. **Output Size**: Image files range 150-220 KB (good quality/size balance)

## Version History

- **v2.1.5** (2026-03-04): Semantic image naming scheme
  - **New**: Position-based filenames `insertion_point_N.jpg` for clarity
  - **Improved**: Image reuse logic now matches by position (not alphabetical order)
  - **Added**: `find_existing_images_by_position()` function for precise lookup
  - **Added**: `call_image_gen_skill_with_prefixes()` for custom filename support
  - **Benefit**: Filenames clearly express purpose - no need to check HTML
  - **Benefit**: Strict position matching prevents incorrect image reuse
- **v2.1.4** (2026-03-04): Image reuse optimization
  - **New**: Automatic detection and reuse of existing AI images
  - **Benefit**: Saves 30-60 seconds per image when re-running
  - **Benefit**: Conserves API quota by skipping unnecessary generation
- **v2.1.2** (2026-03-04): Bugfix - Directory names + insertion point 2 fix
  - **Fixed**: Directory names now use readable document names (no more hash)
  - **Fixed**: Insertion point 2 now works correctly after table conversion
  - **Root Cause**: Tables were converted before AI images, breaking `</table>` insertion
  - **Solution**: Reversed workflow - insert AI images first, then convert tables
  - **Result**: All AI images now correctly inserted (img_0, img_1, img_2)
- **v2.1.1** (2026-03-04): Bugfix - Table image path correction
  - **Fixed**: Table images now include correct `images/<hash>/` prefix
  - **Improved**: Path calculation using `html_file_path` parameter
  - **Validated**: All images (tables + AI) display correctly in browser
  - **Code Change**: Updated `table_converter.py` and `article_illustrator.py`
- **v2.1.0** (2026-03-04): Table conversion + context-aware prompts
  - **New Feature**: Automatic table-to-image conversion using Selenium
  - **New Feature**: Context-aware AI prompt generation with GLM-4-flash
  - **Improved**: Image prompts now match article content (flowcharts, diagrams, etc.)
  - **Removed**: Generic default prompts that produced irrelevant images
  - **Fixed**: UTF-8 encoding issues in AI prompt generation
- **v2.0.1** (2026-03-04): Production validation
  - Successfully tested with 13,260-character technical article
  - Generated 3 high-quality images (177-214 KB each)
  - Confirmed image insertion logic works correctly
  - Validated file organization (images/<document_name>/)
- **v2.0.0** (2026-03-04): Architecture refactoring
  - Image generation delegated to `image-gen` skill
  - HTML processing extracted to `article_illustrator.py`
  - Backward compatible
- **v1.2.0** (2026-03-04): Improved image organization
- **v1.1.0** (2026-03-03): Fixed image insertion bugs
- **v1.0.0**: Initial release

See `.claude/skills/toutiao-img/SKILL.md` for full documentation.
