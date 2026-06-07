# 工业IE智能体 — 前端向导式简化设计

日期：2026-05-27 · 状态：已与用户确认，待转实施计划

## 一、背景与目标

**为什么做：** 当前 Streamlit 前端把内部开发用的功能（参数调节、准确率验证、并发数、机位选择）都摆到了用户面前，术语密集（LBR/节拍/TMU/瓶颈/有效时间…），用户反馈"太复杂、看不懂在干啥"。

**企业方需求（`工业具身智能基础能力.docx` 第一条 · 深业智形）：**
- 终端用户 = 制造业 IE 部门、精益改善部门、汽车/3C/家电装配、数字工厂、工业咨询公司。
- 核心卖点 = **降低对 IE 专家的依赖**，让工厂"快速拿到节拍分析与动作优化建议"。
- 明确输出要求：**动作时间轴**、MTM 动作分类（Reach/Grasp/Move/Assemble/Wait）、标准工时报告、节拍统计、CSV/PDF。

**结论：** 用户的"看不懂"恰恰说明 UI 偏离需求。终端用户虽是 IE 人员，但产品目标是少依赖专家，所以界面要"新手也能用"，同时保留专业术语（加人话解释）。

**目标：**
1. 主界面只承载客户真正要的核心流程：上传视频 → 分析 → 看动作时间轴+节拍/工时 → 导报告。
2. 把内部/高级功能收进"⚙ 高级设置"，默认不打扰普通用户。
3. 术语保留 + 旁加人话解释（双语）。
4. 补上需求要求、当前缺失的"动作时间轴"可视化。

**非目标（本次不做）：**
- 不换技术栈（继续用 Streamlit）。
- 不改分析算法 / LBR 计算 / 报告核心 / 项目管理 / 验证计算逻辑（验证只是从主界面挪进高级，功能不删）。
- 不做动作分类精度调优（另一条线，等真实素材）。
- 不做"双模式（简易/专业）"切换（用户明确要更简单，不要更多模式）。

## 二、已锁定的设计决策

| 决策点 | 选择 |
|---|---|
| 主界面布局 | **向导式单页**（上→下 4 步，一屏到底） |
| 内部/专业功能 | **收进「⚙ 高级设置」**（折叠，默认收起），不删除 |
| 术语 | **保留术语 + 旁加人话解释**（tooltip/小字，双语） |
| 动作时间轴 | **新增**（需求要求，当前缺失） |

## 三、详细设计

### 3.1 整体结构（向导式单页）

顶部条：`工业IE智能体` · 项目选择 `[打开已有 ▾] [+新建]` · `中/EN` · `⚙ 高级设置`。
- **项目概念弱化**：首次上传并分析时，若无当前项目，**由 app 层直接调用现有 `manager.create_project(...)` 自动创建**（`project_manager.py` 本身不改）。已有项目仍可从下拉打开（保留文件系统持久化与多次分析对比能力）。

主体从上到下 4 步（`st.divider` 分段）：
```
① 上传工位视频   [拖入/选择，可多选 → 每个视频 = 一个工位]
② [ ▶ 开始分析 ]  分析中显示进度/spinner
③ 分析结果        ← 核心区（见 3.2）
④ [导出 PDF] [导出 CSV] [导出 JSON]
```

### 3.2 结果区（核心）

每个工位一张卡片：
```
┌ 工位3  ✅真实识别 ─────────────────────────────┐
│ 动作时间轴（这段视频里手在每个时刻做什么）：       │
│ 0s ▓R▓ ░░Wait░░ ▓▓G▓▓ ▓▓▓M▓▓▓ ▓A▓ … 92s      │
│  图例：■伸手 ■抓取 ■移动 ■装配 ░等待             │
├────────────────────────────────────────────┤
│ 节拍 92s    工时 1048TMU   效率 88%   动作 4 个 │
│ (完成一件)  (标准工时)     (有效占比)             │
└────────────────────────────────────────────┘
```
全线汇总条：`LBR 64.7%(各工位忙闲均衡度,越高越好) · 瓶颈 工位5(最慢、卡产能) · 产能 39 件/时`，下接"改善建议"。

- **动作时间轴**：每工位一条水平彩色时间条，按 R/G/M/A/Wait 分段着色。数据来自分析结果新增的 `action_timeline` 字段（见 3.4）。
  - 真实识别（vision_handsyolo）→ 画真实分段。
  - 估算模式（heuristic_estimate）→ 显示"估算模式：仅时长，无动作时间轴"，不伪造分段（诚实）。
  - 实现方式：**内联 HTML 色条**（`st.markdown(unsafe_allow_html=True)`，按各分段时长占比生成等比宽度的彩色 `<span>`）。不引入新依赖（不用 plotly/altair）。
- **指标卡**：术语作标题、下方一行小字人话解释（见 3.3）。
- **识别方式徽章**：沿用已实现的 ✅真实识别 / ⚠估算 / ⛔失败 + 原因。

### 3.3 术语→人话 对照（双语，UI 内常量）

在指标卡副标题、时间轴图例、表头用 `help=` 悬浮或小字呈现：

| 术语 | 人话(中) | EN hint |
|---|---|---|
| 节拍 (Cycle Time) | 完成一件产品的时间 | time to finish one piece |
| LBR (线平衡率) | 各工位忙闲是否均衡，越高越好 | how balanced station loads are; higher is better |
| TMU | 标准工时单位（1 TMU = 0.036 秒）| standard time unit (1=0.036s) |
| 瓶颈 (Bottleneck) | 最慢、限制整线产能的工位 | slowest station, caps line output |
| 有效时间 / 效率 | 真正在干活的时间占比 | share of time doing real work |
| 等待 Wait | 等待/无效时间 | idle / non-value time |
| 动作 R/G/M/A | 伸手/抓取/移动/装配 | Reach/Grasp/Move/Assemble |
| 小时产能 | 每小时能产出多少件 | pieces produced per hour |

### 3.4 后端小改：结果带上动作时间轴

`actions.classify()` 已返回 `segments`（label/start_ms/end_ms），但 `HandsYoloPipeline.analyze()` 目前只用了聚合 summary、丢弃了 segments。改动：
- `vision/base.py`：`assemble_result(...)` 增加可选参数 `action_timeline`，写入 `result["action_timeline"]`（列表：`{label, start_s, end_s}`）。
- `vision/hands_yolo.py`：把 `classify()` 返回的 segments 转成上述列表传入。
- `vision/heuristic.py`：不产生 timeline（或传空），结果里 `action_timeline` 缺省/为空，UI 据此显示"估算模式无时间轴"。
- 结果 schema 向后兼容（新增可选字段，下游报告/验证不读它，不受影响）。

### 3.5 高级设置（收纳内部功能）

放入 `⚙ 高级设置`（`st.expander` 或独立折叠区），默认收起：
- 分析调参：节拍上下限、等待占比、单动作秒数、抽帧步长 `sample_rate`、手部置信度 `min_hand_confidence`。
- 机位类型 `view_type`（逐工位）。
- 并发数。
- **准确率验证整块**（生成标注模板 / 上传 ground truth / 跑验证 / 看误差）——整体搬进高级。
- AI 改善建议提供商选择（deepseek/kimi/qwen）+ 是否调用 AI。

## 四、改动文件清单

| 文件 | 改动 |
|---|---|
| `app/streamlit_project_app.py` | 主要：4 tabs → 向导式单页 + ⚙高级折叠区；新增动作时间轴渲染、术语 tooltip、指标卡 |
| `src/core/vision/base.py` | `assemble_result` 增加 `action_timeline` 字段 |
| `src/core/vision/hands_yolo.py` | 把 segments 转为 timeline 传入结果 |
| `src/core/vision/heuristic.py` | 不产生 timeline（保持诚实） |
| `src/core/project_manager.py` | **不改**（自动建项目由 app 层调用现有 `create_project` 实现）|

## 五、保持不变

分析算法、`ProductionLineCalculator`、`line_report_generator.py`、`improvement_rules.py`、`validation.py` 计算逻辑、项目文件系统、`Dockerfile`、并发框架。验证功能只是从主界面位置挪到「高级设置」，逻辑不删不改。

## 六、验证方法

1. 启动 `streamlit run app/streamlit_project_app.py`，确认向导式单页加载（HTTP 200）。
2. 上传/选择一个高清视频 → 一键分析 → 结果区出现彩色动作时间轴 + 指标卡（含人话 tooltip）。
3. 估算模式工位 → 时间轴显示"估算模式无时间轴"，不伪造。
4. 「⚙ 高级设置」里能找到并正常使用：调参、机位、并发、准确率验证、AI 选择。
5. 导出 PDF/CSV 正常（报告逻辑未变）。
6. 回归：`python tests/test_core_flow.py`、`python tests/test_vision.py` 仍通过。
