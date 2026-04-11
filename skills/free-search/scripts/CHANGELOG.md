# Free Search Skill - Changelog

## [3.3.0] - 2026-03-19

### 重大更新 ⭐

- **移除ZhipuMCP Provider** - 简化架构
  - 移除 `providers/zhipu_mcp_provider.py` 的使用
  - Fallback层级从5级简化为4级
  - CLI移除 `--source zhipu_mcp` 选项

### 改进 📈

- **Fallback层级简化**：从5级简化为4级
  - Level 1: Tavily API（第三方服务，高质量搜索）
  - Level 2: Serper.dev（Google搜索结果API）
  - Level 3: DuckDuckGo（免费搜索）
  - Level 4: AI知识库（最后手段）

### 技术细节 🔧

**修改文件**：
- `search_engine.py` - 移除ZhipuMCPProvider导入和实例化
- `main.py` - 移除 `--source zhipu_mcp` 选项
- `SKILL.md` - 更新文档
- `README.md` - 更新文档

### 向后兼容

- ⚠️ `--source zhipu_mcp` 选项已移除，使用 `--source tavily` 或 `auto` 代替

---

## [3.1.0] - 2026-03-19

### 新增功能 ⭐

- **Serper.dev Provider** - 新增Google搜索结果API作为fallback
  - 高质量搜索结果
  - 支持中文搜索 (hl: zh-cn, gl: cn)
  - API Key自动检测：`C:\D\CAIE_tool\LLM_Configs\serper\apikey.txt`

### 改进 📈

- **Fallback层级升级**：从4级升级到5级
  - Level 1: ZhipuMCP
  - Level 2: Tavily API
  - Level 3: **Serper.dev** (NEW)
  - Level 4: DuckDuckGo
  - Level 5: AI知识库

---

## [2.4.0] - 2026-03-06

### 重大更新 ⭐

- **统一MCP Provider - 智能配额自动切换**
  - **新增文件**：`providers/zhipu_mcp_provider.py`
  - **核心功能**：当配额1用尽时，自动切换到配额2
  - **自动检测**：错误码1310自动识别为配额用尽
  - **无缝切换**：用户无感知的配额切换体验
  - **完全兼容**：保持原有API不变

### 改进 📈

- **Fallback层级简化**：从6级简化为5级
  - Level 1: 智谱MCP（内部自动切换配额1→配额2）⭐ NEW
  - Level 2: Tavily API（第三方服务）
  - Level 3: GLM Web Search（GLM-4-flash）
  - Level 4: DuckDuckGo（免费搜索）
  - Level 5: AI知识库（最后手段）

### 技术细节 🔧

**新增文件**：
- `providers/zhipu_mcp_provider.py` - 智能MCP provider（支持自动配额切换）
- `providers/mcp_unified_provider.py` - 统一MCP provider接口（保留）

**修改文件**：
- `search_engine.py` - 使用ZhipuMCPProvider替代两个独立的MCP provider
- `main.py` - 更新--source选项（移除mcp_websearch和mcp_websearch_2，添加zhipu_mcp）

### 工作原理

```
用户发起搜索
  ↓
尝试配额1
  ↓
配额1返回错误1310？
  ├─ 是 → 自动切换到配额2 ✨
  │     ↓
  │   配额2成功？
  │     ├─ 是 → 返回结果 ✅
  │     └─ 否 → fallback到Tavily
  │
  └─ 否 → 返回结果 ✅
```

### 测试结果 ✅

```bash
$ python main.py "测试搜索" --source zhipu_mcp
[INFO] 尝试 zhipu_mcp...
[SUCCESS] zhipu_mcp（配额1）返回结果
```

**特性**：
- ✅ 自动检测配额用尽（错误码1310）
- ✅ 无缝切换到备用配额
- ✅ 完全透明，用户无感知
- ✅ 支持两个API key文件
- ✅ 支持环境变量配置

### API Key配置

**配额1**（优先使用）：
- 文件：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue.txt`
- 环境变量：`ZHIPU_API_KEY`

**配额2**（备用配额）：
- 文件：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt`
- 环境变量：`ZHIPU_API_KEY_2`

### 使用示例

```bash
# 自动模式（会使用智能MCP provider）
python main.py "搜索内容"

# 指定使用智谱MCP
python main.py "搜索内容" --source zhipu_mcp

# 查看配额状态
python -c "from providers.zhipu_mcp_provider import ZhipuMCPProvider; p = ZhipuMCPProvider(); import json; print(json.dumps(p.get_status(), indent=2, ensure_ascii=False))"
```

### 向后兼容

- ✅ 旧的命令仍然有效（`--source mcp_websearch` 会自动映射到 `zhipu_mcp`）
- ✅ 代码兼容（不破坏现有代码）
- ✅ 配置兼容（API key文件路径不变）

### 已知限制

- 配额切换需要API返回错误码1310
- 如果API没有返回错误码，可能无法自动识别配额用尽
- 需要zhipuai库已安装

---

## [2.3.0] - 2026-03-06

### 新增功能 ⭐

- **第二个MCP WebSearch Provider** - 支持使用第二个智谱Coding Plan配额
  - **新增文件**：`providers/mcp_websearch_provider_2.py`
  - **API Key来源**：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt`
  - **用途**：当第一个MCP配额用尽时，自动切换到第二个配额
  - **优先级**：Priority 2（在第一个MCP之后，Tavily之前）

### 改进 📈

- **Fallback层级升级**：从5级升级到6级
  - Level 1: MCP WebSearch（配额1，apikeyValue.txt）
  - Level 2: **MCP WebSearch 2**（配额2，apikeyValue2.txt）⭐ NEW
  - Level 3: Tavily API（第三方服务）
  - Level 4: GLM Web Search（GLM-4-flash）
  - Level 5: DuckDuckGo（免费搜索）
  - Level 6: AI知识库（最后手段）

### 技术细节 🔧

**新增文件**：
- `providers/mcp_websearch_provider_2.py` - 第二个MCP WebSearch provider

**修改文件**：
- `search_engine.py` - 添加第二个MCP provider到fallback链
- `config.py` - 新增 `get_zhipu_api_key_2()` 函数
- `main.py` - 更新--source参数选项（支持mcp_websearch_2）
- `README.md` - 更新文档说明

### 使用场景

**适用情况**：
- ✅ 第一个MCP配额用尽（错误码1310）
- ✅ 需要继续使用MCP WebSearch的高质量结果
- ✅ 避免立即fallback到Tavily（保留Tavily配额）

### API Key配置

**第一个配额**：
- 文件：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue.txt`
- 状态：已用完 ⚠️

**第二个配额**：
- 文件：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt`
- 状态：未使用 ✅
- API Key：`a17077c0ef7248149c90705326dfd321.vDH9pWpVRYYxx4gp`

---

## [2.2.1] - 2026-03-06

### 改进 🔄

- **Fallback顺序调整**：将Tavily保持在Priority 2，GLM Web Search在Priority 3
  - **原因**：GLM Web Search也使用智谱API（按token计费），与MCP同属智谱服务
  - **新顺序**：MCP → Tavily → GLM → DuckDuckGo → AI知识库
  - **好处**：Tavily是第三方服务，配额独立，优先使用避免智谱配额同时耗尽

### 技术细节

**修改文件**：
- `search_engine.py`: 调整providers列表顺序（Tavily在GLM之前）
- `README.md`: 更新fallback顺序文档

---

## [2.2.0] - 2026-03-06

### 新增功能 ⭐

- **GLM Web Search Provider** - 新增第3级fallback选项
  - 使用GLM-4-flash模型的web_search工具
  - API Key配置：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt`
  - 在Tavily配额用尽时自动激活
  - 支持指定使用：`--source glm_web_search`

### 改进 📈

- **Fallback层级升级**：从4级升级到5级
  - Level 1: MCP WebSearch（智谱Coding Plan配额）
  - Level 2: Tavily API（高质量搜索）
  - Level 3: **GLM Web Search**（新增，使用GLM-4-flash）
  - Level 4: DuckDuckGo（免费搜索）
  - Level 5: AI知识库（预训练知识）

### 技术细节 🔧

**新增文件**：
- `providers/glm_web_search_provider.py` - GLM Web Search provider实现

**修改文件**：
- `search_engine.py` - 添加GLM provider到fallback链
- `main.py` - 更新--source参数选项
- `README.md` - 更新文档说明

### 测试结果 ✅

```bash
# 测试1：直接使用GLM Web Search
python main.py "donghongfei feishu_batch_download" --source glm_web_search
# 结果：✅ 成功返回1条结果，耗时16.81秒

# 测试2：自动fallback（MCP不可用 → Tavily成功）
python main.py "eternalfree feishu-doc-export"
# 结果：✅ MCP跳过，Tavily成功，耗时3.54秒
```

### API Key配置

使用文件：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt`
- 通过 `config.py` 的 `get_zhipu_api_key()` 函数读取
- 与AI知识库provider共用同一个API key

### 性能对比

| Provider | 响应时间 | 质量 | 成本 |
|----------|---------|------|------|
| MCP WebSearch | ~2秒 | ⭐⭐⭐⭐⭐ | 免费（配额限制）|
| Tavily | ~3秒 | ⭐⭐⭐⭐⭐ | 付费（1000次/月免费）|
| **GLM Web Search** | ~17秒 | ⭐⭐⭐⭐ | 按token计费 |
| DuckDuckGo | ~4秒 | ⭐⭐⭐ | 免费 |
| AI知识库 | ~6秒 | ⭐⭐ | 按token计费 |

### 已知限制

- GLM Web Search响应时间较长（~17秒）
- 返回格式为整合内容，而非结构化搜索结果列表
- 依赖GLM-4-flash模型的web_search工具可用性

---

## [2.1.0] - 2026-03-06

### 改进

**MCP WebSearch 智能环境检测**
- ✅ **CLI 模式优化**：MCP WebSearch 在 CLI 下自动跳过，不再浪费时间
- ✅ **Skill 模式支持**：通过 `SKILL_CALL=1` 环境变量识别 Skill tool 调用
- ✅ **多级检测**：支持 `SKILL_CALL`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_AGENT` 三种环境变量

### 技术细节

**变更文件**：
- `providers/mcp_websearch_provider.py`: 增强 `is_available()` 方法
- `skill_wrapper.py`: 新增 Skill 包装器（设置环境变量）
- `.skill/SKILL.md`: 新增 Skill 定义文档

**Fallback 行为变化**：
- **之前**：CLI 模式下每次都尝试 MCP WebSearch → 返回 `MCP_WEBSKILL_REQUIRED` → 尝试下一个
- **现在**：CLI 模式下 `is_available()` 返回 False → 直接跳过 → 从 Tavily 开始

### 测试结果

```bash
# CLI 模式（直接调用）
$ python main.py "测试搜索"
[INFO] 尝试 mcp_websearch...
[WARNING] mcp_websearch 不可用，尝试下一个...  ← 立即跳过
[INFO] 尝试 tavily...
[SUCCESS] tavily 返回 5 条结果

# Skill 模式（通过 Skill tool 调用）
$ SKILL_CALL=1 python skill_wrapper.py "测试搜索"
[INFO] 尝试 mcp_websearch...
[SUCCESS] mcp_websearch 返回结果  ← 正常使用
```

---

## [2.0.0] - 2026-03-03

### 初始版本

- 4 级 fallback 架构（MCP WebSearch → Tavily → DuckDuckGo → AI Knowledge）
- 智能缓存系统（MD5-based, 50-70x speedup）
- 多种输出格式（text, JSON, markdown）
- 配置文件支持（Tavily API key 自动检测）
