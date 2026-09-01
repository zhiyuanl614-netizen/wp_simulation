# 文献调研清单（P0 阶段）

**目的：** 支撑建模假设、参数取值与方法选型。分主题列出需检索的方向与关键词。

## 1. 电厂冷却水/凝汽器故障机理
- 关键词：condenser vacuum degradation, circulating water pump trip, condenser performance, cooling water failure power plant
- 关注：真空恶化对机组出力/效率影响、高背压保护逻辑、循环水泵故障工况

## 2. 汽轮机背压—功率特性
- 关键词：turbine back-pressure correction curve, exhaust pressure effect on turbine output, LP turbine performance
- 关注：背压—微增出力率关系、汽轮机保护定值（低真空跳机）

## 3. 电力系统级联故障 / 韧性
- 关键词：cascading failure power grid, blackout mechanism, power system resilience, RoCoF frequency nadir
- 关注：级联建模方法、保护连锁、UFLS、临界条件识别

## 4. 发电厂—电网耦合 / 多时间尺度仿真
- 关键词：plant-grid coupled dynamic simulation, co-simulation Modelica power system, thermal-electrical coupling, multi-timescale simulation
- 关注：热力-电气联合仿真框架、FMI 联合仿真、DAE 刚性求解

## 5. 仿真工具与数据
- 关键词：ANDES power system simulator, IEEE 118 dynamic data, TGOV1 IEEEG1 exciter model, ThermoPower Modelica
- 关注：开源动态仿真平台、IEEE 118 动态参数集、标准调速/励磁模型

## 6. 辅助系统对电网安全的影响（较新方向）
- 关键词：auxiliary system failure generating unit, common-cause plant trip grid impact, extreme heat water intake power plant
- 关注：极端高温/水资源对火电的影响、共因故障

## 7. 参照文献故障来源结构与本项目对齐（同源 vs 多源）
参照文献 Yu et al., Nat. Commun. 15:4714 (2024) 有**两级案例**，故障来源结构不同：
- **城市系统 Fig.5–6（同源）**：单一气源 GS 故障同时切断 HZ、XS 两厂供气 → 同源共因故障（一个故障点、多台受影响机组）。用于讲机制。
- **省级系统 Fig.7（多源）**：省级气网采用 multiend gas sources（多端源）结构，模拟多气源+多管线**同时故障** → 12 台燃气机组中 6 台受影响，SAET 随与故障点距离从数分钟到数小时不等。用于讲规模效应（N-1 原则失效、共因故障）。

**本项目对齐：**
- **同源** → `src/03_proactive_control/`：单一市政总源/配水点失效累及同源多机（参数化 `ramp`），对齐 Fig.5–6。
- **多源错峰** → `src/00_muni_wdn/`：用真实基准配水网 D-town（C-town 的带真实需水量改进版）仿真，市政总源压力失效经不同 DMA 分区缓冲，各电厂配水节点在不同时刻跌破 28 m → 各机组不同 SAET，对齐 Fig.7。
- **市政水网只作上游边界生成器**：因本项目缓冲（ASW）在电厂内部、不在管网里（缓冲位置不对称，与文献气网 line pack 分布在管网内不同），故只需用管网仿真生成 `H_muni_i(t)` 边界，不耦合进下游求解。
- 数据来源：D-town，Ostfeld (2016), Battle of the Water Network Models, Univ. of Kentucky, CC BY-NC 4.0, https://uknowledge.uky.edu/wdst_models/5（D-town 自带真实城市需水量与日变化模式；C-town 导出版需水为 0，已弃用）

---

## 待补充：核心参数来源表
| 参数 | 来源（待填） |
|---|---|
| IEEE 118 发电机 H, Xd' | |
| 调速器/励磁参数 | |
| 凝汽器换热参数 | |
| 高背压保护定值 | |
| 市政配水管网基准 | D-town, Ostfeld 2016, UKnowledge wdst_models/5 (CC BY-NC 4.0) |
