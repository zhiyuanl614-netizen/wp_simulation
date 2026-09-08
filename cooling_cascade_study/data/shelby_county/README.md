# Shelby County 真实水-电相互依赖基础设施基准数据集说明文档

## 1. 数据集概述与工程背景

本数据集收录并标准化了国际基础设施相互依赖与韧性仿真领域最经典的真实同址基准案例——**美国田纳西州谢尔比县（Shelby County, Tennessee，孟菲斯大都会区 MMSA）水-电相互依赖系统**。

该案例系统真实对应于孟菲斯轻工水电局（Memphis Light, Gas and Water, MLGW）与田纳西河流域管理局（Tennessee Valley Authority, TVA）管辖的供水与供电基础设施。自 1990 年代起，该区域被选为美国国家地震工程研究中心（MCEER）与美国国家标准与技术研究院（NIST）社区韧性规划中心的核心研究测试床（MMSA Testbed），并在随后数十篇经典文献（Adachi & Ellingwood 2008; Hernandez-Fajardo & Dueñas-Osorio 2011; Gonzalez et al. 2016; Wang, Magoua & Li 2022）中被确立为跨基础设施级联失效与韧性恢复的标准 Benchmark。

---

## 2. 文献溯源与版本演进

| 演进阶段 / 文献 | 贡献与数据形态 | 对本研究的映射价值 |
|---|---|---|
| **MCEER 奠基报告**<br>• Chang et al. (1996) *MCEER-96-0011*<br>• Shinozuka et al. (1998) *MCEER-98-MN02* | 首次公开 Shelby County 水网（9 泵站/6 水箱/960 节点）与电网（8 门站电厂/36 变电站）拓扑及地理信息。 | 真实管网与输电线路地理布局的物理源头。 |
| **网络化精简与易损性建模**<br>• Adachi & Ellingwood (2008, 2009, 2010) *RESS* / *J. Infrastruct. Syst.* | 将水网提炼为 49 节点（6 水箱、9 泵站、34 配水节点）、71 管道的骨干输水模型，标定地震易损性。 | 确立了 49 节点水网的标准节点定义与需水分布。 |
| **拓扑水-电相互依赖建立**<br>• Hernandez-Fajardo & Dueñas-Osorio (2011, 2013) *Earthq. Spectra* / *RESS* | 首次建立电网变电站与水网泵站间的物理供电依赖，以及电厂与水网的供水依赖。 | 提供了跨基础设施依赖对（Interdependent Pairs）的物理连接。 |
| **iNDP 恢复基准数据库**<br>• Gonzalez, Dueñas-Osorio et al. (2016) *CA-CIE*<br>• Talebiyan et al. (2019, 2021) | 建立了完整的 Extended Shelby County 数据库（含经纬度、重置成本、失负荷惩罚、气网与通信网），公开于 Rice University SISSRA。 | 本项目 `raw_extended/` 的直接权威源头。 |
| **HLA 联邦共仿真**<br>• Wang, Magoua & Li (2022) *Autom. Constr.* | 采用 EPANET v2.2（水）+ OpenDSS v9.0（电）+ IN-CORE 建立水-电双向级联联邦共仿真模型。 | 本文 §3.4 外部验证叙事与机理对比的基准文献。 |

*注：学术交流中有时因同名县将该系统误标为肯塔基州（Kentucky），经原作者论文与地理坐标（-90.15°W, 35.07°N）核实，权威实际对应为田纳西州谢尔比县（Shelby County, TN）。*

---

## 3. 系统组成与拓扑参数

### 3.1 电力系统（Power Network）
- **母线总数**：75 节点（含 9 个门站发电机节点、17 个 23-kV 变电站、25 个 12-kV 变电站、24 个输电线路交叉/连接点）。
- **支路总数**：93 条输电线路（电压等级包括 115 kV、23 kV、12 kV，长度范围 0.40 km – 16.04 km）。
- **装机与负荷**：
  - 总发电容量（9 台 Gate Station 机组）：$P_{\max,\Sigma} = 1000.0$ MW（或原始未缩放口径 1433 MW）。
  - 总基准用电负荷：$P_{d,\Sigma} = 1000.0$ MW（分布于 42 个 23-kV/12-kV 变电站负荷中心）。
  - 潮流模型支持：`processed/case_shelby.py`（标准 PYPOWER / MATPOWER 格式，支持直流潮流 DC-PF 与最优潮流 OPF）。

### 3.2 供水系统（Water Network）
- **节点总数**：49 节点（含 9 个取自深层自流含水层的泵站水源 P1–P9、6 个高位重力调节水箱 T1–T6、34 个综合配水节点 D1–D34）。
- **管段总数**：71 条主干输水管线（管径 16 cm – 122 cm，长度 1.50 km – 19.32 km）。
- **供水能力与需求**：
  - 总水源供水能力：1148 单位（对应基准日供水量 1.2–1.5 亿加仑）。
  - 水动力学模型支持：`processed/shelby_water_wntr.py`（标准 WNTR / EPANET 2.2 模型，支持 24–72 h 扩展时段 EPS 与水头驱动 PDD 分析）。

### 3.3 气网与通信网（扩展系统）
- **燃气系统**：16 节点（3 门站、6 调压站、7 配气点），17 条输气管线。
- **通信系统**：27 节点（23 光纤/微波节点、4 光缆接头），36 条通信链路。

---

## 4. 水-电相互依赖映射（Interdependency Mapping）

根据 Wang et al. (2022) Table 2 及 Gonzalez et al. (2016)，Shelby 系统的跨域耦合关系如下：

### 4.1 电 $\rightarrow$ 水方向（变电站供电 $\rightarrow$ 泵站）
| 电网变电站（Dependee） | 水网泵站（Depender） | 物理意义 |
|---|---|---|
| Substation 13 (23kV) | Pumping Station P1 (Node 1) | 变电站失电致 P1 停止抽水 |
| Substation 2 (Gate 2) | Pumping Station P2 (Node 2) | 变电站失电致 P2 停止抽水 |
| Substation 12 (23kV) | Pumping Station P3 (Node 3) | 变电站失电致 P3 停止抽水 |
| Substation 25 (23kV) | Pumping Station P4 (Node 4) | 变电站失电致 P4 停止抽水 |
| Substation 22 (23kV) | Pumping Station P5 (Node 5) | 变电站失电致 P5 停止抽水 |
| Substation 9 (23kV) | Pumping Station P6 (Node 8) | 变电站失电致 P6 停止抽水 |
| Substation 4 (Gate 4) | Pumping Station P7 (Node 11) | 变电站失电致 P7 停止抽水 |
| Substation 20 (23kV) | Pumping Station P8 (Node 10) | 变电站失电致 P8 停止抽水 |
| Substation 31 (12kV) | Pumping Station P9 (Node 7) | 变电站失电致 P9 停止抽水 |

### 4.2 水 $\rightarrow$ 电方向（配水节点供水 $\rightarrow$ 电厂冷却水）
| 配水节点（Dependee） | 门站发电机（Depender） | 物理意义（冷却水中断门槛） |
|---|---|---|
| Water Node 19 | Generator G1 (Bus 0 / Gate 37) | 水压低于门槛时 G1 降额/跳闸 |
| Water Node 27 | Generator G2 (Bus 1 / Gate 38) | 水压低于门槛时 G2 降额/跳闸 |
| Water Node 31 | Generator G3 (Bus 2 / Gate 39) | 水压低于门槛时 G3 降额/跳闸 |
| Water Node 44 | Generator G4 (Bus 3 / Gate 40) | 水压低于门槛时 G4 降额/跳闸 |
| Water Node 32 | Generator G5 (Bus 4 / Gate 41) | 水压低于门槛时 G5 降额/跳闸 |
| Water Node 36 | Generator G6 (Bus 5 / Gate 42) | 水压低于门槛时 G6 降额/跳闸 |
| Water Node 42 | Generator G7 (Bus 6 / Gate 43) | 水压低于门槛时 G7 降额/跳闸 |
| Water Node 39 | Generator G8 (Bus 7 / Gate 44) | 水压低于门槛时 G8 降额/跳闸 |

---

## 5. 文件目录结构

```
cooling_cascade_study/data/shelby_county/
├── README.md                      # 本说明文档
├── populate_raw.py                # 原始数据抽取与生成脚本
├── process_shelby_data.py         # 数据标准化转换与模型生成脚本
├── verify_shelby_simulation.py    # 仿真执行与计算校验脚本
├── raw_extended/                  # 原始基准 CSV 数据（Dueñas-Osorio / Talebiyan）
│   ├── WaterNodes.csv             # 49 水节点（经纬度/类型/需水/人口/收入/成本）
│   ├── WaterArcs.csv              # 71 水管线（长度/容量/成本）
│   ├── PowerNodes.csv             # 75 电节点（经纬度/类型/负荷/容量/成本）
│   ├── PowerArcs.csv              # 93 电线路（长度/容量/阻抗参数）
│   ├── GasNodes.csv               # 16 气节点
│   ├── GasArcs.csv                # 17 气管线
│   ├── TelecommunicationNodes.csv # 27 通信节点
│   ├── TelecommunicationArcs.csv  # 36 通信链路
│   └── Interdep.csv               # 73 条跨基础设施相互依赖关系
└── processed/                     # 标准化输出与仿真输入文件
    ├── shelby_water_nodes.csv     # 标准化水节点表
    ├── shelby_water_pipes.csv     # 标准化水管线表
    ├── shelby_power_buses.csv     # 标准化电母线表
    ├── shelby_power_gens.csv      # 标准化发电机表
    ├── shelby_power_branches.csv  # 标准化电支路表
    ├── shelby_coupling_map.csv    # 标准化耦合映射表
    ├── case_shelby.py             # PYPOWER 电力潮流算例文件
    ├── shelby_water_wntr.py       # WNTR 管网水力仿真构建脚本
    └── shelby_summary_stats.json  # 拓扑统计摘要 JSON
```

---

## 6. 复现与运行命令

在工作空间根目录下运行以下命令即可完成数据处理与仿真验证：

```bash
# 1. 重新生成并转换数据
python3 cooling_cascade_study/data/shelby_county/process_shelby_data.py

# 2. 执行直流潮流 (PYPOWER) 与管网水力 (WNTR) 双向校验
python3 cooling_cascade_study/data/shelby_county/verify_shelby_simulation.py
```

执行后将输出：
- 电力系统直流潮流（DC-PF）收敛状态、发电机有功出力分布与支路负载率；
- 供水系统 24 小时水动力学节点压头分布（min/mean/max）、管道流量分布。
