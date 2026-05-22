# 工业IE智能体4.0开发方案

> **版本**：V4.0
> **定位**：多视频综合分析平台（产线系统级改善方案生成）
> **核心价值**：IE工程师的产线改善方案生成平台
> **交付节奏**：MVP保底交付（3天） + 扩展加分（4天） + 路演演示（第5天）

---

## 一、项目定位与价值主张

### 1.1 产品定位

**工业IE智能体4.0**：
- **定位**：产线系统级改善分析平台
- **用户**：IE工程师、产线改善团队
- **场景**：产线效率改善项目（多工序、多工位、多产线）
- **核心能力**：多视频综合分析 → 系统瓶颈识别 → 改善方案生成

### 1.2 用户工作流程

**IE工程师的真实工作流程**（v4.0匹配）：
```
第1步：现场调研（1-2天）
  - 拍摄多个工序视频（不同工位、不同角度）
  - 收集产线布局、工序关系、目标指标

第2步：数据整合（1天）
  - 组织视频数据（按工位/工序分组）
  - 标注工位信息、工序关系

第3步：系统分析（2-3天） ← v4.0核心能力
  - 分析各工位节拍时间
  - 计算产线整体LBR（线平衡率）
  - 识别瓶颈工位
  - 计算等待损失、产能瓶颈

第4步：改善方案（2-3天） ← v4.0核心能力
  - 生成改善目标设定
  - 提出改善措施清单
  - 预测改善效果、ROI估算
  - 制定实施路径

第5步：报告输出（1天）
  - 输出综合改善报告
  - 向管理层汇报改善方案
```

**v4.0解决IE工作流的全流程**：从现场调研到改善方案生成的完整链条。

### 1.3 核心价值主张

| 价值维度 | 传统IE工作 | v4.0方案 | 价值量化 |
|----------|-----------|---------|----------|
| **测量效率** | 2-4小时/视频 | 5-10分钟/视频 | **效率提升10-20倍** |
| **分析效率** | 人工整合多视频数据，2-3天 | 自动整合分析，30分钟 | **分析效率提升5-10倍** |
| **改善方案** | IE专家手工编写，2-3天 | AI自动生成，10分钟 | **改善方案效率提升20倍** |
| **整体效率** | 产线改善项目需7-10天 | 完整流程缩短至1-2天 | **项目周期缩短70-80%** |

**v4.0的核心价值**：
- **系统级分析自动化**：多视频综合分析、产线瓶颈识别（传统需2-3天 → v4.0需30分钟）
- **改善方案自动生成**：国产AI模型生成改善建议、ROI估算（传统需2-3天 → v4.0需10分钟）
- **整体效率提升**：产线改善项目周期从7-10天缩短至1-2天

---

## 二、系统功能规格

### 2.1 输入输出规格

| 规格 | 具体要求 |
|------|----------|
| **输入** | 多个视频文件（按工位/工序/产线分组） |
| **输入格式** | MP4/AVI/MOV/MKV |
| **输出** | 产线综合改善报告（PDF）、改善方案建议、产线指标数据 |
| **分析支持** | 多视频并发分析、产线LBR计算、瓶颈工位识别、改善方案生成 |
| **导出格式** | CSV数据导出、PDF综合报告、产线可视化图表 |

### 2.2 核心功能模块

```
┌─────────────────────────────────────────────────────┐
│          工业IE智能体4.0 - 多视频综合分析平台           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [输入层]                                           │
│   ├── 项目工作空间（创建项目、导入多视频）           │
│   ├── 多视频批量上传                                │
│   ├── 视频分组管理（工位/工序/产线）                 │
│   └── 项目目标设定                                  │
│                                                     │
│  [处理层]                                           │
│   ├── 多视频并发分析引擎                            │
│   │   ├── 视频预处理（格式转换、帧提取）           │
│   │   ├── 姿态估计（MediaPipe 33关键点）           │
│   │   ├── 动作识别（R/G/M/RL/Wait）                │
│   │   └── MTM分析（动作映射+工时计算）             │
│   │                                                 │
│   ├── 结果聚合引擎                                  │
│   │   ├── 多视频结果整合                            │
│   │   ├── 工位数据提取                              │
│   │   └── 异常数据清洗                              │
│   │                                                 │
│   └── 产线综合分析引擎                              │
│   │   ├── LBR线平衡率计算                           │
│   │   ├── 瓶颈工位识别                              │
│   │   ├── 等待时间分布分析                          │
│   │   └── 产能估算                                  │
│   │                                                 │
│   └── 改善方案生成引擎                              │
│   │   ├── 国产AI模型本地调用                        │
│   │   ├── 改善建议生成                              │
│   │   ├── ROI效果预测                               │
│   │   └── 实施路径规划                              │
│   │                                                 │
│  [输出层]                                           │
│   ├── 产线可视化视图（工位布局、瓶颈标记）           │
│   ├── LBR图表（线平衡率柱状图）                     │
│   ├── 综合改善报告（PDF，中英文双语）               │
│   └── 改善方案建议清单                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 三、技术架构设计

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────┐
│          工业IE智能体4.0系统架构                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [界面层 - Streamlit交互界面]                       │
│   ├── 项目管理界面                                  │
│   ├── 视频管理界面                                  │
│   ├── 分析控制台                                    │
│   ├── 结果可视化界面                                │
│   └── 报告导出界面                                  │
│                                                     │
│  [服务层 - 业务逻辑服务]                            │
│   ├── ProjectService - 项目管理                     │
│   ├── VideoService - 视频管理                       │
│   ├── ConcurrentAnalysisService - 并发分析调度      │
│   ├── ProductionLineAnalyzer - 产线综合分析         │
│   ├── LocalLLMService - 国产AI模型调用              │
│   └── ReportService - 报告生成                      │
│                                                     │
│  [分析引擎层 - 核心算法引擎]                        │
│   ├── 单视频分析引擎                                │
│   │   ├── VideoProcessor                            │
│   │   ├── PoseEstimator                             │
│   │   ├── ActionRecognizer                          │
│   │   └── MTMAnalyzer                               │
│   │                                                 │
│   ├── 多视频并发分析引擎                            │
│   │   ├── ConcurrentTaskScheduler                   │
│   │   ├── ResultAggregator                          │
│   │   └── ProductionLineCalculator                 │
│   │                                                 │
│   ├── 产线综合分析引擎                              │
│   │   ├── LBRCalculator                             │
│   │   ├── BottleneckDetector                        │
│   │   ├── WaitAnalyzer                              │
│   │   └── CapacityEstimator                         │
│   │                                                 │
│   └── 改善方案生成引擎                              │
│   │   ├── LocalLLMClient                            │
│   │   ├── ImprovementPromptBuilder                  │
│   │   └── ImprovementParser                         │
│   │                                                 │
│  [数据存储层]                                       │
│   ├── SQLite数据库                                  │
│   │   ├── projects表                                │
│   │   ├── videos表                                  │
│   │   ├── analysis_results表                        │
│   │   └── line_analysis_results表                   │
│   │                                                 │
│   ├── 文件存储                                      │
│   │   ├── 原始视频存储                              │
│   │   ├── 分析结果缓存                              │
│   │   └── 报告文件存储                              │
│   │                                                 │
│   └── 国产AI模型本地部署                            │
│   │   ├── DeepSeek/Qwen模型文件                    │
│   │   └── Ollama推理引擎                            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 3.2 核心数据模型

**数据库表结构设计**：

```sql
-- 项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    client_name TEXT,
    target_metrics TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    status TEXT
);

-- 视频表
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    file_path TEXT NOT NULL,
    file_name TEXT,
    group_type TEXT,
    group_name TEXT,
    metadata TEXT,
    upload_time TIMESTAMP,
    analysis_status TEXT,
    analysis_result_id INTEGER
);

-- 单视频分析结果表
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY,
    video_id INTEGER,
    action_sequence TEXT,
    mtm_summary TEXT,
    cycle_time_metrics TEXT,
    efficiency_metrics TEXT,
    created_at TIMESTAMP
);

-- 产线综合分析结果表
CREATE TABLE line_analysis_results (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    lbr_metrics TEXT,
    bottleneck_stations TEXT,
    wait_distribution TEXT,
    total_cycle_time REAL,
    capacity_estimate REAL,
    improvement_suggestions TEXT,
    created_at TIMESTAMP
);
```

---

## 四、国产AI模型本地部署方案

### 4.1 模型选型

**推荐国产模型**：

| 模型 | 提供方 | 模型大小 | 部署方案 | 适用场景 |
|------|--------|----------|----------|----------|
| **DeepSeek-V3** | DeepSeek | 67B参数 | Ollama本地部署 | 改善方案生成（推荐） |
| **Qwen2.5-72B** | 阿里云 | 72B参数 | Ollama本地部署 | 改善方案生成（备选） |
| **GLM-4-9B** | 智谱AI | 9B参数 | 本地推理 | 轻量部署（备选） |

**推荐方案**：**DeepSeek-V3 + Ollama本地部署**
- DeepSeek-V3性价比高，推理能力强
- Ollama部署简单，一键安装
- 无需云端API，完全本地运行
- 数据安全，不上传云端

### 4.2 Ollama部署方案

**部署流程**：
```bash
# 1. 安装Ollama
# Windows: 下载Ollama Windows安装包（https://ollama.com）
# Linux/Mac: curl -fsSL https://ollama.com/install.sh | sh

# 2. 拉取DeepSeek模型
ollama pull deepseek-r1:671b

# 3. 启动Ollama服务
ollama serve  # 默认端口：http://localhost:11434

# 4. 测试模型
ollama run deepseek-r1:671b
```

### 4.3 LocalLLMClient模块设计

**LocalLLMClient模块**：
```python
import requests
import json

class LocalLLMClient:
    """
    国产AI模型本地客户端（Ollama接口）
    - 支持DeepSeek、Qwen等国产模型
    - 本地推理，无云端依赖
    - 支持长文本生成（改善方案）
    """

    def __init__(self, model_name: str = "deepseek-r1:671b"):
        self.base_url = "http://localhost:11434"
        self.model_name = model_name

    async def generate_improvement_suggestions(
        self,
        project_data: dict,
        analysis_results: dict
    ) -> dict:
        """
        生成改善方案建议
        - 构建改善方案Prompt
        - 调用Ollama本地推理
        - 解析改善建议
        """
        prompt = ImprovementPromptBuilder.build(
            project_data, analysis_results
        )

        # 调用Ollama API
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 4000
                }
            },
            timeout=120
        )

        result = response.json()
        improvement_text = result["response"]

        # 解析改善建议
        return ImprovementParser.parse(improvement_text)
```

### 4.4 改善方案Prompt设计

**改善方案Prompt模板（中文）**：
```python
IMPROVEMENT_PROMPT_TEMPLATE_ZH = """
你是一位资深工业工程（IE）专家，请基于以下产线分析数据生成改善方案建议。

## 项目背景
- 项目名称：{project_name}
- 客户：{client_name}
- 目标：提升产线效率，线平衡率目标85%

## 现状诊断数据
### 产线整体指标
- 线平衡率（LBR）：{lbr}%（当前值，目标85%）
- 总节拍时间：{total_cycle_time}秒
- 产能估算：{capacity_estimate}件/小时

### 各工位分析结果
{station_analysis_results}

### 瓶颈工位识别
- 瓶颈工位：{bottleneck_station}（节拍时间{bottleneck_cycle_time}秒）
- 瓶颈原因：{bottleneck_reasons}

### 等待时间分布
{wait_distribution}

## 改善要求
请生成详细的改善方案建议，包括：

1. **改善目标设定**
   - 线平衡率目标（建议85%以上）
   - 节拍时间目标（具体数值）
   - 产能提升目标（百分比）

2. **改善措施清单**（每个工位至少2-3项建议）
   - 工位A改善建议（具体措施、预计效果）
   - 工位B改善建议（具体措施、预计效果）
   - 瓶颈工位改善建议（至少5项措施，重点改善）
   - 综合改善建议（系统级措施）

3. **改善效果预测**
   - 预计效率提升（百分比）
   - 预计成本节省（金额估算）
   - ROI估算（投资回报周期）

4. **改善实施路径**
   - 第一阶段改善（快速见效措施，1-2周实施）
   - 第二阶段改善（中期优化措施，1-2月实施）
   - 第三阶段改善（长期提升措施，3-6月实施）

请以结构化格式输出改善建议，便于报告生成。
"""
```

### 4.5 本地部署优势

**国产AI模型本地部署的优势**：
1. **无API成本**：本地推理，无需云端API调用费用
2. **无网络依赖**：完全本地运行，适合工业现场离线环境
3. **数据安全**：分析数据不上传云端，满足企业数据安全要求
4. **推理质量**：DeepSeek-V3推理能力强，改善建议质量高
5. **部署简单**：Ollama一键部署，无需复杂配置

---

## 五、MVP版本定义

### 5.1 MVP核心功能

**v4.0 MVP的核心目标**：
- 实现多视频上传与组织（项目工作空间）
- 实现并发分析多个视频
- 实现产线综合指标计算（LBR、瓶颈识别）
- 实现改善方案生成（国产AI模型本地部署）
- 实现综合改善报告导出

**MVP功能清单**：

| 功能类别 | MVP功能 | 优先级 | 说明 |
|----------|---------|--------|------|
| **项目管理** | 创建项目、导入多视频、基本分组 | P0 | 最小项目管理能力 |
| **视频管理** | 批量上传、按工位分组（仅1种策略） | P0 | 仅支持工位分组，简化MVP |
| **分析执行** | 并发分析多视频（固定并发数） | P0 | 多视频并发分析（核心能力） |
| **综合分析** | 线平衡率计算、瓶颈工位识别 | P0 | 产线系统级分析（核心能力） |
| **改善方案** | 国产AI模型本地部署生成改善建议 | P0 | AI改善方案生成（核心能力） |
| **报告生成** | 中文综合改善报告（简化版） | P1 | 综合报告导出 |
| **界面交互** | Streamlit单页界面 | P1 | MVP最小界面 |

### 5.2 MVP开发节奏

**交付节奏**：保底交付（3天） + 扩展加分（4天） + 路演演示（第5天）

#### 保底交付（Day -3 ~ Day -1，3天）

| 时间 | 开发任务 | 关键模块 | 验收标准 |
|------|----------|----------|----------|
| **Day -3** | 项目架构 + 数据库 + 项目管理 | ProjectService, VideoService, DatabaseManager | 能创建项目、导入5+视频 |
| **Day -2** | 并发分析 + 综合指标计算 | ConcurrentAnalysisService, LBRCalculator, BottleneckDetector | 能并发分析、计算LBR、识别瓶颈 |
| **Day -1** | 国产AI模型 + 改善方案 + 报告生成 | LocalLLMClient, ImprovementPromptBuilder, ComprehensiveReportGenerator | 能生成改善建议、导出PDF报告 |

**保底交付验收标准**：
- [ ] 能创建项目工作空间
- [ ] 能批量上传5+视频并按工位分组
- [ ] 能并发分析多个视频（并发数>=2）
- [ ] 能计算产线整体LBR、识别瓶颈工位
- [ ] 能调用国产AI模型生成改善建议（本地部署）
- [ ] 能导出中文综合改善报告（PDF）

#### 扩展加分（Day 1 ~ Day 4，4天）

| 时间 | 开发任务 | 优先级 | 说明 |
|------|----------|--------|------|
| **Day 1** | 多分组策略（工位/工序/产线） + 用户可配置并发数 | P1 | 功能扩展 |
| **Day 2** | 跨视频对比分析 + 产线可视化界面 | P2 | 深度分析能力 |
| **Day 3** | 双语报告生成（中英文） + 报告结构完善 | P2 | 国际化能力 |
| **Day 4** | 界面优化 + 性能优化 + 用户体验打磨 | P3 | 产品打磨 |

#### 路演演示（Day 5）

- 完整演示v4.0的多视频综合分析流程
- 演示产线改善方案生成能力
- 展示系统性价值

### 5.3 MVP新增模块清单

| 新增模块 | 文件路径 | 功能说明 | 开发时间 |
|----------|----------|----------|----------|
| **ProjectService** | `src/services/project_service.py` | 项目工作空间管理 | Day -3 |
| **VideoService** | `src/services/video_service.py` | 多视频批量管理 | Day -3 |
| **DatabaseManager** | `src/services/db_manager.py` | SQLite项目管理 | Day -3 |
| **ConcurrentAnalysisService** | `src/services/concurrent_analysis_service.py` | 多视频并发分析调度 | Day -2 |
| **ResultAggregator** | `src/core/result_aggregator.py` | 多视频结果聚合 | Day -2 |
| **LBRCalculator** | `src/core/lbr_calculator.py` | 线平衡率计算 | Day -2 |
| **BottleneckDetector** | `src/core/bottleneck_detector.py` | 瓶颈工位识别 | Day -2 |
| **LocalLLMClient** | `src/core/local_llm_client.py` | 国产AI模型客户端 | Day -1 |
| **ImprovementPromptBuilder** | `src/core/improvement_prompt_builder.py` | 改善方案Prompt构建 | Day -1 |
| **ImprovementParser** | `src/core/improvement_parser.py` | 改善建议解析 | Day -1 |
| **ComprehensiveReportGenerator** | `src/report/comprehensive_report_generator.py` | 综合报告生成 | Day -1 |
| **StreamlitProjectApp** | `app/streamlit_project_app.py` | 项目级界面 | Day -3~-1 |

**总计新增模块**：12个核心模块

---

## 六、功能分级规划

### 6.1 MVP版本（3天保底交付）

**目标**：验证多视频综合分析的核心价值，实现产线改善方案生成。

**核心功能**：
- ✅ 项目工作空间管理
- ✅ 多视频并发分析
- ✅ 产线综合指标计算（LBR、瓶颈识别）
- ✅ 国产AI模型改善方案生成
- ✅ 中文综合改善报告导出

### 6.2 正式版本（8周商业化开发）

**目标**：完整的多视频综合分析平台，满足IE工程师日常工作需求。

**正式版新增功能**：

| 功能类别 | 正式版新增功能 | 优先级 |
|----------|---------------|--------|
| **项目管理** | 项目导入/导出、项目模板、历史项目 | P1 |
| **视频管理** | 多分组策略（工位/工序/产线）、智能分组 | P0 |
| **分析执行** | 用户可配置并发数（1-8）、进度实时监控 | P0 |
| **综合分析** | 跨视频对比分析、时段对比、产线对比 | P1 |
| **改善方案** | 改善方案质量优化、多轮对话优化 | P1 |
| **报告生成** | 双语报告（中英文）、完整报告结构 | P0 |
| **界面交互** | 多页界面、产线可视化、对比图表 | P1 |

**正式版开发时间**：8周
- Week 1-2：多分组策略、用户可配置并发数、进度监控
- Week 3-4：跨视频对比分析、产线可视化界面
- Week 5-6：双语报告生成、改善方案优化
- Week 7-8：界面优化、性能优化、用户体验打磨

### 6.3 工业部署版本（4周生产级开发）

**目标**：满足工业客户部署需求，提升稳定性、安全性和企业级功能。

**工业部署版新增功能**：

| 功能类别 | 工业部署版新增功能 | 优先级 |
|----------|-------------------|--------|
| **数据安全** | 数据加密、数据库备份、密钥安全存储 | P0 |
| **稳定性** | 错误恢复、任务重试、异常日志 | P0 |
| **权限管理** | 用户登录、项目权限、操作审计 | P1 |
| **部署方案** | Docker容器化、离线部署、私有化部署 | P0 |
| **性能优化** | 大规模视频处理优化、内存优化 | P1 |
| **集成能力** | ERP/MES集成接口、REST API接口 | P2 |

**工业部署版开发时间**：4周
- Week 9：数据安全、稳定性提升
- Week 10：权限管理、部署方案
- Week 11：性能优化、监控运维
- Week 12：集成能力、定制能力

---

## 七、技术栈选型

### 7.1 核心技术栈

| 技术层 | 选型 | 版本要求 | 用途说明 |
|--------|------|----------|----------|
| **视频处理** | OpenCV | >=4.8.0 | 视频读取、帧提取、预处理 |
| **姿态估计** | MediaPipe Pose | >=0.10.0 | 人体33关键点检测 |
| **动作识别** | 规则引擎 | V2.0（自研） | 基于关键点位移判断 |
| **MTM引擎** | Python规则库 | V2.0（自研） | MTM标准表查值 |
| **数据处理** | pandas | >=2.0.0 | CSV导出与分析 |
| **PDF生成** | ReportLab | >=4.0.0 | PDF报告生成 |
| **图表生成** | matplotlib | >=3.7.0 | 动作时间分布图 |
| **交互界面** | Streamlit | >=1.30.0 | Web交互界面 |
| **并发调度** | asyncio | Python内置 | 多视频并发分析 |
| **数据库** | SQLite | Python内置 | 项目数据管理 |
| **AI模型** | DeepSeek-V3 | 67B参数 | 改善方案生成（本地部署） |
| **模型部署** | Ollama | 最新版 | 本地推理引擎 |

### 7.2 新增依赖

| 库 | 版本 | 用途 |
|---|------|------|
| `asyncio` | Python内置 | 异步任务调度 |
| `aiosqlite` | 0.20.0 | 异步SQLite操作 |
| `concurrent.futures` | Python内置 | 并行处理线程池 |
| `plotly` | 5.24.0 | 交互式图表（产线视图） |
| `jinja2` | 3.1.4 | 报告模板渲染 |
| `requests` | 2.32.0 | Ollama API调用 |

---

## 八、验证方案

### 8.1 MVP验收标准

- [ ] 能创建项目并导入5+视频
- [ ] 能批量上传视频并按工位分组
- [ ] 能并发分析多个视频（并发数>=2）
- [ ] 能计算产线整体LBR、识别瓶颈工位
- [ ] 能调用国产AI模型生成改善建议（本地部署）
- [ ] 能导出中文综合改善报告PDF

### 8.2 正式版验收标准

- [ ] 支持工位/工序/产线三种分组策略
- [ ] 用户可配置并发数（1-8）
- [ ] 实时显示分析进度
- [ ] 国产AI模型成功生成改善建议（质量高）
- [ ] 支持中英文双语报告生成
- [ ] 产线可视化界面清晰直观
- [ ] 对比分析功能可用

### 8.3 工业部署版验收标准

- [ ] 数据加密有效
- [ ] 错误恢复机制工作
- [ ] 用户权限管理可用
- [ ] Docker容器成功部署并运行
- [ ] 离线部署可用（无网络环境）
- [ ] 10+视频大规模处理性能稳定
- [ ] 操作日志审计功能完整

---

## 九、项目文件结构

```
工业IE智能体/
├── README.md
├── requirements.txt
│
├── config/
│   ├── default.yaml
│   ├── mtm_tables.yaml
│   └── ollama_config.yaml          # Ollama配置
│
├── src/
│   ├── core/                       # 核心分析模块
│   │   ├── video_processor.py
│   │   ├── pose_estimator.py
│   │   ├── action_recognizer.py
│   │   ├── mtm_analyzer.py
│   │   ├── result_aggregator.py    # 新增：结果聚合
│   │   ├── lbr_calculator.py       # 新增：LBR计算
│   │   ├── bottleneck_detector.py  # 新增：瓶颈识别
│   │   ├── local_llm_client.py     # 新增：国产AI客户端
│   │   ├── improvement_prompt_builder.py  # 新增：Prompt构建
│   │   └── improvement_parser.py   # 新增：改善建议解析
│   │
│   ├── services/                   # 服务层
│   │   ├── project_service.py      # 新增：项目管理
│   │   ├── video_service.py        # 新增：视频管理
│   │   ├── concurrent_analysis_service.py  # 新增：并发分析
│   │   ├── db_manager.py           # 新增：数据库管理
│   │   └── report_service.py       # 新增：报告服务
│   │
│   └── report/                     # 报告模块
│   │   ├── comprehensive_report_generator.py  # 新增：综合报告
│   │   └── csv_exporter.py
│   │
│   └── utils/
│   │   └── visualization.py
│
├── app/
│   └── streamlit_project_app.py    # 新增：项目级界面
│
├── models/                         # 国产AI模型文件
│   ├── deepseek/                   # DeepSeek模型
│   └── ollama/                     # Ollama推理引擎
│
├── data/
│   ├── projects/                   # 项目数据存储
│   │   ├── {project_id}/
│   │   │   ├── videos/
│   │   │   ├── analysis_results/
│   │   │   ├── exports/
│   │   │   └── config.yaml
│   │
│   ├── database/                   # SQLite数据库
│   │   └── ie_agent.db
│   │
│   └── exports/                    # 导出报告
│
└── docs/
    └── 工业IE智能体开发方案V4.0.md  # 本文档
```

---

## 十、开发实施路径总结

| 版本 | 开发时间 | 核心价值 | 目标用户 |
|------|---------|----------|----------|
| **MVP版本** | 3天 | 验证多视频综合分析价值 | 内部验证、早期用户 |
| **正式版本** | 8周（累计9周） | 完整IE改善方案生成平台 | IE工程师、中小企业 |
| **工业部署版本** | 4周（累计13周） | 生产级企业部署平台 | 大型企业、工业客户 |

**整体时间规划**：
- MVP保底交付：3天（Day -3 ~ Day -1）
- MVP扩展加分：4天（Day 1 ~ Day 4）
- 正式版开发：8周
- 工业部署版开发：4周
- 总计：13周完整交付

---

## 十一、架构决策确认

### 决策1：视频分组策略（同时支持多种策略）
**选择**：同时支持工位、工序、产线三种分组策略，用户可自选。
**影响**：
- 数据模型需设计灵活的分组类型字段
- 界面需提供分组策略切换功能
- 分析流程需适配不同分组类型

### 决策2：改善方案生成（国产AI模型本地部署）
**选择**：DeepSeek-V3 + Ollama本地部署，而非云端API。
**影响**：
- 无API成本，完全本地运行
- 无网络依赖，适合工业现场离线环境
- 数据安全，不上传云端
- 需要Ollama部署和模型下载

### 册策3：并发分析数量（用户可配置1-8）
**选择**：用户可配置并发数（1-8），而非固定值或自动调整。
**影响**：
- 界面需提供并发数配置滑块（1-8）
- 系统需提供推荐并发数计算
- 异步任务调度器需支持并发数控制

### 册策4：报告语言支持（同时支持中英文报告）
**选择**：同时支持中英文报告，用户可选择生成语言版本。
**影响**：
- 需要设计双语报告模板
- 需要术语翻译对照表
- 报告生成服务需支持语言切换

---

## 十二、下一步行动

1. **已完成架构规划**：v4.0架构规划已完成
2. **启动MVP开发**：Day -3开始数据层重构
3. **Ollama部署**：提前准备Ollama和DeepSeek模型
4. **迭代验证**：每天里程碑验证与调整