from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import request

from .storage import read_structured

# src/core/llm_client.py -> src/core -> src -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]


class LLMClient:
    """Optional cloud LLM client.

    It returns None on every failure so the caller can fall back to rules.
    """

    API_CONFIGS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
            "env": "DEEPSEEK_API_KEY",
        },
        "kimi": {
            "base_url": "https://api.moonshot.cn/v1/chat/completions",
            "model": "moonshot-v1-8k",
            "env": "KIMI_API_KEY",
        },
        "qwen": {
            # DashScope's OpenAI-compatible endpoint: same chat-completions
            # request/response shape as deepseek/kimi, so the parsing below works.
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "model": "qwen-max",
            "env": "QWEN_API_KEY",
        },
    }

    def __init__(
        self,
        api_provider: str = "deepseek",
        api_key: str | None = None,
        config_path: str | Path = "config/api_config.yaml",
    ) -> None:
        if api_provider not in self.API_CONFIGS:
            raise ValueError(f"Unsupported API provider: {api_provider}")
        self.provider = api_provider
        self.config = self.API_CONFIGS[api_provider]
        # Resolve a relative config path against the repo root so it works no
        # matter the CWD (streamlit is launched from app/, not the repo root).
        cp = Path(config_path)
        if not cp.is_absolute():
            cp = _REPO_ROOT / cp
        self.api_key = api_key or self._load_api_key(cp)

    def generate_improvement(
        self,
        project_data: dict[str, Any],
        analysis_data: dict[str, Any],
        timeout: int = 10,
    ) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        prompt = self._build_prompt(project_data, analysis_data)
        payload = {
            "model": self.config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名资深工业工程IE顾问，请输出严格JSON，不要使用Markdown。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 2000,
        }

        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = request.Request(
                self.config["base_url"],
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            parsed = self._parse_response(content)
            if parsed:
                parsed["source"] = f"ai_{self.provider}"
            return parsed
        except Exception:
            return None

    def generate_report_narrative(
        self,
        project_data: dict[str, Any],
        analysis_data: dict[str, Any],
        knowledge_context: str = "",
        timeout: int = 30,
    ) -> dict[str, Any] | None:
        """Write the report's ANALYSIS PROSE. Numbers are passed in, never invented.

        Returns the narrative JSON dict (schema in ``_build_narrative_prompt``) or
        ``None`` on any failure, so the caller falls back to the rule engine.
        """
        if not self.api_key:
            return None

        prompt = self._build_narrative_prompt(project_data, analysis_data, knowledge_context)
        payload = {
            "model": self.config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名资深工业工程(IE)顾问，负责撰写正式产线改善报告的分析文字。"
                               "严格输出JSON，不要使用Markdown。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 3000,
        }
        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = request.Request(
                self.config["base_url"],
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            parsed = self._parse_response(content)
            if parsed:
                parsed["source"] = f"ai_{self.provider}"
            return parsed
        except Exception:
            return None

    def _build_narrative_prompt(
        self,
        project_data: dict[str, Any],
        analysis_data: dict[str, Any],
        knowledge_context: str,
    ) -> str:
        # Compact per-station payload: numbers only (no timeline/breakdown) to save tokens.
        stations = []
        for s in analysis_data.get("stations", []):
            m = s.get("cycle_time_metrics", {}) or {}
            mm = s.get("mtm_summary", {}) or {}
            stations.append({
                "name": s.get("station_name"),
                "mode": s.get("analysis_mode"),
                "cycle_s": m.get("total_cycle_time"),
                "effective_s": m.get("effective_time"),
                "wait_s": m.get("wait_time"),
                "efficiency_pct": m.get("efficiency"),
                "standard_time_s": mm.get("standard_time"),
                "action_count": mm.get("action_count"),
                "tmu": mm.get("total_tmus"),
            })
        compact = {
            "project": project_data,
            "line_metrics": analysis_data.get("line_metrics", {}),
            "takt_analysis": analysis_data.get("takt_analysis", {}),
            "action_recommendations": analysis_data.get("action_recommendations", []),
            "stations": stations,
        }
        schema = (
            '{"executive_summary":"string",'
            '"key_findings":["string"],'
            '"per_section_commentary":{"overview":"string","stations":"string",'
            '"work_time":"string","takt":"string","efficiency":"string"},'
            '"bottleneck_root_cause":"string",'
            '"takt_interpretation":"string",'
            '"recommendations":[{"title":"string","rationale":"string",'
            '"cited_theory":"string","expected_effect":"string"}],'
            '"implementation_roadmap":{"phase1":{"duration":"string","actions":["string"]},'
            '"phase2":{"duration":"string","actions":["string"]},'
            '"phase3":{"duration":"string","actions":["string"]}},'
            '"conclusion":"string","cited_theories":["string"]}'
        )
        return (
            "请基于以下真实产线分析数据，撰写一份正式工业IE改善报告的【分析文字】。\n"
            "硬性要求：\n"
            "1. 所有数字（节拍、效率、LBR、TMU、标准工时、Takt、需求人数等）均已由系统精确计算，"
            "你只能引用，严禁创造或修改任何数字；提及数值必须与给定数据完全一致。\n"
            "2. 报告核心是给工厂明确的行动决策：加人 / 换人(调岗) / 拆分工序。"
            "请基于 action_recommendations（已给出确定性结论与理由）展开论证，不要推翻其结论。\n"
            "3. 若数据缺失（如 takt_analysis.skipped=true），请写『未提供必要参数，相关分析略』，不要编造。\n"
            "4. 必须引用下方[IE理论依据]作为论证支撑，recommendations[].cited_theory 填所引用的理论名称。\n"
            f"5. 必须严格返回如下JSON结构（不要Markdown、不要多余文字）：\n{schema}\n\n"
            f"[IE理论依据]\n{knowledge_context}\n\n"
            f"[分析数据]\n{json.dumps(compact, ensure_ascii=False)}"
        )

    def _load_api_key(self, config_path: str | Path) -> str | None:
        env_key = os.getenv(self.config["env"])
        if env_key:
            return env_key

        config_file = Path(config_path)
        if not config_file.exists():
            return None
        config = read_structured(config_file, {}) or {}
        return (config.get("api_keys", {}) or {}).get(self.provider)

    def _build_prompt(self, project_data: dict[str, Any], analysis_data: dict[str, Any]) -> str:
        compact = {
            "project": project_data,
            "line_metrics": analysis_data.get("line_metrics", {}),
            "stations": analysis_data.get("stations", []),
        }
        return (
            "请基于以下产线分析数据生成工业IE改善方案。"
            "必须返回JSON，字段包含 improvement_target, bottleneck_suggestions, "
            "system_suggestions, roi_estimate, implementation_path。\n"
            f"{json.dumps(compact, ensure_ascii=False)}"
        )

    def _parse_response(self, content: str) -> dict[str, Any] | None:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1)
        try:
            value = json.loads(cleaned)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None


def generate_improvement_suggestions(
    project_data: dict[str, Any],
    analysis_data: dict[str, Any],
    use_ai: bool = True,
    provider: str = "deepseek",
) -> dict[str, Any]:
    if use_ai:
        try:
            ai_result = LLMClient(provider).generate_improvement(project_data, analysis_data)
            if ai_result:
                return ai_result
        except Exception:
            pass

    from .improvement_rules import ImprovementRuleEngine

    return ImprovementRuleEngine().generate_suggestions(analysis_data)


def generate_report_narrative(
    project_data: dict[str, Any],
    analysis_data: dict[str, Any],
    knowledge_context: str = "",
    use_ai: bool = True,
    provider: str = "deepseek",
) -> dict[str, Any]:
    """Return the report narrative dict. AI if available, else rule-engine fallback.

    The returned dict always carries the full narrative schema and a ``source``
    field ("ai_<provider>" or "rule_fallback").
    """
    if use_ai:
        try:
            result = LLMClient(provider).generate_report_narrative(
                project_data, analysis_data, knowledge_context
            )
            if result:
                result.setdefault("source", f"ai_{provider}")
                return result
        except Exception:
            pass

    from .improvement_rules import ImprovementRuleEngine

    return ImprovementRuleEngine().generate_narrative(
        project_data, analysis_data, knowledge_context
    )
