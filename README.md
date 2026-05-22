# 工业IE智能体 - 动作分析与工时计算系统

> **版本**：v1.0 (Day -3交付完成)
> **日期**：2025-05-21
> **状态**：✅ Day -3验收通过，保底核心模块已实现

---

## 项目简介

工业IE智能体是一个基于AI的动作分析与MTM工时计算系统，旨在：

1. **提升分析效率**：自动完成视频姿态估计，减少80%人工时间
2. **标准化分析流程**：统一MTM标准，结果一致可复用
3. **支持规模化部署**：多工位、多产线并行分析能力

---

## Day -3 完成内容（2025-05-21）

### 已实现核心模块

| 模块 | 文件 | 功能 | 状态 |
|------|------|------|------|
| **视频处理** | [src/core/video_processor.py](src/core/video_processor.py) | VideoProcessor类 - 视频读取、帧提取 | ✅ 完成 |
| **姿态估计** | [src/core/pose_estimator.py](src/core/pose_estimator.py) | PoseEstimator类 - 33关键点提取 | ✅ 完成 |
| **可视化工具** | [src/utils/visualization.py](src/utils/visualization.py) | 骨架绘制、标签绘制 | ✅ 完成 |
| **界面框架** | [app/streamlit_app.py](app/streamlit_app.py) | Streamlit应用界面 | ✅ 完成 |
| **配置文件** | [config/default.yaml](config/default.yaml) | 默认参数配置 | ✅ 完成 |
| **MTM配置** | [config/mtm_tables.yaml](config/mtm_tables.yaml) | MTM时间表 | ✅ 完成 |
| **启动脚本** | [run_offline.bat](run_offline.bat) | 离线启动脚本 | ✅ 完成 |

### 验收结果

```
Day -3验收标准（全部达成）：
✅ 项目结构创建完成
✅ 视频能上传并在界面显示
✅ 姿态估计能提取关键点（33个关键点）
✅ 骨架动画能在界面显示
✅ 所有模块导入验证通过
```

---

## 快速开始

### 1. 启动应用

```bash
# 方式1：使用Streamlit命令
streamlit run app/streamlit_app.py

# 方式2：使用离线启动脚本（Windows）
run_offline.bat
```

### 2. 使用流程

1. 打开浏览器访问 `http://localhost:8501`
2. 上传产线作业视频（支持MP4/AVI/MOV/MKV格式）
3. 点击"开始分析"
4. 观看骨架动画预览

---

## 下一步开发计划

### Day -2 任务（动作识别 + CSV导出）

- ⏳ 动作识别规则引擎（R/G/M/RL四种动作）
- ⏳ MTM分析器（标准工时计算）
- ⏳ CSV导出器（动作序列表导出）

### Day -1 任务（时间轴 + 效率指标）

- ⏳ 时间轴生成器（matplotlib生成PNG图表）
- ⏳ 效率指标计算（周期时间、动作效率）

### Day 1~4 扩展功能（加分项）

- ⏳ Wait动作识别
- ⏳ PDF报告生成
- ⏳ Assemble组合动作
- ⏳ 多工位分析框架

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.13.0 | 开发语言 |
| OpenCV | 4.13.0 | 视频处理 |
| MediaPipe | 0.10.35 | 姿态估计 |
| Streamlit | 1.57.0 | Web界面 |
| NumPy | 2.1.2 | 数值计算 |
| Pandas | 2.2.3 | 数据处理 |
| Matplotlib | 3.9.2 | 图表生成 |
| PyYAML | 6.0.3 | 配置文件 |
| ReportLab | 4.5.1 | PDF生成 |

---

## 项目结构

```
工业IE智能体/
├── README.md                   # 本文档
├── requirements.txt            # 依赖清单
├── run_offline.bat             # 离线启动脚本
│
├── config/
│   ├── default.yaml            # 默认配置
│   └── mtm_tables.yaml         # MTM时间表
│
├── src/
│   ├── core/
│   │   ├── video_processor.py  # 视频处理
│   │   └── pose_estimator.py   # 姿态估计
│   └── utils/
│       └ visualization.py      # 可视化工具
│
├── app/
│   └ streamlit_app.py          # Streamlit界面
│
├── demos/
│   └ demo_integrated.py        # 整合Demo
│
└── docs/
    ├── 工业IE智能体开发方案V3.0.md
    ├── 比赛前准备计划V2.0.md
    └── 动作标注指南.md
```

---

## 文档参考

- [工业IE智能体开发方案V3.0](docs/工业IE智能体开发方案V3.0.md) - 完整技术规格
- [比赛前准备计划V2.0](docs/比赛前准备计划V2.0.md) - 交付时间线与任务分解
- [动作标注指南](docs/动作标注指南.md) - 动作识别规则说明

---

## 联系方式

工业IE智能体团队 | 2025-05-21