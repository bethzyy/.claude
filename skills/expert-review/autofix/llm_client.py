"""
LLMClient — ZhipuAI GLM 统一调用层

职责：
1. API Key 解析（环境变量 > 配置文件 > fallback）
2. 封装 chat.completions.create，带重试和退避
3. 提供 fix_code() 和 generate_plan() 业务方法
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ============ Prompt 模板 ============

FIX_PROMPT = """你是一个代码修复专家。请根据以下审查发现修复代码。

## 审查发现
- 严重级别: {severity}
- 类别: {category}
- 文件: {file_path}
- 问题描述: {description}
- 修复建议: {fix_suggestion}
- 问题代码片段: {code_snippet}

## 要求
1. 只修复上述问题，不要做其他改动
2. 保持代码风格一致（缩进、命名、注释风格）
3. 不要删除已有的注释或文档字符串
4. 如果修复涉及 import，确保 import 语句正确
5. 保持文件其他部分完全不变

## 原始文件内容
```{language}
{file_content}
```

## 输出格式
只输出修复后的完整文件内容，用 ```{language} ``` 包裹，不要添加任何解释。"""

FIX_MULTI_PROMPT = """你是一个代码修复专家。请根据以下多条审查发现修复同一个文件中的问题。

## 审查发现
{findings_list}

## 要求
1. 逐一修复上述所有问题
2. 保持代码风格一致（缩进、命名、注释风格）
3. 不要删除已有的注释或文档字符串
4. 如果修复涉及 import，确保 import 语句正确
5. 保持文件其他部分完全不变

## 原始文件内容
```{language}
{file_content}
```

## 输出格式
只输出修复后的完整文件内容，用 ```{language} ``` 包裹，不要添加任何解释。"""

PLAN_PROMPT = """你是一个代码改进规划师。请根据以下审查发现制定结构化改进方案。

## 项目信息
- 项目名: {project_name}
- 框架: {framework}
- 文件数: {total_files}

## 审查发现（共 {total} 个）
{findings_summary}

## 要求
1. 按文件分组，同一文件的多个问题合并为一个批次
2. 批次间考虑依赖关系（被依赖的文件先修复，如 utils.py 先于 routes/*.py）
3. 每个批次标注优先级（critical/high/medium）和预估复杂度
4. 只包含有具体修复建议的发现
5. 每个批次的 summary 用一句话概括

## 输出格式
严格输出 JSON，不要添加 markdown 标记或其他文字：
{{
  "batches": [
    {{
      "id": 1,
      "priority": "critical",
      "files": ["path/to/file.py"],
      "findings": ["FND-XXX"],
      "summary": "一句话描述",
      "complexity": "low"
    }}
  ]
}}"""


# ============ LLM Client ============

class LLMClient:
    """ZhipuAI GLM 统一调用层"""

    def __init__(self):
        self.api_key = self._resolve_api_key()
        self._client = None
        self.max_retries = 3

    def _resolve_api_key(self) -> str:
        """API Key 解析链：环境变量 > 配置文件 > fallback"""
        # 1. 环境变量
        key = os.environ.get("ZHIPU_API_KEY", "")
        if key:
            return key

        # 2. 项目 .env 文件（当前工作目录或 skill 目录）
        for env_path in [Path.cwd() / ".env", Path.home() / ".env"]:
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line.startswith("ZHIPU_API_KEY=") and not line.startswith("#"):
                        key = line.split("=", 1)[1].strip().strip("\"'")
                        if key:
                            return key

        # 3. Fallback 配置文件
        fallback_paths = [
            Path("C:/D/CAIE_tool/LLM_Configs/zhipu/apikeyValue2.txt"),
            Path.home() / ".config" / "zhipu" / "apikey.txt",
        ]
        for p in fallback_paths:
            if p.exists():
                key = p.read_text(encoding="utf-8").strip().strip("\n\r")
                if key:
                    return key

        raise RuntimeError(
            "ZHIPU_API_KEY not found. Set environment variable or place key in .env file."
        )

    @property
    def client(self):
        """延迟初始化 ZhipuAI client"""
        if self._client is None:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(api_key=self.api_key)
        return self._client

    def chat(
        self,
        messages: list,
        model: str = "glm-4-flash",
        temperature: float = 0.3,
        max_tokens: int = 8192,
    ) -> str:
        """
        调用 ZhipuAI chat API，带重试和退避。

        Args:
            messages: OpenAI 格式的消息列表
            model: 模型名（glm-4-flash / glm-4）
            temperature: 采样温度
            max_tokens: 最大 token 数

        Returns:
            模型响应文本
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=120,
                    stream=False,
                )
                if response.choices:
                    return response.choices[0].message.content.strip()
                return ""
            except Exception as e:
                last_error = e
                wait = 2 ** attempt + 1
                logger.warning(f"LLM call failed (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(wait)

        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_error}")

    def fix_code(
        self,
        file_content: str,
        file_path: str,
        language: str,
        findings: list,
    ) -> Optional[str]:
        """
        根据审查发现生成修复后的文件内容。

        Args:
            file_content: 原始文件内容
            file_path: 文件路径（用于 prompt 上下文）
            language: 编程语言（python / javascript 等）
            findings: 该文件的 Finding 列表（需要 dict 格式，含 severity/title/description/fix_suggestion/code_snippet）

        Returns:
            修复后的完整文件内容，或 None（失败时）
        """
        if len(findings) == 1:
            f = findings[0]
            prompt = FIX_PROMPT.format(
                severity=f.get("severity", "unknown"),
                category=f.get("category", "unknown"),
                file_path=file_path,
                description=f.get("description", ""),
                fix_suggestion=f.get("fix_suggestion", ""),
                code_snippet=f.get("code_snippet", "N/A"),
                language=language,
                file_content=file_content,
            )
        else:
            findings_list = "\n".join(
                f"- [{i+1}] 严重级别: {f.get('severity', '?')} | "
                f"类别: {f.get('category', '?')} | "
                f"问题: {f.get('title', '?')}\n"
                f"  修复建议: {f.get('fix_suggestion', 'N/A')}\n"
                f"  代码片段: {f.get('code_snippet', 'N/A')}"
                for i, f in enumerate(findings)
            )
            prompt = FIX_MULTI_PROMPT.format(
                findings_list=findings_list,
                language=language,
                file_content=file_content,
            )

        try:
            response = self.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4-flash",
                temperature=0.2,
            )
            return self._extract_code_block(response, language)
        except Exception as e:
            logger.error(f"fix_code failed for {file_path}: {e}")
            return None

    def generate_plan(self, findings: list, project_context: dict) -> Optional[dict]:
        """
        根据审查发现生成结构化改进方案。

        Args:
            findings: Finding dict 列表
            project_context: {"project_name", "framework", "total_files"}

        Returns:
            {"batches": [...]} 或 None
        """
        # 过滤有修复建议的发现
        actionable = [f for f in findings if f.get("fix_suggestion")]
        if not actionable:
            return None

        findings_summary = "\n".join(
            f"- [{f.get('id', '?')}] {f.get('severity', '?')} | "
            f"{f.get('category', '?')} | {f.get('title', '?')}\n"
            f"  文件: {f.get('file_path', '?')}\n"
            f"  修复建议: {f.get('fix_suggestion', 'N/A')}"
            for f in actionable
        )

        prompt = PLAN_PROMPT.format(
            project_name=project_context.get("project_name", "unknown"),
            framework=project_context.get("framework", "unknown"),
            total_files=project_context.get("total_files", 0),
            total=len(actionable),
            findings_summary=findings_summary,
        )

        try:
            response = self.chat(
                messages=[{"role": "user", "content": prompt}],
                model="glm-4-flash",
                temperature=0.3,
            )
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"generate_plan failed: {e}")
            return None

    @staticmethod
    def _extract_code_block(text: str, language: str) -> Optional[str]:
        """从 LLM 响应中提取代码块"""
        # 尝试匹配 ```language ... ```
        pattern = rf"```{re.escape(language)}\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)

        # 尝试匹配通用代码块 ``` ... ```
        match = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1)

        # 如果没有代码块标记，整个响应就是代码
        if text and not text.startswith(("I ", "Here ", "The ", "Below ", "```")):
            return text

        return None

    @staticmethod
    def _parse_json_response(text: str) -> Optional[dict]:
        """从 LLM 响应中提取 JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None
