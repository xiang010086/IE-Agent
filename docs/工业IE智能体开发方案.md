# 工业IE智能体开发方案

## 一、设计理念与产品定位

### 1.1 传统工业工程数字化的问题

**传统思路的局限**：
```
数据流向：工人动作 → 效率数字 → 绩效排名 → 扣钱/施压
分析对象：单个工人的效率
核心问题："这个人够不够快？"
最终用途：管理层用来考核工人
```

**问题所在**：
- 把技术用来"盯着人"，而非"改善系统"
- MTM拆解目的是算"你比标准慢了3秒"
- 输出报告是绩效排名
- 最终可能造成工人对技术的抵触和恐惧

### 1.2 本产品的核心理念

**重新提问，改变系统指向**：
```
数据流向：工人动作 → 动作偏差分析 → 系统瓶颈识别 → 改善方案
分析对象：产线系统（设备、物料、布局、工装）
核心问题："这个动作设计得合不合理？有没有危险？新手容不容易出错？"
最终用途：保护工人、改善产线、降低培训成本
```

**三点产品定位**：

| 定位 | 传统做法 | 本产品做法 |
|------|----------|------------|
| **IE工程师工具** | 重复性看录像、掐表、填Excel | AI自动完成分析，专家只做决策 |
| **管理视角** | 个人绩效排名、扣钱施压 | 产线级瓶颈分析（物料堆积？工位不平衡？） |
| **对工人** | 抓违规、考核慢的人 | 识别危险/疲劳动作，当动作教练，预防工伤 |

### 1.3 产品价值主张

**对IE工程师的价值**：
- 从"录像带看守"变成"产线改善设计者"
- AI处理80%重复性工作（动作识别、MTM拆解、工时测算、报告生成）
- 专注20%高价值决策（改善方案设计、工装开发、标准制定）

**对管理层的价值**：
- 不看"谁慢"，看"哪里卡"
- 系统级问题归因：设备、物料、布局、工装，而非个人
- 改善方案可落地：如"料箱左移20cm，整条产线受益"

**对新人的价值**：
- 动作教练而非违规警察
- 识别危险动作预警，预防工伤
- 降低培训周期和出错率

### 1.4 项目需求

**核心功能**：AI视觉分析系统，通过产线作业视频实现：
- 动作自动识别（识别偏差而非考核速度）
- MTM标准动作拆解（验证标准合理性而非算差距）
- 工时测算（评估动作设计而非考核个人）
- 产线节拍分析（识别系统瓶颈而非个人瓶颈）
- 自动生成改善报告（而非绩效排名）

**业务目标**：赋能IE工程师、改善产线系统、保护工人安全

### 1.5 用户情况

- 用户学过机器视觉但未深入掌握，计划使用AI辅助编程（vibe coding）
- 需求方拥有工厂产线、精益改善与工业工程应用场景
- 需求方有具身智能多岗位机器人开发工作
- 需求方将提供所需资源（数据、硬件、IE工程师支持）

---

## 二、推荐技术方案

### 2.1 技术栈选型

| 层级 | 技术选择 | 理由 |
|------|----------|------|
| **姿态估计** | MediaPipe Pose | 开箱即用、轻量级、33关键点、CPU实时运行 |
| **视频处理** | OpenCV + FFmpeg | Python友好、文档丰富、工业标准 |
| **动作识别** | 规则引擎 + 轻量LSTM | 初期规则映射快速可用，后期可引入学习优化 |
| **MTM引擎** | Python规则库 | 直接编码MTM标准表，逻辑清晰 |
| **前端界面** | Streamlit | 30行代码即可搭建Web界面，快速验证 |
| **报告生成** | Jinja2 + Markdown/HTML | 简洁模板系统，易于定制 |
| **开发语言** | Python 3.9+ | AI生态最成熟，学习资源丰富 |

### 2.2 核心依赖库

```
opencv-python       # 视频处理
mediapipe           # 姿态估计（关键点检测）
numpy               # 数值计算
pandas              # 数据处理
torch               # 深度学习框架（可选）
streamlit           # Web界面
jinja2              # 报告模板
matplotlib          # 图表生成
pyyaml              # 配置文件
```

---

## 三、系统架构设计

### 3.1 功能模块划分（以改善为导向）

```
┌─────────────────────────────────────────────────────────────┐
│               工业IE智能体系统（改善导向版）                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │视频输入  │───▶│姿态估计  │───▶│动作识别  │              │
│  │模块      │    │模块      │    │模块      │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │              │              │                       │
│       ▼              ▼              ▼                       │
│  ┌───────────────────────────────────────────────┐         │
│  │               动作偏差分析层                     │         │
│  │  动作合理性 / 危险性 / 易错性 / 疲劳度           │         │
│  └───────────────────────────────────────────────┘         │
│                      │                                      │
│                      ▼                                      │
│  ┌───────────────────────────────────────────────┐         │
│  │               系统瓶颈识别层                     │         │
│  │  设备瓶颈 / 物料瓶颈 / 布局瓶颈 / 工装瓶颈        │         │
│  └───────────────────────────────────────────────┘         │
│                      │                                      │
│                      ▼                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │MTM合理性 │    │改善方案  │───▶│报告生成  │              │
│  │验证模块  │───▶│推荐模块  │    │模块      │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                                             │
│  ┌───────────────────────────────────────────────┐         │
│  │               新人教练模块（可选）               │         │
│  │  动作正确性指导 / 危险预警 / 培训进度追踪        │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 模块职责说明（重新定义）

| 模块 | 功能 | 输入 | 输出 | 与传统方案的区别 |
|------|------|------|------|-----------------|
| **视频输入** | 视频加载、帧提取 | 视频文件 | 帧序列 | 无变化 |
| **姿态估计** | 人体关键点检测 | 视频帧 | 33关键点序列 | 无变化 |
| **动作识别** | 识别动作类型与偏差 | 关键点序列 | 动作列表 + 偏差分析 | **识别偏差而非考核速度** |
| **动作偏差分析** | 分析动作合理性、危险性 | 动作序列 | 偏差类型、危险等级 | **新增核心模块** |
| **系统瓶颈识别** | 识别产线瓶颈源头 | 多工位数据 | 瓶颈类型、位置、原因 | **归因于系统而非个人** |
| **MTM合理性验证** | 验证标准工时是否合理 | MTM分析结果 | 标准建议：放宽/增加辅助 | **验证标准而非算差距** |
| **改善方案推荐** | 生成可落地的改善建议 | 系统分析结果 | 具体改善方案（如料箱左移20cm） | **新增核心模块** |
| **报告生成** | 生成改善报告 | 全部结果 | 改善报告（而非绩效排名） | **输出改善而非考核** |

### 3.3 核心分析维度

**动作偏差分析维度**：

| 偏差类型 | 检测指标 | 改善指向 |
|----------|----------|----------|
| **动作合理性** | 动作幅度、路径曲折度 | 工位布局优化 |
| **动作危险性** | 关节过载、不良姿势、急停急转 | 工装辅助、姿势培训 |
| **动作易错性** | 动作复杂度、步骤数、对齐精度 | 标准化、防呆设计 |
| **动作疲劳度** | 重复次数、负重时长、姿势保持 | 人机工程优化 |
| **动作一致性** | 不同工人动作差异度 | 标准动作培训 |

**系统瓶颈识别维度**：

| 瓶颈类型 | 检测指标 | 改善指向 |
|----------|----------|----------|
| **设备瓶颈** | 设备等待时间、故障频率 | 设备维护、自动化升级 |
| **物料瓶颈** | 取料等待、物料堆积 | 物料配送优化、料箱位置调整 |
| **布局瓶颈** | 走动距离、转身次数 | 工位布局重排 |
| **工装瓶颈** | 操作难度、对齐耗时 | 工装改良、辅助器具 |
| **节拍不平衡** | 各工位时间差异 | 线平衡优化、人员调整 |

### 3.4 报告输出对比

**传统报告 vs 本产品报告**：

| 维度 | 传统工业工程报告 | 本产品报告 |
|------|------------------|------------|
| **标题** | "员工绩效效率分析" | "产线改善机会分析" |
| **核心数据** | 个人工时 vs 标准工时 | 动作偏差类型 + 系统瓶颈位置 |
| **问题归因** | "员工A比标准慢15%" | "工位3取料距离过长，建议料箱左移20cm" |
| **改善建议** | "员工需提升效率" | "优化料箱位置、增加辅助工装、调整标准工时" |
| **输出对象** | HR用于考核 | IE工程师用于改善设计 |
| **对工人影响** | 可能扣钱、压力大 | 工作更安全、更轻松、培训更容易 |

---

## 四、MTM标准动作知识库

### 4.1 MTM-1核心动作要素

MTM-1 将手工操作分解为 **10种基本动作要素**：

| 代码 | 动作名称 | 说明 | 影响因素 |
|------|----------|------|----------|
| **R** | Reach（伸手） | 手移动到目标位置 | 距离、条件类型(A/B/C) |
| **M** | Move（移动） | 移动物体到目标位置 | 距离、重量、条件 |
| **T** | Turn（转动） | 手部绕前臂轴旋转 | 转动角度、重量 |
| **G** | Grasp（抓取） | 获取对物体的控制 | 抓取类型(接触/简单/复杂) |
| **P** | Position（定位） | 对齐、定向和接合物体 | 配合等级(松/紧/非常紧) |
| **RL** | Release（放开） | 松开物体 | 放开类型 |
| **D** | Disengage（拆卸） | 断开物体间接触 | 配合等级、阻力 |
| **AP** | Apply Pressure（施压） | 对物体施加力 | 施压类型 |
| **SE** | Seat（对齐） | 使物体对齐就位 | 对齐类型 |
| **EYE** | Eye Action（眼动作） | 目视检查、确认 | 检查复杂度 |

### 4.2 时间测量单位 (TMU)

```
1 TMU = 0.00001小时 = 0.0006分钟 = 0.036秒

常用换算:
- 100 TMU = 3.6秒
- 1000 TMU = 36秒
- 1分钟 = 1667 TMU
```

### 4.3 MTM时间表示例（简化版）

```yaml
# config/mtm_tables.yaml - MTM时间标准表
reach:
  # R - 伸手动作
  distances:
    short:   # < 10cm
      case_A: 8   # TMU值
      case_B: 10
      case_C: 12
    medium:  # 10-25cm
      case_A: 15
      case_B: 18
      case_C: 22
    long:    # > 25cm
      case_A: 22
      case_B: 26
      case_C: 30

grasp:
  # G - 抓取动作
  types:
    contact: 2     # G0 - 接触抓取
    simple: 5      # G1 - 简单抓取
    transfer: 8    # G3 - 转移抓取
    complex: 12    # G5 - 复杂抓取

move:
  # M - 移动动作
  distances:
    short:
      case_A: 10
      case_B: 12
    medium:
      case_A: 18
      case_B: 22
  weight_adjustment:
    light: 0       # < 1kg
    medium: +5     # 1-5kg
    heavy: +12     # > 5kg

position:
  # P - 定位动作
  classes:
    loose: 5       # P1 - 松配合
    close: 15      # P2 - 紧配合
    precise: 30    # P3 - 精密配合
```

---

## 五、关键算法设计

### 5.1 姿态估计流程（无变化）

```python
# 伪代码 - 姿态估计核心流程
def estimate_pose(video_path):
    """
    输入: 视频文件路径
    输出: 关键点序列 [(frame_id, keypoints_array)]
    """
    # 1. 初始化MediaPipe
    pose = MediaPipePose(model_complexity=1)

    # 2. 逐帧处理
    keypoints_sequence = []
    for frame_id, frame in read_frames(video_path):
        keypoints = pose.process(frame)
        keypoints_sequence.append((frame_id, keypoints))

    # 3. 关键点追踪与平滑
    smoothed_sequence = smooth_keypoints(keypoints_sequence)

    return smoothed_sequence

# MediaPipe 33关键点索引（重点关注上半身）
KEYPOINT_NAMES = {
    0: 'nose',
    11: 'left_shoulder', 12: 'right_shoulder',
    13: 'left_elbow', 14: 'right_elbow',
    15: 'left_wrist', 16: 'right_wrist',
    17: 'left_pinky', 18: 'right_pinky',
    19: 'left_index', 20: 'right_index',
    21: 'left_thumb', 22: 'right_thumb',
    23: 'left_hip', 24: 'right_hip'
}
```

### 5.2 动作识别 + 偏差分析（新增核心）

```python
# 伪代码 - 动作识别与偏差分析
def analyze_actions_with_deviation(keypoints_sequence):
    """
    输入: 关键点时间序列
    输出: [(action_type, deviation_analysis, start_frame, end_frame)]
    
    核心改变：不仅识别动作，还分析动作偏差
    """
    actions = []

    # 1. 识别动作序列
    action_sequence = recognize_basic_actions(keypoints_sequence)

    # 2. 对每个动作进行偏差分析（核心新增）
    for action_type, start, end in action_sequence:
        segment = keypoints_sequence[start:end]

        # === 动作偏差分析 ===
        deviation = analyze_action_deviation(segment, action_type)

        actions.append({
            'action': action_type,
            'start': start,
            'end': end,
            'deviation': deviation  # 偏差分析结果
        })

    return actions

def analyze_action_deviation(segment, action_type):
    """
    分析单个动作的偏差 - 新增核心模块
    
    返回：偏差类型、严重程度、改善建议
    """
    deviation_result = {
        '合理性': None,
        '危险性': None,
        '易错性': None,
        '疲劳度': None
    }

    # === 1. 动作合理性分析 ===
    # 计算动作路径曲折度
    path_tortuosity = calculate_path_tortuosity(segment, 'wrist')
    if path_tortuosity > threshold:
        deviation_result['合理性'] = {
            '问题': '动作路径曲折',
            '严重度': calculate_severity(path_tortuosity),
            '改善': '优化工位布局，减少转身/绕行'
        }

    # 计算动作幅度
    amplitude = calculate_action_amplitude(segment)
    if amplitude > threshold:
        deviation_result['合理性'] = {
            '问题': '动作幅度过大',
            '严重度': calculate_severity(amplitude),
            '改善': '调整物料位置，缩短取料距离'
        }

    # === 2. 动作危险性分析 ===
    # 检测关节过载
    joint_overload = detect_joint_overload(segment)
    if joint_overload:
        deviation_result['危险性'] = {
            '问题': f'{joint_overload["joint"]}关节过载',
            '严重度': 'HIGH',
            '改善': '增加辅助工装，减少关节负担'
        }

    # 检测不良姿势（弯腰、扭转）
    bad_posture = detect_bad_posture(segment)
    if bad_posture:
        deviation_result['危险性'] = {
            '问题': f'不良姿势：{bad_posture}',
            '严重度': 'HIGH',
            '改善': '调整工位高度/角度，减少弯腰扭转'
        }

    # === 3. 动作易错性分析 ===
    # 计算对齐精度要求
    alignment_precision = calculate_alignment_precision(segment)
    if alignment_precision < threshold:
        deviation_result['易错性'] = {
            '问题': '对齐精度要求过高',
            '严重度': 'MEDIUM',
            '改善': '增加防呆设计或定位辅助'
        }

    # === 4. 动作疲劳度分析 ===
    # 计算姿势保持时间
    posture_hold_time = calculate_posture_hold_time(segment)
    if posture_hold_time > threshold:
        deviation_result['疲劳度'] = {
            '问题': '姿势保持时间过长',
            '严重度': 'MEDIUM',
            '改善': '增加短暂休息位或轮换机制'
        }

    return deviation_result
```

### 5.3 系统瓶颈识别（新增核心）

```python
# 伪代码 - 系统瓶颈识别
def identify_system_bottlenecks(multi_station_data):
    """
    输入: 多工位分析数据
    输出: 系统瓶颈类型、位置、原因、改善方案
    
    核心改变：归因于系统而非个人
    """
    bottlenecks = []

    # === 1. 节拍不平衡分析 ===
    cycle_times = [station['cycle_time'] for station in multi_station_data]
    max_time = max(cycle_times)
    min_time = min(cycle_times)
    balance_rate = sum(cycle_times) / (max_time * len(cycle_times))

    if balance_rate < 0.85:  # 线平衡率低于85%
        bottleneck_station = identify_bottleneck_station(cycle_times)
        bottlenecks.append({
            '类型': '节拍不平衡',
            '位置': f'工位{bottleneck_station}',
            '原因': '瓶颈工位作业时间过长',
            '改善': [
                '拆分瓶颈工位作业',
                '增加辅助人员',
                '自动化瓶颈工序'
            ]
        })

    # === 2. 物料瓶颈分析 ===
    for station in multi_station_data:
        if station['物料等待时间'] > threshold:
            bottlenecks.append({
                '类型': '物料瓶颈',
                '位置': f'工位{station["id"]}',
                '原因': '取料等待时间过长',
                '改善': [
                    f'调整料箱位置（建议左移{calculate_distance(station)}cm）',
                    '优化物料配送频次',
                    '增加前置物料缓冲'
                ]
            })

    # === 3. 布局瓶颈分析 ===
    for station in multi_station_data:
        walk_distance = station['走动距离']
        turn_count = station['转身次数']
        if walk_distance > threshold or turn_count > threshold:
            bottlenecks.append({
                '类型': '布局瓶颈',
                '位置': f'工位{station["id"]}',
                '原因': f'走动距离{walk_distance}m，转身{turn_count}次',
                '改善': [
                    '优化工位布局',
                    '物料就近放置',
                    '减少转身操作'
                ]
            })

    # === 4. 设备瓶颈分析 ===
    for station in multi_station_data:
        if station['设备等待时间'] > threshold:
            bottlenecks.append({
                '类型': '设备瓶颈',
                '位置': f'工位{station["id"]}',
                '原因': '设备响应慢或故障频发',
                '改善': [
                    '设备维护保养',
                    '升级自动化设备',
                    '增加备用设备'
                ]
            })

    return bottlenecks
```

### 5.4 MTM合理性验证（核心改变）

```python
# 伪代码 - MTM合理性验证（而非算差距）
def validate_mtm_standard(mtm_analysis, deviation_analysis):
    """
    输入: MTM分析结果、偏差分析结果
    输出: 标准工时合理性评估 + 调整建议
    
    核心改变：不是算"你慢了3秒"，而是验证"标准是否合理"
    """
    validation_result = {
        '标准工时': mtm_analysis['标准工时'],
        '合理性': '待评估',
        '调整建议': [],
        '辅助工装建议': []
    }

    # === 根据偏差分析验证标准合理性 ===
    for action in deviation_analysis:
        if action['deviation']['危险性']:
            # 存在危险动作 → 标准可能反人类，需放宽或增加辅助
            validation_result['合理性'] = '需调整'
            validation_result['调整建议'].append({
                '动作': action['action'],
                '原因': action['deviation']['危险性']['问题'],
                '建议': '放宽标准工时或增加辅助工装'
            })

        if action['deviation']['合理性']['问题'] == '动作幅度过大':
            # 动作设计不合理 → 不应要求工人达到此标准
            validation_result['合理性'] = '需调整'
            validation_result['调整建议'].append({
                '动作': action['action'],
                '原因': '动作幅度过大，超出人体工程合理范围',
                '建议': '优化工位布局后再定标准，或增加辅助器具'
            })

    # === 对比多名工人的动作一致性 ===
    consistency = calculate_action_consistency(multi_worker_data)
    if consistency < 0.7:  # 动作一致性低于70%
        validation_result['调整建议'].append({
            '问题': '不同工人动作差异大',
            '建议': '标准化动作培训或简化操作步骤'
        })

    return validation_result
```

### 5.5 改善方案推荐（新增核心）

```python
# 伪代码 - 改善方案推荐引擎
def generate_improvement_plan(bottlenecks, deviation_analysis, mtm_validation):
    """
    输入: 系统瓶颈、动作偏差、MTM验证结果
    输出: 可落地的改善方案列表
    
    核心改变：输出改善方案而非绩效排名
    """
    improvement_plan = {
        '紧急改善': [],    # 高危险、高影响
        '短期改善': [],    # 1周内可实施
        '长期改善': [],    # 需预算/设备采购
        '预期效果': {}
    }

    # === 1. 紧急改善：危险动作 ===
    for action in deviation_analysis:
        if action['deviation']['危险性']['严重度'] == 'HIGH':
            improvement_plan['紧急改善'].append({
                '问题': action['deviation']['危险性']['问题'],
                '改善': action['deviation']['危险性']['改善'],
                '预期效果': '预防工伤，降低事故率'
            })

    # === 2. 短期改善：布局/物料 ===
    for bottleneck in bottlenecks:
        if bottleneck['类型'] in ['物料瓶颈', '布局瓶颈']:
            improvement_plan['短期改善'].append({
                '位置': bottleneck['位置'],
                '问题': bottleneck['原因'],
                '改善': bottleneck['改善'][0],  # 最直接方案
                '预期效果': f'预计提升效率{calculate_improvement(bottleneck)}%'
            })

    # === 3. 长期改善：设备/自动化 ===
    for bottleneck in bottlenecks:
        if bottleneck['类型'] == '设备瓶颈':
            improvement_plan['长期改善'].append({
                '位置': bottleneck['位置'],
                '问题': bottleneck['原因'],
                '改善': '设备升级或自动化改造',
                '预算': '待评估'
            })

    # === 4. MTM标准调整建议 ===
    if mtm_validation['合理性'] == '需调整':
        improvement_plan['短期改善'].append({
            '问题': '部分动作标准工时不合理',
            '改善': mtm_validation['调整建议'],
            '预期效果': '标准更人性化，减少工人压力'
        })

    # === 5. 预期效果汇总 ===
    improvement_plan['预期效果'] = {
        '效率提升': calculate_total_efficiency_improvement(improvement_plan),
        '工伤风险降低': calculate_safety_improvement(improvement_plan),
        '培训周期缩短': calculate_training_improvement(improvement_plan),
        '工人满意度提升': '预期提升（减少不合理动作要求）'
    }

    return improvement_plan
```

---

## 六、项目文件结构

```
工业IE智能体/
│
├── README.md                     # 项目说明
├── requirements.txt              # Python依赖
├── setup.py                      # 安装配置
│
├── config/                       # 配置文件
│   ├── default.yaml              # 默认配置
│   ├── mtm_tables.yaml           # MTM时间标准表 ★核心
│   └── action_rules.yaml         # 动作识别规则
│
├── src/                          # 源代码
│   ├── core/                     # 核心模块
│   │   ├── video_processor.py    # 视频处理
│   │   ├── pose_estimator.py     # 姿态估计 ★核心
│   │   ├── action_recognizer.py  # 动作识别 ★核心
│   │   └── mtm_analyzer.py       # MTM分析 ★核心
│   │
│   ├── analysis/                 # 分析模块
│   │   ├── time_calculator.py    # 工时计算
│   │   ├── cycle_analyzer.py     # 节拍分析
│   │   └── efficiency_metrics.py # 效率指标
│   │
│   ├── report/                   # 报告模块
│   │   ├── generator.py          # 报告生成器
│   │   ├── templates/            # 报告模板
│   │   │   ├── report.html       # HTML模板
│   │   │   └── report.md         # Markdown模板
│   │   └── charts.py             # 图表生成
│   │
│   └── utils/                    # 工具函数
│       ├── visualization.py      # 可视化工具
│       ├── data_io.py            # 数据读写
│       └── logger.py             # 日志系统
│
├── app/                          # 应用入口
│   ├── streamlit_app.py          # Streamlit Web界面 ★推荐
│   └── cli_tool.py               # 命令行工具（可选）
│
├── data/                         # 数据目录
│   ├── videos/                   # 输入视频
│   ├── processed/                # 处理结果
│   └── exports/                  # 导出报告
│
├── tests/                        # 测试代码
│   ├── test_pose.py              # 姿态估计测试
│   ├── test_mtm.py               # MTM计算测试
│   └── test_integration.py       # 集成测试
│
├── notebooks/                    # 实验笔记本
│   ├── demo_pose_estimation.ipynb  # 姿态估计演示
│   └── demo_action_recognition.ipynb # 动作识别演示
│
└── docs/                         # 文档
    ├── mtm_guide.md              # MTM使用指南
    ├── user_manual.md            # 用户手册
    └── developer_guide.md        # 开发指南
```

---

## 七、MVP开发路线

### 7.1 第一阶段：视频与姿态估计 (2-3天)

**目标**：建立视频处理和姿态估计基础能力

**任务清单**：
1. 创建项目结构和环境配置
2. 实现视频加载模块（OpenCV）
3. 集成MediaPipe姿态估计
4. 实现关键点可视化（骨架绘制）
5. 开发Streamlit基础界面（视频上传、播放、关键点显示）

**验收标准**：
- 能上传视频并逐帧显示
- 能实时显示人体骨架关键点
- 关键点检测成功率 > 90%

### 7.2 第二阶段：动作识别与MTM (2-3天)

**目标**：实现基础动作识别和MTM时间计算

**任务清单**：
1. 编写MTM时间标准表（YAML配置）
2. 实现关键点位移速度计算
3. 开发动作边界检测算法
4. 实现基础动作分类规则（R、G、M、RL）
5. 集成MTM时间计算引擎

**验收标准**：
- 能检测动作边界（起止时间）
- 能识别4种基础动作
- MTM时间计算准确

### 7.3 第三阶段：报告生成 (1-2天)

**目标**：自动生成分析报告

**任务清单**：
1. 设计报告模板结构
2. 实现MTM分析结果可视化（甘特图、时间饼图）
3. 开发报告生成器（Markdown/HTML输出）
4. 集成到Streamlit界面

**验收标准**：
- 能生成包含动作序列、工时、图表的报告
- 报告格式清晰可读

---

## 八、推荐产品形式

### 8.1 Streamlit Web应用（推荐）

**优势**：
- 30行代码即可搭建交互界面
- 无需前端开发经验
- 支持视频上传、实时预览
- 可直接部署到云端分享

**界面功能**：
```
1. 视频上传区
2. 实时预览（带骨架可视化）
3. 分析参数设置（距离阈值、宽放率等）
4. 分析结果展示
   - 动作时间轴
   - MTM动作序列表
   - 工时统计图
5. 报告下载按钮
```

### 8.2 API服务（后续扩展）

如果需要集成到其他系统（MES、ERP），可开发FastAPI服务：
- `/upload` - 上传视频
- `/analyze` - 执行分析
- `/report` - 获取报告

---

## 九、开发所需资源

### 9.1 硬件需求

| 阶段 | 硬件要求 | 说明 |
|------|----------|------|
| MVP开发 | 普通PC | MediaPipe可CPU实时运行 |
| 模型训练 | GPU服务器 | 如需训练LSTM，建议NVIDIA GPU |
| 生产部署 | 云服务器 | 4核8G起步，可选GPU加速 |

### 9.2 数据需求

| 数据类型 | 来源 | 数量 |
|----------|------|------|
| 测试视频 | 工厂产线录制 | 10-20个作业视频 |
| MTM标准表 | IE工程师提供 | 完整MTM-1数据卡 |
| 动作标注 | 人工标注 | 50-100个动作样本 |

### 9.3 人员需求

| 角色 | 投入 | 职责 |
|------|------|------|
| 开发者（用户） | 全程 | 使用AI辅助编程实现 |
| IE工程师 | 咨询 | 提供MTM知识、验证分析结果 |
| 测试人员 | 验收 | 测试系统准确性 |

---

## 十、验证测试方案

### 10.1 功能测试

| 模块 | 测试项 | 通过标准 |
|------|--------|----------|
| 视频处理 | 视频加载、帧提取 | 成功率 > 95% |
| 姿态估计 | 关键点检测、追踪 | 检测率 > 90% |
| 动作识别 | 边界检测、分类 | F1分数 > 0.7 |
| MTM计算 | 时间值查询、汇总 | 与人工计算误差 < 20% |
| 报告生成 | 模板渲染、导出 | 格式正确、内容完整 |

### 10.2 业务验证

```
验证流程：
1. 选取5个标准作业视频
2. IE工程师人工分析（建立基准）
3. 系统自动分析
4. 对比结果：
   - 动作识别准确率
   - 工时计算误差
   - 分析时间对比
5. 验收标准：
   - 工时误差 < 30%
   - 分析效率提升 > 5倍
```

---

## 十一、风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| 动作识别准确率低 | 工时偏差大 | 引入人工校验环节，规则优化 |
| MTM映射复杂 | 开发周期延长 | 先支持核心动作，渐进扩展 |
| 视频环境多样 | 模型泛化差 | 数据增强，场景参数调优 |
| 实时性能不足 | 用户体验差 | 关键帧采样，模型量化 |

---

## 十二、后续迭代路线

### 短期优化 (1-2周)

1. 增加5种动作识别（T、P、D、AP、SE）
2. 引入LSTM学习模型替代规则引擎
3. 优化关键点追踪算法
4. 增加多工位节拍分析

### 中期扩展 (1-2月)

1. 支持多人姿态估计
2. 集成GPU加速推理
3. 开发API服务接口
4. 建立训练数据标注平台

### 长期演进 (3-6月)

1. 对接MES/ERP系统
2. 实时视频流分析
3. 数字孪生产线仿真
4. 自适应MTM参数学习

---

## 十三、立即可用的学习资源

### 13.1 关键技能调用

使用Claude Code时可调用以下技能辅助开发：

| 技能 | 用途 | 调用方式 |
|------|------|----------|
| `/brainstorming` | 需求澄清与设计探索 | Phase 1 |
| `/writing-plans` | 编写详细实现计划 | 编码前 |
| `/python-patterns` | Python最佳实践指导 | 编码时 |
| `/tdd-guide` | 测试驱动开发 | 新功能时 |
| `/code-reviewer` | 代码审查 | 编码后 |
| `/systematic-debugging` | 调试流程 | 出错时 |

### 13.2 外部学习资源

- **MediaPipe教程**: https://mediapipe.readthedocs.io/
- **OpenCV教程**: https://docs.opencv.org/
- **MTM官方**: https://mtm.org/
- **Streamlit教程**: https://docs.streamlit.io/

---

## 十四、总结

### 方案核心要点

1. **技术选型**: MediaPipe + OpenCV + 规则引擎 + Streamlit
2. **核心模块**: 视频处理 → 姿态估计 → 动作识别 → MTM分析 → 报告生成
3. **MVP周期**: 5-7天完成基础功能原型
4. **产品形式**: Streamlit Web应用（最简单有效）
5. **开发模式**: AI辅助编程 + IE工程师咨询

### 推荐下一步

1. **立即可做**: 安装Python环境，测试MediaPipe姿态估计Demo
2. **本周准备**: 收集2-3个测试视频，获取MTM时间标准表
3. **下周启动**: 使用 `/blueprint` 或 `/writing-plans` 技能开始详细规划
4. **开发阶段**: 按MVP阶段逐步实现，每阶段使用 `/tdd-guide` 和 `/code-reviewer`

---

*本方案基于用户需求定制，可根据实际情况调整技术选型和开发节奏。*

---

## 附录A：改善导向核心模块设计

### A.1 改善报告生成器

```python
# 伪代码 - 改善报告生成器
def generate_improvement_report(improvement_plan, analysis_data):
    """
    输入: 改善方案、分析数据
    输出: 改善报告（而非绩效排名报告）
    
    核心改变：报告标题、内容、指向都改为改善导向
    """
    report = {
        '标题': '产线改善机会分析报告',
        '摘要': f'本次分析发现{len(improvement_plan["紧急改善"])}个紧急改善点，'
                f'{len(improvement_plan["短期改善"])}个短期改善机会，'
                f'预计可提升效率{improvement_plan["预期效果"]["效率提升"]}%',
        '章节': []
    }

    # === 第1章：安全改善优先 ===
    report['章节'].append({
        '标题': '一、安全改善建议（紧急优先）',
        '内容': [
            {
                '问题': item['问题'],
                '位置': item.get('位置', '全产线'),
                '改善': item['改善'],
                '预期效果': item['预期效果']
            }
            for item in improvement_plan['紧急改善']
        ]
    })

    # === 第2章：效率改善机会 ===
    report['章节'].append({
        '标题': '二、效率改善机会',
        '内容': [
            {
                '位置': item['位置'],
                '瓶颈类型': item.get('类型', '布局'),
                '改善方案': item['改善'],
                '预期效果': item['预期效果']
            }
            for item in improvement_plan['短期改善']
        ]
    })

    # === 第3章：标准工时合理性评估 ===
    report['章节'].append({
        '标题': '三、标准工时合理性评估',
        '内容': [
            {
                '评估结论': mtm_validation['合理性'],
                '调整建议': mtm_validation['调整建议'],
                '说明': '以下动作标准工时可能需要调整，以符合人体工程实际'
            }
        ]
    })

    # === 第4章：改善实施建议 ===
    report['章节'].append({
        '标题': '四、改善实施建议',
        '内容': {
            '优先级排序': [
                '1. 紧急改善：涉及安全的立即实施',
                '2. 短期改善：布局/物料调整，1周内实施',
                '3. 长期改善：设备/自动化，纳入预算规划'
            ],
            '责任分工': {
                'IE工程师': '改善方案详细设计',
                '产线主管': '改善实施协调',
                '设备部门': '设备/工装改造'
            }
        }
    })

    # === 第5章：预期改善效果 ===
    report['章节'].append({
        '标题': '五、预期改善效果',
        '内容': improvement_plan['预期效果']
    })

    return report
```

### A.2 新人教练模块（可选扩展）

```python
# 伪代码 - 新人动作教练
def action_coaching_for_newbie(real_time_keypoints, standard_action_profile):
    """
    输入: 实时关键点、标准动作模板
    输出: 动作指导、危险预警
    
    用途：新人培训，而非违规抓罚
    """
    coaching = {
        '动作正确性': None,
        '危险预警': None,
        '改进建议': None
    }

    # === 1. 动作正确性对比 ===
    deviation_from_standard = calculate_deviation(real_time_keypoints, standard_action_profile)
    if deviation_from_standard > threshold:
        coaching['动作正确性'] = {
            '偏差': f'与标准动作偏差{deviation_from_standard}%',
            '建议': '建议按标准动作路径操作，可参考培训视频'
        }

    # === 2. 危险动作实时预警 ===
    dangerous_posture = detect_dangerous_posture_realtime(real_time_keypoints)
    if dangerous_posture:
        coaching['危险预警'] = {
            '预警': f'检测到危险姿势：{dangerous_posture}',
            '建议': '请立即调整姿势，避免关节损伤',
            '提示': '如持续出现，建议增加工装辅助或调整工位高度'
        }

    # === 3. 疲劳动作提醒 ===
    fatigue_indicators = detect_fatigue(real_time_keypoints)
    if fatigue_indicators:
        coaching['改进建议'] = {
            '提醒': '检测到疲劳动作特征',
            '建议': '建议短暂休息或轮换操作'
        }

    return coaching

# 新人教练的核心理念
COACHING_PHILOSOPHY = """
动作教练的目标：
1. 帮助新人快速掌握正确动作（降低培训周期）
2. 预防工伤（识别危险姿势并实时预警）
3. 保护工人健康（识别疲劳并建议休息）

不用于：
- 抓罚违规工人
- 绩效考核扣分
- 管理层监控个人
"""
```

---

## 附录B：改善导向项目文件结构

```
工业IE智能体（改善导向版）/
│
├── README.md                     # 项目说明
├── requirements.txt              # Python依赖
├── setup.py                      # 安装配置
│
├── config/                       # 配置文件
│   ├── default.yaml              # 默认配置
│   ├── mtm_tables.yaml           # MTM时间标准表
│   ├── deviation_thresholds.yaml # 偏差判定阈值 ★新增
│   ├── safety_rules.yaml         # 安全动作规则 ★新增
│   └── improvement_templates.yaml# 改善方案模板 ★新增
│
├── src/                          # 源代码
│   ├── core/                     # 核心模块
│   │   ├── video_processor.py    # 视频处理
│   │   ├── pose_estimator.py     # 姿态估计
│   │   ├── action_recognizer.py  # 动作识别
│   │   ├── deviation_analyzer.py # 动作偏差分析 ★新增核心
│   │   ├── bottleneck_detector.py# 系统瓶颈识别 ★新增核心
│   │   ├── mtm_validator.py      # MTM合理性验证 ★新增核心
│   │   └── mtm_analyzer.py       # MTM分析
│   │
│   ├── improvement/              # 改善模块 ★新增目录
│   │   ├── plan_generator.py     # 改善方案生成器 ★核心
│   │   ├── recommendation_engine.py# 改善推荐引擎
│   │   └── effect_predictor.py   # 改善效果预测
│   │
│   ├── coaching/                 # 新人教练模块 ★新增目录
│   │   ├── action_coach.py       # 动作教练
│   │   ├── safety_monitor.py     # 安全预警
│   │   └── training_tracker.py   # 培训进度追踪
│   │
│   ├── report/                   # 报告模块
│   │   ├── generator.py          # 报告生成器
│   │   ├── templates/            # 报告模板
│   │   │   ├── improvement_report.html # 改善报告模板 ★核心
│   │   │   ├── coaching_report.html    # 教练报告模板 ★新增
│   │   │   └── safety_report.html      # 安全报告模板 ★新增
│   │   └── charts.py             # 图表生成
│   │
│   └── utils/                    # 工具函数
│       ├── visualization.py      # 可视化工具
│       ├── safety_metrics.py     # 安全指标计算 ★新增
│       └── data_io.py            # 数据读写
│
├── app/                          # 应用入口
│   ├── streamlit_app.py          # Streamlit Web界面
│   ├── coaching_app.py           # 新人教练界面 ★新增
│   └── cli_tool.py               # 命令行工具
│
├── data/                         # 数据目录
│   ├── videos/                   # 输入视频
│   ├── standard_profiles/        # 标准动作模板 ★新增
│   ├── processed/                # 处理结果
│   └── exports/                  # 导出报告
│
├── tests/                        # 测试代码
│   ├── test_deviation.py         # 偏差分析测试 ★新增
│   ├── test_bottleneck.py        # 瓶颈识别测试 ★新增
│   ├── test_improvement.py       # 改善方案测试 ★新增
│   └── test_coaching.py          # 教练模块测试 ★新增
│
└── docs/                         # 文档
    ├── design_philosophy.md      # 设计理念说明 ★新增核心
    ├── safety_guide.md           # 安全分析指南 ★新增
    ├── improvement_manual.md     # 改善方案手册 ★新增
    ├── coaching_guide.md         # 新人教练指南 ★新增
    ├── mtm_guide.md              # MTM使用指南
    └── user_manual.md            # 用户手册
```

---

## 附录C：设计理念核心文档

### 设计理念宣言

```
工业IE智能体的核心设计理念：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【传统工业工程数字化的问题】

数据流向：工人动作 → 效率数字 → 绩效排名 → 扣钱/施压
分析对象：单个工人的效率
核心问题："这个人够不够快？"
最终用途：管理层用来考核工人

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【本产品的核心理念】

数据流向：工人动作 → 动作偏差分析 → 系统瓶颈识别 → 改善方案
分析对象：产线系统（设备、物料、布局、工装）
核心问题："这个动作设计得合不合理？有没有危险？新手容不容易出错？"
最终用途：保护工人、改善产线、降低培训成本

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【三点产品定位】

1. IE工程师的AI助手（而非车间电子眼）
   - 替代重复性工作（看录像、掐表、填Excel）
   - 让IE工程师从录像带看守变成产线改善设计者

2. 系统级瓶颈分析（而非个人绩效排名）
   - 问题归因于系统：设备、物料、布局、工装
   - 输出改善方案而非考核分数

3. 新人培训教练（而非违规警察）
   - 识别危险动作预警，预防工伤
   - 保护工人健康，降低培训周期

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【对三类用户的价值】

对IE工程师：
  AI处理80%重复性工作，专注20%高价值决策

对管理层：
  不看"谁慢"，看"哪里卡"
  改善方案可落地（如"料箱左移20cm"）

对工人：
  工作更安全、更轻松、培训更容易
  不再担心被监控扣钱

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 附录D：改善导向验证方案

### D.1 功能测试重点转移

| 测试维度 | 传统方案测试重点 | 本产品测试重点 |
|----------|------------------|----------------|
| **动作识别** | 识别准确率、工时计算误差 | 偏差检测准确率、危险识别率 |
| **MTM分析** | 时间值计算准确性 | 标准合理性评估准确性 |
| **报告生成** | 格式正确、数据完整 | 改善建议可落地性、预期效果合理性 |
| **整体流程** | 分析效率提升倍数 | 改善方案实施效果、安全预警有效性 |

### D.2 业务验证流程更新

```
改善导向验证流程：

1. 选取3-5个存在明显改善机会的作业视频
   - 包含危险动作案例
   - 包含布局不合理案例
   - 包含节拍不平衡案例

2. IE工程师人工分析
   - 识别改善机会（而非计算工时）
   - 提出改善方案

3. 系统自动分析
   - 识别相同的改善机会
   - 提出改善方案

4. 对比结果：
   - 改善机会识别准确率 > 80%
   - 改善方案可落地性评分 > 7分（10分制）
   - 危险动作预警准确率 > 90%

5. 实施验证：
   - 按系统建议改善
   - 实际效率提升 vs 预期效率提升
   - 工伤事故降低率
```

---

## 最终总结

### 本方案的核心改变

| 维度 | 传统工业工程数字化 | 本产品方案 |
|------|-------------------|------------|
| **核心理念** | 考核个人效率 | 改善产线系统 |
| **分析对象** | 单个工人 | 设备、物料、布局、工装 |
| **核心问题** | "这个人够不够快？" | "这个动作设计得合不合理？" |
| **MTM用途** | 算差距、考核慢的人 | 验证标准合理性 |
| **输出报告** | 绩效排名报告 | 改善方案报告 |
| **对工人影响** | 可能扣钱、压力大 | 更安全、更轻松、培训更容易 |
| **产品定位** | 车间电子眼 | IE工程师助手 + 新人教练 |

### 技术架构核心新增

1. **动作偏差分析模块** - 分析合理性、危险性、易错性、疲劳度
2. **系统瓶颈识别模块** - 归因于系统而非个人
3. **MTM合理性验证模块** - 验证标准而非算差距
4. **改善方案推荐引擎** - 输出可落地的改善建议
5. **新人教练模块**（可选） - 动作指导、危险预警、培训追踪

### 推荐下一步行动

1. **理念确认**：与需求方确认改善导向的产品定位
2. **技术原型**：先实现姿态估计 + 基础动作偏差检测
3. **业务验证**：用真实产线视频验证改善方案有效性
4. **产品迭代**：根据IE工程师反馈持续优化

---

*方案版本：改善导向版 v2.0*

---

## 立即行动表格

### 你现在要做什么

| 序号 | 时间节点 | 行动内容 | 调用命令/工具 | 输出物 |
|------|----------|----------|---------------|--------|
| **1** | 立即 | 安装Python环境和依赖 | `pip install opencv-python mediapipe streamlit` | 开发环境就绪 |
| **2** | 立即 | 测试MediaPipe姿态估计Demo | 运行 `python demo_pose.py` | 验证技术可行性 |
| **3** | 本周 | 收集2-3个测试视频 | 向需求方获取产线作业视频 | 测试数据 |
| **4** | 本周 | 获取MTM时间标准表 | 向IE工程师获取完整MTM-1数据卡 | MTM配置文件 |
| **5** | 本周 | 与需求方确认产品定位 | 讨论改善导向理念是否认可 | 产品定位文档 |
| **6** | 下周 | 开始第一阶段开发 | `/writing-plans` 编写详细实现计划 | 阶段一计划 |
| **7** | 开发中 | 视频处理模块开发 | `/python-patterns` + `/tdd-guide` | video_processor.py |
| **8** | 开发中 | 姿态估计模块开发 | `/tdd-guide` 先写测试再实现 | pose_estimator.py |
| **9** | 开发中 | 动作偏差分析模块 | `/code-reviewer` 代码审查 | deviation_analyzer.py |
| **10** | 每阶段 | 代码质量检查 | `/code-reviewer` + `/security-reviewer` | 通过的代码 |
| **11** | 完成后 | 功能验证测试 | 用测试视频验证改善方案有效性 | 验收报告 |
| **12** | 完成后 | 与IE工程师复核 | 人工对比改善建议准确性 | 业务验收 |

### 关键决策点

| 决策点 | 决策内容 | 决策时机 | 决策依据 |
|--------|----------|----------|----------|
| **技术选型** | MediaPipe vs AlphaPose | 开始前 | 硬件条件、精度需求 |
| **产品定位** | 改善导向 vs 考核导向 | 开始前 | 与需求方确认理念 |
| **功能范围** | MVP vs 完整功能 | 开始前 | 时间预算、资源 |
| **交付形式** | Streamlit vs API | 阶段一完成 | 用户使用场景 |

### 可用技能清单

| 技能 | 用途 | 何时调用 |
|------|------|----------|
| `/brainstorming` | 需求澄清与设计探索 | 开始前 |
| `/writing-plans` | 编写详细实现计划 | 编码前 |
| `/python-patterns` | Python最佳实践指导 | 编码时 |
| `/tdd-guide` | 测试驱动开发 | 新功能开发时 |
| `/code-reviewer` | 代码审查 | 编码完成后 |
| `/systematic-debugging` | 系统调试流程 | 出错时 |
| `/security-reviewer` | 安全漏洞检查 | 涉及敏感数据时 |

### 里程碑验收标准

| 里程碑 | 时间 | 验收标准 |
|--------|------|----------|
| **环境就绪** | Day 1 | Python环境可用，MediaPipe Demo运行成功 |
| **数据准备** | Day 3 | 有测试视频、MTM标准表、产品定位确认 |
| **阶段一完成** | Week 1 | 视频上传、姿态估计可视化正常工作 |
| **阶段二完成** | Week 2 | 基础动作识别、偏差检测、MTM计算正常 |
| **阶段三完成** | Week 3 | 改善报告自动生成，格式完整 |
| **MVP交付** | Week 4 | 端到端流程可用，改善建议可落地 |

---

## 项目目录结构（当前状态）

```
工业IE智能体/
│
├── docs/
│   └── 工业IE智能体开发方案.md   ← 本文档
│
├── (待创建其他目录和文件)
│
```

**下一步**：运行 `/init` 或 `/project-init` 创建完整项目结构