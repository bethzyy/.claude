"""
FixExecutor — 批量修复执行器

职责：
1. Git checkpoint（每批次前 commit）
2. 调用 LLM 生成修复代码
3. AST 语法验证
4. 写入文件
5. 失败时 rollback
"""

import ast
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """批次执行结果"""
    success: bool
    modified_files: list[str] = field(default_factory=list)
    failed_files: list[str] = field(default_factory=list)
    checkpoint_sha: str = ""
    error: Optional[str] = None


class FixExecutor:
    """批量修复执行器"""

    def __init__(self, llm: LLMClient, project_dir: str):
        self.llm = llm
        self.project_dir = Path(project_dir)
        self.checkpoint_shas: list[str] = []
        self.all_modified_files: list[str] = []

    def execute_batch(self, batch) -> BatchResult:
        """
        执行一个批次的修复。

        流程：
        1. Git checkpoint
        2. 对 batch 中每个文件：
           a. 读取当前文件内容
           b. 构造 prompt（findings + 文件内容）
           c. 调用 LLM 生成修复后内容
           d. AST 语法验证
           e. 写入文件
        3. 返回 BatchResult
        """
        # Step 1: Checkpoint
        checkpoint_sha = self._checkpoint(f"auto-fix: checkpoint before batch {batch.id}")
        if not checkpoint_sha:
            return BatchResult(
                success=False,
                checkpoint_sha="",
                error="无法创建 git checkpoint，跳过此批次",
            )

        result = BatchResult(
            success=True,
            checkpoint_sha=checkpoint_sha,
        )

        # Step 2: 逐文件修复
        for file_path in batch.files:
            try:
                modified = self._fix_file(file_path, batch.findings)
                if modified:
                    result.modified_files.append(file_path)
                    self.all_modified_files.append(file_path)
                else:
                    result.failed_files.append(file_path)
            except Exception as e:
                logger.error(f"修复 {file_path} 失败: {e}")
                result.failed_files.append(file_path)

        # 如果全部失败，标记为失败
        if not result.modified_files and result.failed_files:
            result.success = False
            result.error = f"所有文件修复失败: {result.failed_files}"

        return result

    def _fix_file(self, file_path: str, findings: list[dict]) -> bool:
        """
        修复单个文件。

        Returns:
            True if file was successfully modified
        """
        full_path = self.project_dir / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return False

        # 读取当前内容
        try:
            original_content = full_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return False

        if not original_content.strip():
            logger.warning(f"文件为空: {file_path}")
            return False

        # 确定语言
        language = self._detect_language(file_path)

        # 调用 LLM 生成修复
        fixed_content = self.llm.fix_code(
            file_content=original_content,
            file_path=file_path,
            language=language,
            findings=findings,
        )

        if not fixed_content:
            logger.warning(f"LLM 未返回有效内容: {file_path}")
            return False

        # 检查是否有实际变化
        if fixed_content.strip() == original_content.strip():
            logger.info(f"文件无变化，跳过: {file_path}")
            return False

        # AST 语法验证（仅 Python）
        if language == "python":
            try:
                ast.parse(fixed_content)
            except SyntaxError as e:
                logger.error(f"AST 验证失败 {file_path}: {e}")
                return False

        # 写入文件
        try:
            full_path.write_text(fixed_content, encoding="utf-8")
            logger.info(f"修复成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"写入文件失败 {file_path}: {e}")
            return False

    def _checkpoint(self, message: str) -> Optional[str]:
        """创建 git checkpoint，返回 commit SHA"""
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(self.project_dir),
                capture_output=True,
                timeout=30,
            )
            result = subprocess.run(
                ["git", "commit", "-m", message, "--allow-empty"],
                cwd=str(self.project_dir),
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                # 可能没有变更，获取当前 HEAD
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(self.project_dir),
                    capture_output=True,
                    timeout=10,
                )
                if sha_result.returncode == 0:
                    sha = sha_result.stdout.decode().strip()[:12]
                    self.checkpoint_shas.append(sha)
                    return sha
                return None

            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.project_dir),
                capture_output=True,
                timeout=10,
            )
            if sha_result.returncode == 0:
                sha = sha_result.stdout.decode().strip()[:12]
                self.checkpoint_shas.append(sha)
                return sha
            return None
        except Exception as e:
            logger.error(f"Git checkpoint 失败: {e}")
            return None

    def rollback(self, sha: str) -> bool:
        """回滚到指定 checkpoint"""
        try:
            # 使用 git reset --soft 保留工作区变更便于审查
            result = subprocess.run(
                ["git", "reset", "--soft", sha],
                cwd=str(self.project_dir),
                capture_output=True,
                timeout=30,
            )
            # 同时用 git checkout 恢复文件
            subprocess.run(
                ["git", "checkout", "--", "."],
                cwd=str(self.project_dir),
                capture_output=True,
                timeout=30,
            )
            success = result.returncode == 0
            if success:
                logger.info(f"已回滚到 {sha}")
            else:
                logger.error(f"回滚失败: {result.stderr.decode()}")
            return success
        except Exception as e:
            logger.error(f"Rollback 异常: {e}")
            return False

    @staticmethod
    def _detect_language(file_path: str) -> str:
        """根据文件扩展名检测语言"""
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".vue": "vue",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
        }
        return lang_map.get(ext, "text")
