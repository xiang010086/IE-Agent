"""
线平衡率计算模块
功能：计算产线平衡率、平衡损失、工位负荷均衡度等指标
版本：v1.0 (Day 2交付)
日期：2025-05-21

线平衡率（Line Balance Rate）计算：
- 理论最小人数 = Σ各工位标准时间 / 瓶颈时间
- 线平衡率 = Σ各工位工作时间 / (瓶颈时间 × 工位数) × 100%
- 平衡损失率 = 100% - 线平衡率
"""
import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass
from src.core.action_recognizer import ActionSequence
from src.core.cycle_time_calculator import MultiStationCycle


@dataclass
class LineBalanceMetrics:
    """线平衡指标数据结构"""
    line_balance_rate: float      # 线平衡率（%）
    balance_loss_rate: float      # 平衡损失率（%）
    bottleneck_station: str       # 瓶颈工位名称
    bottleneck_time: float        # 瓶颈时间（秒）
    total_work_time: float        # 总工作时间（秒）
    total_wait_time: float        # 总等待时间（秒）
    station_count: int            # 工位数量
    theoretical_min_workers: int  # 理论最小人数
    actual_workers: int           # 实际人数（需要输入）
    worker_efficiency: float      # 人员效率（%）
    work_distribution: Dict[str, float]  # 各工位负荷分布


@dataclass
class StationLoad:
    """工位负荷数据结构"""
    station_id: int
    station_name: str
    load_rate: float        # 负荷率（%）
    work_time: float        # 工作时间（秒）
    wait_time: float        # 等待时间（秒）
    is_bottleneck: bool     # 是否瓶颈
    is_idle: bool           # 是否空闲过多


class LineBalanceAnalyzer:
    """
    线平衡率分析器
    计算产线平衡率、识别瓶颈工位、优化建议
    """

    def __init__(
        self,
        idle_threshold: float = 30.0,  # 空闲率阈值（%）
        overload_threshold: float = 90.0  # 负荷过载阈值（%）
    ):
        """
        初始化线平衡分析器

        Args:
            idle_threshold: 空闲率阈值，超过此值视为空闲过多
            overload_threshold: 负荷过载阈值，超过此值视为负荷过重
        """
        self.idle_threshold = idle_threshold
        self.overload_threshold = overload_threshold

    def calculate_line_balance_rate(
        self,
        station_cycles: List[MultiStationCycle]
    ) -> float:
        """
        计算线平衡率

        Args:
            station_cycles: 多工位节拍列表

        Returns:
            float: 线平衡率（%）
        """
        if not station_cycles:
            return 0.0

        # 识别瓶颈时间
        bottleneck_time = max(s.cycle_time for s in station_cycles)

        if bottleneck_time <= 0:
            return 0.0

        # 计算各工位工作时间总和
        total_work_time = sum(s.work_time for s in station_cycles)

        # 计算线平衡率
        station_count = len(station_cycles)
        lbr = (total_work_time / (bottleneck_time * station_count)) * 100

        return min(lbr, 100.0)

    def calculate_balance_loss_rate(
        self,
        line_balance_rate: float
    ) -> float:
        """
        计算平衡损失率

        Args:
            line_balance_rate: 线平衡率

        Returns:
            float: 平衡损失率（%）
        """
        return 100.0 - line_balance_rate

    def calculate_theoretical_min_workers(
        self,
        station_cycles: List[MultiStationCycle],
        bottleneck_time: float
    ) -> int:
        """
        计算理论最小人数

        Args:
            station_cycles: 多工位节拍列表
            bottleneck_time: 瓶颈时间（秒）

        Returns:
            int: 理论最小人数
        """
        if bottleneck_time <= 0:
            return 0

        # 总工作量（标准时间）
        total_work = sum(s.work_time for s in station_cycles)

        # 理论最小人数
        min_workers = total_work / bottleneck_time

        return max(1, int(np.ceil(min_workers)))

    def identify_bottleneck(
        self,
        station_cycles: List[MultiStationCycle]
    ) -> Optional[MultiStationCycle]:
        """
        识别瓶颈工位

        Args:
            station_cycles: 多工位节拍列表

        Returns:
            Optional[MultiStationCycle]: 瓶颈工位
        """
        if not station_cycles:
            return None

        return max(station_cycles, key=lambda s: s.cycle_time)

    def analyze_station_loads(
        self,
        station_cycles: List[MultiStationCycle],
        bottleneck_time: float
    ) -> List[StationLoad]:
        """
        分析各工位负荷

        Args:
            station_cycles: 多工位节拍列表
            bottleneck_time: 瓶颈时间

        Returns:
            List[StationLoad]: 工位负荷列表
        """
        if bottleneck_time <= 0:
            return []

        results = []

        for cycle in station_cycles:
            # 计算负荷率（相对于瓶颈）
            load_rate = (cycle.cycle_time / bottleneck_time) * 100

            # 判断是否瓶颈
            is_bottleneck = (cycle.cycle_time >= bottleneck_time)

            # 判断是否空闲过多
            idle_rate = (cycle.wait_time / cycle.cycle_time) * 100 if cycle.cycle_time > 0 else 0
            is_idle = (idle_rate > self.idle_threshold)

            results.append(StationLoad(
                station_id=cycle.station_id,
                station_name=cycle.station_name,
                load_rate=load_rate,
                work_time=cycle.work_time,
                wait_time=cycle.wait_time,
                is_bottleneck=is_bottleneck,
                is_idle=is_idle
            ))

        return results

    def calculate_full_metrics(
        self,
        station_sequences: Dict[int, ActionSequence],
        station_names: Optional[Dict[int, str]] = None,
        actual_workers: int = 1
    ) -> LineBalanceMetrics:
        """
        计算完整线平衡指标

        Args:
            station_sequences: 各工位动作序列
            station_names: 工位名称字典（可选）
            actual_workers: 实际人数

        Returns:
            LineBalanceMetrics: 线平衡指标对象
        """
        if not station_sequences:
            return LineBalanceMetrics(
                line_balance_rate=0.0,
                balance_loss_rate=100.0,
                bottleneck_station='',
                bottleneck_time=0.0,
                total_work_time=0.0,
                total_wait_time=0.0,
                station_count=0,
                theoretical_min_workers=0,
                actual_workers=actual_workers,
                worker_efficiency=0.0,
                work_distribution={}
            )

        # 转换为工位节拍列表
        station_cycles = []
        for station_id, sequence in station_sequences.items():
            name = station_names.get(station_id, f"工位{station_id}") if station_names else f"工位{station_id}"
            work_time = sum(a.duration for a in sequence.actions if a.action_type.value != 'Wait')
            wait_time = sum(a.duration for a in sequence.actions if a.action_type.value == 'Wait')
            station_cycles.append(MultiStationCycle(
                station_id=station_id,
                station_name=name,
                cycle_time=sequence.total_duration,
                wait_time=wait_time,
                work_time=work_time,
                efficiency=(work_time / sequence.total_duration * 100) if sequence.total_duration > 0 else 0
            ))

        # 计算基础指标
        bottleneck = self.identify_bottleneck(station_cycles)
        bottleneck_time = bottleneck.cycle_time if bottleneck else 0.0
        bottleneck_name = bottleneck.station_name if bottleneck else ''

        # 计算线平衡率
        lbr = self.calculate_line_balance_rate(station_cycles)
        loss_rate = self.calculate_balance_loss_rate(lbr)

        # 计算总时间和等待时间
        total_work = sum(s.work_time for s in station_cycles)
        total_wait = sum(s.wait_time for s in station_cycles)

        # 计算理论最小人数
        min_workers = self.calculate_theoretical_min_workers(station_cycles, bottleneck_time)

        # 计算人员效率
        worker_efficiency = 0.0
        if actual_workers > 0 and min_workers > 0:
            worker_efficiency = (min_workers / actual_workers) * 100

        # 计算负荷分布
        work_distribution = {}
        for cycle in station_cycles:
            work_distribution[cycle.station_name] = cycle.cycle_time

        return LineBalanceMetrics(
            line_balance_rate=lbr,
            balance_loss_rate=loss_rate,
            bottleneck_station=bottleneck_name,
            bottleneck_time=bottleneck_time,
            total_work_time=total_work,
            total_wait_time=total_wait,
            station_count=len(station_sequences),
            theoretical_min_workers=min_workers,
            actual_workers=actual_workers,
            worker_efficiency=worker_efficiency,
            work_distribution=work_distribution
        )

    def generate_balance_report(
        self,
        metrics: LineBalanceMetrics
    ) -> str:
        """
        生成线平衡分析报告

        Args:
            metrics: 线平衡指标

        Returns:
            str: 报告文本
        """
        report = f"""
线平衡分析报告
====================

基础指标：
- 线平衡率：{metrics.line_balance_rate:.1f}%
- 平衡损失率：{metrics.balance_loss_rate:.1f}%
- 工位数量：{metrics.station_count}

瓶颈分析：
- 瓶颈工位：{metrics.bottleneck_station}
- 瓶颈时间：{metrics.bottleneck_time:.2f} 秒

时间分布：
- 总工作时间：{metrics.total_work_time:.2f} 秒
- 总等待时间：{metrics.total_wait_time:.2f} 秒

人员配置：
- 理论最小人数：{metrics.theoretical_min_workers} 人
- 实际人数：{metrics.actual_workers} 人
- 人员效率：{metrics.worker_efficiency:.1f}%

工位负荷分布：
"""
        for station, time_val in metrics.work_distribution.items():
            report += f"- {station}: {time_val:.2f} 秒\n"

        report += "\n优化建议：\n"
        if metrics.line_balance_rate < 80:
            report += "- 线平衡率偏低，建议重新分配工作内容\n"
        if metrics.balance_loss_rate > 20:
            report += "- 平衡损失较高，建议拆分瓶颈工位或合并空闲工位\n"
        if metrics.worker_efficiency < 85:
            report += "- 人员效率偏低，建议优化人员配置\n"
        else:
            report += "- 线平衡状态良好，建议保持当前配置\n"

        return report

    def suggest_improvements(
        self,
        metrics: LineBalanceMetrics,
        station_loads: Optional[List[StationLoad]] = None
    ) -> List[str]:
        """
        生成改善建议列表

        Args:
            metrics: 线平衡指标
            station_loads: 工位负荷列表（可选）

        Returns:
            List[str]: 改善建议列表
        """
        suggestions = []

        # 基于线平衡率
        if metrics.line_balance_rate < 70:
            suggestions.append("【紧急】线平衡率低于70%，存在严重不均衡，建议立即进行工序重组")
        elif metrics.line_balance_rate < 80:
            suggestions.append("【警告】线平衡率低于80%，建议拆分瓶颈工位作业内容")
        elif metrics.line_balance_rate < 90:
            suggestions.append("【建议】线平衡率良好，可进一步优化空闲工位")
        else:
            suggestions.append("【优秀】线平衡率高于90%，产线配置合理")

        # 基于瓶颈工位
        if metrics.bottleneck_time > 0:
            suggestions.append(f"瓶颈工位：{metrics.bottleneck_station}，节拍时间：{metrics.bottleneck_time:.1f}秒")

            # 拆分建议
            if metrics.bottleneck_time > metrics.total_work_time / metrics.station_count * 1.5:
                suggestions.append("建议拆分瓶颈工位作业内容，分配给相邻空闲工位")

        # 基于工位负荷
        if station_loads:
            idle_stations = [s for s in station_loads if s.is_idle]
            if idle_stations:
                idle_names = [s.station_name for s in idle_stations]
                suggestions.append(f"空闲过多工位：{', '.join(idle_names)}，建议增加作业内容或合并工位")

            overload_stations = [s for s in station_loads if s.load_rate > self.overload_threshold]
            if overload_stations:
                overload_names = [s.station_name for s in overload_stations]
                suggestions.append(f"负荷过重工位：{', '.join(overload_names)}，建议减少作业内容或增加辅助人员")

        # 基于人员配置
        if metrics.actual_workers > metrics.theoretical_min_workers:
            excess = metrics.actual_workers - metrics.theoretical_min_workers
            suggestions.append(f"当前人员配置超出理论需求{excess}人，可考虑优化人员编制")

        return suggestions

    def calculate_balance_chart_data(
        self,
        metrics: LineBalanceMetrics
    ) -> Dict:
        """
        生成平衡图表数据（用于可视化）

        Args:
            metrics: 线平衡指标

        Returns:
            Dict: 图表数据
        """
        return {
            'line_balance_rate': metrics.line_balance_rate,
            'balance_loss_rate': metrics.balance_loss_rate,
            'bottleneck': {
                'station': metrics.bottleneck_station,
                'time': metrics.bottleneck_time
            },
            'work_distribution': metrics.work_distribution,
            'time_analysis': {
                'work': metrics.total_work_time,
                'wait': metrics.total_wait_time,
                'total': metrics.total_work_time + metrics.total_wait_time
            },
            'worker_config': {
                'min_required': metrics.theoretical_min_workers,
                'actual': metrics.actual_workers,
                'efficiency': metrics.worker_efficiency
            }
        }


def analyze_line_balance(
    station_sequences: Dict[int, ActionSequence],
    actual_workers: int = 1
) -> LineBalanceMetrics:
    """
    便捷函数：分析线平衡率

    Args:
        station_sequences: 各工位动作序列
        actual_workers: 实际人数

    Returns:
        LineBalanceMetrics: 线平衡指标
    """
    analyzer = LineBalanceAnalyzer()
    return analyzer.calculate_full_metrics(station_sequences, actual_workers=actual_workers)