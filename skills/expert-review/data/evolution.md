# Expert Review Evolution State

> 此文件由 expert-review skill 自动维护。记录审查进化状态，驱动自我改进。
> ⚠️ 一般不需要手动编辑。如需重置，删除此文件即可。

## Statistics

- Total reviews conducted: 2
- Total issues found: 505
- Average issues per review: 252.5
- Last review: 2026-04-11 07:20
- Last project: package

## Current Baseline

- Issues found: 276
- By severity: critical=3, high=169, medium=70, low=34
- Duration: 0.8 seconds
- Actionability score: 100.0%

## Internalized Patterns (auto-included in every review)

> 出现 3+ 次的检查模式自动升级为必查项。

- [?] [reliability] 检查 reliability 类问题: missing finally: with open(fil (internalized 2026-04-11, after 9 appearances) (internalized ?, after ? appearances)
- [?] [maintainability] 检查 maintainability 类问题: Long function (54 lines) (internalized 2026-04-11, after 3 appearances) (internalized ?, after ? appearances)
- [?] [reliability] 检查 reliability 类问题: missing finally: with open(con (internalized 2026-04-11, after 18 appearances) (internalized ?, after ? appearances)
- [?] [reliability] 检查 reliability 类问题: missing finally: with open(env (internalized 2026-04-11, after 5 appearances) (internalized ?, after ? appearances)
- [?] [bug] 检查 bug 类问题: bare except: except: (internalized 2026-04-11, after 5 appearances) (internalized ?, after ? appearances)
- [?] [reliability] 检查 reliability 类问题: missing finally: with open(out (internalized 2026-04-11, after 7 appearances) (internalized ?, after ? appearances)
- [?] [reliability] 检查 reliability 类问题: missing finally: with open(dat (internalized 2026-04-11, after 3 appearances) (internalized ?, after ? appearances)
- [?] [testing] 检查 testing 类问题: Missing tests for critical mod (internalized 2026-04-11, after 7 appearances) (internalized ?, after ? appearances)
- [?] [testing] 检查 testing 类问题: Missing tests: baidu_crawler_v (internalized 2026-04-11, after 3 appearances) (internalized ?, after ? appearances)
- [?] [security] 检查 security 类问题: OWASP A05-Security Misconfigur (internalized 2026-04-11, after 4 appearances) (internalized ?, after ? appearances)
- [?] [security] 检查 security 类问题: OWASP A01-Broken Access Contro (internalized 2026-04-11, after 3 appearances) (internalized ?, after ? appearances)
- [?] [reliability] 检查 reliability 类问题: Bare except clause (internalized 2026-04-11, after 5 appearances) (internalized ?, after ? appearances)
- [?] [reliability] 检查 reliability 类问题: Using print() instead of loggi (internalized 2026-04-11, after 56 appearances) (internalized ?, after ? appearances)
- [security] 检查 security 类问题: debug mode: app.run(host='0.0. (internalized 2026-04-11, after 5 appearances)
- [reliability] 检查 reliability 类问题: missing finally: with open(fil (internalized 2026-04-11, after 9 appearances)
- [bug] 检查 bug 类问题: bare except: except: (internalized 2026-04-11, after 3 appearances)
- [maintainability] 检查 maintainability 类问题: Long function (54 lines) (internalized 2026-04-11, after 3 appearances)
- [maintainability] 检查 maintainability 类问题: Long function (51 lines) (internalized 2026-04-11, after 4 appearances)
- [architecture] 检查 architecture 类问题: Circular import: core\template (internalized 2026-04-11, after 4 appearances)
- [architecture] 检查 architecture 类问题: Circular import: core\payment\ (internalized 2026-04-11, after 4 appearances)
- [architecture] 检查 architecture 类问题: Circular import: core\provider (internalized 2026-04-11, after 4 appearances)
- [testing] 检查 testing 类问题: No assertions in test file: te (internalized 2026-04-11, after 11 appearances)
- [testing] 检查 testing 类问题: No error/edge case tests in te (internalized 2026-04-11, after 3 appearances)
- [security] 检查 security 类问题: OWASP A01-Broken Access Contro (internalized 2026-04-11, after 76 appearances)
- [security] 检查 security 类问题: OWASP A02-Cryptographic Failur (internalized 2026-04-11, after 16 appearances)
- [security] 检查 security 类问题: OWASP A05-Security Misconfigur (internalized 2026-04-11, after 5 appearances)
- [reliability] 检查 reliability 类问题: Bare except clause (internalized 2026-04-11, after 3 appearances)
- [reliability] 检查 reliability 类问题: Database operations without er (internalized 2026-04-11, after 3 appearances)

## Anti-Patterns (suppress these checks)

> 已确认为噪音的检查类型，不再报告。

_No anti-patterns yet. False positives will be added here._

## Project-Specific Knowledge

- project_name: package
- test_command: pytest tests/ -v
- framework: Flask

## Prompt Deltas Applied This Session

_No prompt deltas applied this session._
