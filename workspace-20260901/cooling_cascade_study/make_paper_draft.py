"""
生成论文【简要版 / 骨架版】自包含 HTML。
- 依据 docs/paper_outline.md 的 7 章框架；
- 每章/小节只写一段"本部分主要讲什么"的概述（非完整正文）；
- 图片按 Fig 编号内嵌到相应位置（SVG 内联、PNG base64），图源 figures/。
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
footer{padding:20px 60px 40px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);}
"""

HTML = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>论文简要版（骨架）— 基于早期预警的冷却水耦合水-电信息物理系统韧性提升</title>
<style>{CSS}</style></head><body><div class="wrap">

<header>
  <div class="badge">Paper Draft · 简要版（骨架）</div>
  <h1>基于早期预警的冷却水耦合水-电信息物理系统韧性提升</h1>
  <div class="en">Early-warning-based resilience enhancement of cooling-water-coupled water–power cyber-physical systems</div>
  <div class="meta">本文档为<b>简要版（骨架）</b>：每章/小节仅以一段概述说明"本部分主要讲什么"，并将对应图片置于相应位置；<b>不含完整正文</b>。完整框架见 <code>docs/paper_outline.md</code>，图件设计见 <code>docs/figure_design.md</code>。</div>
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

<div class="note">写作约定：以 <b>【本节概述】</b> 标出的段落为占位性说明，后续按此展开为完整正文。图片已按 Fig 编号内嵌到目标位置。</div>

<h2>摘要 Abstract</h2>
<p class="summary">概述电厂冷却水取自市政供水形成的<b>水-电信息物理耦合系统（CPS）</b>；指出既有研究直接把水网与机组作为级联对象、忽略冷却水中间过程的缺口；提出"利用供水慢动态与电力快动态的<b>时间差</b>、经信息系统快响应转化为<b>主动控制窗口</b>以提升韧性"的核心思想；给出关键量化结论（无预警 485.6&nbsp;MW / 49.1&nbsp;MWh → 有预警 0/0；SAET 88.6–124.8&nbsp;min）与两大创新点。</p>
<p style="font-size:12.5px;color:var(--mut)"><b>关键词：</b>water–power cyber-physical system; cooling water system modeling; early warning; resilience enhancement; slow–fast timescale gap; proactive control</p>

<h2>1　引言 Introduction</h2>
<p class="summary">说明本章按"背景 → 相关工作与缺口 → 本文思想与贡献 → 组织结构"四段递进；相关工作并入本章、不单独成章。</p>

<h3>1.1　背景（信息物理耦合系统视角）</h3>
<p class="summary">交代电厂循环冷却水依赖市政供水，物理经冷却水、信息经 ICS/SCADA 双重耦合成 CPS；极端事件下供水中断经冷却水威胁发电；引出核心问题——能否用信息系统快响应把慢-快时间差转化为主动控制窗口以提升韧性。</p>

<h3>1.2　相关工作与研究缺口</h3>
<p class="summary">沿三条线索综述并凝练缺口：(i) 水-电级联多用拓扑/概率耦合或协同仿真（张明媛、李楠），共同局限是用一条耦合边代替冷却水中间过程；(ii) 冷却水—凝汽器物理模型成熟但鲜少嵌入韧性分析；(iii) 能源早期预警（孙宏斌气-电）证明"缓冲时间→控制窗口"的价值但未及水-电冷却水场景。</p>

<h3>1.3　本文思想与贡献</h3>
<p class="summary">阐明核心思想（时间差→主动控制时间→韧性提升）与两大创新：创新点 1 首次显式建模冷却水全过程及故障仿真；创新点 2 利用信息系统快响应获取并利用两系统故障演化时间差。并列出支撑性工作（真实管网边界、取水位置敏感性）。</p>

<h3>1.4　论文组织</h3>
<p class="summary">概述全文 7 章结构与阅读脉络。</p>

<h2>2　方法 Methodology</h2>
<p class="summary">总述本章建立 CPS 四层耦合与信息层的完整方法体系，对应 <code>docs/mathematical_modeling.md</code>；两大创新点的方法主体分别落在 §2.3 与 §2.4。</p>

<h3>2.1　总体框架（水-电 CPS 四层 + 信息层）<span class="tag">全文骨架</span></h3>
<p class="summary">介绍四层（市政供水 / 冷却水 / 电力 / 影响指标）+ 贯穿信息层的耦合结构，强调"物理耦合=冷却水、信息耦合=ICS 预警链路"与多时间尺度（慢→快）。</p>
{figure("Fig1_CPS_framework.svg", "图 1　水-电信息物理耦合系统（CPS）四层耦合总体框架（§2.1）")}

<h3>2.2　市政水网边界层</h3>
<p class="summary">说明以 D-town 基准管网为上游边界：失效判据（配水节点压头 &lt; 28 m）、EPANET EPS/PDD 仿真、以及"为何市政水网只作边界不耦合进下游"的缓冲位置不对称论证。</p>

<h3>2.3　冷却水故障机理链 <span class="tag inno">创新点 1</span></h3>
<p class="summary">给出冷却水全过程建模：水力（质量守恒/孔口/NPSH）→ 热力（ε-NTU/Antoine）→ 背压降额 → 高背压保护跳机，并定义早期预警指标 AET/ASW/SAET。此为创新点 1 的方法主体。</p>
{figure("Fig2_cooling_water_chain.svg", "图 2　电厂冷却水系统物理过程链（创新点 1，§2.3）")}

<h3>2.4　信息系统层与慢-快时间差 <span class="tag inno">创新点 2</span></h3>
<p class="summary">阐述三域独立三级 ICS、市政压力检测与跨域预警链路（快响应）、预警触发时刻的选择论证；说明如何据此获取供水慢动态与电力快动态之间的时间差。此为创新点 2 的方法主体。三域三级 ICS 架构与跨域预警链路已并入总体框架图（见图 1 信息层），此处以图 3 聚焦时间差机制。</p>
{figure("Fig3_timescale_gap_mechanism.svg", "图 3　慢-快动态时间差与早期预警机制（创新点 2，§2.4）")}

<h3>2.5　电力系统层与主动控制</h3>
<p class="summary">介绍电力侧建模：DC 潮流（PTDF）、两级备用（旋转+慢起机）、主动控制线性规划（PA/SP/DP 三策略），以及韧性/影响指标（少发功率、损失电量）。</p>

<h2>3　案例与参数 Case Study &amp; Setup</h2>

<h3>3.1　测试系统与耦合配对</h3>
<p class="summary">介绍 IEEE-118（电）× D-town（水）双网案例与取水节点↔电厂母线的<strong>全耦合</strong>配对：54 台发电机（含平衡机）各配一个取水 junction（保留已校验三对 + 基线健康筛选 + 分层比例抽样 + 确定性配对，消除指定配对任意性）。耦合规律全节点验证 54/54 通过（市政侧只反馈压头；&lt;28 m 此刻即失效；SAET 自该时刻起算）。可行性核查表明额定补水 299.7 L/s 反馈进基线即崩溃（水源出力仅 ~246 L/s），故边界采用语义①：补水不反馈进城市水力、按 PDD 事后评估可供性。</p>
{figure("Fig4_coupling_topology.png", "图 4　IEEE-118 × D-town 水-电耦合拓扑与耦合对（§3.1）")}

<h3>3.2　参数标定与规范出处</h3>
<p class="summary">说明无现场数据下参数按国家/国际规范（GB/T 50102、DL/T 5339、HEI/ASME PTC 12.2）+ 机组额定/实际出力拟合；参数总表列于此（Table 1）。</p>

<h3>3.3　场景矩阵</h3>
<p class="summary">给出场景设计：有/无预警 × PA/SP/DP × 同源/多源取水（Table 2）。</p>

<h2>4　结果 Results</h2>

<h3>4.1　市政侧：多源错峰失压与全网压力时空崩溃</h3>
<p class="summary">展示同一水源失效经不同分区缓冲导致各取水节点错峰失压，以及唯一水源停供后全网压力自水源向外的时空崩溃，作为时间差的市政侧来源与边界真实性证据。并在物理补水口径（0.453 m³/s@707MW 按 Pmax 缩放）下评估市政备用可供性：72 h 需求 165.5 万 m³、PDD 可供 92.0%，分层 Q1 54.9% → never 100%（失压越快的层市政备用丧失越早）。</p>
{figure("Fig5_muni_staggered_depressurization.png", "图 5　市政总源失效后全部 54 个耦合取水节点的压力热力图（行＝取水节点并标注节点名，按失压分层 Q1–Q5、层内按首破阈值时刻排序，白线分层；色＝节点压力，与图 6 同色标、失压呈红色；○ 为首破 28 m 阈值时刻，构成错峰失压前锋；Q5 全程高于阈值，§4.1）")}
{figure("Fig6_network_outage_spatiotemporal.png", "图 6　唯一水源停供 → 全网 399 节点压力时空崩溃（§4.1）")}

<h3>4.2　冷却水故障机理链结果 <span class="tag inno">创新点 1 结果</span></h3>
<p class="summary">用时序结果证明冷却水储水缓冲把市政断水延迟约 SAET≈92 min 才传导到机组跳机（代表机组 bus89、合成阶跃保守下界；闭合轨迹驱动值约 30 h，见 §5.4），直观展示被忽略的冷却水过程如何"制造"可用时间差。</p>
{figure("Fig7_cooling_chain_timeseries.png", "图 7　冷却水故障机理链时序：水位→流量→背压→出力（创新点 1 结果，§4.2）")}

<h3>4.3　有无早期预警对比 <span class="tag inno">创新点 2 核心</span></h3>
<p class="summary">全文最核心结果：无预警时机组跳机造成 485.6 MW 少发 / 49.1 MWh 损失，经信息系统预警 + 主动控制降为 0/0，直接量化早期预警的韧性价值。</p>
{figure("Fig8_early_warning_comparison.png", "图 8　有无早期预警对比（创新点 2 核心结果，§4.3）")}

<h3>4.4　主动控制三策略与韧性提升</h3>
<p class="summary">对比被动/静态主动/动态主动三策略：PA 343.3 MW / 71.9 MWh，SP/DP 完全消除缺额，说明主动控制随时间差充分利用而提升韧性（对齐参照文献 Fig.6）。</p>
{figure("Fig9_PA_SP_DP_strategies.png", "图 9　被动/静态主动/动态主动三策略对比（§4.4）")}

<h3>4.5　电侧 N-k 跳闸扫描（主动控制的稳健性边界）</h3>
<p class="summary">对 19 台有出力耦合机组做 k=1–12 组合跳闸（最坏+随机组合，DC 潮流 LP）：N-1/N-2 最坏可被主动控制完全吸收；k≥3 最坏受备用/爬坡物理限制残留 96–128 MWh；随机组合显著更轻（SP 在 18/24 组合零缺额）。</p>
{figure("Fig12_nk_scaling.png", "图 12　电侧 N-k 跳闸扫描：最坏组合能量缺额随 k 标度与全组合分布（PA vs SP，§4.5）")}

<h2>5　敏感性分析 Sensitivity Analysis</h2>

<h3>5.1　取水节点位置 → 失压时刻分布</h3>
<p class="summary">刻画全网失压时刻分布（0–67 h、28% 节点长期不失压），把"取水位置差异导致失压时刻不同"这一疑问转化为定量分布，并选出 P10/P50/P90 代表节点。</p>
{figure("Fig10_depressurization_time_distribution.png", "图 10　唯一水源停供后全网失压时刻分布（§5.1）")}

<h3>5.2　取水位置 → 电力韧性影响</h3>
<p class="summary">证明取水位置对被动控制峰值缺额影响显著（分散取水削峰），而主动控制对取水位置稳健（缺额均消除），从而强化主动控制的价值与结论稳健性。</p>
{figure("Fig11_intake_node_sensitivity.png", "图 11　取水节点位置对电力影响的敏感性（§5.2）")}

<h3>5.3　（可选）失压速率与断水情景敏感性</h3>
<p class="summary">概述对失压速率 ramp、断水情景等的补充敏感性分析（可选）。</p>

<h3>5.4　闭合水量账与热负荷鲁棒性</h3>
<p class="summary">闭合水量账：以城市实际压头轨迹驱动补水阀（驱动压头 = p−28 m，即 28 m 阈值的物理来源——高位补水箱充填压头需求），取代合成阶跃；闭合 SAET 100% ≥ 已发布合成阶跃值（保守下界，如 bus89：92 min vs 1809 min）。Pmax 热负荷鲁棒变体消除 Pg=0 退化（35 台 Pg=0 机组耦合仅具拓扑/预警意义），29/54 在 72 h 内跳机，触发层闭合 SAET 中位约 37–41 h。</p>

<h2>6　讨论 Discussion</h2>
<p class="summary">总述本章从机理洞见、韧性工程启示、文献对比、局限四方面展开。</p>
<h3>6.1　机理洞见</h3>
<p class="summary">讨论两级缓冲（市政侧水箱 vs 电厂侧 ASW）及"缓冲位置决定失效传导与可用时间差"的核心机理。</p>
<h3>6.2　韧性工程启示</h3>
<p class="summary">提出跨域预警链路、按 SAET 分级的主动降负荷+备用预起机、取水布置分散化等工程建议。</p>
<h3>6.3　与文献对比</h3>
<p class="summary">对比说明本文首次建模冷却水过程（超越张明媛/李楠的直接耦合）、并将孙宏斌气-电早期预警迁移到水-电并落到冷却水中介。</p>
<h3>6.4　局限</h3>
<p class="summary">如实列出局限：无现场数据、解析水力、DP 单次近似；54 台中 35 台 Pg=0（耦合仅具拓扑/预警意义、不发生冷却级联）；补水水量不反馈进城市水力（松耦合 + PDD 事后评估）；SAET 合成阶跃为保守下界（闭合轨迹驱动值更长，§5.4）。</p>

<h2>7　结论 Conclusion</h2>
<p class="summary">复述两大创新与关键量化结论（时间差→主动控制窗口→韧性提升），并展望未来工作（DP 严格迭代、多厂共源、真实电厂-管网地理配对、分级预警）。</p>

</main>
<footer>
  简要版（骨架）· 由 <code>make_paper_draft.py</code> 生成 · 图源 <code>figures/</code> · 框架源 <code>docs/paper_outline.md</code><br>
  说明：本版仅概述各部分内容并定位图片，不含完整正文；后续按框架逐节展开为正式稿。
</footer>
</div></body></html>"""

out = os.path.join(HERE, "论文简要版_骨架.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("saved", out, f"({len(HTML)//1024} KB)")
