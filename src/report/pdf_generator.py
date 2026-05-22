"""
PDF报告生成器
功能：生成MTM分析报告PDF文档（完整版）
版本：v2.0 (Day 4交付 - 完整报告+节拍+线平衡+物体检测)
日期：2025-05-21

依赖：ReportLab >=4.0.0

报告内容：
- 视频基本信息
- 动作识别结果
- MTM工时分析
- 效率指标分析
- 节拍时间分析
- 线平衡分析
- 改善建议
- 物体检测结果
- 时间轴图表
"""
import os
from typing import Dict, Optional, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image
)


class PDFReportGenerator:
    """
    PDF报告生成器
    生成完整的MTM分析报告PDF文档
    """

    def __init__(self, output_dir: str = "data/exports"):
        """
        初始化PDF生成器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 页面尺寸
        self.page_width, self.page_height = A4

        # 样式设置
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            leading=20,
            alignment=1,  # 居中
            textColor=colors.darkblue
        ))

        # 副标题样式
        self.styles.add(ParagraphStyle(
            name='ChineseSubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            leading=16,
            textColor=colors.darkblue
        ))

        # 正文样式
        self.styles.add(ParagraphStyle(
            name='ChineseBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12
        ))

    def generate_report(
        self,
        analysis_data: Dict,
        filename: Optional[str] = None
    ) -> str:
        """
        生成完整分析报告

        Args:
            analysis_data: 分析结果数据
            filename: 输出文件名（可选）

        Returns:
            str: 生成的PDF文件路径
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mtm_report_{timestamp}.pdf"

        filepath = os.path.join(self.output_dir, filename)

        # 创建PDF文档
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # 构建文档内容
        story = []

        # 1. 标题页
        story.extend(self._build_title_page(analysis_data))

        # 2. 视频信息
        story.extend(self._build_video_info_section(analysis_data))

        # 3. 动作分析表格
        story.extend(self._build_action_analysis_section(analysis_data))

        # 4. MTM工时分析
        story.extend(self._build_mtm_analysis_section(analysis_data))

        # 5. 效率指标
        story.extend(self._build_efficiency_section(analysis_data))

        # 6. 节拍分析（新增）
        if 'cycle_metrics' in analysis_data:
            story.extend(self._build_cycle_time_section(analysis_data))

        # 7. 线平衡分析（新增）
        if 'line_balance' in analysis_data:
            story.extend(self._build_line_balance_section(analysis_data))

        # 8. 改善建议（新增）
        if 'suggestions' in analysis_data:
            story.extend(self._build_suggestions_section(analysis_data))

        # 9. 物体检测（新增）
        if 'object_detection' in analysis_data:
            story.extend(self._build_object_detection_section(analysis_data))

        # 10. 时间轴图表（如果有）
        if 'timeline_image' in analysis_data:
            story.extend(self._build_timeline_section(analysis_data))

        # 生成PDF
        doc.build(story)

        print(f"[成功] PDF报告已生成: {filepath}")
        return filepath

    def _build_title_page(self, data: Dict) -> List:
        """构建标题页"""
        elements = []

        # 主标题
        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph(
            "工业IE智能体 - MTM动作分析报告",
            self.styles['ChineseTitle']
        ))
        elements.append(Spacer(1, 1*cm))

        # 报告信息
        video_name = data.get('video_info', {}).get('video_name', '未知')
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        info_data = [
            ['视频文件', video_name],
            ['报告时间', report_time],
            ['系统版本', 'v3.0 (工业IE智能体)'],
        ]

        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkgrey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 2*cm))

        return elements

    def _build_video_info_section(self, data: Dict) -> List:
        """构建视频信息部分"""
        elements = []

        elements.append(Paragraph(
            "1. 视频基本信息",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        video_info = data.get('video_info', {})

        info_data = [
            ['项目', '数值', '单位'],
            ['分辨率', f"{video_info.get('width', 0)} x {video_info.get('height', 0)}", '像素'],
            ['帧率', f"{video_info.get('fps', 30):.1f}", 'FPS'],
            ['时长', f"{video_info.get('duration', 0):.2f}", '秒'],
            ['处理帧数', f"{video_info.get('processed_frames', 0)}", '帧'],
        ]

        info_table = Table(info_data, colWidths=[4*cm, 6*cm, 4*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))

        return elements

    def _build_action_analysis_section(self, data: Dict) -> List:
        """构建动作分析部分"""
        elements = []

        elements.append(Paragraph(
            "2. 动作识别结果",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        actions = data.get('actions', [])

        # 动作统计汇总
        action_counts = data.get('mtm_summary', {}).get('action_counts', {})
        total_actions = data.get('mtm_summary', {}).get('total_actions', 0)

        summary_text = f"共检测到 {total_actions} 个动作"
        elements.append(Paragraph(summary_text, self.styles['ChineseBody']))
        elements.append(Spacer(1, 0.3*cm))

        # 动作统计表
        count_data = [['动作类型', '次数', 'TMU']]
        for action_type, count in action_counts.items():
            # 估算TMU
            tmu_map = {'Reach': 15, 'Grasp': 5, 'Move': 18, 'Release': 2, 'Wait': 0}
            tmu = tmu_map.get(action_type, 0) * count
            count_data.append([action_type, str(count), f"{tmu}"])

        count_table = Table(count_data, colWidths=[4*cm, 4*cm, 4*cm])
        count_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(count_table)
        elements.append(Spacer(1, 0.5*cm))

        # 动作序列详情（显示前15个）
        if actions:
            elements.append(Paragraph("动作序列详情（前15个）：", self.styles['ChineseBody']))
            elements.append(Spacer(1, 0.3*cm))

            action_data = [['序号', '动作', '开始(s)', '结束(s)', '时长(s)', 'TMU']]
            for i, action in enumerate(actions[:15]):
                action_data.append([
                    str(i + 1),
                    action.get('type', ''),
                    f"{action.get('start_time', 0):.2f}",
                    f"{action.get('end_time', 0):.2f}",
                    f"{action.get('duration', 0):.2f}",
                    str(action.get('time_tmu', 0))
                ])

            action_table = Table(action_data, colWidths=[1.5*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm])
            action_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            elements.append(action_table)
            elements.append(Spacer(1, 1*cm))

        return elements

    def _build_mtm_analysis_section(self, data: Dict) -> List:
        """构建MTM工时分析部分"""
        elements = []

        elements.append(Paragraph(
            "3. MTM工时分析",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        mtm_summary = data.get('mtm_summary', {})

        # TMU单位说明
        elements.append(Paragraph(
            "TMU时间单位：1 TMU = 0.036秒 = 0.0006分钟",
            self.styles['ChineseBody']
        ))
        elements.append(Spacer(1, 0.3*cm))

        # MTM工时表
        mtm_data = [
            ['项目', 'TMU值', '时间(秒)', '时间(分)'],
            ['正常时间',
             f"{mtm_summary.get('normal_time_tmu', 0):.1f}",
             f"{mtm_summary.get('normal_time_sec', 0):.3f}",
             f"{mtm_summary.get('normal_time_min', 0):.4f}"],
            ['宽放时间',
             f"{mtm_summary.get('allowance_tmu', 0):.1f}",
             f"{mtm_summary.get('allowance_sec', 0):.3f}",
             f"{mtm_summary.get('allowance_min', 0):.4f}"],
            ['宽放率', f"{mtm_summary.get('allowance_rate', 0.15)*100:.0f}%", '-', '-'],
            ['标准工时',
             f"{mtm_summary.get('standard_time_tmu', 0):.1f}",
             f"{mtm_summary.get('standard_time_sec', 0):.3f}",
             f"{mtm_summary.get('standard_time_min', 0):.4f}"],
        ]

        mtm_table = Table(mtm_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        mtm_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('BACKGROUND', (0, 3), (-1, 4), colors.lightyellow),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(mtm_table)
        elements.append(Spacer(1, 1*cm))

        return elements

    def _build_efficiency_section(self, data: Dict) -> List:
        """构建效率指标部分"""
        elements = []

        elements.append(Paragraph(
            "4. 效率指标分析",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        metrics = data.get('metrics', {})

        # 效率指标表
        efficiency_data = [
            ['指标', '数值', '说明'],
            ['实际观测时间', f"{metrics.get('actual_time', 0):.2f}s", '视频实际时长'],
            ['标准工时', f"{metrics.get('standard_time', 0):.2f}s", 'MTM计算的标准工时'],
            ['等待时间', f"{metrics.get('wait_time', 0):.2f}s", 'Wait动作累计时长'],
            ['等待损失率', f"{metrics.get('wait_loss_rate', 0):.1f}%", '等待时间占比'],
            ['动作效率', f"{metrics.get('action_efficiency', 0):.1f}%", '有效动作时间占比'],
            ['周期时间', f"{metrics.get('cycle_time', 0):.2f}s", '标准工时（含宽放）'],
        ]

        efficiency_table = Table(efficiency_data, colWidths=[4*cm, 4*cm, 6*cm])
        efficiency_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(efficiency_table)
        elements.append(Spacer(1, 0.5*cm))

        # 效率评价
        action_eff = metrics.get('action_efficiency', 0)
        if action_eff >= 80:
            evaluation = "动作效率良好，作业流程合理"
            eval_color = colors.green
        elif action_eff >= 60:
            evaluation = "动作效率一般，存在优化空间"
            eval_color = colors.orange
        else:
            evaluation = "动作效率较低，建议优化作业流程"
            eval_color = colors.red

        elements.append(Paragraph(
            f"效率评价：{evaluation}",
            self.styles['ChineseBody']
        ))
        elements.append(Spacer(1, 1*cm))

        return elements

    def _build_timeline_section(self, data: Dict) -> List:
        """构建时间轴图表部分"""
        elements = []

        elements.append(Paragraph(
            "9. 动作时间分布图",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        timeline_path = data.get('timeline_image', '')

        if timeline_path and os.path.exists(timeline_path):
            # 嵌入时间轴图片
            try:
                img = Image(timeline_path, width=14*cm, height=7*cm)
                elements.append(img)
            except Exception as e:
                elements.append(Paragraph(
                    f"[图片加载失败: {e}]",
                    self.styles['ChineseBody']
                ))

        elements.append(Spacer(1, 1*cm))

        return elements

    def _build_cycle_time_section(self, data: Dict) -> List:
        """构建节拍分析部分（新增）"""
        elements = []

        elements.append(Paragraph(
            "5. 节拍时间分析",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        cycle_metrics = data.get('cycle_metrics', {})

        # 节拍指标表
        cycle_data = [
            ['指标', '数值', '说明'],
            ['客户需求节拍', f"{cycle_metrics.get('takt_time', 0):.2f}s", 'Takt Time'],
            ['标准节拍时间', f"{cycle_metrics.get('standard_cycle_time', 0):.2f}s", 'MTM标准'],
            ['实际节拍时间', f"{cycle_metrics.get('actual_cycle_time', 0):.2f}s", '观测时长'],
            ['节拍效率', f"{cycle_metrics.get('cycle_efficiency', 0):.1f}%", '标准/实际'],
            ['节拍利用率', f"{cycle_metrics.get('cycle_utilization', 0):.1f}%", '标准/Takt'],
            ['瓶颈时间', f"{cycle_metrics.get('bottleneck_time', 0):.2f}s", '最长动作'],
        ]

        cycle_table = Table(cycle_data, colWidths=[4*cm, 4*cm, 6*cm])
        cycle_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(cycle_table)
        elements.append(Spacer(1, 1*cm))

        return elements

    def _build_line_balance_section(self, data: Dict) -> List:
        """构建线平衡分析部分（新增）"""
        elements = []

        elements.append(Paragraph(
            "6. 线平衡分析",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        line_balance = data.get('line_balance', {})

        # 线平衡指标表
        balance_data = [
            ['指标', '数值', '说明'],
            ['线平衡率', f"{line_balance.get('line_balance_rate', 0):.1f}%", 'LBR'],
            ['平衡损失率', f"{line_balance.get('balance_loss_rate', 0):.1f}%", '100-LBR'],
            ['瓶颈工位', line_balance.get('bottleneck_station', 'N/A'), '最长节拍'],
            ['瓶颈时间', f"{line_balance.get('bottleneck_time', 0):.2f}s", '瓶颈节拍'],
            ['理论最小人数', str(line_balance.get('theoretical_min_workers', 1)), '理论需求'],
            ['实际人数', str(line_balance.get('actual_workers', 1)), '当前配置'],
            ['人员效率', f"{line_balance.get('worker_efficiency', 0):.1f}%", '理论/实际'],
        ]

        balance_table = Table(balance_data, colWidths=[4*cm, 4*cm, 6*cm])
        balance_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(balance_table)
        elements.append(Spacer(1, 1*cm))

        return elements

    def _build_suggestions_section(self, data: Dict) -> List:
        """构建改善建议部分（新增）"""
        elements = []

        elements.append(Paragraph(
            "7. 改善建议",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        suggestions = data.get('suggestions', [])

        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                elements.append(Paragraph(
                    f"{i}. {suggestion}",
                    self.styles['ChineseBody']
                ))
                elements.append(Spacer(1, 0.3*cm))
        else:
            elements.append(Paragraph(
                "暂无改善建议",
                self.styles['ChineseBody']
            ))

        elements.append(Spacer(1, 1*cm))

        return elements

    def _build_object_detection_section(self, data: Dict) -> List:
        """构建物体检测部分（新增）"""
        elements = []

        elements.append(Paragraph(
            "8. 物体检测结果",
            self.styles['ChineseSubTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))

        object_detection = data.get('object_detection', {})

        # 物体统计表
        class_totals = object_detection.get('class_totals', {})
        if class_totals:
            obj_data = [['物体类别', '检测次数']]
            for class_name, count in class_totals.items():
                obj_data.append([class_name, str(count)])

            obj_table = Table(obj_data, colWidths=[6*cm, 6*cm])
            obj_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightsalmon),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            elements.append(obj_table)
        else:
            elements.append(Paragraph(
                "未检测到物体或物体检测模块未启用",
                self.styles['ChineseBody']
            ))

        elements.append(Spacer(1, 1*cm))

        return elements


def generate_pdf_report(
    analysis_data: Dict,
    output_path: str = "data/exports"
) -> str:
    """
    快速生成PDF报告（便捷函数）

    Args:
        analysis_data: 分析结果数据
        output_path: 输出目录

    Returns:
        str: PDF文件路径
    """
    generator = PDFReportGenerator(output_dir=output_path)
    return generator.generate_report(analysis_data)