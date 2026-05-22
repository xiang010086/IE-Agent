"""
物体检测模块
功能：使用YOLOv8检测视频中的工件、工具等物体
版本：v1.0 (扩展功能)
日期：2025-05-21

物体检测功能：
- 检测工件、工具等物体类别
- 跟踪物体位置变化
- 结合动作识别判断操作对象
- 生成物体轨迹分析
"""
import numpy as np
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import cv2

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None


@dataclass
class DetectedObject:
    """检测到的物体数据结构"""
    class_id: int           # 类别ID
    class_name: str         # 类别名称
    confidence: float       # 置信度
    bbox: Tuple[int, int, int, int]  # 边界框 (x1, y1, x2, y2)
    center: Tuple[int, int] # 中心点坐标
    frame_id: int           # 帧ID
    timestamp: float        # 时间戳


@dataclass
class ObjectTrack:
    """物体轨迹数据结构"""
    object_id: int          # 物体唯一ID
    class_name: str         # 类别名称
    positions: List[Tuple[int, int, float]]  # (x, y, timestamp)列表
    first_seen: float       # 首次出现时间
    last_seen: float        # 最后出现时间
    total_duration: float   # 总持续时间


@dataclass
class ObjectDetectionResult:
    """物体检测结果"""
    objects: List[DetectedObject]
    tracks: List[ObjectTrack]
    class_counts: Dict[str, int]  # 各类别检测数量
    frame_id: int
    timestamp: float


class ObjectDetector:
    """
    物体检测器
    使用YOLOv8检测视频中的工件、工具等物体
    """

    # 工业场景常用物体类别（COCO类别映射）
    INDUSTRIAL_CLASSES = {
        # COCO预训练模型中的相关类别
        0: 'person',      # 操作人员（可关联姿态估计）
        56: 'chair',      # 工作椅
        58: 'potted plant',  # 可视为工件容器
        59: 'bed',        # 工作台（近似）
        60: 'dining table',  # 工作桌
        61: 'toilet',     # 不相关
        62: 'tv',         # 显示设备
        63: 'laptop',     # 笔记本/控制器
        64: 'mouse',      # 鼠标/小型工具
        65: 'remote',     # 遥控器/小型工具
        66: 'keyboard',   # 键盘/输入设备
        67: 'cell phone', # 手机/通讯设备
        68: 'book',       # 文档/说明书
        69: 'clock',      # 时钟
        70: 'vase',       # 容器
        71: 'scissors',   # 剪刀/工具
        72: 'teddy bear', # 不相关
        73: 'hair drier', # 吹风机/工具
        74: 'toothbrush', # 小型工具
        # 自定义类别（需自定义训练）
        'workpiece': '工件',
        'tool': '工具',
        'box': '料箱',
        'conveyor': '传送带',
        'machine': '设备'
    }

    def __init__(
        self,
        model_name: str = 'yolov8n.pt',
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        use_tracking: bool = True
    ):
        """
        初始化物体检测器

        Args:
            model_name: YOLO模型名称（yolov8n/s/m/l/x）
            confidence_threshold: 置信度阈值
            iou_threshold: IOU阈值（NMS）
            use_tracking: 是否启用物体跟踪
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.use_tracking = use_tracking

        # 模型
        self.model = None
        self.model_loaded = False

        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_name)
                self.model_loaded = True
            except Exception as e:
                print(f"[Warning] YOLO模型加载失败: {e}")
                self.model_loaded = False

        # 跟踪数据
        self.active_tracks: Dict[int, ObjectTrack] = {}
        self.next_track_id = 0

        # 历史检测结果
        self.detection_history: List[ObjectDetectionResult] = []

    def detect_frame(
        self,
        frame: np.ndarray,
        frame_id: int,
        timestamp: float,
        classes: Optional[List[int]] = None
    ) -> ObjectDetectionResult:
        """
        检测单帧中的物体

        Args:
            frame: 图像帧
            frame_id: 帧ID
            timestamp: 时间戳
            classes: 指定检测的类别ID列表（可选）

        Returns:
            ObjectDetectionResult: 检测结果
        """
        if not self.model_loaded:
            return ObjectDetectionResult(
                objects=[],
                tracks=list(self.active_tracks.values()),
                class_counts={},
                frame_id=frame_id,
                timestamp=timestamp
            )

        # YOLO推理
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            classes=classes,
            verbose=False
        )

        detected_objects = []

        if results and len(results) > 0:
            result = results[0]

            if result.boxes is not None:
                boxes = result.boxes

                for i in range(len(boxes)):
                    # 获取边界框
                    xyxy = boxes.xyxy[i].cpu().numpy()
                    x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])

                    # 获取类别和置信度
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    conf = float(boxes.conf[i].cpu().numpy())

                    # 类别名称
                    class_name = self.INDUSTRIAL_CLASSES.get(cls_id, f'class_{cls_id}')

                    # 中心点
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2

                    detected_objects.append(DetectedObject(
                        class_id=cls_id,
                        class_name=class_name,
                        confidence=conf,
                        bbox=(x1, y1, x2, y2),
                        center=(center_x, center_y),
                        frame_id=frame_id,
                        timestamp=timestamp
                    ))

        # 更新物体跟踪
        if self.use_tracking:
            self._update_tracks(detected_objects, timestamp)

        # 类别统计
        class_counts = {}
        for obj in detected_objects:
            class_counts[obj.class_name] = class_counts.get(obj.class_name, 0) + 1

        result_obj = ObjectDetectionResult(
            objects=detected_objects,
            tracks=list(self.active_tracks.values()),
            class_counts=class_counts,
            frame_id=frame_id,
            timestamp=timestamp
        )

        self.detection_history.append(result_obj)

        return result_obj

    def _update_tracks(
        self,
        detected_objects: List[DetectedObject],
        timestamp: float
    ):
        """
        更新物体跟踪

        Args:
            detected_objects: 当前帧检测到的物体
            timestamp: 当前时间戳
        """
        # 简化跟踪：基于位置匹配
        matched_tracks = set()

        for obj in detected_objects:
            best_match_id = None
            best_distance = float('inf')

            # 查找最佳匹配的轨迹
            for track_id, track in self.active_tracks.items():
                if track.class_name != obj.class_name:
                    continue

                if track_id in matched_tracks:
                    continue

                # 计算距离
                last_pos = track.positions[-1][:2]
                distance = np.sqrt(
                    (obj.center[0] - last_pos[0])**2 +
                    (obj.center[1] - last_pos[1])**2
                )

                # 匹配阈值（像素距离）
                if distance < 100 and distance < best_distance:
                    best_match_id = track_id
                    best_distance = distance

            if best_match_id is not None:
                # 更现现有轨迹
                self.active_tracks[best_match_id].positions.append(
                    (obj.center[0], obj.center[1], timestamp)
                )
                self.active_tracks[best_match_id].last_seen = timestamp
                self.active_tracks[best_match_id].total_duration = timestamp - self.active_tracks[best_match_id].first_seen
                matched_tracks.add(best_match_id)
            else:
                # 创建新轨迹
                new_track = ObjectTrack(
                    object_id=self.next_track_id,
                    class_name=obj.class_name,
                    positions=[(obj.center[0], obj.center[1], timestamp)],
                    first_seen=timestamp,
                    last_seen=timestamp,
                    total_duration=0.0
                )
                self.active_tracks[self.next_track_id] = new_track
                self.next_track_id += 1

        # 清理过期轨迹（超过1秒未更新）
        expired_ids = []
        for track_id, track in self.active_tracks.items():
            if timestamp - track.last_seen > 1.0:
                expired_ids.append(track_id)

        for track_id in expired_ids:
            del self.active_tracks[track_id]

    def draw_detections(
        self,
        frame: np.ndarray,
        result: ObjectDetectionResult,
        draw_bbox: bool = True,
        draw_label: bool = True,
        draw_tracks: bool = False
    ) -> np.ndarray:
        """
        在帧上绘制检测结果

        Args:
            frame: 图像帧
            result: 检测结果
            draw_bbox: 是否绘制边界框
            draw_label: 是否绘制标签
            draw_tracks: 是否绘制轨迹

        Returns:
            np.ndarray: 绘制后的帧
        """
        frame_display = frame.copy()

        # 绘制检测物体
        for obj in result.objects:
            if draw_bbox:
                # 边界框颜色根据类别
                color = (0, 255, 0)  # 绿色默认
                if 'person' in obj.class_name:
                    color = (255, 0, 0)  # 红色
                elif 'workpiece' in obj.class_name or 'tool' in obj.class_name:
                    color = (0, 0, 255)  # 蓝色

                cv2.rectangle(
                    frame_display,
                    (obj.bbox[0], obj.bbox[1]),
                    (obj.bbox[2], obj.bbox[3]),
                    color, 2
                )

            if draw_label:
                label = f"{obj.class_name} {obj.confidence:.2f}"
                cv2.putText(
                    frame_display,
                    label,
                    (obj.bbox[0], obj.bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0), 2
                )

        # 绘制轨迹
        if draw_tracks:
            for track in self.active_tracks.values():
                if len(track.positions) > 1:
                    # 绘制轨迹线
                    points = [(int(p[0]), int(p[1])) for p in track.positions]
                    for i in range(1, len(points)):
                        cv2.line(
                            frame_display,
                            points[i-1],
                            points[i],
                            (255, 255, 0), 1
                        )

                    # 绘制轨迹ID
                    if points:
                        cv2.putText(
                            frame_display,
                            f"ID:{track.object_id}",
                            points[-1],
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (255, 255, 0), 1
                        )

        return frame_display

    def get_object_statistics(self) -> Dict:
        """
        获取物体检测统计

        Returns:
            Dict: 统计数据
        """
        total_detections = sum(
            len(r.objects) for r in self.detection_history
        )

        class_totals = {}
        for result in self.detection_history:
            for class_name, count in result.class_counts.items():
                class_totals[class_name] = class_totals.get(class_name, 0) + count

        total_tracks = len(self.active_tracks)
        completed_tracks = self.next_track_id - total_tracks

        return {
            'total_detections': total_detections,
            'class_totals': class_totals,
            'active_tracks': total_tracks,
            'completed_tracks': completed_tracks,
            'frames_processed': len(self.detection_history)
        }

    def analyze_object_interaction(
        self,
        pose_results: List,
        detection_results: List[ObjectDetectionResult]
    ) -> List[Dict]:
        """
        分析人体与物体的交互关系

        Args:
            pose_results: 帧态结果列表
            detection_results: 物体检测结果列表

        Returns:
            List[Dict]: 交互事件列表
        """
        interactions = []

        # 手部关键点索引
        LEFT_WRIST = 15
        RIGHT_WRIST = 16

        for i, (pose, det) in enumerate(zip(pose_results, detection_results)):
            if not pose.has_pose:
                continue

            # 获取手部位置
            left_hand = pose.keypoints[LEFT_WRIST] if LEFT_WRIST < len(pose.keypoints) else None
            right_hand = pose.keypoints[RIGHT_WRIST] if RIGHT_WRIST < len(pose.keypoints) else None

            if left_hand is None and right_hand is None:
                continue

            # 检查手部与物体的距离
            for obj in det.objects:
                if obj.class_name == 'person':
                    continue  # 排除人本身

                # 计算手部到物体的距离
                if left_hand:
                    dist_left = np.sqrt(
                        (left_hand.x - obj.center[0])**2 +
                        (left_hand.y - obj.center[1])**2
                    )
                    if dist_left < 50:  # 距离阈值
                        interactions.append({
                            'frame_id': pose.frame_id,
                            'timestamp': pose.timestamp,
                            'hand': 'left',
                            'object_class': obj.class_name,
                            'object_id': obj.bbox,
                            'distance': dist_left
                        })

                if right_hand:
                    dist_right = np.sqrt(
                        (right_hand.x - obj.center[0])**2 +
                        (right_hand.y - obj.center[1])**2
                    )
                    if dist_right < 50:
                        interactions.append({
                            'frame_id': pose.frame_id,
                            'timestamp': pose.timestamp,
                            'hand': 'right',
                            'object_class': obj.class_name,
                            'object_id': obj.bbox,
                            'distance': dist_right
                        })

        return interactions

    def reset(self):
        """
        重置检测器状态
        """
        self.active_tracks = {}
        self.next_track_id = 0
        self.detection_history = []


def analyze_video_objects(
    frames: List[np.ndarray],
    timestamps: List[float],
    model_name: str = 'yolov8n.pt',
    classes: Optional[List[int]] = None
) -> List[ObjectDetectionResult]:
    """
    便捷函数：分析视频中的物体

    Args:
        frames: 帧列表
        timestamps: 时间戳列表
        model_name: YOLO模型名称
        classes: 指定检测类别

    Returns:
        List[ObjectDetectionResult]: 检测结果列表
    """
    detector = ObjectDetector(model_name=model_name)
    results = []

    for i, (frame, timestamp) in enumerate(zip(frames, timestamps)):
        result = detector.detect_frame(frame, i, timestamp, classes)
        results.append(result)

    return results