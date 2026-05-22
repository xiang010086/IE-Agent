"""
节拍计算模块
功能：计算标准节拍、实际节拍、节拍效率等指标
版本：v1.0 (Day 2交付)
日期：2025-05-21

节拍（Takt Time/Cycle Time）计算：
- 标准节拍 = 总有效工作时间 / 客户需求量
- 实际节拍 = 动作序列总时长
- 节拍效率 = 标准工时 / 实际节拍
"""
import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass
from src.core.action_recognizer import ActionSequence, ActionType


@dataclass
class CycleTimeMetrics:
    """节拍指标数据结构"""
    takt_time: float           # 客户需求节拍（秒）
    standard_cycle_time: float # 标准节拍时间（秒）
    actual_cycle_time: float   # 实际节拍时间（秒）
    cycle_efficiency: float    # 节拍效率（%）
    cycle_variance: float      # 节拍偏差（秒）
    cycle_utilization: float   # 节拍利用率（%）
    bottleneck_time: float     # 瓶颈工序时间（秒）


@dataclass
class MultiStationCycle:
    """多工位节拍数据结构"""
    station_id: int
    station_name: str
    cycle_time: float
    wait_time: float
    work_time: float
    efficiency: float


class CycleTimeCalculator:
    """
    节拍计算器
    计算标准节拍、实际节拍、节拍效率等工业工程指标
    """

    def __init__(
        self,
        working_hours_per_day: float = 8.0,
        breaks_per_day: float = 0.5,
        effective_working_ratio: float = 0.85
    ):
        """
        初始化节拍计算器

        Args:
            working_hours_per_day: 每日工作时长（小时）
            breaks_per_day: 每日休息时间（小时）
            effective_working_ratio: 有效工作时间比例
        """
        self.working_hours_per_day = working_hours_per_day
        self.breaks_per_day = breaks_per_day
        self.effective_working_ratio = effective_working_ratio

    def calculate_takt_time(
        self,
        daily_demand: float,
        shift_count: int = 1
    ) -> float:
        """
        计算客户需求节拍（Takt Time）

        Args:
            daily_demand: 每日客户需求量（件）
            shift_count: 班次数量

        Returns:
            float: 需求节拍（秒/件）
        """
        if daily_demand <= 0:
            return 0.0

        # 计算每班有效工作时间（秒）
        effective_time_per_shift = (
            (self.working_hours_per_day - self.breaks_per_day)
            * 3600
            * self.effective_working_ratio
        )

        # 计算总有效工作时间
        total_effective_time = effective_time_per_shift * shift_count

        # 计算节拍
        takt_time = total_effective_time / daily_demand

        return takt_time

    def calculate_standard_cycle_time(
        self,
        action_sequence: ActionSequence
    ) -> float:
        """
        计算标准节拍时间（基于MTM标准工时）

        Args:
            action_sequence: 动作序列

        Returns:
            float: 标准节拍时间（秒）
        """
        # TMU转换为秒（1 TMU = 0.036秒）
        total_tmu_sec = action_sequence.total_tmu * 0.036

        # 添加宽放时间（默认15%）
        allowance_rate = 0.15
        standard_time = total_tmu_sec * (1 + allowance_rate)

        return standard_time

    def calculate_actual_cycle_time(
        self,
        action_sequence: ActionSequence
    ) -> float:
        """
        计算实际节拍时间（基于实际观测时长）

        Args:
            action_sequence: 动作序列

        Returns:
            float: 实际节拍时间（秒）
        """
        return action_sequence.total_duration

    def calculate_cycle_efficiency(
        self,
        standard_time: float,
        actual_time: float
    ) -> float:
        """
        计算节拍效率

        Args:
            standard_time: 标准时间（秒）
            actual_time: 实际时间（秒）

        Returns:
            float: 节拍效率（%）
        """
        if actual_time <= 0:
            return 0.0

        efficiency = (standard_time / actual_time) * 100
        return min(efficiency, 100.0)  # 效率不超过100%

    def calculate_cycle_metrics(
        self,
        action_sequence: ActionSequence,
        daily_demand: Optional[float] = None,
        shift_count: int = 1
    ) -> CycleTimeMetrics:
        """
        计算完整节拍指标

        Args:
            action_sequence: 动作序列
            daily_demand: 每日客户需求量（可选）
            shift_count: 班次数量

        Returns:
            CycleTimeMetrics: 节拍指标对象
        """
        # 计算节拍时间
        standard_time = self.calculate_standard_cycle_time(action_sequence)
        actual_time = self.calculate_actual_cycle_time(action_sequence)

        # 计算客户需求节拍
        takt_time = 0.0
        if daily_demand and daily_demand > 0:
            takt_time = self.calculate_takt_time(daily_demand, shift_count)

        # 计算效率
        efficiency = self.calculate_cycle_efficiency(standard_time, actual_time)

        # 计算节拍偏差
        variance = actual_time - standard_time

        # 计算节拍利用率（相对于需求节拍）
        utilization = 0.0
        if takt_time > 0:
            utilization = (standard_time / takt_time) * 100

        # 识别瓶颈时间（最长单个动作）
        bottleneck_time = 0.0
        if action_sequence.actions:
            bottleneck_time = max(a.duration for a in action_sequence.actions)

        return CycleTimeMetrics(
            takt_time=takt_time,
            standard_cycle_time=standard_time,
            actual_cycle_time=actual_time,
            cycle_efficiency=efficiency,
            cycle_variance=variance,
            cycle_utilization=utilization,
            bottleneck_time=bottleneck_time
        )

    def calculate_multi_station_cycles(
        self,
        station_sequences: Dict[int, ActionSequence],
        station_names: Optional[Dict[int, str]] = None
    ) -> List[MultiStationCycle]:
        """
        计算多工位节拍

        Args:
            station_sequences: 各工位动作序列 {工位ID: ActionSequence}
            station_names: 工位名称字典（可选）

        Returns:
            List[MultiStationCycle]: 多工位节拍列表
        """
        results = []

        for station_id, sequence in station_sequences.items():
            station_name = station_names.get(station_id, f"工位{station_id}") if station_names else f"工位{station_id}"

            # 计算工作时间（排除Wait）
            work_time = sum(
                a.duration for a in sequence.actions
                if a.action_type != ActionType.WAIT
            )

            # 计算等待时间
            wait_time = sum(
                a.duration for a in sequence.actions
                if a.action_type == ActionType.WAIT
            )

            # 计算效率
            total_time = sequence.total_duration
            efficiency = (work_time / total_time * 100) if total_time > 0 else 0.0

            results.append(MultiStationCycle(
                station_id=station_id,
                station_name=station_name,
                cycle_time=total_time,
                wait_time=wait_time,
                work_time=work_time,
                efficiency=efficiency
            ))

        return results

    def identify_bottleneck_station(
        self,
        station_cycles: List[MultiStationCycle]
    ) -> Optional[MultiStationCycle]:
        """
        识别瓶颈工位（节拍最长的工位）

        Args:
            station_cycles: 多工位节拍列表

        Returns:
            Optional[MultiStationCycle]: 瓶颈工位
        """
        if not station_cycles:
            return None

        return max(station_cycles, key=lambda x: x.cycle_time)

    def calculate_line_takt(
        self,
        station_cycles: List[MultiStationCycle],
        daily_demand: float,
        shift_count: int = 1
    ) -> Dict[str, float]:
        """
        计算产线节拍匹配度

        Args:
            station_cycles: 多工位节拍列表
            daily_demand: 每日需求量
            shift_count: 班次数量

        Returns:
            Dict: 节拍匹配分析结果
        """
        if not station_cycles or daily_demand <= 0:
            return {}

        # 计算需求节拍
        takt_time = self.calculate_takt_time(daily_demand, shift_count)

        # 识别瓶颈工位
        bottleneck = self.identify_bottleneck_station(station_cycles)
        bottleneck_time = bottleneck.cycle_time if bottleneck else 0.0

        # 计算产线节拍匹配度
        line_takt_match = (takt_time / bottleneck_time * 100) if bottleneck_time > 0 else 0.0

        # 计算节拍松弛时间
        slack_time = takt_time - bottleneck_time

        # 计算产能
        if bottleneck_time > 0:
            effective_time = (
                (self.working_hours_per_day - self.breaks_per_day)
                * 3600
                * self.effective_working_ratio
                * shift_count
            )
            production_capacity = effective_time / bottleneck_time
        else:
            production_capacity = 0.0

        return {
            'takt_time': takt_time,
            'bottleneck_time': bottleneck_time,
            'bottleneck_station': bottleneck.station_name if bottleneck else '',
            'line_takt_match': line_takt_match,
            'slack_time': slack_time,
            'production_capacity': production_capacity,
            'meets_demand': bottleneck_time <= takt_time if bottleneck_time > 0 else False
        }

    def generate_cycle_report(
        self,
        metrics: CycleTimeMetrics
    ) -> str:
        """
        生成节拍分析报告文本

        Args:
            metrics: 节拍指标

        Returns:
            str: 报告文本
        """
        report = f"""
节拍分析报告
====================

基础指标：
- 客户需求节拍：{metrics.takt_time:.2f} 秒/件
- 标准节拍时间：{metrics.standard_cycle_time:.2f} 秒
- 实际节拍时间：{metrics.actual_cycle_time:.2f} 秒

效率指标：
- 节拍效率：{metrics.cycle_efficiency:.1f}%
- 节拍利用率：{metrics.cycle_utilization:.1f}%

偏差分析：
- 节拍偏差：{metrics.cycle_variance:.2f} 秒
- 瓶颈时间：{metrics.bottleneck_time:.2f} 秒

建议：
"""
        if metrics.cycle_efficiency < 80:
            report += "- 节拍效率偏低，建议优化动作流程，减少非增值动作\n"
        if metrics.cycle_variance > 5:
            report += "- 实际时间超出标准时间较多，建议进行员工培训或工艺优化\n"
        if metrics.cycle_utilization > 100:
            report += "- 节拍利用率过高，可能影响质量和员工疲劳，建议增加人员或设备\n"
        else:
            report += "- 节拍匹配良好，建议保持当前作业模式\n"

        return report


def calculate_cycle_time_from_sequence(
    action_sequence: ActionSequence,
    daily_demand: Optional[float] = None
) -> CycleTimeMetrics:
    """
    便捷函数：从动作序列计算节拍指标

    Args:
        action_sequence: 动作序列
        daily_demand: 每日需求量（可选）

    Returns:
        CycleTimeMetrics: 节拍指标
    """
    calculator = CycleTimeCalculator()
    return calculator.calculate_cycle_metrics(action_sequence, daily_demand)