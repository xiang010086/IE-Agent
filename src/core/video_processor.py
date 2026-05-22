"""
视频处理模块
功能：视频读取、帧提取、视频信息获取
版本：v1.0
日期：2025-05-21
"""
import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class VideoInfo:
    """视频信息数据结构"""
    fps: float
    frame_count: int
    duration: float
    width: int
    height: int
    codec: str


@dataclass
class FrameData:
    """帧数据结构"""
    frame_id: int
    timestamp: float
    image: np.ndarray
    rgb_image: Optional[np.ndarray] = None


class VideoProcessor:
    """
    视频处理类
    负责视频读取、帧提取、信息获取等基础操作
    """

    def __init__(self, video_path: str):
        """
        初始化视频处理器

        Args:
            video_path: 视频文件路径
        """
        self.video_path = video_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.video_info: Optional[VideoInfo] = None
        self.current_frame_id = 0

    def open(self) -> bool:
        """
        打开视频文件

        Returns:
            bool: 是否成功打开
        """
        self.cap = cv2.VideoCapture(self.video_path)

        if not self.cap.isOpened():
            print(f"[错误] 无法打开视频文件: {self.video_path}")
            return False

        # 获取视频信息
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
        codec = cv2.VideoWriter_fourcc(*'XVID').to_bytes(4).decode()

        duration = frame_count / fps if fps > 0 else 0

        self.video_info = VideoInfo(
            fps=fps,
            frame_count=frame_count,
            duration=duration,
            width=width,
            height=height,
            codec=codec
        )

        print(f"[成功] 视频已打开")
        print(f"  - 分辨率: {width} x {height}")
        print(f"  - 帧率: {fps:.1f} FPS")
        print(f"  - 总帧数: {frame_count}")
        print(f"  - 时长: {duration:.1f} 秒")

        return True

    def close(self):
        """
        关闭视频文件，释放资源
        """
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("[完成] 视频资源已释放")

    def get_video_info(self) -> Optional[VideoInfo]:
        """
        获取视频信息

        Returns:
            VideoInfo: 视频信息对象
        """
        if self.video_info is None:
            if not self.open():
                return None
        return self.video_info

    def read_frame(self) -> Optional[FrameData]:
        """
        读取下一帧

        Returns:
            FrameData: 帧数据对象，如果读取失败返回None
        """
        if self.cap is None or not self.cap.isOpened():
            print("[错误] 视频未打开")
            return None

        ret, frame = self.cap.read()

        if not ret:
            print(f"[完成] 已到达视频末尾")
            return None

        # 计算时间戳
        fps = self.video_info.fps if self.video_info else 30
        timestamp = self.current_frame_id / fps

        # 转换为RGB格式（用于MediaPipe）
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame_data = FrameData(
            frame_id=self.current_frame_id,
            timestamp=timestamp,
            image=frame,
            rgb_image=rgb_frame
        )

        self.current_frame_id += 1

        return frame_data

    def read_frames_batch(self, start_frame: int = 0, max_frames: int = 100) -> List[FrameData]:
        """
        批量读取帧

        Args:
            start_frame: 起始帧ID
            max_frames: 最大读取帧数

        Returns:
            List[FrameData]: 帧数据列表
        """
        frames = []

        if self.cap is None or not self.cap.isOpened():
            if not self.open():
                return frames

        # 跳转到起始帧
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        self.current_frame_id = start_frame

        for _ in range(max_frames):
            frame_data = self.read_frame()
            if frame_data is None:
                break
            frames.append(frame_data)

        return frames

    def extract_all_frames(self, max_frames: Optional[int] = None) -> List[FrameData]:
        """
        提取所有帧

        Args:
            max_frames: 最大帧数限制（可选）

        Returns:
            List[FrameData]: 所有帧数据列表
        """
        frames = []

        if self.cap is None or not self.cap.isOpened():
            if not self.open():
                return frames

        limit = max_frames if max_frames else self.video_info.frame_count

        while len(frames) < limit:
            frame_data = self.read_frame()
            if frame_data is None:
                break
            frames.append(frame_data)

        print(f"[完成] 共提取 {len(frames)} 帧")
        return frames

    def reset(self):
        """
        重置到视频开始位置
        """
        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_id = 0
            print("[完成] 视频已重置到开始位置")

    def __enter__(self):
        """上下文管理器入口"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False

    def __del__(self):
        """析构函数"""
        self.close()


def get_video_info_quick(video_path: str) -> Dict:
    """
    快速获取视频信息（不完整打开）

    Args:
        video_path: 视频文件路径

    Returns:
        Dict: 视频信息字典
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {}

    info = {
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
    }

    cap.release()

    return info