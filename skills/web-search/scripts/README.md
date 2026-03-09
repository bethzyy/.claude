# Web Search Skill - 多级Fallback网络搜索工具

具有多级fallback机制的网络搜索skill，确保在任何情况下都能进行网络搜索。

## 功能特点

- **6级Fallback机制**：MCP WebSearch (配额1) → MCP WebSearch 2 (配额2) → Tavily → GLM Web Search → DuckDuckGo → AI知识库
- **智能缓存系统**：MD5-based缓存，50-70x性能提升
- **透明日志**：清晰记录每个provider的尝试结果
- **多种输出格式**：text/JSON/markdown
- **零配置运行**：DuckDuckGo无需API key

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```bash
# 自动选择最佳搜索源
python main.py "Python编程教程"

# 指定搜索源
python main.py "Rust语言" --source duckduckgo

# JSON输出
python main.py "WebAssembly" --format json

# 清空缓存
python main.py "" --clear-cache
```

## 配置

### Tavily API（可选）

**已自动配置**：系统会自动从 `C:\D\CAIE_tool\LLM_Configs\tavily\apikey.txt` 读取API key。

如需手动配置，也可设置环境变量或创建`.env`文件：

```bash
export TAVILY_API_KEY=your-api-key-here
```

获取API key: https://tavily.com

### ZhipuAI API（可选，AI知识库fallback）

```bash
export ZHIPU_API_KEY=id.secret
```

获取API key: https://open.bigmodel.cn

## Fallback机制

```
1. MCP WebSearch（智谱Coding Plan配额1，apikeyValue.txt）
   ↓ 配额用尽时自动切换 (错误码 1310)
2. MCP WebSearch 2（智谱Coding Plan配额2，apikeyValue2.txt）⭐ NEW
   ↓ 配额用尽时自动切换
3. Tavily API（第三方服务，独立配额）
   ↓ 配额用尽时自动切换 (429/403错误)
4. GLM Web Search（使用GLM-4-flash的web_search工具，按token计费）
   ↓ 失败时自动切换
5. DuckDuckGo（完全免费）
   ↓ 失败时自动切换
6. AI知识库（最后手段）
```

## 返回值格式

### 成功

```json
{
  "success": true,
  "query": "搜索查询",
  "provider_used": "tavily",
  "results": [
    {
      "title": "标题",
      "url": "https://example.com",
      "snippet": "摘要..."
    }
  ],
  "content": "完整内容",
  "cached": false
}
```

### 失败

```json
{
  "success": false,
  "error": "所有搜索方式都失败",
  "attempts": [...]
}
```

## CLI选项

```
positional arguments:
  query                 搜索查询

optional arguments:
  -h, --help            显示帮助
  --max-results N       最大结果数（默认: 5）
  --timeout N           超时时间（秒，默认: 30）
  --format {text,json,markdown}
                        输出格式（默认: text）
  --source {auto,mcp_websearch,tavily,glm_web_search,duckduckgo,ai_knowledge}
                        指定搜索源（默认: auto）
  --no-cache            禁用缓存
  --clear-cache         清空缓存并退出
  --cache-stats         显示缓存统计
```

## 错误处理

### 配额用尽（QUOTA_EXHAUSTED）

自动降级到DuckDuckGo：

```
[INFO] 尝试 tavily...
[WARNING] tavily 配额已用尽，尝试下一个...
[INFO] 尝试 duckduckgo...
[SUCCESS] duckduckgo 返回 5 条结果
```

### 网络超时

自动尝试下一个provider。

### Provider不可用

跳过未配置的provider，尝试下一个可用的。

## 性能

- **首次搜索**：2-5秒
- **缓存搜索**：<0.1秒（50-70x加速）
- **缓存过期**：7天（可配置）

## 依赖

```
requests>=2.31.0
duckduckgo-search>=4.0.0
zhipuai>=0.1.0
```

## 文件结构

```
skills/web-search/
├── main.py                      # CLI入口
├── search_engine.py             # 核心搜索引擎
├── cache_manager.py             # 缓存管理
├── config.py                    # 配置管理
├── providers/
│   ├── __init__.py              # Provider基类
│   ├── mcp_websearch_provider.py # MCP WebSearch
│   ├── tavily_provider.py       # Tavily API
│   ├── glm_web_search_provider.py # GLM Web Search
│   ├── duckduckgo_provider.py   # DuckDuckGo
│   └── ai_knowledge_provider.py # AI知识库
├── requirements.txt             # 依赖列表
└── README.md                    # 文档
```

## 版本历史

- **v1.1.0** (2026-03-06): 新增GLM Web Search fallback
  - **New**: 添加GLM-4-flash web_search工具作为第3级fallback
  - **Enhanced**: 更新为5级fallback机制（原来4级）
  - **Updated**: CLI支持 `--source glm_web_search` 选项
  - **Tested**: 验证GLM Web Search正常工作
  - **API Key**: 从 `C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt` 读取

- **v1.0.0** (2026-03-03): 初始版本
  - 3级fallback机制
  - 智能缓存系统
  - 多种输出格式
  - CLI工具
