# figures/ —— 论文插图集（Fig.1–Fig.11）

> 全部论文插图，按**正文首次引用顺序**编号，与小节序号呼应（详见 `../docs/figure_design.md`）。
> **出版规范（全图统一）：** 全英文标注；统一无衬线字体 **Arial 族**（环境回退 Liberation Sans / DejaVu Sans）；分辨率 **≥ 300 dpi**。
> **格式：** 概念图 Fig.1–3 提供 **SVG（矢量）+ PNG（300 dpi）** 两份；Fig.4–11 为 **PNG @ 300 dpi**。matplotlib 图统一样式见 `../src/figstyle.py`。
> **注：** 原独立的「三域三级 ICS 架构图」（旧 Fig.4）已合并入 **Fig.1**（其信息层已含三域三级 ICS + 跨域预警链路），原图删除，后续图号顺延；图数 12→11。

| 图号 | 文件 | 类型 | 锚定小节 | 服务 | 生成方式 |
|---|---|---|---|---|---|
| Fig.1 | `Fig1_CPS_framework.svg` | 概念·框架（含 ICS 架构）| §2.1 / §2.4 | 全文骨架 + 信息侧 | 手绘 SVG |
| Fig.2 | `Fig2_cooling_water_chain.svg` | 概念·流程 | §2.3 | **创新点 1** | 手绘 SVG |
| Fig.3 | `Fig3_timescale_gap_mechanism.svg` | 概念·机制 | §2.4 | **创新点 2** | 手绘 SVG |
| Fig.4 | `Fig4_coupling_topology.png` | 拓扑（三面板平面图：(a) D-town 水网 / (b) IEEE-118 单线图 / (c) 级联抽取）| §3.1 | 案例可复现 | `src/figures_concept/fig4_coupling_topology.py` |
| Fig.5 | `Fig5_muni_staggered_depressurization.png` | 结果·时序 | §4.1 | 支撑（边界）| `src/00_muni_wdn/plot_muni.py` |
| Fig.6 | `Fig6_network_outage_spatiotemporal.png` | 结果·时空 | §4.1 | 支撑（边界）| `src/00_muni_wdn/plot_network_outage.py` |
| Fig.7 | `Fig7_cooling_chain_timeseries.png` | 结果·时序 | §4.2 | **创新点 1 结果** | `src/01_cooling_chain/plot_results.py` |
| Fig.8 | `Fig8_early_warning_comparison.png` | 结果·对比 | §4.3 | **创新点 2 核心** | `src/02_ics/plot_ics.py` |
| Fig.9 | `Fig9_PA_SP_DP_strategies.png` | 结果·对比 | §4.4 | 创新点 2（策略）| `src/03_proactive_control/plot_p6.py` |
| Fig.10 | `Fig10_depressurization_time_distribution.png` | 敏感性·分布 | §5.1 | 支撑（回应配对）| `src/00_muni_wdn/plot_saet_distribution.py` |
| Fig.11 | `Fig11_intake_node_sensitivity.png` | 敏感性·对比 | §5.2 | 支撑（稳健性）| `src/03_proactive_control/plot_node_sensitivity.py` |

## 说明
- **本目录是全项目唯一的成图集（canonical figure library）**，论文入稿与报告内嵌均以此为准；`results/` 仅保留数据（json/csv/db），不再存图片副本，避免重复。
- **概念图（Fig.1–3）** 为手绘矢量 SVG（源即本目录）。其中 **Fig.1 已并入原 ICS 架构图的三域三级 ICS 信息**，一图兼作系统总框架与信息架构。
- **结果图（Fig.4–11）** 由脚本生成（Fig.4 见 `src/figures_concept/`，Fig.5–11 见各模块 plot 脚本，均 **dpi=300**）。
- **重出与更新：** 重跑对应脚本会在 `results/` 各子目录写出 PNG（可再生的中间产物）；确认无误后复制并按上表重命名覆盖到本目录。`make_report.py` 生成报告时**直接从本目录读图**（旧文件名→Fig 文件名的映射见脚本 `_FIGMAP`）。
- 图—章节—论证功能的完整对应见 `../docs/figure_design.md` 的「1bis 图—框架章节对应」。
