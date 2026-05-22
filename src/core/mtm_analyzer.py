"""
MTM工时分析器
功能：计算标准工时、宽放时间、效率指标
版本：v1.0 (Day -2交付)
日期：2025-05-21
"""
import yaml
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from src.core.action_recognizer import Action, ActionSequence, ActionType


@dataclass
class MTMSummary:
    """MTM工时汇总数据结构"""
    # 正常时间
    normal_time_tmu: float
    normal_time_sec: float
    normal_time_min: float

    # 宽放时间
    allowance_rate: float
    allowance_tmu: float
    allowance_sec: float
    allowance_min: float

    # 标准工时
    standard_time_tmu: float
    standard_time_sec: float
    standard_time_min: float

    # 动作统计
    action_counts: Dict[str, int]
    total_actions: int


@dataclass
class EfficiencyMetrics:
    """效率指标数据结构"""
    actual_time: float        # 实际观测时间（秒）
    standard_time: float      # 标准工时（秒）
    wait_time: float          # 等待时间累计（秒）
    wait_loss_rate: float     # 等待损失率（%）
    action_efficiency: float  # 动作效率（%）
    cycle_time: float         # 周期时间（秒）


class MTMAnalyzer:
    """
    MTM工时分析器
    根据动作序列计算标准工时和效率指标
    """

    def __init__(self, config_path: Optional[str] = None, allowance_rate: float = 0.15):
        """
        初始化MTM分析器

        Args:
            config_path: MTM配置文件路径
            allowance_rate: 宽放率（默认15%）
        """
        self.allowance_rate = allowance_rate
        self.mtm_tables = {}

        # 加载MTM配置
        if config_path:
            self._load_mtm_tables(config_path)
        else:
            # 使用默认路径
            default_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'config',
                'mtm_tables.yaml'
            )
            if os.path.exists(default_path):
                self._load_mtm_tables(default_path)

    def _load_mtm_tables(self, config_path: str):
        """
        加载MTM时间表配置

        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.mtm_tables = yaml.safe_load(f)
            print(f"[成功] MTM时间表已加载: {config_path}")
        except Exception as e:
            print(f"[警告] MTM配置加载失败: {e}")

    def get_tmu_value(
        self,
        action_type: ActionType,
        distance_category: str = "medium",
        complexity: str = "simple"
    ) -> float:
        """
        获取动作的TMU值

        Args:
            action_type: 动作类型
            distance_category: 距离分类（short/medium/long）
            complexity: 复杂度分类（simple/medium/complex）

        Returns:
            float: TMU值
        """
        # 默认TMU值（如果配置未加载）
        default_values = {
            ActionType.REACH: {"short": 8, "medium": 15, "long": 22},
            ActionType.GRASP: {"simple": 5, "medium": 8, "complex": 12},
            ActionType.MOVE: {"short": 10, "medium": 18, "long": 26},
            ActionType.RELEASE: {"simple": 2, "medium": 4, "complex": 8},
            ActionType.WAIT: {"any": 0},
            ActionType.NONE: {"any": 0}
        }

        # 从配置获取
        if self.mtm_tables:
            try:
                action_key = action_type.value.lower()
                if action_key in self.mtm_tables:
                    table = self.mtm_tables[action_key]
                    # 简化处理，返回默认值
                    if action_type == ActionType.REACH:
                        return table.get('A_medium', {}).get('tmu', 15)
                    elif action_type == ActionType.GRASP:
                        return table.get('G1', {}).get('tmu', 5)
                    elif action_type == ActionType.MOVE:
                        return table.get('A_medium', {}).get('tmu', 18)
                    elif action_type == ActionType.RELEASE:
                        return table.get('RL1', {}).get('tmu', 2)
            except:
                pass

        # 返回默认值
        if action_type in default_values:
            if action_type in [ActionType.REACH, ActionType.MOVE]:
                return default_values[action_type].get(distance_category, 15)
            elif action_type in [ActionType.GRASP, ActionType.RELEASE]:
                return default_values[action_type].get(complexity, 5)
            else:
                return 0

        return 0

    def calculate_summary(self, action_sequence: ActionSequence) -> MTMSummary:
        """
        计算MTM工时汇总

        Args:
            action_sequence: 动作序列

        Returns:
            MTMSummary: 工时汇总结果
        """
        # 计算正常时间（TMU）
        normal_time_tmu = sum(action.tmu_value for action in action_sequence.actions)

        # TMU转秒：1 TMU = 0.036秒
        tmu_to_sec = 0.036
        normal_time_sec = normal_time_tmu * tmu_to_sec
        normal_time_min = normal_time_sec / 60

        # 计算宽放时间
        allowance_tmu = normal_time_tmu * self.allowance_rate
        allowance_sec = normal_time_sec * self.allowance_rate
        allowance_min = normal_time_min * self.allowance_rate

        # 计算标准工时
        standard_time_tmu = normal_time_tmu + allowance_tmu
        standard_time_sec = normal_time_sec + allowance_sec
        standard_time_min = normal_time_min + allowance_min

        # 动作统计
        action_counts = action_sequence.action_counts
        total_actions = len(action_sequence.actions)

        return MTMSummary(
            normal_time_tmu=normal_time_tmu,
            normal_time_sec=normal_time_sec,
            normal_time_min=normal_time_min,
            allowance_rate=self.allowance_rate,
            allowance_tmu=allowance_tmu,
            allowance_sec=allowance_sec,
            allowance_min=allowance_min,
            standard_time_tmu=standard_time_tmu,
            standard_time_sec=standard_time_sec,
            standard_time_min=standard_time_min,
            action_counts=action_counts,
            total_actions=total_actions
        )

    def calculate_efficiency(
        self,
        action_sequence: ActionSequence,
        video_duration: float
    ) -> EfficiencyMetrics:
        """
        计算效率指标

        Args:
            action_sequence: 动作序列
            video_duration: 视频总时长（秒）

        Returns:
            EfficiencyMetrics: 效率指标结果
        """
        # 获取工时汇总
        summary = self.calculate_summary(action_sequence)

        # 实际观测时间
        actual_time = video_duration

        # 标准工时
        standard_time = summary.standard_time_sec

        # 等待时间累计（Wait动作）
        wait_time = sum(
            action.duration for action in action_sequence.actions
            if action.action_type == ActionType.WAIT
        )

        # 等待损失率
        wait_loss_rate = (wait_time / actual_time * 100) if actual_time > 0 else 0

        # 动作效率（有效动作时间 / 总观测时间）
        effective_time = sum(
            action.duration for action in action_sequence.actions
            if action.action_type in [ActionType.REACH, ActionType.GRASP, ActionType.MOVE, ActionType.RELEASE]
        )
        action_efficiency = (effective_time / actual_time * 100) if actual_time > 0 else 0

        # 周期时间（标准工时）
        cycle_time = standard_time

        return EfficiencyMetrics(
            actual_time=actual_time,
            standard_time=standard_time,
            wait_time=wait_time,
            wait_loss_rate=wait_loss_rate,
            action_efficiency=action_efficiency,
            cycle_time=cycle_time
        )

    def generate_report_data(
        self,
        action_sequence: ActionSequence,
        video_duration: float,
        video_info: Optional[Dict] = None
    ) -> Dict:
        """
        生成完整报告数据

        Args:
            action_sequence: 动作序列
            video_duration: 视频总时长
            video_info: 视频信息（可选）

        Returns:
            Dict: 完整报告数据
        """
        summary = self.calculate_summary(action_sequence)
        metrics = self.calculate_efficiency(action_sequence, video_duration)

        # 构建报告数据
        report_data = {
            'video_info': video_info or {},
            'actions': [
                {
                    'type': action.action_type.value,
                    'start_time': action.start_time,
                    'end_time': action.end_time,
                    'duration': action.duration,
                    'time_tmu': action.tmu_value,
                    'frame_range': f"{action.start_frame}-{action.end_frame}"
                }
                for action in action_sequence.actions
            ],
            'mtm_summary': {
                'normal_time_tmu': summary.normal_time_tmu,
                'normal_time_sec': summary.normal_time_sec,
                'normal_time_min': summary.normal_time_min,
                'allowance_rate': summary.allowance_rate,
                'allowance_tmu': summary.allowance_tmu,
                'allowance_sec': summary.allowance_sec,
                'standard_time_tmu': summary.standard_time_tmu,
                'standard_time_sec': summary.standard_time_sec,
                'standard_time_min': summary.standard_time_min,
                'action_counts': summary.action_counts,
                'total_actions': summary.total_actions
            },
            'metrics': {
                'actual_time': metrics.actual_time,
                'standard_time': metrics.standard_time,
                'wait_time': metrics.wait_time,
                'wait_loss_rate': metrics.wait_loss_rate,
                'action_efficiency': metrics.action_efficiency,
                'cycle_time': metrics.cycle_time
            }
        }

        return report_data


def calculate_mtm_summary(action_sequence: ActionSequence, allowance_rate: float = 0.15) -> MTMSummary:
    """
    快速计算MTM汇总（便捷函数）

    Args:
        action_sequence: 动作序列
        allowance_rate: 宽放率

    Returns:
        MTMSummary: 工时汇总
    """
    analyzer = MTMAnalyzer(allowance_rate=allowance_rate)
    return analyzer.calculate_summary(action_sequence)