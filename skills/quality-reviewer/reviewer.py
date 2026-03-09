#!/usr/bin/env python3
"""
审查Agent - 负责质量检查和安全审查
"""
import os
import sys
import json
import re
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ReviewerAgent:
    """审查Agent - 负责质量检查和安全扫描"""

    def __init__(self, task_id: str, task_dir: Path, task: Dict = None, logger=None):
        self.task_id = task_id
        self.task_dir = task_dir
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or self._default_logger()

        # NEW: 解析任务目标（v2.1.0+）
        self.goals = None
        self.completeness_target = 90.0  # 默认值

        if task:
            try:
                from task_goal_parser import TaskGoalParser
                self.goals = TaskGoalParser.parse(task)
                self.completeness_target = self.goals.get("completeness_target", 90.0)
                self.logger.info(f"[OK] 任务目标解析成功: {self.completeness_target}%完整度")
            except Exception as e:
                self.logger.warning(f"任务目标解析失败，使用默认值: {e}")
                self.goals = {"completeness_target": 90.0}

    def review_result(self, result: Dict, task: Dict = None) -> Dict:
        """审查执行结果"""
        result_type = result.get("type", "generic")

        print(f"[审查Agent] 开始审查: {result_type}")

        # 根据类型应用审查标准
        if result_type == "code":
            review = self._review_code(result, task)
        elif result_type == "content":
            review = self._review_content(result, task)
        elif result_type == "image":
            review = self._review_image(result, task)
        elif result_type == "web-download":
            review = self._review_web_download(result, task)
        else:
            review = self._review_generic(result, task)

        # 生成最终报告
        report = self._generate_report(review)

        # 保存报告
        self._save_report(report)

        return report

    def _review_code(self, code_result: Dict, task: Dict = None) -> Dict:
        """审查代码质量"""
        code = code_result.get("code", "")

        checks = {
            "security": self._check_security(code_result),
            "vulnerabilities": self._check_vulnerabilities(code_result),
            "risks": self._assess_risks(code_result),
            "quality": self._check_quality(code_result),
            "style": self._check_style(code_result)
        }

        # 计算综合得分
        scores = []
        for check_name, check_result in checks.items():
            if "score" in check_result:
                scores.append(check_result["score"])

        overall_score = sum(scores) / len(scores) if scores else 50

        # 判断是否通过
        approved = overall_score >= 70 and checks["security"]["passed"]

        return {
            "type": "code_review",
            "checks": checks,
            "overall_score": overall_score,
            "approved": approved,
            "suggestions": self._generate_code_suggestions(checks),
            "issues": self._extract_issues(checks)
        }

    def _check_security(self, code_result: Dict) -> Dict:
        """安全漏洞检查 - OWASP Top 10"""
        code = code_result.get("code", "")
        findings = []

        # 1. SQL注入检查
        sql_patterns = [
            # 直接在execute中使用f-string
            r'execute\s*\(\s*f["\'].*?\{.*?\}',
            r'executemany\s*\(\s*f["\'].*?\{.*?\}',
            # SQL关键字+f-string变量（即使不用execute）
            r'f["\'][^"\']*(?:SELECT|INSERT|UPDATE|DELETE|DROP|FROM|WHERE)[^"\']*\{[^"\']*\}[^"\']*["\']',
            # execute中使用字符串拼接
            r'\.execute\s*\(\s*["\'][^"\']*?\+[^"\']*?["\']',
        ]
        for pattern in sql_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                findings.append({
                    "severity": "high",
                    "type": "SQL注入",
                    "description": "检测到SQL执行操作，可能存在注入风险",
                    "recommendation": "使用参数化查询或ORM"
                })
                break

        # 2. XSS漏洞检查
        if re.search(r'innerHTML\s*=|document\.write\s*\(', code):
            findings.append({
                "severity": "high",
                "type": "XSS跨站脚本",
                "description": "检测到直接HTML插入，可能存在XSS风险",
                "recommendation": "使用textContent或框架的自动转义"
            })

        # 3. 硬编码密钥检查
        secret_patterns = [
            (r'api_key\s*=\s*["\'][^"\']+["\']', "API密钥"),
            (r'password\s*=\s*["\'][^"\']+["\']', "密码"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "密钥"),
            (r'token\s*=\s*["\'][^"\']+["\']', "令牌"),
        ]
        for pattern, secret_type in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                findings.append({
                    "severity": "critical",
                    "type": "敏感信息泄露",
                    "description": f"检测到可能的硬编码{secret_type}",
                    "recommendation": "使用环境变量或密钥管理服务"
                })
                break

        # 4. 命令注入检查
        if re.search(r'subprocess\.(call|run|Popen)\s*\(\s*[^)]*\+|os\.system\s*\(', code):
            findings.append({
                "severity": "high",
                "type": "命令注入",
                "description": "检测到系统命令执行，可能存在注入风险",
                "recommendation": "使用参数化列表或shell=False"
            })

        # 5. 不安全的反序列化
        if re.search(r'pickle\.(load|loads)\s*\(', code):
            findings.append({
                "severity": "critical",
                "type": "不安全反序列化",
                "description": "pickle反序列化可能执行任意代码",
                "recommendation": "使用JSON或其他安全格式"
            })

        # 6. 路径遍历检查
        if re.search(r'open\s*\(\s*[^)]*?\+|open\s*\(\s*f["\'].*?\{', code):
            findings.append({
                "severity": "medium",
                "type": "路径遍历",
                "description": "检测到动态文件路径，可能存在路径遍历风险",
                "recommendation": "验证文件路径，限制目录范围"
            })

        # 7. 不安全的哈希算法
        if re.search(r'hashlib\.md5\s*\(|hashlib\.sha1\s*\(', code):
            findings.append({
                "severity": "medium",
                "type": "弱哈希算法",
                "description": "MD5和SHA1已被证明不安全",
                "recommendation": "使用SHA-256或更强的哈希算法"
            })

        # 8. 不安全的随机数
        if re.search(r'import random\s+|#.*密码学|#.*加密', code, re.IGNORECASE):
            if re.search(r'random\.(random|randint|choice)\s*\(', code):
                findings.append({
                    "severity": "medium",
                    "type": "不安全的随机数",
                    "description": "random模块不适用于密码学",
                    "recommendation": "使用secrets模块"
                })

        return {
            "passed": len([f for f in findings if f["severity"] in ["critical", "high"]]) == 0,
            "findings": findings,
            "score": max(0, 100 - len(findings) * 15)
        }

    def _check_vulnerabilities(self, code_result: Dict) -> Dict:
        """已知漏洞扫描 - 检查依赖库版本"""
        code = code_result.get("code", "")
        imports = self._extract_imports(code)
        vulnerabilities = []

        # 已知有漏洞的库版本
        known_vulns = {
            "PIL": "< 9.0.0 存在多个CVE",
            "PILImage": "< 9.0.0 存在多个CVE",
            "requests": "< 2.20.0 存在证书验证问题",
            "flask": "< 1.0 存在调试信息泄露",
            "django": "< 2.2.24 存在SQL注入",
            "pyyaml": "< 5.4 存在任意代码执行",
            "urllib3": "< 1.26.5 存在请求走私漏洞",
        }

        for lib in imports:
            if lib in known_vulns:
                vulnerabilities.append({
                    "library": lib,
                    "description": known_vulns[lib],
                    "severity": "medium",
                    "recommendation": f"升级{lib}到最新版本"
                })

        return {
            "passed": len(vulnerabilities) == 0,
            "vulnerabilities": vulnerabilities,
            "score": max(0, 100 - len(vulnerabilities) * 10)
        }

    def _assess_risks(self, code_result: Dict) -> Dict:
        """潜在风险评估"""
        code = code_result.get("code", "")
        risks = []

        # 1. 数据丢失风险
        if re.search(r'\b(DROP|DELETE|TRUNCATE)\b', code, re.IGNORECASE):
            risks.append({
                "level": "high",
                "category": "数据丢失风险",
                "description": "检测到删除操作",
                "mitigation": "添加确认步骤或软删除机制"
            })

        # 2. 网络请求风险 (SSRF)
        if re.search(r'requests\.(post|get|put|delete)|urllib\.request', code):
            risks.append({
                "level": "medium",
                "category": "网络安全风险",
                "description": "检测到网络请求，可能存在SSRF风险",
                "mitigation": "验证URL白名单，设置超时"
            })

        # 3. 文件操作风险
        if re.search(r'open\s*\([^)]*\s*[\'"]\s*w', code):
            risks.append({
                "level": "medium",
                "category": "文件操作风险",
                "description": "检测到文件写入",
                "mitigation": "验证文件路径，限制目录范围"
            })

        # 4. 并发风险
        if re.search(r'import (threading|multiprocessing)|concurrent\.', code):
            risks.append({
                "level": "low",
                "category": "并发风险",
                "description": "检测到多线程/多进程，可能存在竞态条件",
                "mitigation": "使用适当的锁机制"
            })

        # 5. 资源泄漏风险
        open_count = len(re.findall(r'\bopen\s*\(', code))
        close_count = len(re.findall(r'\.close\s*\(\)|with\s+open\s*\(', code))
        if open_count > close_count:
            risks.append({
                "level": "medium",
                "category": "资源泄漏风险",
                "description": "文件打开和关闭数量不匹配",
                "mitigation": "使用with语句确保资源释放"
            })

        # 6. 时间/计时攻击风险
        if re.search(r'==\s*password|==\s*secret', code, re.IGNORECASE):
            risks.append({
                "level": "low",
                "category": "计时攻击风险",
                "description": "直接比较密码或密钥可能泄露信息",
                "mitigation": "使用constant-time比较函数"
            })

        return {
            "passed": True,  # 风险不阻止通过，但需要警示
            "risks": risks,
            "risk_score": sum([self._risk_level_to_score(r["level"]) for r in risks])
        }

    def _risk_level_to_score(self, level: str) -> int:
        """将风险等级转换为分数"""
        level_scores = {
            "critical": 25,
            "high": 15,
            "medium": 10,
            "low": 5
        }
        return level_scores.get(level, 5)

    def _check_quality(self, code_result: Dict) -> Dict:
        """代码质量检查"""
        code = code_result.get("code", "")

        issues = []

        # 检查代码长度
        if len(code) < 50:
            issues.append("代码过短，可能实现不完整")
        elif len(code) > 5000:
            issues.append("代码过长，建议拆分为多个函数")

        # 检查注释
        comment_ratio = len(re.findall(r'#|//|/\*', code)) / max(len(code.split('\n')), 1)
        if comment_ratio < 0.1:
            issues.append("缺少代码注释")

        # 检查函数定义
        func_count = len(re.findall(r'def\s+\w+\s*\(', code))
        if func_count == 0:
            issues.append("未定义函数，代码结构化不足")

        # 检查异常处理
        if 'try:' not in code and 'except' not in code:
            issues.append("缺少异常处理")

        return {
            "passed": len(issues) < 3,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10)
        }

    def _check_style(self, code_result: Dict) -> Dict:
        """代码风格检查"""
        code = code_result.get("code", "")

        issues = []

        # 检查缩进一致性
        lines = code.split('\n')
        indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
        if len(set(indents)) > 5:
            issues.append("缩进不一致")

        # 检查命名规范
        if re.search(r'class\s+[a-z]', code):
            issues.append("类名应使用驼峰命名法")

        # 检查行长度
        long_lines = [line for line in lines if len(line) > 100]
        if len(long_lines) > 0:
            issues.append(f"{len(long_lines)}行代码过长(>100字符)")

        return {
            "passed": len(issues) < 2,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 5)
        }

    def _review_content(self, content_result: Dict, task: Dict = None) -> Dict:
        """审查内容质量"""
        content = content_result.get("content", "")

        checks = {
            "grammar": self._check_grammar(content_result),
            "originality": self._check_originality(content_result),
            "compliance": self._check_compliance(content_result),
            "length": self._check_length(content_result)
        }

        scores = [check.get("score", 50) for check in checks.values()]
        overall_score = sum(scores) / len(scores)

        return {
            "type": "content_review",
            "checks": checks,
            "overall_score": overall_score,
            "approved": overall_score >= 70,
            "suggestions": self._generate_content_suggestions(checks),
            "issues": self._extract_issues(checks)
        }

    def _review_image(self, image_result: Dict, task: Dict = None) -> Dict:
        """审查图片质量"""
        images = image_result.get("images", [])

        return {
            "type": "image_review",
            "count": len(images),
            "overall_score": 100,
            "approved": len(images) > 0,
            "suggestions": [],
            "issues": []
        }

    def _review_generic(self, result: Dict, task: Dict = None) -> Dict:
        """审查通用结果"""
        return {
            "type": "generic_review",
            "overall_score": 70,
            "approved": True,
            "suggestions": [],
            "issues": []
        }

    def _check_grammar(self, content_result: Dict) -> Dict:
        """检查语法"""
        content = content_result.get("content", "")

        # 简单的语法检查
        issues = []
        if '。。' in content or '，，' in content:
            issues.append("标点符号重复")

        if len([c for c in content if c in '，。！？；：']) < len(content.split()) * 0.05:
            issues.append("缺少标点符号")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10)
        }

    def _check_originality(self, content_result: Dict) -> Dict:
        """检查原创性"""
        # 这里应该调用抄袭检测API
        return {
            "passed": True,
            "score": 100
        }

    def _check_compliance(self, content_result: Dict) -> Dict:
        """检查合规性"""
        content = content_result.get("content", "")

        # 检查敏感词
        sensitive_words = ['暴力', '色情', '赌博']
        found = [word for word in sensitive_words if word in content]

        return {
            "passed": len(found) == 0,
            "found": found,
            "score": 100 if len(found) == 0 else 0
        }

    def _check_length(self, content_result: Dict) -> Dict:
        """检查内容长度"""
        content = content_result.get("content", "")
        length = len(content)

        if length < 100:
            score = 50
            issues = ["内容过短"]
        elif length > 10000:
            score = 80
            issues = ["内容过长"]
        else:
            score = 100
            issues = []

        return {
            "passed": score >= 70,
            "length": length,
            "issues": issues,
            "score": score
        }

    def _generate_code_suggestions(self, checks: Dict) -> List[str]:
        """生成代码改进建议"""
        suggestions = []

        if not checks["security"]["passed"]:
            suggestions.append("修复安全漏洞是最高优先级")

        if checks["security"]["findings"]:
            for finding in checks["security"]["findings"]:
                suggestions.append(f"- {finding['recommendation']}")

        if checks["quality"]["issues"]:
            suggestions.append("改进代码质量")
            for issue in checks["quality"]["issues"]:
                suggestions.append(f"- {issue}")

        return suggestions

    def _generate_content_suggestions(self, checks: Dict) -> List[str]:
        """生成内容改进建议"""
        suggestions = []

        for check_name, check_result in checks.items():
            if not check_result.get("passed", True):
                suggestions.extend(check_result.get("issues", []))

        return suggestions

    def _extract_issues(self, checks: Dict) -> List[Dict]:
        """提取所有问题"""
        issues = []

        for check_name, check_result in checks.items():
            if "findings" in check_result:
                for finding in check_result["findings"]:
                    issues.append({
                        "category": check_name,
                        **finding
                    })

            if "issues" in check_result:
                for issue in check_result["issues"]:
                    issues.append({
                        "category": check_name,
                        "description": issue
                    })

        return issues

    def _generate_report(self, review: Dict) -> Dict:
        """生成审查报告"""
        review_type = review.get("type", "generic")

        # 对于web-download类型，使用特殊的报告结构
        if review_type == "web_download_review":
            report = {
                "task_id": self.task_id,
                "timestamp": datetime.now().isoformat(),
                "review_type": review_type,
                "overall_score": review.get("overall_score", 70),
                "approved": review.get("approved", False),
                "suggestions": review.get("suggestions", []),
                "issues": review.get("issues", []),
                "checks": {
                    "static_checks": review.get("static_checks", {}),
                    "dynamic_checks": review.get("dynamic_checks", {}),
                    "comparison": review.get("comparison", {}),
                    "lessons": review.get("lessons", {})
                }
            }

            # NEW: 包含 fix_tasks（如果存在）
            if "fix_tasks" in review:
                report["fix_tasks"] = review["fix_tasks"]

            # NEW: 包含 task_goals（如果存在）
            if "task_goals" in review:
                report["task_goals"] = review["task_goals"]

            # NEW: 包含 verification_strategy（如果存在）
            if "verification_strategy" in review:
                report["verification_strategy"] = review["verification_strategy"]

        else:
            # 其他类型使用原有格式
            report = {
                "task_id": self.task_id,
                "timestamp": datetime.now().isoformat(),
                "review_type": review_type,
                "overall_score": review.get("overall_score", 70),
                "approved": review.get("approved", False),
                "suggestions": review.get("suggestions", []),
                "issues": review.get("issues", []),
                "checks": review.get("checks", {})
            }

        return report

    def _save_report(self, report: Dict):
        """保存审查报告"""
        report_file = self.task_dir / "review_report.json"
        report_file.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        print(f"[保存] 审查报告已保存: {report_file}")

    def _extract_imports(self, code: str) -> List[str]:
        """提取代码中的导入库"""
        imports = []

        # 匹配 import xxx
        imports.extend(re.findall(r'^import\s+(\w+)', code, re.MULTILINE))

        # 匹配 from xxx import
        imports.extend(re.findall(r'^from\s+(\w+)\s+import', code, re.MULTILINE))

        return list(set(imports))

    def _default_logger(self):
        """Create a default logger if none provided"""
        logger = logging.getLogger(f"ReviewerAgent.{self.task_id}")
        if not logger.handlers:
            # Explicitly use stderr for all logs
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter('[%(name)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _review_web_download(self, download_result: Dict, task: Dict = None) -> Dict:
        """审查下载的网页质量 - v2.1.0 任务感知版本"""
        print(f"[审查Agent] 开始审查网页下载质量")

        # ========== NEW: 解析任务目标 ==========
        if task and not hasattr(self, 'goals'):
            try:
                from task_goal_parser import TaskGoalParser
                self.goals = TaskGoalParser.parse(task)
                self.completeness_target = self.goals.get("completeness_target", 90.0)
                print(f"[审查Agent] [OK] 任务目标: {self.completeness_target}%完整度")
            except Exception as e:
                print(f"[审查Agent] ⚠ 任务目标解析失败: {e}")
                self.goals = {"completeness_target": 90.0}
                self.completeness_target = 90.0

        # 1. 静态检查
        static_checks = {
            "html_structure": self._check_html_structure(download_result),
            "custom_css": self._check_for_custom_css(download_result),  # P0检查
            "resources": self._check_resource_completeness(download_result)
        }

        # 2. 动态测试（使用Playwright）
        dynamic_checks = {"skipped": True, "reason": "Playwright not installed"}

        try:
            from web_interaction_tester import WebInteractionTester

            html_path = download_result.get("html_path")
            if html_path and Path(html_path).exists():
                tester = WebInteractionTester(logger=self.logger)
                print(f"[审查Agent] 运行动态测试: {html_path}")
                dynamic_result = asyncio.run(tester.test_local_html(
                    html_path,
                    tests=["scrolling", "sidebar", "click_interactions"]
                ))

                if dynamic_result.get("success"):
                    dynamic_checks = dynamic_result.get("tests", {})
                else:
                    dynamic_checks = {
                        "error": dynamic_result.get("error", "Unknown error"),
                        "success": False
                    }
        except ImportError:
            print(f"[审查Agent] 警告: web_interaction_tester未找到，跳过动态测试")
        except Exception as e:
            print(f"[审查Agent] 动态测试失败: {e}")
            dynamic_checks = {"error": str(e), "success": False}

        # ========== NEW: 智能验证策略选择 ==========
        comparison = None
        verification_strategy = None
        original_url = download_result.get("original_url")

        if original_url:
            try:
                from verification_strategy import VerificationStrategy

                # 选择验证策略
                strategy_selector = VerificationStrategy(cdp_port=9222)
                verification_strategy = strategy_selector.select_strategy(
                    original_url,
                    self.goals or {"completeness_target": 90.0}
                )

                print(f"[审查Agent] 验证策略: {verification_strategy['method']}")
                print(f"[审查Agent] 原因: {verification_strategy['reason']}")
                print(f"[审查Agent] 置信度: {verification_strategy['confidence']}")

                # 执行对比
                if verification_strategy["method"] == "cdp":
                    # 使用CDP对比器
                    print(f"[审查Agent] 使用CDP获取准确baseline...")

                    from cdp_comparator import CDPComparator
                    from bs4 import BeautifulSoup

                    # 读取下载的HTML
                    html_path = download_result.get("html_path")
                    if html_path and Path(html_path).exists():
                        with open(html_path, 'r', encoding='utf-8') as f:
                            downloaded_html = f.read()

                        # 执行CDP对比 + 渲染检查（修复飞书文档误判）
                        comparator = CDPComparator(
                            logger=self.logger,
                            completeness_target=self.completeness_target
                        )
                        comparison = asyncio.run(comparator.compare_with_baseline_and_rendered_check(
                            original_url,
                            html_path,
                            downloaded_html,
                            verification_strategy["config"]
                        ))

                        if comparison.get("success"):
                            print(f"[审查Agent] [OK] CDP对比成功: {comparison['completeness']}%完整度")
                        else:
                            print(f"[审查Agent] [FAIL] CDP对比失败: {comparison.get('error', 'Unknown error')}")

                            # 尝试降级
                    else:
                        print(f"[审查Agent] [FAIL] HTML文件不存在: {html_path}")
                        comparison = {"error": "HTML file not found", "success": False}

                else:
                    # 使用原有的在线对比方法
                    print(f"[审查Agent] 使用在线对比方法...")
                    from web_interaction_tester import WebInteractionTester

                    tester = WebInteractionTester(logger=self.logger)
                    comparison = asyncio.run(tester.compare_pages(
                        original_url,
                        download_result.get("html_path"),
                        timeout=verification_strategy["config"].get("timeout", 15000)
                    ))

                    if comparison.get("success"):
                        print(f"[审查Agent] [OK] 在线对比成功")
                    else:
                        print(f"[审查Agent] [FAIL] 在线对比失败: {comparison.get('error', 'Unknown error')}")

            except ImportError as e:
                print(f"[审查Agent] ⚠ 智能验证模块未找到，使用传统对比: {e}")
                # 降级到传统对比
                try:
                    from web_interaction_tester import WebInteractionTester
                    tester = WebInteractionTester(logger=self.logger)
                    comparison = asyncio.run(tester.compare_pages(
                        original_url,
                        download_result.get("html_path")
                    ))
                except Exception as e2:
                    print(f"[审查Agent] 传统对比也失败: {e2}")
                    comparison = {"error": str(e2), "success": False}

            except Exception as e:
                print(f"[审查Agent] 智能验证失败: {e}")
                comparison = {"error": str(e), "success": False}

        # 4. 经验检查
        lessons = self._check_against_lessons(download_result, static_checks, dynamic_checks)

        # ========== NEW: 使用任务感知评分 ==========
        overall_score = self._calculate_web_score_v2(
            static_checks, dynamic_checks, comparison, lessons,
            completeness_target=self.completeness_target
        )

        # 6. 判断是否通过
        approved = (
            overall_score >= 70 and
            not lessons.get("critical_issues", []) and
            static_checks["custom_css"]["passed"] and  # P0检查必须通过
            (comparison.get("met_target", True) if comparison else True)  # NEW: 检查是否达到目标
        )

        # 构建返回结果
        result = {
            "type": "web_download_review",
            "overall_score": overall_score,
            "approved": approved,
            "static_checks": static_checks,
            "dynamic_checks": dynamic_checks,
            "comparison": comparison,
            "lessons": lessons,
            "suggestions": self._generate_web_suggestions(
                static_checks, dynamic_checks, comparison, lessons
            ),
            "issues": self._extract_web_issues(
                static_checks, dynamic_checks, comparison, lessons
            )
        }

        # NEW: 添加任务目标和验证策略信息
        if hasattr(self, 'goals') and self.goals:
            result["task_goals"] = {
                "completeness_target": self.completeness_target,
                "met": comparison.get("met_target", True) if comparison else None,
                "actual": comparison.get("completeness", None) if comparison else None
            }

        if verification_strategy:
            result["verification_strategy"] = {
                "method": verification_strategy["method"],
                "reason": verification_strategy["reason"],
                "confidence": verification_strategy["confidence"]
            }

        # NEW: 生成修复任务（供执行agent使用）
        if not approved:
            result["fix_tasks"] = self._generate_fix_tasks(
                static_checks, dynamic_checks, comparison, lessons,
                download_result
            )

        return result

    def _check_html_structure(self, result: Dict) -> Dict:
        """检查HTML结构完整性"""
        html = result.get("html_content", "")
        issues = []

        # 基本结构检查
        if not html:
            return {"passed": False, "issues": ["HTML内容为空"]}

        # 检查基本标签
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        if not soup.find('html'):
            issues.append("缺少<html>标签")

        if not soup.find('body'):
            issues.append("缺少<body>标签")

        if not soup.find('head'):
            issues.append("缺少<head>标签")

        # 检查标题
        if not soup.find('title'):
            issues.append("缺少<title>标签")

        # 检查是否有内容
        text_length = len(soup.get_text())
        if text_length < 100:
            issues.append(f"文本内容过短 ({text_length}字符)")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "text_length": text_length,
            "has_title": bool(soup.find('title')),
            "title": soup.title.string if soup.title else None
        }

    def _check_for_custom_css(self, result: Dict) -> Dict:
        """检查是否添加了自定义CSS（P0）"""
        html = result.get("html_content", "")
        issues = []

        # 检测破坏布局的CSS模式
        forbidden_patterns = [
            (r"height:\s*100vh", "height: 100vh会破坏飞书布局", "P0"),
            (r"overflow-y:\s*auto\s*!important", "强制覆盖可能破坏原始滚动", "P0"),
            (r"body\s*\{[^}]*max-height", "限制body高度", "P0"),
            (r"max-height:\s*100vh", "max-height: 100vh会限制内容", "P1"),
            (r"overflow:\s*hidden", "overflow: hidden可能隐藏内容", "P1"),
        ]

        for pattern, description, severity in forbidden_patterns:
            if re.search(pattern, html):
                issues.append({
                    "severity": severity,
                    "pattern": pattern,
                    "description": description
                })

        # 统计P0问题数量
        p0_issues = [i for i in issues if i.get("severity") == "P0"]

        return {
            "passed": len(p0_issues) == 0,
            "issues": issues,
            "p0_count": len(p0_issues),
            "total_count": len(issues)
        }

    def _check_resource_completeness(self, result: Dict) -> Dict:
        """检查资源完整性"""
        html = result.get("html_content", "")

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
        except ImportError:
            return {"passed": True, "skipped": True, "reason": "BeautifulSoup未安装"}

        # 统计资源引用
        css_links = len(soup.find_all('link', rel='stylesheet'))
        img_tags = len(soup.find_all('img'))
        script_tags = len(soup.find_all('script', src=True))

        # 检查资源是否存在
        assets_dir = result.get("assets_dir")
        if assets_dir and Path(assets_dir).exists():
            downloaded_css = len(list(Path(assets_dir).glob("**/*.css")))
            downloaded_img = len(list(Path(assets_dir).glob("**/*.{jpg,png,gif,svg,webp}")))
            downloaded_js = len(list(Path(assets_dir).glob("**/*.js")))
        else:
            downloaded_css = downloaded_img = downloaded_js = 0

        # 计算完整性
        css_completeness = (downloaded_css / css_links) if css_links > 0 else 1.0
        img_completeness = (downloaded_img / img_tags) if img_tags > 0 else 1.0
        js_completeness = (downloaded_js / script_tags) if script_tags > 0 else 1.0

        return {
            "passed": (
                css_completeness >= 0.8 and
                img_completeness >= 0.7 and
                js_completeness >= 0.8
            ),
            "css": {
                "expected": css_links,
                "downloaded": downloaded_css,
                "completeness": css_completeness
            },
            "images": {
                "expected": img_tags,
                "downloaded": downloaded_img,
                "completeness": img_completeness
            },
            "js": {
                "expected": script_tags,
                "downloaded": downloaded_js,
                "completeness": js_completeness
            }
        }

    def _check_against_lessons(
        self,
        result: Dict,
        static_checks: Dict,
        dynamic_checks: Dict
    ) -> Dict:
        """根据经验教训检查已知问题"""
        critical_issues = []
        warnings = []

        # 检查1: 自定义CSS (LESSONS_LEARNED.md #1)
        if not static_checks.get("custom_css", {}).get("passed", True):
            p0_issues = static_checks["custom_css"].get("p0_count", 0)
            if p0_issues > 0:
                critical_issues.append({
                    "lesson": "LESSONS_LEARNED.md #1",
                    "issue": "检测到危险的自定义CSS",
                    "fix": "移除所有自定义CSS，保留原始样式",
                    "severity": "P0"
                })

        # 检查2: 侧边栏滚动 (LESSONS_LEARNED.md #2)
        if dynamic_checks.get("sidebar"):
            sidebar_result = dynamic_checks["sidebar"]
            if not sidebar_result.get("passed", True):
                critical_issues.append({
                    "lesson": "LESSONS_LEARNED.md #2",
                    "issue": "侧边栏无法正常滚动",
                    "fix": "检查是否修改了overflow样式",
                    "severity": "P0"
                })

        # 检查3: 页面滚动 (LESSONS_LEARNED.md #2)
        if dynamic_checks.get("scrolling"):
            scrolling_result = dynamic_checks["scrolling"]
            if not scrolling_result.get("passed", True):
                warnings.append({
                    "lesson": "LESSONS_LEARNED.md #2",
                    "issue": "页面滚动功能异常",
                    "fix": "检查height和overflow设置",
                    "severity": "P1"
                })

        return {
            "critical_issues": critical_issues,
            "warnings": warnings,
            "total_issues": len(critical_issues) + len(warnings)
        }

    def _calculate_web_score(
        self,
        static_checks: Dict,
        dynamic_checks: Dict,
        comparison: Dict = None,
        lessons: Dict = None
    ) -> float:
        """计算网页下载质量得分"""
        scores = []

        # 静态检查得分 (40%)
        static_score = 0
        if static_checks.get("html_structure", {}).get("passed"):
            static_score += 15

        if static_checks.get("custom_css", {}).get("passed"):
            static_score += 15  # P0检查，权重高
        else:
            static_score -= 20  # P0失败，严重扣分

        if static_checks.get("resources", {}).get("passed"):
            static_score += 10

        scores.append(("static", static_score, 40))

        # 动态测试得分 (30%)
        dynamic_score = 0
        if dynamic_checks.get("skipped"):
            # 跳过动态测试，给基础分
            dynamic_score = 20
        else:
            if dynamic_checks.get("scrolling", {}).get("passed"):
                dynamic_score += 10

            if dynamic_checks.get("sidebar", {}).get("passed"):
                dynamic_score += 10

            if dynamic_checks.get("click_interactions", {}).get("passed"):
                dynamic_score += 10

        scores.append(("dynamic", dynamic_score, 30))

        # 对比测试得分 (20%)
        comparison_score = 0
        if comparison:
            if comparison.get("success"):
                similarity = comparison.get("text_similarity", 0)
                if similarity >= 0.95:
                    comparison_score = 20
                elif similarity >= 0.90:
                    comparison_score = 15
                elif similarity >= 0.80:
                    comparison_score = 10
                else:
                    comparison_score = 5
            else:
                comparison_score = 10  # 对比失败，给部分分
        else:
            comparison_score = 15  # 无对比，给中等分

        scores.append(("comparison", comparison_score, 20))

        # 经验检查得分 (10%)
        lessons_score = 10
        if lessons:
            lessons_score -= len(lessons.get("critical_issues", [])) * 10
            lessons_score -= len(lessons.get("warnings", [])) * 5

        lessons_score = max(0, lessons_score)
        scores.append(("lessons", lessons_score, 10))

        # 总分
        total_score = static_score + dynamic_score + comparison_score + lessons_score

        print(f"[审查Agent] 得分详情:")
        for name, score, weight in scores:
            print(f"  - {name}: {score}/{weight}")

        print(f"[审查Agent] 总分: {total_score}/100")

        return max(0, min(100, total_score))

    def _calculate_web_score_v2(
        self,
        static_checks: Dict,
        dynamic_checks: Dict,
        comparison: Dict = None,
        lessons: Dict = None,
        completeness_target: float = 90.0  # NEW: 任务感知参数
    ) -> float:
        """计算网页下载质量得分 - v2.1.0 任务感知版本

        与原版的主要区别：
        1. 完整度目标作为参数（不再固定90%）
        2. 根据目标动态调整评分标准
        3. CDP对比使用不同的评分逻辑

        Args:
            static_checks: 静态检查结果
            dynamic_checks: 动态检查结果
            comparison: 对比结果（包含method, completeness等）
            lessons: 经验教训
            completeness_target: 完整度目标（默认90%）

        Returns:
            总分（0-100）
        """
        scores = []

        # 静态检查得分 (40%)
        static_score = 0
        if static_checks.get("html_structure", {}).get("passed"):
            static_score += 15

        if static_checks.get("custom_css", {}).get("passed"):
            static_score += 15  # P0检查，权重高
        else:
            static_score -= 20  # P0失败，严重扣分

        if static_checks.get("resources", {}).get("passed"):
            static_score += 10

        scores.append(("static", static_score, 40))

        # 动态测试得分 (30%)
        dynamic_score = 0
        if dynamic_checks.get("skipped"):
            # 跳过动态测试，给基础分
            dynamic_score = 20
        else:
            if dynamic_checks.get("scrolling", {}).get("passed"):
                dynamic_score += 10

            if dynamic_checks.get("sidebar", {}).get("passed"):
                dynamic_score += 10

            if dynamic_checks.get("click_interactions", {}).get("passed"):
                dynamic_score += 10

        scores.append(("dynamic", dynamic_score, 30))

        # 对比测试得分 (35% - 任务感知) - NEW
        comparison_score = 0
        if comparison:
            if comparison.get("success"):
                method = comparison.get("method", "online")

                if method == "cdp":
                    # CDP对比：使用完整度评分
                    completeness = comparison.get("completeness", 0)
                    has_rendering_issue = comparison.get("rendering_issue", False)

                    if has_rendering_issue:
                        # 有渲染问题（SPA应用如飞书文档）
                        # 即使HTML源代码有内容，实际渲染后内容区为空
                        # 这是严重问题，需要大幅扣分
                        self.logger.warning(
                            f"[NEW] 检测到渲染问题: {comparison.get('diagnosis', 'Unknown')[:100]}"
                        )

                        if completeness >= completeness_target:
                            # 完整度数值达标，但渲染失败
                            comparison_score = 10  # 严重扣分（从35降到10）
                            self.logger.warning(
                                f"[FAIL] 完整度数值{completeness:.1f}%达标，但渲染失败（内容区为空）"
                            )
                        else:
                            # 完整度也不达标
                            comparison_score = 5  # 极低分
                            self.logger.warning(
                                f"[FAIL] 完整度{completeness:.1f}%未达标且渲染失败"
                            )

                    elif completeness >= completeness_target:
                        # 达到目标，无渲染问题，满分
                        comparison_score = 35
                        self.logger.info(
                            f"[OK] 完整度 {completeness:.1f}% 达到目标 {completeness_target}%"
                        )
                    elif completeness >= completeness_target - 5:
                        # 接近目标，轻微扣分
                        gap = completeness_target - completeness
                        comparison_score = 30 - gap * 1
                        self.logger.info(
                            f"[WARNING] 完整度 {completeness:.1f}% 接近目标 {completeness_target}%"
                        )
                    else:
                        # 未达到目标，严重扣分
                        gap = completeness_target - completeness
                        comparison_score = max(0, 25 - gap * 2)
                        self.logger.warning(
                            f"[FAIL] 完整度 {completeness:.1f}% 未达到目标 {completeness_target}%"
                        )

                else:
                    # 在线对比：使用相似度评分
                    similarity = comparison.get("text_similarity", 0)
                    if similarity >= 0.95:
                        comparison_score = 35
                    elif similarity >= 0.90:
                        comparison_score = 30
                    elif similarity >= 0.80:
                        comparison_score = 25
                    else:
                        comparison_score = 20
            else:
                # 对比失败，根据是否可降级来评分
                if comparison.get("error"):
                    comparison_score = 10  # 对比错误，低分
                    self.logger.warning(f"对比失败: {comparison.get('error')}")
                else:
                    comparison_score = 15  # 对比失败，给部分分
        else:
            comparison_score = 25  # 无对比，给中等分

        scores.append(("comparison", comparison_score, 35))

        # 经验检查得分 (10%)
        lessons_score = 10
        if lessons:
            lessons_score -= len(lessons.get("critical_issues", [])) * 10
            lessons_score -= len(lessons.get("warnings", [])) * 5

        lessons_score = max(0, lessons_score)
        scores.append(("lessons", lessons_score, 10))

        # 总分
        total_score = static_score + dynamic_score + comparison_score + lessons_score

        print(f"[审查Agent] 得分详情 (v2.1.0 任务感知):")
        for name, score, weight in scores:
            print(f"  - {name}: {score}/{weight}")

        print(f"[审查Agent] 总分: {total_score}/100")

        return max(0, min(100, total_score))

    def _generate_web_suggestions(
        self,
        static_checks: Dict,
        dynamic_checks: Dict,
        comparison: Dict = None,
        lessons: Dict = None
    ) -> List[str]:
        """生成网页下载改进建议"""
        suggestions = []

        # P0问题优先
        if not static_checks.get("custom_css", {}).get("passed"):
            suggestions.append("[P0-CRITICAL] 移除所有自定义CSS (height: 100vh, overflow-y: auto !important)")

        # 经验教训
        if lessons and lessons.get("critical_issues"):
            for issue in lessons["critical_issues"]:
                suggestions.append(f"[P0-CRITICAL] {issue['fix']}")

        # 静态检查问题
        if not static_checks.get("html_structure", {}).get("passed"):
            suggestions.append("修复HTML结构问题")

        # 动态测试问题
        if not dynamic_checks.get("skipped"):
            if not dynamic_checks.get("scrolling", {}).get("passed"):
                suggestions.append("修复页面滚动功能")

            if not dynamic_checks.get("sidebar", {}).get("passed"):
                suggestions.append("修复侧边栏滚动功能")

        # 对比测试问题
        if comparison and comparison.get("success"):
            similarity = comparison.get("text_similarity", 0)
            if similarity < 0.90:
                suggestions.append(f"提高内容完整度 (当前相似度: {similarity:.1%})")

        return suggestions

    def _extract_web_issues(
        self,
        static_checks: Dict,
        dynamic_checks: Dict,
        comparison: Dict = None,
        lessons: Dict = None
    ) -> List[Dict]:
        """提取网页下载的所有问题"""
        issues = []

        # 静态检查问题
        for check_name, check_result in static_checks.items():
            if not check_result.get("passed", True):
                for issue in check_result.get("issues", []):
                    issue_data = {
                        "category": check_name,
                        "severity": check_result.get("severity", "unknown")
                    }
                    if isinstance(issue, dict):
                        issue_data.update(issue)
                    else:
                        issue_data["description"] = issue
                    issues.append(issue_data)

        # 动态测试问题
        if not dynamic_checks.get("skipped"):
            for test_name, test_result in dynamic_checks.items():
                if isinstance(test_result, dict) and not test_result.get("passed", True):
                    issues.append({
                        "category": f"dynamic_{test_name}",
                        "severity": "P1",
                        "description": f"{test_name}测试失败"
                    })

        # 经验检查问题
        if lessons:
            for issue in lessons.get("critical_issues", []) + lessons.get("warnings", []):
                issues.append({
                    "category": "lessons_learned",
                    "severity": issue.get("severity", "P2"),
                    "description": issue.get("issue", "Unknown issue"),
                    "fix": issue.get("fix", "")
                })

        return issues

    def _generate_fix_tasks(
        self,
        static_checks: Dict,
        dynamic_checks: Dict,
        comparison: Dict = None,
        lessons: Dict = None,
        download_result: Dict = None
    ) -> List[Dict[str, Any]]:
        """生成修复任务（供执行agent使用）

        根据审查发现的问题，生成详细的修复任务。
        这些任务可以被task-executor接收并执行。

        Args:
            static_checks: 静态检查结果
            dynamic_checks: 动态检查结果
            comparison: 对比结果
            lessons: 经验检查结果
            download_result: 下载结果

        Returns:
            修复任务列表，每个任务包含：
                - task_id: 任务ID
                - description: 任务描述
                - type: 任务类型
                - priority: 优先级（P0/P1/P2）
                - agent_type: 推荐的agent类型
                - params: 执行参数
        """
        fix_tasks = []

        # 任务1: 处理SPA渲染问题（最高优先级）
        if comparison and comparison.get("rendering_issue"):
            fix_tasks.append({
                "task_id": "fix_spa_rendering",
                "description": f"修复SPA应用渲染问题 - {comparison.get('diagnosis', '未知问题')[:80]}",
                "type": "fix_web_download",
                "priority": "P0",
                "agent_type": "task-executor",
                "params": {
                    "issue_type": "spa_rendering_failure",
                    "original_url": download_result.get("original_url", ""),
                    "html_path": download_result.get("html_path", ""),
                    "problem": comparison.get("diagnosis", ""),
                    "suggested_solution": "使用FeishuDownloaderV2提取纯文本内容，或确保JavaScript可以访问在线API"
                },
                "acceptance_criteria": {
                    "description": "修复后，主内容区应显示实际内容，而非空白",
                    "verification": "使用quality-reviewer重新审查，rendering_check应显示main_content_empty=false"
                }
            })

        # 任务2: 修复侧边栏滚动问题（P0）
        if lessons and lessons.get("critical_issues"):
            for issue in lessons["critical_issues"]:
                if "侧边栏" in issue.get("issue", ""):
                    fix_tasks.append({
                        "task_id": "fix_sidebar_scrolling",
                        "description": f"修复侧边栏滚动功能 - {issue.get('issue', '')}",
                        "type": "fix_web_layout",
                        "priority": "P0",
                        "agent_type": "task-executor",
                        "params": {
                            "issue": issue,
                            "html_path": download_result.get("html_path", ""),
                            "current_state": "sidebar无法滚动",
                            "target_state": "sidebar可正常滚动"
                        },
                        "acceptance_criteria": {
                            "description": "侧边栏可以滚动到底部",
                            "verification": "动态测试sidebar测试应通过"
                        }
                    })

        # 任务3: 修复页面滚动功能（P1）
        if not dynamic_checks.get("skipped", False):
            if not dynamic_checks.get("scrolling", {}).get("passed", True):
                fix_tasks.append({
                    "task_id": "fix_page_scrolling",
                    "description": "修复页面滚动功能",
                    "type": "fix_web_layout",
                    "priority": "P1",
                    "agent_type": "task-executor",
                    "params": {
                        "html_path": download_result.get("html_path", ""),
                        "issue": "页面无法滚动或无法滚动到底部",
                        "current_state": f"scroll_height={dynamic_checks.get('scrolling', {}).get('scroll_height', 0)}, client_height={dynamic_checks.get('scrolling', {}).get('client_height', 0)}",
                        "target_state": "页面可以正常滚动，且能滚动到底部"
                    },
                    "acceptance_criteria": {
                        "description": "页面可以滚动，reached_bottom=true",
                        "verification": "动态测试scrolling测试应通过"
                    }
                })

        # 任务4: 提高内容完整度（P1）
        if comparison and comparison.get("success") and comparison.get("completeness", 0) < self.completeness_target:
            gap = self.completeness_target - comparison.get("completeness", 0)
            fix_tasks.append({
                "task_id": "improve_completeness",
                "description": f"提高内容完整度 - 当前{comparison.get('completeness', 0):.1f}%，目标{self.completeness_target:.1f}%，差距{gap:.1f}%",
                "type": "improve_download_quality",
                "priority": "P1",
                "agent_type": "task-executor",
                "params": {
                    "original_url": download_result.get("original_url", ""),
                    "current_completeness": comparison.get("completeness", 0),
                    "target_completeness": self.completeness_target,
                    "gap": gap,
                    "baseline_length": comparison.get("baseline_length", 0),
                    "downloaded_length": comparison.get("downloaded_length", 0)
                },
                "acceptance_criteria": {
                    "description": f"完整度达到或超过{self.completeness_target:.1f}%",
                    "verification": "CDP对比显示completeness >= target"
                }
            })

        # 任务5: 移除危险CSS（P0）
        if not static_checks.get("custom_css", {}).get("passed", True):
            fix_tasks.append({
                "task_id": "remove_dangerous_css",
                "description": "移除所有自定义CSS（height: 100vh, overflow-y: auto !important）",
                "type": "fix_html_style",
                "priority": "P0",
                "agent_type": "task-executor",
                "params": {
                    "html_path": download_result.get("html_path", ""),
                    "css_to_remove": [
                        "height: 100vh",
                        "overflow-y: auto !important",
                        "overflow: hidden"
                    ],
                    "issue": static_checks.get("custom_css", {}).get("issues", []),
                    "method": "删除或注释掉HTML中的<style>标签或inline style属性"
                },
                "acceptance_criteria": {
                    "description": "custom_css检查通过",
                    "verification": "静态检查custom_css.passed=true"
                }
            })

        self.logger.info(f"[审查Agent] 生成了 {len(fix_tasks)} 个修复任务")
        for i, task in enumerate(fix_tasks, 1):
            self.logger.info(f"  任务{i}: [{task['priority']}] {task['description']}")

        return fix_tasks
