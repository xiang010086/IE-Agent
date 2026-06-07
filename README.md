# 工业IE智能体4.0 MVP

这是一套可运行的工业 IE 多视频产线分析 MVP。它支持项目管理、视频导入、并发分析、LBR 计算、瓶颈识别、改善报告导出，以及人工标注对照验证。

## 核心能力

- 文件系统项目管理：每个项目保存 `config.yaml`、视频、分析结果和报告。
- **可插拔视觉分析**：
  - **俯视工位（`view_type: top_down`）→ 真实识别**：MediaPipe Hands（每手21点）+ YOLO 物体检测，逐帧测出手部轨迹与动作序列，结果随画面变化。
  - **其它/未指定机位 → 时长估算回退**：只用真实视频时长，动作数等为按时长合成的占位值（界面会明确标注"非识别"）。缺依赖/模型时也会优雅回退到这一模式。
- 产线指标：LBR、瓶颈工位、等待损失、小时产能。
- **项目信息 + 节拍(Takt)/产能/人力分析**：填写班次时长/休息/需求量/有效作业率/现有人数等（`config.project_info`），系统算出客户节拍 Takt、产能是否充足、按标准工时测算的需求人数与人力缺口（`src/core/cycle_time_calculator.py`）。选填，不阻断分析；缺参数时自动跳过节拍分析。
- **改善决策（核心）**：把指标确定性地收敛成工厂可执行的三类结论——**加人 / 换人(调岗) / 拆分工序**，每条带真实数字理由（`recommend_line_actions`）。
- **AI 动态报告（数字系统算、DeepSeek 写分析）**：内置 IE 方法论知识库（`data/knowledge/ie_methodology.yaml`：MTM/动作经济/ECRS/七大浪费/产线平衡/Takt/人因/劳动定额），按分析信号自动挑相关理论注入，DeepSeek 据真实数据撰写诊断/根因/改善方案/结论并**引用理论**（数字一律由系统计算、AI 不得编造）。AI 关闭或不可用时回退规则引擎，报告仍完整。PDF 为多区块报告（封面/执行摘要/改善决策/逐工位明细+动作时间轴图/工时/节拍/诊断/建议/路线图/结论/附录/签署）。
- 准确率验证：生成人工标注模板，比较动作数、节拍、等待时间误差（以**动作数准确率**为核心判据）。
- 网页端：Streamlit 单页应用，支持中英文切换，逐工位标注识别方式。

> 诚实边界：动作分类规则为 v1，精度需在真实俯视素材上迭代；YOLO 为 COCO 通用预训练，工业零件/料盒识别需后续自定义训练。

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run app/streamlit_project_app.py
```

然后用 Chrome 打开 `http://localhost:8501`。

> Windows + Anaconda 上 torch 与 mediapipe 的 OpenMP 运行时会冲突（OMP Error #15）。代码已在入口设置 `KMP_DUPLICATE_LIB_OK=TRUE` 规避；如手动跑脚本报该错，在命令前加该环境变量即可。

## 视觉识别准备（俯视工位真实识别）

真实识别需要模型文件，先下载一次（约 20MB，存到 `data/models/`，不入库）：

```powershell
python scripts/download_models.py
```

下载：`hand_landmarker.task`、`pose_landmarker_lite.task`（诊断对比用）、`yolov8n.pt`。

### 先跑诊断，用画面证据确认机位

改造识别地基前，**先确认你的机位下 Hands / Pose 谁更可靠**：

```powershell
python scripts/diagnose_vision.py 你的测试视频.mp4
```

输出 `annotated_output.mp4`（白点=Pose、彩色21点=Hands、方框=YOLO）、`wrist_speed.png`（手速曲线），并在终端打印 Hands/Pose 可靠率与建议。俯视工位通常 Hands 稳、Pose 飘。

## 导入测试视频

```powershell
python scripts/import_video_folder.py "data/input_videos/test_videos_20260526_095117"
```

脚本会自动递归查找 MP4/AVI/MOV/MKV，创建新项目、导入视频（默认按俯视工位 `top_down` 处理）、运行分析并生成报告。

## 准确率验证

先确保项目已经跑过一次分析，然后生成标注模板：

```powershell
python scripts/create_ground_truth_template.py proj_20260526_095403
```

人工填写模板里的 `ground_truth_cycle_time`、`ground_truth_wait_time`、`ground_truth_action_count`，再运行验证：

```powershell
python scripts/validate_project_accuracy.py proj_20260526_095403 "data/projects/proj_20260526_095403/exports/ground_truth_template.csv"
```

输出 `validation_report.csv` / `validation_report.json`。

> **看哪个指标**：节拍准确率是弱证据（系统节拍≈视频时长，人工秒表也按同段时长，天然偏高）。判断"是否真识别"请看 **动作数准确率**（目标 ≥ 80%）。

## 调参说明

常用参数在项目目录的 `config.yaml`，也可以在网页里修改。

- `analysis.concurrency`：并发数（只对估算工位生效；视觉工位为稳定起见串行执行）。
- `analysis.sample_rate`：**视觉抽帧步长**，每隔 N 帧跑一次推理。越大越快越粗，越小越准越慢。
- `analysis.vision.enabled`：是否启用真实视觉识别。
- `analysis.vision.hand_model` / `yolo_model`：模型文件路径。
- `analysis.vision.min_action_frames`：动作段最小帧数，短于此并入相邻段（消碎片）。
- `target.lbr_target`：目标线平衡率，通常先用 85。
- `analysis.tuning.*`：估算回退模式下的节拍/等待/动作折算范围。
- 工位 `view_type`：`top_down` 走真实识别，其它/缺省走时长估算。

如果视频不是单个完整作业周期，优先在网页"视频与工位"里手动覆盖单周期节拍。

## 网页端部署

```powershell
streamlit run app/streamlit_project_app.py --server.port 8501
```

Docker：

```powershell
docker build -t industrial-ie-agent .
docker run -p 8501:8501 -v ${PWD}/data:/app/data industrial-ie-agent
```

更多部署说明见 [docs/web_deployment.md](docs/web_deployment.md)。

## 测试

```powershell
python tests/test_core_flow.py
```

覆盖项目创建、工位添加、并发分析、报告生成、准确率验证（估算路径）。视觉识别的烟测在依赖/模型齐全时自动运行，否则跳过。
