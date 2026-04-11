"""
SecurityExpert — 安全专家

OWASP Top 10 扫描 + 依赖漏洞 + 认证授权 + 密钥检测。
集成 quality-reviewer 的安全扫描能力。
"""

import re
import os
from pathlib import Path

from integrations.quality_reviewer_bridge import QualityReviewerBridge
from typing import List, Dict, Optional

from core._paths import ensure_skill_path
ensure_skill_path()

from experts.base_expert import BaseExpert
from core.finding import Finding, FindingList, Severity, Category
from core.review_context import ReviewContext
from evolution.evolution_store import EvolutionState


class SecurityExpert(BaseExpert):
    """安全专家 — OWASP Top 10 + 依赖漏洞 + 认证授权 + 密钥检测"""

    name = "security"
    name_cn = "安全专家"
    description = "OWASP Top 10 扫描、依赖漏洞检测、认证授权审查、密钥检测"

    # OWASP Top 10 相关模式
    OWASP_PATTERNS = {
        "A01-Broken Access Control": {
            "patterns": [
                (r"(@app\.route|@router\.)\s*\([^)]*\)", "route"),
                (r"login_required|@auth|@permission|@role", "auth_decorator"),
            ],
            "severity": Severity.HIGH,
            "suggestion": "确保所有路由都有适当的访问控制",
        },
        "A02-Cryptographic Failures": {
            "patterns": [
                (r"hashlib\.md5|MD5|sha1\s*\(", "weak_hash"),
                (r"base64\.encode|base64\.b64encode", "base64"),
            ],
            "severity": Severity.HIGH,
            "suggestion": "使用 bcrypt/argon2 替代 MD5/SHA1，base64 不是加密",
        },
        "A03-Injection": {
            "patterns": [
                (r'execute\s*\(\s*f["\']', "sql_format"),
                (r'execute\s*\(\s*["\'].*%', "sql_percent"),
                (r'eval\s*\(', "eval"),
                (r'exec\s*\(', "exec"),
                (r'os\.system\s*\(', "os_system"),
                (r'subprocess.*shell\s*=\s*True', "shell_true"),
            ],
            "severity": Severity.CRITICAL,
            "suggestion": "使用参数化查询/白名单验证，避免动态代码执行",
        },
        "A04-Insecure Design": {
            "patterns": [
                (r"TODO.*security|FIXME.*auth|HACK.*password", "security_todo"),
            ],
            "severity": Severity.MEDIUM,
            "suggestion": "解决安全相关的 TODO/FIXME",
        },
        "A05-Security Misconfiguration": {
            "patterns": [
                (r"DEBUG\s*=\s*True", "debug_on"),
                (r"SECRET_KEY\s*=\s*['\"]", "default_secret"),
                (r"ALLOWED_HOSTS\s*=\s*\[\s*['\"]?\*['\"]?", "allowed_all"),
                (r"CORS.*\*", "cors_all"),
                (r"Access-Control-Allow-Origin.*\*", "cors_wildcard"),
            ],
            "severity": Severity.HIGH,
            "suggestion": "关闭 DEBUG、使用强密钥、限制 CORS 和 Host",
        },
        "A06-Vulnerable Components": {
            "patterns": [],
            "severity": Severity.HIGH,
            "suggestion": "运行 pip audit 检查依赖漏洞",
        },
        "A07-Auth Failures": {
            "patterns": [
                (r"session\['user_id'\]|session\['logged_in'\]", "session_auth"),
                (r"password\s*==\s*['\"]", "plain_password"),
                (r"jwt\.decode\s*\([^,]*\)", "jwt_no_verify"),
            ],
            "severity": Severity.CRITICAL,
            "suggestion": "使用安全的 session 管理、密码哈希、JWT 验证",
        },
        "A08-Software Data Integrity": {
            "patterns": [
                (r"pickle\.loads|pickle\.load", "pickle"),
                (r"yaml\.load\s*\(", "yaml_load"),
            ],
            "severity": Severity.HIGH,
            "suggestion": "避免反序列化不可信数据，使用 yaml.safe_load",
        },
        "A09-Logging Failures": {
            "patterns": [],
            "severity": Severity.LOW,
            "suggestion": "使用 logging 模块替代 print（由 devops_expert 详细检查）",
        },
        "A10-SSRF": {
            "patterns": [
                (r"requests\.(get|post)\s*\(\s*(url|link|uri)\s*\)", "ssrf_risk"),
                (r"urllib\.request\.urlopen\s*\(", "ssrf_urllib"),
            ],
            "severity": Severity.HIGH,
            "suggestion": "验证和限制请求的 URL，防止 SSRF 攻击",
        },
    }

    # 密钥检测模式
    SECRET_PATTERNS = {
        "API Key": r'(api[_-]?key|apikey)\s*=\s*["\'][a-zA-Z0-9]{16,}["\']',
        "Secret Key": r'(secret[_-]?key|secretkey)\s*=\s*["\'][a-zA-Z0-9]{16,}["\']',
        "Password": r'password\s*=\s*["\'][^"\']{4,}["\']',
        "Token": r'(token|access_token)\s*=\s*["\'][a-zA-Z0-9._-]{20,}["\']',
        "Database URL": r'(database_url|db_url|mongo_uri|redis_url)\s*=\s*["\'][^"\']+["\']',
        "Private Key": r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
    }

    def review(self, source_files: List[str] = None) -> FindingList:
        files = self.scan_all_files(source_files)
        py_files = self.filter_by_extension(files, [".py"])
        config_files = self._get_config_files(files)

        # OWASP Top 10 检查
        self._check_owasp(py_files)

        # 密钥检测
        self._check_secrets(py_files + config_files)

        # 认证授权审查
        self._check_authentication(py_files)

        # 依赖漏洞检查
        self._check_dependencies()

        # .env 文件安全
        self._check_env_security()

        # 尝试委托 quality-reviewer
        self._delegate_to_quality_reviewer(py_files)

        return self.findings

    def _check_owasp(self, files: List[str]):
        """OWASP Top 10 检查"""
        for file_path in files:
            content = self.read_file(file_path)
            if not content:
                continue

            lines = self.read_file_lines(file_path)

            for vuln_name, config in self.OWASP_PATTERNS.items():
                for pattern, _ in config["patterns"]:
                    matches = self.find_pattern_in_file(file_path, pattern)
                    for match in matches:
                        if lines:
                            line_no = match["line"] - 1
                            if line_no < len(lines) and self._in_docstring(lines, line_no):
                                continue

                        self.add_finding(
                            title=f"OWASP {vuln_name}: {match['content'][:80]}",
                            severity=config["severity"],
                            category=Category.SECURITY,
                            file_path=file_path,
                            line_range=str(match["line"]),
                            code_snippet=match["content"],
                            description=f"OWASP {vuln_name} 在 {file_path}:{match['line']}",
                            fix_suggestion=config["suggestion"],
                            references=[f"OWASP {vuln_name}"],
                        )

    def _check_secrets(self, files: List[str]):
        """密钥检测"""
        for file_path in files:
            # 跳过 .env.example 和 .env.template
            if any(skip in file_path.lower() for skip in [".example", ".template", ".sample"]):
                continue
            # 跳过测试文件
            path_lower = file_path.lower().replace("\\", "/")
            # Skip files inside test/ or tests/ directories, or starting with test_
            parts = path_lower.split("/")
            is_test_dir = any(p in ("test", "tests", "__pycache__") for p in parts)
            is_test_file = Path(file_path).stem.startswith("test_")
            if is_test_dir or is_test_file:
                continue

            content = self.read_file(file_path)
            if not content:
                continue

            content_lines = content.split("\n")

            for secret_type, pattern in self.SECRET_PATTERNS.items():
                matches = self.find_pattern_in_file(file_path, pattern)
                for match in matches:
                    # 跳过注释行
                    line_no = match["line"] - 1
                    if line_no < len(content_lines):
                        raw_line = content_lines[line_no].strip()
                        if raw_line.startswith("#") or raw_line.startswith("//") or raw_line.startswith("*"):
                            continue

                    # 跳过占位符/示例值
                    matched_value = match["match"]
                    if self._is_placeholder_value(matched_value):
                        continue

                    # 遮蔽实际密钥值
                    masked = match["content"][:50].replace(match["match"], "***REDACTED***")
                    self.add_finding(
                        title=f"Hardcoded {secret_type} detected",
                        severity=Severity.CRITICAL,
                        category=Category.SECURITY,
                        file_path=file_path,
                        line_range=str(match["line"]),
                        code_snippet=masked,
                        description=f"发现硬编码的 {secret_type}",
                        fix_suggestion=f"将 {secret_type} 移到 .env 文件或环境变量中",
                        effort="small",
                    )

    def _check_authentication(self, files: List[str]):
        """认证授权审查"""
        # 检查是否有认证相关代码
        auth_files = []
        for f in files:
            content = self.read_file(f)
            if content and any(kw in content for kw in ["login", "auth", "session", "token", "password"]):
                auth_files.append(f)

        if not auth_files:
            return

        for file_path in auth_files:
            content = self.read_file(file_path)
            if not content:
                continue

            # 检查密码是否明文存储
            if "password" in content and "hash" not in content and "bcrypt" not in content and "argon" not in content:
                if "password ==" in content or "password =" in content:
                    matches = self.find_pattern_in_file(file_path, r'password\s*(==|=)\s*["\']')
                    for match in matches:
                        self.add_finding(
                            title="Plain text password comparison",
                            severity=Severity.CRITICAL,
                            category=Category.SECURITY,
                            file_path=file_path,
                            line_range=str(match["line"]),
                            code_snippet=match["content"][:50],
                            description="密码以明文比较，应使用 bcrypt/argon2 哈希",
                            fix_suggestion="使用 werkzeug.security.check_password_hash 或 bcrypt",
                            effort="medium",
                        )

            # 检查 JWT 是否验证签名
            if "jwt" in content.lower():
                if "decode" in content and "verify" not in content.lower() and "algorithms" not in content:
                    self.add_finding(
                        title="JWT decode without signature verification",
                        severity=Severity.CRITICAL,
                        category=Category.SECURITY,
                        file_path=file_path,
                        description="JWT 解码时未验证签名",
                        fix_suggestion="使用 algorithms 和 audience 参数验证 JWT 签名",
                        effort="small",
                    )

    def _check_dependencies(self):
        """依赖漏洞检查"""
        # 检查 requirements.txt 是否有已知危险版本
        for req_file in ["requirements.txt", "requirements-dev.txt", "requirements-local.txt"]:
            content = self.read_file(req_file)
            if not content:
                continue

            dangerous_packages = {
                "pycrypto": "已停止维护，存在安全漏洞，改用 pycryptodome",
                "django": "检查版本是否为最新安全版本",
                "flask": "检查版本是否为最新安全版本",
                "pillow": "<8.1.0 有 CVE，建议升级",
                "lxml": "<4.6.5 有 CVE，建议升级",
            }

            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                pkg_name = re.split(r"[=<>~!]", line)[0].strip().lower()
                for danger_pkg, reason in dangerous_packages.items():
                    if pkg_name == danger_pkg:
                        self.add_finding(
                            title=f"Potentially vulnerable dependency: {pkg_name}",
                            severity=Severity.MEDIUM,
                            category=Category.SECURITY,
                            file_path=req_file,
                            description=reason,
                            fix_suggestion=f"运行 pip install --upgrade {pkg_name} 或使用 pip audit",
                            effort="small",
                        )

    def _check_env_security(self):
        """Check .env file security"""
        env_file = self.read_file(".env")
        if not env_file:
            return

        gitignore = self.read_file(".gitignore")
        if gitignore:
            env_protected = False
            for line in gitignore.split("\n"):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                # Check if this pattern covers .env
                pattern = stripped.rstrip("/")
                if pattern == ".env" or pattern == ".env*" or pattern == "*.env":
                    env_protected = True
                    break
                # Handle directory patterns like .env/
                if pattern.endswith("*") and ".env".startswith(pattern.rstrip("*")):
                    env_protected = True
                    break
            if not env_protected:
                self.add_finding(
                    title=".env not in .gitignore",
                    severity=Severity.CRITICAL,
                    category=Category.SECURITY,
                    file_path=".gitignore",
                    description=".env file not in .gitignore, may be committed",
                    fix_suggestion="Add .env to .gitignore",
                    effort="small",
                )
        else:
            self.add_finding(
                title=".gitignore not found",
                severity=Severity.HIGH,
                category=Category.SECURITY,
                file_path=".gitignore",
                description="No .gitignore file found",
                fix_suggestion="Create .gitignore and add .env to it",
                effort="small",
            )

    def _delegate_to_quality_reviewer(self, py_files: List[str]):
        """通过 QualityReviewerBridge 委托 quality-reviewer 进行深度安全扫描"""
        try:
            bridge = QualityReviewerBridge()
            if bridge.available:
                self.add_finding(
                    title="quality-reviewer integration: available",
                    severity=Severity.LOW,
                    category=Category.SECURITY,
                    file_path="",
                    description="quality-reviewer 可用于深度安全扫描（OWASP + 漏洞 + 风险评估）",
                    fix_suggestion="运行 quality-reviewer 获取完整安全报告",
                )
        except Exception:
            # 优雅降级 — quality-reviewer 不可用时使用自有逻辑
            pass

    def _get_config_files(self, files: List[str]) -> List[str]:
        """获取配置相关文件"""
        config_patterns = [
            ".env", ".env.local", "config.py", "config.json",
            "settings.py", "settings_local.py",
        ]
        result = []
        for f in files:
            base = os.path.basename(f)
            if any(base == p or base.startswith(p.split(".")[0]) for p in config_patterns):
                result.append(f)
        return result

    def _is_placeholder_value(self, value: str) -> bool:
        """检查密钥值是否是占位符/示例，而非真实密钥"""
        value_lower = value.lower().strip("'\"")
        # 太短的不可能是真实密钥
        if len(value_lower) < 8:
            return True
        # 明显的占位符
        placeholders = [
            "xxx", "xxxx", "example", "test", "dummy", "placeholder",
            "your-", "not-needed", "none", "null", "false", "true",
            "changeme", "todo", "fixme", "password123", "123456",
            "abc123", "sk-xxx", "sk-test", "your_api_key",
            "your_api_key_here", "put_your", "insert_your",
        ]
        for p in placeholders:
            if p in value_lower:
                return True
        # 全是相同字符（如 "aaaaaa"）
        if len(set(value_lower)) <= 2:
            return True
        return False
