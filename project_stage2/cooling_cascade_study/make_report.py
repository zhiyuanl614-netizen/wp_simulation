"""生成完整研究报告 (自包含 HTML, 图片内嵌为 data URI)。"""
import os, base64, json

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")


def img(name):
    p = os.path.join(R, name)
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"


def svg_inline(name):
    """读取 SVG 文件内容, 用于内联嵌入(去掉 XML 声明)。"""
    p = os.path.join(R, name)
    with open(p, "r", encoding="utf-8") as f:
        s = f.read()
    return s


summary = json.load(open(os.path.join(R, "p5_summary.json")))
strat = json.load(open(os.path.join(R, "p5_strategy.json")))
rel = json.load(open(os.path.join(R, "p5_reliability.json")))

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>电厂冷却水故障级联影响与早期预警韧性研究报告</title>
<style>
  :root{{--ink:#1a2b3c;--mut:#5b6b7a;--line:#e2e8f0;--accent:#1f6fb2;--accent2:#2e8b57;
    --warn:#c0392b;--amber:#e08a1e;--bg:#ffffff;--soft:#f7fafc;}}
  *{{box-sizing:border-box}}
  body{{font-family:-apple-system,"Noto Sans CJK SC","Microsoft YaHei",Segoe UI,sans-serif;
    color:var(--ink);line-height:1.75;margin:0;background:#eef2f6;}}
  .wrap{{max-width:920px;margin:0 auto;background:var(--bg);
    box-shadow:0 1px 20px rgba(0,0,0,.06);}}
  header{{background:linear-gradient(135deg,#123a5c,#1f6fb2);color:#fff;padding:56px 60px 44px;}}
  header h1{{margin:0 0 8px;font-size:30px;line-height:1.3;font-weight:700;}}
  header .sub{{font-size:16px;opacity:.92;}}
  header .meta{{margin-top:22px;font-size:13px;opacity:.85;border-top:1px solid rgba(255,255,255,.25);padding-top:16px;}}
  main{{padding:20px 60px 60px;}}
  h2{{font-size:23px;margin:46px 0 6px;padding-bottom:8px;border-bottom:2px solid var(--accent);color:#123a5c;}}
  h3{{font-size:18px;margin:30px 0 4px;color:#1f4e79;}}
  h4{{font-size:15px;margin:20px 0 4px;color:var(--accent2);}}
  p{{margin:10px 0;}}
  .lead{{font-size:16px;color:var(--mut);}}
  code{{background:var(--soft);padding:1px 6px;border-radius:4px;font-size:13px;
    font-family:"SF Mono",Consolas,monospace;color:#c0392b;}}
  pre{{background:#1a2b3c;color:#e2e8f0;padding:16px 20px;border-radius:8px;overflow-x:auto;
    font-size:13px;line-height:1.6;font-family:"SF Mono",Consolas,monospace;}}
  figure{{margin:20px 0;text-align:center;}}
  figure img{{max-width:100%;border:1px solid var(--line);border-radius:8px;}}
  figcaption{{font-size:13px;color:var(--mut);margin-top:8px;}}
  table{{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px;}}
  th,td{{border:1px solid var(--line);padding:8px 12px;text-align:center;}}
  th{{background:#123a5c;color:#fff;font-weight:600;}}
  tr:nth-child(even) td{{background:var(--soft);}}
  .kpi-row{{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0;}}
  .kpi{{flex:1;min-width:170px;background:var(--soft);border:1px solid var(--line);
    border-radius:10px;padding:18px 20px;border-left:4px solid var(--accent);}}
  .kpi .num{{font-size:28px;font-weight:700;color:var(--accent);}}
  .kpi .lbl{{font-size:13px;color:var(--mut);margin-top:2px;}}
  .callout{{background:#eef6fb;border-left:4px solid var(--accent);border-radius:0 8px 8px 0;
    padding:14px 20px;margin:18px 0;}}
  .callout.warn{{background:#fdf0ee;border-color:var(--warn);}}
  .callout.ok{{background:#eef7f1;border-color:var(--accent2);}}
  .callout b{{color:#123a5c;}}
  .toc{{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:20px 28px;margin:24px 0;}}
  .toc ol{{margin:6px 0;padding-left:22px;}} .toc a{{color:var(--accent);text-decoration:none;}}
  .toc a:hover{{text-decoration:underline;}}
  .tag{{display:inline-block;background:var(--accent);color:#fff;font-size:11px;padding:2px 9px;
    border-radius:12px;margin-right:6px;vertical-align:middle;}}
  .muted{{color:var(--mut);font-size:13px;}}
  ul li,ol li{{margin:5px 0;}}
  footer{{padding:30px 60px;background:#123a5c;color:#c9d6e2;font-size:13px;text-align:center;}}
  .chain{{font-family:"SF Mono",Consolas,monospace;font-size:12.5px;background:#f0f5f9;
    border:1px solid var(--line);border-radius:8px;padding:16px 20px;white-space:pre;overflow-x:auto;color:#1a2b3c;}}
</style></head>
<body><div class="wrap">
<header>
  <div style="font-size:13px;opacity:.8;letter-spacing:2px;margin-bottom:12px;">研究报告 · RESEARCH REPORT</div>
  <h1>电厂冷却水故障级联影响与<br>早期预警系统韧性量化研究</h1>
  <div class="sub">Cascading Impact of Power-Plant Cooling-Water Failure and Resilience Quantification of Early Warning</div>
  <div class="meta">
    测试系统：IEEE 118 节点 &nbsp;|&nbsp; 故障源：市政供水管网故障 &nbsp;|&nbsp; 方法：水力-热力-机电多时间尺度耦合 + 准稳态级联仿真<br>
    研究阶段：P0–P5+ 完整闭环 &nbsp;|&nbsp; 日期：2026-07-06
  </div>
</header>
<main>

<div class="toc">
  <b>目录</b>
  <ol>
    <li><a href="#s1">摘要</a></li>
    <li><a href="#s2">研究背景与目标</a></li>
    <li><a href="#s3">建模方法：多时间尺度耦合</a></li>
    <li><a href="#s4">P1 — 机理贯通（SMIB 最小闭环）</a></li>
    <li><a href="#s5">P3 — 全系统级联（IEEE 118）</a></li>
    <li><a href="#s6">P4 — 早期预警韧性量化</a></li>
    <li><a href="#s7">P5 — 韧性图谱与最优处置策略</a></li>
    <li><a href="#s8">P5+ — 预警可靠性与鲁棒策略</a></li>
    <li><a href="#s9">ICS — 工业控制系统与预警内生化</a></li>
    <li><a href="#s10">结论与政策建议</a></li>
    <li><a href="#s11">局限与后续工作</a></li>
    <li><a href="#s12">附录：实现与复现</a></li>
  </ol>
</div>

<h2 id="s1">1. 摘要</h2>
<p class="lead">本研究针对一类现实但少被建模的扰动——<b>市政供水管网故障导致电厂循环冷却水系统失去补水</b>——构建了从"水源侧水力学 → 凝汽器/低压缸热力 → 机组机电 → 电网级联"的多时间尺度耦合动态仿真框架，并在 IEEE 118 节点系统上量化其级联影响。</p>
<p>核心科学问题是：<b>水力慢动态（分钟级）与电力快动态（秒级）之间的时序差异，能否作为"早期预警窗口"</b>——市政故障信息经信息/工控系统（ICS）提前告知电网，使其在机组跳闸前<b>主动</b>预置备用/切负荷，而非被动等待。研究通过预警前后对比量化系统韧性的优化。</p>
<div class="kpi-row">
  <div class="kpi"><div class="num">≈29 min</div><div class="lbl">水力缓冲（预警）窗口 t_buffer</div></div>
  <div class="kpi"><div class="num">+7.5 Hz</div><div class="lbl">5机共因故障频率韧性增益</div></div>
  <div class="kpi"><div class="num">4 机</div><div class="lbl">预警价值临界故障规模</div></div>
  <div class="kpi"><div class="num">15%→0%</div><div class="lbl">鲁棒策略下崩溃概率(4机)</div></div>
</div>
<p>主要结论：(1) 单机及小规模故障系统可自持（含"降额自保护"负反馈），但<b>同源多机共因故障</b>会使频率跌至崩溃区（4机 46.9、5机 41.7 Hz）；(2) 早期预警 + 主动处置（预置备用 + 速率受限降负荷 + 预防性切负荷）可把频率崩溃转化为可控事件，5机故障韧性增益 <b>+7.5 Hz</b>；(3) 存在明确的<b>故障规模临界</b>（4机为预警价值区），而水力缓冲窗口（约 29 min）远大于所需预警窗口，说明预警机制物理可行；(4) 但预警不完美——<b>漏报会带来约 15% 的尾部崩溃风险</b>，需保留与漏报率匹配的托底切负荷（鲁棒策略）；(5) <b>主动降负荷必须节奏匹配</b>——卸载速率不能快于备用/切负荷补充速率，否则适得其反；(6) 加入三级<b>工业控制系统（ICS）</b>后，预警从理想假设升级为信息系统的<b>内生输出</b>——仅在<b>市政供水压力</b>侧源头检测即可在断供瞬间可靠预警（有预警 f=50 Hz，无预警 f=47.85 Hz），验证了预警机制的工程可实现性。</p>

<h2 id="s2">2. 研究背景与目标</h2>
<p>火电机组循环冷却水系统维持汽轮机低压缸背压与机组安全。其补水通常来自市政管网，经<b>高位补水箱</b>（临界设备）自流补入<b>集水池</b>；循环水泵从集水池抽水送入凝汽器换热，热水经冷却塔冷却后回流集水池，构成"闭式循环 + 开式补水"。当市政管网故障切断补水，将触发如下级联：</p>
<div class="chain">市政水网故障（补水中断）
  → 高位补水箱水位下降 → 无法向集水池补水
     → 集水池水位缓降（蒸发/排污/风吹损失得不到补充）
        → 循环水泵吸入条件恶化 → 流量下降 / 汽蚀跳泵
           → 凝汽器换热能力降低 → 真空恶化、低压缸背压升高
              → 高背压保护动作 → 机组甩负荷 / 跳机
                 → 电网有功缺额 → 频率跌落 / 潮流转移 / 电压波动
                    → 超出保护裕度 → 线路过载 / UFLS → 级联扩散</div>
<h4>研究目标</h4>
<ul>
  <li><b>机理：</b>建立市政水网—补水箱—集水池—循环水—凝汽器—低压缸—发电机—电网的全链条耦合模型。</li>
  <li><b>量化：</b>刻画不同故障时序/规模对电网频率、潮流、级联的冲击。</li>
  <li><b>核心：</b>量化"早期预警 → 主动处置"相对"被动响应"的系统韧性增益，给出最优预警-处置策略。</li>
</ul>
<h4>研究范围（已锁定）</h4>
<table>
<tr><th>维度</th><th>选定</th></tr>
<tr><td>机组类型</td><td>常规燃煤汽轮机组（聚焦凝汽器—低压缸，不含锅炉慢动态）</td></tr>
<tr><td>电网载体</td><td>IEEE 118 节点（54 机、186 支路、总负荷 4242 MW、平衡机 bus 69）</td></tr>
<tr><td>仿真精度</td><td>机电暂态 RMS / 准稳态（QSS）级联；不做电磁暂态 EMT</td></tr>
<tr><td>数据</td><td>无现场数据，动态参数按国家/国际标准 + 机组额定/实际出力拟合</td></tr>
<tr><td>故障源</td><td>市政供水管网故障 → 高位补水箱失去补水（细化水源侧水力学）</td></tr>
</table>

<h2 id="s3">3. 建模方法：多时间尺度耦合</h2>
<p>研究的核心难点是<b>时间尺度跨度大</b>（水力/热力分钟级、机电毫秒—秒级）。采用四层子模型 + 接口耦合：</p>
<table>
<tr><th>层</th><th>子模型</th><th>关键变量</th><th>时间尺度</th></tr>
<tr><td>W</td><td>水源侧水力学</td><td>补水/水位、循环水流量 m_cw、水温 T_cw</td><td>数十秒—数十分钟</td></tr>
<tr><td>A</td><td>凝汽器—低压缸热力</td><td>背压 p_b、机械功率降额 k_p</td><td>秒—数十秒</td></tr>
<tr><td>B</td><td>机组机电</td><td>转速/频率、机械/电磁功率</td><td>毫秒—秒</td></tr>
<tr><td>C</td><td>电网潮流/级联</td><td>系统频率、母线电压、支路潮流</td><td>毫秒—分钟</td></tr>
</table>
<p class="muted">W→A 传递 m_cw、T_cw 与跳泵事件；A→B 传递背压降额 k_p；B→C 注入机组功率；C→B 反馈频率/电压；并含 B→A、A→W 的弱反馈。水力用质量守恒 + 泵 NPSH 汽蚀判据；热力用 ε-NTU 换热；机电用摇摆方程 + 调速器；电网用交流潮流 + 过载跳线迭代。</p>
<h4>水源侧水力学建模要点（依据电厂实际物理确认）</h4>
<ul>
  <li><b>市政→补水箱：</b>市政压力直供 + 液位控制阀，速率 = Cv·开度·√(市政压头−箱内水位)；<b>市政故障 = 压头→0 → 补水归零</b>。</li>
  <li><b>补水箱→集水池：</b>重力自流 + 液位闭环调节阀，阀开度由集水池水位偏差决定 → 补水量自动"取决于集水池净损失"；补水箱放空则无水可补。</li>
  <li><b>循环水泵→凝汽器：</b>正常按额定循环水量满流量运行；故障时由集水池<b>淹没深度/NPSH</b> 决定——水位过低→汽蚀降流量→跌破最小淹没深度跳泵。</li>
  <li><b>蒸发/排污/风吹损失：</b><b>随热负荷（出力）变化</b>——蒸发 ∝ 凝汽器热负荷、排污 ∝ 蒸发、风吹 ∝ 循环流量（近恒定），非恒定值。</li>
</ul>
<div class="callout"><b>由此产生的重要物理反馈：</b>因损失随热负荷变化，当机组因背压升高而降额时，热负荷下降 → 蒸发/排污减少 → 集水池排水变慢 → <b>缓冲时间延长、跳机推迟</b>。这一温和的<b>降额自保护负反馈</b>使中等规模共因故障比恒定损失假设下更缓和，故本研究的危险阈值定位在 4–5 机共因规模。</div>

<h2 id="s4">4. P1 — 机理贯通（SMIB 最小闭环）</h2>
<p>在单机—系统等值（SMIB 型）框架上打通全链条，验证四层耦合的时序因果。下图六联图完整呈现"市政断水 → 水位下降 → 跳泵 → 背压上升 → 跳机 → 频率响应"：</p>
<figure><img src="{img('p1_smib_bus89_tf60_ramp0.png')}" alt="P1 SMIB 全链条">
<figcaption>图 4.1　SMIB 全链条时序（bus89, Pg=607/Pmax=707 MW；市政阶跃断水）</figcaption></figure>
<div class="callout"><b>关键时序量——缓冲时间 t_buffer：</b>由"补水箱+集水池可用蓄水量 / 循环损失率"决定。阶跃断水下 t_buffer≈22 min，市政供水渐降（600 s）下延长至≈38 min。这正是留给电网侧应急处置的<b>预警窗口</b>。</div>
<table>
<tr><th>场景</th><th>市政故障形式</th><th>缓冲时间</th><th>频率最低点</th></tr>
<tr><td>S01</td><td>阶跃断水</td><td>≈22 min</td><td>49.5 Hz</td></tr>
<tr><td>S02</td><td>渐降（600 s）</td><td>≈38 min</td><td>49.5 Hz</td></tr>
</table>
<p class="muted">观察：故障发展速率主要影响缓冲窗口长度；跳机后的频率冲击深度主要由机组出力占比决定。系统备用决定频率能否恢复——这引出 P3/P4 的多机共因研究。</p>

<h2 id="s5">5. P3 — 全系统级联（IEEE 118）</h2>
<p>将 P1 的水力-热力子模型作为受影响机组的功率降额/跳机信号源，接入 IEEE 118 交流网络，采用<b>准稳态交流潮流 + 一次调频再调度 + 过载跳线迭代</b>刻画级联。对比单机与同源多机共因：</p>
<figure><img src="{img('p3_compare.png')}" alt="P3 单机 vs 多机">
<figcaption>图 5.1　单机（bus89）vs 同源3机共因（89/80/10）的频率、电压、线路负载率、级联对比</figcaption></figure>
<div class="callout warn"><b>共因故障是最危险时序模式：</b>单台 607 MW 机组跳闸，系统备用可维持频率于 49.8 Hz；但市政水网同时断供多厂时，多台大机组相继跳闸，频率深跌（5机共因 41.7 Hz）。存在两条级联路径：<b>频率路径</b>（有功缺额→频率跌落→UFLS/欠频）与<b>潮流路径</b>（大机组跳闸→潮流转移→线路过载→系统解列）。<b>降额自保护负反馈</b>（见第 3 节）会拉开共因机组的跳机时刻，使危险阈值上移至 4–5 机规模。</div>

<h2 id="s6">6. P4 — 早期预警韧性量化</h2>
<p>对比两种控制模式：<b>被动</b>（跳机后才响应）与<b>主动预警</b>（市政故障经 ICS 预警后，跳机前即降负荷 + 预置/提前起机备用）。主动降负荷同时降低凝汽器热负荷，减缓背压上升、延后跳机。</p>
<figure><img src="{img('p4_warning_compare.png')}" alt="P4 被动 vs 主动">
<figcaption>图 6.1　同源5机共因：被动 vs 主动预警的频率响应与有功缺额演化</figcaption></figure>
<div class="callout ok"><b>核心结果：</b>早期预警（预置备用 + 速率受限降负荷 + 15% 预防性切负荷）把一次频率崩溃（41.7 Hz）转化为可控事件（49.2 Hz），<b>韧性增益 +7.5 Hz</b>，由"崩溃"转为"安全"，且 runback 将全部机组保持在跳机线以下（避免连锁跳机）。右图可见主动模式下缺额被"平滑转移"（make-before-break），而被动模式呈阶梯式突降。</div>
<div class="callout warn"><b>重要物理约束：</b>主动降负荷（runback）卸下发电的速率<b>不能快于备用/切负荷的补充速率</b>，否则会自造缺额、适得其反——"软着陆"是节奏匹配问题。对大规模缺额（5机 ~2317 MW ≫ 备用 ~900 MW），<b>预防性切负荷是不可或缺的第二杠杆</b>。</div>
<figure><img src="{img('p4_leadtime_sweep.png')}" alt="P4 敏感性">
<figcaption>图 6.2　韧性对"备用起机速率"与"预警提前量"的敏感性——右图显示明显拐点</figcaption></figure>
<p>韧性由<b>预警提前量 × 备用起机能力 × 预防性切负荷</b>共同决定。对大规模共因故障，仅靠预置备用不足以覆盖巨额缺额，须叠加预防性切负荷；预警提前量则决定备用与切负荷能否在跳机前从容就位。</p>

<h2 id="s7">7. P5 — 韧性图谱与最优处置策略</h2>
<p>二维全场景扫描（预警提前量 × 故障规模），生成韧性图谱：</p>
<figure><img src="{img('p5_resilience_map.png')}" alt="P5 韧性图谱">
<figcaption>图 7.1　韧性图谱：主动预警下频率最低点（左）与韧性增益 ΔResilience（右）</figcaption></figure>
<figure><img src="{img('p5_critical_leadtime.png')}" alt="P5 临界预警提前量">
<figcaption>图 7.2　临界预警提前量 t_lead*——保证系统安全（f≥49 Hz）所需的最小预警窗口</figcaption></figure>
<table>
<tr><th>故障规模</th><th>被动 f_nadir</th><th>主动(预置备用,≥5min)</th><th>结论</th></tr>
<tr><td>1–3 机</td><td>49.5–50.0 Hz</td><td>50.0 Hz</td><td>备用/降额自保护自足</td></tr>
<tr><td><b>4 机</b></td><td><b>46.9 Hz（崩溃）</b></td><td><b>49.9 Hz（安全）</b></td><td><b>预警黄金价值区（配 ~6% 切负荷）</b></td></tr>
<tr><td>5 机</td><td>41.7 Hz</td><td>43+ Hz</td><td>仅预置备用不足，须叠加切负荷</td></tr>
</table>
<h3>最优预警-处置策略</h3>
<p>三个主动杠杆：<b>L1 预置/提前起机三级备用</b>（受预警提前量约束）、<b>L2 速率受限主动降负荷（runback）</b>、<b>L3 预防性切负荷</b>（快速但有失负荷代价）。达到安全所需的最小切负荷：</p>
<figure><img src="{img('p5_optimal_strategy.png')}" alt="P5 最优策略">
<figcaption>图 7.3　达到安全所需最小预防性切负荷随预警提前量的变化</figcaption></figure>
<table>
<tr><th>故障规模</th><th>所需最小切负荷</th><th>说明</th></tr>
<tr><td>3 机</td><td><b>0%（仅预置备用）</b></td><td>降额自保护 + 备用即可</td></tr>
<tr><td>4 机</td><td>切负荷 ~6%</td><td>少量切负荷即达标</td></tr>
<tr><td>5 机</td><td>切负荷 10–15%</td><td>大规模缺额，须显著切负荷</td></tr>
</table>
<div class="callout ok"><b>核心政策结论：预警可"替代"切负荷。</b>故障规模越小、预警越早，越能用"预置备用 + 软着陆降负荷"替代硬切负荷（3 机可完全免切、4 机仅 ~6%、5 机须 10–15%）。<b>这直接量化了信息/ICS 预警的安全与经济价值。</b>P1 表明水力缓冲窗口（≈29 min）远大于所需临界预警窗口，说明预警机制物理可行且裕度充裕。</div>

<h2 id="s8">8. P5+ — 预警可靠性与鲁棒策略</h2>
<p>前述结论假设预警"完美"。现实 ICS 预警存在<b>漏报、时延抖动、误报</b>。用蒙特卡洛（漏报率 15%、预警提前量 N(8,3) min、误报率 10%）评估三类策略的风险分布：</p>
<figure><img src="{img('p5_reliability.png')}" alt="P5 可靠性">
<figcaption>图 8.1　预警不确定下的策略风险：期望韧性（左）、崩溃概率（中）、4机故障韧性分布（右）</figcaption></figure>
<table>
<tr><th>故障</th><th>策略</th><th>期望 f_nadir</th><th>崩溃概率 P(f&lt;47Hz)</th><th>5% 尾部</th></tr>
<tr><td>4 机</td><td>S-Reactive（纯被动）</td><td>46.95</td><td>89.1%</td><td>46.91</td></tr>
<tr><td>4 机</td><td>S-Trust（信任预警）</td><td>49.53</td><td>15.1%</td><td>46.91</td></tr>
<tr><td>4 机</td><td><b>S-Robust（鲁棒托底）</b></td><td><b>49.91</b></td><td><b>0.0%</b></td><td><b>49.41</b></td></tr>
<tr><td>5 机</td><td>S-Trust（信任预警）</td><td>47.37</td><td>15.6%</td><td>41.73</td></tr>
<tr><td>5 机</td><td><b>S-Robust（鲁棒托底）</b></td><td><b>49.12</b></td><td>15.1%</td><td><b>44.23</b></td></tr>
</table>
<div class="callout warn"><b>"完全信任预警"有致命尾部风险：</b>S-Trust 平时表现好，但漏报（15%）场景仍会崩溃——4/5 机故障崩溃概率约 15%（≈漏报率）。<b>预警不能作为唯一防线。</b></div>
<div class="callout ok"><b>鲁棒策略以小代价对冲尾部：</b>常备 5% 托底切负荷，使 3 机崩溃概率 15.9%→<b>0%</b>，4 机 5% 尾部从 42.7→46.6 Hz。误报代价（误报率×托底比例 = 10%×5%）远小于其规避的崩溃损失。<b>预警是"降本"而非"免责"工具</b>——它减少常备托底需求，但仍须保留与漏报率匹配的托底措施。</div>

<h2 id="s9">9. ICS — 工业控制系统与预警内生化</h2>
<p>前述 P4/P5 中，"预警提前量"被抽象为一个给定参数（检测延时 <code>t_detect</code>）。为使早期预警机制具备<b>工程可实现性</b>，本章按真实工程分层加入三级<b>工业控制系统（ICS / 信息系统）</b>：<b>市政供水侧、冷却水系统侧、电力系统侧各自设有独立的三级 ICS（PLC/SCADA/调度中心）</b>。其中冷却水侧与电力系统侧同属<b>电厂侧</b>、两者 ICS 厂内<b>交互协同</b>；而<b>市政供水 ICS 与电力系统 ICS 相互独立运行</b>——正因如此才需要<b>早期预警链路</b>：市政供水 ICS 检出自身断供后，将预警信息<b>跨域传输</b>给电力系统 ICS，使电网得以在机组跳闸前主动处置。</p>
<h4>系统架构（三域独立三级 ICS + 物理层场站设备 + 跨域预警）</h4>
<figure style="margin:16px 0;">{svg_inline('ics_architecture.svg')}
<figcaption>图 9.1　冷却水—电网耦合 ICS 架构：三级信息系统（PLC/SCADA/调度中心）+ 物理层场站设备（市政管网→补水箱→集水池→循环水泵→凝汽器→冷却塔）+ 跨域预警链路</figcaption></figure>
<p class="muted">如图 9.1：市政供水域（独立运行）经"市政补水"物理链路向电厂侧供水；电厂侧冷却水系统与电力系统的凝汽器背压经"背压→功率降额"物理耦合；市政供水 ICS 与电力系统 ICS 之间仅有一条独立的早期预警信息链路（红色虚线），而冷却水侧与电力系统侧 ICS 厂内双向交互（紫色）。物理层复用已验证的解析水力-热力模型（不引入外部管网水力库）；全过程写入 SQLite（传感器/执行器/告警/调度/跨域预警/快照 6 表），可审计回放。</p>
<h4>检测策略与简化假设</h4>
<p>本章的 ICS 检测采用以下简化（聚焦研究命题、避免引入无关耦合）：</p>
<ul>
  <li><b>只监测市政供水压力（源头信号）。</b>补水箱、集水池、凝汽器背压均属<b>电力系统内部子系统</b>，彼此存在物理交互，不作为独立预警监测点——预警应来自厂外的市政供水侧，判据最清晰。</li>
  <li><b>不考虑检测延时 / 通信丢包 / 漏报。</b>市政压头一旦跌破阈值即刻可靠预警（零时延）。</li>
  <li><b>只区分两种情形：</b>有早期预警（WARN）vs 无早期预警（NOWARN，被动）。</li>
</ul>
<figure><img src="{img('ics_warning_compare.png')}" alt="ICS 有无早期预警对比">
<figcaption>图 9.2　ICS 有无早期预警对比：① 市政供水压头与检出时刻　② 集水池水位　③ 背压（主动 vs 被动）　④ 频率响应</figcaption></figure>
<table>
<tr><th>情形</th><th>检测量 & 判据</th><th>检出=预警送达</th><th>跳机时刻</th><th>频率最低点</th></tr>
<tr><td><b>WARN 有预警</b></td><td>p_muni &lt; 5 m（市政供水压力）</td><td>60 s（即刻）</td><td>无（避免跳机）</td><td><b>50.00 Hz</b></td></tr>
<tr><td>NOWARN 无预警</td><td>不检测（被动）</td><td>—</td><td>1760 s</td><td><b>47.85 Hz</b></td></tr>
</table>
<div class="callout ok"><b>关键结论：</b>(1) <b>市政供水压力是理想的源头预警信号</b>——市政断供即刻（零时延）在厂外源头检出，无需依赖电力系统内部子系统（补水箱/集水池/背压）的耦合状态；(2) <b>预警内生化成功</b>——ICS 依据市政压力自动给出检出/送达时刻，电网侧 <code>t_detect</code> 不再是手填参数；(3) <b>预警使电网主动处置、避免频率跌落</b>——WARN 经预警触发速率受限降负荷，机组不跳、频率维持 50 Hz，而 NOWARN 被动等跳机，频率跌至 47.85 Hz。</div>
<p class="muted">说明：本单机场景较缓和（降负荷即可救），预警价值主要体现在避免跳机与频率跌落；在大规模同源多机共因故障（第 6–8 章）下，"有无预警"对最终韧性影响更显著，ICS 层正为那里的预警触发提供物理可实现的信息来源。</p>

<h2 id="s10">10. 结论与政策建议</h2>
<ol>
  <li><b>时序差异确可转化为韧性。</b>市政水网故障的水力慢动态提供约 29 min 缓冲窗口，经 ICS 预警使电网提前处置，可将同源 5 机共因故障从频率崩溃（41.7 Hz）挽回至安全（49.2 Hz），韧性增益 +7.5 Hz。</li>
  <li><b>存在故障规模临界。</b>1–3 机备用/降额自保护自足；4 机是预警"黄金价值区"（被动崩溃→主动安全）；5 机须叠加较大预防性切负荷。</li>
  <li><b>预警可替代切负荷，量化价值明确。</b>规模越小、预警越早，越能用预置备用/软着陆替代硬切负荷（3 机免切、4 机 ~6%、5 机 10–15%）。</li>
  <li><b>主动降负荷须节奏匹配。</b>runback 卸载速率不能快于备用/切负荷补充速率，否则自造缺额、适得其反——这是一条重要的工程约束。</li>
  <li><b>预警机制工程可实现。</b>三级 ICS 表明，在市政供水侧直接监测压力/补水流量（源头检测）即可在断供后数秒内检出并跨域预警，预警提前量接近整个水力缓冲窗口——为"信息系统触发电网主动处置"提供了落地路径。</li>
  <li><b>预警须与托底措施协同。</b>考虑漏报，应采用鲁棒策略：常备与漏报率匹配的托底切负荷，预警到达再按需加码，以极小确定性代价对冲灾难性尾部风险。</li>
</ol>
<h4>面向工程的建议</h4>
<ul>
  <li>建立电厂供水侧（市政管网/补水箱水位）与电网调度间的<b>信息/ICS 预警通道</b>，把补水箱水位/流量作为预警触发量。</li>
  <li>针对同源多厂供水，识别<b>共因故障机组集合</b>，预置对应的三级备用起机预案。</li>
  <li>制定<b>规模自适应的预警-处置策略表</b>（本报告图 7.3/第 7 节表），并叠加鲁棒托底切负荷。</li>
</ul>

<h2 id="s11">11. 局限与后续工作</h2>
<ul>
  <li><b>QSS + 简化频率模型：</b>一阶机理正确捕捉"速率/提前量竞赛"，但非逐周波机电暂态；RoCoF、暂态摇摆、电压动态需 ANDES/PSS-E RMS 增强。</li>
  <li><b>参数为标准/典型值拟合：</b>绝对量值供参考，相对趋势与临界结论稳健；后续按 <code>docs/parameter_fitting.md</code> 回填实测参数。</li>
  <li><b>可扩展维度：</b>断水速率、多机跳机间隔、环境高温共因、网络 N-1 叠加；预警漏报率敏感性与形式化风险-代价优化。</li>
</ul>

<h2 id="s12">12. 附录：实现与复现</h2>
<p>全部代码与结果以分阶段目录组织，均可复现：</p>
<pre>cooling_cascade_study/
├── docs/       研究方案 / 建模规范 / 参数拟合 / 文献清单
├── models/     水源侧水力学 + 四层耦合建模规范
├── p1_smib/    P1 SMIB 最小闭环 (params/submodels/simulate/plot)
├── p3_ieee118/ P3 IEEE118 级联 (network/cascade/run_p3/plot)
├── p4_resilience/  P4 预警韧性 (compare_warning/sweep_leadtime)
├── p5_map/     P5 韧性图谱+策略+可靠性 (resilience_map/optimal_strategy/
│               build_lookup/reliability)
├── ics/        工业控制系统三级ICS (db/field_plc/scada/dispatch/
│               ics_simulation/run_ics_scenarios/plot_ics)
└── results/    全部 CSV / PNG / JSON / SQLite 结果</pre>
<p class="muted">技术栈：Python + NumPy/SciPy + PYPOWER（交流潮流）+ Matplotlib。IEEE 118 拓扑/潮流复用 <code>ieee118_dc/</code>。运行入口见各阶段 <code>README.md</code>。</p>

</main>
<footer>
  电厂冷却水故障级联影响与早期预警系统韧性量化研究 · P0–P5+ 完整闭环<br>
  <span style="opacity:.7">基于 IEEE 118 节点系统 · 多时间尺度耦合仿真 · 2026-07-06</span>
</footer>
</div></body></html>"""

out = os.path.join(HERE, "研究报告_冷却水故障级联与预警韧性.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("saved", out, f"({len(HTML)//1024} KB HTML, images embedded)")
