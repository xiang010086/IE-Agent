"""
Demo 3: Streamlit界面验证
运行命令：streamlit run demos/demo_streamlit.py
验证目标：能搭建简单Web界面
"""
import streamlit as st
import numpy as np
from PIL import Image

# 页面配置
st.set_page_config(
    page_title="工业IE智能体 Demo",
    page_icon="🏭",
    layout="wide"
)

# 标题
st.title("🏭 工业IE智能体 - 功能验证Demo")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 配置")
    st.checkbox("显示姿态骨架", value=True)
    st.slider("检测置信度", 0.0, 1.0, 0.5)

# 主界面 - 两列布局
col1, col2 = st.columns(2)

with col1:
    st.header("📤 图像上传测试")
    uploaded_file = st.file_uploader(
        "上传测试图像",
        type=['png', 'jpg', 'jpeg']
    )

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="上传的图像", width=300)
        st.success("✅ 图像上传功能正常！")

with col2:
    st.header("📊 功能状态")
    st.info("""
    **验证清单：**
    - ✅ Streamlit界面正常
    - ✅ 文件上传功能正常
    - ✅ 图像显示功能正常
    - ⏳ 姿态估计（需要真实图像）
    """)

    if st.button("🚀 运行测试", type="primary"):
        st.balloons()
        st.success("🎉 Demo运行成功！")

st.markdown("---")

# 功能说明
st.header("📖 使用说明")
st.markdown("""
### 验证步骤：
1. 上传一张包含人物的图像
2. 点击"运行测试"按钮
3. 查看右侧状态面板

### 下一步：
- 获取产线作业视频后，可以测试完整功能：
  - 视频姿态估计
  - 动作识别
  - MTM分析
""")