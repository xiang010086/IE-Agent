"""
CSV数据导出器
功能：导出动作序列、MTM工时数据到CSV文件
版本：v1.0 (Day -2交付)
日期：2025-05-21
"""
import csv
import os
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from src.core.action_recognizer import Action, ActionSequence, ActionType
from src.core.mtm_analyzer import MTMSummary, EfficiencyMetrics


class CSVExporter:
    """
    CSV数据导出器
    支持导出动作序列表和MTM工时汇总表
    """

    def __init__(self, output_dir: str = "data/exports"):
        """
        初始化CSV导出器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_action_sequence(
        self,
        action_sequence: ActionSequence,
        filename: Optional[str] = None,
        include_keypoints: bool = False
    ) -> str:
        """
        导出动作序列表到CSV

        Args:
            action_sequence: 动作序列对象
            filename: 输出文件名（可选）
            include_keypoints: 是否包含关键点数据

        Returns:
            str: 生成的CSV文件路径
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"action_sequence_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        # 构建数据
        data = []
        for i, action in enumerate(action_sequence.actions):
            row = {
                '序号': i + 1,
                '动作类型': action.action_type.value,
                '动作代码': self._get_action_code(action.action_type),
                '开始帧': action.start_frame,
                '结束帧': action.end_frame,
                '开始时间(s)': round(action.start_time, 3),
                '结束时间(s)': round(action.end_time, 3),
                '持续时间(s)': round(action.duration, 3),
                'TMU值': action.tmu_value,
                '标准时间(s)': round(action.tmu_value * 0.036, 3),  # TMU转秒
                '距离分类': action.distance_category,
                '置信度': round(action.confidence, 2)
            }
            data.append(row)

        # 使用pandas导出
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')  # utf-8-sig支持中文

        print(f"[成功] 动作序列CSV已导出: {filepath}")
        return filepath

    def export_mtm_summary(
        self,
        mtm_summary: MTMSummary,
        filename: Optional[str] = None,
        video_info: Optional[Dict] = None
    ) -> str:
        """
        导出MTM工时汇总表到CSV

        Args:
            mtm_summary: MTM汇总对象
            filename: 输出文件名（可选）
            video_info: 视频信息（可选）

        Returns:
            str: 生成的CSV文件路径
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mtm_summary_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        # 构建数据
        data = []

        # 视频信息部分
        if video_info:
            data.append({'类别': '视频信息', '项目': '文件名', '数值': video_info.get('name', '未知'), '单位': '-'})
            data.append({'类别': '视频信息', '项目': '时长', '数值': round(video_info.get('duration', 0), 2), '单位': '秒'})
            data.append({'类别': '视频信息', '项目': '帧率', '数值': video_info.get('fps', 30), '单位': 'FPS'})

        # 正常时间部分
        data.append({'类别': '正常时间', '项目': 'TMU值', '数值': round(mtm_summary.normal_time_tmu, 2), '单位': 'TMU'})
        data.append({'类别': '正常时间', '项目': '时间(秒)', '数值': round(mtm_summary.normal_time_sec, 3), '单位': '秒'})
        data.append({'类别': '正常时间', '项目': '时间(分)', '数值': round(mtm_summary.normal_time_min, 4), '单位': '分钟'})

        # 宽放时间部分
        data.append({'类别': '宽放时间', '项目': '宽放率', '数值': round(mtm_summary.allowance_rate * 100, 1), '单位': '%'})
        data.append({'类别': '宽放时间', '项目': 'TMU值', '数值': round(mtm_summary.allowance_tmu, 2), '单位': 'TMU'})
        data.append({'类别': '宽放时间', '项目': '时间(秒)', '数值': round(mtm_summary.allowance_sec, 3), '单位': '秒'})

        # 标准工时部分
        data.append({'类别': '标准工时', '项目': 'TMU值', '数值': round(mtm_summary.standard_time_tmu, 2), '单位': 'TMU'})
        data.append({'类别': '标准工时', '项目': '时间(秒)', '数值': round(mtm_summary.standard_time_sec, 3), '单位': '秒'})
        data.append({'类别': '标准工时', '项目': '时间(分)', '数值': round(mtm_summary.standard_time_min, 4), '单位': '分钟'})

        # 动作统计部分
        for action_type, count in mtm_summary.action_counts.items():
            data.append({'类别': '动作统计', '项目': f'{action_type}次数', '数值': count, '单位': '次'})
        data.append({'类别': '动作统计', '项目': '总动作数', '数值': mtm_summary.total_actions, '单位': '次'})

        # 使用pandas导出
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

        print(f"[成功] MTM汇总CSV已导出: {filepath}")
        return filepath

    def export_full_report(
        self,
        action_sequence: ActionSequence,
        mtm_summary: MTMSummary,
        efficiency_metrics: Optional[EfficiencyMetrics] = None,
        video_info: Optional[Dict] = None,
        filename: Optional[str] = None
    ) -> Dict[str, str]:
        """
        导出完整报告（多个CSV文件）

        Args:
            action_sequence: 动作序列
            mtm_summary: MTM汇总
            efficiency_metrics: 效率指标（可选）
            video_info: 视频信息（可选）
            filename: 基础文件名（可选）

        Returns:
            Dict[str, str]: 生成的文件路径字典
        """
        # 生成基础文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"analysis_{timestamp}"
        else:
            base_name = filename

        # 导出各部分
        files = {}

        files['action_sequence'] = self.export_action_sequence(
            action_sequence,
            filename=f"{base_name}_actions.csv"
        )

        files['mtm_summary'] = self.export_mtm_summary(
            mtm_summary,
            filename=f"{base_name}_mtm.csv",
            video_info=video_info
        )

        # 导出效率指标
        if efficiency_metrics:
            metrics_filepath = os.path.join(self.output_dir, f"{base_name}_metrics.csv")
            metrics_data = [
                {'指标': '实际观测时间', '数值': round(efficiency_metrics.actual_time, 3), '单位': '秒'},
                {'指标': '标准工时', '数值': round(efficiency_metrics.standard_time, 3), '单位': '秒'},
                {'指标': '等待时间', '数值': round(efficiency_metrics.wait_time, 3), '单位': '秒'},
                {'指标': '等待损失率', '数值': round(efficiency_metrics.wait_loss_rate, 2), '单位': '%'},
                {'指标': '动作效率', '数值': round(efficiency_metrics.action_efficiency, 2), '单位': '%'},
                {'指标': '周期时间', '数值': round(efficiency_metrics.cycle_time, 3), '单位': '秒'}
            ]
            df = pd.DataFrame(metrics_data)
            df.to_csv(metrics_filepath, index=False, encoding='utf-8-sig')
            files['metrics'] = metrics_filepath
            print(f"[成功] 效率指标CSV已导出: {metrics_filepath}")

        return files

    def _get_action_code(self, action_type: ActionType) -> str:
        """
        获取动作代码缩写

        Args:
            action_type: 动作类型

        Returns:
            str: 动作代码
        """
        codes = {
            ActionType.REACH: 'R',
            ActionType.GRASP: 'G',
            ActionType.MOVE: 'M',
            ActionType.RELEASE: 'RL',
            ActionType.WAIT: 'W',
            ActionType.NONE: 'N'
        }
        return codes.get(action_type, 'N')


def export_to_csv(
    action_sequence: ActionSequence,
    mtm_summary: MTMSummary,
    output_dir: str = "data/exports"
) -> Dict[str, str]:
    """
    快速导出到CSV（便捷函数）

    Args:
        action_sequence: 动作序列
        mtm_summary: MTM汇总
        output_dir: 输出目录

    Returns:
        Dict[str, str]: 生成的文件路径
    """
    exporter = CSVExporter(output_dir=output_dir)
    return exporter.export_full_report(
        action_sequence=action_sequence,
        mtm_summary=mtm_summary
    )