/**
 * 工业IE智能体开发方案 - 精简版Word文档生成
 * 内容：核心方案、产品价值、功能概述、技术原理（适度深度）
 */

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, PageNumber, AlignmentType, HeadingLevel, BorderStyle,
        WidthType, VerticalAlign, PageBreak, LevelFormat, LineRuleType } = require('docx');
const fs = require('fs');

// === 页面配置 ===
const PAGE = { width: 11906, height: 16838 }; // A4
const MARGIN = { top: 1441, bottom: 1441, left: 1085, right: 1085 }; // 2.54cm / 1.91cm
const SIZE = { title: 36, h1: 32, h2: 28, h3: 24, body: 24, small: 21 };
const SPACING = { line: 360, h1Before: 480, h1After: 240, h2Before: 360, h2After: 120, h3Before: 240, h3After: 120, bodyAfter: 120 };

// === 辅助函数 ===
function createH1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: SPACING.h1Before, after: SPACING.h1After, line: SPACING.line, lineRule: LineRuleType.AUTO },
    children: [new TextRun({ text, font: { ascii: 'Times New Roman', eastAsia: '黑体' }, size: SIZE.h1, bold: true })],
  });
}

function createH2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: SPACING.h2Before, after: SPACING.h2After, line: SPACING.line, lineRule: LineRuleType.AUTO },
    children: [new TextRun({ text, font: { ascii: 'Times New Roman', eastAsia: '黑体' }, size: SIZE.h2, bold: true })],
  });
}

function createH3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: SPACING.h3Before, after: SPACING.h3After, line: SPACING.line, lineRule: LineRuleType.AUTO },
    children: [new TextRun({ text, font: { ascii: 'Times New Roman', eastAsia: '黑体' }, size: SIZE.h3, bold: true })],
  });
}

function createBody(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: SPACING.line, lineRule: LineRuleType.AUTO, after: SPACING.bodyAfter },
    indent: { firstLine: 480 },
    children: [new TextRun({ text, font: { ascii: 'Times New Roman', eastAsia: '宋体' }, size: SIZE.body })],
  });
}

function createBodyNoIndent(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: SPACING.line, lineRule: LineRuleType.AUTO, after: SPACING.bodyAfter },
    children: [new TextRun({ text, font: { ascii: 'Times New Roman', eastAsia: '宋体' }, size: SIZE.body })],
  });
}

// === 三线表 ===
function createThreeLineTable(data) {
  const THICK = { style: BorderStyle.SINGLE, size: 12, color: '000000' };
  const THIN = { style: BorderStyle.SINGLE, size: 6, color: '000000' };
  const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };

  // 动态列宽
  const cols = Math.max(...data.map(r => r.length));
  const minW = 800;
  const lens = [];
  for (let j = 0; j < cols; j++) {
    let max = 0;
    for (let r of data) {
      let len = 0;
      for (let c of (r[j] || '')) len += c.charCodeAt(0) > 127 ? 2 : 1;
      max = Math.max(max, len);
    }
    lens.push(max);
  }
  const totalLen = lens.reduce((a, b) => a + b, 0);
  const totalW = 9070;
  const widths = lens.map(l => Math.max(minW, Math.floor((l / totalLen) * (totalW - cols * minW)) + minW));

  const rows = data.map((row, i) => {
    const isHeader = i === 0;
    const isLast = i === data.length - 1;
    const cells = row.map((t, j) => new TableCell({
      width: { size: widths[j], type: WidthType.DXA },
      borders: { top: isHeader ? THICK : NONE, bottom: isHeader ? THIN : (isLast ? THICK : NONE), left: NONE, right: NONE },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: t, size: SIZE.small, bold: isHeader, font: { ascii: 'Times New Roman', eastAsia: '宋体' } })],
      })],
    }));
    return new TableRow({ children: cells });
  });

  return new Table({ width: { size: totalW, type: WidthType.DXA }, rows, alignment: AlignmentType.CENTER });
}

// === 主文档构建 ===
async function generateDocument() {
  const children = [];

  // 封面标题
  children.push(createH1('工业IE智能体系统'));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 240, after: 480 },
    children: [new TextRun({ text: '产品方案概述', font: { ascii: 'Times New Roman', eastAsia: '黑体' }, size: SIZE.h2 })],
  }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text: '版本：V3.0 | 日期：2025年5月', font: { ascii: 'Times New Roman', eastAsia: '宋体' }, size: SIZE.body })],
  }));
  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第一章：项目背景与价值
  children.push(createH1('一、项目背景与价值主张'));

  children.push(createH2('1.1 传统痛点'));
  children.push(createBody('工业工程（IE）分析是制造业效率提升的核心方法，但传统方式面临四大痛点：'));

  children.push(createThreeLineTable([
    ['痛点', '具体问题', '影响'],
    ['依赖专家', 'MTM分析需IE工程师逐帧看录像、手工拆解动作', '分析周期长、人力成本高'],
    ['效率低下', '人工掐表、填Excel、生成报告', '1个视频分析需2-4小时'],
    ['难以复制', '分析能力依赖个人经验，无法标准化', '新手培训周期长'],
    ['无法规模化', '传统方式无法批量分析多条产线', '改善进度受限'],
  ]));

  children.push(createH2('1.2 产品价值'));
  children.push(createBody('本产品通过AI技术自动完成动作识别与工时分析，为工厂带来以下价值：'));

  children.push(createThreeLineTable([
    ['价值维度', '传统方式', '本产品', '价值量化'],
    ['分析效率', '2-4小时/视频', '5-10分钟/视频', '效率提升10-20倍'],
    ['人力成本', '需IE专家全程', '专家只需复核决策', '节省80%人工时间'],
    ['分析标准化', '依赖个人经验', 'AI统一标准分析', '结果一致可复用'],
    ['规模化能力', '单条产线', '多工位、多产线并行', '覆盖全厂产线'],
  ]));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第二章：设计理念
  children.push(createH1('二、设计理念（差异化定位）'));

  children.push(createH2('2.1 三点核心定位'));
  children.push(createThreeLineTable([
    ['定位', '传统做法', '本产品做法'],
    ['IE工程师工具', '重复看录像、掐表、填Excel', 'AI自动完成分析，专家只做决策'],
    ['管理视角', '个人绩效排名', '产线级瓶颈分析（物料堆积？工位不平衡？）'],
    ['对工人', '抓违规、考核慢的人', '识别危险/疲劳动作，预防工伤'],
  ]));

  children.push(createH2('2.2 对三类用户的价值'));
  children.push(createThreeLineTable([
    ['用户', '传统方式痛点', '本产品价值'],
    ['IE工程师', '80%时间看录像、掐表、填表', 'AI处理80%重复工作，专注20%决策'],
    ['管理层', '只能看到"谁慢"，不知道"为什么慢"', '系统级问题归因，改善方案可落地'],
    ['工人', '担心被监控、被考核', '工作更安全、培训更容易'],
  ]));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第三章：系统功能概述
  children.push(createH1('三、系统功能概述'));

  children.push(createH2('3.1 核心功能模块'));
  children.push(createBodyNoIndent('系统采用分层架构，从视频输入到报告输出形成完整分析链条：'));
  children.push(createThreeLineTable([
    ['功能层', '主要模块', '说明'],
    ['输入层', '视频上传', '支持手机视频、工位监控视频、产线录像'],
    ['处理层', '姿态估计 + 动作识别', 'AI自动识别伸手、抓取、移动、等待等动作'],
    ['分析层', 'MTM工时计算', '自动映射标准工时，计算周期时间'],
    ['输出层', '分析报告', '动作时间轴图表、工时报告、改善建议'],
  ]));

  children.push(createH2('3.2 输入输出规格'));
  children.push(createThreeLineTable([
    ['规格', '具体要求'],
    ['输入格式', '手机视频（MP4）、工位监控视频（AVI）、产线录像（MOV）'],
    ['输出内容', '动作时间轴图表、MTM动作分类表、标准工时分析报告'],
    ['导出格式', 'CSV表格（数据明细）、PDF报告（完整报告）'],
  ]));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第四章：技术方案（扩充）
  children.push(createH1('四、技术方案'));

  children.push(createH2('4.1 技术架构概述'));
  children.push(createBody('系统采用"AI感知+规则引擎+知识库"三层架构，实现从视频到报告的自动化分析流程：'));

  children.push(createH3('4.1.1 三层架构'));
  children.push(createThreeLineTable([
    ['架构层', '技术选型', '核心功能'],
    ['感知层', 'MediaPipe Pose + OpenCV', '人体姿态检测、视频帧提取'],
    ['分析层', '自研规则引擎', '动作判定逻辑、时间统计'],
    ['知识层', 'MTM标准库', '动作工时赋值、计算公式'],
  ]));

  children.push(createH3('4.1.2 技术栈清单'));
  children.push(createThreeLineTable([
    ['技术层', '选型', '用途说明'],
    ['视频处理', 'OpenCV', '视频读取、帧提取、格式转换'],
    ['姿态估计', 'MediaPipe Pose', '人体33关键点检测（实时）'],
    ['动作识别', '自研规则引擎', '基于关键点位移判断动作类型'],
    ['工时计算', 'MTM知识库', '动作代码→标准工时映射'],
    ['数据导出', 'pandas', 'CSV表格生成'],
    ['报告生成', 'matplotlib + ReportLab', '时间轴图表+PDF报告'],
    ['交互界面', 'Streamlit', '快速Web界面'],
  ]));

  children.push(createH2('4.2 AI姿态估计原理'));
  children.push(createBody('系统使用MediaPipe Pose模型检测人体姿态，核心原理如下：'));

  children.push(createH3('4.2.1 关键点体系'));
  children.push(createBodyNoIndent('MediaPipe Pose检测人体33个关键点，覆盖全身主要部位：'));
  children.push(createThreeLineTable([
    ['部位', '关键点编号', '用途'],
    ['头部', '0-4（鼻、眼、耳）', '头部朝向判断'],
    ['上肢', '11-16（肩、肘、腕）', '手臂动作识别核心'],
    ['躯干', '5-10（肩、髋）', '身体朝向判断'],
    ['下肢', '23-32（膝、踝）', '站立/移动判断'],
  ]));

  children.push(createH3('4.2.2 检测流程'));
  children.push(createBodyNoIndent('姿态估计的处理流程为：'));
  children.push(createBodyNoIndent('步骤1：视频帧提取 → OpenCV逐帧读取视频，提取RGB图像'));
  children.push(createBodyNoIndent('步骤2：姿态检测 → MediaPipe模型识别人体，输出33关键点坐标'));
  children.push(createBodyNoIndent('步骤3：坐标归一化 → 将关键点坐标转换为0-1范围的相对位置'));
  children.push(createBodyNoIndent('步骤4：置信度筛选 → 过滤低置信度关键点（visibility < 0.5）'));

  children.push(createH2('4.3 动作识别逻辑'));
  children.push(createBody('系统采用规则引擎进行动作识别，基于关键点的位移、速度、姿态角度判断动作类型：'));

  children.push(createH3('4.3.1 识别原理'));
  children.push(createThreeLineTable([
    ['判定维度', '计算方法', '用途'],
    ['位移距离', '关键点帧间位移量', '判断移动幅度'],
    ['移动速度', '位移/时间间隔', '区分快速/慢速动作'],
    ['姿态角度', '关键点连线角度（腕-肘-肩）', '判断手臂伸展/弯曲'],
    ['持续时间', '动作起止时间差', '区分瞬时/持续动作'],
  ]));

  children.push(createH3('4.3.2 动作判定规则示例'));
  children.push(createThreeLineTable([
    ['动作', '触发条件', '终止条件'],
    ['Reach（伸手）', '手腕向外移动 + 速度>阈值 + 手臂伸展', '手腕速度骤降'],
    ['Grasp（抓取）', '手腕静止 + 手臂弯曲 + 前动作为Reach', '手腕开始新移动'],
    ['Move（移动）', '手腕稳定移动 + 携带姿态 + 前动作为Grasp', '手腕速度骤降'],
    ['Wait（等待）', '全身静止 + 持续>1秒', '检测到新Reach动作'],
  ]));

  children.push(createH2('4.4 MTM工时计算'));
  children.push(createBody('系统内置MTM-1标准动作知识库，自动将识别的动作映射为标准工时：'));

  children.push(createH3('4.4.1 MTM时间单位'));
  children.push(createBodyNoIndent('MTM使用TMU（Time Measurement Unit）作为标准时间单位：'));
  children.push(createThreeLineTable([
    ['换算关系', '数值'],
    ['1 TMU', '0.036秒'],
    ['100 TMU', '3.6秒'],
    ['1000 TMU', '36秒'],
    ['1分钟', '1667 TMU'],
  ]));

  children.push(createH3('4.4.2 动作工时赋值'));
  children.push(createThreeLineTable([
    ['动作代码', '动作名称', '标准工时（TMU）'],
    ['R-A（短）', '伸手<10cm', '8 TMU'],
    ['R-A（中）', '伸手10-25cm', '15 TMU'],
    ['R-A（长）', '伸手>25cm', '22 TMU'],
    ['G1', '简单抓取', '5 TMU'],
    ['M-A（短）', '移动<10cm', '10 TMU'],
    ['M-A（中）', '移动10-25cm', '18 TMU'],
    ['RL1', '简单放开', '2 TMU'],
  ]));

  children.push(createH2('4.5 技术优势'));
  children.push(createThreeLineTable([
    ['优势', '说明'],
    ['实时处理', 'MediaPipe Pose CPU实时运行，无需GPU'],
    ['轻量部署', 'Python实现，依赖少，易于本地运行'],
    ['规则透明', '动作判定规则可配置、可解释'],
    ['标准兼容', '工时计算严格遵循MTM-1标准'],
    ['扩展灵活', '预留YOLO物体检测、多工位接口'],
  ]));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第五章：产品优势总结
  children.push(createH1('五、产品优势总结'));

  children.push(createH2('5.1 与传统方式对比'));
  children.push(createThreeLineTable([
    ['对比维度', '传统MTM分析', '本产品'],
    ['分析方式', '人工逐帧看录像', 'AI自动识别'],
    ['分析时间', '2-4小时/视频', '5-10分钟/视频'],
    ['人员要求', '需IE专家全程参与', '专家只需复核'],
    ['结果一致性', '依赖个人经验', 'AI统一标准'],
    ['可扩展性', '单人单线', '批量多线并行'],
  ]));

  children.push(createH2('5.2 核心亮点'));
  children.push(createBodyNoIndent('• 规则完整：所有动作有具体判定规则与标准工时赋值'));
  children.push(createBodyNoIndent('• 公式明确：周期时间、效率损失公式可直接计算'));
  children.push(createBodyNoIndent('• 接口清晰：报告生成接口与数据结构定义明确'));
  children.push(createBodyNoIndent('• 扩展性强：支持多工位、多人员、YOLO物体检测扩展'));

  children.push(createH2('5.3 应用场景'));
  children.push(createBodyNoIndent('• 产线效率分析：快速识别瓶颈工位，指导产线平衡优化'));
  children.push(createBodyNoIndent('• 培训标准化：将专家动作分析能力数字化，新员工培训更高效'));
  children.push(createBodyNoIndent('• 安全预警：识别危险/疲劳动作，预防工伤事故'));
  children.push(createBodyNoIndent('• 远程分析：支持视频上传远程分析，无需现场驻点'));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第六章：比赛交付计划
  children.push(createH1('六、比赛交付计划（5天节奏）'));

  children.push(createH2('6.1 MVP保底交付（Day -3 ~ Day -1）'));
  children.push(createBody('提前3天开发，确保路演前有可演示的核心功能：'));
  children.push(createThreeLineTable([
    ['天数', '核心任务', '交付标志'],
    ['Day -3', '项目结构+视频处理+姿态估计', '能上传视频并显示骨架动画'],
    ['Day -2', '基础动作识别(R/G/M/RL)+CSV导出', '能检测4种动作并导出CSV'],
    ['Day -1', 'MTM工时计算+时间轴生成', '能生成工时报告和PNG图表'],
  ]));

  children.push(createH3('保底交付验收标准'));
  children.push(createBodyNoIndent('✅ 上传视频 → 界面显示骨架动画'));
  children.push(createBodyNoIndent('✅ 动作识别 → 检测R/G/M/RL四种动作'));
  children.push(createBodyNoIndent('✅ CSV导出 → 下载动作序列明细表'));
  children.push(createBodyNoIndent('✅ 时间轴 → 生成动作分布PNG图表'));

  children.push(createH2('6.2 现场扩展加分（Day 1 ~ Day 4）'));
  children.push(createBody('比赛现场4天扩展开发，增强产品完整度：'));
  children.push(createThreeLineTable([
    ['天数', '扩展任务', '加分效果'],
    ['Day 1', 'Wait识别 + PDF报告生成', '完善动作库，支持完整报告导出'],
    ['Day 2', '节拍统计公式 + 效率指标计算', '提供产线级分析数据'],
    ['Day 3', 'Assemble组合动作 + 多工位框架', '展示扩展架构能力'],
    ['Day 4', '改善建议引擎 + 界面优化', '提升用户体验和商业价值'],
  ]));

  children.push(createH2('6.3 路演演示（Day 5）'));
  children.push(createThreeLineTable([
    ['演示环节', '时长', '展示内容'],
    ['产品定位', '2分钟', '差异化理念、三类用户价值'],
    ['核心功能', '5分钟', '上传视频→分析→导出完整流程'],
    ['技术亮点', '3分钟', 'AI姿态估计、MTM知识库、规则引擎'],
    ['扩展能力', '3分钟', '多工位接口、YOLO预留、部署方案'],
    ['商业价值', '2分钟', '效率提升量化、成本节省、规模化能力'],
  ]));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第七章：预留扩展能力
  children.push(createH1('七、预留扩展能力'));

  children.push(createH2('7.1 多工位分析框架'));
  children.push(createBody('系统预留多工位分析接口，正式版可扩展为产线级分析：'));
  children.push(createThreeLineTable([
    ['扩展项', '当前状态', '正式版能力'],
    ['工位数量', '单工位分析', '支持5+工位并行分析'],
    ['线平衡率', '公式已定义', '自动计算产线平衡率'],
    ['瓶颈识别', '单工位工时输出', '自动识别瓶颈工位'],
    ['数据汇总', '单视频报告', '多工位统一汇总报告'],
  ]));

  children.push(createH2('7.2 多人员检测接口'));
  children.push(createBody('预留多人姿态检测接口，用于协作场景分析：'));
  children.push(createThreeLineTable([
    ['场景', '说明'],
    ['双人协作', '分析工人间配合动作，识别等待他人场景'],
    ['培训对比', '新老员工动作对比，量化培训效果'],
    ['安全预警', '多人同时作业危险动作识别'],
  ]));

  children.push(createH2('7.3 YOLO物体检测预留'));
  children.push(createBody('预留YOLO接口，用于增强场景理解：'));
  children.push(createThreeLineTable([
    ['检测对象', '业务价值'],
    ['工具识别', '判断工人使用什么工具'],
    ['零件检测', '追踪物料流转轨迹'],
    ['物料堆积', '识别物料堆积预警'],
    ['设备状态', '检测设备运行状态'],
  ]));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第八章：工业部署方案
  children.push(createH1('八、工业部署方案'));

  children.push(createH2('8.1 部署场景分类'));
  children.push(createBody('产品支持多种工业现场部署形态：'));
  children.push(createThreeLineTable([
    ['场景', '特点', '部署方案'],
    ['内网离线', '无外网、数据敏感', '本地安装，U盘传输视频'],
    ['工位嵌入式', '边缘设备部署', '轻量化版本，实时分析'],
    ['云端远程', '多工厂集中管理', 'FastAPI服务，远程调用'],
    ['RTSP实时流', '监控摄像头接入', '实时帧分析，不间断监测'],
  ]));

  children.push(createH2('8.2 MVP部署形态'));
  children.push(createBody('比赛演示阶段采用本地部署方案：'));
  children.push(createThreeLineTable([
    ['项目', '说明'],
    ['运行环境', 'Windows/Linux/Mac，Python 3.8+'],
    ['启动方式', '双击run_offline.bat，浏览器访问localhost:8501'],
    ['数据输入', '本地视频文件或U盘导入'],
    ['结果输出', '本地CSV/PDF文件'],
    ['网络需求', '无外网需求，模型已预下载'],
  ]));

  children.push(createH2('8.3 正式版部署架构'));
  children.push(createBodyNoIndent('正式版支持更完整的工业部署能力：'));
  children.push(createBodyNoIndent('• Docker容器化：标准化部署包，一键安装'));
  children.push(createBodyNoIndent('• FastAPI服务：提供REST API，支持远程调用'));
  children.push(createBodyNoIndent('• 数据库集成：分析结果持久化存储'));
  children.push(createBodyNoIndent('• 权限管理：多用户、多角色访问控制'));
  children.push(createBodyNoIndent('• RTSP接入：实时监控流分析，不间断监测'));

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // 第九章：部署后预期效果
  children.push(createH1('九、部署后预期效果'));

  children.push(createH2('9.1 效率提升量化'));
  children.push(createThreeLineTable([
    ['指标', '传统方式', '部署后', '提升幅度'],
    ['视频分析时间', '2-4小时/视频', '5-10分钟/视频', '10-20倍'],
    ['专家参与时间', '全程参与', '仅复核决策', '节省80%'],
    ['产线分析周期', '周级', '日级', '缩短7倍'],
    ['报告生成', '手工填写', '自动生成', '效率提升90%'],
  ]));

  children.push(createH2('9.2 业务价值实现'));
  children.push(createThreeLineTable([
    ['价值维度', '实现方式', '预期效果'],
    ['产能提升', '识别瓶颈工位，优化产线平衡', '产能提升10-15%'],
    ['培训效率', '动作标准化，数字化对比', '新员工上手时间缩短50%'],
    ['安全改善', '危险动作预警', '工伤事故降低30%'],
    ['成本节省', '减少IE专家重复劳动', '人力成本节省60%'],
  ]));

  children.push(createH2('9.3 规模化能力'));
  children.push(createBodyNoIndent('• 单工厂覆盖：支持全厂多条产线并行分析'));
  children.push(createBodyNoIndent('• 多工厂部署：云端服务集中管理，分布式采集'));
  children.push(createBodyNoIndent('• 持续改善：数据积累形成改善知识库，持续优化'));
  children.push(createBodyNoIndent('• 标准复制：分析结果标准化，易于跨工厂推广'));

  children.push(createH2('9.4 实施路径建议'));
  children.push(createThreeLineTable([
    ['阶段', '时间', '目标'],
    ['试点阶段', '1-2周', '单工位验证，建立信任'],
    ['扩展阶段', '1-2月', '覆盖关键产线，产出改善报告'],
    ['规模化', '3-6月', '全厂部署，形成标准化流程'],
    ['持续优化', '长期', '数据驱动，持续改善迭代'],
  ]));

  // 创建文档
  const doc = new Document({
    styles: {
      paragraphStyles: [
        { id: 'Normal', name: 'Normal',
          run: { font: { ascii: 'Times New Roman', eastAsia: '宋体' }, size: SIZE.body },
          paragraph: { spacing: { line: SPACING.line, lineRule: LineRuleType.AUTO } } },
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal',
          run: { font: { ascii: 'Times New Roman', eastAsia: '黑体' }, size: SIZE.h1, bold: true },
          paragraph: { spacing: { before: SPACING.h1Before, after: SPACING.h1After, line: SPACING.line }, outlineLevel: 0 } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal',
          run: { font: { ascii: 'Times New Roman', eastAsia: '黑体' }, size: SIZE.h2, bold: true },
          paragraph: { spacing: { before: SPACING.h2Before, after: SPACING.h2After, line: SPACING.line }, outlineLevel: 1 } },
      ]
    },
    sections: [{
      properties: {
        page: { size: PAGE, margin: MARGIN }
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: '工业IE智能体系统 - 开发方案', size: SIZE.small, font: { ascii: 'Times New Roman', eastAsia: '宋体' } })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: '— ', size: SIZE.small }),
              new TextRun({ children: [PageNumber.CURRENT], size: SIZE.small }),
              new TextRun({ text: ' —', size: SIZE.small }),
            ],
          })],
        }),
      },
      children: children,
    }],
  });

  // 保存文档
  const outputPath = 'e:/创业项目/工业IE智能体/docs/工业IE智能体开发方案.docx';
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`✓ 已生成: ${outputPath}`);
}

// 执行
generateDocument().catch(err => {
  console.error('生成失败:', err);
  process.exit(1);
});