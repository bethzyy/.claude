---
name: web-search
description: Multi-level fallback web search skill with automatic provider switching. Tries ZhipuMCP → Tavily → DuckDuckGo → AI knowledge base. Use when user asks to "search web", "find information", "look up online", "find latest info about", or any web search request.
version: 3.0.0
entry_point: main.py
author: Claude Code
tags: [search, web, fallback, zhipu, tavily, duckduckgo]
---

# Web Search Skill

Multi-level fallback web search skill that ensures search functionality is always available by automatically switching between providers.

## Trigger Conditions

Use this skill when the user asks to:
- "Search the web for ..."
- "Find information about ..."
- "Look up online ..."
- "Find the latest info on ..."
- "Search for ..." (without specifying a local source)
- Any request that requires current web information

## What's New in v3.0.0

- **🏗️ Architecture Migration to Anthropic Official Standard**: Complete migration to single-location architecture
  - **NEW LOCATION**: All code now in `.claude/skills/web-search/scripts/` (official standard)
  - **OLD LOCATION**: `skills/web-search/` (deprecated, dual-location architecture)
  - **Backward Compatible**: Existing commands still work through wrapper script
  - **Command Change**: Use `python .claude/skills/web-search/main.py` or just `/skill web-search`
  - **Benefits**: Unified structure, easier maintenance, consistent with other skills
  - **Migration**: Part of global skills architecture standardization (2026-03-08)
  - **Complex Migration**: Migrated 9 provider files, test suite, and documentation

## How It Works

The skill implements a **4-level fallback mechanism**:

1. **ZhipuMCP** (Priority 1 - **First Choice**)
   - Uses ZhipuAI GLM Web Search API
   - API key from `C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue.txt`
   - Highest quality results with AI-powered understanding
   - Automatically falls back on quota exhaustion (error code 1310)

2. **Tavily API** (Priority 2)
   - High-quality search results
   - Auto-detects API key from `C:\D\CAIE_tool\LLM_Configs\tavily\apikey.txt`
   - Has quota limits (1000 requests/month free tier)
   - Automatically falls back on quota exhaustion (429/403 errors)

3. **DuckDuckGo** (Priority 3)
   - Completely free, no API key required
   - Reliable fallback when all paid options are exhausted
   - Uses `duckduckgo-search` Python library

4. **AI Knowledge Base** (Priority 4 - **Last Resort**)
   - Last resort fallback
   - Uses ZhipuAI GLM-4-flash model's pre-trained knowledge
   - Requires `ZHIPU_API_KEY` environment variable
   - **Note**: Provides pre-2024 knowledge only, not real-time information

## Usage

### Basic Usage

```bash
python main.py "Python异步编程教程"
```

### Specify Search Source

```bash
# Use DuckDuckGo only (free, no API key)
python main.py "Rust语言特性" --source duckduckgo

# Use AI knowledge only (last resort)
python main.py "机器学习基础" --source ai_knowledge
```

### Output Formats

```bash
# JSON output
python main.py "WebAssembly" --format json

# Markdown output
python main.py "区块链技术" --format markdown

# Plain text (default)
python main.py "量子计算"
```

### Cache Management

```bash
# Clear cache
python main.py "" --clear-cache

# Show cache statistics
python main.py "" --cache-stats

# Disable cache for this search
python main.py "最新新闻" --no-cache
```

## Installation

Install required dependencies:

```bash
pip install requests duckduckgo-search zhipuai
```

Or install from requirements file:

```bash
pip install -r requirements.txt
```

## Configuration

### Tavily API (Optional)

**Auto-detected**: The skill automatically reads from `C:\D\CAIE_tool\LLM_Configs\tavily\apikey.txt` if it exists.

You can also set `TAVILY_API_KEY` environment variable:

```bash
# Windows CMD
set TAVILY_API_KEY=your-api-key-here

# Windows PowerShell
$env:TAVILY_API_KEY="your-api-key-here"

# Linux/Mac
export TAVILY_API_KEY="your-api-key-here"
```

Or create `.env` file in project root:

```
TAVILY_API_KEY=your-api-key-here
```

Get API key at: https://tavily.com

### ZhipuAI API (Optional, for AI knowledge fallback)

Set `ZHIPU_API_KEY` environment variable:

```bash
# Windows CMD
set ZHIPU_API_KEY=id.secret

# Windows PowerShell
$env:ZHIPU_API_KEY="id.secret"

# Linux/Mac
export ZHIPU_API_KEY="id.secret"
```

Or create `.env` file in project root:

```
ZHIPU_API_KEY=id.secret
```

Get API key at: https://open.bigmodel.cn

## Return Value Structure

### Success

```json
{
  "success": true,
  "query": "搜索查询",
  "provider_used": "tavily|duckduckgo|ai_knowledge",
  "results": [
    {
      "title": "结果标题",
      "url": "https://example.com",
      "snippet": "结果摘要..."
    }
  ],
  "content": "格式化的完整内容",
  "metadata": {},
  "attempts": [...],
  "cached": false
}
```

### Failure

```json
{
  "success": false,
  "error": "所有搜索方式都失败",
  "query": "搜索查询",
  "attempts": [
    {
      "provider": "tavily",
      "success": false,
      "error": "QUOTA_EXHAUSTED"
    },
    {
      "provider": "duckduckgo",
      "success": false,
      "error": "搜索异常: ..."
    }
  ],
  "cached": false
}
```

## Error Handling

The skill automatically handles the following errors:

### Quota Exhaustion (Error Code: QUOTA_EXHAUSTED)

When Tavily API returns 429 or 403 status codes, the skill automatically falls back to DuckDuckGo without user intervention.

```
[INFO] 尝试 tavily...
[WARNING] tavily 配额已用尽，尝试下一个...
[INFO] 尝试 duckduckgo...
[SUCCESS] duckduckgo 返回 5 条结果
```

### Network Timeout

Each provider has a configurable timeout (default: 30 seconds). If timeout occurs, automatically tries the next provider.

### Provider Unavailable

If a provider is not configured (missing API key) or library not installed, automatically skips to the next available provider.

## Logging

The skill provides transparent logging:

```
[INFO] 开始搜索: "Python异步编程"
[INFO] 尝试 tavily...
[SUCCESS] tavily 返回 5 条结果

=== 搜索结果 ===
查询: Python异步编程
来源: TAVILY
结果数: 5
缓存: 否
...
[耗时: 2.3秒]
```

## Performance

### Caching

- **First search**: 2-5 seconds
- **Cached search**: <0.1 seconds (50-70x speedup)
- **Cache expiry**: 7 days (configurable)
- **Cache location**: `search_cache/` directory

### Fallback Scenarios

- **Best case** (Tavily available): 2-3 seconds
- **Typical case** (DuckDuckGo): 3-5 seconds
- **Worst case** (AI knowledge): 5-10 seconds

## Architecture

```
search_engine.py (Core engine)
    ├── CacheManager (MD5-based caching)
    └── Providers (Priority order)
        ├── ZhipuMCPProvider (ZhipuAI Web Search, single quota)
        ├── TavilyProvider (Third-party API, high quality)
        ├── DuckDuckGoProvider (Free, no API key)
        └── AIKnowledgeProvider (Last resort, pre-trained knowledge)
```

## Advantages

1. **Reliability**: 4 independent search sources, ensures at least one works
2. **Transparent**: Clear logs show which provider succeeded
3. **Smart caching**: Avoids redundant queries, significant performance boost
4. **Zero configuration**: DuckDuckGo works without any API keys
5. **Graceful degradation**: Automatically degrades to next best option
6. **Simplified architecture**: Single quota design, easier to maintain
7. **Minimal dependencies**: Removed GLM Web Search for cleaner codebase

## Limitations

1. **AI knowledge fallback** only provides pre-2024 information (GLM-4-flash training cutoff)
2. **DuckDuckGo** may have different result quality compared to Tavily
3. **Rate limiting**: Each provider has its own rate limits

## Troubleshooting

### "Tavily API Key未配置"

**Solution**: Set `TAVILY_API_KEY` environment variable or create `.env` file. Or let it fallback to DuckDuckGo (free).

### "未安装duckduckgo-search库"

**Solution**: Run `pip install duckduckgo-search`

### "ZHIPU_API_KEY未配置"

**Solution**: Set `ZHIPU_API_KEY` environment variable. Note: This is only needed for AI knowledge fallback (last resort).

### All providers fail

**Check**:
1. Internet connection
2. API keys are valid (Tavily, ZhipuAI)
3. Required libraries installed: `pip install requests duckduckgo-search zhipuai`

## File Structure

```
skills/web-search/
├── main.py                      # CLI entry point
├── search_engine.py             # Core engine with fallback logic
├── cache_manager.py             # MD5-based caching system
├── config.py                    # API key management
├── providers/
│   ├── __init__.py              # Provider base class
│   ├── tavily_provider.py       # Tavily API wrapper
│   ├── duckduckgo_provider.py   # DuckDuckGo wrapper
│   └── ai_knowledge_provider.py # AI knowledge fallback
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation
```

## Dependencies

```
requests>=2.31.0
duckduckgo-search>=4.0.0
zhipuai>=0.1.0
```

## Version History

- **v2.6.0** (2026-03-07): Remove GLM Web Search provider
  - Removed GLMWebSearchProvider to simplify architecture
  - Updated fallback order: ZhipuMCP → Tavily → DuckDuckGo → AI Knowledge
  - Reduced from 5-level to 4-level fallback mechanism
  - Cleaner codebase with fewer dependencies

- **v2.5.0** (2026-03-07): Remove quota 2, simplify architecture
  - Removed dual-quota auto-switching logic
  - Simplified to single quota design (apikeyValue.txt only)
  - Cleaned up all quota 2 related code

- **v1.0.0** (2026-03-03): Initial release
  - 4-level fallback mechanism
  - Smart caching with 7-day expiry
  - Multiple output formats (text/JSON/markdown)
  - CLI interface with comprehensive options
