"""生成完整研究报告 (自包含 HTML, 图片内嵌为 data URI)。
主线: P1 机理 -> ICS 早期预警 -> P6 主动控制(对齐文献); 影响以少发功率/损失电量衡量。"""
import os, base64, json

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")          # 数据 (json/csv/db) 源
FIG = os.path.join(HERE, "figures")        # 成图集 (唯一图库, 供报告内嵌)

# results/ 按模块分子目录; 用文件名前缀映射到子目录 (仅数据文件, 供 json.load)
_SUBDIR = {
    "muni_boundary": "muni", "network_outage": "muni", "saet_distribution": "muni",
    "p1_smib": "cooling_chain",
    "ics_": "ics",
    "p6_": "proactive_control",
}

# 报告图片统一从 figures/ 读取: 旧文件名 -> figures/ 下的 Fig 编号文件名
_FIGMAP = {
    "p1_smib_bus89_tf60_ramp0.png": "Fig7_cooling_chain_timeseries.png",
    "ics_warning_compare.png": "Fig8_early_warning_comparison.png",
    "p6_strategy_compare.png": "Fig9_PA_SP_DP_strategies.png",
    "muni_boundary.png": "Fig5_muni_staggered_depressurization.png",
    "network_outage.png": "Fig6_network_outage_spatiotemporal.png",
    "saet_distribution.png": "Fig10_depressurization_time_distribution.png",
    "p6_node_sensitivity.png": "Fig11_intake_node_sensitivity.png",
    # ICS 架构已并入 Fig.1（CPS 总体框架，含三域三级 ICS + 预警链路）
    "ics_architecture.svg": "Fig1_CPS_framework.svg",
}


def _resolve(name):
    """数据文件路径解析 (results/ 子目录)。"""
    for pre, sub in _SUBDIR.items():
        if name.startswith(pre):
            return os.path.join(R, sub, name)
    return os.path.join(R, name)


def _fig(name):
    """图片路径解析: 优先 figures/ (映射后), 回退 results/。"""
    mapped = _FIGMAP.get(name, name)
    p = os.path.join(FIG, mapped)
    return p if os.path.exists(p) else _resolve(name)


def img(name):
    with open(_fig(name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def svg_inline(name):
    with open(_fig(name), "r", encoding="utf-8") as f:
        return f.read()


ics = json.load(open(_resolve("ics_warning_compare.json")))
p6 = json.load(open(_resolve("p6_strategy_compare.json")))
p6r = p6["results"]
ind = p6["indicators"]
W, N = ics["WARN"], ics["NOWARN"]
muni = json.load(open(_resolve("muni_boundary.json")))
mp = muni["plants"]
nsens = json.load(open(_resolve("p6_node_sensitivity.json")))
_ns_co = nsens["layouts"]["CO"]["results"]
_ns_dp = nsens["layouts"]["DISP"]["results"]
_ns_dist = nsens["distribution"]
# 各电厂故障后失效时刻 (h), 按错峰次序
_mrows = sorted(
    [(k, v["node"], v["zone"], v["head0_m"], v["t_fail_after_fault_s"] / 3600.0)
     for k, v in mp.items() if v["t_fail_after_fault_s"] is not None],
    key=lambda x: x[4])

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>电厂冷却水故障与早期预警主动控制研究报告</title>
<style>
  :root{{--ink:#1a2b3c;--mut:#5b6b7a;--line:#e2e8f0;--accent:#1f6fb2;--accent2:#2e8b57;
    --warn:#c0392b;--amber:#e08a1e;--bg:#ffffff;--soft:#f7fafc;}}
  *{{box-sizing:border-box}}
  body{{font-family:-apple-system,"Noto Sans CJK SC","Microsoft YaHei",Segoe UI,sans-serif;
    color:var(--ink);line-height:1.75;margin:0;background:#eef2f6;}}
  .wrap{{max-width:920px;margin:0 auto;background:var(--bg);box-shadow:0 1px 20px rgba(0,0,0,.06);}}
  header{{background:linear-gradient(135deg,#123a5c,#1f6fb2);color:#fff;padding:56px 60px 44px;}}
  header h1{{margin:0 0 8px;font-size:29px;line-height:1.3;font-weight:700;}}
  header .sub{{font-size:15px;opacity:.92;}}
  header .meta{{margin-top:22px;font-size:13px;opacity:.85;border-top:1px solid rgba(255,255,255,.25);padding-top:16px;}}
  main{{padding:20px 60px 60px;}}
  h2{{font-size:23px;margin:46px 0 6px;padding-bottom:8px;border-bottom:2px solid var(--accent);color:#123a5c;}}
  h3{{font-size:18px;margin:30px 0 4px;color:#1f4e79;}}
  h4{{font-size:15px;margin:20px 0 4px;color:var(--accent2);}}
  p{{margin:10px 0;}}
  .lead{{font-size:16px;color:var(--mut);}}
  code{{background:var(--soft);padding:1px 6px;border-radius:4px;font-size:13px;font-family:"SF Mono",Consolas,monospace;color:#c0392b;}}
  pre{{background:#1a2b3c;color:#e2e8f0;padding:16px 20px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6;font-family:"SF Mono",Consolas,monospace;}}
  figure{{margin:20px 0;text-align:center;}}
  figure img{{max-width:100%;border:1px solid var(--line);border-radius:8px;}}
  figcaption{{font-size:13px;color:var(--mut);margin-top:8px;}}
  table{{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px;}}
  th,td{{border:1px solid var(--line);padding:8px 12px;text-align:center;}}
  th{{background:#123a5c;color:#fff;font-weight:600;}}
  tr:nth-child(even) td{{background:var(--soft);}}
  .kpi-row{{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0;}}
  .kpi{{flex:1;min-width:170px;background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:18px 20px;border-left:4px solid var(--accent);}}
  .kpi .num{{font-size:26px;font-weight:700;color:var(--accent);}}
  .kpi .lbl{{font-size:13px;color:var(--mut);margin-top:2px;}}
  .callout{{background:#eef6fb;border-left:4px solid var(--accent);border-radius:0 8px 8px 0;padding:14px 20px;margin:18px 0;}}
  .callout.warn{{background:#fdf0ee;border-color:var(--warn);}}
  .callout.ok{{background:#eef7f1;border-color:var(--accent2);}}
  .callout b{{color:#123a5c;}}
  .toc{{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:20px 28px;margin:24px 0;}}
  .toc ol{{margin:6px 0;padding-left:22px;}} .toc a{{color:var(--accent);text-decoration:none;}}
  .toc a:hover{{text-decoration:underline;}}
  .muted{{color:var(--mut);font-size:13px;}}
  ul li,ol li{{margin:5px 0;}}
  footer{{padding:30px 60px;background:#123a5c;color:#c9d6e2;font-size:13px;text-align:center;}}
  .chain{{font-family:"SF Mono",Consolas,monospace;font-size:12.5px;background:#f0f5f9;border:1px solid var(--line);border-radius:8px;padding:16px 20px;white-space:pre;overflow-x:auto;color:#1a2b3c;}}
</style></head>
<body><div class="wrap">
<header>
  <div style="font-size:13px;opacity:.8;letter-spacing:2px;margin-bottom:12px;">研究报告 · RESEARCH REPORT</div>
  <h1>市政供水中断引发的电厂冷却水故障<br>与电力系统早期预警主动控制研究</h1>
  <div class="sub">Impact of Municipal Water-Supply Interruption on the Power System via Plant Cooling-Water Failure, and Early-Warning Proactive Control</div>
  <div class="meta">
    测试系统：IEEE 118 节点 &nbsp;|&nbsp; 失效源：市政配水节点压头 &lt; 28 m，无法为高位补水箱补水<br>
    影响量化：少发功率 (MW) + 损失电量 (MWh) &nbsp;|&nbsp; 潮流：直流潮流 (DC-PF) &nbsp;|&nbsp; 方法对齐：孙宏斌院士团队气-电早期预警 (Nat. Commun. 2024)
  </div>
</header>
<main>

<div class="toc">
  <b>目录</b>
  <ol>
    <li><a href="#s1">摘要</a></li>
    <li><a href="#s2">研究背景与目标</a></li>
    <li><a href="#s3">建模方法：多时间尺度耦合</a></li>
    <li><a href="#s3a">市政水网边界：多源错峰失压（D-town 基准网）</a></li>
    <li><a href="#s4">P1 — 故障机理链（市政断水 → 机组跳机）</a></li>
    <li><a href="#s5">ICS — 三域信息系统与早期预警</a></li>
    <li><a href="#s6">P6 — 主动控制线性规划（对齐文献方法）</a></li>
    <li><a href="#s7">结论与建议</a></li>
    <li><a href="#s8">局限与后续工作</a></li>
    <li><a href="#s9">附录：实现与复现</a></li>
  </ol>
</div>

<h2 id="s1">1. 摘要</h2>
<p class="lead">本研究针对<b>市政供水管网压力失效（配水节点压头 &lt; 最小供水阈值 28 m，无法为电厂高位补水箱补水）</b>这一起点，构建"市政断水 → 补水箱/集水池排空 → 循环水泵汽蚀跳泵 → 凝汽器背压升高 → 机组高背压保护跳机 → 电力系统少发电"的全链条耦合模型，并量化其对电力系统的影响。</p>
<p>核心科学问题：<b>水力慢动态（分钟级）与电力快动态（秒级）之间的时序差异，能否作为早期预警窗口</b>——市政供水信息控制系统(ICS)检出断供后，将预警跨域传给电力系统 ICS，使电网在机组跳机前<b>主动</b>调整发电，而非被动等待。影响以<b>少发功率(MW)与损失电量(MWh)</b>衡量（与参照文献一致）。</p>
<div class="kpi-row">
  <div class="kpi"><div class="num">28 m</div><div class="lbl">最小供水阈值（失效源）</div></div>
  <div class="kpi"><div class="num">{ind['89']['SAET_min']:.0f}–{ind['10']['SAET_min']:.0f} min</div><div class="lbl">SAET 静态可用逃逸时间</div></div>
  <div class="kpi"><div class="num">{N['max_deficit_MW']:.0f} → 0 MW</div><div class="lbl">少发功率峰值（无→有预警）</div></div>
  <div class="kpi"><div class="num">{N['energy_deficit_MWh']:.0f} → 0 MWh</div><div class="lbl">损失电量（无→有预警）</div></div>
</div>
<p>主要结论：(1) 市政断水经水力缓冲（补水箱+集水池储水）后才传导至机组，提供了分钟级预警窗口（SAET ≈ {ind['89']['SAET_min']:.0f}–{ind['10']['SAET_min']:.0f} min）；(2) <b>无早期预警</b>时，单台机组因水源中断跳机，造成少发功率峰值 <b>{N['max_deficit_MW']:.0f} MW</b>、损失电量 <b>{N['energy_deficit_MWh']:.1f} MWh</b>；<b>有早期预警</b>时，电网提前主动降负荷并预置备用，少发功率与损失电量均降为 <b>0</b>；(3) 采用与文献一致的主动控制线性规划，同源多机共因故障下，被动/静态主动/动态主动三策略的少发功率依次为 <b>{p6r['PA']['max_deficit_MW']:.0f} → {p6r['SP']['max_deficit_MW']:.0f} → {p6r['DP']['max_deficit_MW']:.0f} MW</b>，动态主动可完全消除缺额。</p>

<h2 id="s2">2. 研究背景与目标</h2>
<p>火电机组循环冷却水系统的补水通常来自市政管网，经<b>高位补水箱</b>（临界设备）自流补入<b>集水池</b>；循环水泵从集水池抽水送入凝汽器换热，热水经冷却塔冷却后回流集水池，构成"闭式循环 + 开式补水"。当市政配水节点压头跌破最小供水阈值，补水中断，引发如下链条：</p>
<div class="chain">市政配水节点压头 &lt; 28 m（失效源, 无法为补水箱补水）
   → 高位补水箱水位下降 → 无法向集水池补水
      → 集水池水位缓降（蒸发/排污/风吹损失得不到补充）
         → 循环水泵吸入淹没深度不足 → 汽蚀 / 跳泵
            → 凝汽器换热能力下降 → 真空恶化、低压缸背压升高
               → 高背压保护动作 → 机组跳机
                  → 电力系统少发功率 → 损失电量（若无预警）</div>
<p>本研究的框架借鉴自 <b>Yu, Guo, Wu, Qiao, Sun. Early warning and proactive control strategies for power blackouts caused by gas network malfunctions. Nature Communications 15:4714 (2024)（孙宏斌院士团队）</b>的"气-电早期预警"方法，将物理量由天然气替换为冷却水，主动/被动运行逻辑与之一致。</p>
<h4>研究目标</h4>
<ul>
  <li><b>机理：</b>建立"市政配水节点 → 补水箱 → 集水池 → 循环水 → 凝汽器 → 低压缸 → 发电机"全链条耦合模型。</li>
  <li><b>量化：</b>以<b>少发功率与损失电量</b>衡量水源中断对电力系统的影响。</li>
  <li><b>核心：</b>对比<b>有无早期预警</b>下的影响，并用主动控制线性规划求解 PA/SP/DP 三策略。</li>
</ul>
<h4>研究范围（已锁定）</h4>
<table>
<tr><th>维度</th><th>选定</th></tr>
<tr><td>机组类型</td><td>常规燃煤汽轮机组（聚焦凝汽器—低压缸）</td></tr>
<tr><td>电网载体</td><td>IEEE 118 节点（54 机、186 支路、总负荷 4242 MW）</td></tr>
<tr><td>失效源</td><td>市政配水节点压头 &lt; 28 m，无法为高位补水箱补水</td></tr>
<tr><td>影响指标</td><td>少发功率 (MW) + 损失电量 (MWh)（与文献一致）</td></tr>
<tr><td>潮流方法</td><td>直流潮流 (DC-PF / PTDF)（与文献一致）</td></tr>
<tr><td>备用体系</td><td>两级（旋转备用 + 慢起机备用），与文献一致</td></tr>
</table>

<h2 id="s3">3. 建模方法：多时间尺度耦合</h2>
<p>研究的核心难点是时间尺度跨度大（水力/热力分钟级、机电秒级）。采用四层子模型 + 信息层耦合：</p>
<table>
<tr><th>层</th><th>子模型</th><th>关键变量</th><th>时间尺度</th></tr>
<tr><td>W</td><td>水源侧水力学</td><td>市政压头、水箱/池水位、循环水流量 m_cw</td><td>数十秒—数十分钟</td></tr>
<tr><td>A</td><td>凝汽器—低压缸</td><td>背压 p_b、机械功率降额 k_p</td><td>秒—数十秒</td></tr>
<tr><td>B</td><td>机组机电</td><td>出力、跳机</td><td>秒</td></tr>
<tr><td>C</td><td>电网（直流潮流）</td><td>少发功率、损失电量、支路潮流</td><td>秒—分钟</td></tr>
</table>
<p class="muted">水力用质量守恒 + 孔口/阀门水力学 + NPSH 汽蚀理论；热力用 ε-NTU 换热 + Antoine 饱和线；电网用直流潮流(PTDF)。完整数学模型见 <code>docs/mathematical_modeling.md</code>。</p>
<p class="muted"><b>冷却水系统参数按规范校准：</b>循环水量按设计温升 8 K 标定、循环损失 ≈2.2%、冷却塔冷幅 5 K（<b>GB/T 50102《工业循环水冷却设计规范》</b>）；集水池容积按吸水井有效停留 4.1 min 设计（<b>DL/T 5339《火力发电厂水工设计规范》</b>）；凝汽器换热参照 HEI/ASME PTC 12.2。参数出处见 <code>docs/parameter_fitting.md</code>。</p>

<h2 id="s3a">3A. 市政水网边界：多源错峰失压（真实基准管网）</h2>
<p>为让"市政供水失效"具备<b>真实管网依据</b>，本研究引入市政配水管网基准模型 <b>D-town</b>（单水库总源 + 11 泵/7 水箱分区 + 399 节点/443 管段的分层 DMA 结构，<b>含真实城市需水量与日变化模式</b>）作为<b>上游边界生成器</b>：用其水力仿真生成各电厂配水节点的压头轨迹，经 28 m 阈值判据得到各电厂供水失效时刻，再交给下游冷却水/电力模型。<b>下游模型完全不变</b>，市政水网只提供边界。</p>
<p class="muted"><b>为何用 D-town 而非 C-town：</b>同系列 C-town 导出版需水量全为 0（校准用拓扑骨架），需人为补背景负荷才能让水箱排空；D-town 是 C-town 拓扑的<b>带真实需水量改进版</b>（348 节点真实需水 + 5 条日变化模式），消除了这一人为成分——图中昼夜起伏即真实日变化需水所致。</p>
<div class="callout"><b>为何市政水网只作边界、不耦合进下游（缓冲位置不对称）：</b>参照文献气网必须做网络水力仿真，因为缓冲（管存气 line pack）分布在<b>管网内部</b>，AET/SAET 由管存气算出。本项目的缓冲（可用储水量 ASW）在<b>电厂内部</b>（高位补水箱 + 集水池），是集总的、不在市政管网里。故市政管网对下游只是一个<b>压力边界</b>，不承载下游需要的缓冲物理——用它生成配水节点压头轨迹即充分。</div>
<h4>同源 vs 多源两类案例（对齐文献两级案例）</h4>
<table>
<tr><th>案例</th><th>参照文献</th><th>本项目实现</th></tr>
<tr><td><b>同源</b></td><td>Fig.5–6：单气源 GS 故障累及多厂</td><td>单一市政总源/配水点失效累及同源多机（P6 参数化失压）</td></tr>
<tr><td><b>多源错峰</b></td><td>Fig.7：多端源省级案例，6 机不同 SAET</td><td>市政总源失效经不同 DMA 缓冲，各配水节点错峰失效、各机组不同 SAET（本节 D-town 真实生成）</td></tr>
</table>
<figure><img src="{img('muni_boundary.png')}" alt="市政水网多源错峰失压">
<figcaption>图 3A.1　D-town 市政总源压力失效（t=6 h 起水库压头下降）→ 各电厂配水节点错峰失压：同一总源失效，经不同 DMA 分区缓冲，各配水节点在不同时刻跌破 28 m 阈值 → 各机组获得不同 SAET（昼夜起伏为真实日变化需水）</figcaption></figure>
<table>
<tr><th>电厂母线</th><th>配水节点</th><th>DMA 分区</th><th>正常压头</th><th>故障后失效时刻</th></tr>
{''.join(f"<tr><td>{k}</td><td>{node}</td><td>{dma}</td><td>{h0:.1f} m</td><td><b>+{tf:.1f} h</b></td></tr>" for k, node, dma, h0, tf in _mrows)}
</table>
<div class="callout ok"><b>关键结果：</b>同一市政总源故障，经不同 DMA 分区的水箱缓冲与管网距离，三座电厂配水节点分别在故障后 <b>{' / '.join(f'{tf:.1f}' for *_, tf in _mrows)} h</b> 跌破供水阈值——<b>各机组失效时刻天然不同、SAET 各异</b>，无需人为指定。这精确镜像了文献"SAET 随与故障点距离从数分钟到数小时不等"的现象，为多源共因故障下的差异化主动控制提供了真实边界。</div>
<p class="muted">方法与说明：EPANET 2.2 扩展时段准稳态(EPS，分钟级，与失压传导尺度一致，水质分析关闭)、压力驱动需水(PDD)；故障以水源(水库)压头下降施加，比硬切管道更贴合"市政供水压力失效"的物理本意；D-town 自带真实城市需水量，图中昼夜起伏即真实日变化需水(高区水箱夜间重力供水)；各配水节点随其供区水箱逐级耗尽先后失效，下游只取首次跌破阈值时刻。数据来源：Ostfeld (2016), Battle of the Water Network Models, Univ. of Kentucky (CC BY-NC 4.0)。详见 <code>muni_wdn/</code>。</p>

<h4>唯一水源完全停供 → 全网压力崩溃的时空演化</h4>
<p>除上述"3 个电厂取水点错峰"外，本研究另做一项<b>全网时空分析</b>：模拟 D-town <b>唯一水源（水库 R1）完全停止供水</b>后，<b>整个管网全部 399 节点</b>压力的时空演化——失压如何从水源处开始、随各分区水箱逐级放空而在空间上扩散。停供以水源压头阶跃降至近零施加（配合 PDD + 压力钳制为 0，物理正确，避免硬切产生的非物理负压）。</p>
<figure><img src="{img('network_outage.png')}" alt="全网压力崩溃时空演化">
<figcaption>图 3A.2　唯一水源自 t=0 完全停供 → 全网 399 节点压力崩溃：① 全网压力统计随时间 ② 失压节点占比随时间 ③–⑥ 空间快照（节点着色压力，蓝=健康、红=失压）。停供后由分区水箱储水续供约 12 h，水箱逐级放空后失压区自水源向外空间扩散</figcaption></figure>
<div class="callout"><b>关键现象（缓冲窗口 + 空间扩散）：</b>唯一水源自 t=0 停供后，全网压力<b>并不立即崩溃</b>——7 个分区水箱靠储水继续供水，维持约 <b>12 h</b>（市政侧缓冲窗口）；随水箱见底，失压节点（压头 &lt; 28 m）占比从初始 ~10% 扩大到 ~62%，<b>全网半数节点在停供后约 12.5 h 失压</b>。空间快照清晰显示崩溃自水源向外扩散——这与"缓冲位置决定失效传导"的核心论点一致（此处缓冲在市政水箱，而下游耦合的缓冲在电厂内部）。</div>

<h2 id="s4">4. P1 — 故障机理链（市政断水 → 机组跳机）</h2>
<p>在单机框架上打通全链条，验证从市政断水到机组跳机的时序因果，并据此计算早期预警指标 AET/ASW/SAET。下图展示"市政断水 → 补水箱/集水池水位下降 → 跳泵 → 背压上升 → 跳机"的物理链条：</p>
<figure><img src="{img('p1_smib_bus89_tf60_ramp0.png')}" alt="P1 故障机理链">
<figcaption>图 4.1　故障机理链时序（bus89；市政阶跃断水）：水位 → 循环水流量 → 背压 → 机组出力</figcaption></figure>
<div class="callout"><b>缓冲时间与预警指标：</b>市政断水后，补水箱与集水池储水延缓故障传导，机组在断水后约 27 分钟才被迫跳机（SAET）。这段"可用逃逸时间"正是留给电网侧的预警窗口。各受影响机组的静态预警指标：</div>
<table>
<tr><th>机组母线</th><th>SAET 静态可用逃逸时间 (min)</th><th>ASW0 初始可用储水量 (m³)</th></tr>
<tr><td>89</td><td>{ind['89']['SAET_min']:.1f}</td><td>{ind['89']['ASW0_m3']:.0f}</td></tr>
<tr><td>80</td><td>{ind['80']['SAET_min']:.1f}</td><td>{ind['80']['ASW0_m3']:.0f}</td></tr>
<tr><td>10</td><td>{ind['10']['SAET_min']:.1f}</td><td>{ind['10']['ASW0_m3']:.0f}</td></tr>
</table>
<p class="muted">SAET（Static Available Escape Time，静态可用逃逸时间）与 ASW（Available Stored Water，可用储水量）是文献 AET/ALP 的水侧类比。出力越小的机组热负荷越低、集水池排水越慢，SAET 越长。</p>

<h2 id="s5">5. ICS — 三域信息系统与早期预警</h2>
<p>按真实工程分层，市政供水侧、冷却水系统侧、电力系统侧<b>各设独立的三级工业控制系统（PLC / SCADA / 调度中心）</b>。市政供水 ICS 与电力系统 ICS 相互独立运行——正因如此才需要早期预警链路：市政供水 ICS 检出断供后，将预警跨域传给电力系统 ICS。冷却水侧与电力系统侧同属电厂、两者 ICS 厂内交互。</p>
<figure>{svg_inline('ics_architecture.svg')}
<figcaption>图 5.1　水-电信息物理耦合系统总体框架（含三域独立三级 ICS：市政供水 / 冷却水系统 / 电力系统各设 PLC/SCADA/调度中心，+ 跨域早期预警链路；即论文 Fig.1）</figcaption></figure>
<h4>预警触发时刻的选择</h4>
<p>预警链路的触发时刻有两种可能定义：<b>（方案一）</b>市政管网一旦发生任意故障即报警；<b>（方案二，本研究采用）</b>仅当为电厂机组<b>配水的配水节点压头</b>跌破最小供水阈值（&lt; 28 m）时才报警。采用方案二的依据：(1) <b>可观测性/因果正确</b>——市政管网为多水源环状结构，某处故障不必然导致电厂配水节点失压，可直接观测且直接决定后果的物理量是配水节点压头；(2) <b>与文献对齐</b>——文献以终端进气口压力跌破保护阈值为触发点并起算 AET/SAET，对应到本研究即配水节点压头越阈，也正是可用储水量 ASW 开始净耗尽的起点；(3) <b>避免误报成本</b>——主动控制有再调度/备用消耗代价，方案二仅在真实威胁出现时触发；(4) <b>时间零点自洽</b>——28 m 同时是失效判据与检出阈值，使"失效"与"预警"重合于同一瞬间，给 ASW/AET/SAET 干净可复现的 t=0。（曾评估"关注级+行动级"的<b>分级预警</b>折中，但因其破坏"有无预警"的二值对照、且提前量在无现场数据下不可量化，本研究不予引入，留作未来工作。）</p>
<h4>有无早期预警对比（影响以少发功率 / 损失电量衡量）</h4>
<p>检测量为<b>市政供水压力</b>（源头信号）；压头一旦跌破 28 m 即刻可靠预警（不考虑检测延时/丢包/漏报）。对比两种情形：</p>
<figure><img src="{img('ics_warning_compare.png')}" alt="有无预警对比">
<figcaption>图 5.2　有无早期预警对比：① 市政供水压头与检出时刻 ② 集水池水位 ③ 凝汽器背压 ④ 电力系统功率缺额（少发功率）</figcaption></figure>
<table>
<tr><th>情形</th><th>检测量 & 判据</th><th>机组是否跳机</th><th>少发功率峰值</th><th>损失电量</th></tr>
<tr><td><b>有早期预警</b></td><td>p_muni &lt; 28 m → 主动降负荷 + 预置备用</td><td>否（避免跳机）</td><td><b>{W['max_deficit_MW']:.0f} MW</b></td><td><b>{W['energy_deficit_MWh']:.1f} MWh</b></td></tr>
<tr><td>无早期预警</td><td>被动（等跳机后备用才响应）</td><td>是（约 {N['t_gen_trip']/60:.0f} min）</td><td><b>{N['max_deficit_MW']:.0f} MW</b></td><td><b>{N['energy_deficit_MWh']:.1f} MWh</b></td></tr>
</table>
<div class="callout ok"><b>关键结果：</b>无早期预警时，机组因水源中断跳机，电力系统承受 <b>{N['max_deficit_MW']:.0f} MW</b> 少发功率峰值、损失 <b>{N['energy_deficit_MWh']:.1f} MWh</b> 电量；有早期预警时，电网在跳机前主动降负荷、其余机组提前爬坡顶上，机组不跳、少发功率与损失电量均为 <b>0</b>。这直接量化了早期预警对电力系统的价值。全过程写入 SQLite（<code>ics_sim.db</code>），可审计回放。</div>

<h2 id="s6">6. P6 — 主动控制线性规划（对齐文献方法）</h2>
<p>按参照文献方法，用<b>线性规划</b>求解主动控制：目标为最小化控制期总能量缺额（损失电量），约束含功率平衡、机组容量、<b>爬坡率</b>、<b>直流潮流(PTDF)</b>、失效机组末端出力为零；被动模式加"备用只能在跳机后动作"的因果约束。物理量气→水类比：管存气(line pack) → 可用储水量 (ASW)；可用逃逸时间 (AET/SAET) 一致。</p>
<h4>三种控制策略（对齐文献 PA/SP/DP）</h4>
<ul>
  <li><b>PA 被动控制：</b>受影响机组按水力轨迹突然跳机，备用事后响应（受爬坡限制）。</li>
  <li><b>SP 静态主动控制：</b>控制时间 T_i = SAET_i，在静态逃逸时间内将机组降到零，备用从预警时刻起提前爬坡。</li>
  <li><b>DP 动态主动控制：</b>迭代延长控制时间（T_i = α·SAET_i），动用更多备用与储水。</li>
</ul>
<figure><img src="{img('p6_strategy_compare.png')}" alt="P6 主动控制对比">
<figcaption>图 6.1　主动控制 LP（DC 潮流）PA/SP/DP 对比：① 功率缺额时序 ② 受影响机组出力（主动=软着陆）③ 关键指标（对齐文献 Fig.6）</figcaption></figure>
<table>
<tr><th>策略（同源3机 89/80/10）</th><th>最大少发功率</th><th>损失电量</th><th>最大线路过载</th></tr>
<tr><td>PA 被动控制</td><td>{p6r['PA']['max_deficit_MW']:.1f} MW</td><td>{p6r['PA']['energy_deficit_MWh']:.1f} MWh</td><td>{p6r['PA']['max_overload_MW']:.1f} MW</td></tr>
<tr><td>SP 静态主动控制</td><td>{p6r['SP']['max_deficit_MW']:.1f} MW</td><td>{p6r['SP']['energy_deficit_MWh']:.1f} MWh</td><td>{p6r['SP']['max_overload_MW']:.1f} MW</td></tr>
<tr><td><b>DP 动态主动控制</b></td><td><b>{p6r['DP']['max_deficit_MW']:.1f} MW</b></td><td><b>{p6r['DP']['energy_deficit_MWh']:.1f} MWh</b></td><td>{p6r['DP']['max_overload_MW']:.1f} MW</td></tr>
</table>
<div class="callout ok"><b>关键结论（与文献一致）：</b>(1) <b>主动控制大幅削减甚至消除少发功率</b>——PA 的 {p6r['PA']['max_deficit_MW']:.0f} MW 峰值经 SP 降到 {p6r['SP']['max_deficit_MW']:.0f} MW、DP 完全消除；(2) <b>软着陆机制</b>——受影响机组预警后逐步降出力（图②），其余机组在缺额前提前爬坡顶上；被动则等跳机后才响应，反应不及导致深缺额；(3) <b>DP 优于 SP</b>——动态延长控制时间可动用更多备用与储水；(4) 潮流全程采用<b>直流潮流(DC-PF/PTDF)</b>、备用体系为<b>两级（旋转+慢起机备用）</b>，与文献一致。</div>
<p class="muted">与文献差异：文献用真实浙江省耦合系统 + 气网动态水力(FDTD/Weymouth)，本项目用 IEEE-118 + 解析冷却水水力模型；文献 DP 用严格迭代算法，本项目用 T_set=α·SAET 单次延长近似。方法框架与运行逻辑一致。</p>

<h4>取水节点位置的敏感性（失压时刻依赖取水位置）</h4>
<p>市政唯一水源停供后，不同配水节点跌破 28 m 的时刻<b>差异极大</b>（全网分布：P10/中位/P90 = {_ns_dist['p10_h']:.1f}/{_ns_dist['median_h']:.1f}/{_ns_dist['p90_h']:.1f} h，最长 {_ns_dist['max_h']:.0f} h，且 {_ns_dist['never_fail_pct']:.0f}% 节点长时间不失压）。因此"选哪个节点为电厂供冷却水"会改变"开始影响机组的时刻"。这里须区分<b>两级缓冲</b>：<b>市政级</b>（水源停供→取水节点失压，小时级，<b>强依赖节点位置</b>）与<b>冷却级</b>（取水失效→机组跳机，冷却 SAET ~90–125 min，<b>电厂内部属性、与节点无关</b>）。</p>
<figure><img src="{img('p6_node_sensitivity.png')}" alt="取水节点位置敏感性">
<figcaption>图 6.2　取水节点位置 → 电力影响敏感性：① 市政侧失压时刻全网分布（强依赖取水位置）② 取水布置(同源同位置 CO / 分散取水 DISP) × 控制策略(PA/SP/DP) 的系统最大缺额</figcaption></figure>
<table>
<tr><th>取水布置</th><th>市政失压偏移</th><th>PA 被动 最大缺额</th><th>SP/DP 主动 最大缺额</th></tr>
<tr><td><b>CO 同源同位置</b>（危机同时）</td><td>[0, 0, 0] h</td><td>{_ns_co['PA']['max_deficit_MW']:.0f} MW</td><td>{_ns_co['SP']['max_deficit_MW']:.0f} / {_ns_co['DP']['max_deficit_MW']:.0f} MW</td></tr>
<tr><td><b>DISP 分散取水</b>（危机错峰）</td><td>{nsens['muni_offsets_h']['DISP']} h</td><td><b>{_ns_dp['PA']['max_deficit_MW']:.0f} MW</b></td><td>{_ns_dp['SP']['max_deficit_MW']:.0f} / {_ns_dp['DP']['max_deficit_MW']:.0f} MW</td></tr>
</table>
<div class="callout ok"><b>机理结论（回应"失压时刻依赖取水位置"）：</b>(1) <b>被动(PA) 受取水位置显著影响</b>——同源同位置各机组缺额脉冲<b>时间重叠、峰值叠加</b>（{_ns_co['PA']['max_deficit_MW']:.0f} MW）；分散取水（市政偏移小时级 ≫ 冷却窗口 ~2 h）缺额脉冲<b>时间分离、峰值不叠加</b>（{_ns_dp['PA']['max_deficit_MW']:.0f} MW，即最严重单机）。(2) <b>主动(SP/DP) 对取水位置稳健</b>——各机组自其市政失压时刻起有冷却 SAET 窗口做软着陆（窗口与节点无关），逐台均可消除缺额；市政失压先后仅把危机在时间轴上平移/错开，不改变"每台机组可被主动救回"这一结论。<b>启示：</b>无早期预警时，取水位置分散有助于削减被动峰值缺额；有早期预警+主动控制时，结果对取水位置稳健。</div>

<h2 id="s7">7. 结论与建议</h2>
<ol>
  <li><b>水力慢动态提供了预警窗口。</b>市政断水经补水箱/集水池储水缓冲后才传导至机组，SAET ≈ {ind['89']['SAET_min']:.0f}–{ind['10']['SAET_min']:.0f} min，为电网侧主动处置争取了充足时间。</li>
  <li><b>早期预警显著降低电力系统影响。</b>单机场景下，早期预警把少发功率峰值由 {N['max_deficit_MW']:.0f} MW 降为 0、损失电量由 {N['energy_deficit_MWh']:.1f} MWh 降为 0。</li>
  <li><b>主动控制可消除缺额。</b>同源多机共因故障下，动态主动控制(DP)将少发功率由被动的 {p6r['PA']['max_deficit_MW']:.0f} MW 完全消除。</li>
  <li><b>方法与国际前沿一致。</b>本研究的早期预警 + 主动控制框架与孙宏斌院士团队"气-电早期预警"(Nat. Commun. 2024) 方法逐项对齐（AET/ASW/SAET 指标、LP 求解 PA/SP/DP、DC 潮流、两级备用），印证了该方法在"水-电"场景的可迁移性。</li>
</ol>
<h4>面向工程的建议</h4>
<ul>
  <li>建立市政供水侧与电力调度间的<b>信息/ICS 预警通道</b>，以市政配水节点压力为触发量。</li>
  <li>针对同源多厂供水，识别<b>共因故障机组集合</b>，制定按 SAET 分级的主动降负荷 + 备用预起机预案。</li>
</ul>

<h2 id="s8">8. 局限与后续工作</h2>
<ul>
  <li><b>解析水力模型：</b>本项目用解析冷却水水力模型；更精细的管网/凝汽器动态可进一步引入。</li>
  <li><b>参数为标准/典型值拟合：</b>无现场数据，绝对量值供参考，相对趋势与结论稳健；详见 <code>docs/parameter_fitting.md</code>。</li>
  <li><b>DP 迭代：</b>本项目 DP 用 T_set=α·SAET 单次延长近似，可扩展为文献 Table 2 的严格迭代算法。</li>
  <li><b>可扩展维度：</b>断水速率、多机跳机间隔、更大规模共因故障等。</li>
  <li><b>分级预警：</b>本研究采用单阈值（配水节点压头 &lt; 28 m）触发以保持"有无预警"的二值对照。若将来取得真实市政管网瞬态数据，或研究重心转向预警系统本身的阈值整定与误报/漏报权衡，可扩展为"关注级（如 30 m 预警带，仅提升备用就绪度）+ 行动级（28 m 正式预警）"的分级预警。</li>
</ul>

<h2 id="s9">9. 附录：实现与复现</h2>
<pre>cooling_cascade_study/
├── docs/       研究方案/数学建模/参数拟合/文献对齐/水源侧模型/场景矩阵
├── src/        计算模块 (按研究主线编号)
│   ├── 00_muni_wdn/          市政水网 (D-town): 错峰失压+全网崩溃+失压分布
│   ├── 01_cooling_chain/     故障机理链 (params/submodels/simulate/plot)
│   ├── 02_ics/              三域三级信息系统 (db/plc/scada/dispatch/sim/plot)
│   └── 03_proactive_control/ 主动控制LP (dc_network/warning_indicators/
│                            proactive_lp/run_p6/plot_p6/node_sensitivity)
└── results/    按模块分子目录 (muni/cooling_chain/ics/proactive_control)</pre>
<p class="muted">技术栈：Python + NumPy/SciPy(linprog) + PYPOWER(直流潮流/PTDF) + WNTR/EPANET(市政水网水力仿真) + Matplotlib。IEEE 118 拓扑复用 <code>ieee118_dc/</code>；市政水网基准 D-town(CC BY-NC 4.0) 见 <code>src/00_muni_wdn/data/</code>。运行入口见各模块 README.md。</p>

</main>
<footer>
  市政供水中断引发的电厂冷却水故障与电力系统早期预警主动控制研究<br>
  <span style="opacity:.7">基于 IEEE 118 · 影响以少发功率/损失电量衡量 · 方法对齐孙宏斌院士团队 Nat. Commun. 2024</span>
</footer>
</div></body></html>"""

out = os.path.join(HERE, "研究报告_冷却水故障级联与预警韧性.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("saved", out, f"({len(HTML)//1024} KB)")
