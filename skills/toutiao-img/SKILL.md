---
name: toutiao-img
description: This skill should be used when the user asks to "add images to article", "generate article illustrations", "create 配图", "add article pictures", or discusses generating AI images for Toutiao articles. Automatically analyzes article content and generates contextual images with strategic placement.
version: 1.1.0
---

# Toutiao Article Image Generator

Generate AI-powered contextual images for Toutiao articles and automatically insert them at strategic positions.

## When This Skill Applies

This skill activates when the user's request involves:
- Adding images or illustrations to a Toutiao article
- Generating AI images for HTML articles
- Creating article 配图 (illustrations)
- Enhancing articles with visual content
- Publishing to Toutiao platform with images

## How to Use

**Command Format**:
```
python C:/D/CAIE_tool/MyAIProduct/skills/toutiao-img/add_images_to_toutiao_article.py <html_file_path> [style] [count]
```

**Parameters**:
- `html_file_path` (required): Path to article HTML file
- `style` (optional): Image style
  - `realistic` - Professional photography (default)
  - `artistic` - Creative and elegant
  - `cartoon` - Colorful illustration
  - `technical` - Clean infographics
- `count` (optional): Number of images to generate (default: 3)

**Examples**:
```bash
# Basic usage
python skills/toutiao-img/add_images_to_toutiao_article.py article.html

# With style and count
python skills/toutiao-img/add_images_to_toutiao_article.py article.html artistic 5

# Absolute path
python C:/D/CAIE_tool/MyAIProduct/skills/toutiao-img/add_images_to_toutiao_article.py "C:/path/to/article.html"
```

## What This Skill Does

1. **Analyzes Article Content**
   - Extracts title from `<title>` or `<h1>` tag
   - Extracts body content from `<body>` tag

2. **Generates Contextual Prompts**
   - Uses GLM-4.6 AI to analyze article content
   - Creates relevant prompts for each image:
     - Image 1: Core concept visualization (after introduction)
     - Image 2: Detailed content illustration (after tables/comparisons)
     - Image 3: Practical application scenario (after case studies)

3. **Generates AI Images**
   - 7-level fallback chain ensures high success rate:
     1. Seedream 5.0 (2048x2048, highest quality)
     2. Seedream 4.5 (2048x2048)
     3. Seedream 4.0 (2048x2048)
     4. Seedream 3.0 t2i (1024x1024, free tier)
     5. Antigravity multi-model fallback
     6. CogView-3-flash (ZhipuAI)
     7. Pollinations (free service, last resort)

4. **Inserts Images Strategically**
   - Image 1: After introduction (before first `<h2>`)
   - Image 2: After comparison tables (after `</table>`, before next heading)
   - Image 3: At 3rd major section (after 3rd `<h2>` tag)

5. **Generates Output HTML**
   - Creates new file with `-images` suffix
   - Professional styling (650px max width, rounded corners, shadows)
   - Images saved in same directory as HTML file

## Output Files

- **HTML**: `{original_name}-images.html` - Article with inserted images
- **Images**: `article_img{N}_{desc}_{timestamp}.jpg` - Generated image files

## Image Specifications

- Size: 1024x1024 or 2048x2048
- Format: JPEG, quality 95%
- Max display width: 650px (responsive)
- Styling: Rounded corners (8px), subtle shadow

## Environment Variables

**Required**:
```bash
ZHIPU_API_KEY=your_api_key_here
```

**Optional**:
```bash
VOLCANO_API_KEY=your_key         # For Seedream models
ANTIGRAVITY_API_KEY=your_key     # For fallback models
```

## Publishing Steps

1. Open generated `*-images.html` in browser
2. Select all (Ctrl+A)
3. Copy (Ctrl+C)
4. Paste into Toutiao editor
5. Manually upload the generated image files

## Best Practices

- Ensure articles have clear structure (title, introduction, body, case studies)
- Recommended article length: 500+ words for better prompt generation
- Keep image style consistent for same article
- For technical docs, use `technical` style
- For lifestyle content, use `artistic` style
- For business articles, use `realistic` style (default)

## Troubleshooting

**Issue**: "UnicodeEncodeError: 'gbk' codec can't encode"
- **Cause**: Unicode symbols not supported by Windows GBK encoding
- **Status**: Fixed - uses ASCII equivalents [OK], [ERROR], [WARNING]

**Issue**: Images not displaying in generated HTML
- **Cause**: Incorrect relative path
- **Status**: Fixed - images saved in same directory as HTML

**Issue**: API call fails
- **Cause**: Invalid API key or insufficient balance
- **Solution**: Verify `ZHIPU_API_KEY` environment variable

**Issue**: Image generation timeout
- **Cause**: Network issues or API busy
- **Solution**: System automatically uses 7-level fallback chain

**Issue**: Only 1 image inserted instead of 3 (FIXED in v1.1.0)
- **Cause**: Insertion logic was too strict - required specific HTML patterns
  - Image 2: Required `</table>` followed by `<h2>` (but often `<h3>`)
  - Image 3: Required h2 title containing "案例" (but many articles don't have this)
- **Symptom**: Script reports generating 3 images, but only 1 appears in HTML
- **Solution** (v1.1.0): Made insertion logic more flexible
  - Image 2: Now matches `</table>` followed by `<h2>` OR `<h3>`
  - Image 3: Now inserts after 3rd `<h2>` tag, regardless of title content
- **Workaround**: If issue persists, manually insert images into HTML at desired positions

## Technical Details

**File Naming Convention**:
```
article_img{number}_{description}_{timestamp}.jpg
Example: article_img1_context_img1_20260303_121425.jpg
```

**Image Path Handling**:
- Images saved in **same directory** as input HTML file
- HTML uses direct filename reference: `<img src="article_img1_...jpg">`
- No `../` prefix, ensures images display correctly after copy-paste

**Windows-Specific Considerations**:
- Uses ASCII symbols in print: `[OK]`, `[ERROR]`, `[WARNING]`
- Avoids Unicode: ✓, ✗, ✅, ❌, ⚠
- Prevents GBK encoding errors

## References

- **Script location**: `C:/D/CAIE_tool/MyAIProduct/skills/toutiao-img/add_images_to_toutiao_article.py`
- **Original generator**: `post/article/toutiao_article_generator.py`
- **Core methods**:
  - `add_images_to_toutiao_article()` (lines 18-93) - Main entry point
  - `generate_article_images()` (lines 96-163) - Image generation with AI prompts
  - `insert_images_to_content()` (lines 237-272) - Strategic image placement logic
  - `generate_image_prompts_with_ai()` (lines 166-234) - AI-powered prompt generation
- **Example article**: `post/article/他山之石/元宵节花灯风俗——千年光影中的非遗传承.html`
