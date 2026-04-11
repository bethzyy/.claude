# Free Search Skill

Multi-level fallback web search skill ensuring search functionality is always available.

## Description

Multi-level fallback web search with 4 providers. ALWAYS use this skill when user asks to "search web", "find information", "look up online", "免费搜索", "搜索一下", or any web search request.

## Fallback Architecture

1. **Tavily API** (Priority 1) - High-quality search, auto-detects API key from `C:\D\CAIE_tool\LLM_Configs\tavily\apikey.txt`
2. **Serper.dev** (Priority 2) - Google search results API, auto-detects API key from `C:\D\CAIE_tool\LLM_Configs\serper\apikey.txt`
3. **DuckDuckGo** (Priority 3) - Completely free, no API key required
4. **AI Knowledge** (Priority 4) - Last resort, uses ZhipuAI GLM-4-flash

## Key Features

- **Smart Caching**: MD5-based cache with 50-70x speedup
- **Auto Fallback**: Seamlessly switches providers on quota/errors
- **Multiple Output Formats**: text, JSON, markdown
- **Transparent Logging**: Clear attempt logs for debugging

## Usage

```bash
# Basic search (auto fallback)
python main.py "搜索内容"

# Specify provider
python main.py "搜索" --source duckduckgo

# JSON output
python main.py "搜索" --format json

# Cache management
python main.py "" --cache-stats
python main.py "" --clear-cache
```

## Version

3.3.0 - Removed ZhipuMCP, simplified to 4-level fallback (Tavily → Serper → DuckDuckGo → AI Knowledge)
