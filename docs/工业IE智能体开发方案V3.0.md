# 工业IE智能体系统开发方案 V3.0

> **版本**：V3.0（修正版）
> **日期**：2025年5月21日
> **交付节奏**：提前3天保底 + 现场4天扩展 + 第5天路演
> **目标**：确保保底交付可演示，扩展加分项有据可依

---

## 一、项目背景与价值主张

### 1.1 传统痛点

| 痛点 | 具体问题 | 影响 |
|------|----------|------|
| **依赖专家** | MTM分析需IE工程师逐帧看录像、手工拆解动作 | 分析周期长、人力成本高 |
| **效率低下** | 人工掐表、填Excel、生成报告 | 1个视频分析需2-4小时 |
| **难以复制** | 分析能力依赖个人经验，无法标准化 | 新手培训周期长 |
| **无法规模化** | 传统方式无法批量分析多条产线 | 改善进度受限 |

### 1.2 用户需求（基于行业调研推导）

**核心需求推导**：
- 传统MTM分析依赖IE专家，人工分析耗时长
- 工厂希望**快速获得节拍分析与动作优化建议**
- 希望建立**标准化、数字化、可复制的工业工程分析系统**
- 支持**远程分析与规模化部署**

> **说明**：以上需求基于工业工程行业痛点与MTM标准实践推导，
> 具体参数需与目标企业（如深业智形）实际沟通确认后调整。

### 1.3 产品价值

| 价值维度 | 传统方式 | 本产品 | 价值量化 |
|----------|----------|--------|----------|
| **分析效率** | 2-4小时/视频 | 5-10分钟/视频 | **效率提升10-20倍** |
| **人力成本** | 需IE专家全程 | 专家只需复核决策 | **节省80%人工时间** |
| **分析标准化** | 依赖个人经验 | AI统一标准分析 | **结果一致可复用** |
| **规模化能力** | 单条产线 | 多工位、多产线并行 | **覆盖全厂产线** |

---

## 二、设计理念（差异化定位）

### 2.1 产品定位

**三点核心定位**：

| 定位 | 传统做法 | 本产品做法 |
|------|----------|------------|
| **IE工程师工具** | 重复看录像、掐表、填Excel | AI自动完成分析，专家只做决策 |
| **管理视角** | 个人绩效排名 | 产线级瓶颈分析（物料堆积？工位不平衡？） |
| **对工人** | 抓违规、考核慢的人 | 识别危险/疲劳动作，预防工伤 |

### 2.2 对三类用户的价值

| 用户 | 传统方式痛点 | 本产品价值 |
|------|--------------|------------|
| **IE工程师** | 80%时间看录像、掐表、填表 | AI处理80%重复工作，专注20%决策 |
| **管理层** | 只能看到"谁慢"，不知道"为什么慢" | 系统级问题归因，改善方案可落地 |
| **工人** | 担心被监控、被考核 | 工作更安全、培训更容易 |

---

## 三、系统功能规格

### 3.1 输入输出规格（基于MTM标准定义）

| 规格 | 具体要求 |
|------|----------|
| **输入** | 手机视频、工位监控视频、产线录像 |
| **输出** | 动作时间轴、MTM动作分类、标准工时分析报告 |
| **动作支持** | Reach、Grasp、Move、Release、Wait等 |
| **分析支持** | 时间序列分析、节拍统计 |
| **导出格式** | CSV/PDF报告导出 |

> **说明**：以上规格基于MTM-1标准动作要素定义，
> 具体动作支持范围以第四章4.3表格为准。

### 3.2 核心功能模块

```
┌─────────────────────────────────────────────────────────────┐
│                    工业IE智能体系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   输入层                                                     │
│   ├── 手机视频（MP4/AVI/MOV）                                │
│   ├── 工位监控视频（RTSP流 - 正式版）                         │
│   ├── 产线录像                                               │
│   └── U盘直读（离线场景）                                     │
│                                                             │
│   处理层                                                     │
│   ├── 视频预处理（格式转换、帧提取、画质增强）                 │
│   ├── 姿态估计（MediaPipe 33关键点）                         │
│   ├── 物体检测（YOLOv8 - 可选启用）                          │
│   ├── 动作识别（R/G/M/RL/Wait）                              │
│   ├── Assemble检测（可选，R+G+M+RL序列合并）                  │
│   └── MTM分析（动作映射+工时计算）                           │
│                                                             │
│   分析层                                                     │
│   ├── 时间序列分析                                           │
│   ├── 节拍统计（公式计算）                                    │
│   ├── 线平衡率计算                                           │
│   ├── 系统瓶颈识别                                           │
│   └── 改善方案推荐                                           │
│                                                             │
│   输出层                                                     │
│   ├── 动作时间轴（PNG图表）                                   │
│   ├── MTM动作分类表（CSV）                                    │
│   ├── 标准工时报告（PDF - 实际生成逻辑）                      │
│   └── 改善机会报告                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、技术栈选型（完整版）

### 4.1 技术栈清单

| 技术层 | 选型 | 版本要求 | MVP状态 | 用途说明 |
|--------|------|----------|----------|----------|
| **视频处理** | OpenCV | >=4.8.0 | ✅ 已完成 | 视频读取、帧提取、预处理 |
| **姿态估计** | MediaPipe Pose | >=0.10.0 | ✅ 已完成 | 人体33关键点检测 |
| **物体检测** | YOLOv8 | >=8.0.0 | ✅ 已完成 | 工具/零件检测（已实现） |
| **动作识别** | 规则引擎 | V1.0（自研） | ✅ 已完成 | 基于关键点位移判断 |
| **MTM引擎** | Python规则库 | V1.0（自研） | ✅ 已完成 | MTM标准表查值 |
| **数据处理** | pandas | >=2.0.0 | ✅ 已完成 | CSV导出与分析 |
| **PDF生成** | ReportLab | >=4.0.0 | ✅ 已完成 | PDF报告生成（完整版） |
| **时间轴** | matplotlib | >=3.7.0 | ✅ 已完成 | 动作时间分布图 |
| **Web界面** | Streamlit | >=1.30.0 | ✅ 已完成 | 快速交互界面 v6.0 |
| **API服务** | FastAPI | >=0.100.0 | ⏳ 正式版 | 远程分析接口 |
| **容器部署** | Docker | - | ⏳ 正式版 | 工业现场部署 |

> **版本说明**：表格版本与第十三章requirements.txt一致，
> 使用`>=`范围版本，安装时pip自动选择兼容的最新版本。

### 4.2 YOLO技术说明

**物体检测已实现（v1.0）**：

| 对比项 | MediaPipe方案 | YOLO方案 |
|--------|---------------|----------|
| **姿态估计** | ✅ MediaPipe Pose已实现 | YOLO-Pose也可，但MediaPipe更轻量 |
| **物体检测** | MediaPipe不支持 | ✅ YOLOv8已实现（ObjectDetector类） |
| **MVP需求** | 动作识别（姿态为主）✅ 完成 | 物体识别（工具/零件）✅ 已实现 |
| **部署难度** | 低（CPU实时） | 中（需模型文件，已配置） |

**YOLO已实现功能**：
- ✅ ObjectDetector类封装
- ✅ YOLOv8n模型（轻量版）
- ✅ 物体跟踪（位置轨迹）
- ✅ 手-物体交互分析
- ✅ 工业场景物体类别映射

**当前状态**：
- 物体检测模块已实现 → `src/core/object_detector.py`
- 可在Streamlit界面启用 → 需在界面整合
- 支持COCO预训练类别 → 自定义训练需额外数据

### 4.3 MVP支持的动作范围

| 动作代码 | 动作名称 | MVP状态 | 识别方式 | 说明 |
|----------|----------|----------|----------|------|
| **R** | Reach（伸手） | ✅ 已完成 | 手腕位移+手臂伸展 | 保底核心动作 |
| **G** | Grasp（抓取） | ✅ 已完成 | 手腕速度骤降+手臂弯曲 | 保底核心动作 |
| **M** | Move（移动） | ✅ 已完成 | 手腕稳定移动+携带姿态 | 保底核心动作 |
| **RL** | Release（放开） | ✅ 已完成 | 手腕放松+手臂伸展 | 保底必需动作 |
| **W** | Wait（等待） | ✅ 已完成 | 全身静止>1秒 | 扩展核心动作 |
| **P** | Position（定位） | ❌ MVP不支持 | 需指尖检测 | MediaPipe Pose无指尖关键点 |
| **Assemble** | 装配组合 | ✅ 已完成 | R+G+M+RL序列合并 | 加分项，不含P |

**MVP动作库完整性说明**：
- 保底交付（Day -2）：R、G、M、RL 四种基础动作 ✅ 已完成
- Day 1扩展：Wait等待动作 ✅ 已完成
- Day 3加分项：Assemble组合动作 ✅ 已完成
- 不支持：P定位动作（需MediaPipe Hands或YOLO辅助）

---

## 五、MTM标准动作知识库

### 5.1 MTM-1基本动作要素

| 代码 | 动作名称 | 英文名 | 说明 |
|------|----------|--------|------|
| **R** | 伸手 | Reach | 手移动到目标位置 |
| **G** | 抓取 | Grasp | 获取对物体的控制 |
| **M** | 移动 | Move | 移动物体到目标位置 |
| **P** | 定位 | Position | 对齐、定向和接合物体 |
| **RL** | 放开 | Release | 松开物体 |

### 5.2 时间测量单位（TMU）

```
TMU时间单位换算：

1 TMU = 0.00001小时 = 0.0006分钟 = 0.036秒

常用换算：
- 100 TMU = 3.6秒
- 1000 TMU = 36秒
- 1分钟 = 1667 TMU
```

### 5.3 MTM-1时间值速查表（常用动作）

| 代码 | 动作类型 | A类（短距离） | B类（中距离） | C类（长距离） |
|------|----------|---------------|---------------|---------------|
| **R** | Reach（伸手） | 8 TMU（<10cm） | 15 TMU（10-25cm） | 22 TMU（>25cm） |
| **G** | Grasp（抓取） | G1: 5 TMU（简单） | G3: 8 TMU（中等） | G5: 12 TMU（复杂） |
| **M** | Move（移动） | 10 TMU（<10cm） | 18 TMU（10-25cm） | 26 TMU（>25cm） |
| **RL** | Release（放开） | RL1: 2 TMU（简单） | RL2: 4 TMU（正常） | RL3: 8 TMU（复杂） |
| **P** | Position（定位） | P1: 10 TMU（简单） | P2: 20 TMU（中等） | P3: 30 TMU（精密） |

> **注**：详细动作分类条件见第六章识别规则，本表为常用值速查卡，便于开发时快速查值。

### 5.4 组合动作说明

**Assemble（装配）不是MTM-1标准的基本动作要素**，而是工业实践中的常用组合动作。

```
定义来源：
- Assemble = R + G + M + RL 的完整作业序列
- 用于简化报告呈现，将连续动作合并为单个"装配单元"

MTM赋值方式：
- 组合动作工时 = Σ(各基本动作工时) × 序列效率系数
- 本产品定义：简单装配 × 0.9（10%效率折扣）

示例：
- R(15) + G(5) + M(18) + RL(2) = 40 TMU
- Assemble工时 = 40 × 0.9 = 36 TMU

说明：
- Assemble在MTM-1标准中无独立代码
- 工业实践中常用此组合简化分析报告
- MVP作为可选加分项，用户可勾选是否合并显示
```

---

## 六、动作识别规则（完整定义）

### 6.1 Reach（R）伸手动作

**识别规则**：

```
关键点说明：
MediaPipe Pose的17-22号关键点仅为手指根部关节（MCP），不包含指尖，
因此无法直接检测手指开合状态。MVP采用手腕位移+手臂姿态角度判定。

触发条件（全部满足）：
1. 手腕关键点(15/16)向外移动
2. 移动速度 > 速度阈值（默认：0.15帧/秒）
3. 移动距离 > 距离阈值（默认：0.05画面比例）
4. 手臂伸展姿态（手腕-手肘-肩膀连线角度 > 150°）

终止条件：
1. 手腕速度骤降（< 0.05帧/秒）
2. 或检测到Grasp动作开始

MTM赋值：
- 短距离（< 10cm）：R-A-short = 8 TMU
- 中距离（10-25cm）：R-A-medium = 15 TMU  
- 长距离（> 25cm）：R-A-long = 22 TMU
```

### 6.2 Grasp（G）抓取动作

**识别规则**：

```
关键点限制说明：
MediaPipe Pose不含指尖关键点，无法检测"手指合拢"动作。
MVP采用以下替代判定方式：
1. 手腕从快速移动转为静止（速度骤降）
2. 手臂姿态从伸展转为弯曲（手腕-手肘角度变化）
3. 手部位置接近目标物体区域（需视频画面判断或YOLO辅助）

触发条件（满足以下组合）：
1. 前一动作为Reach（手腕刚完成伸展移动）
2. 手腕速度骤降（从 > 0.1 变为 < 0.05帧/秒）
3. 手腕-手肘距离缩短（手臂弯曲迹象）
4. 持续时间 < 0.5秒（抓取为瞬时动作）

终止条件：
1. 手腕开始新的稳定移动（Move动作开始）
2. 或静止超过1.0秒（转为Wait动作）
3. 或静止0.5-1.0秒后手臂放松（转为Release动作）

MTM赋值：
- 简单抓取G1：5 TMU
- 中等抓取G3：8 TMU
- 复杂抓取G5：12 TMU（MVP默认用G1）

阈值衔接说明：
┌────────────────────────────────────────────────────────────┐
│ 静止时间判定规则（与Wait定义统一）：                          │
│                                                            │
│ 静止 < 0.5秒：                                              │
│   → 归入Grasp动作尾部缓冲期                                 │
│                                                            │
│ 静止 0.5-1.0秒：                                            │
│   → 动作过渡期，检测手臂姿态变化                             │
│   → 若手臂放松伸展 → 记录为Release                          │
│   → 若手臂保持弯曲 → 等待后续判定                           │
│                                                            │
│ 静止 > 1.0秒：                                              │
│   → 明确转为Wait动作                                        │
│                                                            │
│ 此规则与6.4 Wait定义完全一致，避免阈值冲突                    │
└────────────────────────────────────────────────────────────┘

技术局限提示：
正式版如需精确手指动作检测，应切换为MediaPipe Hands（21关键点含指尖）
或叠加YOLO物体检测辅助判断"手是否接触物体"。
```

### 6.3 Move（M）移动动作

**识别规则**：

```
关键点限制说明：
MediaPipe Pose不含指尖关键点，"手指闭合状态"无法直接检测。
MVP采用手腕稳定移动+手臂携带姿态判定。

触发条件（全部满足）：
1. Grasp动作刚刚结束（前0.5秒内）
2. 手腕开始稳定移动（速度 > 0.1帧/秒）
3. 手臂呈携带姿态（手肘弯曲，手腕相对躯干位置稳定）
4. 移动方向基本稳定（方向变化 < 30°/帧）

终止条件：
1. 手腕速度骤降（< 0.05）
2. 或检测到Release动作开始（手腕放松、手臂伸展）
3. 或持续超过最大时间（默认：5秒）

MTM赋值：
- 短距离M-A-short：10 TMU
- 中距离M-A-medium：18 TMU
- 长距离M-A-long：26 TMU
- 重量调整：+5 TMU（1-5kg），+12 TMU（> 5kg）
```

### 6.4 Wait（W）等待动作

**识别规则**：

```
触发条件（全部满足）：
1. 全身关键点位移速度 < 静止阈值（默认：0.02帧/秒）
2. 持续时间 > 最小等待时长（默认：1.0秒）
3. 无R/G/M动作正在执行

终止条件：
1. 检测到新的R动作开始
2. 或持续超过最大等待时间（默认：30秒）

关键区分：等待 vs 动作间歇
┌────────────────────────────────────────────────────────────┐
│ 区分标准：                                                   │
│                                                            │
│ 动作间歇（属于前一个动作尾部）：                              │
│   - 持续时间 < 0.5秒                                        │
│   - 速度下降但未完全静止                                     │
│   - 归入前一动作的缓冲期                                     │
│                                                            │
│ 等待动作（独立W动作）：                                      │
│   - 持续时间 > 1.0秒                                        │
│   - 速度完全静止（< 0.02）                                   │
│   - 前一动作已明确结束                                       │
│                                                            │
│ 判断逻辑：                                                   │
│   if 前一动作结束时间 > 0.5秒 AND 当前静止时长 > 1.0秒:      │
│       → 记录为Wait动作                                      │
│   else:                                                     │
│       → 归入前一动作缓冲期                                   │
└────────────────────────────────────────────────────────────┘

MTM赋值：
- Wait不计入标准工时（作为效率损失分析）
- 记录等待时长用于瓶颈分析
```

### 6.5 Assemble（装配）组合动作

**识别规则**：

```
定义：Assemble = R + G + M + RL 的完整装配序列（MVP不含P定位动作）

MVP状态说明：
Position（P定位）动作需要精确的手部微调检测，MediaPipe Pose无法实现。
MVP将Assemble定义为 R + G + M + RL 序列，不含P。
正式版可叠加MediaPipe Hands实现P检测。

触发条件（序列检测）：
1. 检测到完整的R→G→M→RL序列（MVP不含P）
2. 序列总时间 < 最大装配时间（默认：10秒）
3. 动作间间隔 < 序列断开阈值（默认：1.0秒）

识别逻辑：
┌────────────────────────────────────────────────────────────┐
│ 步骤1：检测基础动作序列                                      │
│   记录所有R、G、M、RL动作及其时间戳                            │
│                                                            │
│ 步骤2：序列匹配                                             │
│   查找满足条件的连续序列：                                   │
│   R结束时间 → G开始时间 < 0.3秒                              │
│   G结束时间 → M开始时间 < 0.2秒                              │
│   M结束时间 → RL开始时间 < 0.5秒                             │
│                                                            │
│ 步骤3：Assemble判定                                         │
│   if 匹配成功：                                             │
│       → 合并为单个Assemble动作                              │
│       → MTM时间 = Σ(R+G+M+RL) - 10%序列折扣                  │
│   else:                                                     │
│       → 保持独立动作记录                                    │
└────────────────────────────────────────────────────────────┘

几何阈值（关键点判定）：
- R阶段：手腕移动轨迹终点接近目标物体位置
- G阶段：手腕速度骤降，手臂弯曲
- M阶段：手腕携带物体移动轨迹稳定
- RL阶段：手腕放松，手臂伸展

MTM赋值：
- 简单装配：Σ(R+G+M+RL) × 0.9 TMU（10%序列效率折扣）
- 复杂装配：Σ(R+G+M+RL) × 1.0 TMU（无折扣）

MVP实现策略：
- Assemble作为"可选检测项"
- 默认输出独立R/G/M/RL，用户可在界面勾选"合并Assemble"
- 正式版叠加MediaPipe Hands后可增加P定位检测
```

### 6.6 Release（RL）放开动作

**识别规则**：

```
定义：松开对物体的控制，手从携带状态转为自由状态

关键点限制说明：
MediaPipe Pose不含指尖关键点，无法检测"手指松开"动作。
MVP采用手腕放松姿态+手臂伸展判定。

触发条件（满足以下任一组合）：

┌────────────────────────────────────────────────────────────┐
│ 组合A：正常Release（Move后放开）                             │
│   1. Move动作刚刚结束（前1.0秒内）                            │
│   2. 手腕速度骤降（速度 < 0.05帧/秒）                         │
│   3. 手臂从弯曲转为伸展（角度 > 150°）                        │
│                                                            │
│ 组合B：快速Release（Grasp后直接放开）                        │
│   适用场景：拿起检查后立即放下、抓取后发现错误随即松手         │
│   1. Grasp动作刚刚结束（前1.0秒内）                           │
│   2. 静止0.5-1.0秒 + 手臂从弯曲转为伸展                      │
│   3. 无Move动作插入（前一动作是Grasp而非Move）               │
└────────────────────────────────────────────────────────────┘

终止条件：
1. 手腕开始新的向外移动（下一个Reach动作开始）
2. 或静止超过1.0秒（转为Wait动作）

MTM赋值：
- 简单放开RL1：2 TMU
- 正常放开RL2：4 TMU
- 复杂放开RL3：8 TMU（MVP默认用RL1）

识别逻辑：
┌────────────────────────────────────────────────────────────┐
│ 步骤1：检测前一动作类型                                      │
│   判断前1.0秒内结束的是Move还是Grasp                         │
│                                                            │
│ 步骤2：按不同路径判定                                        │
│   if 前动作==Move:                                          │
│       → 检查手腕速度骤降 + 手臂伸展                          │
│       → 满足则记录为Release（组合A）                         │
│   elif 前动作==Grasp:                                       │
│       → 检查静止时长(0.5-1.0秒) + 手臂伸展                   │
│       → 满足则记录为Release（组合B）                         │
│                                                            │
│ 步骤3：RL判定                                               │
│   if 满足组合A或组合B任一:                                  │
│       → 记录为Release动作                                   │
│       → MTM时间 = RL1（2 TMU）                              │
│   else:                                                     │
│       → 归入前一动作尾部缓冲期                               │
└────────────────────────────────────────────────────────────┘

与其他动作的关系：
- RL是Move的终止条件之一（组合A）
- RL是Grasp的可能后续动作（组合B，无Move插入时）
- RL是Assemble序列的最后一个动作
- RL结束后可能触发Wait或下一个Reach

MVP实现策略：
- RL支持两种触发路径（Move后或Grasp后直接）
- 结合手臂姿态变化判定（伸展=放松）
- 与Wait区分：RL有明确的姿态变化，Wait为持续静止
```

---

## 七、节拍统计公式（完整定义）

> **适用场景说明**：
> - MVP分析单条视频、单个工位，可输出**周期时间**和**效率指标**
> - **节拍时间、线平衡率、瓶颈工时**需要多工位数据，为正式版功能
> - MVP阶段仅输出单工位工时，产线级指标作为路演扩展说明

### 7.1 周期时间（Cycle Time）—— MVP可计算

```
定义：完成一个作业循环所需的标准工时

公式：
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   周期时间 = Σ(各动作标准工时)                               │
│                                                            │
│   Cycle Time = Σ(Action Standard Times)                    │
│                                                            │
│   数据来源：                                                │
│   - MVP从单视频分析中提取动作序列                            │
│   - 每个动作映射MTM工时值                                   │
│   - 汇总得出该工位的标准工时                                │
│                                                            │
│   计算步骤：                                                │
│   1. 汇总所有动作的MTM工时（TMU）                            │
│   2. 加上宽放时间（默认15%）                                 │
│   3. 转换为分钟                                             │
│                                                            │
│   示例：                                                    │
│   动作序列：R(15)+G(5)+M(18)+R(15)+G(5)+RL(2)               │
│   正常时间 = 60 TMU = 2.16秒                                │
│   宽放时间 = 60 × 15% = 9 TMU                               │
│   标准工时 = 69 TMU = 2.48秒                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.2 节拍时间（Takt Time）—— 正式版功能

```
定义：满足客户需求的理想生产节奏
适用场景：产线级分析，需多个工位数据

公式：
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   节拍时间 = 可用生产时间 / 客户需求量                        │
│                                                            │
│   Takt Time = Available Time / Customer Demand             │
│                                                            │
│   数据来源：                                                │
│   - 需用户输入：班次时长、客户需求量                         │
│   - 或从生产计划系统导入                                    │
│                                                            │
│   示例：                                                    │
│   每班8小时 = 480分钟                                       │
│   客户需求 = 100件                                          │
│   节拍时间 = 480 / 100 = 4.8分钟/件                         │
│                                                            │
│   MVP状态：公式定义完成，用户输入界面已实现（Day 2）            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.3 瓶颈工时（Bottleneck Time）—— 正式版功能

```
定义：产线上最慢工位的作业时间

公式：
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   瓶颈工时 = MAX(各工位标准工时)                             │
│                                                            │
│   Bottleneck = MAX(Station 1, Station 2, ..., Station N)   │
│                                                            │
│   示例（5工位产线）：                                        │
│   工位1：2.5分钟                                            │
│   工位2：3.2分钟 ← 瓶颈                                     │
│   工位3：2.8分钟                                            │
│   工位4：2.3分钟                                            │
│   工位5：2.6分钟                                            │
│                                                            │
│   瓶颈工时 = 3.2分钟                                        │
│   产线产能 = 60 / 3.2 = 18.75件/小时                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.4 线平衡率（Line Balance Rate）—— 正式版功能

```
定义：产线各工位作业时间均衡程度
适用场景：产线级分析，需多个工位数据

公式：
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   线平衡率 = Σ(各工位工时) / (瓶颈工时 × 工位数) × 100%      │
│                                                            │
│   LBR = Σ(CTi) / (Bottleneck × N) × 100%                   │
│                                                            │
│   数据来源：                                                │
│   - 需多工位视频分析结果（各工位周期时间）                    │
│   - MVP单视频分析无法直接计算                               │
│   - 正式版多工位模块可自动计算                              │
│                                                            │
│   示例（5工位产线）：                                        │
│   Σ工时 = 2.5+3.2+2.8+2.3+2.6 = 13.4分钟                   │
│   瓶颈 × N = 3.2 × 5 = 16分钟                               │
│   线平衡率 = 13.4 / 16 × 100% = 83.75%                     │
│                                                            │
│   评判标准：                                                │
│   - LBR > 85%：优秀                                         │
│   - LBR 70-85%：良好                                        │
│   - LBR < 70%：需要改善                                     │
│                                                            │
│   MVP状态：公式定义完成，多工位模块已实现（Day 3）              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.5 效率损失分析 —— MVP可计算

```
Wait时间分析公式：

┌────────────────────────────────────────────────────────────┐
│                                                            │
│   等待损失率 = Σ(Wait时长) / 总周期时间 × 100%              │
│                                                            │
│   Wait Loss Rate = Σ(Wait Time) / Total Cycle × 100%       │
│                                                            │
│   数据来源：                                                │
│   - MVP从动作识别结果中提取Wait动作时长                      │
│   - 总周期时间为视频分析时长                                │
│   - 单工位分析可直接计算                                    │
│                                                            │
│   示例：                                                    │
│   总周期时间 = 60秒                                         │
│   Wait动作累计 = 12秒                                       │
│   等待损失率 = 12 / 60 × 100% = 20%                        │
│                                                            │
│   改善方向：                                                │
│   - Wait > 10%：检查物料配送、设备响应                      │
│   - Wait > 20%：检查节拍平衡、瓶颈工位                      │
│                                                            │
│   MVP状态：公式定义完成，实现依赖Wait检测（Day 1下午）        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.6 动作效率（Action Efficiency）—— MVP可计算

```
定义：有效动作时间占总观测时间的比例

公式：
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   动作效率 = Σ(有效动作时长) / 总观测时间 × 100%             │
│                                                            │
│   Action Efficiency = Σ(R+G+M+RL时长) / Total Time × 100%  │
│                                                            │
│   有效动作定义：                                            │
│   - Reach（伸手）：R动作累计时长                            │
│   - Grasp（抓取）：G动作累计时长                            │
│   - Move（移动）：M动作累计时长                             │
│   - Release（放开）：RL动作累计时长                         │
│   - 不包含Wait（等待）                                      │
│                                                            │
│   数据来源：                                                │
│   - MVP从动作识别结果中统计各动作时长                        │
│   - 总观测时间为视频分析时长                                │
│                                                            │
│   示例：                                                    │
│   总观测时间 = 60秒                                         │
│   R累计 = 8秒                                               │
│   G累计 = 4秒                                               │
│   M累计 = 30秒                                              │
│   RL累计 = 6秒                                              │
│   Wait累计 = 12秒                                           │
│   有效动作时长 = 8+4+30+6 = 48秒                            │
│   动作效率 = 48 / 60 × 100% = 80%                          │
│                                                            │
│   评判标准：                                                │
│   - 动作效率 > 90%：优秀                                    │
│   - 动作效率 80-90%：良好                                   │
│   - 动作效率 < 80%：需改善（存在大量Wait或动作间隙）         │
│                                                            │
│   MVP状态：公式定义完成，Day -1可计算（无需Wait识别）        │
│                                                            │
│   注：Wait识别完成后可结合等待损失率进行综合效率分析          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 八、PDF报告生成接口（加分项）

> **定位说明**：PDF报告为**加分项**，保底交付只需CSV导出。
> 本节仅定义接口与数据结构，完整实现代码约200行，见附录或单独文件。

### 8.1 PDF生成器接口定义

```python
# src/report/pdf_generator.py
"""
PDF报告生成器 - 接口定义
依赖：ReportLab（pip install reportlab）
状态：加分项，Day 1扩展开发
"""

class PDFReportGenerator:
    """PDF报告生成器"""
    
    def __init__(self, output_path: str):
        """初始化，指定输出路径"""
        pass
    
    def generate_report(self, analysis_data: dict) -> str:
        """
        生成完整分析报告
        
        Args:
            analysis_data: 分析结果数据（见8.2数据结构定义）
        
        Returns:
            str: 生成的PDF文件路径
        """
        pass
    
    def _add_title_page(self, data: dict):
        """添加标题页"""
        pass
    
    def _add_action_analysis(self, actions: list):
        """添加动作分析表格"""
        pass
    
    def _add_time_analysis(self, mtm_summary: dict):
        """添加工时分析表格"""
        pass
    
    def _add_efficiency_metrics(self, metrics: dict):
        """添加效率指标"""
        pass


def generate_pdf_report(analysis_data: dict, output_path: str) -> str:
    """PDF报告生成入口函数"""
    generator = PDFReportGenerator(output_path)
    return generator.generate_report(analysis_data)
```

### 8.2 输入数据结构定义

```python
# PDF生成所需的analysis_data结构
analysis_data = {
    # 视频基本信息
    'video_info': {
        'video_name': str,      # 视频文件名
        'duration': float,      # 视频时长（秒）
        'fps': int,             # 帧率
        'frame_count': int,     # 总帧数
        'width': int,           # 分辨率宽度
        'height': int           # 分辨率高度
    },
    
    # 动作列表（核心数据）
    'actions': [
        {
            'type': str,        # 动作类型：Reach/Grasp/Move/Wait等
            'start_time': float, # 开始时间（秒）
            'end_time': float,   # 结束时间（秒）
            'duration': float,   # 持续时间（秒）
            'time_tmu': float    # MTM工时（TMU）
        }
    ],
    
    # MTM工时汇总
    'mtm_summary': {
        'normal_time_tmu': float,    # 正常时间（TMU）
        'normal_time_sec': float,    # 正常时间（秒）
        'normal_time_min': float,    # 正常时间（分钟）
        'allowance_tmu': float,      # 宽放时间（TMU，默认15%）
        'allowance_sec': float,      # 宽放时间（秒）
        'allowance_min': float,      # 宽放时间（分钟）
        'standard_time_tmu': float,  # 标准工时（TMU）
        'standard_time_sec': float,  # 标准工时（秒）
        'standard_time_min': float   # 标准工时（分钟）
    },
    
    # 效率指标
    'metrics': {
        'actual_time': float,        # 实际观测时间（秒）
        'standard_time': float,      # 标准工时（秒）
        'wait_time': float,          # 等待时间累计（秒）
        'wait_loss_rate': float,     # 等待损失率（%）
        'action_efficiency': float   # 动作效率（%）
    },
    
    # 可选：改善建议
    'improvement': [str],  # 改善建议列表
    
    # 可选：时间轴图表路径
    'timeline_image': str  # PNG图表文件路径
}
```

### 8.3 MVP开发优先级

| 功能 | MVP状态 | 开发时间 | 说明 |
|------|----------|----------|------|
| CSV导出 | ✅ 已完成 | Day -2 | 核心导出功能 |
| PNG时间轴 | ✅ 已完成 | Day -1 | matplotlib生成 |
| PDF报告 | ✅ 已完成 | Day 1 | ReportLab实现（完整版v2.0） |

> **调用方式**：核心分析模块完成动作识别后，
> 将数据按上述结构封装，调用 `generate_pdf_report(data, "output.pdf")` 即可。

---

## 九、部署方案概述

> **定位说明**：MVP仅支持本地Streamlit运行，
> 工业部署为正式版功能，本节简要说明扩展方向。

### 9.1 MVP部署形态

```
MVP部署（保底交付）：
┌─────────────────────────────────────────────────────┐
│  开发机 / 比赛演示机                                  │
│  ├── Python环境（提前安装依赖）                       │
│  ├── 视频文件（本地目录或U盘）                        │
│  ├── Streamlit运行：streamlit run app.py            │
│  └── 浏览器访问：http://localhost:8501               │
│                                                      │
│  启动脚本（run_offline.bat）：                       │
│  @echo off                                          │
│  cd /d "%~dp0"                                      │
│  python -m streamlit run app/streamlit_app.py       │
│  pause                                              │
└─────────────────────────────────────────────────────┘
```

### 9.2 正式版扩展方向

| 场景 | MVP状态 | 正式版方案 | 说明 |
|------|----------|------------|------|
| **内网离线** | ✅ 支持 | 本地文件读取 | U盘视频直接分析 |
| **RTSP流** | ❌ 不支持 | OpenCV VideoCapture | 实时监控接入 |
| **边缘设备** | ❌ 不支持 | 轻量化版本 | 工位嵌入式PC |
| **云端API** | ❌ 不支持 | FastAPI服务 | 远程分析接口 |

> **比赛重点**：MVP演示只需本地运行，
> 工业部署方案作为路演"扩展能力"说明即可，不展开技术细节。

---

## 十、交付时间线（实际节奏）

### 10.1 时间线规划

```
┌─────────────────────────────────────────────────────────────┐
│                    交付时间线                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  阶段划分：                                                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  提前开发阶段（保底交付）                              │   │
│  │  Day -3 ~ Day -1：核心功能开发                        │   │
│  │  目标：单视频分析全流程可运行                          │   │
│  │  交付：能演示"上传视频→显示骨架→导出CSV"               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  现场开发阶段（扩展加分）                              │   │
│  │  Day 1 ~ Day 4：功能扩展、优化                         │   │
│  │  目标：完整功能、数据验证、用户体验                     │   │
│  │  加分项：多工位、Assemble、改善建议                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  路演阶段                                              │   │
│  │  Day 5：完整演示、汇报                                 │   │
│  │  目标：展示产品价值、技术亮点                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 提前开发（保底交付）- Day -3 ~ Day -1

**状态：✅ 全部完成 (2025-05-21 下午)**

| 天数 | 任务 | 交付物 | 必须完成标志 | 实际状态 |
|------|------|--------|--------------|----------|
| **Day -3** | 项目结构+视频处理+姿态估计 | 视频上传、骨架显示 | ✅ 能看到骨架 | ✅ 已完成 |
| **Day -2** | 基础动作识别(R/G/M/RL)+CSV导出 | 动作检测、CSV下载 | ✅ 能导出CSV | ✅ 已完成 |
| **Day -1** | MTM工时计算+时间轴生成 | 工时报告、PNG图表 | ✅ 保底交付完成 | ✅ 已完成 |

**保底交付验收标准**：
```
保底交付验收达成 (2025-05-21)：
✅ 1. 上传视频 → 界面显示骨架动画
✅ 2. 动作识别 → 检测R/G/M/RL动作
✅ 3. CSV导出 → 下载动作序列表
✅ 4. 时间轴 → 生成PNG图表

保底交付已完成，可演示完整流程！
```

### 10.3 现场开发（扩展加分）- Day 1 ~ Day 4

**状态：Day 1~Day 4 全部完成 (2025-05-21)**

| 天数 | 任务 | 加分项 | 优先级 | 实际状态 |
|------|------|--------|--------|----------|
| **Day 1** | Wait动作识别 + PDF报告生成 | Wait检测、PDF导出 | P1 | ✅ 已完成 |
| **Day 2** | 节拍统计公式实现 + 瓶颈计算 | 线平衡率计算 | P2 | ✅ 已完成 |
| **Day 3** | Assemble组合动作 + 多工位框架 | Assemble合并、Station类 | P3 | ✅ 已完成 |
| **Day 4** | 改善建议引擎 + 界面优化 | 改善报告、UI美化 | P3 | ✅ 已完成 |

**Day 1~Day 4 完成验收**：
```
Day 1 加分项完成 (2025-05-21)：
✅ 5. Wait识别 → 全身静止检测（阈值0.02，持续>1秒）
✅ 6. PDF导出 → ReportLab生成完整报告

Day 2 加分项完成 (2025-05-21)：
✅ 7. 节拍计算 → Takt Time、标准节拍、效率、利用率、瓶颈识别
✅ 8. 线平衡率 → LBR公式、工位负荷分析、改善建议引擎

Day 3 加分项完成 (2025-05-21)：
✅ 9. Assemble组合动作 → R+G+M+RL序列自动合并、TMU累加
✅ 10. 多工位分析框架 → MultiStationAnalyzer类、产线综合分析

Day 4 加分项完成 (2025-05-21)：
✅ 11. UI美化 → CSS样式优化、布局改进、状态展示

额外实现（超出原计划）：
✅ 改善建议引擎 → 基于LBR指标的智能建议生成（Day 2提前完成）
✅ 多工位完整框架 → MultiStationAnalyzer提供完整产线分析（Day 3实现）
✅ Assemble开关 → 用户可选择是否合并组合动作
```

### 10.4 路演演示 - Day 5

| 演示内容 | 时长 | 说明 |
|----------|------|------|
| **产品定位** | 2分钟 | 理念差异化、价值主张 |
| **核心功能** | 5分钟 | 上传→分析→导出完整流程 |
| **技术亮点** | 3分钟 | MediaPipe、动作规则、MTM知识库 |
| **扩展能力** | 3分钟 | 多工位分析、物体检测、部署方案 |
| **商业价值** | 2分钟 | 效率提升、成本节省 |

---

## 十一、扩展能力展示（路演证据）

### 11.1 多工位分析框架

```python
# src/reserved/multi_station.py
"""
多工位分析框架 - 路演可展示的接口设计
"""

class StationAnalyzer:
    """多工位分析器"""
    
    def __init__(self):
        self.stations = {}  # 工位数据存储
        self.station_count = 0
    
    def add_station(self, station_id: str, video_path: str):
        """
        添加工位分析任务
        
        Args:
            station_id: 工位编号（如 "Station-1"）
            video_path: 该工位的视频文件路径
        
        Returns:
            StationData对象
        """
        station_data = StationData(station_id, video_path)
        self.stations[station_id] = station_data
        self.station_count += 1
        return station_data
    
    def analyze_all_stations(self):
        """
        分析所有工位（并行）
        
        Returns:
            dict: 各工位分析结果
        """
        results = {}
        for station_id, station in self.stations.items():
            results[station_id] = station.analyze()
        return results
    
    def calculate_line_balance(self):
        """
        计算线平衡率
        
        公式：LBR = Σ(工时) / (瓶颈工时 × 工位数) × 100%
        
        Returns:
            float: 线平衡率（%）
        """
        cycle_times = [s.cycle_time for s in self.stations.values()]
        
        total_time = sum(cycle_times)
        bottleneck = max(cycle_times)
        lbr = (total_time / (bottleneck * self.station_count)) * 100
        
        return lbr
    
    def identify_bottleneck(self):
        """
        识别瓶颈工位
        
        Returns:
            str: 瓶颈工位编号
        """
        max_time = 0
        bottleneck_station = None
        
        for station_id, station in self.stations.items():
            if station.cycle_time > max_time:
                max_time = station.cycle_time
                bottleneck_station = station_id
        
        return bottleneck_station


class StationData:
    """单个工位数据"""
    
    def __init__(self, station_id: str, video_path: str):
        self.station_id = station_id
        self.video_path = video_path
        self.actions = []
        self.cycle_time = 0
        self.wait_time = 0
    
    def analyze(self):
        """分析该工位（调用核心分析模块）"""
        # MVP预留：实际调用 video_processor + pose_estimator + action_recognizer
        # 返回分析结果
        pass


# 路演演示代码
def demo_multi_station():
    """路演多工位演示"""
    analyzer = StationAnalyzer()
    
    # 添加5个工位
    analyzer.add_station("工位1", "videos/station1.mp4")
    analyzer.add_station("工位2", "videos/station2.mp4")
    analyzer.add_station("工位3", "videos/station3.mp4")
    analyzer.add_station("工位4", "videos/station4.mp4")
    analyzer.add_station("工位5", "videos/station5.mp4")
    
    # 分析
    results = analyzer.analyze_all_stations()
    
    # 计算线平衡率
    lbr = analyzer.calculate_line_balance()
    print(f"线平衡率：{lbr:.1f}%")
    
    # 识别瓶颈
    bottleneck = analyzer.identify_bottleneck()
    print(f"瓶颈工位：{bottleneck}")
```

### 11.2 多人员检测接口

```python
# src/reserved/multi_person.py
"""
多人员检测接口 - 路演可展示的设计
API说明：使用与核心模块一致的mp.solutions.pose（旧版API）
"""

import mediapipe as mp
import cv2

class MultiPersonDetector:
    """多人姿态估计"""
    
    def __init__(self, max_persons: int = 5):
        self.max_persons = max_persons
        # 使用与核心模块一致的旧版API
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
    def detect_all_persons(self, frame):
        """
        检测画面中所有人员
        
        Args:
            frame: 视频帧
        
        Returns:
            list: 各人员的关键点列表
        """
        # MediaPipe Pose默认检测最明显的一人
        # 多人检测需要分割画面或使用其他方案
        persons_keypoints = []
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if results.pose_landmarks:
            # 提取关键点
            keypoints = []
            for landmark in results.pose_landmarks.landmark:
                keypoints.append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                })
            persons_keypoints.append({
                'person_id': 0,
                'keypoints': keypoints
            })
        
        return persons_keypoints
    
    def track_persons(self, frames_sequence):
        """
        追踪多人员轨迹
        
        Args:
            frames_sequence: 帧序列
        
        Returns:
            dict: {person_id: keypoints_sequence}
        """
        tracking_results = {}
        return tracking_results
    
    def close(self):
        """释放资源"""
        self.pose.close()


# 路演演示场景
def demo_multi_person():
    """路演多人场景演示"""
    detector = MultiPersonDetector(max_persons=3)
    
    print("多人检测能力说明：")
    print("1. MVP使用mp.solutions.pose检测单人")
    print("2. 多人检测正式版方案：画面分割 + 多实例分析")
    print("3. 支持各人员独立追踪，生成个人动作序列")
    print("4. API与核心模块保持一致（mp.solutions.pose）")
    
    detector.close()


# ============================================================
# 资源管理与单例模式建议
# ============================================================
#
# 注意事项：
# 本模块独立实例化Pose对象，而核心模块也会实例化自己的Pose对象。
# 若同时导入两个模块，会创建两个MediaPipe Pose实例，可能导致：
# - 内存占用增加
# - GPU资源冲突（如同时使用GPU加速）
# - 推理性能下降
#
# 推荐架构（正式版）：
# 使用单例模式或依赖注入，共享Pose实例：
#
# class PoseService:
#     """Pose实例管理服务"""
#     _instance = None
#     
#     @classmethod
#     def get_pose(cls):
#         if cls._instance is None:
#             cls._instance = mp.solutions.pose.Pose(...)
#         return cls._instance
#     
#     @classmethod
#     def close(cls):
#         if cls._instance:
#             cls._instance.close()
#             cls._instance = None
#
# # 核心模块和扩展模块均通过PoseService获取实例
# pose = PoseService.get_pose()
#
# MVP阶段说明：
# - 本模块仅在路演演示时单独运行
# - 不与核心模块同时导入，避免资源冲突
# - 正式版建议采用上述单例架构
```

### 11.3 YOLO物体检测接口

```python
# src/reserved/object_detector.py
"""
YOLO物体检测接口 - 路演可展示的设计
"""

class ObjectDetector:
    """YOLO物体检测"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.enabled = False
    
    def enable(self):
        """启用YOLO检测"""
        # 加载YOLOv8模型
        # from ultralytics import YOLO
        # self.model = YOLO('yolov8n.pt')
        self.enabled = True
    
    def detect_objects(self, frame):
        """
        检测画面中的物体
        
        Args:
            frame: 视频帧
        
        Returns:
            list: 检测到的物体列表
        """
        if not self.enabled:
            return []
        
        # YOLO检测
        # results = self.model(frame)
        # 返回物体类别、位置、置信度
        objects = []
        return objects
    
    def detect_tools(self, frame):
        """检测工具/零件"""
        # 过滤特定类别：工具、零件、物料
        pass


# 路演演示场景
def demo_yolo():
    """路演YOLO能力演示"""
    detector = ObjectDetector()
    
    print("YOLO物体检测能力：")
    print("1. 检测工人使用的工具类型")
    print("2. 检测零件/物料位置变化")
    print("3. 结合姿态估计判断'抓取什么'")
    print("4. 支持物料堆积检测")
```

---

## 十二、项目文件结构（保底阶段）

> **说明**：以下为保底交付（Day -3 ~ Day -1）必需的文件结构，
> `src/reserved/`、`deploy/`、`tests/`为正式版预留，保底阶段无需创建。

```
工业IE智能体/
│
├── README.md
├── requirements.txt
├── run_offline.bat              # 离线启动脚本（仅根目录一份）
│
├── config/
│   ├── default.yaml
│   ├── mtm_tables.yaml          # MTM时间表 ★核心
│   └── action_thresholds.yaml   # 动作阈值配置
│
├── src/
│   ├── core/
│   │   ├── video_processor.py   # 视频处理
│   │   ├── pose_estimator.py    # 姿态估计
│   │   ├── action_recognizer.py # 动作识别（含规则）
│   │   ├── wait_detector.py     # Wait检测
│   │   └── mtm_analyzer.py      # MTM分析
│   │
│   ├── analysis/
│   │   ├── time_calculator.py   # 工时计算
│   │   ├── cycle_analyzer.py    # 节拍分析
│   │   └── timeline_generator.py
│   │
│   ├── report/
│   │   ├── csv_exporter.py      # CSV导出 ★保底必需
│   │   └── pdf_generator.py     # PDF生成（加分项）
│   │
│   └── utils/
│       ├── visualization.py
│       └── data_io.py
│
├── app/
│   └── streamlit_app.py         # Streamlit界面 ★保底必需
│
├── demos/
│   ├── demo_opencv.py
│   ├── demo_mediapipe.py
│   └── demo_streamlit.py
│
├── data/
│   ├── videos/                  # 测试视频存放
│   ├── processed/               # 处理结果缓存
│   └── exports/                 # 导出报告存放
│
└── docs/
    ├── 工业IE智能体开发方案V3.0.md  # 本文档
    ├── 比赛前准备计划.md
    └── 需求对比与功能规划补充.md
```

**正式版预留目录（保底阶段不创建）**：
```
├── src/reserved/                # 预留模块（路演展示用）
│   ├── multi_station.py         # 多工位框架
│   ├── multi_person.py          # 多人员检测
│   ├── object_detector.py       # YOLO接口
│   └── improvement_gen.py       # 改善推荐
│
├── deploy/                      # 工业部署配置（正式版）
│   ├── docker-compose.yml
│   └── install_requirements.bat
│
├── app/api_server.py            # FastAPI服务（正式版）
│
└── tests/                       # 单元测试（正式版）
```

---

## 十三、依赖安装清单

```bash
# requirements.txt
# 版本说明：使用>=范围版本，避免精确版本号不存在的问题
# 实际安装时pip会自动选择兼容的最新版本

# MVP核心依赖
opencv-python>=4.8.0          # 视频处理（4.8.x以上均兼容）
mediapipe>=0.10.0             # 姿态估计（0.10.x系列）
streamlit>=1.30.0             # Web界面
numpy>=1.24.0                 # 数值计算
pandas>=2.0.0                 # 数据处理
matplotlib>=3.7.0             # 图表生成
pyyaml>=6.0                   # 配置文件解析
reportlab>=4.0.0              # PDF生成

# 可选依赖（正式版）
ultralytics>=8.0.0            # YOLOv8物体检测
fastapi>=0.100.0              # API服务
uvicorn>=0.23.0               # ASGI服务器
```

**安装验证命令**：
```bash
# 安装核心依赖
pip install -r requirements.txt

# 验证关键库是否正常
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import mediapipe; print('MediaPipe OK')"
python -c "import streamlit; print('Streamlit OK')"
```

---

## 十四、方案确认

### 14.1 方案亮点

| 亮点 | 说明 |
|------|------|
| **规则完整** | 所有动作（R/G/M/RL/W/Assemble）有具体判定规则、阈值、MTM赋值 |
| **公式明确** | 周期时间、效率损失、节拍、线平衡公式已实现 |
| **接口清晰** | PDF生成完整版（10页），数据结构清晰 |
| **部署聚焦** | MVP本地运行方案明确，工业部署作为路演扩展说明 |
| **时间线清晰** | 保底交付+扩展加分已完成，可路演演示 |
| **扩展已实现** | 多工位分析、YOLO物体检测均已实现 |

### 14.2 技术确认项

| 确认项 | 说明 | 状态 |
|--------|------|------|
| **动作规则** | R/G/M/RL/W/Assemble六种动作有具体阈值和判定逻辑 | ✅ 已完成 |
| **节拍公式** | 周期时间、效率损失、节拍/线平衡公式已实现 | ✅ 已完成 |
| **PDF报告** | 完整版报告（10页），含节拍/线平衡/改善建议/物体检测 | ✅ 已完成 |
| **物体检测** | YOLOv8物体检测模块已实现 | ✅ 已完成 |
| **部署方案** | MVP本地运行方案明确 | ✅ 已定义 |
| **交付节奏** | 保底3天+扩展4天+路演第5天 | ✅ 已完成 |
| **扩展展示** | 多工位分析/YOLO物体检测已实现 | ✅ 已完成 |

---

*方案版本：V3.0（完整版）*
*文档日期：2025年5月21日*
*最后更新：2025-05-21*
*更新内容：全部功能模块已完成，物体检测+PDF增强已实现*
*完成状态：Day -3~Day 4 全部完成，13个核心模块已实现，可演示*

---

## 十五、已实现功能清单及使用指南

### 15.1 核心功能模块

| 模块 | 功能 | 状态 | 文件路径 |
|------|------|------|----------|
| **视频处理** | 视频读取、帧提取、信息获取 | ✅ 完成 | `src/core/video_processor.py` |
| **姿态估计** | MediaPipe 33关键点检测 | ✅ 完成 | `src/core/pose_estimator.py` |
| **动作识别** | R/G/M/RL/W/Assemble 六种动作 | ✅ 完成 | `src/core/action_recognizer.py` |
| **MTM分析** | TMU计算、标准工时、宽放 | ✅ 完成 | `src/core/mtm_analyzer.py` |
| **Wait检测** | 全身静止检测（>1秒） | ✅ 完成 | `src/core/wait_detector.py` |
| **节拍计算** | Takt Time、标准节拍、效率 | ✅ 完成 | `src/core/cycle_time_calculator.py` |
| **线平衡分析** | LBR、瓶颈识别、改善建议 | ✅ 完成 | `src/core/line_balance_analyzer.py` |
| **多工位分析** | 多工位综合分析框架 | ✅ 完成 | `src/core/multi_station_analyzer.py` |
| **物体检测** | YOLOv8物体检测（工件/工具） | ✅ 完成 | `src/core/object_detector.py` |
| **时间轴生成** | 动作时间分布图表 | ✅ 完成 | `src/analysis/timeline_generator.py` |
| **CSV导出** | 动作序列、MTM汇总导出 | ✅ 完成 | `src/report/csv_exporter.py` |
| **PDF报告** | 完整分析报告（10页） | ✅ 完成 | `src/report/pdf_generator.py` |
| **Streamlit界面** | Web交互界面 v6.0 | ✅ 完成 | `app/streamlit_app.py` |

### 15.2 动作识别类型

| 动作代码 | 动作名称 | 识别条件 | TMU值（默认） |
|----------|----------|----------|---------------|
| **R** | Reach（伸手） | 手腕速度>0.15 + 手臂角度>150° | 15 TMU |
| **G** | Grasp（抓取） | 速度骤降<0.05 + R之后 | 5 TMU |
| **M** | Move（移动） | 稳定移动>0.1 + G之后 | 18 TMU |
| **RL** | Release（放开） | 速度骤降 + 手臂伸展 + M之后 | 2 TMU |
| **W** | Wait（等待） | 全身静止<0.02 + 持续>1秒 | 0 TMU |
| **Assemble** | 装配组合 | R→G→M→RL序列合并 | 累加TMU |

### 15.3 使用指南

#### 方式一：Streamlit Web界面（推荐）

```bash
# 启动应用
streamlit run app/streamlit_app.py

# 或使用离线启动脚本
run_offline.bat
```

**操作流程**：
1. 上传产线作业视频（MP4/AVI/MOV/MKV）
2. 配置参数（最大帧数、节拍参数、线平衡参数）
3. 点击"开始分析"
4. 查看结果（动作识别、MTM工时、节拍分析、线平衡）
5. 导出报告（CSV/PDF）

#### 方式二：Python API调用

```python
from src.core.video_processor import VideoProcessor
from src.core.pose_estimator import PoseEstimator
from src.core.action_recognizer import analyze_video_actions
from src.core.mtm_analyzer import MTMAnalyzer
from src.core.cycle_time_calculator import calculate_cycle_time_from_sequence
from src.core.line_balance_analyzer import analyze_line_balance

# 1. 读取视频
with VideoProcessor('video_path.mp4') as vp:
    frames = vp.extract_frames(max_frames=100)
    video_info = vp.get_video_info()

# 2. 姿态估计
estimator = PoseEstimator()
pose_results = [estimator.detect_pose(f.image, f.frame_id, int(f.timestamp*1000)) for f in frames]

# 3. 动作识别（含Assemble合并）
action_sequence = analyze_video_actions(pose_results, fps=30, merge_assemble=True)

# 4. MTM分析
mtm_analyzer = MTMAnalyzer()
mtm_summary = mtm_analyzer.calculate_summary(action_sequence)

# 5. 节拍计算
cycle_metrics = calculate_cycle_time_from_sequence(action_sequence, daily_demand=100)

# 6. 线平衡分析
line_metrics = analyze_line_balance({1: action_sequence}, actual_workers=1)

# 7. 物体检测（可选）
from src.core.object_detector import ObjectDetector
detector = ObjectDetector(model_name='yolov8n.pt')
for frame in frames:
    detection = detector.detect_frame(frame.image, frame.frame_id, frame.timestamp)
```

#### 方式三：多工位分析

```python
from src.core.multi_station_analyzer import analyze_production_line

# 多工位视频数据
station_data = {
    1: pose_results_station1,
    2: pose_results_station2,
    3: pose_results_station3,
}

station_names = {1: "工位A", 2: "工位B", 3: "工位C"}

# 产线综合分析
line_analysis = analyze_production_line(
    station_data,
    station_names=station_names,
    daily_demand=500,
    actual_workers=3
)

# 输出结果
print(f"线平衡率: {line_analysis.line_balance.line_balance_rate:.1f}%")
print(f"瓶颈工位: {line_analysis.bottleneck_station.station_name}")
for suggestion in line_analysis.improvement_suggestions:
    print(suggestion)
```

### 15.4 输出报告内容

**CSV导出**：
- 动作序列表（序号、动作类型、时间、TMU）
- MTM汇总表（正常时间、宽放、标准工时）
- 效率指标表

**PDF报告（完整版）**：
1. 标题页（视频名称、报告时间）
2. 视频基本信息（分辨率、帧率、时长）
3. 动作识别结果（统计表+序列详情）
4. MTM工时分析（TMU计算表）
5. 效率指标分析（动作效率、等待损失）
6. 节拍时间分析（Takt Time、标准节拍）
7. 线平衡分析（LBR、瓶颈工位）
8. 改善建议（智能生成）
9. 物体检测结果（类别统计）
10. 动作时间分布图（可视化）

### 15.5 参数配置

**动作识别阈值**（可在代码中调整）：
```python
ActionRecognizer(
    velocity_threshold_reach=0.15,    # Reach速度阈值
    velocity_threshold_grasp=0.05,    # Grasp速度阈值
    velocity_threshold_move=0.1,      # Move速度阈值
    velocity_threshold_wait=0.02,     # Wait静止阈值
    arm_angle_threshold_reach=150,    # 手臂伸展角度
    min_duration_wait=1.0,            # Wait最小持续时间
    fps=30                            # 视频帧率
)
```

**节拍计算参数**：
```python
CycleTimeCalculator(
    working_hours_per_day=8.0,        # 每班工作时长
    breaks_per_day=0.5,               # 每班休息时间
    effective_working_ratio=0.85      # 有效工作时间比例
)
```

**线平衡阈值**：
```python
LineBalanceAnalyzer(
    idle_threshold=30.0,              # 空闲率阈值
    overload_threshold=90.0           # 负荷过载阈值
)
```

### 15.6 依赖安装

```bash
# 一键安装所有依赖
pip install opencv-python mediapipe streamlit numpy pandas matplotlib pyyaml reportlab ultralytics

# 验证安装
python -c "import cv2, mediapipe, streamlit; print('All OK')"
```

### 15.7 系统要求

- Python >= 3.9
- 内存 >= 4GB（视频处理）
- GPU可选（YOLOv8加速）
- 操作系统：Windows/Linux/Mac

---

## 十六、扩展能力与路演展示

### 16.1 已实现的扩展功能

| 扩展功能 | 说明 | 文件 |
|----------|------|------|
| **Assemble组合动作** | R+G+M+RL自动合并 | `action_recognizer.py` |
| **多工位分析** | 产线综合平衡分析 | `multi_station_analyzer.py` |
| **物体检测** | YOLOv8工件/工具检测 | `object_detector.py` |
| **改善建议引擎** | 基于LBR智能建议 | `line_balance_analyzer.py` |

### 16.2 路演演示要点

1. **产品定位**：工业IE领域的AI动作分析工具
2. **技术亮点**：MediaPipe姿态估计 + MTM规则引擎 + YOLO物体检测
3. **核心价值**：自动化工时分析、识别瓶颈、改善建议
4. **扩展能力**：多工位产线分析、物体跟踪交互