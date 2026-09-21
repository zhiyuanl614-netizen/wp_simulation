# muni_wdn —— 市政供水管网边界生成器

**角色：上游边界生成器（不与下游耦合求解）。** 用真实基准配水管网 **D-town** 的水力仿真，生成各电厂配水节点的压头轨迹 `H_muni_i(t)`，经"最小供水阈值 28 m"判据得到各电厂供水失效时刻 `t_fault_i`（**多源错峰失压**）。取水点不硬编码——一律从 `results/muni/coupling_map.json`（单一真源）读取。下游冷却水/电力/主动控制模型完全不变，只把失效时刻（及等效 ramp）作为边界参数读入。

## 为什么市政水网只作边界、不耦合进下游

**缓冲位置不对称（关键论证）：** 参照文献气网必须做网络水力仿真，因为缓冲（line pack 管存气）分布在管网内，AET/SAET 由管存气算出。本项目缓冲（可用储水量 ASW）在**电厂内部**（补水箱+集水池），是集总的、不在市政管网里。故市政管网对下游只是一个**压力边界**，不承载下游需要的缓冲物理——用它生成 `H_muni_i(t)` 即充分。

## 为什么用 D-town（而非 C-town）

同一 BWN 系列的 **C-town 导出版 `[JUNCTIONS]` 需水量全为 0、无城市负荷**（校准用拓扑骨架），需人为补背景负荷才能让水箱排空——引入人为成分。**D-town 是 C-town 拓扑的带真实需水量改进版**（2013 BWN 长期改进竞赛）：399 个 junction 中 **348 个有真实需水、5 条日变化需水模式**（另 51 个基础需水为 0，系纯过流/占位节点，不可作电厂取水点——见耦合映射硬过滤 F1）、7 个分区水箱、单水库总源。城市负荷真实，无需人为补充——这消除了 C-town 版的唯一不真实成分。

## D-town 基准模型

单水库 R1（市政总源）+ 11 泵 + 7 水箱（T1–T7，分区缓冲）+ 399 节点 + 443 管段 + 5 阀，分层 DMA 结构，含真实城市需水量。

**故障施加（水源压头下降，两个口径）：**

| 口径 | 施加方式 | 用途 |
|---|---|---|
| **B-ST 合成阶跃** | R1 于 t=0 压头置零 | 耦合登记（`coupling_map.py`）、全网失压分布（`saet_distribution.py`）、全网压力崩溃（`network_outage.py`） |
| **B-RT 渐降** | R1 自 t=6 h 起 3 h 内线性降至近零 | 下游边界 `t_fault_i`（`boundary_generator.py` / `full_coupling_boundary.py`）、闭合水量账（`closed_water_balance.py`） |

相比硬切管道更贴合"市政供水压力失效"的物理本意，且保持水力求解良态（D-town 的 11 泵在硬切总源后会进入不稳定工况使 EPANET 求解崩溃）。

## 同源 vs 多源（对齐文献两级案例）

| | 文献 | 本项目 |
|---|---|---|
| 同源 | Fig.5–6：单气源 GS 故障累及多厂 | 单一市政总源/配水点失效累及同源多机（基线，`src/03_proactive_control/` 参数化 `ramp`）|
| 多源错峰 | Fig.7：多端源省级案例，6 机不同 SAET | 市政总源失效经不同 DMA 缓冲，各配水节点错峰失效、各机组不同 SAET（本模块 D-town 真实生成）|

## 指定耦合映射（v2，coupling_map.py）

耦合集合为**研究者指定的 6 对**：6 台大出力凝汽式机组（bus 89/80/10/66/65/26，ΣPg＝2631 MW）↔ 6 个真实供水节点（J102/J97/J198/J5/J217/J177，均属 DMA1 分区），**rank↔rank 确定性配对**（取水节点按 B-ST 失压时刻升序 × 机组按 Pg 降序，一一配对——失压最快的节点配最大机组，构成最保守组合）。三条硬过滤固化于脚本（不合格即断言失败）：

| # | 硬过滤 | 判据 | 目的 |
|---|---|---|---|
| F1 | 需水非零 | `demand_base_Lps > 0` | 必须真实供水 |
| F2 | 故障前健康 | 无故障 24 h EPS 全程最小压头 > 32 m | 排除基线即病态节点 |
| F3 | 失压可触发 | B-ST 72 h 内存在 H < 28 m 事件 | 级联可发生 |

> v1（54 台全耦合 + Q1–Q5 失压时刻分层比例抽样）已废弃：IEEE-118 的 54 条机组登记中 35 台 Pg＝0（调相机/占位调度点），D-town 399 节点中 51 个零需水——二者均不构成有效耦合主体。设计与重构依据见 `../../docs/coupling_map.md`，重构后的全链复算见 `../../docs/verification/report_v2_20260915.md`。

## 脚本清单（v2：7 个计算脚本 + 3 个绘图脚本）

| 脚本 | 功能 | 输出 |
|---|---|---|
| `coupling_map.py` | 指定耦合映射（6 对 + 硬过滤校验） | `results/muni/coupling_map.{json,csv,png}` |
| `boundary_generator.py` | 6 指定取水节点 B-RT 渐降失压（读 coupling_map.json） | `results/muni/muni_boundary.json` |
| `saet_distribution.py` | 全网 399 节点失压时刻分布 + P10/P50/P90 代表节点（B-ST） | `results/muni/saet_distribution.json` |
| `network_outage.py` | 唯一水源停供 → 全网压力时空崩溃（B-ST） | `results/muni/network_outage.json` |
| `full_coupling_boundary.py` | 全耦合失效边界（B-RT）+ 一致性验证 + 补水可供性事后评估 | `results/muni/full_coupling_boundary.json` 等 |
| `closed_water_balance.py` | 闭合水量账（城市轨迹 → 电厂补水阀，物理补水口径） | `results/muni/closed_water_balance.{json,csv}` |
| `verify_coupling_rule.py` | 耦合规律 R1/R2/R3 逐节点独立复验（6/6） | `results/muni/coupling_rule_verification.{json,csv}` |
| `plot_muni.py` | Fig.5（6 取水节点错峰失压热力图） | `figures/Fig5_*.png` |
| `plot_network_outage.py` | Fig.6（全网压力时空崩溃） | `figures/Fig6_*.png` |
| `plot_saet_distribution.py` | Fig.12（全网失压时刻分布） | `figures/Fig12_*.png` |

## 运行

```bash
pip install wntr
cd src/00_muni_wdn
python coupling_map.py          # 耦合映射（单一真源，其余脚本依赖它）
python boundary_generator.py    # 6 指定取水节点 B-RT 边界
python saet_distribution.py     # 全网失压时刻分布
python network_outage.py        # 唯一水源停供 → 全网压力崩溃
python full_coupling_boundary.py
python closed_water_balance.py
python verify_coupling_rule.py
python plot_muni.py && python plot_network_outage.py && python plot_saet_distribution.py
```

## 两类分析

| 模块 | 焦点 | 输出 |
|---|---|---|
| `boundary_generator.py` / `full_coupling_boundary.py` | **6 个指定取水节点**的失压边界（供下游 t_fault_i 与可供性评估） | `muni_boundary.json` / `full_coupling_boundary.json` |
| `network_outage.py` / `saet_distribution.py` | **唯一水源完全停供**后**全网 399 节点**压力的时空崩溃与失压时刻分布 | `network_outage.json` / `saet_distribution.json` |

### 唯一水源停供 → 全网压力崩溃（network_outage）

- **停供施加（阶跃，自 t=0 起）**：水源 R1 压头自仿真起始时刻即降至近零并保持（唯一水源自始完全停供）。用"压头→0"而非"硬切出水管"：硬切会使 EPANET 稳态解在无水节点算出大量非物理负压（可达 −10⁴ m）；压头→0 + PDD + `minimum_pressure=0` 则物理正确——水源停供后由 7 个分区水箱储水续供，水箱逐级放空后所在区才真正失压。
- **物理正确性**：自 t=0 停供后压力**并不立即崩溃**——全网 7 个水箱靠储水续供，维持约 12 h（缓冲窗口）；随水箱见底，失压节点占比从初始 ~10% 扩大到 ~62%，**全网半数节点在停供后约 12.5 h 失压**，呈自水源向外的**空间扩散**。
- **可视化**（`plot_network_outage.py` → Fig.6）：① 全网压力统计（均值/P10–P90/中位）随时间；② 失压节点占比随时间；③–⑥ 4 个时刻的空间快照（节点坐标着色压力，蓝=健康、红=失压）。

## 方法与说明（如实标注）

1. **EPANET 2.2 EPS**：扩展时段准稳态（分钟级），与失压传导尺度（SAET，分钟~小时）一致；水质(水龄)分析关闭，只解水力。
2. **压力驱动需水（PDD）**：压力不足时供水量按物理削减（`required_pressure=20 m`、`minimum_pressure=0`）。
3. **真实城市需水量**：D-town 自带 348 节点真实需水 + 5 条日变化模式——图中昼夜起伏即真实日变化需水所致（高区水箱夜间重力供水），无需人为补背景负荷。
4. **失效取首次跌破**：各配水节点随其供区水箱逐级耗尽而先后失效，下游只取各节点**首次**跌破 28 m 的时刻并锁存（不因后续波动复位）。

## 数据来源（CC BY-NC 4.0，须署名）

Ostfeld, Avi. *"05 Long Term Improvement" (D-town)* (2016). Battle of the Water Network Models. University of Kentucky Libraries. https://uknowledge.uky.edu/wdst_models/5

数据文件 `data/DTOWN.inp`（位于仓库根 `data/` 目录）按 CC BY-NC 4.0 授权分发，非商业使用，须署名原作者与来源。
