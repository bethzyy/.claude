"""
ArchitectureExpert — 架构分析师

审查模块依赖、设计模式、耦合度、接口设计、技术债务。
"""

import os
import re
from typing import List, Dict, Optional, Set, Tuple

from core._paths import SKILL_DIR, ensure_skill_path
ensure_skill_path()

from experts.base_expert import BaseExpert
from core.finding import Finding, FindingList, Severity, Category
from core.review_context import ReviewContext
from evolution.evolution_store import EvolutionState


class ArchitectureExpert(BaseExpert):
    """架构分析师 — 模块依赖、设计模式、耦合度"""

    name = "architecture"
    name_cn = "架构分析师"
    description = "审查模块依赖关系、设计模式、紧耦合、循环依赖、技术债务"

    def review(self, source_files: List[str] = None) -> FindingList:
        files = self.scan_all_files(source_files)
        py_files = self.filter_by_extension(files, [".py"])

        self._check_module_structure(py_files)
        self._check_circular_imports(py_files)
        self._check_god_classes(py_files)
        self._check_interface_consistency(py_files)
        self._check_dependency_direction(py_files)

        return self.findings

    def _check_module_structure(self, files: List[str]):
        """检查模块结构是否合理"""
        # 统计各目录的文件数
        dir_counts: Dict[str, int] = {}
        for f in files:
            parts = f.replace("\\", "/").split("/")
            if len(parts) > 1:
                dir_name = parts[0]
                dir_counts[dir_name] = dir_counts.get(dir_name, 0) + 1

        # 根目录文件过多 = 缺乏模块化
        root_files = [f for f in files if "/" not in f.replace("\\", "/")]
        if len(root_files) > 10:
            self.add_finding(
                title=f"Too many files in root directory ({len(root_files)} files)",
                severity=Severity.MEDIUM,
                category=Category.ARCHITECTURE,
                file_path="",
                description=f"根目录有 {len(root_files)} 个 Python 文件，建议按功能分子目录",
                fix_suggestion="将相关文件组织到子模块中（如 routes/, models/, services/）",
                effort="medium",
            )

    def _check_circular_imports(self, files: List[str]):
        """检测循环导入风险"""
        import_map: Dict[str, Set[str]] = {}

        for file_path in files:
            content = self.read_file(file_path)
            if not content:
                continue

            imports = set()
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("from "):
                    # from module import something
                    match = re.match(r"from\s+([.\w]+)\s+import", stripped)
                    if match:
                        module = match.group(1).split(".")[0]
                        imports.add(module)
                elif stripped.startswith("import "):
                    match = re.match(r"import\s+([\w.,\s]+)", stripped)
                    if match:
                        for mod in match.group(1).split(","):
                            imports.add(mod.strip().split(".")[0])

            import_map[file_path] = imports

        # 检测循环：A imports B, B imports A
        checked = set()
        for f_a, imports_a in import_map.items():
            for f_b in imports_a:
                # 检查 f_b 是否也在文件列表中
                for f_b_full in files:
                    module_name = f_b_full.replace("/", ".").replace("\\", ".").replace(".py", "")
                    if f_b in module_name or module_name.endswith(f".{f_b}"):
                        # f_a imports f_b, 检查 f_b 是否 imports f_a
                        imports_b = import_map.get(f_b_full, set())
                        a_module = f_a.replace("/", ".").replace("\\", ".").replace(".py", "")
                        for imp_b in imports_b:
                            if imp_b in a_module or a_module.endswith(f".{imp_b}"):
                                pair = tuple(sorted([f_a, f_b_full]))
                                if pair not in checked:
                                    checked.add(pair)
                                    self.add_finding(
                                        title=f"Circular import: {f_a} <-> {f_b_full}",
                                        severity=Severity.HIGH,
                                        category=Category.ARCHITECTURE,
                                        file_path=f_a,
                                        description=f"检测到循环导入: {f_a} 和 {f_b_full} 互相引用",
                                        fix_suggestion="使用依赖注入或将共享逻辑提取到独立模块",
                                        effort="large",
                                    )
                                break
                        break

    def _check_god_classes(self, files: List[str]):
        """检测上帝类（行数过多 + 方法过多）"""
        for file_path in files:
            content = self.read_file(file_path)
            if not content:
                continue

            lines = content.split("\n")
            total_lines = len(lines)

            # 检查文件是否过大
            if total_lines > 500:
                self.add_finding(
                    title=f"Oversized file: {file_path} ({total_lines} lines)",
                    severity=Severity.MEDIUM,
                    category=Category.ARCHITECTURE,
                    file_path=file_path,
                    description=f"文件 {file_path} 有 {total_lines} 行，超过 500 行阈值",
                    fix_suggestion="拆分为多个模块，按单一职责原则组织",
                    effort="large",
                )

            # 检查类是否过大
            class_pattern = re.compile(r"^class\s+(\w+)")
            class_starts = []
            for i, line in enumerate(lines):
                if class_pattern.match(line):
                    class_starts.append((i, class_pattern.match(line).group(1)))

            for idx, (start, class_name) in enumerate(class_starts):
                end = class_starts[idx + 1][0] if idx + 1 < len(class_starts) else len(lines)
                class_lines = end - start

                if class_lines > 300:
                    self.add_finding(
                        title=f"God class: {class_name} ({class_lines} lines)",
                        severity=Severity.HIGH,
                        category=Category.ARCHITECTURE,
                        file_path=file_path,
                        line_range=f"{start+1}-{end}",
                        description=f"类 {class_name} 有 {class_lines} 行，职责过多",
                        fix_suggestion="拆分为多个小类，使用组合替代继承",
                        effort="large",
                    )

                # 计算方法数
                method_count = 0
                for line in lines[start:end]:
                    if re.match(r"\s+def\s+\w+", line):
                        method_count += 1

                if method_count > 20:
                    self.add_finding(
                        title=f"Too many methods: {class_name} ({method_count} methods)",
                        severity=Severity.MEDIUM,
                        category=Category.ARCHITECTURE,
                        file_path=file_path,
                        line_range=f"{start+1}-{end}",
                        description=f"类 {class_name} 有 {method_count} 个方法",
                        fix_suggestion="使用 Mixin 或拆分为多个类",
                        effort="large",
                    )

    def _check_interface_consistency(self, files: List[str]):
        """检查接口一致性"""
        # 检查是否有抽象基类但没有具体实现
        abc_files = [f for f in files if "abc" in f or "abstract" in f]
        if not abc_files:
            return

        for file_path in abc_files:
            content = self.read_file(file_path)
            if not content:
                continue

            # 检查 ABC 类
            abc_matches = re.finditer(r"class\s+(\w+)\(.*ABC.*\):", content)
            for match in abc_matches:
                class_name = match.group(1)
                # 检查是否有 abstractmethod
                if "@abstractmethod" in content:
                    self.add_finding(
                        title=f"ABC class with abstract methods: {class_name}",
                        severity=Severity.LOW,
                        category=Category.ARCHITECTURE,
                        file_path=file_path,
                        description=f"确认 {class_name} 有对应的实现类",
                        fix_suggestion="确保每个 ABC 都有至少一个具体实现",
                    )

    def _check_dependency_direction(self, files: List[str]):
        """检查依赖方向是否合理（高层不应依赖低层细节）"""
        # 简单检查：是否有 routes 直接操作数据库
        route_files = [f for f in files if "route" in f.lower() or "api" in f.lower() or "view" in f.lower()]
        for file_path in route_files:
            content = self.read_file(file_path)
            if not content:
                continue

            # 检查是否直接执行 SQL
            if "execute(" in content and "SELECT" in content.upper():
                self.add_finding(
                    title="Route layer directly executing SQL queries",
                    severity=Severity.MEDIUM,
                    category=Category.ARCHITECTURE,
                    file_path=file_path,
                    description="路由层不应直接执行 SQL，应通过 Model 或 Service 层",
                    fix_suggestion="将数据库操作移到 Model 或 Repository 层",
                    effort="medium",
                )
