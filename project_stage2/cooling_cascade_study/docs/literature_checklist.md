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

---

## 待补充：核心参数来源表
| 参数 | 来源（待填） |
|---|---|
| IEEE 118 发电机 H, Xd' | |
| 调速器/励磁参数 | |
| 凝汽器换热参数 | |
| 高背压保护定值 | |
| UFLS 分级定值 | |
