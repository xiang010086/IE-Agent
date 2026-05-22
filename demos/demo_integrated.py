"""
Demo 4: 整合Demo - 视频上传+姿态估计+骨架显示
运行命令：streamlit run demos/demo_integrated.py
验证目标：完整流程验证（上传视频→姿态估计→骨架动画）

使用新版MediaPipe API (0.10.35): mp.tasks.vision.PoseLandmarker
"""
import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
import tempfile
import os
import urllib.request

# 页面配置
st.set_page_config(
    page_title="工业IE智能体 - 整合Demo",
    layout="wide"
)

# 新版MediaPipe API
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# 下载模型文件
MODEL_PATH = "demos/pose_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"

@st.cache_resource
def download_model():
    """下载姿态估计模型"""
    if not os.path.exists(MODEL_PATH):
        st.info("[下载] 正在下载姿态估计模型...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            st.success("[成功] 模型下载成功！")
        except Exception as e:
            st.error(f"[失败] 模型下载失败: {e}")
            return None
    return MODEL_PATH

@st.cache_resource
def init_pose_estimator(model_path):
    """初始化姿态估计器"""
    if model_path and os.path.exists(model_path):
        options = PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO
        )
        detector = PoseLandmarker.create_from_options(options)
        return detector
    return None

# 标题
st.title("[工业IE智能体] 整合功能验证")
st.markdown("---")

# 下载模型
model_path = download_model()

# 侧边栏配置
with st.sidebar:
    st.header("[配置参数]")
    show_pose = st.checkbox("显示姿态骨架", value=True)
    max_frames = st.slider("最大处理帧数", 10, 500, 100, 10)

    st.markdown("---")
    st.header("[Demo状态]")
    if model_path and os.path.exists(model_path):
        st.info("""
        **验证清单：**
        - [OK] OpenCV视频读取
        - [OK] MediaPipe姿态估计
        - [OK] Streamlit界面
        - [OK] 模型已下载
        - [等待] 视频上传...
        """)
    else:
        st.warning("[警告] 模型未下载，请检查网络")

# 主界面 - 两列布局
col1, col2 = st.columns([1, 1])

with col1:
    st.header("[视频上传]")
    uploaded_file = st.file_uploader(
        "上传产线作业视频",
        type=['mp4', 'avi', 'mov'],
        help="支持MP4、AVI、MOV格式"
    )

    if uploaded_file:
        # 保存到临时文件
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name

        st.success(f"[成功] 视频上传成功：{uploaded_file.name}")

        # 读取视频信息
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        st.markdown(f"""
        **视频信息：**
        - 分辨率：{width} x {height}
        - 帧率：{fps:.1f} FPS
        - 总帧数：{frame_count}
        - 时长：{duration:.1f} 秒
        """)

with col2:
    st.header("[姿态估计结果]")

    if uploaded_file and model_path:
        if st.button("[开始分析]", type="primary"):
            # 初始化检测器
            detector = init_pose_estimator(model_path)

            if detector is None:
                st.error("[错误] 姿态估计器初始化失败")
            else:
                # 进度条
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 处理视频
                cap = cv2.VideoCapture(video_path)
                actual_fps = fps if fps > 0 else 30

                # 存储处理后的帧
                processed_frames = []
                keypoints_data = []
                frame_id = 0

                status_text.text("[处理] 正在处理视频...")

                while cap.isOpened() and frame_id < max_frames:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # 转换为RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # 创建MediaPipe图像
                    mp_image = mp.Image(
                        image_format=mp.ImageFormat.SRGB,
                        data=rgb_frame
                    )

                    # 姿态估计（VIDEO模式需要时间戳）
                    timestamp_ms = int(frame_id * 1000 / actual_fps)
                    result = detector.detect_for_video(mp_image, timestamp_ms)

                    # 提取关键点
                    if result.pose_landmarks and len(result.pose_landmarks) > 0:
                        landmarks = result.pose_landmarks[0]
                        keypoints = []
                        for lm in landmarks:
                            keypoints.append({
                                'x': lm.x,
                                'y': lm.y,
                                'z': lm.z,
                                'visibility': lm.visibility if hasattr(lm, 'visibility') else 1.0
                            })
                        keypoints_data.append({
                            'frame_id': frame_id,
                            'keypoints': keypoints
                        })

                        # 绘制骨架
                        if show_pose:
                            # 新版API需要手动绘制骨架
                            POSE_CONNECTIONS = [
                                (0, 1), (1, 2), (2, 3), (3, 7),  # 头部
                                (0, 4), (4, 5), (5, 6), (6, 8),  # 头部
                                (9, 10),  # 嘴
                                (11, 12),  # 肩膀
                                (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),  # 左臂
                                (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),  # 右臂
                                (11, 23), (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),  # 左腿
                                (12, 24), (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),  # 右腿
                                (23, 24), (24, 23)  # 胸部
                            ]

                            # 绘制关键点
                            h, w = frame.shape[:2]
                            for lm in landmarks:
                                x = int(lm.x * w)
                                y = int(lm.y * h)
                                cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

                            # 绘制连接线
                            for start_idx, end_idx in POSE_CONNECTIONS:
                                if start_idx < len(landmarks) and end_idx < len(landmarks):
                                    start_point = (int(landmarks[start_idx].x * w), int(landmarks[start_idx].y * h))
                                    end_point = (int(landmarks[end_idx].x * w), int(landmarks[end_idx].y * h))
                                    cv2.line(frame, start_point, end_point, (255, 0, 0), 2)

                    processed_frames.append(frame)
                    frame_id += 1

                    # 更新进度
                    progress = min(frame_id / min(frame_count, max_frames), 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"[进度] 处理：{frame_id}/{min(frame_count, max_frames)} 帧")

                cap.release()
                detector.close()

                # 显示结果
                status_text.text("[完成] 处理完成！")

                # 显示统计信息
                st.success(f"""
                [成功] 分析完成！

                **统计结果：**
                - 处理帧数：{len(processed_frames)}
                - 检测到姿态的帧数：{len(keypoints_data)}
                - 检测成功率：{len(keypoints_data)/len(processed_frames)*100:.1f}%
                - 提取关键点：每帧33个关键点
                """)

                # 显示关键点信息示例
                if keypoints_data:
                    st.subheader("关键点数据示例（第1帧）")
                    first_frame = keypoints_data[0]
                    kp_df_data = []
                    for i, kp in enumerate(first_frame['keypoints'][:10]):  # 显示前10个
                        kp_df_data.append({
                            '关键点ID': i,
                            'X': f"{kp['x']:.3f}",
                            'Y': f"{kp['y']:.3f}",
                            'Z': f"{kp['z']:.3f}",
                            '可见度': f"{kp['visibility']:.3f}"
                        })
                    st.table(kp_df_data)

                # 播放骨架动画
                st.subheader("骨架动画预览")
                if processed_frames and show_pose:
                    # 显示第一帧和中间帧作为预览
                    preview_cols = st.columns(3)
                    preview_indices = [0, len(processed_frames)//2, len(processed_frames)-1]

                    for i, idx in enumerate(preview_indices):
                        if idx < len(processed_frames):
                            frame_rgb = cv2.cvtColor(processed_frames[idx], cv2.COLOR_BGR2RGB)
                            preview_cols[i].image(frame_rgb, caption=f"帧 {idx}", use_container_width=True)

                # 导出按钮（模拟）
                st.markdown("---")
                st.subheader("数据导出")
                col_export1, col_export2 = st.columns(2)

                with col_export1:
                    if st.button("[导出] CSV关键点数据"):
                        # 这里后续会实现真正的CSV导出
                        st.info("[提示] CSV导出功能将在Day -2实现")

                with col_export2:
                    if st.button("[导出] 时间轴图表"):
                        # 这里后续会实现真正的时间轴生成
                        st.info("[提示] 时间轴生成将在Day -1实现")

    elif uploaded_file and not model_path:
        st.error("[错误] 模型未下载，无法进行分析")

st.markdown("---")

# 功能说明
st.header("[Demo说明]")
st.markdown("""
### 已验证功能：
1. [OK] **视频上传**：支持MP4/AVI/MOV格式
2. [OK] **视频读取**：OpenCV读取视频、提取帧、获取视频信息
3. [OK] **姿态估计**：MediaPipe新版API提取33个关键点
4. [OK] **骨架绘制**：手动绘制骨架连接线

### 待实现功能（保底交付）：
- [待] **动作识别**：检测R/G/M/RL动作（Day -2）
- [待] **MTM分析**：计算标准工时（Day -2）
- [待] **CSV导出**：导出动作序列表（Day -2）
- [待] **时间轴生成**：matplotlib生成PNG图表（Day -1）
- [待] **PDF报告**：ReportLab生成PDF报告（Day 1，加分项）

### 下一步：
继续开发核心模块，完成保底交付！
""")

# 清理临时文件
if uploaded_file and 'tfile' in locals():
    try:
        os.unlink(tfile.name)
    except:
        pass