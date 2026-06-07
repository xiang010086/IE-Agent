from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.core.improvement_rules import ImprovementRuleEngine
from src.core.knowledge import build_knowledge_context, detect_signals, select_entries
from src.core.llm_client import generate_improvement_suggestions, generate_report_narrative
from src.core.project_manager import ProjectManager
from src.core.storage import write_json
from src.utils.visualization import render_timeline_png


class LineReportGenerator:
    """Generate CSV and PDF reports for one production-line project."""

    def __init__(self, project_manager: ProjectManager | None = None) -> None:
        self.project_manager = project_manager or ProjectManager()
        self.font_name = self._register_chinese_font()

    def generate(
        self,
        project_id: str,
        use_ai: bool = False,
        provider: str = "deepseek",
    ) -> dict[str, str]:
        config = self.project_manager.load_config(project_id)
        summary = self.project_manager.load_summary(project_id)
        if not summary.get("stations"):
            summary = {
                "project": config["project"],
                "target": config.get("target", {}),
                "line_metrics": {},
                "stations": self.project_manager.load_station_results(project_id),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }

        # Kept for the appendix / CSV (ROI etc.) and backward compatibility.
        suggestions = generate_improvement_suggestions(
            config.get("project", {}),
            summary,
            use_ai=use_ai,
            provider=provider,
        )
        if not suggestions:
            suggestions = ImprovementRuleEngine().generate_suggestions(summary)

        # IE-theory-grounded narrative: numbers in / prose out. Pick relevant
        # theory by analysis signals, inject as grounding, let DeepSeek write the
        # analysis (falls back to the rule engine narrative if AI is off/down).
        signals = detect_signals(
            summary.get("line_metrics", {}),
            summary.get("takt_analysis", {}),
            summary.get("stations", []),
        )
        entries = select_entries(signals)
        knowledge_context = build_knowledge_context(entries)
        narrative = generate_report_narrative(
            {**config.get("project", {}), "project_info": config.get("project_info", {})},
            summary,
            knowledge_context,
            use_ai=use_ai,
            provider=provider,
        )

        paths = self.project_manager.get_paths(project_id)
        export_payload = {
            **summary,
            "improvement_suggestions": suggestions,
            "report_narrative": narrative,
            "knowledge_used": [e.get("id") for e in entries],
            "report_generated_at": datetime.now().isoformat(timespec="seconds"),
        }
        write_json(paths.exports / "comprehensive_report.json", export_payload)
        csv_path = self.export_csv(project_id, export_payload)
        timeline_images = self._render_timelines(project_id, summary.get("stations", []))
        pdf_path = self.export_pdf(project_id, export_payload, timeline_images)
        return {
            "csv": str(csv_path),
            "pdf": str(pdf_path),
            "json": str(paths.exports / "comprehensive_report.json"),
            "narrative_source": narrative.get("source", ""),
        }

    def _render_timelines(self, project_id: str, stations: list[dict[str, Any]]) -> dict[str, str]:
        """Render each station's action timeline to a PNG. Returns station_id -> path."""
        paths = self.project_manager.get_paths(project_id)
        images: dict[str, str] = {}
        for station in stations:
            timeline = station.get("action_timeline") or []
            total = (station.get("cycle_time_metrics", {}) or {}).get("total_cycle_time")
            out = paths.exports / f"timeline_{station.get('station_id')}.png"
            result = render_timeline_png(timeline, out, total_seconds=total)
            if result is not None:
                images[station.get("station_id")] = str(result)
        return images

    def export_csv(self, project_id: str, payload: dict[str, Any]) -> Path:
        paths = self.project_manager.get_paths(project_id)
        csv_path = paths.exports / "data_export.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["工位ID", "工位名称", "节拍时间(s)", "有效时间(s)", "等待时间(s)", "效率(%)", "动作数", "TMU"])
            for station in payload.get("stations", []):
                metrics = station.get("cycle_time_metrics", {})
                mtm = station.get("mtm_summary", {})
                writer.writerow(
                    [
                        station.get("station_id"),
                        station.get("station_name"),
                        metrics.get("total_cycle_time"),
                        metrics.get("effective_time"),
                        metrics.get("wait_time"),
                        metrics.get("efficiency"),
                        mtm.get("action_count"),
                        mtm.get("total_tmus"),
                    ]
                )
        return csv_path

    def export_pdf(
        self,
        project_id: str,
        payload: dict[str, Any],
        timeline_images: dict[str, str] | None = None,
    ) -> Path:
        paths = self.project_manager.get_paths(project_id)
        pdf_path = paths.exports / "comprehensive_report.pdf"
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="产线IE动作分析与改善报告",
        )
        story = self._build_story(payload, timeline_images or {})
        doc.build(story)
        return pdf_path

    # -- story helpers --------------------------------------------------

    def _image(self, path: str | None, max_width_mm: float = 165.0):
        """ReportLab Image scaled to page width, preserving aspect; None on failure."""
        if not path:
            return None
        try:
            iw, ih = ImageReader(str(path)).getSize()
            w = max_width_mm * mm
            h = w * ih / iw if iw else 30 * mm
            return Image(str(path), width=w, height=h)
        except Exception:
            return None

    @staticmethod
    def _narr(narrative: dict[str, Any], *keys: str, fallback: str = "") -> str:
        """Safely pull nested narrative prose; fallback if missing/empty."""
        cur: Any = narrative
        for key in keys:
            if not isinstance(cur, dict):
                return fallback
            cur = cur.get(key)
        return cur if isinstance(cur, str) and cur.strip() else fallback

    def _build_story(self, payload: dict[str, Any], timeline_images: dict[str, str]) -> list[Any]:
        S = self._styles()
        project = payload.get("project", {})
        pinfo = payload.get("project_info", {}) or {}
        line = payload.get("line_metrics", {})
        takt = payload.get("takt_analysis", {}) or {}
        actions = payload.get("action_recommendations", []) or []
        narrative = payload.get("report_narrative", {}) or {}
        suggestions = payload.get("improvement_suggestions", {}) or {}
        stations = payload.get("stations", [])
        story: list[Any] = []

        action_cn = {"add_worker": "加人", "split_task": "拆分工序",
                     "swap_worker": "换人/调岗", "ok": "维持现状"}
        mode_cn = {"vision_handsyolo": "真实识别", "heuristic_estimate": "时长估算", "error": "失败"}

        # ---- Cover ----
        story.append(Paragraph("产线IE动作分析与改善报告", S["TitleCN"]))
        story.append(Spacer(1, 6))
        src = str(narrative.get("source", ""))
        src_cn = "AI 生成（DeepSeek）" if src.startswith("ai_") else "规则引擎生成（AI 未启用/不可用）"
        gen_at = payload.get("report_generated_at", "")
        cover = [
            ["项目", "信息"],
            ["项目名称", project.get("name", "")],
            ["客户/部门", project.get("client", "") or pinfo.get("industry", "")],
            ["产品 / 产线", f"{pinfo.get('product') or '-'} / {pinfo.get('line_name') or '-'}"],
            ["分析人员", pinfo.get("analyst", "") or "-"],
            ["报告日期", pinfo.get("report_date", "") or gen_at[:10]],
            ["生成时间", gen_at],
            ["分析叙述来源", src_cn],
        ]
        story.append(self._table(cover, [55 * mm, 110 * mm]))
        story.append(Spacer(1, 10))

        # ---- 1. Executive summary ----
        story.append(Paragraph("一、执行摘要", S["HeadingCN"]))
        story.append(Paragraph(self._narr(narrative, "executive_summary", fallback="（无摘要）"), S["BodyCN"]))
        for finding in narrative.get("key_findings", []) or []:
            story.append(Paragraph(f"• {finding}", S["BodyCN"]))
        story.append(Spacer(1, 8))

        # ---- 2. Action verdict (the whole point) ----
        story.append(Paragraph("二、改善决策（加人 / 换人 / 拆分工序）", S["HeadingCN"]))
        if actions:
            for a in actions:
                lbl = action_cn.get(a.get("action"), a.get("action", ""))
                story.append(Paragraph(f"<b>➤ {lbl}</b>（{a.get('target', '')}）：{a.get('reason', '')}", S["BodyCN"]))
        else:
            story.append(Paragraph("暂无明确决策建议。", S["BodyCN"]))
        story.append(Spacer(1, 8))

        # ---- 3. Line overview ----
        story.append(Paragraph("三、产线总览", S["HeadingCN"]))
        story.append(self._table([
            ["指标", "数值"],
            ["工位数量", line.get("station_count", 0)],
            ["LBR 线平衡率", f"{line.get('lbr', 0)}%"],
            ["目标 LBR", f"{line.get('lbr_target', 85)}%"],
            ["最大节拍", f"{line.get('max_cycle_time', 0)} 秒"],
            ["平均节拍", f"{line.get('average_cycle_time', 0)} 秒"],
            ["总等待时间", f"{line.get('total_wait_time', 0)} 秒"],
            ["估算小时产能", f"{line.get('estimated_hourly_capacity', 0)} 件/小时"],
        ], [60 * mm, 90 * mm]))
        bn = line.get("bottleneck") or {}
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"瓶颈工位：{bn.get('station_name', '暂无')}，节拍 {bn.get('cycle_time', 0)} 秒。", S["BodyCN"]))
        ov = self._narr(narrative, "per_section_commentary", "overview")
        if ov:
            story.append(Paragraph(ov, S["BodyCN"]))
        story.append(PageBreak())

        # ---- 4. Per-station detail + timeline images ----
        story.append(Paragraph("四、逐工位明细", S["HeadingCN"]))
        st_table = [["工位", "节拍(s)", "有效(s)", "等待(s)", "效率(%)", "标准工时(s)", "动作数", "模式"]]
        for s in stations:
            m = s.get("cycle_time_metrics", {}) or {}
            mt = s.get("mtm_summary", {}) or {}
            st_table.append([
                s.get("station_name"), m.get("total_cycle_time"), m.get("effective_time"),
                m.get("wait_time"), m.get("efficiency"), mt.get("standard_time"),
                mt.get("action_count"), mode_cn.get(s.get("analysis_mode"), "-"),
            ])
        story.append(self._table(st_table, [30 * mm, 17 * mm, 17 * mm, 17 * mm, 15 * mm, 22 * mm, 15 * mm, 20 * mm]))
        sc = self._narr(narrative, "per_section_commentary", "stations")
        if sc:
            story.append(Paragraph(sc, S["BodyCN"]))
        for s in stations:
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"工位「{s.get('station_name')}」动作时间轴：", S["BodyCN"]))
            img = self._image(timeline_images.get(s.get("station_id")))
            story.append(img if img is not None
                         else Paragraph("（估算模式或无有效动作，未生成时间轴）", S["BodyCN"]))
        story.append(PageBreak())

        # ---- 5. Work time ----
        story.append(Paragraph("五、工时分析", S["HeadingCN"]))
        wt = self._narr(narrative, "per_section_commentary", "work_time")
        if wt:
            story.append(Paragraph(wt, S["BodyCN"]))
        story.append(Paragraph(
            "说明：标准工时 = 有效作业时间 × 宽放系数；TMU 为 MTM 预定动作时间单位（1 TMU = 0.036 秒）。",
            S["BodyCN"]))

        # ---- 6. Takt ----
        story.append(Spacer(1, 8))
        story.append(Paragraph("六、节拍(Takt)与产能分析", S["HeadingCN"]))
        if takt.get("skipped"):
            story.append(Paragraph(takt.get("skip_reason") or "未提供节拍参数，跳过节拍分析。", S["BodyCN"]))
        else:
            cap = "充足" if takt.get("capacity_status") == "ok" else "不足"
            story.append(self._table([
                ["指标", "数值"],
                ["客户节拍 Takt", f"{takt.get('takt_time_s')} 秒"],
                ["瓶颈节拍", f"{takt.get('bottleneck_cycle_s')} 秒"],
                ["产能判定", cap],
                ["每班可用工时", f"{takt.get('available_time_s')} 秒"],
                ["需求人数", f"{takt.get('required_workers')} 人"],
                ["现有人数", f"{takt.get('current_workers')} 人"],
                ["人数缺口", f"{takt.get('worker_gap')} 人"],
            ], [60 * mm, 90 * mm]))
        ti = self._narr(narrative, "takt_interpretation")
        if ti:
            story.append(Paragraph(ti, S["BodyCN"]))

        # ---- 7. Bottleneck / efficiency diagnosis ----
        story.append(Spacer(1, 8))
        story.append(Paragraph("七、瓶颈与效率诊断", S["HeadingCN"]))
        story.append(Paragraph(self._narr(narrative, "bottleneck_root_cause", fallback="（无）"), S["BodyCN"]))
        ef = self._narr(narrative, "per_section_commentary", "efficiency")
        if ef:
            story.append(Paragraph(ef, S["BodyCN"]))
        story.append(PageBreak())

        # ---- 8. Recommendations (with cited theory) ----
        story.append(Paragraph("八、改善建议（含理论依据）", S["HeadingCN"]))
        for r in narrative.get("recommendations", []) or []:
            story.append(Paragraph(f"<b>{r.get('title', '')}</b>", S["BodyCN"]))
            if r.get("rationale"):
                story.append(Paragraph(f"依据：{r.get('rationale')}", S["BodyCN"]))
            if r.get("cited_theory"):
                story.append(Paragraph(f"理论支撑：{r.get('cited_theory')}", S["BodyCN"]))
            if r.get("expected_effect"):
                story.append(Paragraph(f"预期效果：{r.get('expected_effect')}", S["BodyCN"]))
            story.append(Spacer(1, 4))

        # ---- 9. Roadmap ----
        story.append(Spacer(1, 6))
        story.append(Paragraph("九、实施路线图", S["HeadingCN"]))
        roadmap = narrative.get("implementation_roadmap", {}) or {}
        ph_cn = {"phase1": "第一阶段", "phase2": "第二阶段", "phase3": "第三阶段"}
        for k in ("phase1", "phase2", "phase3"):
            ph = roadmap.get(k, {}) or {}
            acts = "、".join(ph.get("actions", []) or [])
            story.append(Paragraph(f"{ph_cn[k]}（{ph.get('duration', '')}）：{acts}", S["BodyCN"]))

        # ---- 10. Conclusion ----
        story.append(Spacer(1, 6))
        story.append(Paragraph("十、结论", S["HeadingCN"]))
        story.append(Paragraph(self._narr(narrative, "conclusion", fallback="（无）"), S["BodyCN"]))

        # ---- Appendix ----
        story.append(Spacer(1, 8))
        story.append(Paragraph("附录", S["HeadingCN"]))
        cited = narrative.get("cited_theories", []) or []
        if cited:
            story.append(Paragraph("引用理论：" + "、".join(str(c) for c in cited), S["BodyCN"]))
        roi = suggestions.get("roi_estimate", {}) or {}
        if roi:
            story.append(Paragraph(
                f"ROI 保守估算：产能提升约 {roi.get('capacity_gain_percent', 0)}%，"
                f"回收期 {roi.get('payback_period', '待测算')}。", S["BodyCN"]))
        story.append(Paragraph(
            "免责声明：节拍/标准工时基于视频时长与 MTM 估算，动作识别为 v1（精度待迭代）；"
            "数值供改善决策参考，建议结合现场复核。", S["BodyCN"]))

        # ---- Sign-off ----
        story.append(Spacer(1, 16))
        story.append(Paragraph(
            f"分析：{pinfo.get('analyst') or '____________'}　　复核：____________　　"
            f"批准：____________　　日期：{pinfo.get('report_date') or '____________'}", S["BodyCN"]))
        return story

    def _register_chinese_font(self) -> str:
        font_name = "STSong-Light"
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))
            return font_name
        except Exception:
            return "Helvetica"

    def _styles(self) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "TitleCN": ParagraphStyle(
                "TitleCN",
                parent=base["Title"],
                fontName=self.font_name,
                fontSize=18,
                leading=24,
                alignment=1,
            ),
            "HeadingCN": ParagraphStyle(
                "HeadingCN",
                parent=base["Heading2"],
                fontName=self.font_name,
                fontSize=13,
                leading=18,
                spaceAfter=6,
            ),
            "BodyCN": ParagraphStyle(
                "BodyCN",
                parent=base["BodyText"],
                fontName=self.font_name,
                fontSize=10,
                leading=15,
            ),
        }

    def _table(self, data: list[list[Any]], col_widths: list[float]) -> Table:
        # Coerce None/numbers to strings (keep flowables like Paragraph as-is).
        safe = [
            [c if hasattr(c, "wrap") else ("-" if c is None else str(c)) for c in row]
            for row in data
        ]
        table = Table(safe, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7B7B7")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6F8")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return table
