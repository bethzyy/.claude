# Web Search Skill

Multi-level fallback web search skill ensuring search functionality is always available.

## Description

Multi-level fallback web search with 4 providers. ALWAYS use this skill when user asks to "search web", "find information", "look up online", or any web search request.

## Fallback Architecture

1. **MCP WebSearch** (Priority 1) - Uses ZhipuAI Coding Plan quota, no API key required
2. **Tavily API** (Priority 2) - Auto-detects API key from `C:\D\CAIE_tool\LLM_Configs\tavily\apikey.txt`
3. **DuckDuckGo** (Priority 3) - Completely free, no API key
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

2.0.0 - Added environment detection for MCP WebSearch (CLI mode auto-skip)
