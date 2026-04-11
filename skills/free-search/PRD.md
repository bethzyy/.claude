# Free Search Skill - PRD 文档

## 文档信息

| 属性 | 值 |
|------|-----|
| **名称** | free-search |
| **版本** | v3.3.0 |
| **状态** | ✅ 已实现 |
| **入口文件** | main.py |
| **技术栈** | Python + Tavily API + Serper API + DuckDuckGo + ZhipuAI GLM |
| **最后更新** | 2026-03-24 |

---

## 1. 产品概述

### 1.1 产品定位

Free Search 是一个多级回退的网页搜索技能，通过自动切换搜索提供商确保搜索功能始终可用。零成本、始终在线、无需配置。

### 1.2 核心价值

- **零成本**: DuckDuckGo 完全免费，无需 API Key
- **高可用性**: 4 级回退机制确保至少一个提供商可用
- **智能缓存**: MD5 基础缓存系统，7 天过期，50-70x 性能提升
- **透明日志**: 清晰显示哪个提供商成功

### 1.3 触发模式

```
"search web", "find information", "look up online",
"免费搜索", "搜索一下", "网页搜索"
```

---

## 2. 功能需求

### F1: 多级回退搜索

| 优先级 | 提供商 | 特点 |
|--------|--------|------|
| 1 | Tavily API | 高质量结果，自动检测 API Key |
| 2 | Serper.dev | Google 搜索结果 API |
| 3 | DuckDuckGo | 完全免费，无需 API Key |
| 4 | AI Knowledge | GLM-4-flash 预训练知识（最后手段） |

### F2: 智能缓存

- **缓存算法**: MD5 哈希查询字符串
- **过期时间**: 7 天（可配置）
- **存储位置**: `search_cache/` 目录
- **性能提升**: 50-70x（缓存命中时）

### F3: 多种输出格式

- `text`: 纯文本（默认）
- `json`: 结构化 JSON
- `markdown`: Markdown 格式

### F4: 错误处理

- **配额耗尽 (429/403)**: 自动回退到下一级
- **网络超时**: 30 秒超时，自动重试
- **提供商不可用**: 自动跳过

---

## 3. 技术架构

### 3.1 模块结构

```
.claude/skills/free-search/
├── main.py                    # CLI 入口
├── scripts/
│   ├── search_engine.py       # 核心引擎（回退逻辑）
│   ├── cache_manager.py       # MD5 缓存系统
│   └── providers/             # 搜索提供商
│       ├── tavily_provider.py
│       ├── serper_provider.py
│       ├── duckduckgo_provider.py
│       └── ai_knowledge_provider.py
└── requirements.txt
```

### 3.2 回退逻辑

```python
def search(query):
    for provider in [Tavily, Serper, DuckDuckGo, AIKnowledge]:
        result = provider.search(query)
        if result.success:
            return result
    return Error("所有搜索方式都失败")
```

### 3.3 API Key 配置

| 提供商 | 环境变量 | 自动检测路径 |
|--------|----------|--------------|
| Tavily | `TAVILY_API_KEY` | `C:\D\CAIE_tool\LLM_Configs\tavily\apikey.txt` |
| Serper | `SERPER_API_KEY` | `C:\D\CAIE_tool\LLM_Configs\serper\apikey.txt` |
| ZhipuAI | `ZHIPU_API_KEY` | - |

---

## 4. 使用示例

### 4.1 基础搜索

```bash
python .claude/skills/free-search/main.py "Python异步编程教程"
```

### 4.2 指定搜索源

```bash
# 仅使用 DuckDuckGo
python .claude/skills/free-search/main.py "Rust语言特性" --source duckduckgo

# 仅使用 AI 知识库
python .claude/skills/free-search/main.py "机器学习基础" --source ai_knowledge
```

### 4.3 输出格式

```bash
# JSON 输出
python .claude/skills/free-search/main.py "WebAssembly" --format json

# Markdown 输出
python .claude/skills/free-search/main.py "区块链技术" --format markdown
```

### 4.4 缓存管理

```bash
# 清除缓存
python .claude/skills/free-search/main.py "" --clear-cache

# 显示缓存统计
python .claude/skills/free-search/main.py "" --cache-stats

# 禁用缓存
python .claude/skills/free-search/main.py "最新新闻" --no-cache
```

---

## 5. 性能指标

| 场景 | 耗时 |
|------|------|
| Tavily 可用 | 2-3 秒 |
| DuckDuckGo 回退 | 3-5 秒 |
| AI 知识库回退 | 5-10 秒 |
| 缓存命中 | <0.1 秒 |

---

## 6. 依赖项

```
requests>=2.31.0
duckduckgo-search>=4.0.0
zhipuai>=0.1.0
```

---

## 7. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3.3.0 | 2026-03-19 | 移除 ZhipuMCP 提供商，简化为 4 级回退 |
| v3.1.0 | 2026-03-19 | 添加 Serper.dev 提供商 |
| v3.0.0 | 2026-03-08 | 迁移到 Anthropic 官方标准架构 |
| v2.6.0 | 2026-03-07 | 移除 GLM Web Search 提供商 |
| v1.0.0 | 2026-03-03 | 初始版本 |

---

## 8. 相关文件

- **SKILL.md**: `.claude/skills/free-search/SKILL.md`
- **主入口**: `.claude/skills/free-search/main.py`
- **核心引擎**: `.claude/skills/free-search/scripts/search_engine.py`
