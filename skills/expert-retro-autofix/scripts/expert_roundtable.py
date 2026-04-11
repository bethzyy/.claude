"""
ExpertRoundtable — 三人专家圆桌讨论

流程：
  Round 1: 3个专家独立分析（并行 GLM-4-flash）
  Round 2: 3个专家交叉审查其他专家发现（并行 GLM-4-flash）
  Round 3: 综合去重、定级、分批（GLM-4）

输入：项目快照 JSON 文件路径
输出：结构化 findings JSON 到 stdout
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 复用 expert-review 的 LLMClient
SKILLS_DIR = Path(__file__).resolve().parent.parent.parent
EXPERT_REVIEW_DIR = SKILLS_DIR / "expert-review"
if str(EXPERT_REVIEW_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERT_REVIEW_DIR))

from autofix.llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============ 三人专家系统提示 ============

EXPERT_A_SYSTEM = """你是「代码质量架构师」，专注于：
- Bug 和逻辑缺陷（空指针、边界条件、竞态）
- 错误处理缺口（吞异常、缺失 try/except、错误类型不当）
- 性能瓶颈（N+1查询、内存泄漏、不必要的同步操作）
- 代码味道（重复代码、过长函数、魔法数字、过度嵌套）
- 输入验证缺失（未校验用户输入、未处理 None/空值）
- 可测试性差（硬编码依赖、不可 mock 的全局状态）

你的输出必须是 JSON 数组，每个元素包含：
{
  "id": "FND-A{N}",
  "severity": "critical|high|medium|low",
  "category": "bug|error_handling|performance|code_smell|validation|testability",
  "file_path": "相对路径",
  "line_range": "行号范围（如 42-56）",
  "title": "一句话标题",
  "description": "详细问题描述",
  "fix_suggestion": "具体修复建议（可操作的步骤）",
  "code_snippet": "问题代码片段"
}

如果未发现问题，返回空数组 []。"""

EXPERT_B_SYSTEM = """你是「系统设计评审员」，专注于：
- 模块耦合度（循环依赖、紧耦合、接口不清晰）
- API 契约一致性（请求/响应格式、错误码、版本管理）
- 数据流正确性（数据在模块间传递是否准确、完整）
- 抽象边界（层次越权、职责不清）
- 可扩展性（硬编码配置、不易扩展的设计）
- 技术债（过时用法、TODO/FIXME 遗留、废弃 API）
- 数据库设计（索引缺失、查询效率、ORM 误用）

你的输出必须是 JSON 数组，每个元素包含：
{
  "id": "FND-B{N}",
  "severity": "critical|high|medium|low",
  "category": "architecture|api_contract|data_flow|coupling|scalability|tech_debt|database",
  "file_path": "相对路径",
  "line_range": "行号范围",
  "title": "一句话标题",
  "description": "详细问题描述",
  "fix_suggestion": "具体修复建议",
  "code_snippet": "问题代码片段"
}

如果未发现问题，返回空数组 []。"""

EXPERT_C_SYSTEM = """你是「运维可靠性工程师」，专注于：
- 安全漏洞（OWASP Top 10：注入、XSS、CSRF、敏感信息泄露、认证缺陷）
- 配置管理（硬编码密钥、不安全的默认配置、环境变量处理）
- 部署就绪度（Docker 配置、依赖锁定、健康检查）
- 监控缺口（关键路径无日志、无告警、无指标）
- 资源管理（连接池泄漏、文件句柄未关闭、临时文件清理）
- 韧性设计（无超时、无重试、无熔断、无降级）
- 依赖安全（已知漏洞包、未锁定版本）

你的输出必须是 JSON 数组，每个元素包含：
{
  "id": "FND-C{N}",
  "severity": "critical|high|medium|low",
  "category": "security|config|deployment|monitoring|resource|resilience|dependency",
  "file_path": "相对路径",
  "line_range": "行号范围",
  "title": "一句话标题",
  "description": "详细问题描述",
  "fix_suggestion": "具体修复建议",
  "code_snippet": "问题代码片段"
}

如果未发现问题，返回空数组 []。"""

CROSS_REVIEW_PROMPT = """你刚完成了独立分析。现在请审查另外两位专家的发现：

## 你的原始发现
{own_findings}

## 专家 {other_a} 的发现
{findings_a}

## 专家 {other_b} 的发现
{findings_b}

## 任务
1. 从你的专业领域出发，检查其他专家的发现中是否有遗漏或误判
2. 标注你不同意的发现（说明原因）
3. 补充你发现的跨领域问题（多个 finding 之间的关联风险）

输出 JSON 数组，每个元素格式：
{
  "id": "FND-{expert}-{N}",
  "type": "new_finding|disagreement|cross_cutting",
  "refers_to": "引用的 finding ID（如果是 disagreement 或 cross_cutting）",
  "severity": "critical|high|medium|low",
  "category": "...",
  "file_path": "...",
  "line_range": "...",
  "title": "...",
  "description": "...",
  "fix_suggestion": "...",
  "code_snippet": "..."
}

如无补充，返回空数组 []。"""

SYNTHESIS_PROMPT = """你是「评审综合官」，负责将三位专家两轮讨论的结果整合为最终改进方案。

## Round 1 独立发现
{round1_findings}

## Round 2 交叉审查
{round2_findings}

## 任务
1. **去重**：合并描述同一问题的 finding，保留描述最完整的版本
2. **定级**：综合三位专家意见确定最终严重级别
3. **排序**：按 critical → high → medium → low 排序
4. **分批**：按文件分组，考虑依赖关系（被依赖的文件先修复）
5. **过滤**：移除 false positive 和不具操作性的建议

## 输出格式
严格输出 JSON：
{
  "findings": [
    {
      "id": "FND-{N}",
      "severity": "critical|high|medium|low",
      "category": "...",
      "file_path": "...",
      "line_range": "...",
      "title": "...",
      "description": "...",
      "fix_suggestion": "...",
      "code_snippet": "...",
      "sources": ["FND-A1", "FND-C3"]
    }
  ],
  "batches": [
    {
      "id": 1,
      "priority": "critical|high|medium",
      "files": ["path/to/file.py"],
      "findings": ["FND-1", "FND-3"],
      "summary": "一句话描述",
      "complexity": "low|medium|high"
    }
  ],
  "stats": {
    "total_findings": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  }
}"""


def load_snapshot(snapshot_path: str) -> dict:
    """加载项目快照 JSON"""
    with open(snapshot_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_snapshot_for_expert(snapshot: dict, expert_focus: str) -> str:
    """根据专家关注点格式化快照内容"""
    parts = [f"# 项目快照\n"]
    parts.append(f"## 基本信息")
    parts.append(f"- 项目名: {snapshot.get('project_name', 'unknown')}")
    parts.append(f"- 框架: {snapshot.get('framework', 'unknown')}")
    parts.append(f"- 总文件数: {snapshot.get('total_files', 0)}")

    # 结构信息
    if "file_tree" in snapshot:
        parts.append(f"\n## 文件结构")
        for f in snapshot["file_tree"]:
            parts.append(f"- {f}")

    # 模式扫描结果
    if "pattern_findings" in snapshot:
        parts.append(f"\n## 模式扫描发现")
        for p in snapshot["pattern_findings"]:
            parts.append(f"- [{p.get('severity', '?')}] {p.get('pattern', '?')}: {p.get('file', '?')}:{p.get('line', '?')} — {p.get('content', '')[:100]}")

    # 架构信息
    if "architecture" in snapshot:
        parts.append(f"\n## 架构分析")
        arch = snapshot["architecture"]
        if "imports" in arch:
            parts.append(f"### 关键模块依赖")
            for mod, deps in list(arch["imports"].items())[:20]:
                parts.append(f"- {mod} → {', '.join(deps[:5])}")
        if "route_service_map" in arch:
            parts.append(f"### 路由-服务映射")
            for route, svc in arch.get("route_service_map", {}).items():
                parts.append(f"- {route} → {svc}")

    # 测试结果
    if "test_results" in snapshot:
        parts.append(f"\n## 测试结果")
        parts.append(f"```")
        parts.append(snapshot["test_results"][:2000])
        parts.append(f"```")

    # 依赖信息
    if "dependencies" in snapshot:
        parts.append(f"\n## 依赖")
        parts.append(snapshot["dependencies"][:1000])

    # 关键代码片段（按专家关注点筛选）
    if "key_snippets" in snapshot:
        parts.append(f"\n## 关键代码片段")
        for s in snapshot["key_snippets"][:10]:
            parts.append(f"### {s.get('file', '?')} (lines {s.get('start', '?')}-{s.get('end', '?')})")
            parts.append(f"```{s.get('language', '')}")
            parts.append(s.get("content", "")[:500])
            parts.append("```")

    return "\n".join(parts)


def run_round1(llm: LLMClient, snapshot_text: str) -> Dict[str, List[dict]]:
    """Round 1: 三位专家独立分析"""
    experts = {
        "A": EXPERT_A_SYSTEM,
        "B": EXPERT_B_SYSTEM,
        "C": EXPERT_C_SYSTEM,
    }

    results = {}
    for expert_id, system_prompt in experts.items():
        logger.info(f"Round 1: Expert {expert_id} 正在分析...")
        try:
            response = llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请分析以下项目快照，找出你专业领域内的问题：\n\n{snapshot_text}"},
                ],
                model="glm-4-flash",
                temperature=0.3,
                max_tokens=8192,
            )
            findings = llm._parse_json_response(response)
            if isinstance(findings, list):
                results[expert_id] = findings
            else:
                logger.warning(f"Expert {expert_id} 返回非数组结果，尝试提取数组")
                # 尝试从 dict 中提取数组
                if isinstance(findings, dict):
                    for v in findings.values():
                        if isinstance(v, list):
                            results[expert_id] = v
                            break
                    else:
                        results[expert_id] = []
                else:
                    results[expert_id] = []
        except Exception as e:
            logger.error(f"Expert {expert_id} Round 1 失败: {e}")
            results[expert_id] = []

    return results


def run_round2(llm: LLMClient, round1_results: Dict[str, List[dict]]) -> Dict[str, List[dict]]:
    """Round 2: 交叉审查"""
    experts = {"A": "代码质量架构师", "B": "系统设计评审员", "C": "运维可靠性工程师"}
    expert_keys = list(experts.keys())

    results = {}
    for i, expert_id in enumerate(expert_keys):
        other_ids = [k for k in expert_keys if k != expert_id]
        own_findings = json.dumps(round1_results.get(expert_id, []), ensure_ascii=False, indent=2)
        findings_a = json.dumps(round1_results.get(other_ids[0], []), ensure_ascii=False, indent=2)
        findings_b = json.dumps(round1_results.get(other_ids[1], []), ensure_ascii=False, indent=2)

        logger.info(f"Round 2: Expert {expert_id} 交叉审查...")
        try:
            response = llm.chat(
                messages=[
                    {"role": "user", "content": CROSS_REVIEW_PROMPT.format(
                        own_findings=own_findings[:3000],
                        other_a=experts[other_ids[0]],
                        findings_a=findings_a[:3000],
                        other_b=experts[other_ids[1]],
                        findings_b=findings_b[:3000],
                    )},
                ],
                model="glm-4-flash",
                temperature=0.3,
                max_tokens=4096,
            )
            cross_findings = llm._parse_json_response(response)
            if isinstance(cross_findings, list):
                results[expert_id] = cross_findings
            else:
                results[expert_id] = []
        except Exception as e:
            logger.error(f"Expert {expert_id} Round 2 失败: {e}")
            results[expert_id] = []

    return results


def run_synthesis(llm: LLMClient, round1: Dict[str, List[dict]], round2: Dict[str, List[dict]]) -> dict:
    """Round 3: 综合去重、定级、分批"""
    all_r1 = []
    for expert_id, findings in round1.items():
        all_r1.extend(findings)

    all_r2 = []
    for expert_id, findings in round2.items():
        all_r2.extend(findings)

    prompt = SYNTHESIS_PROMPT.format(
        round1_findings=json.dumps(all_r1, ensure_ascii=False, indent=2)[:6000],
        round2_findings=json.dumps(all_r2, ensure_ascii=False, indent=2)[:4000],
    )

    logger.info("Round 3: 综合分析...")
    try:
        response = llm.chat(
            messages=[{"role": "user", "content": prompt}],
            model="glm-4-flash",
            temperature=0.2,
            max_tokens=8192,
        )
        result = llm._parse_json_response(response)
        if isinstance(result, dict):
            return result
        return {"findings": [], "batches": [], "stats": {"total_findings": 0}}
    except Exception as e:
        logger.error(f"综合分析失败: {e}")
        return {"findings": [], "batches": [], "stats": {"total_findings": 0}}


def main():
    """主入口：读取快照 → 三轮讨论 → 输出 findings"""
    if len(sys.argv) < 2:
        print("用法: python expert_roundtable.py <snapshot.json>", file=sys.stderr)
        sys.exit(1)

    snapshot_path = sys.argv[1]
    if not Path(snapshot_path).exists():
        print(f"快照文件不存在: {snapshot_path}", file=sys.stderr)
        sys.exit(1)

    # 加载快照
    snapshot = load_snapshot(snapshot_path)
    snapshot_text = format_snapshot_for_expert(snapshot, "all")
    logger.info(f"快照加载完成: {snapshot.get('project_name', 'unknown')}, {snapshot.get('total_files', 0)} 文件")

    # 初始化 LLM 客户端
    llm = LLMClient()

    # Round 1: 独立分析
    logger.info("===== Round 1: 独立分析 =====")
    round1_results = run_round1(llm, snapshot_text)
    total_r1 = sum(len(v) for v in round1_results.values())
    logger.info(f"Round 1 完成: 共 {total_r1} 个发现 (A:{len(round1_results.get('A',[]))} B:{len(round1_results.get('B',[]))} C:{len(round1_results.get('C',[]))})")

    # Round 2: 交叉审查
    logger.info("===== Round 2: 交叉审查 =====")
    round2_results = run_round2(llm, round1_results)
    total_r2 = sum(len(v) for v in round2_results.values())
    logger.info(f"Round 2 完成: 共 {total_r2} 个补充发现")

    # Round 3: 综合
    logger.info("===== Round 3: 综合分析 =====")
    final = run_synthesis(llm, round1_results, round2_results)
    logger.info(f"综合完成: {final.get('stats', {}).get('total_findings', 0)} 个最终发现, {len(final.get('batches', []))} 个批次")

    # 输出到 stdout
    print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
