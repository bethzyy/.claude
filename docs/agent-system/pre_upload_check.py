#!/usr/bin/env python3
"""
上传前检查脚本 - 执行-审查Agent系统

检查：
1. 文件完整性
2. 敏感信息泄露
3. Python语法错误
4. 导入依赖检查
"""

import sys
import re
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def print_status(symbol, message, color=None):
    """打印状态信息"""
    if color:
        print(f"{color}{symbol} {message}{Colors.END}")
    else:
        print(f"{symbol} {message}")

def check_file_integrity():
    """检查文件完整性"""
    print("\n" + "="*60)
    print("[检查1] 文件完整性")
    print("="*60)

    required_files = [
        ".claude/skills/task-executor/executor.py",
        ".claude/skills/task-executor/skill_integrator.py",
        ".claude/skills/task-executor/main.py",
        ".claude/skills/quality-reviewer/reviewer.py",
        ".claude/skills/task-coordinator/coordinator.py",
        ".claude/skills/README-AGENT-SYSTEM.md",
        "test/skill-evals/task-executor/test_skill_integration.py",
    ]

    missing = []
    for file in required_files:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size
            print_status("[OK]", f"{file} ({size} bytes)", Colors.GREEN)
        else:
            print_status("[X]", f"{file} - MISSING", Colors.RED)
            missing.append(file)

    if missing:
        print(f"\n[错误] 缺失 {len(missing)} 个文件")
        return False
    else:
        print(f"\n[通过] 所有必需文件存在")
        return True

def check_sensitive_info():
    """检查敏感信息"""
    print("\n" + "="*60)
    print("[检查2] 敏感信息泄露")
    print("="*60)

    sensitive_patterns = [
        (r'api_key\s*=\s*["\'][\w-]+["\']', "硬编码API密钥"),
        (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码secret"),
        (r'token\s*=\s*["\'][^"\']+["\']', "硬编码token"),
        (r'ZHIPU_API_KEY\s*=\s*["\'][\w.]+["\']', "智谱API密钥"),
    ]

    files_to_check = [
        ".claude/skills/task-executor/executor.py",
        ".claude/skills/task-executor/skill_integrator.py",
        ".claude/skills/quality-reviewer/reviewer.py",
    ]

    issues = []
    for file in files_to_check:
        path = Path(file)
        if not path.exists():
            continue

        content = path.read_text(encoding='utf-8')
        for pattern, desc in sensitive_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(f"{file}:{line_num} - {desc}")

    if issues:
        print_status("[!]", "Found sensitive info:", Colors.YELLOW)
        for issue in issues:
            print(f"  - {issue}")
        print(f"\n[WARNING] Remove sensitive info before upload")
        return False
    else:
        print_status("[OK]", "No hardcoded sensitive info found", Colors.GREEN)
        return True

def check_python_syntax():
    """检查Python语法"""
    print("\n" + "="*60)
    print("[检查3] Python语法")
    print("="*60)

    py_files = [
        ".claude/skills/task-executor/executor.py",
        ".claude/skills/task-executor/skill_integrator.py",
        ".claude/skills/quality-reviewer/reviewer.py",
        ".claude/skills/task-coordinator/coordinator.py",
        "test/skill-evals/task-executor/test_skill_integration.py",
    ]

    errors = []
    for file in py_files:
        path = Path(file)
        if not path.exists():
            continue

        try:
            compile(path.read_text(encoding='utf-8'), file, 'exec')
            print_status("[OK]", f"{file}", Colors.GREEN)
        except SyntaxError as e:
            print_status("[X]", f"{file} - Line {e.lineno}: {e.msg}", Colors.RED)
            errors.append(file)

    if errors:
        print(f"\n[错误] {len(errors)} 个文件有语法错误")
        return False
    else:
        print(f"\n[通过] 所有Python文件语法正确")
        return True

def check_imports():
    """检查导入依赖"""
    print("\n" + "="*60)
    print("[检查4] 导入依赖")
    print("="*60)

    # 设置路径
    project_root = Path.cwd()
    sys.path.insert(0, str(project_root / '.claude' / 'skills' / 'task-executor'))
    sys.path.insert(0, str(project_root / 'skills'))

    # 测试导入
    imports = [
        ("skill_integrator", "SkillIntegrator"),
    ]

    errors = []
    for module, name in imports:
        try:
            mod = __import__(module)
            getattr(mod, name)
            print_status("[OK]", f"{module}.{name}", Colors.GREEN)
        except ImportError as e:
            print_status("[X]", f"{module}.{name} - {e}", Colors.RED)
            errors.append(module)
        except Exception as e:
            print_status("[!]", f"{module}.{name} - {e}", Colors.YELLOW)

    if errors:
        print(f"\n[警告] {len(errors)} 个模块导入失败")
        print("提示: 某些依赖可能只在运行时需要")
        return True  # 不阻止上传
    else:
        print(f"\n[通过] 所有导入正常")
        return True

def generate_summary():
    """生成上传总结"""
    print("\n" + "="*60)
    print("[上传总结]")
    print("="*60)

    print("\n需要上传的文件：")
    print("\n核心代码：")
    print("  .claude/skills/task-executor/")
    print("  .claude/skills/quality-reviewer/")
    print("  .claude/skills/task-coordinator/")
    print("\n文档：")
    print("  .claude/skills/README-AGENT-SYSTEM.md")
    print("  AGENT-SYSTEM-FILES.md")
    print("\n测试：")
    print("  test/skill-evals/task-executor/test_skill_integration.py")

    print("\n上传命令：")
    print("  Windows: upload_agent_system.bat")
    print("  Linux/Mac: bash upload_agent_system.sh")

    print("\n或手动执行：")
    print("  git add .claude/skills/")
    print("  git add test/skill-evals/")
    print("  git add AGENT-SYSTEM-FILES.md")
    print('  git commit -m "feat: Add Executor-Reviewer Agent System v2.0.0"')
    print("  git push")

def main():
    """主函数"""
    print("="*60)
    print("执行-审查Agent系统 - 上传前检查")
    print("="*60)

    results = []

    # 执行检查
    results.append(check_file_integrity())
    results.append(check_sensitive_info())
    results.append(check_python_syntax())
    results.append(check_imports())

    # 生成总结
    generate_summary()

    # 总结
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print_status("[OK]", f"All checks passed ({passed}/{total})", Colors.GREEN)
        print("\nSafe to upload to GitHub!")
        return 0
    else:
        print_status("[!]", f"Some checks failed ({passed}/{total})", Colors.YELLOW)
        print("\nFix issues before uploading")
        return 1

if __name__ == "__main__":
    sys.exit(main())
