"""
DataFlowExpert — 数据流与行为正确性审查员

检测跨模块数据传播问题：浅拷贝不同步、generator 返回值未捕获、
共享可变状态、引用传递导致的状态不一致。
支持 Python (.py) 和 TypeScript (.ts) 文件。
"""

import re
from typing import List, Dict, Optional

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from experts.base_expert import BaseExpert
from core.finding import Finding, FindingList, Severity, Category
from core.review_context import ReviewContext
from evolution.evolution_store import EvolutionState


class DataFlowExpert(BaseExpert):
    """数据流与行为正确性审查员"""

    name = "data_flow"
    name_cn = "数据流审查员"
    description = "审查跨模块数据传播、引用同步、generator 返回值、共享可变状态"

    # === Python 检测模式 ===

    PYTHON_PATTERNS = {
        "shallow copy + mutate": {
            # [list(args)] 或 dict(old) 后对副本做 append/push/update
            "pattern": r"(\w+)\s*=\s*\[.*?\]\s*\(.*?\)|(\w+)\s*=\s*\[\s*\.\.\.\w+\]",
            "severity": Severity.HIGH,
            "category": Category.DATA_FLOW,
            "suggestion": "浅拷贝创建了新数组，修改副本不会同步到原数组。如需同步，直接操作原数组或显式返回修改后的副本。",
        },
        "list copy + append": {
            # list(old_list) 或 old[:] 后 append
            "pattern": r"(\w+)\s*=\s*\w+\s*\[\s*:\s*\]|\w+\s*=\s*list\(",
            "severity": Severity.MEDIUM,
            "category": Category.DATA_FLOW,
            "suggestion": "列表切片创建副本，后续 append/push 不会反映到原列表。确认调用方是否需要看到修改。",
        },
        "dict copy + update": {
            "pattern": r"(\w+)\s*=\s*\w+\s*\.copy\(\)|(\w+)\s*=\s*dict\(",
            "severity": Severity.MEDIUM,
            "category": Category.DATA_FLOW,
            "suggestion": "字典拷贝后 update 不会同步到原字典。确认数据流是否需要双向同步。",
        },
    }

    # === TypeScript/JavaScript 检测模式 ===

    TYPESCRIPT_PATTERNS = {
        "spread copy + mutate": {
            # [...arr] 或 {...obj} 后 push/修改
            "pattern": r"(\w+)\s*=\s*\[\s*\.\.\.(\w+)\s*\]",
            "severity": Severity.HIGH,
            "category": Category.DATA_FLOW,
            "suggestion": "[...arr] 创建浅拷贝，后续 push/修改不会同步到原数组。如需同步，直接操作原数组或显式返回。",
        },
        "object spread copy": {
            "pattern": r"(\w+)\s*=\s*\{\s*\.\.\.(\w+)\s*\}",
            "severity": Severity.MEDIUM,
            "category": Category.DATA_FLOW,
            "suggestion": "{...obj} 创建浅拷贝，嵌套对象仍是引用。确认深层修改是否影响原对象。",
        },
        "for await return uncaptured": {
            # for await...of 消费 async generator 但没有 = 赋值
            "pattern": r"for\s+await\s*\(\s*\w+\s+of\s+\w+\(",
            "severity": Severity.HIGH,
            "category": Category.DATA_FLOW,
            "suggestion": "for await...of 不捕获 async generator 的 return value。如需获取返回值，使用 generator.next() 或将返回值存储在 generator 外部变量中。",
        },
        "for of return uncaptured": {
            "pattern": r"for\s*\(\s*\w+\s+of\s+\w+\(",
            "severity": Severity.HIGH,
            "category": Category.DATA_FLOW,
            "suggestion": "for...of 不捕获 generator 的 return value。如果 generator 返回了重要数据（如更新后的状态），需要额外处理。",
        },
        "array parameter mutation": {
            # 函数参数是数组，函数内 push/splice
            "pattern": r"(\w+)\s*\.\s*(push|pop|shift|unshift|splice|sort|reverse)\s*\(",
            "severity": Severity.MEDIUM,
            "category": Category.DATA_FLOW,
            "suggestion": "修改传入的数组参数会影响调用方。如不希望产生副作用，应在函数内创建副本。",
        },
    }

    def review(self, source_files: List[str] = None) -> FindingList:
        files = self.scan_all_files(source_files)

        py_files = self.filter_by_extension(files, [".py"])
        ts_files = self.filter_by_extension(files, [".ts", ".tsx", ".js", ".jsx"])

        for file_path in py_files:
            self._check_patterns(file_path, self.PYTHON_PATTERNS)

        for file_path in ts_files:
            self._check_typescript_patterns(file_path)

        return self.findings

    def _check_patterns(self, file_path: str, patterns: Dict[str, Dict]):
        """Python 通用模式检测"""
        lines = self.read_file_lines(file_path)
        if not lines:
            return

        for pattern_name, config in patterns.items():
            matches = self.find_pattern_in_file(file_path, config["pattern"])
            for match in matches:
                line_no = match["line"] - 1
                if line_no < len(lines):
                    raw_line = lines[line_no].strip()
                    if raw_line.startswith("#") or raw_line.startswith("//"):
                        continue

                self.add_finding(
                    title=f"{pattern_name}: {match['content'][:80]}",
                    severity=config["severity"],
                    category=config["category"],
                    file_path=file_path,
                    line_range=str(match["line"]),
                    code_snippet=match["content"],
                    description=f"在 {file_path}:{match['line']} 发现 {pattern_name}",
                    fix_suggestion=config["suggestion"],
                )

    def _check_typescript_patterns(self, file_path: str):
        """TypeScript 专用检测（含上下文感知）"""
        lines = self.read_file_lines(file_path)
        if not lines:
            return

        content = "\n".join(lines)

        # === 检测 [...arr] 浅拷贝 + 后续 mutation ===
        self._check_spread_copy_mutate(file_path, lines, content)

        # === 检测 for await...of 消费 generator 但返回值丢失 ===
        self._check_generator_return(file_path, lines)

        # === 检测 async generator yield + return 但调用方不处理返回值 ===
        self._check_async_generator_contract(file_path, lines, content)

    def _check_spread_copy_mutate(self, file_path: str, lines: List[str], content: str):
        """检测 [...arr] 浅拷贝后对副本做 push/修改"""
        spread_pattern = re.compile(r"(\w+)\s*=\s*\[\s*\.\.\.(\w+)\s*\]")
        mutations = {"push", "pop", "shift", "unshift", "splice", "sort", "reverse"}

        for match in spread_pattern.finditer(content):
            copy_var = match.group(1)
            source_var = match.group(2)

            # 在后续 20 行内检查是否有 mutation
            match_line = content[:match.end()].count("\n")
            check_lines = lines[match_line:match_line + 20]

            for i, line in enumerate(check_lines):
                stripped = line.strip()
                if f"{copy_var}." in stripped or f"{copy_var}[" in stripped:
                    for mutation in mutations:
                        if f".{mutation}(" in stripped:
                            self.add_finding(
                                title=f"Shallow copy mutation: {copy_var} = [...{source_var}] then .{mutation}()",
                                severity=Severity.HIGH,
                                category=Category.DATA_FLOW,
                                file_path=file_path,
                                line_range=str(match_line + i + 1),
                                code_snippet=stripped,
                                description=(
                                    f"{copy_var} 是 {source_var} 的浅拷贝。"
                                    f"对 {copy_var} 调用 .{mutation}() 不会修改 {source_var}。"
                                    f"如果 {source_var} 的持有者需要看到修改，这是 bug。"
                                ),
                                fix_suggestion=(
                                    f"如需同步修改：直接操作 {source_var}，"
                                    f"或让函数返回修改后的 {copy_var} 并由调用方替换原引用。"
                                ),
                            )
                            break  # 每个 spread 只报一次

    def _check_generator_return(self, file_path: str, lines: List[str]):
        """检测 for await...of 消费 generator 但 return value 未被捕获"""
        gen_pattern = re.compile(r"for\s+(await\s+)?(\w+)\s+of\s+(\w+)\s*\(")
        return_pattern = re.compile(r"return\s*\{")

        for i, line in enumerate(lines):
            match = gen_pattern.search(line)
            if not match:
                continue

            var_name = match.group(2)
            gen_name = match.group(3)
            is_await = bool(match.group(1))

            # 检查是否是 async generator function（yield + async）
            # 检查 generator 函数定义中是否有 return 语句
            func_name = gen_name
            # 向上查找函数定义
            for j in range(i, max(i - 50, 0), -1):
                if f"function* {func_name}" in lines[j] or f"async function* {func_name}" in lines[j]:
                    # 找到了 generator 定义
                    break
                if f"function {func_name}" in lines[j] or f"async function {func_name}" in lines[j]:
                    # 不是 generator（没有 *）
                    break

            # 检查 for 循环的结果是否被赋值
            # for await...of 本身不捕获 return value
            # 但如果循环后有使用 gen_name 的地方，可能已经处理了
            loop_indent = len(line) - len(line.lstrip())
            after_loop = lines[i + 1:i + 5] if i + 1 < len(lines) else []

            # 如果 for 循环被赋值给变量（const result = for await...），则已捕获
            if i > 0:
                prev_line = lines[i - 1].strip()
                if prev_line.startswith("const ") or prev_line.startswith("let ") or prev_line.startswith("var "):
                    if "=" in prev_line:
                        continue  # 已赋值

            # 检查 generator 函数是否有 return 语句（有意义的返回值）
            # 简化：如果项目中有 async generator（async function*），报告
            for j in range(max(0, i - 100), i):
                if re.search(r"async\s+function\s*\*\s*\w+", lines[j]):
                    self.add_finding(
                        title=f"Generator return value may be lost: for {is_await and 'await ' or ''}{var_name} of {gen_name}",
                        severity=Severity.MEDIUM,
                        category=Category.DATA_FLOW,
                        file_path=file_path,
                        line_range=str(i + 1),
                        code_snippet=line.strip(),
                        description=(
                            f"async generator {gen_name} 可能有有意义的 return value，"
                            f"但 for await...of 不会捕获它。"
                        ),
                        fix_suggestion=(
                            "如果 generator 返回了 QueryResult 或类似数据，"
                            "需要在使用 generator.next() 后获取 value，"
                            "或将返回值存储在 generator 外部的变量中。"
                        ),
                    )
                    break

    def _check_async_generator_contract(self, file_path: str, lines: List[str], content: str):
        """检测 async generator 函数的 yield + return 契约是否被调用方遵守"""
        # 找到所有 async function* 定义
        gen_func_pattern = re.compile(r"(?:export\s+)?(?:async\s+)?function\s*\*\s*(\w+)\s*[<(]")

        for match in gen_func_pattern.finditer(content):
            func_name = match.group(1)
            func_start = content[:match.start()].count("\n")

            # 检查函数内是否有 return 语句（除了 return;）
            func_lines = lines[func_start:func_start + 200] if func_start + 200 <= len(lines) else lines[func_start:]
            has_return = False
            for fl in func_lines:
                stripped = fl.strip()
                if re.match(r"return\s*\{", stripped) or re.match(r"return\s+\w", stripped):
                    has_return = True
                    break
                if stripped.startswith("return;") or stripped == "return":
                    break  # 空 return，不是有意义的返回值

            if not has_return:
                continue  # 没有 return value，不需要检查

            # 检查调用方是否正确处理了返回值
            for call_match in re.finditer(rf"{func_name}\s*\(", content):
                call_line_no = content[:call_match.start()].count("\n")
                call_line = lines[call_line_no].strip()

                # 如果在 for await...of 中消费
                if "for" in call_line and "of" in call_line:
                    self.add_finding(
                        title=f"Async generator {func_name} return value not captured by caller",
                        severity=Severity.HIGH,
                        category=Category.DATA_FLOW,
                        file_path=file_path,
                        line_range=str(call_line_no + 1),
                        code_snippet=call_line,
                        description=(
                            f"async generator {func_name} 有有意义的 return value，"
                            f"但调用方使用 for await...of 消费，返回值被丢弃。"
                        ),
                        fix_suggestion=(
                            f"方案1: 让 generator 修改传入的参数（引用传递），而非通过 return 返回。\n"
                            f"方案2: 用 generator.next() 手动迭代，最后检查 done 和 value。\n"
                            f"方案3: 将返回值存储在闭包或外部变量中。"
                        ),
                    )
