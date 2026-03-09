# 智能配额切换功能 - 快速参考

## 🎯 功能概述

**自动切换配额**：当配额1用尽时，自动切换到配额2

**效果**：用户无感知，搜索持续可用

---

## ⚡ 快速开始

### 基本使用

```bash
# 自动模式（推荐）
python main.py "搜索内容"

# 指定使用智谱MCP
python main.py "搜索内容" --source zhipu_mcp
```

### 预期行为

**场景1：配额1可用** ✅
```
[INFO] 尝试 zhipu_mcp...
[SUCCESS] zhipu_mcp（配额1）返回结果
```

**场景2：配额1用尽** 🔄
```
[WARNING] 配额1已用尽（错误码1310）
[INFO] 切换到配额2
[SUCCESS] zhipu_mcp（配额2）返回结果
```

**场景3：配额都用尽** ⚠️
```
[WARNING] 配额1已用尽（错误码1310）
[WARNING] 配额2已用尽（错误码1310）
[INFO] 尝试 tavily...
[SUCCESS] tavily 返回结果
```

---

## 🔑 配置

### 配额1（优先）

**文件**：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue.txt`

**环境变量**：`ZHIPU_API_KEY`

### 配额2（备用）

**文件**：`C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt`

**环境变量**：`ZHIPU_API_KEY_2`

---

## 🔍 验证切换

### 模拟配额1用尽

```bash
# 备份配额1
cd C:\D\CAIE_tool\MyAIProduct\LLM_Configs\GLM
mv apikeyValue.txt apikeyValue.txt.backup

# 测试搜索（应该使用配额2）
cd C:\D\CAIE_tool\MyAIProduct\skills\web-search
python main.py "测试配额切换" --source zhipu_mcp

# 恢复配额1
cd C:\D\CAIE_tool\MyAIProduct\LLM_Configs\GLM
mv apikeyValue.txt.backup apikeyValue.txt
```

### 查看配额状态

```python
from providers.zhipu_mcp_provider import ZhipuMCPProvider
import json

p = ZhipuMCPProvider()
print(json.dumps(p.get_status(), indent=2, ensure_ascii=False))
```

---

## 📊 Fallback链

```
1. 智谱MCP（配额1 → 配额2自动切换）✨
   ↓ 都用尽
2. Tavily API
   ↓ 用尽
3. GLM Web Search
   ↓ 用尽
4. DuckDuckGo
   ↓ 用尽
5. AI知识库
```

---

## 💡 常见问题

### Q: 如何知道正在使用哪个配额？

**A**: 查看日志中的provider名称：
- `zhipu_mcp（配额1）` - 使用配额1
- `zhipu_mcp（配额2）` - 使用配额2

### Q: 切换需要多长时间？

**A**: 几乎即时。切换逻辑在内存中完成，无额外延迟。

### Q: 切换失败怎么办？

**A**: 会自动fallback到Tavily，确保搜索功能始终可用。

### Q: 可以禁用自动切换吗？

**A**: 可以使用其他搜索源：
```bash
python main.py "搜索内容" --source tavily
python main.py "搜索内容" --source duckduckgo
```

---

## ✨ 核心优势

| 特性 | 说明 |
|------|------|
| **智能切换** | 自动识别错误1310，切换配额 |
| **透明无感** | 切换过程对用户透明 |
| **高可用性** | 双配额 + 5级fallback保障 |
| **简单易用** | 无需修改任何配置，开箱即用 |

---

## 📁 相关文件

- **核心代码**: `providers/zhipu_mcp_provider.py`
- **搜索引擎**: `search_engine.py`
- **详细文档**: `test/temp/intelligent_quota_switching_report.md`

---

**版本**: v2.4.0
**更新时间**: 2026-03-06
**状态**: ✅ 已完成
