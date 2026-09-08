"""
生成论文【简要版 / 骨架版】自包含 HTML（v2 修订版）。
- 依据 docs/paper_outline.md 的 7 章框架；
- 每章/小节只写一段"本部分主要讲什么"的概述（非完整正文）；
- 图片按 Fig 编号内嵌到相应位置（SVG 内联、PNG base64），图源 figures/；
- v2 修订（对齐孙宏斌 Nat.Commun. 2024 + 取张明媛/李楠文优点）：
  S1 被动vs主动对比表(Table 1, 镜像文献 Table 1)；
  S2 临界降出力速率数值算例(新 Fig.8, 镜像文献 Fig.3)；
  S3 两级案例叙事显式化；S4 结果汇总表(Table 4, 双指标报告法)；
  S5 SAET 保守下界口径正面化；S6 数据/代码可用性占位；
  S7 摘要规模语境+结论边界限定+限定式"首次"；
  Z1-Z3 敏感性章落实/场景依据/配对先例；L1-L3 可审计/事件标注/架构范式；
  C1 图号重排(13图)、C2 "18/24"表述修正、C4 SAET 口径标注。
输出: 论文简要版_骨架.html
"""
import os, base64

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def figure(fname, cap, width="88%"):
    """按扩展名内嵌图片，返回 <figure> HTML。"""
    p = os.path.join(FIG, fname)
    if not os.path.exists(p):
        return f'<figure><div class="missing">[缺图] {fname}</div><figcaption>{cap}</figcaption></figure>'
    if fname.lower().endswith(".svg"):
        with open(p, "r", encoding="utf-8") as f:
            svg = f.read()
        inner = f'<div class="svgbox" style="max-width:{width}">{svg}</div>'
    else:
        inner = f'<img style="width:{width}" src="data:image/png;base64,{_b64(p)}" alt="{cap}">'
    return f'<figure>{inner}<figcaption>{cap}</figcaption></figure>'


CSS = """
:root{--ink:#1a2b3c;--mut:#5b6b7a;--line:#e2e8f0;--accent:#1f6fb2;--soft:#f7fafc;--gold:#b9770f;}
*{box-sizing:border-box}
body{font-family:-apple-system,"Noto Sans CJK SC","Microsoft YaHei",Segoe UI,sans-serif;
 color:var(--ink);line-height:1.85;margin:0;background:#eef2f6;}
.wrap{max-width:900px;margin:0 auto;background:#fff;box-shadow:0 1px 20px rgba(0,0,0,.06);}
header{background:linear-gradient(135deg,#123a5c,#1f6fb2);color:#fff;padding:50px 60px 40px;}
header .badge{font-size:12px;letter-spacing:2px;opacity:.85;text-transform:uppercase;}
header h1{margin:12px 0 6px;font-size:26px;line-height:1.35;font-weight:700;}
header .en{font-size:14px;opacity:.9;font-style:italic;}
header .meta{margin-top:18px;font-size:12.5px;opacity:.85;border-top:1px solid rgba(255,255,255,.25);padding-top:14px;}
main{padding:26px 60px 60px;}
.note{background:#fff8e6;border-left:4px solid var(--gold);padding:10px 16px;margin:14px 0;
 font-size:13px;color:#6b4e12;border-radius:4px;}
h2{font-size:21px;margin:34px 0 6px;padding-bottom:8px;border-bottom:2px solid var(--accent);color:#123a5c;}
h3{font-size:16px;margin:22px 0 4px;color:#1f6fb2;}
p.summary{margin:6px 0 4px;}
p.summary::before{content:"【本节概述】";color:var(--accent);font-weight:700;margin-right:6px;}
.tag{display:inline-block;background:#eaf3fb;color:#1f6fb2;font-size:11px;border-radius:10px;
 padding:1px 9px;margin-left:8px;vertical-align:middle;}
.tag.inno{background:#eafaf1;color:#1e8449;}
figure{margin:18px 0;text-align:center;background:var(--soft);border:1px solid var(--line);
 border-radius:8px;padding:14px;}
figure img,.svgbox{display:block;margin:0 auto;}
.svgbox svg{width:100%;height:auto;}
figcaption{font-size:12.5px;color:var(--mut);margin-top:10px;text-align:center;}
.missing{color:#c0392b;padding:40px;font-size:13px;}
.toc{background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:14px 22px;margin:18px 0;}
.toc b{color:#123a5c;}
.toc ol{margin:6px 0 0;padding-left:22px;font-size:13.5px;}
table.paper{width:100%;border-collapse:collapse;margin:14px 0 6px;font-size:12.5px;}
table.paper caption{caption-side:top;text-align:left;font-size:12.5px;color:#123a5c;
 padding-bottom:6px;font-weight:700;}
table.paper th{background:#eaf3fb;color:#123a5c;padding:6px 8px;border:1px solid #cfe0ee;font-weight:600;}
table.paper td{padding:5px 8px;border:1px solid var(--line);text-align:center;line-height:1.6;}
table.paper td.l{text-align:left;}
table.paper tr:nth-child(even) td{background:#fafcfe;}
.tblnote{font-size:11.5px;color:var(--mut);margin:0 0 12px;}
footer{padding:20px 60px 40px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);}
"""

HTML = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>论文简要版（骨架 v2）— 基于早期预警的冷却水耦合水-电信息物理系统韧性提升</title>
<style>{CSS}</style></head><body><div class="wrap">

<header>
  <div class="badge">Paper Draft · 简要版（骨架 · v2 修订）</div>
  <h1>基于早期预警的冷却水耦合水-电信息物理系统韧性提升</h1>
  <div class="en">Early-warning-based resilience enhancement of cooling-water-coupled water–power cyber-physical systems</div>
  <div class="meta">本文档为<b>简要版（骨架）</b>：每章/小节仅以一段概述说明"本部分主要讲什么"，并将对应图片置于相应位置；<b>不含完整正文</b>。完整框架见 <code>docs/paper_outline.md</code>，图件设计见 <code>docs/figure_design.md</code>。v2 修订要点：对齐孙宏斌文范式（Table 1 对比表、临界降出力速率算例、双指标结果汇总表、两级案例叙事、数据/代码可用性占位）+ 嫁接张明媛/李楠文优点（敏感性章、场景依据、可审计数据、事件时刻标注）。全文 <b>13 图 4 表</b>。</div>
</header>

<main>

<div class="toc">
  <b>目录</b>
  <ol>
    <li>引言（含相关工作与研究缺口）</li>
    <li>方法（CPS 框架 / 市政边界 / 冷却水机理链 / 信息系统 / 主动控制）</li>
    <li>案例与参数</li>
    <li>结果</li>
    <li>敏感性分析</li>
    <li>讨论</li>
    <li>结论</li>
  </ol>
</div>

<div class="note">写作约定：以 <b>【本节概述】</b> 标出的段落为占位性说明，后续按此展开为完整正文。图片已按 Fig 编号（首次引用顺序）内嵌到目标位置；表格为实内容版（数据取自 <code>results/</code> 存档，正稿期仅需排版转换）。</div>

<h2>摘要 Abstract</h2>
<p class="summary">概述电厂冷却水取自市政供水形成的<b>水-电信息物理耦合系统（CPS）</b>；指出既有研究直接把水网与机组作为级联对象、忽略冷却水中间过程的缺口；提出"利用供水慢动态与电力快动态的<b>时间差</b>、经信息系统快响应转化为<b>主动控制窗口</b>以提升韧性"的核心思想。给出关键量化结论：无预警时单机跳机造成 <b>485.6 MW 少发 / 49.1 MWh 损失</b>（≈ IEEE-118 总负荷 4242 MW 的 11.4%），经信息系统预警 + 主动控制降为 <b>0/0</b>；冷却缓冲窗口 SAET 88.6–124.8 min（合成阶跃保守下界口径；真实市政衰减轨迹下更长），临界降出力速率 0.55 %Pg/min 下运行时间可延长至 183 min（SAET 的 2.1 倍）。主动控制的适用边界：k≤2 台同时失效时缺额完全消除；k≥3 受备用/爬坡物理限制残留 95.6–128.2 MWh。末句给出两大创新点与跨域发现（冷却水储水缓冲天然长于燃气管存气，瓶颈自"信息速度"转移至"备用充足性"）。取水位置敏感性作为支撑性结论：全网失压时刻 0–67 h 分布（28% 节点不失压），分散取水使被动峰值 343→315 MW（危机时间隔离、峰值不叠加），主动控制对取水位置稳健（0/0）。</p>
<p style="font-size:12.5px;color:var(--mut)"><b>关键词：</b>water–power cyber-physical system; cooling water system modeling; early warning; resilience enhancement; slow–fast timescale gap; proactive control</p>

<h2>1　引言 Introduction</h2>
<p class="summary">说明本章按"背景 → 相关工作与缺口 → 本文思想与贡献 → 组织结构"四段递进；相关工作并入本章、不单独成章。</p>

<h3>1.1　背景（信息物理耦合系统视角）</h3>
<p class="summary">交代电厂循环冷却水依赖市政供水，物理经冷却水、信息经 ICS/SCADA 双重耦合成 CPS；以真实事件为钩子（极端高温/干旱期电厂因冷却水受限降额、城市供水事故引发停电的公开事例）引出核心问题——能否用信息系统快响应把慢-快时间差转化为主动控制窗口以提升韧性。</p>

<h3>1.2　相关工作与研究缺口</h3>
<p class="summary">沿四条线索综述并凝练缺口：(i) 水-电级联多用拓扑/概率耦合或协同仿真（张明媛、李楠），共同局限是用一条耦合边代替冷却水中间过程；(ii) 火电冷却水依赖与热浪降额文献群（thermoelectric water dependence：冷却水温/水量对出力的影响已用于选址与容量规划，但未建模<b>厂内储水动态</b>、亦未接入市政管网故障→预警→主动控制闭环）；(iii) 冷却水—凝汽器物理模型成熟但鲜少嵌入韧性分析；(iv) 能源早期预警（孙宏斌气-电）证明"缓冲时间→控制窗口"的价值但未及水-电冷却水场景。</p>

<h3>1.3　本文思想与贡献</h3>
<p class="summary">阐明核心思想（时间差→主动控制时间→韧性提升）与两大创新。创新点表述采用限定式：<b>据我们所知，在相互依赖水-电系统的早期预警韧性分析中，首次显式建模"市政配水节点→高位补水箱→集水池→循环水泵→凝汽器→低压缸→发电机"的冷却水全过程</b>（创新点 1）；利用信息系统快响应获取并利用两系统故障演化时间差（创新点 2）。并列出支撑性工作（真实管网边界、取水位置敏感性、N-k 稳健性边界）。</p>

<h3>1.4　论文组织</h3>
<p class="summary">概述全文 7 章结构与阅读脉络。</p>

<h2>2　方法 Methodology</h2>
<p class="summary">总述本章建立 CPS 四层耦合与信息层的完整方法体系，对应 <code>docs/mathematical_modeling.md</code>；两大创新点的方法主体分别落在 §2.3 与 §2.4。</p>

<h3>2.1　总体框架（水-电 CPS 四层 + 信息层）<span class="tag">全文骨架</span></h3>
<p class="summary">介绍四层（市政供水 / 冷却水 / 电力 / 影响指标）+ 贯穿信息层的耦合结构，强调"物理耦合=冷却水、信息耦合=ICS 预警链路"与多时间尺度（慢→快）；信息架构（三域三级 ICS + 跨域预警链路）对齐协同仿真文献的联邦架构图范式（李楠文 Fig.1）。</p>
{figure("Fig1_CPS_framework.svg", "图 1　水-电信息物理耦合系统（CPS）四层耦合总体框架（§2.1）")}

<h3>2.2　市政水网边界层</h3>
<p class="summary">说明以 D-town 基准管网为上游边界：失效判据（配水节点压头 &lt; 28 m）、EPANET EPS/PDD 仿真、以及"为何市政水网只作边界不耦合进下游"的缓冲位置不对称论证。<b>双口径定义（正稿前置）：</b>B-ST 合成阶跃边界（市政压头瞬时跌零，SAET 保守下界，主结果口径）与 B-RT 真实轨迹边界（城市压头渐降剖面驱动补水阀，SAET 更长，见 §5.4）。</p>

<h3>2.3　冷却水故障机理链 <span class="tag inno">创新点 1</span></h3>
<p class="summary">给出冷却水全过程建模：水力（质量守恒/孔口/NPSH）→ 热力（ε-NTU/Antoine）→ 背压降额 → 高背压保护跳机，并定义早期预警指标 AET/ASW/SAET（气→水类比：ALP→ASW、AET/SAET 同名同义）。此为创新点 1 的方法主体。指标的关键性质——存在<b>临界降出力速率</b>使运行时间最长（"降额自保护"负反馈），其数值算例见 §4.2 图 8。</p>
{figure("Fig2_cooling_water_chain.svg", "图 2　电厂冷却水系统物理过程链（创新点 1，§2.3）")}

<h3>2.4　信息系统层与慢-快时间差 <span class="tag inno">创新点 2</span></h3>
<p class="summary">阐述三域独立三级 ICS、市政压力检测与跨域预警链路（快响应）、预警触发时刻的选择论证；说明如何据此获取供水慢动态与电力快动态之间的时间差。此为创新点 2 的方法主体。三域三级 ICS 架构与跨域预警链路已并入总体框架图（见图 1 信息层），此处以图 3 聚焦时间差机制。<b>信息层简化声明（正稿显式化）：</b>单阈值检测（压头&lt;28 m，与失效判据同一阈值）、零时延、可靠传输——与参照文献口径一致并保证"有无预警"对照的干净性；全过程按传感器/执行器/告警/调度/跨域预警/快照六表写入 SQLite，可回放审计（对齐协同仿真文献的细粒度状态数据优点）。</p>
{figure("Fig3_timescale_gap_mechanism.svg", "图 3　慢-快动态时间差与早期预警机制（创新点 2，§2.4）")}

<table class="paper">
<caption>表 1　被动控制 vs 主动（早期预警驱动）控制对比（§2.4，对齐参照文献 Table 1）</caption>
<tr><th style="width:16%">属性</th><th>被动控制（无预警）</th><th>主动控制（早期预警）</th></tr>
<tr><td>使用信息</td><td class="l">仅电力系统自身（跳机后才知情）</td><td class="l">市政供水 + 电力跨域信息（配水节点压头 &lt; 28 m 即预警）</td></tr>
<tr><td>动作时刻</td><td class="l">机组跳机后（慢响应，受爬坡限制）</td><td class="l">市政失压即刻（零时延，快响应）</td></tr>
<tr><td>控制效果</td><td class="l">事后动用备用，深度缺额</td><td class="l">SAET 窗口内 runback 软着陆 + 备用预爬坡</td></tr>
<tr><td>影响（单机 bus89）</td><td class="l">485.6 MW / 49.1 MWh</td><td class="l">0 MW / 0 MWh（避免跳机）</td></tr>
</table>
<p class="tblnote">数据来源：results/ics/ics_warning_compare.json（NOWARN / WARN）。</p>

<h3>2.5　电力系统层与主动控制</h3>
<p class="summary">介绍电力侧建模：DC 潮流（PTDF）、两级备用（旋转+慢起机，语义与 ICS 模拟口径分别声明）、主动控制线性规划（PA/SP/DP 三策略），以及韧性/影响指标（少发功率 MW、损失电量 MWh 双指标，对齐参照文献报告口径）。</p>

<h2>3　案例与参数 Case Study &amp; Setup</h2>

<h3>3.1　测试系统与耦合配对</h3>
<p class="summary">介绍 IEEE-118（电，118 母线/186 支路/54 机/总负荷 4242 MW）× D-town（水，399 节点/单水库/7 分区水箱/真实城市需水）双网案例与取水节点↔电厂母线的<strong>全耦合</strong>配对：54 台发电机（含平衡机）各配一个取水 junction（保留已校验三对 + 基线健康筛选 + 分层比例抽样 + 确定性配对，消除指定配对任意性）。耦合规律全节点验证 54/54 通过（市政侧只反馈压头；&lt;28 m 此刻即失效；SAET 自该时刻起算）。可行性核查表明额定补水 299.7 L/s 反馈进基线即崩溃（水源出力仅 ~246 L/s），故边界采用语义①：补水不反馈进城市水力、按 PDD 事后评估可供性。<b>配对先例援引（诚实性）：</b>与两篇参照文献一致，配对为功能规则 + 确定性抽样（张明媛文同样采用真实城市水网 + IEEE-118 合成配对），其任意性由 §5 取水位置敏感性主动回应。</p>
{figure("Fig4_coupling_topology.png", "图 4　IEEE-118 × D-town 水-电耦合拓扑与耦合对（§3.1）：(a) D-town 水网（真实坐标）与 54 个耦合取水节点，按唯一水源停供后的失压时刻分层着色；(b) IEEE-118 单线图与 54 台耦合发电机（同分层着色圆环）；(c) 54 对确定性配对（左=取水节点按失压时刻排序，右=发电机母线与左侧耦合节点逐行对齐、连线水平，连线与左侧彩条按分层着色）。分层定义：Q1–Q4=失压时刻四分位（快→慢），Q5=72 h 内不失压；各层计数 Q1 (n=6) / Q2 (n=13) / Q3 (n=10) / Q4 (n=9) / Q5 (n=16)，共 54 对")}

<h3>3.2　参数标定与规范出处</h3>
<p class="summary">说明无现场数据下参数按国家/国际规范（GB/T 50102、DL/T 5339、HEI/ASME PTC 12.2）+ 机组额定/实际出力拟合，以"额定工况自洽"为标定约束；参数总表见 Table 2。</p>

<table class="paper">
<caption>表 2　参数总表（代表机组 bus89：Pg=607 / Pmax=707 MW；完整出处登记见 docs/parameter_fitting.md）</caption>
<tr><th style="width:34%">参数（左：含义/符号）</th><th>取值</th><th>出处/规范</th></tr>
<tr><td class="l">额定/实际出力 P<sub>max</sub> / P<sub>g</sub></td><td>707 / 607 MW</td><td>IEEE-118 gen.csv</td></tr>
<tr><td class="l">市政正常压头 / 最小供水阈值 H<sub>muni,0</sub> / H<sub>muni,min</sub></td><td>32 / 28 m</td><td>供水管网服务压力（失效源）</td></tr>
<tr><td class="l">高位补水箱底面积/容积（A<sub>tank</sub>）</td><td>30 m² / 120 m³</td><td>循环水事故补水缓冲</td></tr>
<tr><td class="l">集水池底面积/容积（A<sub>pool</sub>，停留 4.1 min）</td><td>1700 m² / ≈5100 m³</td><td><b>DL/T 5339</b>（3–5 min）</td></tr>
<tr><td class="l">额定循环水量 m<sub>cw0</sub>（设计温升 8 K）</td><td>0.0295·P<sub>max</sub> ≈ 21 m³/s</td><td><b>GB/T 50102</b>（8–10 K）</td></tr>
<tr><td class="l">循环总损失率（蒸发+排污+风吹）</td><td>≈2.2%</td><td><b>GB/T 50102</b>（2–3%）</td></tr>
<tr><td class="l">冷却塔冷幅 approach</td><td>5 K</td><td><b>GB/T 50102</b>（3–5 K）</td></tr>
<tr><td class="l">泵最小淹没深度/降额带</td><td>1.2 / 0.5 m</td><td>泵样本+循环泵保护</td></tr>
<tr><td class="l">设计/跳机背压 p<sub>b0</sub> / p<sub>b,trip</sub></td><td>5 / 15 kPa（≈3×设计）</td><td>HEI / 低真空保护规程</td></tr>
<tr><td class="l">背压出力率 γ / 保护延时 τ</td><td>0.02 kPa⁻¹ / 3 s</td><td>微增出力率 / 保护规程</td></tr>
<tr><td class="l">传热-流量指数 n（UA ∝ m<sub>cw</sub><sup>n</sup>）</td><td>0.8</td><td>Dittus–Boelter 类比</td></tr>
<tr><td class="l">旋转备用比例 r_frac（占受影响机组出力）</td><td>0.20</td><td>典型值</td></tr>
<tr><td class="l">慢起机备用到位时间 / 其余机组爬坡率 R<sub>i</sub></td><td>~15 min / ~0.01·P<sub>max</sub>·min⁻¹</td><td>典型值（两级备用语义见 §2.5）</td></tr>
<tr><td class="l">线路限值倍率/下限 κ / rate_floor</td><td>1.5 / 50 MW</td><td>由基准潮流派生</td></tr>
</table>
<p class="tblnote">规范符合性核验见 docs/parameter_fitting.md §4；SAET 口径注：88.6 min 为预警指标口径（warning_indicators），92.4 min 为闭合账登记口径（closed_water_balance），均为 B-ST 合成阶跃下的保守下界；跳机绝对时刻（故障自 t=1.0 min 起）cooling_chain 链 93.4 min（图 7）与 ICS 链 93.6 min（图 9）系两模块链积分步长与事件采样差异，机理与保护判据一致。</p>

<h3>3.3　场景矩阵</h3>
<p class="summary">给出场景设计：有/无预警 × PA/SP/DP × 同源/多源取水（Table 3）。<b>场景选择依据（对齐地震 PGA 分档范式）：</b>按"故障烈度（阶跃/渐降）× 范围（单机/同源多机/全网停供）× 应对（有无预警 × 三策略）"组织；烈度上限取唯一水源全停（D-town 单水库结构下的确定性极端事件），多源错峰由管网仿真自然生成。</p>

<table class="paper">
<caption>表 3　场景矩阵（S00–S08；边界口径除注明外均为 B-ST 合成阶跃）</caption>
<tr><th>场景</th><th>市政故障</th><th>范围</th><th>预警</th><th>策略</th><th>研究定位</th></tr>
<tr><td>S00</td><td>无故障</td><td>—</td><td>—</td><td>正常运行</td><td class="l">稳态基线</td></tr>
<tr><td>S01</td><td>阶跃断水</td><td>单机 bus89</td><td>NOWARN</td><td>被动</td><td class="l">核心-被动基准</td></tr>
<tr><td>S02</td><td>阶跃断水</td><td>单机 bus89</td><td>WARN</td><td>主动 runback</td><td class="l">核心-预警价值</td></tr>
<tr><td>S03</td><td>渐降 600 s</td><td>单机 bus89</td><td>WARN vs NOWARN</td><td>主动 vs 被动</td><td class="l">失压速率敏感性（§5.3）</td></tr>
<tr><td>S04–S06</td><td>断水</td><td>同源 3 机 89/80/10</td><td>NOWARN / WARN</td><td>PA / SP / DP</td><td class="l">三策略对比（对齐文献 Fig.5–6）</td></tr>
<tr><td>S07</td><td>N-k 组合跳闸</td><td>19 台有出力耦合机组</td><td>WARN</td><td>PA / SP</td><td class="l">稳健性边界（k=1–12，最坏+随机）</td></tr>
<tr><td>S08</td><td>按失压顺序级联（72 h）</td><td>19 台有出力耦合机组</td><td>WARN</td><td>PA / SP</td><td class="l">全序级联规模标度</td></tr>
</table>
<p class="tblnote">S07/S08 边界取自全耦合映射（B-ST 口径 t_fault_i + 各机 SAET_i）；扩展自 docs/scenario_matrix.csv。</p>

<h2>4　结果 Results</h2>

<h3>4.1　市政侧：多源错峰失压与全网压力时空崩溃</h3>
<p class="summary">展示同一水源失效经不同分区缓冲导致各取水节点错峰失压，以及唯一水源停供后全网压力自水源向外的时空崩溃，作为时间差的市政侧来源与边界真实性证据。<b>两级案例对应（对齐文献）：</b>多源错峰失压对齐参照文献 Fig.7 的多端源省级案例——各机组 SAET 因取水位置而异。并在物理补水口径（0.453 m³/s@707MW 按 Pmax 缩放）下评估市政备用可供性：72 h 需求 165.5 万 m³、PDD 可供 92.0%，分层 Q1 55.1% → never 100%（失压越快的层市政备用丧失越早）。</p>
{figure("Fig5_muni_staggered_depressurization.png", "图 5　唯一水源 R1 阶跃停供（t=0，B-ST 合成阶跃口径，与图 6 及 Q1–Q5 分层定义同一故障模型）后全部 54 个耦合取水节点的压力热力图（行＝取水节点并标注节点名，按失压分层 Q1–Q5、层内按首破阈值时刻排序，白线分层；色＝节点压力，与图 6 同色标 RdYlBu 0–80 m、失压呈红色；○ 为首破 28 m 阈值时刻，构成错峰失压前锋——38 节点于 0–67 h 依次跌破（Q1 含 3 个 t=0 瞬时初始解即失效节点），Q5 全程高于阈值，§4.1）。口径注：B-RT 真实轨迹口径（t=6 h 起 3 h 线性压降）为下游主动控制链（§4.4）与 §5.4 的输入口径，不在本图展示")}
{figure("Fig6_network_outage_spatiotemporal.png", "图 6　唯一水源 R1 阶跃停供（t=0，理想化最烈情形）→ 全网 399 节点压力时空崩溃（§4.1）：(a) 节点压力 P10–P90 带、均值与中位数（黑点线=28 m 阈值）；(b) 低于阈值节点占比——t=0 瞬时初始解即有 9.5% 节点低于阈值（阶跃的即时水力重分布），半网失效 +12.5 h，48 h 峰值 62.4%、72 h 末 56.4%（日内需水波动致非单调）；(c1)–(c4) 空间快照 2×2（t=0/12/24/48 h，色=节点压力，与图 5 同色标 RdYlBu 0–80 m；灰线=管段，■=水源 R1，▲=水箱）。口径注：本图与图 5 同为 t=0 阶跃停供（B-ST 主结果口径，时间零点一致）；B-RT 真实轨迹口径（t=6 h 起 3 h 线性压降）为下游主动控制链（§4.4）与 §5.4 闭合水量账的输入口径")}

<h3>4.2　冷却水故障机理链结果 <span class="tag inno">创新点 1 结果</span></h3>
<p class="summary">用时序结果证明冷却水储水缓冲把市政断水延迟约 SAET≈92 min 才传导到机组跳机，直观展示被忽略的冷却水过程如何"制造"可用时间差。<b>口径声明（正面化）：</b>主结果采用 B-ST 合成阶跃边界（保守下界）；B-RT 真实市政衰减轨迹下 SAET 显著更长（bus89：92 min vs 1809 min），故主结论偏保守（详见 §5.4）。</p>
{figure("Fig7_cooling_chain_timeseries.png", "图 7　冷却水故障机理链时序（创新点 1 结果，§4.2；bus89 阶跃断水 B-ST 口径。六面板：(a) 补水箱/集水池水位、(b) 循环流量、(c) 凝汽器背压、(d) 出力降额系数 k_p、(e) 机组出力、(f) 少发功率；竖虚线＝市政失压 t=1.0 min）。关键事件时刻（1 s 网格数据核实）：① 市政失压 t=1.0 min → ② 补水箱排空 t=5.2 min（此后集水池成为唯一缓冲）→ ③ t=71.8 min 集水池进入淹没不足降额带（<1.7 m），循环流量自额定线性降额 → ④ t=93.4 min 凝汽器背压越限 15 kPa（m_cw 已降至 36%，全程未触及 1.2 m 跳泵水位——流量降额先于水泵跳闸触发保护）→ ⑤ 高背压保护跳机 t=93.4 min（3 s 延时；SAET=92.4 min，闭合账口径）→ ⑥ 出力 607 MW→0、少发功率 607 MW")}
<p class="summary"><b>临界降出力速率数值算例（对齐文献 Fig.3）：</b>对代表机组 bus89 扫描降出力速率 r（出力按 r 线性降到零）：慢于临界速率（r &lt; r*）时机组在出力未降完前被强制跳机（储水消耗使冷却能力渐进劣化、背压越限触发，先于储水耗尽，跳机时残余 ASW 约 5–13%）；快于临界速率可主动停机；恰为临界速率时运行时间最长——T<sub>max</sub> = 183.3 min，为 SAET（88.6 min）的 2.1 倍。临界值 r* ≈ 0.55 %Pg/min（满出力降零时长 11000 s）。机理：降出力 → 凝汽器热负荷下降 → 蒸发/排污损失减少 → 储水消耗变慢（"降额自保护"负反馈）。该算例为 DP 策略（延长控制时间动用更多缓冲）提供物理依据。</p>
{figure("Fig8_critical_ramp_example.png", "图 8　临界降出力速率数值算例（§4.2，对齐参照文献 Fig.3）：(a) 不同速率下出力轨迹（粗红=临界速率；事件标记位于轨迹末端：●=主动停机、✕=强制跳机）；(b) 可用储水量 ASW 轨迹（✕=强制跳机时刻——储水消耗使冷却能力渐进劣化、背压越限触发，先于储水耗尽，故 ✕ 位于跳机时刻的残余水位）；(c) 运行时间随满出力降零时长的变化（★=临界点，虚线=SAET）")}

<h3>4.3　有无早期预警对比 <span class="tag inno">创新点 2 核心</span></h3>
<p class="summary">全文最核心结果：无预警时机组跳机造成 485.6 MW 少发 / 49.1 MWh 损失，经信息系统预警 + 主动控制降为 0/0，直接量化早期预警的韧性价值（对齐文献 Fig.5–6 城市级案例的机制演示定位）。该结论的条件与适用边界见 §4.5（k≥3 残留）。</p>
{figure("Fig9_early_warning_comparison.png", "图 9　有无早期预警对比（创新点 2 核心结果，§4.3）：市政水源中断（t=1.0 min 阶跃失压）下两情形对照。(a) 市政供水压头（32 m→0；28 m 失效阈值，t=1.1 min 检出并零时延送达预警）；(b) 集水池水位（无预警满出力持续消耗；有预警随 runback 减缓并趋稳；两情形均未触及 1.2 m 跳泵水位）；(c) 凝汽器背压（无预警爬升至 15 kPa 越限、93.6 min 强制跳机；有预警随热负荷下降回落）；(d) 功率缺额——无预警：峰值缺额 485.6 MW、损失电量 49.1 MWh（备用约 12 min 逐步补足）；有预警：检出即触发与备用爬坡速率匹配的 runback（15 min 降零）＋旋转/慢速备用预起机，全程零缺额、零跳机")}

<h3>4.4　主动控制三策略与韧性提升</h3>
<p class="summary">对比被动/静态主动/动态主动三策略：PA 343.3 MW / 71.9 MWh，SP/DP 完全消除缺额，说明主动控制随时间差充分利用而提升韧性（对齐参照文献 Fig.6 的三策略报告口径）。本案例 SAET 窗口（88.6–124.8 min）宽裕故 SP 即可达 0/0——其物理根源（冷却水储水缓冲长于燃气管存气）与边界条件见 §4.5 与 §6.3。</p>
{figure("Fig10_PA_SP_DP_strategies.png", "图 10　被动/静态主动/动态主动三策略对比（§4.4，同源 3 机 bus89/80/10 场景，LP 优化＋DC 潮流；PA＝被动、SP＝静态主动、DP＝动态主动）：(a) 系统功率缺额时序——PA 下三机组于各自 SAET（88.6/116.9/124.8 min）相继跳机，两度形成缺额（峰值 343.3 MW 与 216.2 MW，备用约 15 min 内回补归零）；SP/DP 经预警触发主动 runback，全程零缺额；(b) 受影响机组总出力（PA 相继跳机阶梯下降 vs SP/DP 自检出起受控降出力）；(c) 峰值功率缺额（PA 343 MW，SP/DP 0）；(d) 损失电量（PA 71.9 MWh，SP/DP 0）——本案例 SAET 窗口宽裕故 SP 即达 0/0，DP 与 SP 重合")}

<h3>4.5　主动控制的稳健性边界：电侧 N-k 跳闸扫描</h3>
<p class="summary">对 19 台有出力耦合机组（ΣPg=4377 MW）做 k=1–12 组合跳闸（最坏 top-k + 随机组合，DC 潮流 LP）：N-1/N-2 最坏可被主动控制完全吸收；k≥3 最坏受备用/爬坡物理限制残留 95.6–128.2 MWh（SP）；随机组合显著更轻——全部 24 组合中 18 个 SP 零缺额（含最坏 k=1/2；随机子集内部 16/18）。本节界定前述 0/0 结论的适用边界（临界失效规模 k*=3），是结果章的"划界"支点。</p>
{figure("Fig11_nk_scaling.png", "图 11　电侧 N-k 跳闸扫描（§4.5；54 台耦合机组中有出力的 19 台为总体，k＝1/2/3/6/9/12，每组取最坏子集（Pg top-k）＋3 个固定种子随机子集，LP 优化＋DC 潮流）：(a) 最坏子集能量缺额随 k 标度——PA 与 SP（以各机 SAET 软着陆）曲线、绿色带＝预警避免的缺额、灰虚线（右轴）＝失去出力；k≤2 时 SP 完全消除缺额，k≥3 起受备用/爬坡物理限制残留（最坏子集 95.6→128.2 MWh），即临界失效规模 k*=3；(b) 全部 24 项子集的能量缺额分布（○＝PA，□＝SP）——SP 零缺额 18/24 项，未消除者集中于大 k 的最坏/高失出力子集")}

<table class="paper">
<caption>表 4　结果汇总：峰值缺额（MW）/ 损失电量（MWh）/ 最大线路过载（MW）（双指标报告法，对齐参照文献；数据源 results/）</caption>
<tr><th style="width:30%">场景</th><th>策略</th><th>峰值缺额 MW</th><th>损失电量 MWh</th><th>最大过载 MW</th></tr>
<tr><td class="l" rowspan="2">单机 bus89（无预警 / 有预警）</td><td>被动 NOWARN</td><td><b>485.6</b></td><td><b>49.1</b></td><td>—</td></tr>
<tr><td>主动 WARN</td><td><b>0.0</b></td><td><b>0.0</b></td><td>—</td></tr>
<tr><td class="l" rowspan="3">同源 3 机 CO（89/80/10，同时危机）</td><td>PA 被动</td><td><b>343.3</b></td><td><b>71.9</b></td><td>163.4</td></tr>
<tr><td>SP 静态主动</td><td>0.0</td><td>0.0</td><td>36.8</td></tr>
<tr><td>DP 动态主动</td><td>0.0</td><td>0.0</td><td>36.8</td></tr>
<tr><td class="l" rowspan="2">分散取水 DISP（错峰 τ=3.75/9.75/17.0 h）</td><td>PA 被动</td><td>314.9</td><td>52.5</td><td>151.3</td></tr>
<tr><td>SP / DP</td><td>0.0</td><td>0.0</td><td>23.7</td></tr>
<tr><td class="l">N-k worst k=1（607 MW）</td><td>PA / SP</td><td>91.1 / 0.0</td><td>7.6 / 0.0</td><td>—</td></tr>
<tr><td class="l">N-k worst k=2（1123 MW）</td><td>PA / SP</td><td>108.6 / 0.0</td><td>9.0 / 0.0</td><td>—</td></tr>
<tr><td class="l">N-k worst k=3（1600 MW）</td><td>PA / SP</td><td>172.6 / 57.1</td><td>112.0 / 95.6</td><td>—</td></tr>
<tr><td class="l">N-k worst k=6（2833 MW）</td><td>PA / SP</td><td>172.1 / 57.5</td><td>112.1 / 96.0</td><td>—</td></tr>
<tr><td class="l">N-k worst k=12（4138 MW）</td><td>PA / SP</td><td>223.4 / 76.8</td><td>143.9 / 128.2</td><td>—</td></tr>
<tr><td class="l">全序级联 72 h（19 台按失压顺序）</td><td>PA / SP</td><td>184.9 / 0.0</td><td>15.4 / 0.0</td><td>—</td></tr>
</table>
<p class="tblnote">N-k 为 worst top-k 子集；随机子集显著更轻（SP 16/18 零缺额）。单机/三机行为 B-ST 口径；N-k/级联取全耦合映射 B-ST 失效时刻。"—"＝该场景未单独报告过载。</p>

<h2>5　敏感性分析 Sensitivity Analysis</h2>

<h3>5.1　取水节点位置 → 失压时刻分布</h3>
<p class="summary">刻画唯一水源停供后全网失压时刻分布（B-ST 口径：t=0 阶跃断供，72 h / 15 min 延时水力仿真，失压判据 H&lt;28 m）：399 个配水节点中 289 个（72.4%）于 72 h 内失压、110 个（27.6%）不失压；失压时刻 0–67 h，P10/中位/P90 = 0/9.75/17.0 h，以直方图＋CDF＋空间分布三视图呈现（图 12），把\"取水位置差异导致失压时刻不同\"这一疑问转化为定量分布，并选出 P10/P50/P90 代表节点（J314 3.75 h／J142 9.75 h／J89 17.0 h——在\"故障前健康且会失压\"的候选中按分位数就近选取，供 §5.2 敏感性分析）。</p>
{figure("Fig12_depressurization_time_distribution.png", "图 12　唯一水源停供后全网失压时刻分布（§5.1，B-ST 合成阶跃口径：R1 于 t=0 断供，72 h / 15 min 延时水力仿真，失压判据 H<28 m）：399 个配水节点中 289 个（72.4%）于 72 h 内失压、110 个（27.6%）不失压；失压时刻 0–67 h，P10/中位/P90＝0/9.75/17.0 h。(a) 失压时刻直方图；(b) 累计失压节点比例（72% 平台＝72 h 观测窗内不再新增）；(c) 失压时刻空间分布（RdYlGn 色，色标截顶 P95＝20.3 h 以防 67 h 离群压缩色域；灰＝不失压节点；■＝唯一水源 R1；△＝水箱；○＝代表节点——取故障前健康且会失压节点中 P10/P50/P90 就近者，供 §5.2 取水位置敏感性分析：J314 3.75 h／J142 9.75 h／J89 17.0 h）")}

<h3>5.2　取水位置 → 电力韧性影响</h3>
<p class="summary">证明取水位置对被动控制峰值缺额影响显著（图 13：分散取水削峰 343.3→314.9 MW、71.9→52.5 MWh、最大过载 163.4→151.3 MW），而主动控制对取水位置稳健（SP/DP 双布置均 0/0）。机理：市政失压错峰 3.75/9.75/17.0 h ≫ 冷却窗口 ~2 h → 三机危机时间完全隔离（等价于三个独立单机事件，单机 LP 峰值取 max、能量取 sum——峰值不叠加），DISP 峰值即最严重单机；主动下各机在自身冷却 SAET 窗口软着陆、与节点无关。分散取水布置（DISP）即文献 Fig.7 多端源案例\"SAET 随距离而异\"的水侧对应。</p>
{figure("Fig13_intake_node_sensitivity.png", "图 13　取水节点位置对电力影响的敏感性（§5.2，三厂 bus 89/80/10；LP 优化＋DC 潮流）：(a) 市政失压时刻分布与 P10/P50/P90 代表节点（J314 3.75 h／J142 9.75 h／J89 17.0 h，选取口径见图 12）；(b) 取水布置 × 控制策略的系统峰值功率缺额——CO＝同源同位置（三机同时危机，联合 LP）：PA 峰值 343 MW、损失电量 71.9 MWh、最大过载 163.4 MW；DISP＝分散取水（三厂分别取 P10/P50/P90 代表节点，市政失压错峰 3.75/9.75/17.0 h ≫ 冷却窗口 ~2 h → 三机危机时间完全隔离，各单机 LP 求解、峰值不叠加、能量守恒）：PA 峰值降为 315 MW（＝最严重单机）、损失电量 52.5 MWh、最大过载 151.3 MW——取水位置显著影响【被动】峰值缺额；SP/DP 在两种布置下均 0/0（各机在自身冷却 SAET 窗口内软着陆，与取水节点无关）——主动控制对取水位置稳健")}

<h3>5.3　失压速率与参数敏感性</h3>
<p class="summary">失压速率：市政渐降（ramp=600 s）相对阶跃断水延长缓冲窗口 SAET（S03 已有数据），主动控制价值随之更宽裕。参数敏感性（正稿期待项）：其余机组爬坡率 R（决定 SP 可行性的第一敏感参数）、两级备用参数（r_frac / 慢起机容量与速率）、DP 时间比 α——上述扫描构成"主动控制相变边界"的补充证据链，与 §4.5 的失效规模边界互补。</p>

<h3>5.4　闭合水量账与热负荷鲁棒性</h3>
<p class="summary">闭合水量账（B-RT 口径）：以城市实际压头轨迹驱动补水阀（驱动压头 = p−28 m，即 28 m 阈值的物理来源——高位补水箱充填压头需求），取代合成阶跃；闭合 SAET 100% ≥ 已发布合成阶跃值（保守下界，如 bus89：92 min vs 1809 min）。Pmax 热负荷鲁棒变体消除 Pg=0 退化（35 台 Pg=0 机组耦合仅具拓扑/预警意义），29/54 在 72 h 内跳机，触发层闭合 SAET 中位约 37–41 h。</p>

<h2>6　讨论 Discussion</h2>
<p class="summary">总述本章从机理洞见、韧性工程启示、文献对比、局限四方面展开。</p>
<h3>6.1　机理洞见</h3>
<p class="summary">讨论两级缓冲（市政侧水箱 vs 电厂侧 ASW）及"缓冲位置决定失效传导与可用时间差"的核心机理；临界降出力速率（§4.2）揭示"降额自保护"负反馈的存在与边界。</p>
<h3>6.2　韧性工程启示</h3>
<p class="summary">提出跨域预警链路、按 SAET 分级的主动降负荷+备用预起机（临界速率 r* 为 runback 整定上限）、取水布置分散化等工程建议。</p>
<h3>6.3　与文献对比</h3>
<p class="summary">对比说明本文首次（限定式）建模冷却水过程（超越张明媛/李楠的直接耦合），并将孙宏斌气-电早期预警迁移到水-电并落到冷却水中介。<b>量化语境对照（系统不同、仅作语境）：</b>文献省级案例被动 1577.0 MW / 345.5 MWh → 动态主动 372.0 MW / 13.8 MWh；本文 SP/DP 即达 0/0 的物理原因在于冷却水储水缓冲（SAET 88.6–124.8 min）天然长于燃气管存气（文献中分钟级），且临界速率下"降额自保护"可再延长一倍——水-电场景的时间差禀赋优于气-电，韧性瓶颈自"信息速度"转移至"多机共因下的备用充足性与爬坡能力"（§4.5 的 k* 边界）。</p>
<h3>6.4　局限</h3>
<p class="summary">如实列出局限：无现场数据、解析水力、DP 单次近似；54 台中 35 台 Pg=0（耦合仅具拓扑/预警意义、不发生冷却级联）；补水水量不反馈进城市水力（松耦合 + PDD 事后评估）；SAET 合成阶跃为保守下界（闭合轨迹驱动值更长，§5.4）；信息层为单阈值/零时延/可靠传输的理想化口径（正稿将讨论时延鲁棒性）。</p>

<h2>7　结论 Conclusion</h2>
<p class="summary">复述两大创新与关键量化结论（时间差→主动控制窗口→韧性提升），给出<b>有边界的结论</b>：单机与同源 3 机场景下早期预警 + 主动控制将少发功率/损失电量由 485.6 MW / 49.1 MWh（或 343.3 MW / 71.9 MWh）降为 0；适用边界为同时失效机组数 k≤2（k≥3 残留 95.6–128.2 MWh）；取水位置敏感性——全网失压时刻 0–67 h 分布（399 节点 72.4% 失压、27.6% 不失压），分散取水使被动峰值 343→315 MW（危机时间隔离、峰值不叠加）而主动控制对位置稳健（0/0）；跨域发现：冷却水缓冲窗口天然长于燃气管存气。展望未来工作：预警时延/漏报鲁棒性与分级预警整定、爬坡率与备用参数扫描、DP 严格迭代、多厂共源、真实电厂-管网地理配对。</p>

<h2>数据与代码可用性 <span style="font-size:13px;color:var(--mut)">Data &amp; Code Availability</span></h2>
<p class="summary">模型与分析代码、全部仿真数据拟归档 Zenodo DOI 并公开（对齐参照文献开源实践）；D-town 管网数据（Ostfeld 2016, Battle of the Water Network Models, University of Kentucky Libraries）按 CC BY-NC 4.0 使用并于致谢署名。作者贡献（CRediT）、基金与利益冲突声明：正稿期补齐。</p>

</main>
<footer>
  简要版（骨架 v2.1）· 由 <code>make_paper_draft.py</code> 生成 · 图源 <code>figures/</code> · 框架源 <code>docs/paper_outline.md</code><br>
  v2 修订记录：对齐孙宏斌文（Table 1 对比表 / 临界降出力速率算例 Fig.8 / Table 4 双指标结果汇总 / 两级案例叙事 / 数据可用性占位）+ 取张明媛文（场景依据、配对先例、敏感性章落实）与李楠文（可审计数据、事件时刻标注、架构范式）优点 + 图号按首次引用顺序重排（13 图 4 表）+ 一致性修正（49.1 MWh、18/24 表述、SAET 口径标注）。详见 <code>docs/skeleton_revision_plan.md</code>。<br>
  v2.1 修订记录（图件校准轮同步，2026-09-02）：图 4–13 逐张校准——字号 12 统一、序号 (a)(b)(c) 加粗左上、图例/色标零覆盖、画布重排（图 10 2×2、图 12 两行 (c) 通栏放大 ≈2.2×）；各图 caption 扩写并数据链复跑核实（muni/p6/nk/saet_distribution/node_sensitivity 全部逐字节一致）；正文同步——摘要与结论补取水位置敏感性（343→315 MW、主动稳健 0/0）、§5.1 补 399/289/110 与代表节点口径、§5.2 补机理（危机时间隔离、峰值不叠加）与过载 163.4→151.3、表 4 补 DISP 过载 151.3/23.7。校准明细见 <code>docs/figure_calibration_log.md</code>。
</footer>
</div></body></html>"""

out = os.path.join(HERE, "论文简要版_骨架.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("saved", out, f"({len(HTML)//1024} KB)")
