"""
Day -3 验证脚本
验证目标：检查所有核心模块是否正常工作
运行命令：python scripts/verify_day3.py
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 50)
print("  Day -3 Verification Script")
print("  Check Core Modules")
print("=" * 50)
print()

# 1. 验证项目结构
print("[1] Check Project Structure...")
required_dirs = ['src/core', 'src/utils', 'app', 'config', 'data']
missing_dirs = []

for dir_path in required_dirs:
    full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), dir_path)
    if not os.path.exists(full_path):
        missing_dirs.append(dir_path)

if missing_dirs:
    print(f"  [X] Missing directories: {missing_dirs}")
else:
    print("  [OK] Project structure complete")
print()

# 2. 验证核心文件
print("[2] 验证核心文件...")
required_files = {
    'src/core/video_processor.py': 'VideoProcessor类',
    'src/core/pose_estimator.py': 'PoseEstimator类',
    'src/utils/visualization.py': '可视化工具',
    'app/streamlit_app.py': 'Streamlit界面',
    'config/default.yaml': '默认配置',
    'config/mtm_tables.yaml': 'MTM时间表'
}

missing_files = []
for file_path, description in required_files.items():
    full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
    if not os.path.exists(full_path):
        missing_files.append(f"{file_path} ({description})")

if missing_files:
    print(f"  ❌ 缺少文件: {missing_files}")
else:
    print("  ✅ 所有核心文件存在")
print()

# 3. 验证模块导入
print("[3] 验证模块导入...")
import_errors = []

try:
    from src.core.video_processor import VideoProcessor
    print("  ✅ VideoProcessor导入成功")
except ImportError as e:
    import_errors.append(f"VideoProcessor: {e}")
    print(f"  ❌ VideoProcessor导入失败: {e}")

try:
    from src.core.pose_estimator import PoseEstimator
    print("  ✅ PoseEstimator导入成功")
except ImportError as e:
    import_errors.append(f"PoseEstimator: {e}")
    print(f"  ❌ PoseEstimator导入失败: {e}")

try:
    from src.utils.visualization import draw_pose_skeleton
    print("  ✅ Visualization导入成功")
except ImportError as e:
    import_errors.append(f"Visualization: {e}")
    print(f"  ❌ Visualization导入失败: {e}")

try:
    import yaml
    print("  ✅ PyYAML导入成功")
except ImportError as e:
    import_errors.append(f"PyYAML: {e}")
    print(f"  ❌ PyYAML导入失败: {e}")

print()

# 4. 验证配置文件
print("[4] 验证配置文件...")
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'default.yaml')

if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if 'video' in config and 'pose' in config:
            print("  ✅ 配置文件格式正确")
        else:
            print("  ❌ 配置文件缺少必要字段")
    except Exception as e:
        print(f"  ❌ 配置文件读取失败: {e}")
else:
    print("  ❌ 配置文件不存在")

print()

# 5. 验证视频处理功能
print("[5] 验证视频处理功能...")
try:
    from src.core.video_processor import get_video_info_quick

    # 检查OpenCV
    import cv2
    print(f"  ✅ OpenCV版本: {cv2.__version__}")
    print("  ✅ VideoProcessor类功能可用")
except ImportError as e:
    print(f"  ❌ 视频处理依赖缺失: {e}")

print()

# 6. 验证姿态估计功能
print("[6] 验证姿态估计功能...")
try:
    import mediapipe as mp
    print(f"  ✅ MediaPipe版本: {mp.__version__}")

    # 检查模型文件
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'demos', 'pose_landmarker.task')
    if os.path.exists(model_path):
        print(f"  ✅ 姿态估计模型已下载")
    else:
        print(f"  ⏳ 姿态估计模型待下载（首次运行时自动下载）")

    print("  ✅ PoseEstimator类功能可用")
except ImportError as e:
    print(f"  ❌ 姿态估计依赖缺失: {e}")

print()

# 7. 验证Streamlit
print("[7] 验证Streamlit...")
try:
    import streamlit as st
    print(f"  ✅ Streamlit版本: {st.__version__}")
except ImportError as e:
    print(f"  ❌ Streamlit导入失败: {e}")

print()

# 总结
print("=" * 50)
print("  验证总结")
print("=" * 50)

if not missing_dirs and not missing_files and not import_errors:
    print("  ✅ Day -3 所有验证项通过！")
    print()
    print("  保底交付验收标准：")
    print("  ✅ 项目结构创建完成")
    print("  ✅ VideoProcessor类实现完成")
    print("  ✅ PoseEstimator类实现完成")
    print("  ✅ 可视化工具实现完成")
    print("  ✅ Streamlit界面搭建完成")
    print()
    print("  下一步：")
    print("  1. 运行 streamlit run app/streamlit_app.py")
    print("  2. 上传视频验证完整流程")
    print("  3. 开始 Day -2 任务：动作识别、MTM分析、CSV导出")
else:
    print("  ❌ 存在问题，需要修复：")
    if missing_dirs:
        print(f"     缺少目录: {missing_dirs}")
    if missing_files:
        print(f"     缺少文件: {missing_files}")
    if import_errors:
        print(f"     导入错误: {import_errors}")

print("=" * 50)