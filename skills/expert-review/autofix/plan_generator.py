"""
PlanGenerator — Finding → 结构化改进方案

职责：
1. 过滤可操作的发现（有 fix_suggestion）
2. 按文件分组 + severity 排序
3. 分析 import 依赖关系，拓扑排序
4. 可选 LLM 增强批次划分
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FixBatch:
    """一个修复批次"""
    id: int
    priority: str           # critical / high / medium / low
    files: list[str]        # 本批次涉及的文件（相对路径）
    finding_ids: list[str]  # 本批次要修复的 finding ID
    findings: list[dict]    # finding dict 列表
    summary: str
    complexity: str         # low / medium / high


@dataclass
class ImprovementPlan:
    """结构化改进方案"""
    batches: list[FixBatch] = field(default_factory=list)
    total_findings: int = 0
    total_batches: int = 0

    def __post_init__(self):
        self.total_batches = len(self.batches)
        self.total_findings = sum(len(b.finding_ids) for b in self.batches)


class PlanGenerator:
    """改进方案生成器"""

    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def generate(
        self,
        findings: list,
        project_dir: str,
        project_context: dict,
        use_llm: bool = True,
        llm_client=None,
    ) -> ImprovementPlan:
        """
        生成改进方案。

        Args:
            findings: Finding 对象或 dict 列表
            project_dir: 项目根目录
            project_context: {"project_name", "framework", "total_files"}
            use_llm: 是否用 LLM 优化批次划分
            llm_client: LLMClient 实例（use_llm=True 时必须提供）

        Returns:
            ImprovementPlan
        """
        # 标准化为 dict
        finding_dicts = [
            f.to_dict() if hasattr(f, "to_dict") else f for f in findings
        ]

        # 1. 过滤：只保留有 fix_suggestion 的
        actionable = [f for f in finding_dicts if f.get("fix_suggestion")]
        if not actionable:
            logger.info("无可操作的发现（无 fix_suggestion）")
            return ImprovementPlan()

        # 2. 按文件分组
        file_groups = {}
        for f in actionable:
            fp = f.get("file_path", "")
            if not fp:
                continue
            if fp not in file_groups:
                file_groups[fp] = []
            file_groups[fp].append(f)

        # 3. 创建批次
        raw_batches = []
        batch_id = 1
        for file_path, file_findings in file_groups.items():
            # 批次优先级 = 该文件中最高 severity
            min_severity = min(
                self.SEVERITY_ORDER.get(f.get("severity", "medium").lower(), 2)
                for f in file_findings
            )
            priority_name = [k for k, v in self.SEVERITY_ORDER.items() if v == min_severity][0]

            # 复杂度：单文件发现数 > 3 或有 "high" complexity 标记
            complexity = "low"
            if len(file_findings) > 3:
                complexity = "high"
            elif len(file_findings) > 1:
                complexity = "medium"

            # 摘要
            titles = [f.get("title", "") for f in file_findings[:3]]
            summary = f"{Path(file_path).name}: {'; '.join(titles[:2])}"
            if len(titles) > 2:
                summary += f" 等{len(file_findings)}个问题"

            batch = FixBatch(
                id=batch_id,
                priority=priority_name,
                files=[file_path],
                finding_ids=[f.get("id", "") for f in file_findings],
                findings=file_findings,
                summary=summary,
                complexity=complexity,
            )
            raw_batches.append(batch)
            batch_id += 1

        # 4. 排序：severity 优先 → 依赖拓扑
        sorted_batches = self._topological_sort(raw_batches, project_dir)

        # 5. 重新编号
        for i, batch in enumerate(sorted_batches, 1):
            batch.id = i

        # 6. LLM 增强（可选）
        if use_llm and llm_client:
            sorted_batches = self._llm_enhance(
                sorted_batches, actionable, project_context, llm_client
            )

        return ImprovementPlan(batches=sorted_batches)

    def _topological_sort(
        self, batches: list[FixBatch], project_dir: str
    ) -> list[FixBatch]:
        """
        拓扑排序：被依赖的文件优先修复。

        策略：分析文件 import 关系，如果 batch A 的文件被 batch B 的文件 import，
        则 A 应该在 B 之前执行。

        对于非 Python 文件或解析失败的文件，保持原顺序。
        """
        # 构建文件 → batch 映射
        file_to_batch = {}
        for batch in batches:
            for fp in batch.files:
                file_to_batch[fp] = batch

        # 分析依赖
        deps = {}  # batch_id → set of batch_ids it depends on
        for batch in batches:
            deps[batch.id] = set()
            for fp in batch.files:
                full_path = Path(project_dir) / fp
                if not full_path.exists():
                    continue
                if not fp.endswith(".py"):
                    continue
                try:
                    imports = self._extract_imports(full_path)
                    for imp in imports:
                        # 将 import 模块名映射到文件路径
                        dep_path = self._module_to_file(imp, project_dir)
                        if dep_path and dep_path in file_to_batch:
                            dep_batch = file_to_batch[dep_path]
                            if dep_batch.id != batch.id:
                                deps[batch.id].add(dep_batch.id)
                except Exception:
                    pass

        # 拓扑排序（Kahn 算法）
        in_degree = {b.id: 0 for b in batches}
        for bid, dep_ids in deps.items():
            in_degree[bid] = len(dep_ids)

        batch_map = {b.id: b for b in batches}
        queue = [bid for bid, deg in in_degree.items() if deg == 0]
        # 按 severity 排序
        queue.sort(key=lambda bid: self.SEVERITY_ORDER.get(batch_map[bid].priority, 2))

        result = []
        while queue:
            bid = queue.pop(0)
            result.append(batch_map[bid])
            for other_bid in list(deps.keys()):
                if bid in deps[other_bid]:
                    deps[other_bid].discard(bid)
                    in_degree[other_bid] -= 1
                    if in_degree[other_bid] == 0:
                        queue.append(other_bid)
                        queue.sort(key=lambda x: self.SEVERITY_ORDER.get(batch_map[x].priority, 2))

        # 添加无法拓扑排序的批次（有环）
        remaining = [b for b in batches if b not in result]
        remaining.sort(key=lambda b: self.SEVERITY_ORDER.get(b.priority, 2))
        result.extend(remaining)

        return result

    @staticmethod
    def _extract_imports(file_path: Path) -> list[str]:
        """从 Python 文件中提取 import 的模块名"""
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])
        return imports

    @staticmethod
    def _module_to_file(module_name: str, project_dir: str) -> Optional[str]:
        """将模块名映射到文件路径"""
        # 项目内的模块
        candidates = [
            str(Path(module_name.replace(".", "/")).with_suffix(".py")),
            str(Path("app") / module_name.replace(".", "/") / "__init__.py"),
            str(Path("app") / module_name.replace(".", "/")).with_suffix(".py"),
        ]
        for rel in candidates:
            if (Path(project_dir) / rel).exists():
                return rel
        return None

    def _llm_enhance(
        self,
        batches: list[FixBatch],
        findings: list[dict],
        project_context: dict,
        llm_client,
    ) -> list[FixBatch]:
        """用 LLM 优化批次划分和依赖分析"""
        try:
            plan_data = llm_client.generate_plan(findings, project_context)
            if not plan_data or "batches" not in plan_data:
                return batches

            llm_batches = plan_data["batches"]
            if not llm_batches:
                return batches

            # 用 LLM 的批次结构，但保留原始 finding 数据
            enhanced = []
            for i, lb in enumerate(llm_batches):
                # 找到对应的 findings
                lb_finding_ids = lb.get("findings", [])
                matched_findings = [
                    f for f in findings
                    if f.get("id", "") in lb_finding_ids
                ]
                if not matched_findings:
                    continue

                batch = FixBatch(
                    id=i + 1,
                    priority=lb.get("priority", "high"),
                    files=lb.get("files", []),
                    finding_ids=lb_finding_ids,
                    findings=matched_findings,
                    summary=lb.get("summary", ""),
                    complexity=lb.get("complexity", "medium"),
                )
                enhanced.append(batch)

            if enhanced:
                logger.info(f"LLM 优化: {len(batches)} → {len(enhanced)} 批次")
                return enhanced
        except Exception as e:
            logger.warning(f"LLM enhance failed, using local plan: {e}")

        return batches
