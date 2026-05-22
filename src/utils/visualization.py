"""
可视化工具模块
功能：骨架绘制、动作标签绘制、图像处理辅助
版本：v1.0
日期：2025-05-21
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from src.core.pose_estimator import Keypoint, POSE_CONNECTIONS


# 颜色配置
COLORS = {
    'skeleton_line': (255, 0, 0),       # 蓝色 - 骨架连接线
    'keypoint': (0, 255, 0),            # 绿色 - 关键点
    'action_reach': (255, 255, 0),      # 黄色 - Reach动作
    'action_grasp': (255, 0, 255),      # 紫色 - Grasp动作
    'action_move': (0, 255, 255),       # 青色 - Move动作
    'action_release': (128, 255, 0),    # 浅绿 - Release动作
    'action_wait': (128, 128, 128),     # 灰色 - Wait动作
    'text': (255, 255, 255),            # 白色 - 文字
    'text_background': (0, 0, 0),       # 黑色 - 文字背景
}


def draw_pose_skeleton(
    frame: np.ndarray,
    keypoints: List[Keypoint],
    connections: List[Tuple[int, int]] = POSE_CONNECTIONS,
    keypoint_radius: int = 3,
    line_thickness: int = 2,
    show_visibility: bool = False
) -> np.ndarray:
    """
    在帧上绘制姿态骨架

    Args:
        frame: BGR格式的视频帧
        keypoints: 关键点列表
        connections: 骨架连接关系列表
        keypoint_radius: 关键点圆圈半径
        line_thickness: 连接线粗细
        show_visibility: 是否显示可见度

    Returns:
        np.ndarray: 绘制了骨架的帧
    """
    if not keypoints or len(keypoints) == 0:
        return frame

    h, w = frame.shape[:2]

    # 绘制连接线
    for start_idx, end_idx in connections:
        if start_idx < len(keypoints) and end_idx < len(keypoints):
            kp1 = keypoints[start_idx]
            kp2 = keypoints[end_idx]

            # 只绘制可见度较高的连接
            if kp1.visibility > 0.5 and kp2.visibility > 0.5:
                start_point = (int(kp1.x * w), int(kp1.y * h))
                end_point = (int(kp2.x * w), int(kp2.y * h))

                cv2.line(
                    frame,
                    start_point,
                    end_point,
                    COLORS['skeleton_line'],
                    line_thickness
                )

    # 绘制关键点
    for kp in keypoints:
        if kp.visibility > 0.5:
            x = int(kp.x * w)
            y = int(kp.y * h)

            cv2.circle(
                frame,
                (x, y),
                keypoint_radius,
                COLORS['keypoint'],
                -1  # 填充
            )

            # 可选：显示可见度
            if show_visibility:
                text = f"{kp.visibility:.2f}"
                cv2.putText(
                    frame,
                    text,
                    (x + 5, y + 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.3,
                    COLORS['text'],
                    1
                )

    return frame


def draw_action_label(
    frame: np.ndarray,
    action_type: str,
    position: Tuple[int, int] = (50, 50),
    font_scale: float = 1.0,
    background: bool = True
) -> np.ndarray:
    """
    在帧上绘制动作标签

    Args:
        frame: BGR格式的视频帧
        action_type: 动作类型 (Reach/Grasp/Move/Release/Wait)
        position: 标签位置
        font_scale: 字体大小
        background: 是否绘制背景框

    Returns:
        np.ndarray: 绘制了标签的帧
    """
    # 获取颜色
    color_key = f'action_{action_type.lower()}'
    color = COLORS.get(color_key, COLORS['text'])

    # 标签文字
    text = f"动作: {action_type}"

    if background:
        # 计算文字区域大小
        (text_w, text_h), baseline = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            2
        )

        # 绘制背景框
        cv2.rectangle(
            frame,
            (position[0] - 5, position[1] - text_h - 5),
            (position[0] + text_w + 5, position[1] + 5),
            COLORS['text_background'],
            -1
        )

    # 绘制文字
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        2
    )

    return frame


def draw_frame_info(
    frame: np.ndarray,
    frame_id: int,
    timestamp: float,
    fps: float = 30.0
) -> np.ndarray:
    """
    在帧上绘制帧信息

    Args:
        frame: BGR格式的视频帧
        frame_id: 帧ID
        timestamp: 时间戳（秒）
        fps: 帧率

    Returns:
        np.ndarray: 绘制了信息的帧
    """
    # 帧信息文字
    info_text = f"帧: {frame_id} | 时间: {timestamp:.2f}s | FPS: {fps:.1f}"

    # 绘制在右上角
    h, w = frame.shape[:2]
    position = (w - 300, 30)

    # 绘制背景
    (text_w, text_h), _ = cv2.getTextSize(
        info_text,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        1
    )

    cv2.rectangle(
        frame,
        (position[0] - 5, position[1] - text_h - 5),
        (position[0] + text_w + 5, position[1] + 5),
        COLORS['text_background'],
        -1
    )

    # 绘制文字
    cv2.putText(
        frame,
        info_text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        COLORS['text'],
        1
    )

    return frame


def draw_progress_bar(
    frame: np.ndarray,
    progress: float,
    position: Tuple[int, int] = (50, 50),
    width: int = 200,
    height: int = 20
) -> np.ndarray:
    """
    在帧上绘制进度条

    Args:
        frame: BGR格式的视频帧
        progress: 进度 (0.0-1.0)
        position: 进度条位置
        width: 进度条宽度
        height: 进度条高度

    Returns:
        np.ndarray: 绘制了进度条的帧
    """
    # 绘制背景
    cv2.rectangle(
        frame,
        position,
        (position[0] + width, position[1] + height),
        (100, 100, 100),
        -1
    )

    # 绘制进度
    progress_width = int(width * progress)
    cv2.rectangle(
        frame,
        position,
        (position[0] + progress_width, position[1] + height),
        (0, 255, 0),
        -1
    )

    # 绘制边框
    cv2.rectangle(
        frame,
        position,
        (position[0] + width, position[1] + height),
        (255, 255, 255),
        2
    )

    # 绘制进度文字
    text = f"{progress * 100:.1f}%"
    cv2.putText(
        frame,
        text,
        (position[0] + width + 10, position[1] + height // 2 + 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        COLORS['text'],
        1
    )

    return frame


def resize_frame(
    frame: np.ndarray,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    keep_aspect_ratio: bool = True
) -> np.ndarray:
    """
    调整帧大小

    Args:
        frame: 输入帧
        target_width: 目标宽度
        target_height: 目标高度
        keep_aspect_ratio: 是否保持宽高比

    Returns:
        np.ndarray: 调整后的帧
    """
    h, w = frame.shape[:2]

    if target_width is None and target_height is None:
        return frame

    if keep_aspect_ratio:
        if target_width:
            ratio = target_width / w
            new_width = target_width
            new_height = int(h * ratio)
        else:
            ratio = target_height / h
            new_width = int(w * ratio)
            new_height = target_height
    else:
        new_width = target_width or w
        new_height = target_height or h

    return cv2.resize(frame, (new_width, new_height))


def convert_to_pil_image(frame: np.ndarray) -> 'Image.Image':
    """
    将OpenCV帧转换为PIL图像

    Args:
        frame: BGR格式的OpenCV帧

    Returns:
        PIL.Image: RGB格式的PIL图像
    """
    from PIL import Image

    # OpenCV使用BGR格式，转换为RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    return Image.fromarray(rgb_frame)


def create_blank_frame(width: int = 640, height: int = 480, color: Tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
    """
    创建空白帧

    Args:
        width: 宽度
        height: 高度
        color: 背景颜色 (BGR)

    Returns:
        np.ndarray: 空白帧
    """
    return np.full((height, width, 3), color, dtype=np.uint8)