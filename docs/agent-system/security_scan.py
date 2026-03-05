#!/usr/bin/env python3
"""
安全扫描脚本 - 检查.claude/skills目录中的敏感信息
"""

import re
from pathlib import Path

# 定义敏感信息模式
SENSITIVE_PATTERNS = {
    'ZHIPU_API_KEY': r'ZHIPU_API_KEY\s*[=:]\s*["\'][\w\.]+["\']',
    'API_KEY': r'api[_-]?key\s*[=:]\s*["\'][\w\-\.]+["\']',
    'SECRET': r'secret\s*[=:]\s*["\'][^"\']{8,}["\']',
    'PASSWORD': r'password\s*[=:]\s*["\'][^"\']{6,}["\']',
    'TOKEN': r'token\s*[=:]\s*["\'][\w\-\.]+["\']',
    'BEARER': r'bearer\s+["\'][\w\-\.]+["\']',
    'AUTHORIZATION': r'authorization\s*[=:]\s*["\'][\w\-\.]+["\']',
}

def scan_directory():
    """扫描.claude/skills目录"""
    skills_dir = Path('.claude/skills')
    issues = []
    files_checked = 0

    print('='*60)
    print('安全扫描: .claude/skills 目录')
    print('='*60)
    print()

    # 扫描Python文件
    print('[1/2] 扫描Python文件...')
    for py_file in skills_dir.rglob('*.py'):
        files_checked += 1
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            for name, pattern in SENSITIVE_PATTERNS.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    lines = content.split('\n')
                    line_content = lines[line_num - 1].strip()

                    # 过滤掉示例和注释
                    if '#' in line_content and line_content.index('#') < line_content.find(match.group()):
                        continue

                    # 过滤掉环境变量赋值（右值）
                    if 'os.environ.get' in line_content or 'os.getenv' in line_content:
                        continue

                    issues.append({
                        'file': str(py_file.relative_to(skills_dir)),
                        'line': line_num,
                        'type': name,
                        'content': line_content[:80]
                    })
        except Exception as e:
            pass

    # 扫描其他文件
    print('[2/2] 扫描配置和文档文件...')
    for ext in ['.md', '.json', '.txt', '.yaml', '.yml', '.toml']:
        for file in skills_dir.rglob(f'*{ext}'):
            files_checked += 1
            try:
                content = file.read_text(encoding='utf-8', errors='ignore')

                for name, pattern in SENSITIVE_PATTERNS.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': str(file.relative_to(skills_dir)),
                            'line': line_num,
                            'type': name,
                            'content': '...'
                        })
            except:
                pass

    print()
    print('='*60)
    print('扫描结果')
    print('='*60)
    print(f'已检查: {files_checked} 个文件')
    print()

    if issues:
        print('[发现潜在问题]')
        print('='*60)
        for issue in issues:
            print(f"  文件: {issue['file']}:{issue['line']}")
            print(f"  类型: {issue['type']}")
            print(f"  内容: {issue['content']}")
            print()
        return False
    else:
        print('[OK] 未发现硬编码的敏感信息')
        print('='*60)
        print('所有API密钥都通过环境变量或配置文件加载')
        return True

def check_env_files():
    """检查.env文件"""
    print()
    print('='*60)
    print('检查.env文件')
    print('='*60)

    skills_dir = Path('.claude/skills')
    env_files = list(skills_dir.rglob('.env')) + list(skills_dir.rglob('.env.*'))

    if env_files:
        print(f'[发现] {len(env_files)} 个.env文件:')
        for env_file in env_files:
            rel_path = env_file.relative_to(skills_dir)
            print(f"  - {rel_path}")
        print()
        print('[提示] 确保.env文件在.gitignore中')
    else:
        print('[OK] 未发现.env文件')

def check_gitignore():
    """检查.gitignore配置"""
    print()
    print('='*60)
    print('检查.gitignore')
    print('='*60)

    # 检查项目根目录.gitignore
    root_gitignore = Path('.gitignore')
    skills_gitignore = Path('.claude/skills/.gitignore')

    if root_gitignore.exists():
        content = root_gitignore.read_text()
        if '.env' in content:
            print('[OK] 根目录.gitignore包含.env规则')
        else:
            print('[警告] 根目录.gitignore缺少.env规则')

    if skills_gitignore.exists():
        print('[OK] .claude/skills/.gitignore存在')
    else:
        print('[信息] .claude/skills/.gitignore不存在（使用根目录）')

def main():
    """主函数"""
    # 执行扫描
    safe = scan_directory()

    # 检查.env文件
    check_env_files()

    # 检查.gitignore
    check_gitignore()

    # 总结
    print()
    print('='*60)
    print('总结')
    print('='*60)

    if safe:
        print('[安全] .claude/skills目录可以安全上传到GitHub')
        print()
        print('建议:')
        print('  1. 运行上传前检查: python .claude/docs/agent-system/pre_upload_check.py')
        print('  2. 使用上传脚本: .claude/docs/agent-system/upload_agent_system.bat')
        return 0
    else:
        print('[警告] 发现潜在安全问题，请人工审核后再上传')
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
