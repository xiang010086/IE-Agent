from __future__ import annotations

from typing import Any

# action verdict -> (中文标签, 引用理论) for the fallback narrative
_ACTION_LABEL = {
    "add_worker": ("加人", "节拍时间(Takt)理论 / 劳动定额"),
    "split_task": ("拆分工序", "ECRS改善四原则 / 产线平衡"),
    "swap_worker": ("换人/调岗", "人因工程 / 动作经济原则"),
    "ok": ("维持现状", "标准作业 / 持续改善"),
}


class ImprovementRuleEngine:
    """Rule-based fallback that always returns useful IE improvement advice."""

    def generate_suggestions(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        line_metrics = analysis_data.get("line_metrics", {})
        bottleneck = line_metrics.get("bottleneck") or {}
        lbr_current = float(line_metrics.get("lbr", 0.0))
        lbr_target = float(line_metrics.get("lbr_target", 85.0))
        max_cycle_time = float(line_metrics.get("max_cycle_time", 0.0))
        total_wait_time = float(line_metrics.get("total_wait_time", 0.0))
        target_cycle = round(max_cycle_time * 0.85, 2) if max_cycle_time else 0.0

        bottleneck_name = bottleneck.get("station_name", "待识别工位")
        bottleneck_cycle = float(bottleneck.get("cycle_time", max_cycle_time or 0.0))

        return {
            "source": "rule_fallback",
            "improvement_target": {
                "lbr_target": lbr_target,
                "lbr_current": round(lbr_current, 1),
                "lbr_gap": round(lbr_target - lbr_current, 1),
                "cycle_time_target": target_cycle,
                "capacity_target": "优先将瓶颈节拍降低10%-15%，再推进全线平衡。",
            },
            "bottleneck_suggestions": [
                {
                    "station": bottleneck_name,
                    "priority": "最高",
                    "problem": f"当前瓶颈节拍约 {bottleneck_cycle:.1f} 秒，直接限制整线产能。",
                    "suggestions": [
                        "拆分瓶颈工位中过长的动作，把可并行动作转移给负荷较低工位。",
                        "优化物料摆放，将高频取放物料放入最佳伸手区，减少移动和寻找时间。",
                        "把重复动作标准化为作业指导书，减少人员差异造成的节拍波动。",
                        "评估夹具、定位治具或半自动设备，优先替代低价值重复动作。",
                    ],
                    "expected_effect": f"瓶颈节拍预计降低 {bottleneck_cycle * 0.12:.1f}-{bottleneck_cycle * 0.18:.1f} 秒。",
                }
            ],
            "system_suggestions": [
                {
                    "type": "线平衡优化",
                    "suggestion": "按各工位节拍重新分配任务，让工位负荷靠近瓶颈工位的85%-95%。",
                    "expected_effect": f"LBR从 {lbr_current:.1f}% 向 {min(lbr_target, max(lbr_current + 5, 80)):.1f}% 提升。",
                },
                {
                    "type": "等待时间优化",
                    "suggestion": "在瓶颈前后设置小缓冲区，并明确上下游补料和交接规则。",
                    "expected_effect": f"总等待时间预计降低约 {total_wait_time * 0.3:.1f} 秒。",
                },
                {
                    "type": "标准作业",
                    "suggestion": "将最佳动作顺序固化为标准作业组合票，培训后再复测节拍。",
                    "expected_effect": "降低节拍波动，提升改善效果的可复制性。",
                },
            ],
            "roi_estimate": {
                "capacity_gain_percent": 12.0,
                "payback_period": "1-3个月，取决于治具/设备投入规模",
                "assumption": "按瓶颈节拍改善12%、等待时间降低30%进行保守估算。",
            },
            "implementation_path": {
                "phase1": {
                    "duration": "1-2周",
                    "actions": ["瓶颈工位动作拆解", "物料摆放优化", "标准作业确认"],
                },
                "phase2": {
                    "duration": "1-2个月",
                    "actions": ["工位任务重分配", "夹具/辅助工具导入", "节拍复测"],
                },
                "phase3": {
                    "duration": "3-6个月",
                    "actions": ["自动化方案评估", "持续改善看板", "跨产线复制"],
                },
            },
        }

    def generate_narrative(
        self,
        project_data: dict[str, Any],
        analysis_data: dict[str, Any],
        knowledge_context: str = "",
    ) -> dict[str, Any]:
        """Deterministic fallback for the report narrative (same schema as DeepSeek).

        All numbers come straight from line_metrics / takt_analysis — nothing is
        invented — so the report is complete and number-faithful even with AI off.
        """
        line = analysis_data.get("line_metrics", {}) or {}
        takt = analysis_data.get("takt_analysis", {}) or {}
        actions = analysis_data.get("action_recommendations", []) or []
        bottleneck = line.get("bottleneck") or {}

        station_count = line.get("station_count", 0)
        lbr = line.get("lbr", 0.0)
        lbr_target = line.get("lbr_target", 85.0)
        bn_name = bottleneck.get("station_name", "待识别工位")
        bn_cycle = bottleneck.get("cycle_time", line.get("max_cycle_time", 0.0))
        capacity = line.get("estimated_hourly_capacity", 0.0)
        total_wait = line.get("total_wait_time", 0.0)

        headline = actions[0] if actions else {"action": "ok", "reason": ""}
        head_label = _ACTION_LABEL.get(headline.get("action"), ("维持现状", "标准作业"))[0]

        # recommendations mapped from the deterministic action verdicts
        recommendations = []
        for a in actions:
            label, theory = _ACTION_LABEL.get(a.get("action"), ("改善", "工业工程方法论"))
            recommendations.append({
                "title": f"{label}（{a.get('target', '产线')}）",
                "rationale": a.get("reason", ""),
                "cited_theory": theory,
                "expected_effect": "改善产线平衡/产能匹配，降低单件人工与等待损失。",
            })

        # takt interpretation
        if takt.get("skipped"):
            takt_text = "未提供必要参数（班次/需求/有效率），本次跳过节拍与人力测算。"
        else:
            cap = "充足" if takt.get("capacity_status") == "ok" else "不足"
            takt_text = (
                f"客户节拍 Takt 约 {takt.get('takt_time_s')} 秒，瓶颈节拍 {takt.get('bottleneck_cycle_s')} 秒，"
                f"产能{cap}；按标准工时测算需求人数 {takt.get('required_workers')} 人，"
                f"现有 {takt.get('current_workers')} 人。"
            )

        cited = []
        for a in actions:
            theory = _ACTION_LABEL.get(a.get("action"), (None, None))[1]
            if theory and theory not in cited:
                cited.append(theory)

        return {
            "source": "rule_fallback",
            "executive_summary": (
                f"本产线共 {station_count} 个工位，产线平衡率 LBR {lbr}%（目标 {lbr_target}%），"
                f"瓶颈工位为「{bn_name}」（节拍 {bn_cycle} 秒），估算小时产能 {capacity} 件。"
                f"核心改善决策：{head_label}。"
            ),
            "key_findings": [
                f"产线平衡率 LBR {lbr}%，目标 {lbr_target}%。",
                f"瓶颈工位「{bn_name}」节拍 {bn_cycle} 秒，限制整线产能。",
                f"总等待时间约 {total_wait} 秒。",
                takt_text,
            ],
            "per_section_commentary": {
                "overview": f"全线 {station_count} 工位，LBR {lbr}%（目标 {lbr_target}%），瓶颈「{bn_name}」。",
                "stations": "各工位节拍/有效时间/等待详见明细表；效率偏低工位为换人/培训重点。",
                "work_time": "工时由 MTM 正常时间叠加宽放得到标准工时，作为人力与产能测算基准。",
                "takt": takt_text,
                "efficiency": f"瓶颈「{bn_name}」决定整线产能，应优先改善。",
            },
            "bottleneck_root_cause": (
                f"瓶颈工位「{bn_name}」节拍 {bn_cycle} 秒为全线最长，根因通常是工序集中、"
                f"动作冗余或上下游节拍不匹配，应按 ECRS 拆分/重排其工序。"
            ),
            "takt_interpretation": takt_text,
            "recommendations": recommendations or [{
                "title": "维持现状", "rationale": "未见明显瓶颈或产能问题。",
                "cited_theory": "标准作业 / 持续改善", "expected_effect": "保持稳定并持续改善。",
            }],
            "implementation_roadmap": {
                "phase1": {"duration": "1-2周", "actions": ["瓶颈工位动作拆解", "物料摆放优化", "标准作业确认"]},
                "phase2": {"duration": "1-2个月", "actions": ["工位任务重分配", "夹具/辅助工具导入", "节拍复测"]},
                "phase3": {"duration": "3-6个月", "actions": ["自动化方案评估", "持续改善看板", "跨产线复制"]},
            },
            "conclusion": (
                f"建议优先执行「{head_label}」，结合产线平衡与标准作业持续改善，"
                f"使各工位负荷趋近瓶颈的 85%-95%，逐步达成 LBR 目标 {lbr_target}%。"
            ),
            "cited_theories": cited or ["产线平衡", "标准作业"],
        }
