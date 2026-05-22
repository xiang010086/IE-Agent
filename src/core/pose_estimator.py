"""
姿态估计模块
功能：使用MediaPipe提取人体33关键点
版本：v1.0
日期：2025-05-21
"""
import mediapipe as mp
import numpy as np
import cv2
import urllib.request
import os
from typing import Optional, Dict, List
from dataclasses import dataclass


# MediaPipe Pose关键点编号
# 0-10: 头部（鼻子、眼睛、耳朵、嘴巴）
# 11-12: 肩膀
# 13-14: 手肘
# 15-16: 手腕
# 17-22: 手指根部（MCP关节，不含指尖）
# 23-24: 髋部
# 25-26: 膝盖
# 27-28: 踝关节
# 29-32: 脚趾

KEYPOINT_NAMES = {
    0: 'nose',
    1: 'left_eye_inner',
    2: 'left_eye',
    3: 'left_eye_outer',
    4: 'right_eye_inner',
    5: 'right_eye',
    6: 'right_eye_outer',
    7: 'left_ear',
    8: 'right_ear',
    9: 'mouth_left',
    10: 'mouth_right',
    11: 'left_shoulder',
    12: 'right_shoulder',
    13: 'left_elbow',
    14: 'right_elbow',
    15: 'left_wrist',
    16: 'right_wrist',
    17: 'left_pinky_mcp',
    18: 'right_pinky_mcp',
    19: 'left_index_mcp',
    20: 'right_index_mcp',
    21: 'left_thumb_mcp',
    22: 'right_thumb_mcp',
    23: 'left_hip',
    24: 'right_hip',
    25: 'left_knee',
    26: 'right_knee',
    27: 'left_ankle',
    28: 'right_ankle',
    29: 'left_heel',
    30: 'right_heel',
    31: 'left_foot_index',
    32: 'right_foot_index'
}

# 骨架连接关系
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),  # 左侧头部
    (0, 4), (4, 5), (5, 6), (6, 8),  # 右侧头部
    (9, 10),  # 嘴巴
    (11, 12),  # 肩膀连线
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),  # 左臂
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),  # 右臂
    (11, 23), (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),  # 左腿
    (12, 24), (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),  # 右腿
    (23, 24),  # 髋部连线
]


@dataclass
class Keypoint:
    """单个关键点数据"""
    x: float  # 归一化X坐标 (0-1)
    y: float  # 归一化Y坐标 (0-1)
    z: float  # 相对深度
    visibility: float  # 可见度置信度
    name: str  # 关键点名称


@dataclass
class PoseResult:
    """姿态估计结果"""
    frame_id: int
    timestamp: float
    keypoints: List[Keypoint]
    has_pose: bool
    confidence: float


class PoseEstimator:
    """
    姿态估计类
    使用MediaPipe Pose提取人体33关键点
    """

    def __init__(self, model_complexity: int = 1, use_new_api: bool = True):
        """
        初始化姿态估计器

        Args:
            model_complexity: 模型复杂度 (0=lite, 1=full, 2=heavy)
            use_new_api: 是否使用新版API (mp.tasks.vision)
        """
        self.model_complexity = model_complexity
        self.use_new_api = use_new_api
        self.detector = None
        self.pose = None
        self.model_path = None

        # 初始化
        if use_new_api:
            self._init_new_api()
        else:
            self._init_old_api()

    def _init_old_api(self):
        """
        初始化旧版API (mp.solutions.pose)
        适用于IMAGE模式
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=self.model_complexity,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            smooth_landmarks=True
        )
        print(f"[成功] 姿态估计器初始化完成 (旧版API, 复杂度={self.model_complexity})")

    def _init_new_api(self):
        """
        初始化新版API (mp.tasks.vision.PoseLandmarker)
        适用于VIDEO模式，需要时间戳
        """
        # 模型下载路径
        model_dir = "demos"
        model_filename = "pose_landmarker.task"
        self.model_path = os.path.join(model_dir, model_filename)

        # 检查模型是否存在，不存在则下载
        if not os.path.exists(self.model_path):
            print("[下载] 正在下载姿态估计模型...")
            model_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
            try:
                urllib.request.urlretrieve(model_url, self.model_path)
                print(f"[成功] 模型下载完成: {self.model_path}")
            except Exception as e:
                print(f"[警告] 模型下载失败，将使用旧版API: {e}")
                self.use_new_api = False
                self._init_old_api()
                return

        # 创建检测器
        PoseLandmarker = mp.tasks.vision.PoseLandmarker
        PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=self.model_path),
            running_mode=VisionRunningMode.VIDEO
        )

        self.detector = PoseLandmarker.create_from_options(options)
        print(f"[成功] 姿态估计器初始化完成 (新版API, VIDEO模式)")

    def detect_pose(self, frame: np.ndarray, frame_id: int, timestamp_ms: int) -> PoseResult:
        """
        检测单帧姿态

        Args:
            frame: BGR格式的视频帧
            frame_id: 帧ID
            timestamp_ms: 时间戳（毫秒）

        Returns:
            PoseResult: 姿态估计结果
        """
        if self.use_new_api and self.detector:
            return self._detect_new_api(frame, frame_id, timestamp_ms)
        elif self.pose:
            return self._detect_old_api(frame, frame_id, timestamp_ms / 1000)
        else:
            return PoseResult(
                frame_id=frame_id,
                timestamp=timestamp_ms / 1000,
                keypoints=[],
                has_pose=False,
                confidence=0.0
            )

    def _detect_new_api(self, frame: np.ndarray, frame_id: int, timestamp_ms: int) -> PoseResult:
        """
        新版API检测（VIDEO模式）
        """
        # 转换为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 创建MediaPipe图像
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # 检测姿态
        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        # 提取关键点
        keypoints = []
        has_pose = False
        confidence = 0.0

        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            has_pose = True
            landmarks = result.pose_landmarks[0]

            for idx, lm in enumerate(landmarks):
                keypoint = Keypoint(
                    x=lm.x,
                    y=lm.y,
                    z=lm.z,
                    visibility=lm.visibility if hasattr(lm, 'visibility') else 1.0,
                    name=KEYPOINT_NAMES.get(idx, f'keypoint_{idx}')
                )
                keypoints.append(keypoint)

            # 计算平均可见度作为置信度
            confidence = np.mean([kp.visibility for kp in keypoints])

        return PoseResult(
            frame_id=frame_id,
            timestamp=timestamp_ms / 1000,
            keypoints=keypoints,
            has_pose=has_pose,
            confidence=confidence
        )

    def _detect_old_api(self, frame: np.ndarray, frame_id: int, timestamp: float) -> PoseResult:
        """
        旧版API检测（IMAGE模式）
        """
        # 转换为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 检测姿态
        result = self.pose.process(rgb_frame)

        # 提取关键点
        keypoints = []
        has_pose = False
        confidence = 0.0

        if result.pose_landmarks:
            has_pose = True
            landmarks = result.pose_landmarks.landmark

            for idx, lm in enumerate(landmarks):
                keypoint = Keypoint(
                    x=lm.x,
                    y=lm.y,
                    z=lm.z,
                    visibility=lm.visibility,
                    name=KEYPOINT_NAMES.get(idx, f'keypoint_{idx}')
                )
                keypoints.append(keypoint)

            confidence = np.mean([kp.visibility for kp in keypoints])

        return PoseResult(
            frame_id=frame_id,
            timestamp=timestamp,
            keypoints=keypoints,
            has_pose=has_pose,
            confidence=confidence
        )

    def close(self):
        """
        关闭检测器，释放资源
        """
        if self.detector:
            self.detector.close()
            self.detector = None
            print("[完成] 新版API检测器已关闭")

        if self.pose:
            self.pose.close()
            self.pose = None
            print("[完成] 旧版API检测器已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False

    def __del__(self):
        """析构函数"""
        self.close()


def get_keypoint_by_name(keypoints: List[Keypoint], name: str) -> Optional[Keypoint]:
    """
    通过名称获取关键点

    Args:
        keypoints: 关键点列表
        name: 关键点名称

    Returns:
        Keypoint: 关键点对象，如果不存在返回None
    """
    for kp in keypoints:
        if kp.name == name:
            return kp
    return None


def get_keypoint_by_id(keypoints: List[Keypoint], idx: int) -> Optional[Keypoint]:
    """
    通过ID获取关键点

    Args:
        keypoints: 关键点列表
        idx: 关键点ID (0-32)

    Returns:
        Keypoint: 关键点对象，如果不存在返回None
    """
    if 0 <= idx < len(keypoints):
        return keypoints[idx]
    return None


def calculate_velocity(keypoints1: List[Keypoint], keypoints2: List[Keypoint], fps: float) -> Dict[str, float]:
    """
    计算关键点速度

    Args:
        keypoints1: 第1帧关键点
        keypoints2: 第2帧关键点
        fps: 帧率

    Returns:
        Dict: 各关键点速度字典
    """
    velocities = {}

    if len(keypoints1) != len(keypoints2):
        return velocities

    time_diff = 1.0 / fps

    for kp1, kp2 in zip(keypoints1, keypoints2):
        dx = kp2.x - kp1.x
        dy = kp2.y - kp1.y
        distance = np.sqrt(dx**2 + dy**2)
        velocity = distance / time_diff

        velocities[kp1.name] = velocity

    return velocities


def keypoints_to_dict(keypoints: List[Keypoint]) -> Dict:
    """
    将关键点列表转换为字典格式

    Args:
        keypoints: 关键点列表

    Returns:
        Dict: 关键点字典 {name: {x, y, z, visibility}}
    """
    result = {}
    for kp in keypoints:
        result[kp.name] = {
            'x': kp.x,
            'y': kp.y,
            'z': kp.z,
            'visibility': kp.visibility
        }
    return result