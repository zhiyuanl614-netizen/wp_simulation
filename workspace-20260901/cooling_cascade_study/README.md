# 电厂冷却水故障级联影响动态仿真研究

**项目代号：** `cooling_cascade_study`
**研究目标：** 量化**市政供水管网压力失效（配水节点压头 < 最小供水阈值 28 m，无法为电厂高位补水箱补水）经冷却水故障对电力系统的影响**，并对比**有无早期预警**下电网主动/被动控制的差异。方法逐项对齐 Yu, Guo, Wu, Qiao, Sun. *Early warning and proactive control strategies for power blackouts caused by gas network malfunctions.* Nature Communications 15:4714 (2024)（孙宏斌院士团队），物理量由天然气替换为冷却水。

> 本项目与 `../ieee118_dc/`（IEEE 118 直流潮流算例）相互独立，仅在需要电网拓扑/参数时复用其数据（`p1` 机组额定出力取自 `ieee118_dc/gen.csv`）。

## 目录结构

```
cooling_cascade_study/
├── README.md                      本文件（项目导航）
├── make_report.py                 报告生成器（读 figures/ 图 + results/ 数据 → 自包含 HTML）
├── 研究报告_冷却水故障级联与预警韧性.html   ★ 最终研究报告（自包含）
│
├── docs/                          文档层
│   ├── research_plan.md           研究方案（背景/目标/方法）
│   ├── mathematical_modeling.md   ★ 完整数学建模（全部函数模型+理论方法）
│   ├── parameter_fitting.md       参数拟合与来源登记表（规范出处）
│   ├── literature_checklist.md    文献调研清单 + 同源/多源对齐
│   ├── water_side_model.md        水源侧水力学子模型说明
│   └── scenario_matrix.csv        仿真场景 / 时序矩阵
│
├── src/                           计算模块层（按研究主线编号）
│   ├── 00_muni_wdn/               市政水网（D-town 真实基准网, 含真实需水量）
│   │   ├── README.md  data/DTOWN.inp
│   │   ├── boundary_generator.py      电厂取水点错峰失压（供 03 边界 t_fault_i）
│   │   ├── saet_distribution.py       全网失压时刻分布 + P10/P50/P90 代表节点
│   │   ├── network_outage.py          唯一水源停供→全网 399 节点压力时空崩溃
│   │   ├── coupling_map.py            全耦合映射(54 发电机↔取水 junction, 见 docs/coupling_map.md)
│   │   └── plot_muni.py  plot_saet_distribution.py  plot_network_outage.py
│   ├── 01_cooling_chain/          故障机理链（市政断水→跳机；产出 AET/ASW/SAET）
│   │   └── README.md  params.py  submodels.py  simulate.py  plot_results.py
│   ├── 02_ics/                    三域独立三级 ICS + 架构图（有无预警对比）
│   │   ├── README.md  db.py  field_plc.py  scada.py  dispatch.py
│   │   └── ics_simulation.py  run_ics_scenarios.py  plot_ics.py
│   └── 03_proactive_control/      主动控制 LP（对齐文献 PA/SP/DP + DC潮流）
│       ├── README.md  dc_network.py  warning_indicators.py  proactive_lp.py
│       ├── run_p6.py  plot_p6.py
│       └── node_sensitivity.py  plot_node_sensitivity.py   取水节点位置敏感性
│
├── figures/                       ★ 论文成图集（唯一图库, Fig.1–12 + README）
│   ├── Fig1–3 *.svg               概念图（手绘矢量：框架/冷却水链/时间差机制）
│   ├── Fig4_ICS_architecture.svg  ICS 架构（手工制作, 无脚本重生成, 唯一存档）
│   └── Fig5–12 *.png / *.svg      结果图（脚本生成, dpi=300）
│
└── results/                       仿真数据（按模块分子目录, 仅 json/csv/db）
    ├── muni/                      muni_boundary·network_outage·saet_distribution (.json)
    ├── cooling_chain/             p1_smib_*.csv
    ├── ics/                       ics_sim.db·ics_warning_compare.json·ics_timeseries.json
    └── proactive_control/         p6_strategy_compare·p6_timeseries·p6_node_sensitivity (.json)
```

> **图 vs 数据的约定：** `figures/` 是唯一成图集（入稿/报告用）；`results/` 只存仿真数据。绘图脚本重跑会在 `results/` 写出可再生的 PNG（中间产物），确认后复制并按 Fig 编号覆盖到 `figures/`。

## 研究主线（对齐参照文献）

- **00 市政水网** 用真实基准配水管网 **D-town**（含真实城市需水量）仿真：①各电厂取水点**多源错峰失压**（供下游边界，对齐文献 Fig.7 多端源案例）；②唯一水源停供后**全网 399 节点压力时空崩溃**；③失压时刻**全网分布**（回应"失压时刻依赖取水位置"）。市政水网只作**上游边界生成器**，因缓冲(ASW)在电厂内部、不在管网里。
- **01 故障机理链** 打通"市政配水节点压头<28m失效→补水箱/集水池排空→跳泵→背压上升→机组跳机"，计算早期预警指标 **AET/ASW/SAET**。
- **02 ICS** 三域独立三级工业控制系统（市政供水/冷却水/电力各设 PLC/SCADA/调度 + SQLite）——市政供水 ICS 检出压头失效后经早期预警链路通知电力 ICS，触发主动处置；**影响以少发功率(MW)/损失电量(MWh)衡量**。
- **03 主动控制 LP** 对齐文献"气-电早期预警"方法：AET/ASW/SAET 指标 + LP 求解 **PA/SP/DP** 三策略，全程 **DC 潮流**、**两级备用**；含取水节点位置敏感性。

## 核心结论（一句话）

市政供水中断经电厂冷却水故障传导至电力系统；**早期预警 + 主动控制**可将少发功率与损失电量大幅削减甚至消除（无预警 485.6 MW / 49.1 MWh → 有预警 0 / 0；同源多机共因下动态主动控制 DP 完全消除缺额）。

## 运行（复现）

```bash
pip install pypower wntr        # 每个新 session 需重装

# 00 市政水网
cd src/00_muni_wdn
python boundary_generator.py && python plot_muni.py
python saet_distribution.py   && python plot_saet_distribution.py
python network_outage.py      && python plot_network_outage.py

# 01 故障机理链（t_end 需 ≥6500，因 SAET~90min）
cd ../01_cooling_chain
python simulate.py --t_fault 60 --ramp 0   --t_end 6500 --dt 4
python simulate.py --t_fault 60 --ramp 600 --t_end 6500 --dt 4
python plot_results.py

# 02 ICS
cd ../02_ics
python run_ics_scenarios.py && python plot_ics.py

# 03 主动控制 LP
cd ../03_proactive_control
python run_p6.py            && python plot_p6.py
python node_sensitivity.py  && python plot_node_sensitivity.py

# 报告（项目根）
cd ../..
python make_report.py
```

## 快速入口

- 整体思路 → `docs/research_plan.md`
- **完整数学模型与理论方法** → `docs/mathematical_modeling.md`
- 参数拟合与规范出处 → `docs/parameter_fitting.md`
- 水源侧水力学子模型 → `docs/water_side_model.md`
- 仿真场景设计 → `docs/scenario_matrix.csv`
- 文献清单与对齐 → `docs/literature_checklist.md`

## 一句话概述

**市政水网压力失效（补水中断）** → 高位补水箱/集水池水位下降 → 循环水泵流量下降/汽蚀跳泵 → 凝汽器真空恶化、低压缸背压升高 → 机组高背压保护跳闸 → 电力系统少发功率/损失电量（若无预警）。本研究通过**水力-热力-机械-电气多时间尺度耦合仿真**量化上述链条，并证明早期预警+主动控制的价值。影响以**少发功率(MW)/损失电量(MWh)** 衡量，潮流全程 **DC-PF/PTDF**（不含系统频率）。

## 已确定的研究范围

- 机组：常规燃煤汽轮机组，聚焦**凝汽器—低压缸**（不含锅炉慢动态）
- 电网：固定 **IEEE 118**（复用 `../ieee118_dc/`），潮流用**直流潮流(DC-PF/PTDF)**
- 备用：**两级**（旋转备用 + 慢起机备用）
- 数据：**无现场数据**，参数按国家/国际标准（GB/T 50102、DL/T 5339、HEI/ASME PTC 12.2）+ 机组额定/实际出力拟合；市政管网用 D-town 公开基准（CC BY-NC 4.0）
- 失效源：**市政配水节点压头 < 28 m**，无法为高位补水箱补水
- 影响指标：**少发功率 (MW) + 损失电量 (MWh)**（与文献一致）
```
