"""
时间轴生成器
功能：使用matplotlib生成动作时间分布PNG图表
版本：v1.0 (Day -1交付)
日期：2025-05-21
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
from typing import List, Dict, Optional
from datetime import datetime
from src.core.action_recognizer import Action, ActionSequence, ActionType


class TimelineGenerator:
    """
    时间轴生成器
    生成动作时间分布图、MTM工时统计图
    """

    # 动作颜色配置
    ACTION_COLORS = {
        ActionType.REACH: '#FFD700',      # 金色 - Reach
        ActionType.GRASP: '#FF69B4',      # 粉色 - Grasp
        ActionType.MOVE: '#00CED1',       # 青色 - Move
        ActionType.RELEASE: '#32CD32',    # 绿色 - Release
        ActionType.WAIT: '#808080',       # 灰色 - Wait
        ActionType.NONE: '#FFFFFF'        # 白色 - None
    }

    # 中文字体配置
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    def __init__(self, output_dir: str = "data/exports"):
        """
        初始化时间轴生成器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_action_timeline(
        self,
        action_sequence: ActionSequence,
        filename: Optional[str] = None,
        title: str = "动作时间分布图"
    ) -> str:
        """
        生成动作时间轴分布图

        Args:
            action_sequence: 动作序列对象
            filename: 输出文件名（可选）
            title: 图表标题

        Returns:
            str: 生成的PNG文件路径
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"timeline_{timestamp}.png"

        filepath = os.path.join(self.output_dir, filename)

        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))

        # 绘制动作条带
        for i, action in enumerate(action_sequence.actions):
            color = self.ACTION_COLORS.get(action.action_type, '#CCCCCC')

            # 绘制水平条带
            ax.barh(
                0,
                action.duration,
                left=action.start_time,
                height=0.5,
                color=color,
                edgecolor='black',
                linewidth=0.5
            )

            # 在条带上标注动作代码
            action_code = self._get_action_code(action.action_type)
            if action.duration > 0.1:  # 只在足够长的动作上标注
                ax.text(
                    action.start_time + action.duration / 2,
                    0,
                    action_code,
                    ha='center',
                    va='center',
                    fontsize=10,
                    fontweight='bold'
                )

        # 设置坐标轴
        ax.set_xlim(0, action_sequence.total_duration)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel('时间 (秒)', fontsize=12)
        ax.set_ylabel('动作序列', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')

        # 隐藏Y轴刻度
        ax.set_yticks([])

        # 添加图例
        legend_patches = []
        for action_type, color in self.ACTION_COLORS.items():
            if action_type != ActionType.NONE and action_type in action_sequence.action_counts:
                legend_patches.append(
                    mpatches.Patch(
                        color=color,
                        label=f"{action_type.value} ({self._get_action_code(action_type)})"
                    )
                )

        if legend_patches:
            ax.legend(
                handles=legend_patches,
                loc='upper right',
                fontsize=10
            )

        # 添加网格
        ax.grid(True, axis='x', linestyle='--', alpha=0.5)

        # 保存图表
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"[成功] 时间轴图表已生成: {filepath}")
        return filepath

    def generate_mtm_pie_chart(
        self,
        action_sequence: ActionSequence,
        filename: Optional[str] = None,
        title: str = "MTM工时分布图"
    ) -> str:
        """
        生成MTM工时饼图

        Args:
            action_sequence: 动作序列对象
            filename: 输出文件名（可选）
            title: 图表标题

        Returns:
            str: 生成的PNG文件路径
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mtm_pie_{timestamp}.png"

        filepath = os.path.join(self.output_dir, filename)

        # 统计各动作TMU值
        tmu_data = {}
        for action in action_sequence.actions:
            if action.action_type != ActionType.NONE:
                key = action.action_type.value
                tmu_data[key] = tmu_data.get(key, 0) + action.tmu_value

        if not tmu_data:
            # 无数据时生成空图
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.text(0.5, 0.5, '无动作数据', ha='center', va='center', fontsize=14)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return filepath

        # 创建饼图
        fig, ax = plt.subplots(figsize=(8, 8))

        labels = list(tmu_data.keys())
        sizes = list(tmu_data.values())
        colors = [self.ACTION_COLORS.get(ActionType(label), '#CCCCCC') for label in labels]

        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85
        )

        # 设置字体
        for text in texts:
            text.set_fontsize(11)
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        # 设置标题
        ax.set_title(title, fontsize=14, fontweight='bold')

        # 添加TMU总量标注
        total_tmu = sum(sizes)
        ax.text(
            0, 0,
            f'Total: {total_tmu:.0f} TMU\n({total_tmu * 0.036:.2f}秒)',
            ha='center',
            va='center',
            fontsize=12,
            fontweight='bold'
        )

        # 保存图表
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"[成功] MTM饼图已生成: {filepath}")
        return filepath

    def generate_combined_report(
        self,
        action_sequence: ActionSequence,
        mtm_summary: Dict,
        efficiency_metrics: Dict,
        filename: Optional[str] = None
    ) -> str:
        """
        生成综合报告图表（多子图）

        Args:
            action_sequence: 动作序列
            mtm_summary: MTM汇总数据
            efficiency_metrics: 效率指标数据
            filename: 输出文件名（可选）

        Returns:
            str: 生成的PNG文件路径
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_combined_{timestamp}.png"

        filepath = os.path.join(self.output_dir, filename)

        # 创建多子图
        fig = plt.figure(figsize=(16, 10))

        # 子图1：时间轴分布
        ax1 = fig.add_subplot(2, 2, 1)
        self._draw_timeline_subplot(ax1, action_sequence)

        # 子图2：MTM工时饼图
        ax2 = fig.add_subplot(2, 2, 2)
        self._draw_mtm_pie_subplot(ax2, action_sequence)

        # 子图3：动作统计柱状图
        ax3 = fig.add_subplot(2, 2, 3)
        self._draw_action_counts_subplot(ax3, action_sequence)

        # 子图4：效率指标
        ax4 = fig.add_subplot(2, 2, 4)
        self._draw_efficiency_subplot(ax4, efficiency_metrics)

        # 设置总标题
        fig.suptitle('工业IE智能体 - 动作分析报告', fontsize=16, fontweight='bold')

        # 保存图表
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"[成功] 综合报告图表已生成: {filepath}")
        return filepath

    def _draw_timeline_subplot(self, ax, action_sequence: ActionSequence):
        """绘制时间轴子图"""
        for action in action_sequence.actions:
            color = self.ACTION_COLORS.get(action.action_type, '#CCCCCC')
            ax.barh(
                0,
                action.duration,
                left=action.start_time,
                height=0.4,
                color=color,
                edgecolor='black'
            )

        ax.set_xlim(0, action_sequence.total_duration)
        ax.set_ylim(-0.3, 0.3)
        ax.set_xlabel('时间 (秒)')
        ax.set_title('动作时间轴')
        ax.set_yticks([])

    def _draw_mtm_pie_subplot(self, ax, action_sequence: ActionSequence):
        """绘制MTM饼图子图"""
        tmu_data = {}
        for action in action_sequence.actions:
            if action.action_type != ActionType.NONE:
                key = action.action_type.value
                tmu_data[key] = tmu_data.get(key, 0) + action.tmu_value

        if tmu_data:
            labels = list(tmu_data.keys())
            sizes = list(tmu_data.values())
            colors = [self.ACTION_COLORS.get(ActionType(label), '#CCCCCC') for label in labels]
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
            ax.set_title('MTM工时分布')

    def _draw_action_counts_subplot(self, ax, action_sequence: ActionSequence):
        """绘制动作统计柱状图子图"""
        action_counts = action_sequence.action_counts
        if action_counts:
            actions = list(action_counts.keys())
            counts = list(action_counts.values())
            colors = [self.ACTION_COLORS.get(ActionType(a), '#CCCCCC') for a in actions]

            ax.bar(actions, counts, color=colors, edgecolor='black')
            ax.set_xlabel('动作类型')
            ax.set_ylabel('次数')
            ax.set_title('动作统计')

    def _draw_efficiency_subplot(self, ax, efficiency_metrics: Dict):
        """绘制效率指标子图"""
        metrics_name = ['动作效率', '标准工时占比']
        metrics_value = [
            efficiency_metrics.get('action_efficiency', 0),
            min(efficiency_metrics.get('standard_time', 0) / efficiency_metrics.get('actual_time', 1) * 100, 100)
        ]

        ax.bar(metrics_name, metrics_value, color=['#4CAF50', '#2196F3'], edgecolor='black')
        ax.set_ylim(0, 100)
        ax.set_ylabel('百分比 (%)')
        ax.set_title('效率指标')

        # 添加数值标注
        for i, v in enumerate(metrics_value):
            ax.text(i, v + 2, f'{v:.1f}%', ha='center', fontsize=10)

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


def generate_timeline(action_sequence: ActionSequence, output_dir: str = "data/exports") -> str:
    """
    快速生成时间轴（便捷函数）

    Args:
        action_sequence: 动作序列
        output_dir: 输出目录

    Returns:
        str: PNG文件路径
    """
    generator = TimelineGenerator(output_dir=output_dir)
    return generator.generate_action_timeline(action_sequence)