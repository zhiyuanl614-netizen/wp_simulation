# 电厂冷却水故障级联影响动态仿真研究

**项目代号：** `cooling_cascade_study`
**研究目标：** 量化**市政供水管网压力失效（配水节点压头 < 最小供水阈值 28 m，无法为电厂高位补水箱补水）经冷却水故障对电力系统的影响**，并对比**有无早期预警**下电网主动/被动控制的差异。方法逐项对齐 Yu, Guo, Wu, Qiao, Sun. *Early warning and proactive control strategies for power blackouts caused by gas network malfunctions.* Nature Communications 15:4714 (2024)（孙宏斌院士团队），物理量由天然气替换为冷却水。

> 外部基准数据集中存放于仓库根 `data/`：`ieee118_dc/`（IEEE 118 直流潮流算例，2026-09-17 自仓库外移入）与 `DTOWN.inp`（D-town 市政水网基准）；`p1` 机组额定出力取自 `data/ieee118_dc/gen.csv`。

## 目录结构

```
cooling_cascade_study/
├── README.md                      本文件（项目导航）
├── 论文完整版.md                  ★ 论文唯一正稿 v8（D-town 指定 6 对耦合；第 2 章逐节英文重写进行中：§2.1 已完成 2026-09-17；直接在本文件改稿）
├── 论文完整版.html                ★ 论文 v8 自包含渲染（图片与 MathJax 全内嵌，可离线阅读/打印 PDF；由 docs/render_manuscript_html.py 渲染）
│
├── docs/                          文档层
│   ├── render_manuscript_html.py  渲染脚本（论文完整版.md → 自包含 HTML：data URI 图片＋内嵌 MathJax）
│   ├── parameter_fitting.md       参数拟合与来源登记表（规范出处；正文 §2.3 及补充材料表 S3 引用）
│   ├── scenario_matrix.csv        仿真场景 / 时序矩阵（正文表 3 引用）
│   ├── submission/                投稿件层（AE_submission_checklist.md 投稿清单＋cover_letter_AppliedEnergy.md 投稿信）
│   └── verification/              ★ 复现验证（report_v4_20260920.md 全链重跑报告＋cleanroom_reproduction_20260921.md 净室复现证书；补充材料 S4 汇总引用）
│
├── src/                           计算模块层（按研究主线编号）
│   ├── figstyle.py                统一图件样式（出版级规范：字号 12/300dpi/语义色板）
│   ├── figures_concept/           概念与拓扑图脚本（fig4_coupling_topology.py、
│   │                              fig12_nk_scaling.py[现产 figures/Fig11＝主文 Fig.9] + assets/IEEE118 图）
│   ├── 00_muni_wdn/               市政水网（D-town 真实基准网, 含真实需水量）
│   │   ├── README.md
│   │   ├── boundary_generator.py       电厂取水点错峰失压（供 03 边界 t_fault_i）
│   │   ├── saet_distribution.py        全网失压时刻分布 + P10/P50/P90 代表节点
│   │   ├── network_outage.py           唯一水源停供→全网 399 节点压力时空崩溃
│   │   ├── coupling_map.py             指定耦合映射（6 发电机↔6 取水 junction，硬过滤）
│   │   ├── full_coupling_boundary.py   指定耦合失效边界（B-RT 口径，S07/S08 输入）
│   │   ├── closed_water_balance.py     闭合水量账（B-RT 口径）
│   │   ├── verify_coupling_rule.py     耦合规律验证（6/6）
│   │   └── plot_muni.py  plot_saet_distribution.py  plot_network_outage.py
│   ├── 01_cooling_chain/          故障机理链（市政断水→跳机；产出 AET/ASW/SAET）
│   │   └── README.md  params.py  submodels.py  simulate.py  plot_results.py
│   ├── 02_ics/                    三域独立三级 ICS（有无预警对比）
│   │   ├── README.md  db.py  field_plc.py  scada.py  dispatch.py
│   │   └── ics_simulation.py  run_ics_scenarios.py  plot_ics.py
│   └── 03_proactive_control/      主动控制 LP（对齐文献 PA/SP/DP + DC潮流）
│       ├── README.md  dc_network.py  warning_indicators.py  proactive_lp.py
│       ├── run_p6.py  plot_p6.py                              三策略对比（图 7/8）
│       ├── critical_ramp_example.py                           临界降出力速率算例（图 6）
│       ├── node_sensitivity.py  plot_node_sensitivity.py      取水位置敏感性（图 11）
│       ├── nk_scan.py  full_order_cascade.py                  N-k 扫描（图 9）/ 全序级联
│       ├── ramp_rate_scan.py                                   备用爬坡率 R 扫描（图 12/表 5）
│       └── dp_reserve_scan.py                                  DP 差异化＋备用容量 rf 扫描（图 12/表 6）
│
├── figures/                       ★ 论文成图集（唯一图库；主文 Fig.1–12＋补充材料 Fig.S1/S2, 已全部校准；文件名沿用历史编号）
│   ├── Fig1–3 *.svg               概念图（手绘矢量：框架[含 ICS 架构]/冷却水链/时间差机制）
│   └── Fig4–14 *.png              结果图（脚本生成, dpi=300；Fig5/6 由补充材料 S3.2 引用, Fig7–14 对应主文 Fig.5–12）
│
├── data/                          外部基准数据（2026-09-17 集中整理）
│   ├── ieee118_dc/                IEEE 118 直流潮流算例（bus/gen/branch/ptdf 等＋DC-PF 校验报告）
│   └── DTOWN.inp                  D-town 市政水网基准模型（EPANET .inp，CC BY-NC 4.0 须署名）
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

市政供水中断经电厂冷却水故障传导至电力系统；**早期预警 + 主动控制**可将少发功率与损失电量大幅削减甚至消除（无预警 485.6 MW / 49.1 MWh → 有预警 0 / 0；同源六机共因 334.9 MW / 59.6 MWh → 0 / 0，N-k 全部 24 个子集 SP 均为 0）；冷却缓冲窗 SUET（统一热负荷口径）92.4–192.9 min，临界降出力速率 r\*=0.545 %Pg/min 经降额自保护反馈将运行时间延至 1.98×SUET（183.3 min）；适用边界在**备用-爬坡轴**（R\*、rf\*），不在失效规模轴；分散取水使被动能量损失削减 26.6% 而峰值不变，主动控制对取水位置稳健。

## 运行（复现）

> **复现验证：** v1 全量复现（2026-09-02）：全部 16 个计算脚本 + 9 个绘图脚本按依赖顺序完整重跑，与存档结果逐项比对——实质数值差异 0、论文引用数值全部逐位复现、8/9 张再生成图像素级一致；v2 耦合层重构后全链复算（2026-09-15）：节点无关不变量（ICS 485.6 MW/49.1 MWh、r\*=0.545 %Pg/min、T_max=183.3 min、bus89 SAET=88.6 min）与 v1 逐位一致，LP/扫描链锚点回归校验（10/10、8/8）全部通过；v3 评审修订（2026-09-20，报告 M1–M8 逐条落实）：热负荷更新口径全链统一为 Q_cond=λ_Q·Pg·min(of,k_p)，SUET 重注册为 92.4/121.8/130.0/151.5/151.9/192.9 min（bus 89/80/10/66/65/26），市政/冷却链/ICS 三层与 v3 逐字节一致，03 链（LP/扫描/级联）在统一语义下全量重跑且不依赖 SUET 的锚点全部复现；检验报告见 `docs/verification/report_v4_20260920.md`（v2/v3 报告已随 2026-09-21 空间清理移除，可由 git 历史恢复）（v1 报告 `report.md` 已随 2026-09-16 空间清理移除，可由 git 历史恢复）。比对基准存档（archived_results_snapshot）已在全部链路核实一致后的空间整理（2026-09-02）中移除：`results/` 为唯一权威版本，快照与其仅差 LP 计时字段、登记串与模式演进字段（均良性）。
>
> **图件校准（2026-09-02 定版，v2 复算 2026-09-15 全部重绘）：** 图 4–14 已逐张校准并数据链复跑核实，校准日志已随 2026-09-06 工作空间整理移入 git 历史（清理前快照 `63fc7f6`）；运行环境注意——容器每回合重置，需 `pip install pypower wntr`。图件本轮再生成记录见下方"恢复说明（2026-09-16）"。

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
python docs/render_manuscript_html.py  # 自包含 HTML 渲染（论文完整版.md → 论文完整版.html）
```

## 快速入口

- 参数拟合与规范出处 → `docs/parameter_fitting.md`
- 仿真场景设计 → `docs/scenario_matrix.csv`
- **论文完整版**（唯一正稿：图 1–12 嵌入正文、图 S1/S2 在补充材料、文献统一编号、自包含 HTML）→ `论文完整版.md` / `论文完整版.html`（改稿直接编辑 `论文完整版.md`，随后运行 `docs/render_manuscript_html.py` 重渲染）
- 复现验证报告 → `docs/verification/report_v4_20260920.md`

> **归档说明（2026-09-06 整理）：** 以下过程文档已被后续版本完全取代并移除，全部可由 git 历史恢复（清理前快照 `63fc7f6`）：`研究报告_冷却水故障级联与预警韧性.html`、`论文简要版_骨架.html`（由 `论文完整版` 取代，亦可经 `make_report.py` / `make_paper_draft.py` 再生）；`docs/research_plan.md`、`docs/paper_outline.md`、`docs/skeleton_revision_plan.md`、`docs/figure_design.md`、`docs/figure_calibration_log.md`、`docs/water_side_model.md`、`docs/literature_checklist.md`（内容已吸收进骨架、正稿与图注）。
>
> **清理说明（2026-09-16）：** 本轮空间清理移除旧版与无关条目，均可由 git 历史恢复（清理前检查点 commit `checkpoint: D-town v2 restoration complete (pre-cleanup)`）：`results_backup_v1/`、`src_backup_v1/`（v1 备份）；`logs_dp_scan.txt`、`logs_ramp_scan.txt`（运行日志）；`make_report.py`、`make_paper_draft.py`、`make_advisor_ppt.py`、`论文简要版_骨架.md`（旧生成器与骨架，合稿题目已改为脚本内硬编码）；`docs/paper_review_and_guidance.md`（骨架评审备忘，P0 已全部闭环）；`docs/rebuild_dp_reserve_scan.py`（一次性重建工具）；`docs/verification/report.md`（v1 复现报告，由 report_v2 取代）；`docs/verification/report_v3_20260915.md`（v3 Anytown 实验记录，已取代）；`src/00_muni_wdn/data/ANYTOWN.inp`（v3 实验数据，与 D-town 主链无关）。
>
> **恢复说明（2026-09-16，本轮修复）：** 为消除正文与仓库现状的悬空引用、恢复论文成图集，以下条目自 git 历史恢复或重生成——① `figures/`（Fig.1–3 SVG 自提交 `b8802b1` 恢复；Fig.4–14 由当前 v2 终版脚本 + 存档 `results/` 重生成——其中 10 张与论文完整版.html 内嵌版逐字节一致，Fig.7 因当前环境 matplotlib mathtext 渲染差异（数据/脚本相同，仅文本抗锯齿级差异）改取 HTML 内嵌版原字节，最终 `figures/` 14/14 与论文 HTML 内嵌版逐字节一致；Fig.8 重算的 critical_ramp 数值与存档逐位一致）；② `data/shelby_county/`（22 件，自 `b8802b1` 恢复，`verify_shelby_simulation.py` 复验通过——§3.4 引用闭环；`populate_raw.py` 数据内嵌、无需 zip）；③ `ieee118_dc/report_ieee118_dcpf.html`（自 `2d2447e` 恢复，其输入数据与当前 ieee118_dc 逐位一致）；④ `src/00_muni_wdn/README.md` 重写为 v2 语义（指定 6 对耦合，清除 v1 三厂取水表与"54 台全耦合"描述）。注意：提交 `b8802b1` 中的 Fig.4/5/12/13 为旧版脚本（2026-09-08）产物，布局与当前 v2 终版脚本不同，勿再从该提交恢复图片。

> **清理说明（2026-09-17）：** 移除 Shelby 外部验证内容与相关文件（正文 §3.4 整节、ch6/ch7 相应句、`data/shelby_county/` 全 22 件），表号级联重编（原表 4–7 → 表 4–6，正文与 src 树注释同步）；`ieee118_dc/` 自仓库外移入 `data/`、`DTOWN.inp` 自 `src/00_muni_wdn/data/` 移入 `data/`（相关代码路径已同步并通过编译）；docs/ 仅保留 render_manuscript_html.py、parameter_fitting.md、scenario_matrix.csv、verification/；章节正稿（`docs/paper_chapters/`）、合稿器 `merge_manuscript.py`、`renumber_map.json`、`mathematical_modeling.md`、`coupling_map.md`、`literature_structure_reference.md` 一并移除——`论文完整版.md` 成为唯一可编辑正稿（v7），改稿后仅重跑 render。清理前检查点 commit `0054934`（`checkpoint: pre-cleanup`），全部可由 git 历史恢复。

> **清理说明（2026-09-21，第二轮）：** 移除已闭环任务的过程文档（清理前检查点 commit `ee91e9a`，全部可由 git 历史恢复）——`docs/review/` 整目录（`editorial_assessment`、`expert_assessment`、`methods_review`、`zero_deficit_defense_analysis`：#28 专家评估、#30 零缺额裁定等已落盘于正稿与补充材料）；`docs/submission/` 下四份执行完毕的细案（`condensation_plan`、`normalization_plan`（#31）、`structure_plan`（#32）、`reference_expansion_plan`（#33），执行记录均已盖章且成果落盘）。保留：投稿清单、投稿信、验证报告与净室证书（活跃引用）、参数登记与场景矩阵（正文引用）。零缺额分析如需 rebuttal 复用，自 git 历史恢复即可。

> **清理说明（2026-09-21）：** 投稿定稿后空间瘦身（清理前检查点 commit `474fc45`），移除一次性脚本与被取代版本——`scripts/` 下 `condense_manuscript.py`–`condense7_manuscript.py`（正文压缩轮 7 遍已执行完毕，锚点全部落盘于正稿）、`m5_checks.py`、`pairing_permutation.py`（评审轮一次性运行器，实现在 `src/03_proactive_control/`，输出在 `results/`）；`docs/verification/report_v2_20260915.md`、`report_v3_20260918.md`（由 v4 取代）；`results/muni/coupling_map.png`（中间图，论文用 `figures/Fig4`）、`data/ieee118_dc/report_ieee118_dcpf.html`（DC 潮流中间报告）；工作区根目录 M1 重跑临时文件（`rerun_m1.*`、`sweep_m1_values.py` 等 12 件）。`scripts/` 仅留 `make_graphical_abstract.py`（投稿 GA 复现）。文件数 145→120（不含 .git），全部被删项均可由 git 历史恢复。

## 一句话概述

**市政水网压力失效（补水中断）** → 高位补水箱/集水池水位下降 → 循环水泵流量下降/汽蚀跳泵 → 凝汽器真空恶化、低压缸背压升高 → 机组高背压保护跳闸 → 电力系统少发功率/损失电量（若无预警）。本研究通过**水力-热力-机械-电气多时间尺度耦合仿真**量化上述链条，并证明早期预警+主动控制的价值。影响以**少发功率(MW)/损失电量(MWh)** 衡量，潮流全程 **DC-PF/PTDF**（不含系统频率）。

## 已确定的研究范围

- 机组：常规燃煤汽轮机组，聚焦**凝汽器—低压缸**（不含锅炉慢动态）
- 电网：固定 **IEEE 118**（复用 `data/ieee118_dc/`），潮流用**直流潮流(DC-PF/PTDF)**
- 备用：**两级**（旋转备用 + 慢起机备用）
- 数据：**无现场数据**，参数按国家/国际标准（GB/T 50102、DL/T 5339、HEI/ASME PTC 12.2）+ 机组额定/实际出力拟合；市政管网用 D-town 公开基准（CC BY-NC 4.0）
- 失效源：**市政配水节点压头 < 28 m**，无法为高位补水箱补水
- 影响指标：**少发功率 (MW) + 损失电量 (MWh)**（与文献一致）
