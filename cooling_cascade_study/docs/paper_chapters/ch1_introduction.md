# 1 引言 Introduction

> 正稿章节草稿 v2（2026-09-07，语言润色版：仅优化行文与段落，数字/引注/事实性表述未动）。本章为叙述性章节，文中全部事实性数字（485.6 MW/49.1 MWh、88.6–124.8 min、0.55 %Pg/min、k\*=3 等）已在第 3/4 章逐项溯源核验；新增参考文献 [18]–[21]（火电冷却水依赖与相互依赖综述文献群）经本轮逐篇检索核实（卷期页码 DOI 见文末），用于支撑"研究缺口"与"首次"断言的限定式表述。参考文献编号沿用既定体系 [1]–[17]，新增 [18]–[21] 接排（合稿时按全文首次出现顺序统一重排）。

## 1.1 背景：水-电信息物理双重耦合

电厂循环冷却水系统是城市供水管网与电力系统之间一条长期被简化的物理纽带：常规燃煤汽轮机组的循环冷却水需持续补水以弥补蒸发、排污与风吹损失，该补水通常取自市政配水管网；与此同时，电厂冷却水系统与市政管网又各自处于工控系统（ICS/SCADA）的监控之下。两套基础设施由此构成**物理经冷却水、信息经 ICS 的双重耦合**的水-电信息物理耦合系统（CPS）。

这一耦合在极端条件下已被反复激活。近年来，欧美已多次出现火电/核电机组因冷却水温度升高、河流流量下降而减产或临时停机 [18]；van Vliet 等 [18] 的评估进一步预测，2031–2060 年欧美火电容量将因冷却水缺乏平均下降 4%–19%（直流冷却机组最脆弱）；Macknick 等 [19] 系统梳理了各发电技术的取水与耗水系数，Bartos 与 Chester [20] 则量化了气候变化下美国西部电网的供水-供电联合脆弱性。

另一侧，城市供水系统自身的水源/管网事故（爆管、水厂故障、停电反噬）亦可能同时切断多台机组的冷却补水，形成**共因失效**。然而，既有相互依赖研究多以一条直接耦合边（"停水→停机"）代替冷却水中间过程 [2,3,21]，忽略了"市政失压"与"机组跳机"之间**可资利用的缓冲时间**。由此引出本文的核心科学问题：**市政供水失效经电厂冷却链传导为电力缺额的过程有多慢？这一时间差能否在机组跳机之前被跨域信息与主动控制所利用？该利用的物理边界又何在？**

## 1.2 相关工作与研究缺口

与本文相关的研究可归为四条线索：

**（i）相互依赖基础设施与水-电级联建模。** Ouyang [21] 将该领域方法学分为经验、代理、系统动力学、经济理论与网络化六类；Li 与 Zhang [2] 以功能耦合边连接真实城市供水网与 IEEE 标准电力系统做级联失效分析；Wang 等 [3] 以 HLA 联邦架构实现跨域共仿真。**共同局限**：耦合边普遍为"供水失效→机组停运"的直接映射（拓扑/概率/仿真细节各异），电厂侧冷却水过程本身未被建模。

**（ii）火电冷却水依赖与热浪降额。** van Vliet 等 [18]、Macknick 等 [19]、Bartos 与 Chester [20] 系统研究了气候-水文驱动下的冷却水温度/流量约束对出力的影响。**共同局限**：关注**气候慢变量**（热浪、干旱、水温）驱动的取水条件恶化，服务于选址与容量规划；未建模**故障快事件**下厂内储水动态，亦未接入"市政管网故障→预警→主动控制"闭环。

**（iii）冷却水-凝汽器热力工程。** 表面式凝汽器的 ε-NTU 换热、端差与背压特性有成熟的行业标准体系（HEI、ASME PTC 12.2 [11,12]；Dittus–Boelter 类传热关联 [13]）。**共同局限**：停留在部件级设计与试验方法层面，未作为系统级失效链的环节进入电网韧性分析。

**（iv）能源系统早期预警与主动控制。** Yu 等 [1] 针对气-电耦合系统提出 ALP/AET/SAET 早期预警指标与 PA/SP/DP 主动控制线性规划，实现缺额消除。**共同局限**：该范式止于气-电场景；水-电冷却水场景的缓冲物理（水储存于厂内集总容器，燃气管存则分布于管网之内）根本不同，该范式能否迁移、迁移后结论如何变化，尚无研究。

**缺口凝练**：既有工作**建模了冷却水的"结果"（停机）、跳过了冷却水的"过程"（储水-水力-换热-背压）；建模了气候"慢"驱动的降额、未建模故障"快"事件的级联；预警-主动控制范式止于气-电**。上述三条局限的交叠空白正是本文的切入点。

## 1.3 本文思想与贡献

本文的核心思想是：**冷却水缓冲使"市政失压"与"机组跳机"之间存在分钟-小时级时间差，而信息系统与电网控制的响应为秒级——若把这一慢-快时间差经跨域早期预警转化为主动控制窗口，即可在水侧故障演变为电力缺额之前完成对冲。** 主要贡献为：

1. **冷却水全过程的显式建模（据我们所知首次）**：在相互依赖水-电系统的早期预警韧性分析中，显式建模"市政配水节点→高位补水箱→集水池→循环水泵→凝汽器→低压缸→发电机"的冷却水全过程链（孔口-质量守恒-汽蚀-ε-NTU-背压降额-延时保护），超越既有"直接耦合边"范式（第 2、4.2 章）。
2. **慢-快时间差的定量化与利用**：提出气-水类比的 ASW/AET/SAET 指标体系与三域三级 ICS 跨域预警链路，以 LP 主动控制（PA/SP/DP）将时间差转化为韧性；发现临界降出力速率（0.55 %Pg/min）及其"降额自保护"负反馈——缓冲窗口可主动延长至 SAET 的 2.07 倍（第 2.3.3、4.2、4.3 章）。
3. **真实管网边界与可审计性**：以 D-town 真实城市管网生成失压边界，54 台机组全耦合确定性配对并 54/54 独立复验耦合规律；以两级缓冲位置不对称论证"市政侧只作边界"的方法论，并以取水位置敏感性（CO/DISP）与闭合水量账主动回应配对任意性与口径保守性（第 3、5.1、5.2、5.4 章）。
4. **有边界的结论**：以电侧 N-k 扫描与全序级联划定主动控制的适用边界——同时失效机组数 k≤2 时缺额完全消除，k≥3 受备用与爬坡物理限制残留 95.6–128.2 MWh（临界失效规模 k\*=3）；由此提出跨域发现：水-电场景的韧性瓶颈自"信息速度"转移至"多机共因下的备用充足性与爬坡能力"（第 4.5、6.3 章）。

案例组织对齐参照文献 [1] 的两级递进：同源共因场景（三厂同时危机，CO）对应其城市级同源案例（Fig.5–6），多源错峰场景（54 节点全耦合、全序级联）对应其省级多端源案例（Fig.7）。

## 1.4 论文组织

本文余下部分组织如下：第 2 章建立四层物理链与信息层的完整数学模型（两个创新点的方法主体）；第 3 章介绍 IEEE-118 × D-town 测试系统、全耦合配对、参数标定及其规范出处；第 4 章沿"市政侧失压→冷却链时间差→预警价值→三策略→稳健性边界"主线呈现结果；第 5 章给出取水位置、失压速率、水量口径的系统敏感性分析；第 6 章讨论机理洞见、工程启示、与文献对比及局限；第 7 章结论。

## 本章参考文献

[1] Yu F, Guo Q, Wu J, Qiao Z, Sun H. Early warning and proactive control strategies for power blackouts caused by gas network malfunctions. *Nature Communications*, 2024, 15: 4714. DOI: 10.1038/s41467-024-48964-0.

[2] Li Y, Zhang M. Cascading failure analysis of interdependent water-power networks based on functional coupling. *Reliability Engineering and System Safety*, 2025, 259: 110950.

[3] Wang F, Magoua J J, Li N. Modeling cascading failure of interdependent critical infrastructure systems using HLA-based co-simulation. *Automation in Construction*, 2022, 133: 104008.

[11] Heat Exchange Institute. Standards for Steam Surface Condensers. Cleveland, OH: HEI.

[12] ASME. ASME PTC 12.2, Steam Surface Condensers (Performance Test Code). New York: ASME.

[13] Dittus F W, Boelter L M K. Heat transfer in automobile radiators of the tubular type. *University of California Publications in Engineering*, 1930, 2(13): 443–461.

[18] van Vliet M T H, Yearsley J R, Ludwig F, Vögele S, Lettenmaier D P, Kabat P. Vulnerability of US and European electricity supply to climate change. *Nature Climate Change*, 2012, 2: 676–681. DOI: 10.1038/nclimate1546.

[19] Macknick J, Newmark R, Heath G, Hallett K C. Operational water consumption and withdrawal factors for electricity generating technologies: a review of existing literature. *Environmental Research Letters*, 2012, 7(4): 045802. DOI: 10.1088/1748-9326/7/4/045802.

[20] Bartos M D, Chester M V. Impacts of climate change on electric power supply in the Western United States. *Nature Climate Change*, 2015, 5(8): 748–752. DOI: 10.1038/nclimate2648.

[21] Ouyang M. Review on modeling and simulation of interdependent critical infrastructure systems. *Reliability Engineering & System Safety*, 2014, 121: 43–60. DOI: 10.1016/j.ress.2013.06.040.

（编号沿用第 2/3 章既定体系，新增 [18]–[21] 接排；[11]–[13] 已在第 2/3 章详引，此处列本章正文直接引用条目。）
