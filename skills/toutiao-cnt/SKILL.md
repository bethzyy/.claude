---
name: toutiao-cnt
description: Create, generate, or convert content into 今日头条 (Toutiao) articles. ALWAYS use this skill when user wants to "create article", "generate article", "write article about [topic]", "生成一篇头条文章", "写一篇头条文章", "创作一篇头条文章", "帮我生成头条文章", "帮我写头条文章", "生成头条文章", "写一篇文章", "创作文章", "把 [内容] 写成头条文章", "把 [文件] 转换成头条文章", "将 [文档] 变成HTML文章", "把 [内容] 转成今日头条文章", "把...变成文章", "把...转成文章", "把...写成文章", "将...转换为文章", "生成HTML文章", "生成头条html文章", "研究并生成文章", "写一篇关于...的文章", or discusses creating/updating 今日头条 articles. Supports creating from topics AND converting existing files (Markdown, HTML, Text) into Toutiao-compatible HTML format. Automatically handles research (uses web-search for fact accuracy), content generation, and file conversion. Includes article structure best practices to ensure logical flow and avoid redundancy. MUST trigger for ANY Toutiao article creation or content transformation task including "把 [file] 写成/转成/变成 [format]" patterns.
version: 5.1.0
---

# Toutiao Article Content Manager

Comprehensive tool for managing Toutiao (今日头条) articles with dual capabilities:

## 1. Article Creation
Generate complete articles from user-specified topics using AI, with automatic research and content generation.

## 2. Content Integration
Intelligently integrate new content into existing Toutiao articles with automatic duplicate detection, flexible positioning, and support for multiple content formats (Markdown/HTML/Text).

## What's New in v5.1.0

- **🔍 明确"适当扩展"边界**：解决扩展与编造的模糊地带
  - **明确允许的扩展**：重组顺序、过渡句（基于事实）、简化术语、添加段落标题
  - **明确禁止的扩展**：未提及的案例/数据/版本号、预测假设、技术细节编造、过度推断
  - **严格模式阈值提高**：从 100 字符提高到 300 字符，避免技术内容触发过于宽松
  - **增强验证机制**：检查扩展内容是否有事实依据，新增"扩展内容验证"规则
  - **新高严重度问题**：技术细节编造、过度推断、"补充背景"式编造

## What's New in v5.0.0

- **🎯 基于事实生成，杜绝编造**：重大改进，解决 AI 编造问题
  - **修复搜索路径**：从 `skills/web-search` 修正为 `.claude/skills/web-search`
  - **新增 `--content` 参数**：支持传入用户已有的专业内容（文件或直接文本）
  - **新增 `--strict` 参数**：严格模式，无事实材料则拒绝生成
  - **自适应字数**：根据事实材料量自动调整建议字数（不再硬性 1500-2000 字）
  - **增强验证**：全文验证（不只是前 1000 字），更严格的验证标准
  - **信息来源标注**：文章末尾自动添加"参考来源"部分
  - **保守策略**：无事实材料时使用限定词和免责声明，宁可简短也不编造

## What's New in v4.0.0

- **🏗️ Architecture Migration to Anthropic Official Standard**: Complete migration to single-location architecture
  - **NEW LOCATION**: All code now in `.claude/skills/toutiao-cnt/scripts/` (official standard)
  - **OLD LOCATION**: `skills/toutiao-cnt/` (deprecated, dual-location architecture)
  - **Backward Compatible**: Existing commands still work through wrapper script
  - **Command Change**: Use `python .claude/skills/toutiao-cnt/main.py` or just `/skill toutiao-cnt`
  - **Benefits**: Unified structure, easier maintenance, consistent with other skills
  - **Migration**: Part of global skills architecture standardization (2026-03-08)

## What's New in v3.6.0

- **Automatic ASCII Diagram Formatting**: All generated articles now include optimized `.diagram` CSS style
  - Fixes alignment issues in ASCII art/architecture diagrams
  - Uses monospace font (`Courier New`, `Consolas`) for proper character alignment
  - Compact line-height (1.2) for tight spacing between diagram lines
  - `white-space: pre` preserves ASCII formatting exactly as written
  - When integrating content, the system automatically injects `.diagram` style if missing
  - Example use case: Architecture diagrams, flowcharts, system structure visualization

## When This Skill Applies

This skill activates when the user's request involves:
- Creating HTML articles for Toutiao platform
- Generating 今日头条 compatible article templates
- Formatting articles for 头条发布
- Ensuring article works in Toutiao editor without formatting issues
- Converting content to Toutiao-friendly HTML format

## Core Principles

**DO** ✅:
- Use simple HTML tags (div, p, ul, ol, table)
- Use basic CSS (background colors, borders, fonts)
- Use standard inline styles for adjustments
- Ensure maximum compatibility

**DON'T** ❌:
- Use `display: grid` or `display: flex`
- Use `transition`, `transform`, `animation`
- Use `:hover` pseudo-classes
- Use complex gradients or box-shadows
- Use responsive breakpoints with grid/flex
- Use absolute or fixed positioning

## Standard CSS Template

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.9;
    color: #222;
    font-size: 17px;
    max-width: 750px;
    margin: 0 auto;
    background: #fff;
}

.article-container {
    padding: 20px;
}

/* Title styles */
h1 {
    font-size: 24px;
    font-weight: bold;
    line-height: 1.4;
    margin-bottom: 10px;
    color: #000;
}

h2 {
    font-size: 20px;
    font-weight: bold;
    margin-top: 40px;
    margin-bottom: 20px;
    color: #333;
    border-left: 4px solid #f85959;
    padding-left: 12px;
}

h3 {
    font-size: 18px;
    font-weight: bold;
    margin-top: 30px;
    margin-bottom: 15px;
    color: #444;
}

h4 {
    font-size: 16px;
    font-weight: bold;
    margin-top: 20px;
    margin-bottom: 10px;
    color: #555;
}

/* Paragraphs */
p {
    margin-bottom: 15px;
    text-align: justify;
}

/* Metadata */
.article-meta {
    color: #999;
    font-size: 14px;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #eee;
}

/* Banner styles */
.intro-box {
    background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
    border-left: 4px solid #f85959;
    padding: 20px;
    margin: 25px 0;
    border-radius: 8px;
}

.section-box {
    background: #fafafa;
    border-radius: 8px;
    padding: 20px;
    margin: 25px 0;
}

.warning-banner {
    background: #fff3e0;
    border-left: 4px solid #ff9800;
    padding: 15px 20px;
    margin: 20px 0;
    border-radius: 4px;
}

.danger-banner {
    background: #ffebee;
    border-left: 4px solid #f44336;
    padding: 15px 20px;
    margin: 20px 0;
    border-radius: 4px;
}

.success-banner {
    background: #e8f5e9;
    border-left: 4px solid #4caf50;
    padding: 15px 20px;
    margin: 20px 0;
    border-radius: 4px;
}

.info-banner {
    background: #e3f2fd;
    border-left: 4px solid #2196f3;
    padding: 15px 20px;
    margin: 20px 0;
    border-radius: 4px;
}

/* Table styles */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 15px;
}

table th {
    background: #f85959;
    color: white;
    padding: 12px 10px;
    text-align: left;
    font-weight: bold;
}

table td {
    border: 1px solid #e0e0e0;
    padding: 12px 10px;
}

table tr:nth-child(even) {
    background: #f9f9f9;
}

/* List styles */
ul, ol {
    margin-bottom: 15px;
    padding-left: 25px;
}

li {
    margin-bottom: 10px;
}

/* Other elements */
.emoji {
    font-size: 18px;
}

.author-info {
    background: #f8f9fa;
    padding: 20px;
    margin-top: 50px;
    border-radius: 8px;
    text-align: center;
}

.tag {
    display: inline-block;
    background: #e3f2fd;
    color: #1976d2;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    margin-right: 5px;
}

/* ASCII Diagram styles */
.diagram {
    background: #f0f7ff;
    border: 1px dashed #90caf9;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    font-family: 'Courier New', 'Consolas', monospace;
    font-size: 14px;
    line-height: 1.2;
    text-align: center;
    white-space: pre;
    overflow-x: auto;
}

hr {
    margin: 40px 0;
    border: none;
    border-top: 1px solid #eee;
}
```

## HTML Structure Template

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文章标题</title>
    <style>
        /* Paste CSS template here */
    </style>
</head>
<body>
    <div class="article-container">
        <h1>文章标题</h1>

        <div class="article-meta">
            <span>发布时间：YYYY-MM-DD</span> | <span>阅读时间：约X分钟</span> | <span>分类：xxx</span>
        </div>

        <div class="intro-box">
            <p style="margin: 0;"><strong>📌 核心提示：</strong>文章导语，简明扼要地说明文章价值。</p>
        </div>

        <h2><span class="emoji">🎯</span> 一、第一章节标题</h2>
        <p>章节内容...</p>

        <h2><span class="emoji">📊</span> 二、第二章节标题</h2>
        <div class="section-box">
            <h4 style="margin-top: 0;">小标题</h4>
            <ul style="margin: 0; padding-left: 20px;">
                <li>列表项1</li>
                <li>列表项2</li>
            </ul>
        </div>

        <hr>

        <div class="author-info">
            <p style="margin: 0; font-weight: bold; font-size: 16px;">关于作者</p>
            <p style="margin: 5px 0 0; color: #666; font-size: 14px;">作者简介...</p>
        </div>

        <p style="text-align: center; color: #999; font-size: 13px; margin-top: 30px;">
            相关标签：<span class="tag">标签1</span><span class="tag">标签2</span>
        </p>

        <p style="text-align: center; color: #999; font-size: 13px; margin-top: 20px;">
            本文首发于今日头条 | 未经授权禁止转载 | 最后更新：YYYY-MM-DD
        </p>
    </div>
</body>
</html>
```

## Common Content Patterns

### 1. Price/Parameter List
```html
<div class="section-box">
    <h4 style="margin-top: 0;">标题</h4>
    <ul style="margin: 0; padding-left: 20px;">
        <li><strong>项目名称</strong> — 说明：价格</li>
        <li><strong>项目名称</strong> — 说明：价格</li>
    </ul>
</div>
```

### 2. Alert Banners
```html
<!-- Warning -->
<div class="warning-banner">
    <h4 style="margin: 0 0 10px 0;">⚠️ 警告标题</h4>
    <p style="margin: 0;">警告内容...</p>
</div>

<!-- Danger -->
<div class="danger-banner">
    <h4 style="margin: 0 0 10px 0;">🚨 危险标题</h4>
    <p style="margin: 0;">危险内容...</p>
</div>

<!-- Success -->
<div class="success-banner">
    <h4 style="margin: 0 0 10px 0;">✅ 成功标题</h4>
    <p style="margin: 0;">成功内容...</p>
</div>
```

### 3. Process Flow
```html
<div class="info-banner" style="text-align: center; font-weight: bold;">
    步骤1 → 步骤2 → 步骤3 → 步骤4
    <div style="margin-top: 15px; font-size: 14px; color: #666; font-weight: normal;">
        说明1 ↑ &nbsp;&nbsp;&nbsp;&nbsp; 说明2 ↑ &nbsp;&nbsp;&nbsp;&nbsp; 说明3 ↑
    </div>
</div>
```

### 4. Data Table
```html
<table>
    <thead>
        <tr>
            <th width="25%">列1</th>
            <th width="25%">列2</th>
            <th width="50%">列3</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>数据1</td>
            <td>数据2</td>
            <td>数据3</td>
        </tr>
    </tbody>
</table>
```

### 5. ASCII Architecture Diagram
```html
<div class="diagram">
┌─────────────────────────────────────┐<br>
│           主系统              │<br>
│  ┌───────────────────────────────┐  │<br>
│  │      沙箱环境       │  │<br>
│  │  ┌─────────┐  ┌─────────┐     │  │<br>
│  │  │ 程序 A  │  │ 程序 B  │     │  │<br>
│  │  └─────────┘  └─────────┘     │  │<br>
│  └───────────────────────────────┘  │<br>
│         ↕️ 受限的通信                 │<br>
└─────────────────────────────────────┘
</div>
```

**Note**: The `.diagram` class automatically ensures:
- Monospace font for proper alignment
- Compact line-height (1.2) for tight spacing
- `white-space: pre` to preserve ASCII formatting
- Centered display with professional styling

## Publishing Workflow

1. Create HTML file using the template above
2. Fill in your article content
3. Preview in browser
4. Select all (Ctrl+A)
5. Copy (Ctrl+C)
6. Paste into Toutiao editor
7. Verify formatting in preview mode
8. Publish

---

# Article Creation Features

## Overview

Generate complete Toutiao articles from user-specified topics using AI. The system will:
- Research the topic automatically
- Generate structured content with proper headings
- Create HTML formatted for Toutiao editor
- Support customizable writing styles

## Command Format

```bash
python C:/D/CAIE_tool/MyAIProduct/.claude/skills/toutiao-cnt/main.py create <topic> [options]
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `topic` (required) | Article topic/theme |
| `--output-dir` | Output directory (default: current directory) |
| `--style` | Writing style (professional/casual/academic/etc.) |
| `--content` | **NEW** User-provided content (file path or direct text) |
| `--strict` | **NEW** Strict mode: reject generation without fact materials |
| `--min-words` | **NEW** Minimum word count (default: 500) |
| `--max-words` | **NEW** Maximum word count (default: 2000) |

## Usage Examples

### 1. Create Article from Topic (with web search)
```bash
python .claude/skills/toutiao-cnt/main.py create "元宵节风俗"
```

### 2. Create with User Content (Recommended for accuracy)
```bash
# Using a file as fact source
python .claude/skills/toutiao-cnt/main.py create "Claude Code Agent 使用指南" \
    --content "post/article/他山之石/Claude-Code原生Agent完全指南-头条版.html"

# Using direct text as fact source
python .claude/skills/toutiao-cnt/main.py create "Python 装饰器详解" \
    --content "装饰器是 Python 的一个重要特性，它允许在不修改函数代码的情况下扩展函数功能..."
```

### 3. Create with Strict Mode (Reject if no facts)
```bash
# This will fail if no web search results or user content
python .claude/skills/toutiao-cnt/main.py create "不存在的主题xyz123" --strict

# This will succeed because user content is provided
python .claude/skills/toutiao-cnt/main.py create "自定义主题" \
    --content "这里是用户提供的专业内容..." --strict
```

### 4. Create with Specific Output Directory
```bash
python .claude/skills/toutiao-cnt/main.py create "RPA自动化" --output-dir "C:/D/CAIE_tool/MyAIProduct/post/article/他山之石"
```

### 5. Create with Custom Style
```bash
python .claude/skills/toutiao-cnt/main.py create "人工智能发展" --style academic
```

## Generated Article Structure

Articles are automatically structured with:
- **Title**: Clear, engaging headline
- **Introduction**: Overview of the topic
- **Main Content**: Multiple sections with H2/H3 headings
- **Examples**: Concrete examples and data
- **Summary**: Key takeaways
- **Proper HTML**: Formatted for Toutiao editor

## Output Files

- **Format**: HTML file ready for Toutiao
- **Naming**: `Article_{title}_{timestamp}.html`
- **Location**: Specified output directory or current directory

## Typical Workflow

### Creating a New Article

1. **Specify topic:**
   ```bash
   python .claude/skills/toutiao-cnt/main.py create "元宵节各地风俗"
   ```

2. **AI automatically:**
   - Researches the topic
   - Generates structured content
   - Formats HTML properly
   - Creates output file

3. **Review and publish:**
   - Open generated HTML file
   - Review content in browser
   - Copy all (Ctrl+A, Ctrl+C)
   - Paste into Toutiao editor
   - Make minor adjustments if needed
   - Publish

## Tips for Better Articles

**Specify detailed topics:**
- ❌ Too vague: "美食"
- ✅ Better: "元宵节传统美食与制作方法"
- ✅ Best: "元宵节汤圆与元宵的制作工艺及南北差异"

**Choose appropriate style:**
- `professional`: Business, technical topics
- `casual`: Lifestyle, culture, food
- `academic`: Research, analysis
- `storytelling`: Narratives, history

## Article Structure Best Practices

### Optimal Logical Flow

A well-structured article should follow this progression:

```
1. Hook/Introduction (What)
   └─ Grab attention, establish topic relevance

2. Core Concept/Philosophy (Why) ⭐ KEY
   └─ Build cognitive framework BEFORE diving into details
   └─ Example: "Agent Teams" concept before introducing individual agents

3. Detailed Content (How)
   └─ Specific features, components, or implementations
   └─ Based on the framework established in step 2

4. Comparison/Selection (When)
   └─ Help readers choose between options
   └─ Use tables for quick reference

5. Practical Examples (Application)
   └─ Real-world use cases
   └─ Demonstrate how concepts apply in practice

6. Advanced Tips (Depth)
   └─ Power user techniques
   └─ Avoid redundancy with previous sections

7. Summary (Recap)
   └─ Key takeaways
   └─ Actionable next steps
```

### Common Structure Mistakes to Avoid

❌ **Don't:**
- Put core concepts at the end (readers lose context)
- Have overlapping sections (comparison table + examples covering same ground)
- Jump between abstraction levels (concept → details → back to concept)
- Use vague section titles that don't reflect content

✅ **Do:**
- Start with why/philosophy, then what/details
- Ensure each section has a unique purpose
- Use progressive disclosure (simple → complex)
- Make section titles descriptive and accurate

### Section Title Guidelines

**Bad titles:**
- "How to use" (too generic)
- "More information" (doesn't indicate content)
- "Overview" (could mean anything)

**Good titles:**
- "Agent Combination: Real-World Workflow" (specific)
- "Direct Dialog vs Agent: When to Choose Which" (clear comparison)
- "Traditional vs Agent Teams: Architecture Comparison" (descriptive)

### Redundancy Checklist

Before finalizing an article, check for:
- [ ] Do any sections repeat information?
- [ ] Are examples distinct from comparison tables?
- [ ] Does each section add unique value?
- [ ] Can any overlapping content be merged?

**Example of redundancy elimination:**
- Before: Section on "Choosing the right approach" + Section on "Use cases" (overlap)
- After: Section on "When to use each" (comparison table) + Section on "Combination examples" (unique workflows)

---

## Important Notes

1. **Images**: Toutiao doesn't support local images. Upload to Toutiao's image host first
2. **Code blocks**: Use Toutiao editor's built-in code block feature, not HTML formatting
3. **Links**: Will be automatically recognized after pasting
4. **Special characters**: Use HTML entities (e.g., `&nbsp;`)
5. **Testing**: Always verify formatting in Toutiao preview mode

## Reference Examples

Complete example file:
- `C:\D\CAIE_tool\MyAIProduct\post\article\他山之石\域名费用.html`

Refer to this file to understand the complete structure and styling application.

---

# Content Integration Features

## Overview

The content integration feature allows you to intelligently add new content to existing Toutiao articles while:
- Avoiding duplicate sections
- Maintaining consistent styling
- Preserving existing structure
- Supporting flexible insertion positions

## Command Format

```bash
python C:/D/CAIE_tool/MyAIProduct/.claude/skills/toutiao-cnt/main.py integrate <html_file> <new_content> [options]
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `html_file` (required) | Path to existing HTML article |
| `content` (required) | New content (text/Markdown file/HTML string) |
| `--position` | Insert position: `after`, `before`, `end` (default) |
| `--after` | Insert after this section title |
| `--before` | Insert before this section title |
| `--merge` | Smart merge, skip duplicate sections |
| `--list-sections` | List all existing sections in the article |
| `--output-suffix` | Output file suffix (default: `-updated`) |

## Usage Examples

### 1. Add Content to End of Article
```bash
python .claude/skills/toutiao-cnt/main.py article.html "## 新章节

这是新章节的内容，支持Markdown格式。"
```

### 2. Insert After Specific Section
```bash
python .claude/skills/toutiao-cnt/main.py article.html content.md --position after --after "工具对比"
```

### 3. Insert Before Specific Section
```bash
python .claude/skills/toutiao-cnt/main.py article.html new_content.html --position before --before "总结"
```

### 4. Smart Merge (Auto-skip Duplicates)
```bash
python .claude/skills/toutiao-cnt/main.py article.html updates.md --merge
```

### 5. List Existing Sections
```bash
python .claude/skills/toutiao-cnt/main.py article.html --list-sections
```

Output:
```
文章章节结构：
============================================================
1. RPA 自动化
2.   工作原理
3.   常见应用场景
4.   RPA 工具与平台
5.     企业级商业平台（国外）
6.     国产RPA平台
7.     开源实现方案（程序员友好）
============================================================
```

## Supported Content Formats

### 1. Plain Text
```bash
python integrate_content.py article.html "新段落内容"
```

### 2. Markdown
```markdown
## 新章节标题

段落内容...

- 列表项1
- 列表项2

### 子章节

| 列1 | 列2 |
|-----|-----|
| 数据 | 数据 |
```

### 3. HTML
```html
<h2>新章节</h2>
<p>段落内容...</p>
<table>
    <tr><th>列1</th></tr>
    <tr><td>数据</td></tr>
</table>
```

### 4. Markdown File
```bash
python integrate_content.py article.html path/to/content.md
```

## Smart Features

### 1. Duplicate Section Detection
When using `--merge`, the integrator automatically:
- Scans new content for section titles
- Checks if sections already exist in the article
- Skips duplicate sections with a warning

Example:
```bash
$ python integrate_content.py article.html updates.md --merge
[WARNING] 章节已存在: RPA 工具，跳过
[WARNING] 章节已存在: 优缺点，跳过
[INFO] 内容已添加到文章末尾
```

### 2. Automatic HTML Conversion
- Markdown → HTML (tables, lists, headings)
- Plain text → `<p>` tags
- Code blocks → `<div class="code-block">`

### 3. Structure Preservation
- Existing styles are preserved
- Article container is maintained
- Proper HTML nesting is ensured

## Typical Workflow

### Scenario: Enhancing an Existing Article

1. **Check existing structure:**
   ```bash
   python integrate_content.py RPA自动化.html --list-sections
   ```

2. **Prepare new content** (e.g., `updates.md`):
   ```markdown
   ## 如何选择RPA工具？

   根据不同角色推荐方案...

   ## 学习路径建议

   ### 入门级
   - 步骤1
   - 步骤2
   ```

3. **Integrate with smart merge:**
   ```bash
   python integrate_content.py RPA自动化.html updates.md --position before --before "优缺点" --merge
   ```

4. **Review and publish:**
   - Open `RPA自动化-updated.html`
   - Verify content placement
   - Copy to Toutiao editor

## Output Files

- **Default**: `{original_name}-updated.html`
- **Custom suffix**: Use `--output-suffix` (e.g., `-v2`)

## Troubleshooting

### Issue: "章节已存在" but you want to replace
**Solution**: Remove the `--merge` flag to allow duplicates

### Issue: Content inserted at wrong position
**Solution**: Use `--list-sections` to verify exact section titles, then use `--after` or `--before`

### Issue: Markdown tables not rendering correctly
**Solution**: Ensure proper table syntax with `|` separators

## Technical Details

**Script location**: `C:\D\CAIE_tool\MyAIProduct\.claude\skills\toutiao-cnt\scripts\integrate_content.py`

**Dependencies**:
- BeautifulSoup4 (`pip install beautifulsoup4`)
- Standard library only (no other dependencies)

**Key features**:
- HTML structure analysis using BeautifulSoup
- Section extraction based on headings (h1-h4)
- Markdown to HTML conversion
- Duplicate detection with regex matching
- UTF-8 encoding support for Chinese content
