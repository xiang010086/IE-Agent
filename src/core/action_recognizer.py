"""
动作识别规则引擎
功能：基于关键点序列检测 R/G/M/RL/W/Assemble 动作
版本：v3.0 (Day 3交付 - 整合Assemble组合动作)
日期：2025-05-21
"""
import numpy as np
from typing import List, Optional, Dict, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from src.core.pose_estimator import Keypoint, PoseResult

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from src.core.wait_detector import WaitDetector
else:
    # 实际运行时导入
    from src.core.wait_detector import WaitDetector, ActionType as WaitActionType


class ActionType(Enum):
    """动作类型枚举"""
    NONE = "None"
    REACH = "Reach"      # R - 伸手
    GRASP = "Grasp"      # G - 抓取
    MOVE = "Move"        # M - 移动
    RELEASE = "Release"  # RL - 放开
    WAIT = "Wait"        # W - 等待（Day 1实现）
    ASSEMBLE = "Assemble"  # 组合动作（R+G+M+RL合并）（Day 3实现）


@dataclass
class Action:
    """单个动作数据结构"""
    action_type: ActionType
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    duration: float
    tmu_value: float  # MTM工时值（TMU）
    distance_category: str = "medium"  # 距离分类：short/medium/long
    confidence: float = 0.0
    keypoints_data: List[Dict] = field(default_factory=list)


@dataclass
class ActionSequence:
    """动作序列数据结构"""
    actions: List[Action]
    total_duration: float
    total_tmu: float
    action_counts: Dict[str, int]


class ActionRecognizer:
    """
    动作识别规则引擎
    基于MediaPipe关键点检测R/G/M/RL四种核心动作
    """

    def __init__(
        self,
        velocity_threshold_reach: float = 0.15,
        velocity_threshold_grasp: float = 0.05,
        velocity_threshold_move: float = 0.1,
        velocity_threshold_release: float = 0.05,
        velocity_threshold_wait: float = 0.02,
        arm_angle_threshold_reach: float = 150,
        arm_angle_threshold_release: float = 150,
        min_duration_wait: float = 1.0,
        fps: float = 30.0
    ):
        """
        初始化动作识别器

        Args:
            velocity_threshold_reach: Reach速度阈值
            velocity_threshold_grasp: Grasp速度阈值（骤降）
            velocity_threshold_move: Move速度阈值
            velocity_threshold_release: Release速度阈值
            velocity_threshold_wait: Wait静止阈值
            arm_angle_threshold_reach: Reach手臂伸展角度
            arm_angle_threshold_release: Release手臂伸展角度
            min_duration_wait: Wait最小持续时间
            fps: 视频帧率
        """
        self.velocity_threshold_reach = velocity_threshold_reach
        self.velocity_threshold_grasp = velocity_threshold_grasp
        self.velocity_threshold_move = velocity_threshold_move
        self.velocity_threshold_release = velocity_threshold_release
        self.velocity_threshold_wait = velocity_threshold_wait
        self.arm_angle_threshold_reach = arm_angle_threshold_reach
        self.arm_angle_threshold_release = arm_angle_threshold_release
        self.min_duration_wait = min_duration_wait
        self.fps = fps

        # 状态跟踪
        self.current_action: Optional[ActionType] = ActionType.NONE
        self.action_start_frame: int = 0
        self.action_start_time: float = 0.0
        self.prev_action: Optional[ActionType] = ActionType.NONE
        self.prev_action_end_time: float = 0.0

        # 历史数据
        self.pose_history: List[PoseResult] = []
        self.velocity_history: List[Dict[str, float]] = []
        self.action_sequence: List[Action] = []

        # Wait检测器（Day 1新增）
        self.wait_detector = WaitDetector(
            static_velocity_threshold=velocity_threshold_wait,
            min_wait_duration=min_duration_wait,
            fps=fps
        )

        # 关键点索引（MediaPipe Pose）
        self.LEFT_WRIST = 15
        self.RIGHT_WRIST = 16
        self.LEFT_ELBOW = 13
        self.RIGHT_ELBOW = 14
        self.LEFT_SHOULDER = 11
        self.RIGHT_SHOULDER = 12

    def calculate_velocity(self, pose1: PoseResult, pose2: PoseResult) -> Dict[str, float]:
        """
        计算关键点速度

        Args:
            pose1: 前一帧姿态结果
            pose2: 当前帧姿态结果

        Returns:
            Dict: 各关键点速度
        """
        velocities = {}

        if not pose1.has_pose or not pose2.has_pose:
            return velocities

        time_diff = 1.0 / self.fps

        # 计算手腕速度
        for wrist_idx, elbow_idx, name in [
            (self.LEFT_WRIST, self.LEFT_ELBOW, 'left_wrist'),
            (self.RIGHT_WRIST, self.RIGHT_ELBOW, 'right_wrist')
        ]:
            if wrist_idx < len(pose1.keypoints) and wrist_idx < len(pose2.keypoints):
                kp1 = pose1.keypoints[wrist_idx]
                kp2 = pose2.keypoints[wrist_idx]

                dx = kp2.x - kp1.x
                dy = kp2.y - kp1.y
                distance = np.sqrt(dx**2 + dy**2)
                velocity = distance / time_diff

                velocities[name] = velocity

        # 计算全身平均速度（用于Wait检测）
        total_velocity = 0.0
        count = 0
        for kp1, kp2 in zip(pose1.keypoints, pose2.keypoints):
            dx = kp2.x - kp1.x
            dy = kp2.y - kp1.y
            distance = np.sqrt(dx**2 + dy**2)
            total_velocity += distance / time_diff
            count += 1

        if count > 0:
            velocities['body_avg'] = total_velocity / count

        return velocities

    def calculate_arm_angle(self, pose: PoseResult, side: str = 'right') -> float:
        """
        计算手臂伸展角度

        Args:
            pose: 帿态结果
            side: 'left' 或 'right'

        Returns:
            float: 手臂角度（度）
        """
        if not pose.has_pose:
            return 0.0

        if side == 'left':
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST

        if any(idx >= len(pose.keypoints) for idx in [shoulder_idx, elbow_idx, wrist_idx]):
            return 0.0

        shoulder = pose.keypoints[shoulder_idx]
        elbow = pose.keypoints[elbow_idx]
        wrist = pose.keypoints[wrist_idx]

        # 计算向量
        vec1 = np.array([elbow.x - shoulder.x, elbow.y - shoulder.y])
        vec2 = np.array([wrist.x - elbow.x, wrist.y - elbow.y])

        # 计算角度
        cos_angle = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        angle_deg = np.degrees(angle)

        return angle_deg

    def detect_reach(self, velocities: Dict[str, float], pose: PoseResult) -> bool:
        """
        检测Reach动作

        Args:
            velocities: 当前速度
            pose: 当前姿态

        Returns:
            bool: 是否检测到Reach
        """
        # 检查手腕速度
        wrist_velocity = max(
            velocities.get('left_wrist', 0),
            velocities.get('right_wrist', 0)
        )

        # 检查手臂角度
        arm_angle = max(
            self.calculate_arm_angle(pose, 'left'),
            self.calculate_arm_angle(pose, 'right')
        )

        # Reach触发条件
        return (
            wrist_velocity > self.velocity_threshold_reach and
            arm_angle > self.arm_angle_threshold_reach
        )

    def detect_grasp(self, velocities: Dict[str, float], pose: PoseResult) -> bool:
        """
        检测Grasp动作

        Args:
            velocities: 当前速度
            pose: 当前姿态

        Returns:
            bool: 是否检测到Grasp
        """
        # 检查手腕速度骤降
        wrist_velocity = min(
            velocities.get('left_wrist', 1.0),
            velocities.get('right_wrist', 1.0)
        )

        # Grasp触发条件：速度骤降 + 前一动作是Reach
        return (
            wrist_velocity < self.velocity_threshold_grasp and
            self.current_action == ActionType.REACH
        )

    def detect_move(self, velocities: Dict[str, float], pose: PoseResult) -> bool:
        """
        检测Move动作

        Args:
            velocities: 当前速度
            pose: 当前姿态

        Returns:
            bool: 是否检测到Move
        """
        # 检查手腕稳定移动
        wrist_velocity = max(
            velocities.get('left_wrist', 0),
            velocities.get('right_wrist', 0)
        )

        # Move触发条件：速度稳定 + 前一动作是Grasp
        return (
            wrist_velocity > self.velocity_threshold_move and
            self.current_action == ActionType.GRASP
        )

    def detect_release(self, velocities: Dict[str, float], pose: PoseResult) -> bool:
        """
        检测Release动作

        Args:
            velocities: 当前速度
            pose: 当前姿态

        Returns:
            bool: 是否检测到Release
        """
        # 检查手腕速度骤降
        wrist_velocity = min(
            velocities.get('left_wrist', 1.0),
            velocities.get('right_wrist', 1.0)
        )

        # 检查手臂伸展
        arm_angle = max(
            self.calculate_arm_angle(pose, 'left'),
            self.calculate_arm_angle(pose, 'right')
        )

        # Release触发条件：速度骤降 + 手臂伸展 + 前一动作是Move或Grasp
        return (
            wrist_velocity < self.velocity_threshold_release and
            arm_angle > self.arm_angle_threshold_release and
            self.current_action in [ActionType.MOVE, ActionType.GRASP]
        )

    def process_frame(self, pose_result: PoseResult) -> Optional[Action]:
        """
        处理单帧，进行动作识别（包含Wait检测）

        Args:
            pose_result: 当前帧姿态结果

        Returns:
            Optional[Action]: 如果动作结束，返回动作对象；否则返回None
        """
        # 添加到历史
        self.pose_history.append(pose_result)

        # 计算速度
        if len(self.pose_history) >= 2:
            velocities = self.calculate_velocity(
                self.pose_history[-2],
                self.pose_history[-1]
            )
            self.velocity_history.append(velocities)
        else:
            velocities = {}

        # 检测动作（优先级：R > G > M > RL）
        detected_action = None
        if pose_result.has_pose:
            if self.detect_reach(velocities, pose_result):
                detected_action = ActionType.REACH
            elif self.detect_grasp(velocities, pose_result):
                detected_action = ActionType.GRASP
            elif self.detect_move(velocities, pose_result):
                detected_action = ActionType.MOVE
            elif self.detect_release(velocities, pose_result):
                detected_action = ActionType.RELEASE

        # Wait检测（Day 1新增）
        wait_action = self.wait_detector.detect_wait(
            pose_result,
            self.current_action
        )

        # 如果检测到Wait动作结束，添加到序列
        if wait_action:
            wait_action_obj = self._create_action(
                ActionType.WAIT,
                wait_action['start_frame'],
                wait_action['end_frame'],
                wait_action['start_time'],
                wait_action['end_time']
            )
            self.action_sequence.append(wait_action_obj)

        # 如果正在等待，设置当前动作为WAIT
        if self.wait_detector.is_currently_waiting():
            detected_action = ActionType.WAIT

        # 处理动作状态变化
        completed_action = None

        if detected_action != self.current_action:
            # 当前动作结束
            if self.current_action != ActionType.NONE:
                completed_action = self._create_action(
                    self.current_action,
                    self.action_start_frame,
                    pose_result.frame_id - 1,
                    self.action_start_time,
                    pose_result.timestamp - (1.0 / self.fps)
                )
                self.action_sequence.append(completed_action)

            # 新动作开始
            self.prev_action = self.current_action
            self.prev_action_end_time = pose_result.timestamp
            self.current_action = detected_action or ActionType.NONE
            self.action_start_frame = pose_result.frame_id
            self.action_start_time = pose_result.timestamp

        return completed_action

    def _create_action(
        self,
        action_type: ActionType,
        start_frame: int,
        end_frame: int,
        start_time: float,
        end_time: float
    ) -> Action:
        """
        创建动作对象

        Args:
            action_type: 动作类型
            start_frame: 开始帧
            end_frame: 结束帧
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            Action: 动作对象
        """
        duration = end_time - start_time
        tmu_value = self._get_tmu_value(action_type)

        return Action(
            action_type=action_type,
            start_frame=start_frame,
            end_frame=end_frame,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            tmu_value=tmu_value,
            confidence=0.8
        )

    def _get_tmu_value(self, action_type: ActionType) -> float:
        """
        获取MTM工时值（默认使用中等距离）

        Args:
            action_type: 动作类型

        Returns:
            float: TMU值
        """
        tmu_values = {
            ActionType.REACH: 15,    # R-A-medium
            ActionType.GRASP: 5,     # G1
            ActionType.MOVE: 18,     # M-A-medium
            ActionType.RELEASE: 2,   # RL1
            ActionType.WAIT: 0,      # Wait不计入工时
            ActionType.ASSEMBLE: 40, # 基础组合值（R+G+M+RL），实际应动态计算
            ActionType.NONE: 0
        }
        return tmu_values.get(action_type, 0)

    def detect_assemble_patterns(self, actions: List[Action]) -> List[Action]:
        """
        检测并合并Assemble组合动作（R+G+M+RL序列）

        Args:
            actions: 原始动作列表

        Returns:
            List[Action]: 合并后的动作列表
        """
        if len(actions) < 4:
            return actions

        merged_actions = []
        i = 0

        while i < len(actions):
            # 检查是否存在 R→G→M→RL 连续序列
            if i + 3 < len(actions):
                seq = [
                    actions[i].action_type,
                    actions[i+1].action_type,
                    actions[i+2].action_type,
                    actions[i+3].action_type
                ]

                # 检查是否符合 Assemble 模式
                if seq == [ActionType.REACH, ActionType.GRASP, ActionType.MOVE, ActionType.RELEASE]:
                    # 创建合并的 Assemble 动作
                    assemble_action = self._merge_assemble(
                        actions[i],
                        actions[i+1],
                        actions[i+2],
                        actions[i+3]
                    )
                    merged_actions.append(assemble_action)
                    i += 4  # 跳过已合并的4个动作
                    continue

            # 不符合模式，保留原动作
            merged_actions.append(actions[i])
            i += 1

        return merged_actions

    def _merge_assemble(
        self,
        reach: Action,
        grasp: Action,
        move: Action,
        release: Action
    ) -> Action:
        """
        合并 R+G+M+RL 为一个 Assemble 动作

        Args:
            reach: Reach动作
            grasp: Grasp动作
            move: Move动作
            release: Release动作

        Returns:
            Action: 合并后的Assemble动作
        """
        # 计算合并后的时间范围
        start_frame = reach.start_frame
        end_frame = release.end_frame
        start_time = reach.start_time
        end_time = release.end_time
        duration = end_time - start_time

        # 计算合并后的TMU值（累加）
        total_tmu = reach.tmu_value + grasp.tmu_value + move.tmu_value + release.tmu_value

        # 合并关键点数据
        merged_keypoints = []
        for action in [reach, grasp, move, release]:
            merged_keypoints.extend(action.keypoints_data)

        return Action(
            action_type=ActionType.ASSEMBLE,
            start_frame=start_frame,
            end_frame=end_frame,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            tmu_value=total_tmu,
            distance_category="combined",
            confidence=0.85,
            keypoints_data=merged_keypoints
        )

    def get_action_sequence(self, merge_assemble: bool = True) -> ActionSequence:
        """
        获取完整动作序列

        Args:
            merge_assemble: 是否合并Assemble组合动作

        Returns:
            ActionSequence: 动作序列对象
        """
        # 处理动作序列（可选合并Assemble）
        final_actions = self.action_sequence
        if merge_assemble:
            final_actions = self.detect_assemble_patterns(self.action_sequence)

        total_duration = sum(a.duration for a in final_actions)
        total_tmu = sum(a.tmu_value for a in final_actions)

        action_counts = {}
        for action in final_actions:
            key = action.action_type.value
            action_counts[key] = action_counts.get(key, 0) + 1

        return ActionSequence(
            actions=final_actions,
            total_duration=total_duration,
            total_tmu=total_tmu,
            action_counts=action_counts
        )

    def reset(self):
        """
        重置识别器状态
        """
        self.current_action = ActionType.NONE
        self.action_start_frame = 0
        self.action_start_time = 0.0
        self.prev_action = ActionType.NONE
        self.prev_action_end_time = 0.0
        self.pose_history = []
        self.velocity_history = []
        self.action_sequence = []


def analyze_video_actions(
    pose_results: List[PoseResult],
    fps: float = 30.0,
    merge_assemble: bool = True
) -> ActionSequence:
    """
    分析视频动作序列（便捷函数）

    Args:
        pose_results: 帿态结果列表
        fps: 视频帧率

    Returns:
        ActionSequence: 动作序列
    """
    recognizer = ActionRecognizer(fps=fps)

    for pose_result in pose_results:
        recognizer.process_frame(pose_result)

    # 处理最后一个动作
    if recognizer.current_action != ActionType.NONE:
        last_pose = pose_results[-1]
        action = recognizer._create_action(
            recognizer.current_action,
            recognizer.action_start_frame,
            last_pose.frame_id,
            recognizer.action_start_time,
            last_pose.timestamp
        )
        recognizer.action_sequence.append(action)

    return recognizer.get_action_sequence(merge_assemble=merge_assemble)