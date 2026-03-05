# 执行-审查Agent系统 - 完整文件结构

## 📂 目录结构

```
C:/D/CAIE_tool/MyAIProduct/
│
├─ .claude/
│  ├─ skills/                          # Agent系统核心代码
│  │  ├─ task-executor/                # 执行Agent v2.0.0
│  │  │  ├─ executor.py                # 执行Agent核心 (19KB)
│  │  │  ├─ skill_integrator.py        # Skill集成器 (14KB) ✨新增
│  │  │  ├─ main.py                    # 命令行入口
│  │  │  └─ SKILL.md
│  │  │
│  │  ├─ quality-reviewer/             # 审查Agent
│  │  │  ├─ reviewer.py                # 审查核心 (20KB)
│  │  │  ├─ main.py
│  │  │  └─ review_criteria/           # 审查标准
│  │  │     ├─ security.json
│  │  │     ├─ code_quality.json
│  │  │     └─ content_quality.json
│  │  │
│  │  ├─ task-coordinator/             # 任务协调器
│  │  │  ├─ coordinator.py             # 协调器核心 (5KB)
│  │  │  └─ main.py
│  │  │
│  │  └─ README-AGENT-SYSTEM.md        # 系统架构文档 (12KB)
│  │
│  └─ docs/                            # 文档中心 ✨新增
│     └─ agent-system/                 # Agent系统专属文档
│        ├─ README.md                  # 📚 系统总览（入口）
│        ├─ QUICKSTART.md              # 🚀 5分钟快速上手
│        ├─ STRUCTURE.md               # 📁 本文件
│        ├─ AGENT-SYSTEM-FILES.md      # 📋 文件清单
│        ├─ UPLOAD-GUIDE.md            # 📤 上传指南
│        ├─ pre_upload_check.py        # 🔍 上传前检查
│        ├─ upload_agent_system.bat    # 🚀 Windows上传脚本
│        └─ upload_agent_system.sh     # 🚀 Linux/Mac上传脚本
│
└─ test/                               # 测试文件
   └─ skill-evals/
      └─ task-executor/
         └─ test_skill_integration.py  # 集成测试 (7KB) ✨新增
```

## 📚 文档导航

### 快速入口

| 文档 | 路径 | 说明 |
|------|------|------|
| **系统总览** | `.claude/docs/agent-system/README.md` | 完整的系统介绍和特性说明 |
| **快速上手** | `.claude/docs/agent-system/QUICKSTART.md` | 5分钟快速上手指南 |
| **文件清单** | `.claude/docs/agent-system/AGENT-SYSTEM-FILES.md` | 需要上传的文件列表 |
| **上传指南** | `.claude/docs/agent-system/UPLOAD-GUIDE.md` | GitHub上传详细步骤 |

### 技术文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **系统架构** | `.claude/skills/README-AGENT-SYSTEM.md` | 详细的技术架构和API文档 |
| **项目指南** | `CLAUDE.md` | 整个项目的主文档 |

## 🎯 关键文件

### 核心代码

| 文件 | 大小 | 版本 | 说明 |
|------|------|------|------|
| `skill_integrator.py` | 14KB | v1.0.0 | ✨新增 - 统一skill调用接口 |
| `executor.py` | 19KB | v2.0.0 | 🔄更新 - 执行Agent核心 |
| `reviewer.py` | 20KB | v1.0.0 | ✓ - 审查Agent核心 |
| `coordinator.py` | 5KB | v1.0.0 | ✓ - 任务协调器 |

### 文档文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `README.md` | ~5KB | ✨新增 - 系统总览 |
| `QUICKSTART.md` | ~3KB | ✨新增 - 快速上手 |
| `AGENT-SYSTEM-FILES.md` | ~4KB | 文件清单 |
| `UPLOAD-GUIDE.md` | ~8KB | 上传指南 |

### 脚本文件

| 文件 | 说明 |
|------|------|
| `pre_upload_check.py` | 上传前检查脚本 |
| `upload_agent_system.bat` | Windows上传脚本 |
| `upload_agent_system.sh` | Linux/Mac上传脚本 |

## 🚀 快速访问

### 查看文档

```bash
# Windows
start .claude\docs\agent-system\README.md

# Linux/Mac
open .claude/docs/agent-system/README.md
```

### 运行检查

```bash
cd C:/D/CAIE_tool/MyAIProduct
python .claude/docs/agent-system/pre_upload_check.py
```

### 上传到GitHub

```bash
cd C:/D/CAIE_tool/MyAIProduct
claude/docs/agent-system/upload_agent_system.bat
```

## 📊 统计信息

```
代码文件: 4个 (~58KB)
文档文件: 7个 (~27KB)
测试文件: 1个 (~7KB)
脚本文件: 3个 (~8KB)
─────────────────────
总计: 15个文件 (~100KB)
```

## 🎯 下一步

1. **阅读文档**: 从 `.claude/docs/agent-system/README.md` 开始
2. **运行检查**: 执行 `pre_upload_check.py` 验证系统
3. **上传GitHub**: 使用上传脚本或手动上传

---

**创建时间**: 2026-03-05
**版本**: 2.0.0
**维护者**: Claude Code
