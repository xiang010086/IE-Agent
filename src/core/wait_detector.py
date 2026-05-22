"""
Wait动作检测器
功能：基于全身静止检测等待动作
版本：v1.0 (Day 1交付 - 加分项)
日期：2025-05-21

Wait识别规则：
- 全身关键点位移速度 < 静止阈值（默认：0.02帧/秒）
- 持续时间 > 最小等待时长（默认：1.0秒）
- 无R/G/M动作正在执行
"""
import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

# 本地定义ActionType以避免循环导入
class ActionType(Enum):
    """动作类型枚举"""
    NONE = "None"
    REACH = "Reach"
    GRASP = "Grasp"
    MOVE = "Move"
    RELEASE = "Release"
    WAIT = "Wait"

from src.core.pose_estimator import PoseResult, Keypoint


@dataclass
class WaitState:
    """等待状态数据结构"""
    is_waiting: bool
    start_frame: int
    start_time: float
    duration: float
    static_velocity: float


class WaitDetector:
    """
    Wait动作检测器
    检测全身静止超过最小等待时长的情况
    """

    def __init__(
        self,
        static_velocity_threshold: float = 0.02,
        min_wait_duration: float = 1.0,
        max_wait_duration: float = 30.0,
        fps: float = 30.0
    ):
        """
        初始化Wait检测器

        Args:
            static_velocity_threshold: 静止速度阈值（默认0.02）
            min_wait_duration: 最小等待时长（秒，默认1.0）
            max_wait_duration: 最大等待时长（秒，默认30.0）
            fps: 视频帧率
        """
        self.static_velocity_threshold = static_velocity_threshold
        self.min_wait_duration = min_wait_duration
        self.max_wait_duration = max_wait_duration
        self.fps = fps

        # 状态跟踪
        self.wait_state: Optional[WaitState] = None
        self.pose_history: List[PoseResult] = []
        self.velocity_history: List[float] = []

        # Wait动作记录
        self.wait_actions: List[Dict] = []

    def calculate_body_velocity(
        self,
        pose1: PoseResult,
        pose2: PoseResult
    ) -> float:
        """
        计算全身平均速度

        Args:
            pose1: 前一帧姿态
            pose2: 当前帧姿态

        Returns:
            float: 全身平均速度
        """
        if not pose1.has_pose or not pose2.has_pose:
            return 1.0  # 无姿态时返回高速度（非静止）

        time_diff = 1.0 / self.fps
        total_velocity = 0.0
        count = 0

        # 计算所有关键点的平均速度
        for kp1, kp2 in zip(pose1.keypoints, pose2.keypoints):
            if kp1.visibility > 0.5 and kp2.visibility > 0.5:
                dx = kp2.x - kp1.x
                dy = kp2.y - kp1.y
                distance = np.sqrt(dx**2 + dy**2)
                velocity = distance / time_diff
                total_velocity += velocity
                count += 1

        if count > 0:
            return total_velocity / count
        return 1.0

    def detect_wait(
        self,
        pose_result: PoseResult,
        current_action: ActionType
    ) -> Optional[Dict]:
        """
        检测Wait动作

        Args:
            pose_result: 当前帧姿态结果
            current_action: 当前正在执行的动作

        Returns:
            Optional[Dict]: 如果检测到Wait动作结束，返回动作信息；否则返回None
        """
        # 添加到历史
        self.pose_history.append(pose_result)

        # 计算速度
        if len(self.pose_history) >= 2:
            velocity = self.calculate_body_velocity(
                self.pose_history[-2],
                self.pose_history[-1]
            )
            self.velocity_history.append(velocity)
        else:
            velocity = 1.0
            self.velocity_history.append(velocity)

        # 检测静止状态
        is_static = velocity < self.static_velocity_threshold

        # Wait检测逻辑
        detected_wait = None

        # 只有在无其他动作执行时才检测Wait
        if current_action == ActionType.NONE or current_action == ActionType.WAIT:
            if is_static:
                # 进入或继续等待状态
                if self.wait_state is None:
                    # 开始等待
                    self.wait_state = WaitState(
                        is_waiting=True,
                        start_frame=pose_result.frame_id,
                        start_time=pose_result.timestamp,
                        duration=0,
                        static_velocity=velocity
                    )
                else:
                    # 继续等待，更新持续时间
                    self.wait_state.duration = pose_result.timestamp - self.wait_state.start_time
                    self.wait_state.static_velocity = velocity

                # 检查是否达到最大等待时长
                if self.wait_state.duration >= self.max_wait_duration:
                    detected_wait = {
                        'start_frame': self.wait_state.start_frame,
                        'end_frame': pose_result.frame_id,
                        'start_time': self.wait_state.start_time,
                        'end_time': pose_result.timestamp,
                        'duration': self.wait_state.duration,
                        'velocity': self.wait_state.static_velocity
                    }
                    self.wait_actions.append(detected_wait)
                    self.wait_state = None

            else:
                # 不静止，结束等待状态
                if self.wait_state is not None:
                    # 只有超过最小等待时长才记录为Wait动作
                    if self.wait_state.duration >= self.min_wait_duration:
                        detected_wait = {
                            'start_frame': self.wait_state.start_frame,
                            'end_frame': pose_result.frame_id,
                            'start_time': self.wait_state.start_time,
                            'end_time': pose_result.timestamp,
                            'duration': self.wait_state.duration,
                            'velocity': self.wait_state.static_velocity
                        }
                        self.wait_actions.append(detected_wait)

                    # 重置等待状态
                    self.wait_state = None

        else:
            # 有其他动作执行，强制结束等待
            if self.wait_state is not None and self.wait_state.duration >= self.min_wait_duration:
                detected_wait = {
                    'start_frame': self.wait_state.start_frame,
                    'end_frame': pose_result.frame_id - 1,
                    'start_time': self.wait_state.start_time,
                    'end_time': pose_result.timestamp - (1.0 / self.fps),
                    'duration': self.wait_state.duration,
                    'velocity': self.wait_state.static_velocity
                }
                self.wait_actions.append(detected_wait)

            self.wait_state = None

        return detected_wait

    def is_currently_waiting(self) -> bool:
        """
        检查当前是否处于等待状态

        Returns:
            bool: 是否正在等待
        """
        return self.wait_state is not None and self.wait_state.is_waiting

    def get_wait_duration(self) -> float:
        """
        获取当前等待持续时间

        Returns:
            float: 等待时长（秒）
        """
        if self.wait_state:
            return self.wait_state.duration
        return 0.0

    def get_total_wait_time(self) -> float:
        """
        获取总等待时间

        Returns:
            float: 所有Wait动作的总时长
        """
        return sum(w['duration'] for w in self.wait_actions)

    def get_wait_count(self) -> int:
        """
        获取Wait动作次数

        Returns:
            int: Wait动作次数
        """
        return len(self.wait_actions)

    def get_wait_actions(self) -> List[Dict]:
        """
        获取所有Wait动作记录

        Returns:
            List[Dict]: Wait动作列表
        """
        return self.wait_actions

    def reset(self):
        """
        重置检测器状态
        """
        self.wait_state = None
        self.pose_history = []
        self.velocity_history = []
        self.wait_actions = []


def calculate_wait_loss_rate(wait_time: float, total_time: float) -> float:
    """
    计算等待损失率

    Args:
        wait_time: 等待时间（秒）
        total_time: 总观测时间（秒）

    Returns:
        float: 等待损失率（百分比）
    """
    if total_time <= 0:
        return 0.0
    return (wait_time / total_time) * 100


def evaluate_wait_efficiency(wait_loss_rate: float) -> Dict[str, str]:
    """
    评估等待效率并给出建议

    Args:
        wait_loss_rate: 等待损失率

    Returns:
        Dict: 评估结果和建议
    """
    if wait_loss_rate < 10:
        return {
            'level': '优秀',
            'color': 'green',
            'suggestion': '等待时间占比合理，无明显瓶颈'
        }
    elif wait_loss_rate < 20:
        return {
            'level': '良好',
            'color': 'yellow',
            'suggestion': '存在少量等待，建议检查物料配送是否及时'
        }
    else:
        return {
            'level': '需改善',
            'color': 'red',
            'suggestion': '等待损失过高，建议：1)检查节拍平衡 2)优化物料配送 3)排查设备响应时间'
        }