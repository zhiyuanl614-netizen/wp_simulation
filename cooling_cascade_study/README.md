# 电厂冷却水故障级联影响动态仿真研究

**项目代号：** `cooling_cascade_study`
**研究目标：** 量化**市政供水管网压力失效（配水节点压头 < 最小供水阈值 28 m，无法为电厂高位补水箱补水）经冷却水故障对电力系统的影响**，并对比**有无早期预警**下电网主动/被动控制的差异。方法逐项对齐 Yu, Guo, Wu, Qiao, Sun. *Early warning and proactive control strategies for power blackouts caused by gas network malfunctions.* Nature Communications 15:4714 (2024)（孙宏斌院士团队），物理量由天然气替换为冷却水。

> 本项目与 `../ieee118_dc/`（IEEE 118 直流潮流算例）相互独立，仅在需要电网拓扑/参数时复用其数据（`p1` 机组额定出力取自 `ieee118_dc/gen.csv`）。

## 目录结构

```
cooling_cascade_study/
├── README.md                      本文件（项目导航）
├── make_report.py                 研究报告生成器（读 figures/ 图 + results/ 数据 → 自包含 HTML；历史报告按需再生）
├── make_paper_draft.py            论文骨架生成器（13 图 4 表 + 章节摘要 → 自包含 HTML；历史骨架按需再生）
├── 论文简要版_骨架.md              ★ 论文骨架 Markdown 学术规范版（题目-摘要-关键词-引言-方法-案例-结果-敏感性-讨论-结论，主旨句式；合稿脚本题目源）
├── 论文完整版.md                  ★ 论文合稿版 v1（八件正稿程序化合并：图 1–13 嵌入正文＋文献按首现顺序统一重排；生成器 docs/merge_manuscript.py）
├── 论文完整版.html                ★ 论文合稿版 v1 自包含渲染（图片与 MathJax 全内嵌，可离线阅读/打印 PDF；生成器 docs/render_manuscript_html.py）
│
├── docs/                          文档层
│   ├── paper_chapters/            正稿章节草稿（全 8 件：ch1–ch7 ＋前后件〔摘要/数据可用性/致谢〕；合稿正文的权威源）
│   ├── merge_manuscript.py        合稿脚本（八件正稿 → 论文完整版.md：三类机械变换＋全套断言校验）
│   ├── render_manuscript_html.py  合稿渲染脚本（论文完整版.md → 自包含 HTML：data URI 图片＋内嵌 MathJax）
│   ├── renumber_map.json          合稿文献重排映射（旧编号→新编号，按全文首次出现顺序）
│   ├── mathematical_modeling.md   ★ 完整数学建模（全部函数模型+理论方法，权威公式源）
│   ├── coupling_map.md            全耦合映射验证（54 对配对与 Q1–Q5 分层；源码 docstring 引用的设计文档）
│   ├── parameter_fitting.md       参数拟合与来源登记表（规范出处；正文表 2 引用）
│   ├── scenario_matrix.csv        仿真场景 / 时序矩阵（正文表 3 引用）
│   ├── paper_review_and_guidance.md   审阅意见与写作指导（P0 实验待办在此）
│   └── verification/report.md     ★ 复现验证报告（全流程复算，2026-09-02；正文 §3.3 引用）
│
├── src/                           计算模块层（按研究主线编号）
│   ├── figstyle.py                统一图件样式（出版级规范：字号 12/300dpi/语义色板）
│   ├── figures_concept/           概念与拓扑图脚本（fig4_coupling_topology.py、
│   │                              fig12_nk_scaling.py[现产 Fig11] + assets/IEEE118 图）
│   ├── 00_muni_wdn/               市政水网（D-town 真实基准网, 含真实需水量）
│   │   ├── README.md  data/DTOWN.inp
│   │   ├── boundary_generator.py       电厂取水点错峰失压（供 03 边界 t_fault_i）
│   │   ├── saet_distribution.py        全网失压时刻分布 + P10/P50/P90 代表节点
│   │   ├── network_outage.py           唯一水源停供→全网 399 节点压力时空崩溃
│   │   ├── coupling_map.py             全耦合映射（54 发电机↔取水 junction）
│   │   ├── full_coupling_boundary.py   全耦合失效边界（S07/S08 输入）
│   │   ├── closed_water_balance.py     闭合水量账（B-RT 口径）
│   │   ├── verify_coupling_rule.py     耦合规律验证（54/54）
│   │   └── plot_muni.py  plot_saet_distribution.py  plot_network_outage.py
│   ├── 01_cooling_chain/          故障机理链（市政断水→跳机；产出 AET/ASW/SAET）
│   │   └── README.md  params.py  submodels.py  simulate.py  plot_results.py
│   ├── 02_ics/                    三域独立三级 ICS（有无预警对比）
│   │   ├── README.md  db.py  field_plc.py  scada.py  dispatch.py
│   │   └── ics_simulation.py  run_ics_scenarios.py  plot_ics.py
│   └── 03_proactive_control/      主动控制 LP（对齐文献 PA/SP/DP + DC潮流）
│       ├── README.md  dc_network.py  warning_indicators.py  proactive_lp.py
│       ├── run_p6.py  plot_p6.py                              三策略对比（图 9/10）
│       ├── critical_ramp_example.py                           临界降出力速率算例（图 8）
│       ├── node_sensitivity.py  plot_node_sensitivity.py      取水位置敏感性（图 13）
│       ├── nk_scan.py  full_order_cascade.py                  N-k 扫描（图 11）/ 全序级联
│       ├── ramp_rate_scan.py                                   备用爬坡率 R 扫描（图 14/表 5）
│       └── dp_reserve_scan.py                                  DP 差异化＋备用容量 rf 扫描（图 14/表 6）
│
├── figures/                       ★ 论文成图集（唯一图库, Fig.1–14, 已全部校准）
│   ├── Fig1–3 *.svg               概念图（手绘矢量：框架[含 ICS 架构]/冷却水链/时间差机制）
│   └── Fig4–14 *.png              结果图（脚本生成, dpi=300）
│
└── results/                       仿真数据（按模块分子目录, 仅 json/csv/db）
    ├── muni/                      boundary·network_outage·saet_distribution·coupling_map·
    │                              full_coupling_boundary·closed_water_balance·耦合验证 (.json/.csv)
    ├── cooling_chain/             p1_smib_*.csv
    ├── ics/                       ics_sim.db·ics_warning_compare.json·ics_timeseries.json
    └── proactive_control/         p6_*·p6_node_sensitivity·nk_scan·critical_ramp·
                                   full_order_cascade·ramp_rate_scan·dp_reserve_scan (.json/.csv)
```

> **图 vs 数据的约定：** `figures/` 是唯一成图集（入稿/报告用）；`results/` 只存仿真数据。绘图脚本重跑会在 `results/` 写出可再生的 PNG（中间产物，用后即删），确认后复制并按 Fig 编号覆盖到 `figures/`。

## 研究主线（对齐参照文献）

- **00 市政水网** 用真实基准配水管网 **D-town**（含真实城市需水量）仿真：①各电厂取水点**多源错峰失压**（供下游边界，对齐文献 Fig.7 多端源案例）；②唯一水源停供后**全网 399 节点压力时空崩溃**；③失压时刻**全网分布**（回应"失压时刻依赖取水位置"）。市政水网只作**上游边界生成器**，因缓冲(ASW)在电厂内部、不在管网里。
- **01 故障机理链** 打通"市政配水节点压头<28m失效→补水箱/集水池排空→跳泵→背压上升→机组跳机"，计算早期预警指标 **AET/ASW/SAET**。
- **02 ICS** 三域独立三级工业控制系统（市政供水/冷却水/电力各设 PLC/SCADA/调度 + SQLite）——市政供水 ICS 检出压头失效后经早期预警链路通知电力 ICS，触发主动处置；**影响以少发功率(MW)/损失电量(MWh)衡量**。
- **03 主动控制 LP** 对齐文献"气-电早期预警"方法：AET/ASW/SAET 指标 + LP 求解 **PA/SP/DP** 三策略，全程 **DC 潮流**、**两级备用**；含临界速率算例、取水节点位置敏感性与 N-k 稳健性扫描。

## 核心结论（一句话）

市政供水中断经电厂冷却水故障传导至电力系统；**早期预警 + 主动控制**可将少发功率与损失电量大幅削减甚至消除（无预警 485.6 MW / 49.1 MWh → 有预警 0 / 0；同源多机共因下亦 0/0）；适用边界为同时失效机组数 **k≤2**（k≥3 残留 95.6–128.2 MWh），分散取水使被动峰值 343→315 MW 而主动控制对位置稳健。

## 运行（复现）

> **复现验证（2026-09-02）：** 全部 16 个计算脚本 + 9 个绘图脚本已按依赖顺序完整重跑，与存档结果逐项比对——实质数值差异 0、论文引用数值全部逐位复现、8/9 张再生成图像素级一致。检验报告见 `docs/verification/report.md`。比对基准存档（archived_results_snapshot）已在全部链路核实一致后的空间整理（2026-09-02）中移除：`results/` 为唯一权威版本，快照与其仅差 LP 计时字段、登记串与模式演进字段（均良性，见报告 §4）。
>
> **图件校准（2026-09-02）：** 图 4–13 已逐张校准并数据链复跑核实（逐字节一致），校准日志已随 2026-09-06 工作空间整理移入 git 历史（清理前快照 `63fc7f6`）；运行环境注意——容器每回合重置，需 `pip install pypower wntr`。

```bash
pip install pypower wntr scipy matplotlib adjustText   # 每个新 session 需重装

# 00 市政水网（7 个计算脚本）
cd src/00_muni_wdn
python boundary_generator.py    && python plot_muni.py
python saet_distribution.py     && python plot_saet_distribution.py
python network_outage.py        && python plot_network_outage.py
python coupling_map.py && python full_coupling_boundary.py
python closed_water_balance.py && python verify_coupling_rule.py

# 01 故障机理链（t_end 需 ≥6500，因 SAET~90min）
cd ../01_cooling_chain
python simulate.py --t_fault 60 --ramp 0   --t_end 6500 --dt 4
python simulate.py --t_fault 60 --ramp 600 --t_end 6500 --dt 4
python plot_results.py

# 02 ICS
cd ../02_ics
python run_ics_scenarios.py && python plot_ics.py

# 03 主动控制 LP（7 个计算脚本）
cd ../03_proactive_control
python run_p6.py               && python plot_p6.py
python node_sensitivity.py     && python plot_node_sensitivity.py
python critical_ramp_example.py
python nk_scan.py              # ~250 s（24×2 LP）
python full_order_cascade.py
python ramp_rate_scan.py       # ~1100 s（3 场景×9 R×2 策略 LP, 11 项锚点回归校验）
python dp_reserve_scan.py      # ~1000 s（DP×9 R + rf×4×PA/SP 共 51 LP, 8 项锚点校验）

# 概念/拓扑图（Fig4）
cd ../figures_concept && python fig4_coupling_topology.py && cd ..

# 交付物生成（项目根）
cd ../..
python make_report.py          # 研究报告
python make_paper_draft.py     # 论文骨架
```

## 快速入口

- **完整数学模型与理论方法** → `docs/mathematical_modeling.md`
- 参数拟合与规范出处 → `docs/parameter_fitting.md`
- 全耦合映射与分层 → `docs/coupling_map.md`
- 仿真场景设计 → `docs/scenario_matrix.csv`
- 审阅意见与 P0 实验待办 → `docs/paper_review_and_guidance.md`
- 论文骨架（MD 学术规范版，主旨句式）→ `论文简要版_骨架.md`
- **正稿章节草稿**（数值溯源至代码/数据，含文末参考文献）→ `docs/paper_chapters/`
- **论文合稿完整版**（图 1–13 嵌入正文、文献首现重排、自包含 HTML）→ `论文完整版.md` / `论文完整版.html`（生成器 `docs/merge_manuscript.py` + `docs/render_manuscript_html.py`，重排映射 `docs/renumber_map.json`）
- 复现验证报告 → `docs/verification/report.md`

> **归档说明（2026-09-06 整理）：** 以下过程文档已被后续版本完全取代并移除，全部可由 git 历史恢复（清理前快照 `63fc7f6`）：`研究报告_冷却水故障级联与预警韧性.html`、`论文简要版_骨架.html`（由 `论文完整版` 取代，亦可经 `make_report.py` / `make_paper_draft.py` 再生）；`docs/research_plan.md`、`docs/paper_outline.md`、`docs/skeleton_revision_plan.md`、`docs/figure_design.md`、`docs/figure_calibration_log.md`、`docs/water_side_model.md`、`docs/literature_checklist.md`（内容已吸收进骨架、正稿与图注）。

## 一句话概述

**市政水网压力失效（补水中断）** → 高位补水箱/集水池水位下降 → 循环水泵流量下降/汽蚀跳泵 → 凝汽器真空恶化、低压缸背压升高 → 机组高背压保护跳闸 → 电力系统少发功率/损失电量（若无预警）。本研究通过**水力-热力-机械-电气多时间尺度耦合仿真**量化上述链条，并证明早期预警+主动控制的价值。影响以**少发功率(MW)/损失电量(MWh)** 衡量，潮流全程 **DC-PF/PTDF**（不含系统频率）。

## 已确定的研究范围

- 机组：常规燃煤汽轮机组，聚焦**凝汽器—低压缸**（不含锅炉慢动态）
- 电网：固定 **IEEE 118**（复用 `../ieee118_dc/`），潮流用**直流潮流(DC-PF/PTDF)**
- 备用：**两级**（旋转备用 + 慢起机备用）
- 数据：**无现场数据**，参数按国家/国际标准（GB/T 50102、DL/T 5339、HEI/ASME PTC 12.2）+ 机组额定/实际出力拟合；市政管网用 D-town 公开基准（CC BY-NC 4.0）
- 失效源：**市政配水节点压头 < 28 m**，无法为高位补水箱补水
- 影响指标：**少发功率 (MW) + 损失电量 (MWh)**（与文献一致）
