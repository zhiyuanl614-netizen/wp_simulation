# 电厂冷却水故障级联影响动态仿真研究

**项目代号：** `cooling_cascade_study`
**建立日期：** 2026-07-06
**研究目标：** 考虑电厂冷却水系统故障后，对发电机组本体及电网的级联影响，开展不同时序下的动态仿真研究。

> 本项目与 `ieee118_dc/`（IEEE 118 直流潮流算例）相互独立，仅在需要电网拓扑/参数时复用其数据。

## 目录结构

```
cooling_cascade_study/
├── README.md                     本文件（项目导航）
├── docs/
│   ├── research_plan.md          初步研究方案（核心文档）
│   ├── parameter_fitting.md      参数拟合与来源登记表（无现场数据→按标准/出力拟合）
│   └── literature_checklist.md   文献调研清单
├── models/
│   ├── model_specification.md    多时间尺度建模规范（W→A→B→C 四层）
│   └── water_side_model.md       水源侧水力学子模型（市政断水→补水箱→集水池→循环水）
├── scenarios/
│   └── scenario_matrix.csv       仿真场景 / 时序矩阵
├── p1_smib/                      P1 阶段代码（SMIB 最小闭环仿真）
│   ├── README.md  params.py  submodels.py  simulate.py  plot_results.py
├── p3_ieee118/                   P3 阶段代码（IEEE 118 全系统级联）
│   ├── README.md  network.py  cascade.py  run_p3.py  plot_p3.py
├── p4_resilience/                P4 早期预警韧性量化（最终研究目标）
│   ├── README.md  compare_warning.py  sweep_leadtime.py
├── ics/                          ★ 工业控制系统(信息系统)三级ICS —— 预警内生化
├── p5_map/                       ★ P5 全场景韧性图谱 + 最优策略 + 预警可靠性
│   ├── README.md                 P5 说明与核心结论
│   ├── resilience_map.py         预警提前量×故障规模 韧性图谱
│   ├── optimal_strategy.py       最优预警-处置策略（预置备用+预防性切负荷）
│   ├── build_lookup.py           预计算 f_nadir 查找表
│   └── reliability.py            预警可靠性/鲁棒策略 蒙特卡洛
└── results/                      仿真结果（CSV + PNG + JSON + 事件日志）
```

## 进度（P0→P5 研究闭环）

- ✅ **P0** 方案 / 建模规范 / 参数策略 / 场景矩阵
- ✅ **P1** SMIB 最小闭环——打通"市政断水→水位下降→跳泵→背压上升→跳机→频率响应"全链条（见 `p1_smib/`）
- ✅ **P3** IEEE 118 全系统级联——QSS 交流潮流 + 一次调频 + 过载跳线，量化单机 vs 同源多机共因差异（见 `p3_ieee118/`）
- ✅ **P4** 早期预警韧性量化——被动 vs 主动预警对比，量化"预警提前量→韧性"，**命中最终研究目标**（见 `p4_resilience/`）
- ✅ **P5** 全场景韧性图谱 + 最优预警-处置策略——临界预警窗口、预警替代切负荷（见 `p5_map/`）
- ✅ **P5+** 预警可靠性/鲁棒策略——漏报/时延抖动/误报下的蒙特卡洛风险评估，鲁棒托底策略（见 `p5_map/reliability.py`）
- ✅ **ICS** 三级工业控制系统（PLC/SCADA/调度 + SQLite）——把预警**内生化**为信息系统输出（检测策略 A/B/C/D 决定预警提前量），见 `ics/`

## 最终研究目标（一句话）

利用**水力慢动态提供的分钟级预警窗口**，经 ICS 把市政水网故障信息提前告知电网，使其在机组跳闸前**主动预置备用**——把频率崩溃（45.6 Hz）转为可控事件（49.4 Hz），**韧性增益 +3.72 Hz**。

## 快速入口

- 想看整体思路 → `docs/research_plan.md`
- 想看建模细节 → `models/model_specification.md`
- 想看仿真场景设计 → `scenarios/scenario_matrix.csv`
- 想看要读的文献 → `docs/literature_checklist.md`

## 一句话概述

**市政水网故障（补水中断）** → 高位补水箱/集水池水位下降 → 循环水泵流量下降/汽蚀跳泵 → 凝汽器真空恶化、低压缸背压升高 → 机组高背压保护跳闸 → 电网功率失衡（频率/电压/潮流）→ 保护级联。本研究通过**水力-热力-机械-电气多时间尺度耦合动态仿真**量化上述链条并评估电网韧性。

## 已确定的研究范围

- 机组：常规燃煤汽轮机组，聚焦**凝汽器—低压缸**（不含锅炉慢动态）
- 电网：固定 **IEEE 118**（复用 `ieee118_dc/`）
- 数据：**无现场数据**，动态参数按国家/国际标准 + 额定/实际出力**拟合**
- 故障源：**市政水网故障**，细化水源侧水力学，临界设备为**高位补水箱**
- 精度/重点：**机电暂态 RMS** + **机理揭示**（少量场景深挖）
