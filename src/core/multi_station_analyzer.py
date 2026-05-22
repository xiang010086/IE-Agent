"""
多工位分析模块
功能：支持多工位视频分析、产线综合分析
版本：v1.0 (Day 3交付)
日期：2025-05-21

多工位分析功能：
- 支持多个工位视频上传和处理
- 每个工位独立动作识别和节拍分析
- 产线整体平衡率计算
- 瓶颈工位识别与改善建议
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np

from src.core.pose_estimator import PoseResult
from src.core.action_recognizer import ActionSequence, ActionRecognizer, ActionType
from src.core.mtm_analyzer import MTMAnalyzer
from src.core.cycle_time_calculator import CycleTimeCalculator, CycleTimeMetrics, MultiStationCycle
from src.core.line_balance_analyzer import LineBalanceAnalyzer, LineBalanceMetrics


@dataclass
class StationAnalysis:
    """工位分析结果数据结构"""
    station_id: int
    station_name: str
    action_sequence: ActionSequence
    cycle_metrics: CycleTimeMetrics
    efficiency: float  # 工位效率
    wait_ratio: float  # 等待时间占比


@dataclass
class ProductionLineAnalysis:
    """产线整体分析结果"""
    stations: List[StationAnalysis]
    line_balance: LineBalanceMetrics
    bottleneck_station: StationAnalysis
    total_production_time: float
    line_efficiency: float
    improvement_suggestions: List[str]


class MultiStationAnalyzer:
    """
    多工位分析器
    支持多个工位的独立分析和产线整体分析
    """

    def __init__(
        self,
        station_names: Optional[Dict[int, str]] = None,
        daily_demand: Optional[float] = None,
        shift_count: int = 1,
        actual_workers: int = 1,
        fps: float = 30.0
    ):
        """
        初始化多工位分析器

        Args:
            station_names: 工位名称字典 {工位ID: 名称}
            daily_demand: 每日需求量
            shift_count: 班次数量
            actual_workers: 实际人数
            fps: 视频帧率
        """
        self.station_names = station_names or {}
        self.daily_demand = daily_demand
        self.shift_count = shift_count
        self.actual_workers = actual_workers
        self.fps = fps

        # 分析器实例
        self.action_recognizer = ActionRecognizer(fps=fps)
        self.mtm_analyzer = MTMAnalyzer()
        self.cycle_calculator = CycleTimeCalculator()
        self.line_balance_analyzer = LineBalanceAnalyzer()

        # 工位分析结果存储
        self.station_results: Dict[int, StationAnalysis] = {}

    def analyze_station(
        self,
        station_id: int,
        pose_results: List[PoseResult],
        merge_assemble: bool = True
    ) -> StationAnalysis:
        """
        分析单个工位

        Args:
            station_id: 工位ID
            pose_results: 帧态结果列表
            merge_assemble: 是否合并Assemble组合动作

        Returns:
            StationAnalysis: 工位分析结果
        """
        # 动作识别
        self.action_recognizer.reset()
        for pose in pose_results:
            self.action_recognizer.process_frame(pose)

        action_sequence = self.action_recognizer.get_action_sequence(merge_assemble=merge_assemble)

        # 节拍计算
        cycle_metrics = self.cycle_calculator.calculate_cycle_metrics(
            action_sequence,
            self.daily_demand,
            self.shift_count
        )

        # 计算效率
        work_time = sum(
            a.duration for a in action_sequence.actions
            if a.action_type != ActionType.WAIT
        )
        wait_time = sum(
            a.duration for a in action_sequence.actions
            if a.action_type == ActionType.WAIT
        )
        total_time = action_sequence.total_duration

        efficiency = (work_time / total_time * 100) if total_time > 0 else 0.0
        wait_ratio = (wait_time / total_time * 100) if total_time > 0 else 0.0

        # 工位名称
        station_name = self.station_names.get(station_id, f"工位{station_id}")

        result = StationAnalysis(
            station_id=station_id,
            station_name=station_name,
            action_sequence=action_sequence,
            cycle_metrics=cycle_metrics,
            efficiency=efficiency,
            wait_ratio=wait_ratio
        )

        # 存储结果
        self.station_results[station_id] = result

        return result

    def analyze_multiple_stations(
        self,
        station_data: Dict[int, List[PoseResult]],
        merge_assemble: bool = True
    ) -> ProductionLineAnalysis:
        """
        分析多工位产线

        Args:
            station_data: 多工位数据 {工位ID: 帧态结果列表}
            merge_assemble: 是否合并Assemble组合动作

        Returns:
            ProductionLineAnalysis: 产线整体分析结果
        """
        # 分析每个工位
        station_analyses = []
        for station_id, pose_results in station_data.items():
            analysis = self.analyze_station(station_id, pose_results, merge_assemble)
            station_analyses.append(analysis)

        # 转换为多工位节拍数据
        station_cycles = []
        station_sequences = {}
        for analysis in station_analyses:
            work_time = sum(
                a.duration for a in analysis.action_sequence.actions
                if a.action_type != ActionType.WAIT
            )
            wait_time = sum(
                a.duration for a in analysis.action_sequence.actions
                if a.action_type == ActionType.WAIT
            )

            station_cycles.append(MultiStationCycle(
                station_id=analysis.station_id,
                station_name=analysis.station_name,
                cycle_time=analysis.action_sequence.total_duration,
                wait_time=wait_time,
                work_time=work_time,
                efficiency=analysis.efficiency
            ))

            station_sequences[analysis.station_id] = analysis.action_sequence

        # 计算线平衡率
        line_balance = self.line_balance_analyzer.calculate_full_metrics(
            station_sequences,
            self.station_names,
            self.actual_workers
        )

        # 识别瓶颈工位
        bottleneck = self.line_balance_analyzer.identify_bottleneck(station_cycles)
        bottleneck_analysis = None
        if bottleneck:
            for analysis in station_analyses:
                if analysis.station_id == bottleneck.station_id:
                    bottleneck_analysis = analysis
                    break

        # 计算产线总时间
        total_production_time = sum(s.cycle_time for s in station_cycles)

        # 计算产线整体效率
        line_efficiency = line_balance.line_balance_rate

        # 生成改善建议
        suggestions = self.line_balance_analyzer.suggest_improvements(line_balance)

        return ProductionLineAnalysis(
            stations=station_analyses,
            line_balance=line_balance,
            bottleneck_station=bottleneck_analysis,
            total_production_time=total_production_time,
            line_efficiency=line_efficiency,
            improvement_suggestions=suggestions
        )

    def generate_line_report(self, analysis: ProductionLineAnalysis) -> str:
        """
        生成产线分析报告文本

        Args:
            analysis: 产线分析结果

        Returns:
            str: 报告文本
        """
        report = f"""
产线综合分析报告
====================

一、工位概况
工位数量：{len(analysis.stations)}
总生产时间：{analysis.total_production_time:.2f} 秒

"""

        # 各工位详情
        report += "二、各工位分析\n"
        for station in analysis.stations:
            report += f"""
【{station.station_name}】
- 节拍时间：{station.action_sequence.total_duration:.2f} 秒
- 工位效率：{station.efficiency:.1f}%
- 等待占比：{station.wait_ratio:.1f}%
- 动作数量：{len(station.action_sequence.actions)} 个
"""

        # 线平衡分析
        report += f"""
三、线平衡分析
- 线平衡率：{analysis.line_balance.line_balance_rate:.1f}%
- 平衡损失率：{analysis.line_balance.balance_loss_rate:.1f}%
- 瓶颈工位：{analysis.line_balance.bottleneck_station}
- 瓶颈时间：{analysis.line_balance.bottleneck_time:.2f} 秒
- 理论最小人数：{analysis.line_balance.theoretical_min_workers} 人
- 人员效率：{analysis.line_balance.worker_efficiency:.1f}%

"""

        # 改善建议
        report += "四、改善建议\n"
        for suggestion in analysis.improvement_suggestions:
            report += f"- {suggestion}\n"

        return report

    def get_station_work_distribution(self, analysis: ProductionLineAnalysis) -> Dict[str, float]:
        """
        获取工位负荷分布数据（用于可视化）

        Args:
            analysis: 产线分析结果

        Returns:
            Dict[str, float]: 工位负荷分布
        """
        distribution = {}
        for station in analysis.stations:
            distribution[station.station_name] = station.action_sequence.total_duration
        return distribution

    def get_comparison_chart_data(self, analysis: ProductionLineAnalysis) -> Dict:
        """
        获取工位对比图表数据

        Args:
            analysis: 产线分析结果

        Returns:
            Dict: 图表数据
        """
        return {
            'station_names': [s.station_name for s in analysis.stations],
            'cycle_times': [s.action_sequence.total_duration for s in analysis.stations],
            'efficiencies': [s.efficiency for s in analysis.stations],
            'wait_ratios': [s.wait_ratio for s in analysis.stations],
            'action_counts': [len(s.action_sequence.actions) for s in analysis.stations],
            'bottleneck_id': analysis.bottleneck_station.station_id if analysis.bottleneck_station else 0
        }


def analyze_production_line(
    station_data: Dict[int, List[PoseResult]],
    station_names: Optional[Dict[int, str]] = None,
    daily_demand: Optional[float] = None,
    actual_workers: int = 1
) -> ProductionLineAnalysis:
    """
    便捷函数：分析产线

    Args:
        station_data: 多工位数据
        station_names: 工位名称
        daily_demand: 每日需求量
        actual_workers: 实际人数

    Returns:
        ProductionLineAnalysis: 产线分析结果
    """
    analyzer = MultiStationAnalyzer(
        station_names=station_names,
        daily_demand=daily_demand,
        actual_workers=actual_workers
    )
    return analyzer.analyze_multiple_stations(station_data)