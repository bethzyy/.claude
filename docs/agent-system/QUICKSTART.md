# 执行-审查Agent系统 - 5分钟快速上手

## 📍 文件位置

```
C:/D/CAIE_tool/MyAIProduct/
├─ .claude/
│  ├─ skills/
│  │  ├─ task-executor/       ← 执行Agent
│  │  ├─ quality-reviewer/    ← 审查Agent
│  │  ├─ task-coordinator/    ← 任务协调器
│  │  └─ README-AGENT-SYSTEM.md
│  │
│  └─ docs/
│     └─ agent-system/        ← 文档中心（你在这里）
│        ├─ README.md         ← 本文件
│        ├─ AGENT-SYSTEM-FILES.md
│        ├─ UPLOAD-GUIDE.md
│        ├─ pre_upload_check.py
│        ├─ upload_agent_system.bat
│        └─ upload_agent_system.sh
│
└─ test/
   └─ skill-evals/
      └─ task-executor/
         └─ test_skill_integration.py
```

## 🚀 3步上手

### Step 1: 验证安装

```bash
cd C:/D/CAIE_tool/MyAIProduct
python .claude/docs/agent-system/pre_upload_check.py
```

期望输出：
```
[OK] All checks passed (4/4)
Safe to upload to GitHub!
```

### Step 2: 运行测试

```bash
python test/skill-evals/task-executor/test_skill_integration.py
```

### Step 3: 执行任务

**方式1: 使用协调器**
```bash
python .claude/skills/task-coordinator/main.py \
    --type composite \
    --composite-type article_with_images \
    --topic "人工智能" \
    --num-images 3
```

**方式2: 使用Python代码**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / '.claude' / 'skills' / 'task-executor'))

from executor import ExecutorAgent

agent = ExecutorAgent(
    task_id="demo",
    task_dir=Path("test/temp")
)

result = agent.execute_task({
    "type": "composite",
    "composite_type": "article_with_images",
    "topic": "量子计算",
    "num_images": 2
})

print(result)
```

## 📚 文档导航

| 我想... | 查看文档 |
|---------|---------|
| 了解系统架构 | [系统架构文档](../README-AGENT-SYSTEM.md) |
| 上传到GitHub | [上传指南](UPLOAD-GUIDE.md) |
| 查看文件清单 | [文件清单](AGENT-SYSTEM-FILES.md) |
| 运行测试 | [测试文档](../README-AGENT-SYSTEM.md#测试) |

## 🔗 相关链接

- [项目主文档](../../../CLAUDE.md)
- [进度追踪](../../../PROGRESS.md)
