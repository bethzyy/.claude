"""
QualityReviewerBridge — 桥接 quality-reviewer skill

复用 quality-reviewer 的 OWASP Top 10 扫描和漏洞检测能力。
基于审查 quality-reviewer/reviewer.py 的真实 API 设计。

安全机制（三层信任模型）:
1. 白名单: reviewer.py 路径必须在 SKILL_DIR/../quality-reviewer/ 下
2. 哈希校验: 首次加载记录 SHA256，后续比对；不匹配则拒绝
3. 模式审计: 验证模块包含预期的 ReviewerAgent 类和方法签名

ReviewerAgent 真实签名:
  __init__(self, task_id: str, task_dir: Path, task: Dict = None, logger=None)
  _check_security(self, code_result: Dict) -> Dict    # 输入: {"type": "code", "code": "..."}
  _check_vulnerabilities(self, code_result: Dict) -> Dict
  _assess_risks(self, code_result: Dict) -> Dict
  返回: {"passed": bool, "findings": List[Dict], "score": int}
"""

import hashlib
import json
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Optional, List

from core._paths import SKILL_DIR, DATA_DIR, ensure_skill_path
ensure_skill_path()

# 预期的方法签名（用于模式审计）
_EXPECTED_METHODS = {"_check_security", "_check_vulnerabilities", "_assess_risks"}


class QualityReviewerBridge:
    """桥接 quality-reviewer 的安全扫描能力（三层信任模型）"""

    def __init__(self):
        self._reviewer_class = None
        self._available = False
        self._error = None
        self._init_bridge()

    def _get_hash_file(self) -> Path:
        return DATA_DIR / "trusted_hashes.json"

    def _load_hashes(self) -> Dict:
        hash_file = self._get_hash_file()
        if hash_file.exists():
            try:
                return json.loads(hash_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_hashes(self, hashes: Dict):
        hash_file = self._get_hash_file()
        hash_file.parent.mkdir(parents=True, exist_ok=True)
        hash_file.write_text(
            json.dumps(hashes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _compute_hash(self, file_path: Path) -> str:
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def _init_bridge(self):
        """尝试初始化 quality-reviewer 桥接（三层信任校验）"""
        try:
            # === 第 1 层: 白名单路径检查 ===
            reviewer_path = (
                SKILL_DIR.parent
                / "quality-reviewer"
                / "reviewer.py"
            )
            expected_parent = SKILL_DIR.parent / "quality-reviewer"
            if not reviewer_path.exists():
                self._error = f"reviewer.py not found at {reviewer_path}"
                return

            # 验证路径解析后仍在预期目录下（防 symlink 攻击）
            resolved = reviewer_path.resolve()
            if not str(resolved).startswith(str(expected_parent.resolve())):
                self._error = f"Path trust violation: {resolved} not under {expected_parent}"
                return

            # === 第 2 层: 哈希校验 ===
            hashes = self._load_hashes()
            hash_key = "quality-reviewer/reviewer.py"
            current_hash = self._compute_hash(resolved)

            if hash_key in hashes:
                if hashes[hash_key] != current_hash:
                    self._error = (
                        f"Hash mismatch for {hash_key}: "
                        f"expected {hashes[hash_key][:16]}..., "
                        f"got {current_hash[:16]}... — "
                        f"reviewer.py may have been tampered with. "
                        f"Delete {self._get_hash_file()} to re-trust."
                    )
                    return
            # 首次加载: 哈希不存在 → 信任并记录（在成功加载后保存）

            # === 第 3 层: 模块加载 + 模式审计 ===
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "quality_reviewer_module", str(resolved)
            )
            if not spec or not spec.loader:
                self._error = f"Failed to create module spec for {resolved}"
                return

            mod = importlib.util.module_from_spec(spec)
            # 让 quality-reviewer 的内部导入也能工作
            qr_dir = str(resolved.parent)
            if qr_dir not in sys.path:
                sys.path.insert(0, qr_dir)
            spec.loader.exec_module(mod)

            # 模式审计: 验证 ReviewerAgent 类存在且包含预期方法
            if not hasattr(mod, "ReviewerAgent"):
                self._error = "ReviewerAgent class not found in reviewer.py"
                return

            missing_methods = _EXPECTED_METHODS - set(
                name for name in dir(mod.ReviewerAgent) if not name.startswith("__")
            )
            if missing_methods:
                self._error = (
                    f"ReviewerAgent missing expected methods: {missing_methods}"
                )
                return

            # 三层校验全部通过
            self._reviewer_class = mod.ReviewerAgent
            self._available = True

            # 记录哈希（首次或更新）
            hashes[hash_key] = current_hash
            self._save_hashes(hashes)

        except Exception as e:
            self._error = f"Import failed: {str(e)}"
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_error(self) -> Optional[str]:
        return self._error

    def _create_reviewer(self, task_id: str) -> Optional[object]:
        """创建 ReviewerAgent 实例，需要 task_dir 存在"""
        try:
            # 使用临时目录作为 task_dir
            task_dir = Path(tempfile.mkdtemp(prefix="expert_review_qr_"))
            reviewer = self._reviewer_class(
                task_id=task_id,
                task_dir=task_dir,
            )
            return reviewer
        except Exception as e:
            self._error = f"Failed to create ReviewerAgent: {str(e)}"
            return None

    def check_security(self, code: str, file_path: str = "") -> Optional[Dict]:
        """
        委托 OWASP Top 10 安全扫描。

        真实 API: reviewer._check_security({"type": "code", "code": "..."})
        返回: {"passed": bool, "findings": [...], "score": int}
        """
        if not self._available:
            return None

        try:
            reviewer = self._create_reviewer(f"sec_{file_path or 'scan'}")
            if not reviewer:
                return None

            code_result = {"type": "code", "code": code}
            if file_path:
                code_result["file_path"] = file_path

            result = reviewer._check_security(code_result)
            return result
        except Exception as e:
            self._error = f"_check_security failed: {str(e)}"
            return None

    def check_vulnerabilities(self, code: str, file_path: str = "") -> Optional[Dict]:
        """
        委托依赖漏洞检测。

        检查: PIL<9.0.0, requests<2.20.0, flask<1.0, django<2.2.24 等
        """
        if not self._available:
            return None

        try:
            reviewer = self._create_reviewer(f"vuln_{file_path or 'scan'}")
            if not reviewer:
                return None

            code_result = {"type": "code", "code": code}
            if file_path:
                code_result["file_path"] = file_path

            result = reviewer._check_vulnerabilities(code_result)
            return result
        except Exception as e:
            self._error = f"_check_vulnerabilities failed: {str(e)}"
            return None

    def assess_risks(self, code: str, file_path: str = "") -> Optional[Dict]:
        """
        委托风险评估。

        检查: 数据丢失(DROP/DELETE)、SSRF、文件操作、并发、资源泄漏
        """
        if not self._available:
            return None

        try:
            reviewer = self._create_reviewer(f"risk_{file_path or 'scan'}")
            if not reviewer:
                return None

            code_result = {"type": "code", "code": code}
            if file_path:
                code_result["file_path"] = file_path

            result = reviewer._assess_risks(code_result)
            return result
        except Exception as e:
            self._error = f"_assess_risks failed: {str(e)}"
            return None

    def scan_file(self, file_path: str) -> Dict:
        """
        对单个文件执行完整扫描（安全+漏洞+风险）。

        Returns:
            {
                "available": bool,
                "security": {...} | None,
                "vulnerabilities": {...} | None,
                "risks": {...} | None,
                "error": str | None,
            }
        """
        result = {"available": self._available, "error": self._error}

        if not self._available:
            return result

        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception as e:
            result["error"] = f"Failed to read {file_path}: {str(e)}"
            return result

        # 依次执行三种扫描
        result["security"] = self.check_security(code, file_path)
        result["vulnerabilities"] = self.check_vulnerabilities(code, file_path)
        result["risks"] = self.assess_risks(code, file_path)

        return result
