#!/usr/bin/env python3
"""
审查Agent - 负责质量检查和安全审查
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ReviewerAgent:
    """审查Agent - 负责质量检查和安全扫描"""

    def __init__(self, task_id: str, task_dir: Path):
        self.task_id = task_id
        self.task_dir = task_dir
        self.task_dir.mkdir(parents=True, exist_ok=True)

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
        report = {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat(),
            "review_type": review.get("type", "generic"),
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
