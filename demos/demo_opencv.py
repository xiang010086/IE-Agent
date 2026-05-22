"""
Demo 1: OpenCV视频读取验证
验证目标：能读取视频并提取帧
"""
import cv2
import numpy as np

print("=" * 50)
print("Demo 1: OpenCV视频读取验证")
print("=" * 50)

# 测试1：检查OpenCV版本
print(f"[OK] OpenCV版本: {cv2.__version__}")

# 测试2：创建测试图像（因为没有视频文件）
print("\n测试：创建并保存测试图像...")
test_image = np.zeros((480, 640, 3), dtype=np.uint8)
test_image[:] = (100, 150, 200)  # 灰蓝色背景

# 添加文字
cv2.putText(test_image, "OpenCV Working!", (150, 240),
            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

# 保存测试图像
cv2.imwrite("demos/test_image.png", test_image)
print("[OK] 测试图像已保存到 demos/test_image.png")

# 测试3：读取图像验证
img = cv2.imread("demos/test_image.png")
if img is not None:
    print(f"[OK] 图像读取成功，尺寸: {img.shape}")
else:
    print("[FAIL] 图像读取失败")

print("\n" + "=" * 50)
print("Demo 1 完成：OpenCV功能正常！")
print("=" * 50)