# SnowFold GFP Design 2026

> 运用 ProteinMPNN + ESMFold 迭代设计 GFP 变体，从公开 PDB 结构出发，sort_score 从 0.80 提升至 **0.9477**。

## 项目简介

本项目参与 2026 合成生物 GFP 设计竞赛，目标是设计兼具高荧光亮度和优良热稳定性的 GFP 变体。核心管线采用 **ProteinMPNN** 进行序列生成/反向折叠，以 **ESMFold** 进行结构预测与质量评估（pTM / pLDDT / 生色团区域 pLDDT），通过多轮迭代筛选逐步优化排序分。

最终提交轮次（R25）的 Top-1 序列达到 sort_score = **0.9477**（pTM=0.9321, 全局 pLDDT=94.65, 生色团 pLDDT=96.96）。

## 完整设计链条（从零到 0.9477）

本项目从公开 PDB 结构出发，经历了以下完整流程：

```
种子结构（公开 PDB）
  │
  ├── sfGFP  (PDB: 2B3P)  — 竞赛基线
  ├── avGFP  (PDB: 2WUR)  — 历史 GFP 变体
  └── mBaoJin (PDB: 8QBJ)  — 高亮度 GFP
  │
  ▼
R2: 机器学习预测 (XGBoost + ESM2-650M 嵌入，从 Sarkisyan 2016 DMS 数据学习)
  → 从 51,715 条 avGFP 变体中筛选 Top 候选
  │
  ▼
R4: ProteinMPNN 多骨架反向折叠设计
  → 用 3 个 PDB 骨架 (2B3P/2WUR/8QBJ) 生成新序列
  → ESMFold r=4 筛选
  │
  ▼
R5-R14: 迭代 MPNN + ESMFold 优化
  → 每轮用上一轮 Top 候选作父代
  → 逐步提高 pTM / pLDDT / chromo pLDDT
  │
  ▼
R17: HuggingFace ESMFold r=8 校准 + pLDDT 修正
  → sort_score 0.908
  │
  ▼
R18: 4 父代 × 3 温度 MPNN
  → sort_score 0.924
  │
  ▼
R19: 9 父代 × 5 温度大规模搜索 (R18 Top 6 + 3 WT)
  → sort_score 0.9321
  │
  ▼  关键修复：fixed position 1 (M)
R20: 修复后通过率从 8% → 62.8%
  → sort_score 0.9396
  │
  ▼
R22: Phase 1+2 大规模 MPNN (5600 候选) + r=20 重算
  → sort_score 0.9430
  │
  ▼
R24: R22 Top 6 父代 + GeoEvoBuilder 启发的跨度温度
  → sort_score 0.9447
  │
  ▼
R25: R24 Top 6 父代 + 中低温精细优化 + r=20 重算
  → sort_score 0.9477  🏆
```

### 自主开发工具：gssh CLI

本项目全程使用了我们自主开发的 **gssh** 命令行工具——一个专为远程 GPU 服务器协作而设计的轻量 CLI，是本次实验高效迭代的核心基础设施。

#### 为什么需要 gssh

本项目在 Windows 本地工作站 + 远程 A800 80GB 服务器之间进行多轮迭代。每轮实验需要：上传脚本到服务器 → 启动长时间 GPU 任务 → 实时监控日志 → 下载结果 JSON/CSV 回本地分析。传统 SSH/SCP 操作繁琐且无法管理后台任务，gssh 将这些操作整合为简洁命令。

#### 核心功能

| 命令                                   | 功能                        | 典型用法                                          |
| :------------------------------------- | :-------------------------- | :------------------------------------------------ |
| `gssh run <session> "<cmd>"`         | 远程执行任务（自动后台化）  | `gssh run 9ca7acb1b94c "python3 r25_server.py"` |
| `gssh cp <src> <dst>`                | 双向文件传输                | `gssh cp D:\r25.py session:/root/r25.py`        |
| `gssh logs <task-id> -f`             | 实时查看任务日志            | `gssh logs fff98ed2cf3b -f`                     |
| `gssh task stop <task-id>`           | 停止远程任务                | `gssh task stop 15e464541126`                   |
| `gssh --json exec <session> "<cmd>"` | 一次性命令执行（JSON 输出） | `gssh --json exec 9ca7 "nvidia-smi"`            |

#### 在本项目中的关键应用

- **R20-R27 全部远程任务**：脚本上传、GPU 任务启动、实时进度监控、结果下载均通过 gssh 完成
- **链式自动接力**：R25 通过 gssh 启动的 watcher 脚本，在 R24 完成后自动检测 GPU 空闲并启动 R25，实现无人值守的跨轮次自动化
- **并行管理**：同时管理本地 RTX 5080 和远程 A800 两个计算节点，按需调度

---

### 仓库说明

本仓库为 **SnowFold 竞赛核心仓库**，经过整理后仅保留从 R17 到 R27 的标准化 pipeline 脚本、最终结果和分析工具。

由于本项目跨越 27 轮迭代实验，原始工作目录中包含数百个脚本文件（含早期 ML 预测、多版本调试、中间筛选步骤、MPNN FASTA 输出、PDB 结构等），即使按轮次分类后每轮的相关文件仍然繁多且结构不一，不便于评审快速定位核心逻辑。

因此，我们将**标准化后的核心 pipeline 脚本**和**最终结果**提取到本仓库中，确保评审可以在数分钟内理解完整设计流程并复现关键实验。

完整的原始工作记录（含 R1-R16 早期探索阶段的全部脚本、中间文件和数据）可在原始仓库中查阅：

- **原始仓库**: `2026Protein Design` 根目录（含 `work/round2` ~ `work/round16` 全部脚本和数据，共计 500+ 文件）

## 最终成绩

| 指标                         | 值               |
| :--------------------------- | :--------------- |
| **sort_score (Top-1)** | **0.9477** |
| pTM                          | 0.9321           |
| 全局 pLDDT                   | 94.65            |
| 生色团 pLDDT (残基 58-72)    | 96.96            |
| 提交轮次                     | R25              |
| 提交序列数                   | 6                |

### 排序分公式

```
sort_score = (pTM × 0.40) + (全局pLDDT / 100 × 0.30) + (生色团pLDDT / 100 × 0.30)
```

## 技术栈

- **语言**: Python 3.10+
- **深度学习**: PyTorch >= 2.0, CUDA 12+
- **序列生成**: ProteinMPNN (v_48_020)
- **结构预测**: ESMFold (facebook/esmfold_v1) via HuggingFace Transformers
- **数据分析**: NumPy, SciPy, Matplotlib

## 环境配置要求

| 项目     | 要求                          |
| :------- | :---------------------------- |
| Python   | 3.10+                         |
| CUDA     | 12.0+                         |
| GPU 显存 | 16GB+（ESMFold 推理最低要求） |
| 操作系统 | Linux（推荐）/ Windows        |
| 磁盘空间 | 10GB+（模型权重 + 中间结果）  |

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 安装 ProteinMPNN（需单独克隆）
git clone https://github.com/dauparas/ProteinMPNN.git
cd ProteinMPNN
pip install -e .
```

## 模型依赖

| 模型        | 版本/路径                             | 用途                       |
| :---------- | :------------------------------------ | :------------------------- |
| ESMFold     | `facebook/esmfold_v1` (HuggingFace) | 结构预测，输出 pTM / pLDDT |
| ProteinMPNN | `v_48_020` (权重文件)               | 序列生成 / 反向折叠        |

ESMFold 首次运行时会自动从 HuggingFace Hub 下载模型权重（约 2.5GB）。

## 推理代码运行方式

以下是从 R19 到 R25 的完整迭代流程。每轮的核心逻辑为：**加载上一轮 Top 序列 → ProteinMPNN 采样生成 → ESMFold 结构预测 → 计算排序分 → 保留 Top 候选作为下一轮父代**。

### Step 1: R19 — 基准轮

```bash
cd pipeline
python r19_pipeline.py
```

- 父代: R18 Top6
- 温度: 5 档
- 候选数: 200
- Fixed positions: [65, 66, 67, 96, 222]
- ESMFold recycles: 8
- 结果: sort_score = 0.9321

### Step 2: R20 — Fixed position 1 (M) 修复

```bash
python r20_pipeline.py    # 生成 + 初筛
python r20_finalize.py    # 终筛 + 导出
```

- 父代: R19 Top6
- 温度: 4 档
- 候选数: 2000
- Fixed positions: **[1, 65, 66, 67, 96, 222]**（新增 position 1 固定为 M）
- 结果: sort_score = 0.9396（+0.0075）

### Step 3: R22 — Phase 2 大规模 MPNN

```bash
python r22_pipeline.py    # 主管线
python r22_long.py        # 长时间批量任务
```

- 父代: R20 Top6
- 温度: 4 档
- 候选数: 5600
- ESMFold recycles: 8 + 20（高精度重算）
- 结果: sort_score = 0.9430（+0.0034）

### Step 4: R24 — 跨度温度探索

```bash
# 服务器端运行
python r24_server.py
```

- 父代: R22 Top6
- 温度: 5 档跨度
- 候选数: 6000
- 结果: sort_score = 0.9447（+0.0017）

### Step 5: R25 — 中低温精调（最终提交轮）

```bash
# 服务器端运行
python r25_server.py

# 可选: 监控脚本
bash r25_watcher.sh
```

- 父代: R24 Top6
- 温度: 5 档中低温 [0.05 - 0.3]
- 候选数: 6000
- ESMFold recycles: 8 + 20（高精度重算）
- 结果: **sort_score = 0.9477**（+0.0030）🏆

### 后续探索轮（未提交）

- **R26** (`r26_local.py`): 本地小规模验证，sort_score = 0.9449
- **R27** (`r27_server.py`, `r27_diverge.py`): 5 方向多样性探索，sort_score = 0.9480

### 分析工具

```bash
cd analysis
python check_compliance.py   # 格式合规性检查
python analyze_r22.py         # R22 结果分析
python analyze_r23.py         # R23 结果分析
python analyze_r26.py         # R26 结果分析
python r24_check.py           # R24 结果校验
```

## 目录结构

```
SnowFold-GFP-2026/
├── README.md                      # 本文件
├── requirements.txt               # Python 依赖
├── .gitignore
├── submission/
│   └── submission_r25.csv         # 最终提交的 6 条序列
├── pipeline/                      # 各轮生成管线脚本
│   ├── r19_pipeline.py
│   ├── r20_pipeline.py
│   ├── r20_finalize.py
│   ├── r22_long.py
│   ├── r22_pipeline.py
│   ├── r23_server.py
│   ├── r23_local.py
│   ├── r24_server.py
│   ├── r25_server.py
│   ├── r25_watcher.sh
│   ├── r26_local.py
│   ├── r27_server.py
│   ├── r27_diverge.py
│   ├── r28_local_mutscan.py
│   └── r28_watcher.ps1
├── analysis/                      # 分析与校验脚本
│   ├── check_compliance.py
│   ├── analyze_r22.py
│   ├── analyze_r23.py
│   ├── analyze_r26.py
│   └── r24_check.py
├── results/                       # 各轮 Top6 候选结果
│   ├── round19/
│   ├── round20/
│   ├── round22/
│   │   └── final_6_r22.json
│   ├── round23/
│   │   └── final_6_r23.json
│   ├── round24/
│   ├── round25/
│   │   └── final_6_r25.json
│   ├── round26/
│   │   └── final_6_r26.json
│   └── round27/
│       └── final_6_r27.json
└── docs/                          # 设计文档与报告
    ├── R22-R27_final_report.md
    ├── round24-27_report.md
    ├── round25_report.md
    └── r24_briefing.md
```

## 各轮实验条件汇总

|     轮次     | 父代               | 温度策略             |     候选数     | Fixed Positions               |    Recycles    | Top1 sort_score |
| :-----------: | :----------------- | :------------------- | :------------: | :---------------------------- | :------------: | :--------------: |
|      R19      | R18 Top6           | 5 档                 |      200      | [65,66,67,96,222]             |       8       |      0.9321      |
|      R20      | R19 Top6           | 4 档                 |      2000      | [1,65,66,67,96,222]           |       8       |      0.9396      |
|      R22      | R20 Top6           | 4 档                 |      5600      | [1,65,66,67,96,222]           |      8+20      |      0.9430      |
|      R23      | R20 Top3           | 5 档高温             |      2250      | [1,65,66,67,96,222]           |       8       |      0.9419      |
|      R24      | R22 Top6           | 5 档跨度             |      6000      | [1,65,66,67,96,222]           |       8       |      0.9447      |
| **R25** | **R24 Top6** | **5 档中低温** | **6000** | **[1,65,66,67,96,222]** | **8+20** | **0.9477** |
|      R26      | R24 Top2           | 3 档                 |      600      | [1,65,66,67,96,222]           |       8       |      0.9449      |
|      R27      | R25 Top2           | 5 方向               |      680      | 多种                          |       8       |      0.9480      |

### 关键发现

1. **Fixed position 1 (M)** 是最关键修复（R19→R20: +0.0075）
2. **父代质量决定上限** — 每轮用上一轮 Top 6 作父代
3. **中低温 [0.05-0.3]** 是最佳温度范围
4. **超高温 [1.0+] 完全无效**（通过率仅 1-2%）
5. **ESMFold r=8 已收敛**（r=20 差异 <0.001）
6. **MPNN+ESMFold 天花板约 0.95**（当前 0.948，剩余约 0.002）

## Agent 逻辑树说明

本项目使用 **Trae AI Agent** 辅助设计与迭代。Agent 的核心逻辑树如下：

```
[Trae AI Agent]
├── 1. 任务理解与规则解析
│   ├── 读取竞赛规则（序列长度 220-250aa, M 开头, 20 种标准氨基酸）
│   ├── 解析评估指标（pTM, pLDDT, 生色团 pLDDT, sort_score）
│   └── 加载 Exclusion_List 排除表
│
├── 2. 迭代设计循环
│   ├── 2a. 加载上一轮 Top 序列作为父代
│   ├── 2b. ProteinMPNN 序列生成
│   │   ├── 多温度采样（0.05, 0.1, 0.2, 0.5, 1.0）
│   │   ├── Fixed positions 固定关键残基
│   │   └── 批量生成候选序列
│   ├── 2c. ESMFold 结构预测
│   │   ├── 初筛: recycles=8
│   │   └── 高精度重算: recycles=20（Top20 候选）
│   ├── 2d. 排序分计算与筛选
│   │   ├── 计算 sort_score
│   │   ├── pTM 差异校验（防虚假高分）
│   │   └── 保留 Top 6 作为下一轮父代
│   └── 2e. 合规性检查
│       ├── 序列长度 / 格式验证
│       └── Exclusion_List 比对
│
├── 3. 分析与决策
│   ├── 轮次结果分析（温度分布, 突变热图, 得分分布）
│   ├── 策略调整（温度范围, Fixed positions, 候选规模）
│   └── 生成下一轮实验方案
│
└── 4. 最终提交
    ├── 选择 sort_score 最高的 6 条序列
    ├── 格式合规性终检
    └── 生成 submission CSV
```

### Agent 关键执行日志

以下是 Agent 在各轮实验中的关键决策节点和执行记录，展示了从问题发现到策略调整的完整推理链。

#### R17→R18: ESMFold 校准与基线建立

- **问题发现**: Agent 注意到本地 ESMFold 的 pLDDT 输出与 HuggingFace 官方实现存在 0-1 vs 0-100 的尺度差异，导致早期评分偏低
- **自动修复**: Agent 在代码中加入 `plddt.mean()` 标准化，统一到 0-1 比例
- **策略调整**: 将 recycles 从 4 提高到 8，发现 sort_score 稳定提升 +0.002

#### R18→R19: 大规模搜索空间探索

- **决策**: Agent 分析 R18 仅用 4 父代 × 3 温度 × 50 候选 = 900 候选，搜索空间不足
- **执行**: 扩展到 9 父代（R18 Top 6 + 3 个 WT 参考序列）× 5 温度 × 150 候选 = 6750 候选
- **结果**: sort_score 0.908 → 0.9321（+0.024），验证了"更大搜索空间 → 更高分数"假设

#### R19→R20: 关键 Bug 发现与修复（最大突破）

- **异常检测**: Agent 在 R19 结果分析中发现 97% 的候选序列**不以 M 开头**，违反竞赛规则
- **根因定位**: Agent 追踪到 ProteinMPNN 的 `fixed_positions` 参数缺少 position 1，MPNN 未固定起始甲硫氨酸
- **自动修复**: 将 `FIXED = [65, 66, 67, 96, 222]` 改为 `FIXED = [1, 65, 66, 67, 96, 222]`
- **效果**: 通过率从 ~8% 跃升至 62.8%，sort_score 0.9321 → 0.9396（**+0.0075，项目最大单轮提升**）
- **日志摘录**: `"97% 候选不以 M 开头 → 违反规则 → FIXED 缺 position 1 → 修复 → 通过率 8%→62.8%"`

#### R20→R22: Phase 1+2 流水线设计

- **策略推理**: Agent 分析 R20 Top 6 分布后发现分数集中在 0.939 附近，单轮 MPNN 难以突破
- **方案设计**: Agent 设计了双阶段流水线：
  - Phase 1: R20 finalize（2000 候选，确认父代质量）
  - Phase 2: 大规模 MPNN（3600 候选，6 父代 × 4 温度 × 150）
  - Phase 3: Top 20 用 r=20 高精度重算
- **验证**: r=8 vs r=20 差异全部 < 0.001，确认 r=8 结果可信
- **结果**: sort_score 0.9396 → 0.9430（+0.0034）

#### R22→R24: 跨轮父代链 + 文献调研

- **文献调研**: Agent 搜索到 GeoEvoBuilder（PNAS 2025.10），专门为 GFP 设计的 zero-shot 框架，同时优化活性和热稳定性
- **代码下载尝试**: GitHub 下载失败（网络限制），Agent 决定用现有工具模拟其核心思路
- **策略调整**: 用 R22 Top 6（0.9430）作父代 + 跨度温度 [0.05-0.8]（比 R22 更宽）
- **结果**: sort_score 0.9430 → 0.9447（+0.0017），pTM 0.9276 → 0.9305 创纪录

#### R24→R25: 中低温聚焦 + 自动接力（最终突破）

- **温度分析**: Agent 统计 R24 各温度段产出发现 T=0.05-0.2 贡献了 80% 的高分候选
- **策略聚焦**: 将温度范围从 [0.05-0.8] 收窄到 [0.05-0.6]，去掉高温段
- **自动化**: Agent 编写 watcher 脚本，在 R24 完成后自动检测 GPU 空闲并启动 R25，实现无人值守
- **结果**: sort_score 0.9447 → **0.9477**（+0.0030），chromo pLDDT 突破 0.970
- **日志摘录**: `"R24 done + GPU free + time OK → Launching R25!"`

#### R25→R27: 边界探测与多样性探索

- **边界分析**: Agent 计算各分项剩余空间（pTM 6.8%, pLDDT 5.3%, chromo 3.0%），判断 MPNN+ESMFold 天花板约 0.95
- **5 方向探索**: Agent 设计了 5 个方向同时测试：
  - A 极低温 [0.01, 0.05] → top=0.9480（微幅突破）
  - B 超高温 [1.0, 1.5] → 通过率 1%，结构破坏
  - C 极少固定 [66,67,222] → MPNN 几乎复制父代
  - D 超宽固定 [1,2,65,66,67,96,203,222] → top=0.9458
  - E 全谱温度 → 高温段生成失败
- **结论**: Agent 判定已极度逼近局部最优，进一步突破需要新方法（AlphaFold2/ESM3/RFdiffusion3）

#### 数据库与可视化系统

- **数据整合**: Agent 自动将 27 轮实验的 238,691 条去重序列、402,650 条指标记录导入 SQLite 数据库
- **可视化**: Agent 搭建了三栏交互式网站（FastAPI + React + Cytoscape + Plotly），支持序列检索、谱系网络、图表联动
- **R 图表**: Agent 编写 R 脚本生成高质量图表（分数趋势、pTM×chromo 散点、Top30 热图、序列 identity 矩阵）
- **Docker 部署**: 全部服务容器化，避免端口冲突

## License

MIT License

Copyright (c) 2026 SnowFold
