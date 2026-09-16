#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate vector SVG diagrams for:
  - Fig1_CPS_framework.svg: 4-layer CPS framework + 3-Domain 3-Level ICS & Early Warning link (§2.1)
  - Fig2_cooling_water_chain.svg: Physical cooling water cascade process chain (§2.3)
  - Fig3_timescale_gap_mechanism.svg: Timescale separation and early warning proactive control (§2.4)
"""
import os

FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def make_fig1():
    """Fig 1: 4-layer CPS framework and 3-Domain 3-Level ICS with cross-domain early warning link."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 650" width="1000" height="650" style="background:#ffffff; font-family:Arial, Helvetica, sans-serif;">
  <defs>
    <linearGradient id="muniGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#eaf3fb"/>
      <stop offset="100%" stop-color="#d4e6f7"/>
    </linearGradient>
    <linearGradient id="coolGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e8f8f5"/>
      <stop offset="100%" stop-color="#d1f2eb"/>
    </linearGradient>
    <linearGradient id="powerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fef5e7"/>
      <stop offset="100%" stop-color="#fdebd0"/>
    </linearGradient>
    <linearGradient id="icsGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f4f6f7"/>
      <stop offset="100%" stop-color="#eaeded"/>
    </linearGradient>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#5b6b7a"/>
    </marker>
    <marker id="arrowBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2980b9"/>
    </marker>
    <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#e74c3c"/>
    </marker>
    <marker id="arrowGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#27ae60"/>
    </marker>
  </defs>

  <!-- Title / Outer Container -->
  <rect x="15" y="15" width="970" height="620" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>

  <!-- Left Column: Physical Layer (4 Layers) -->
  <rect x="35" y="35" width="560" height="580" rx="6" fill="#fafbfc" stroke="#94a3b8" stroke-width="1.2"/>
  <text x="55" y="65" font-size="16" font-weight="bold" fill="#1e293b">Physical Domain · 四层物理耦合过程</text>

  <!-- Layer 1: Municipal Water -->
  <g transform="translate(55, 80)">
    <rect x="0" y="0" width="520" height="105" rx="6" fill="url(#muniGrad)" stroke="#2980b9" stroke-width="1.5"/>
    <text x="15" y="24" font-size="13" font-weight="bold" fill="#1b4f72">① 市政供水层 (Municipal Water Layer)</text>
    <rect x="15" y="36" width="140" height="55" rx="4" fill="#ffffff" stroke="#2980b9" stroke-width="1"/>
    <text x="85" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#1b4f72">水源与水厂</text>
    <text x="85" y="76" font-size="10" text-anchor="middle" fill="#5b6b7a">Reservoir / Source</text>

    <line x1="155" y1="63" x2="190" y2="63" stroke="#2980b9" stroke-width="1.5" marker-end="url(#arrowBlue)"/>

    <rect x="195" y="36" width="145" height="55" rx="4" fill="#ffffff" stroke="#2980b9" stroke-width="1"/>
    <text x="267" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#1b4f72">主干管网与水箱</text>
    <text x="267" y="76" font-size="10" text-anchor="middle" fill="#5b6b7a">D-town 399 Nodes</text>

    <line x1="340" y1="63" x2="375" y2="63" stroke="#2980b9" stroke-width="1.5" marker-end="url(#arrowBlue)"/>

    <rect x="380" y="36" width="125" height="55" rx="4" fill="#fdedec" stroke="#e74c3c" stroke-width="1.5"/>
    <text x="442" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#c0392b">取水配水节点</text>
    <text x="442" y="76" font-size="10" text-anchor="middle" fill="#c0392b">H &lt; 28 m (失效源)</text>
  </g>

  <!-- Physical Coupling Arrow 1->2 -->
  <path d="M 497 185 L 497 205" stroke="#2980b9" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <text x="505" y="198" font-size="10" fill="#2980b9" font-weight="bold">补水中断</text>

  <!-- Layer 2: Cooling Water System -->
  <g transform="translate(55, 210)">
    <rect x="0" y="0" width="520" height="115" rx="6" fill="url(#coolGrad)" stroke="#17a2b8" stroke-width="1.5"/>
    <text x="15" y="24" font-size="13" font-weight="bold" fill="#0e6251">② 电厂循环冷却水层 (Cooling Water Layer · 创新点 1)</text>

    <rect x="15" y="36" width="115" height="65" rx="4" fill="#ffffff" stroke="#17a2b8" stroke-width="1"/>
    <text x="72" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#0e6251">高位补水箱</text>
    <text x="72" y="74" font-size="10" text-anchor="middle" fill="#5b6b7a">Tank (V_mk)</text>
    <text x="72" y="89" font-size="9" text-anchor="middle" fill="#7f8c8d">质量守恒缓冲</text>

    <line x1="130" y1="68" x2="160" y2="68" stroke="#17a2b8" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="165" y="36" width="115" height="65" rx="4" fill="#ffffff" stroke="#17a2b8" stroke-width="1"/>
    <text x="222" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#0e6251">集水池缓冲</text>
    <text x="222" y="74" font-size="10" text-anchor="middle" fill="#5b6b7a">Basin (V_b)</text>
    <text x="222" y="89" font-size="9" text-anchor="middle" fill="#7f8c8d">SAET=88–125 min</text>

    <line x1="280" y1="68" x2="310" y2="68" stroke="#17a2b8" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="315" y="36" width="95" height="65" rx="4" fill="#ffffff" stroke="#17a2b8" stroke-width="1"/>
    <text x="362" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#0e6251">循环水泵</text>
    <text x="362" y="74" font-size="10" text-anchor="middle" fill="#5b6b7a">Pump</text>
    <text x="362" y="89" font-size="9" text-anchor="middle" fill="#c0392b">NPSH 汽蚀</text>

    <line x1="410" y1="68" x2="435" y2="68" stroke="#17a2b8" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="440" y="36" width="70" height="65" rx="4" fill="#ffffff" stroke="#e08a1e" stroke-width="1"/>
    <text x="475" y="58" font-size="10" font-weight="bold" text-anchor="middle" fill="#b9770f">冷却塔</text>
    <text x="475" y="74" font-size="9" text-anchor="middle" fill="#5b6b7a">Tower</text>
    <text x="475" y="89" font-size="8" text-anchor="middle" fill="#7f8c8d">散热/蒸发</text>
  </g>

  <!-- Physical Coupling Arrow 2->3 -->
  <path d="M 362 325 L 362 345" stroke="#17a2b8" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="370" y="338" font-size="10" fill="#17a2b8" font-weight="bold">循环流量衰减</text>

  <!-- Layer 3: Condenser & LP Turbine -->
  <g transform="translate(55, 350)">
    <rect x="0" y="0" width="520" height="105" rx="6" fill="url(#powerGrad)" stroke="#e08a1e" stroke-width="1.5"/>
    <text x="15" y="24" font-size="13" font-weight="bold" fill="#7e5109">③ 凝汽器与热力机组层 (Thermal &amp; Turbine Layer)</text>

    <rect x="40" y="36" width="180" height="55" rx="4" fill="#ffffff" stroke="#e08a1e" stroke-width="1"/>
    <text x="130" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#7e5109">凝汽器换热 (ε-NTU)</text>
    <text x="130" y="76" font-size="10" text-anchor="middle" fill="#5b6b7a">换热恶化 → 背压 P_c 爬升</text>

    <line x1="220" y1="63" x2="280" y2="63" stroke="#e08a1e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="285" y="36" width="195" height="55" rx="4" fill="#ffffff" stroke="#e08a1e" stroke-width="1"/>
    <text x="382" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#7e5109">低压缸与保护跳机</text>
    <text x="382" y="76" font-size="10" text-anchor="middle" fill="#c0392b">降额系数 k_p / P_c &gt; 35 kPa 跳机</text>
  </g>

  <!-- Physical Coupling Arrow 3->4 -->
  <path d="M 382 455 L 382 475" stroke="#c0392b" stroke-width="2" marker-end="url(#arrowRed)"/>
  <text x="390" y="468" font-size="10" fill="#c0392b" font-weight="bold">出力受限 / 突跳</text>

  <!-- Layer 4: Power System -->
  <g transform="translate(55, 480)">
    <rect x="0" y="0" width="520" height="115" rx="6" fill="#fdf2e9" stroke="#c0392b" stroke-width="1.5"/>
    <text x="15" y="24" font-size="13" font-weight="bold" fill="#922b21">④ 电力系统与电网层 (Power Grid Layer)</text>

    <rect x="20" y="36" width="145" height="65" rx="4" fill="#ffffff" stroke="#c0392b" stroke-width="1"/>
    <text x="92" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#922b21">受影响机组</text>
    <text x="92" y="74" font-size="10" text-anchor="middle" fill="#5b6b7a">Pg 降额 / 跳机</text>
    <text x="92" y="89" font-size="9" text-anchor="middle" fill="#c0392b">缺额冲击 (485.6 MW)</text>

    <line x1="165" y1="68" x2="195" y2="68" stroke="#c0392b" stroke-width="1.5" marker-end="url(#arrowRed)"/>

    <rect x="200" y="36" width="145" height="65" rx="4" fill="#ffffff" stroke="#27ae60" stroke-width="1"/>
    <text x="272" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#1e8449">备用机组预起机</text>
    <text x="272" y="74" font-size="10" text-anchor="middle" fill="#5b6b7a">Spinning Reserve</text>
    <text x="272" y="89" font-size="9" text-anchor="middle" fill="#1e8449">爬坡 R · 空间消纳</text>

    <line x1="345" y1="68" x2="375" y2="68" stroke="#c0392b" stroke-width="1.5" marker-end="url(#arrowRed)"/>

    <rect x="380" y="36" width="125" height="65" rx="4" fill="#ffffff" stroke="#c0392b" stroke-width="1"/>
    <text x="442" y="58" font-size="11" font-weight="bold" text-anchor="middle" fill="#922b21">IEEE-118 输电网</text>
    <text x="442" y="74" font-size="10" text-anchor="middle" fill="#5b6b7a">PTDF 潮流平衡</text>
    <text x="442" y="89" font-size="9" text-anchor="middle" fill="#5b6b7a">负荷 4242 MW</text>
  </g>

  <!-- Right Column: Cyber / ICS Domain -->
  <rect x="615" y="35" width="350" height="580" rx="6" fill="#f8fafc" stroke="#64748b" stroke-width="1.2"/>
  <text x="635" y="65" font-size="16" font-weight="bold" fill="#0f172a">Cyber Domain · 三域三级 ICS</text>

  <!-- Municipal ICS -->
  <g transform="translate(635, 80)">
    <rect x="0" y="0" width="310" height="110" rx="6" fill="url(#icsGrad)" stroke="#2980b9" stroke-width="1.2"/>
    <text x="12" y="22" font-size="12" font-weight="bold" fill="#1b4f72">市政供水域 ICS (Municipal Domain)</text>
    <rect x="12" y="32" width="85" height="65" rx="3" fill="#ffffff" stroke="#2980b9" stroke-width="1"/>
    <text x="54" y="52" font-size="10" font-weight="bold" text-anchor="middle" fill="#1b4f72">Field PLC</text>
    <text x="54" y="70" font-size="9" text-anchor="middle" fill="#5b6b7a">压力传感器</text>
    <text x="54" y="85" font-size="8" text-anchor="middle" fill="#7f8c8d">1s 周期采集</text>

    <line x1="97" y1="64" x2="115" y2="64" stroke="#5b6b7a" stroke-width="1" marker-end="url(#arrow)"/>

    <rect x="118" y="32" width="90" height="65" rx="3" fill="#ffffff" stroke="#2980b9" stroke-width="1"/>
    <text x="163" y="52" font-size="10" font-weight="bold" text-anchor="middle" fill="#1b4f72">SCADA</text>
    <text x="163" y="70" font-size="9" text-anchor="middle" fill="#e74c3c">H &lt; 28 m 检出</text>
    <text x="163" y="85" font-size="8" text-anchor="middle" fill="#7f8c8d">15s 扫描周期</text>

    <line x1="208" y1="64" x2="223" y2="64" stroke="#5b6b7a" stroke-width="1" marker-end="url(#arrow)"/>

    <rect x="225" y="32" width="75" height="65" rx="3" fill="#fdedec" stroke="#e74c3c" stroke-width="1.2"/>
    <text x="262" y="52" font-size="10" font-weight="bold" text-anchor="middle" fill="#c0392b">管网调度</text>
    <text x="262" y="70" font-size="9" text-anchor="middle" fill="#c0392b">越限触发</text>
    <text x="262" y="85" font-size="8" text-anchor="middle" fill="#c0392b">跨域预警</text>
  </g>

  <!-- Cross-Domain Early Warning Highway (Key Innovation 2) -->
  <g transform="translate(635, 200)">
    <rect x="0" y="0" width="310" height="70" rx="5" fill="#fef9e7" stroke="#e74c3c" stroke-width="2" stroke-dasharray="6,3"/>
    <text x="155" y="24" font-size="12" font-weight="bold" text-anchor="middle" fill="#c0392b">★ 跨域早期预警链路 (Cross-Domain Early Warning)</text>
    <text x="155" y="44" font-size="10" text-anchor="middle" fill="#7e5109">市政越限即刻直报电网调度 (零时延 · 跨域时间差通道)</text>
    <text x="155" y="60" font-size="9" text-anchor="middle" fill="#5b6b7a">将 88.6–124.8 min 慢动态耗竭转化为快响应主动控制窗口</text>
  </g>
  <path d="M 897 190 L 897 200" stroke="#e74c3c" stroke-width="2" marker-end="url(#arrowRed)"/>
  <path d="M 790 270 L 790 480" stroke="#e74c3c" stroke-width="2" marker-end="url(#arrowRed)"/>

  <!-- Power ICS -->
  <g transform="translate(635, 480)">
    <rect x="0" y="0" width="310" height="115" rx="6" fill="url(#icsGrad)" stroke="#c0392b" stroke-width="1.2"/>
    <text x="12" y="22" font-size="12" font-weight="bold" fill="#922b21">电力域 ICS (Power Domain)</text>

    <rect x="12" y="32" width="90" height="70" rx="3" fill="#fdedec" stroke="#c0392b" stroke-width="1.2"/>
    <text x="57" y="50" font-size="10" font-weight="bold" text-anchor="middle" fill="#922b21">调度中心 EMS</text>
    <text x="57" y="66" font-size="9" text-anchor="middle" fill="#c0392b">收到预警信号</text>
    <text x="57" y="81" font-size="9" text-anchor="middle" fill="#1e8449">启动主动 LP</text>
    <text x="57" y="94" font-size="8" text-anchor="middle" fill="#5b6b7a">SP / DP 优化</text>

    <line x1="102" y1="67" x2="118" y2="67" stroke="#5b6b7a" stroke-width="1" marker-end="url(#arrow)"/>

    <rect x="120" y="32" width="90" height="70" rx="3" fill="#ffffff" stroke="#c0392b" stroke-width="1"/>
    <text x="165" y="50" font-size="10" font-weight="bold" text-anchor="middle" fill="#922b21">电厂 SCADA</text>
    <text x="165" y="66" font-size="9" text-anchor="middle" fill="#5b6b7a">受影响机组:</text>
    <text x="165" y="81" font-size="9" text-anchor="middle" fill="#b9770f">Runback 下调</text>
    <text x="165" y="94" font-size="8" text-anchor="middle" fill="#7f8c8d">备用机组: 预起</text>

    <line x1="210" y1="67" x2="223" y2="67" stroke="#5b6b7a" stroke-width="1" marker-end="url(#arrow)"/>

    <rect x="225" y="32" width="75" height="70" rx="3" fill="#eafaf1" stroke="#27ae60" stroke-width="1.2"/>
    <text x="262" y="50" font-size="10" font-weight="bold" text-anchor="middle" fill="#1e8449">控制执行</text>
    <text x="262" y="66" font-size="9" text-anchor="middle" fill="#1e8449">软着陆成功</text>
    <text x="262" y="81" font-size="9" font-weight="bold" text-anchor="middle" fill="#1e8449">缺额 0 / 0</text>
    <text x="262" y="94" font-size="8" text-anchor="middle" fill="#5b6b7a">(k ≤ 2 场景)</text>
  </g>

  <!-- Bottom Summary Note -->
  <rect x="35" y="620" width="930" height="1" fill="#cbd5e1"/>
</svg>"""
    with open(os.path.join(FIG_DIR, "Fig1_CPS_framework.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    print("Fig1_CPS_framework.svg generated.")


def make_fig2():
    """Fig 2: Physical cooling water cascade process chain."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 480" width="1000" height="480" style="background:#ffffff; font-family:Arial, Helvetica, sans-serif;">
  <defs>
    <linearGradient id="boxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f8fafc"/>
    </linearGradient>
    <linearGradient id="hlGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e8f8f5"/>
      <stop offset="100%" stop-color="#d1f2eb"/>
    </linearGradient>
    <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#1b4f72"/>
    </marker>
    <marker id="arrRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#c0392b"/>
    </marker>
    <marker id="arrAmber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#e08a1e"/>
    </marker>
  </defs>

  <!-- Background Box -->
  <rect x="15" y="15" width="970" height="450" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>

  <!-- Top Banner: Intermediate physical process modeled in this paper -->
  <rect x="175" y="30" width="650" height="32" rx="4" fill="#eafaf1" stroke="#27ae60" stroke-width="1.2"/>
  <text x="500" y="52" font-size="13" font-weight="bold" fill="#1e8449" text-anchor="middle">★ 本文首次显式建模的电厂内部储水缓冲与热力耦合物理过程链（打破传统"直接耦合边"假设）</text>

  <!-- Step 1: Municipal Depressurization -->
  <g transform="translate(30, 90)">
    <rect x="0" y="0" width="125" height="180" rx="6" fill="#fdedec" stroke="#e74c3c" stroke-width="1.5"/>
    <text x="62" y="28" font-size="12" font-weight="bold" text-anchor="middle" fill="#c0392b">市政配水节点</text>
    <text x="62" y="46" font-size="10" text-anchor="middle" fill="#5b6b7a">Municipal Node</text>
    <line x1="15" y1="56" x2="110" y2="56" stroke="#e74c3c" stroke-width="1"/>
    <text x="62" y="78" font-size="10" font-weight="bold" text-anchor="middle" fill="#c0392b">压头失效判据</text>
    <text x="62" y="98" font-size="11" font-weight="bold" text-anchor="middle" fill="#1e293b">H &lt; 28 m</text>
    <text x="62" y="122" font-size="9" text-anchor="middle" fill="#5b6b7a">进水流量降为 0</text>
    <text x="62" y="140" font-size="9" text-anchor="middle" fill="#c0392b">q_in = 0</text>
    <text x="62" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">t = 0 危机起点</text>
  </g>

  <!-- Arrow 1 -> 2 -->
  <line x1="155" y1="180" x2="185" y2="180" stroke="#1b4f72" stroke-width="2" marker-end="url(#arr)"/>

  <!-- Step 2: Makeup Tank -->
  <g transform="translate(190, 90)">
    <rect x="0" y="0" width="130" height="180" rx="6" fill="url(#hlGrad)" stroke="#17a2b8" stroke-width="1.5"/>
    <text x="65" y="28" font-size="12" font-weight="bold" text-anchor="middle" fill="#0e6251">高位补水箱</text>
    <text x="65" y="46" font-size="10" text-anchor="middle" fill="#5b6b7a">Makeup Tank</text>
    <line x1="15" y1="56" x2="115" y2="56" stroke="#17a2b8" stroke-width="1"/>
    <text x="65" y="78" font-size="10" font-weight="bold" text-anchor="middle" fill="#0e6251">质量守恒微分方程</text>
    <text x="65" y="98" font-size="10" text-anchor="middle" fill="#1e293b">dV_mk/dt = -q_mk</text>
    <text x="65" y="122" font-size="9" text-anchor="middle" fill="#5b6b7a">有效容积 500 m³</text>
    <text x="65" y="142" font-size="9" font-weight="bold" text-anchor="middle" fill="#e08a1e">耗竭时间 ≈ 40 min</text>
    <text x="65" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">一级储水缓冲</text>
  </g>

  <!-- Arrow 2 -> 3 -->
  <line x1="320" y1="180" x2="350" y2="180" stroke="#1b4f72" stroke-width="2" marker-end="url(#arr)"/>

  <!-- Step 3: Cooling Basin -->
  <g transform="translate(355, 90)">
    <rect x="0" y="0" width="135" height="180" rx="6" fill="url(#hlGrad)" stroke="#17a2b8" stroke-width="1.5"/>
    <text x="67" y="28" font-size="12" font-weight="bold" text-anchor="middle" fill="#0e6251">集水池储水</text>
    <text x="67" y="46" font-size="10" text-anchor="middle" fill="#5b6b7a">Cooling Basin</text>
    <line x1="15" y1="56" x2="120" y2="56" stroke="#17a2b8" stroke-width="1"/>
    <text x="67" y="78" font-size="10" font-weight="bold" text-anchor="middle" fill="#0e6251">池内水位动态</text>
    <text x="67" y="98" font-size="10" text-anchor="middle" fill="#1e293b">dV_b/dt = -q_loss</text>
    <text x="67" y="122" font-size="9" text-anchor="middle" fill="#5b6b7a">容积 3000 m³</text>
    <text x="67" y="142" font-size="9" font-weight="bold" text-anchor="middle" fill="#e08a1e">SAET: 88.6–124.8 min</text>
    <text x="67" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">二级慢动态耗竭</text>
  </g>

  <!-- Arrow 3 -> 4 -->
  <line x1="490" y1="180" x2="520" y2="180" stroke="#1b4f72" stroke-width="2" marker-end="url(#arr)"/>

  <!-- Step 4: Circulating Pump -->
  <g transform="translate(525, 90)">
    <rect x="0" y="0" width="125" height="180" rx="6" fill="url(#boxGrad)" stroke="#5b6b7a" stroke-width="1.5"/>
    <text x="62" y="28" font-size="12" font-weight="bold" text-anchor="middle" fill="#1e293b">循环水泵</text>
    <text x="62" y="46" font-size="10" text-anchor="middle" fill="#5b6b7a">Circulating Pump</text>
    <line x1="15" y1="56" x2="110" y2="56" stroke="#5b6b7a" stroke-width="1"/>
    <text x="62" y="78" font-size="10" font-weight="bold" text-anchor="middle" fill="#1e293b">汽蚀与流量降额</text>
    <text x="62" y="98" font-size="10" text-anchor="middle" fill="#1e293b">NPSHa &lt; NPSHr</text>
    <text x="62" y="122" font-size="9" text-anchor="middle" fill="#5b6b7a">流量自适应衰减</text>
    <text x="62" y="142" font-size="9" font-weight="bold" text-anchor="middle" fill="#c0392b">q_c(t) 渐进下降</text>
    <text x="62" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">物理非线性断流</text>
  </g>

  <!-- Arrow 4 -> 5 -->
  <line x1="650" y1="180" x2="680" y2="180" stroke="#1b4f72" stroke-width="2" marker-end="url(#arr)"/>

  <!-- Step 5: Condenser Heat Exchange -->
  <g transform="translate(685, 90)">
    <rect x="0" y="0" width="135" height="180" rx="6" fill="#fef9e7" stroke="#e08a1e" stroke-width="1.5"/>
    <text x="67" y="28" font-size="12" font-weight="bold" text-anchor="middle" fill="#7e5109">凝汽器换热</text>
    <text x="67" y="46" font-size="10" text-anchor="middle" fill="#5b6b7a">Condenser (ε-NTU)</text>
    <line x1="15" y1="56" x2="120" y2="56" stroke="#e08a1e" stroke-width="1"/>
    <text x="67" y="78" font-size="10" font-weight="bold" text-anchor="middle" fill="#7e5109">传热恶化与背压</text>
    <text x="67" y="98" font-size="10" text-anchor="middle" fill="#1e293b">NTU(q_c) = UA/C_min</text>
    <text x="67" y="122" font-size="9" text-anchor="middle" fill="#5b6b7a">饱和凝结温度 T_s 爬升</text>
    <text x="67" y="142" font-size="9" font-weight="bold" text-anchor="middle" fill="#c0392b">背压 P_c 持续升高</text>
    <text x="67" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">热力平衡破坏</text>
  </g>

  <!-- Arrow 5 -> 6 -->
  <line x1="820" y1="180" x2="845" y2="180" stroke="#c0392b" stroke-width="2" marker-end="url(#arrRed)"/>

  <!-- Step 6: Turbine & Grid Impact -->
  <g transform="translate(850, 90)">
    <rect x="0" y="0" width="120" height="180" rx="6" fill="#fdedec" stroke="#c0392b" stroke-width="1.5"/>
    <text x="60" y="28" font-size="12" font-weight="bold" text-anchor="middle" fill="#922b21">汽轮发电机组</text>
    <text x="60" y="46" font-size="10" text-anchor="middle" fill="#5b6b7a">Turbine-Gen</text>
    <line x1="12" y1="56" x2="108" y2="56" stroke="#c0392b" stroke-width="1"/>
    <text x="60" y="78" font-size="10" font-weight="bold" text-anchor="middle" fill="#922b21">降额与保护跳机</text>
    <text x="60" y="98" font-size="9" text-anchor="middle" fill="#1e293b">k_p(P_c) 降额修正</text>
    <text x="60" y="122" font-size="9" font-weight="bold" text-anchor="middle" fill="#c0392b">P_c &gt; 35 kPa 跳机</text>
    <text x="60" y="142" font-size="9" text-anchor="middle" fill="#c0392b">电力缺额 485.6 MW</text>
    <text x="60" y="165" font-size="9" text-anchor="middle" fill="#7f8c8d">电网冲击产生</text>
  </g>

  <!-- Cooling Tower Feedback Loop (Bottom) -->
  <g transform="translate(355, 300)">
    <rect x="0" y="0" width="465" height="135" rx="6" fill="#fffcf5" stroke="#e08a1e" stroke-width="1.2" stroke-dasharray="4,3"/>
    <text x="232" y="24" font-size="11" font-weight="bold" fill="#b9770f" text-anchor="middle">循环冷却水闭合反馈与损失模型 (Cooling Tower &amp; Loss Feedback)</text>

    <text x="25" y="55" font-size="10" fill="#1e293b">• 蒸发损失: q_evap = 0.00153 · c_p · ΔT_c · q_c (随换热负荷动态变化)</text>
    <text x="25" y="80" font-size="10" fill="#1e293b">• 排污与风吹损失: q_blow = q_evap / (N_c - 1), q_wind = 0.001 · q_c</text>
    <text x="25" y="105" font-size="10" fill="#1e293b">• 降额自保护负反馈: 降出力速率 r* = 0.55 %Pg/min 时可将运行时间自 88.6 min 延长至 183.3 min (2.1倍)</text>
  </g>

  <!-- Cooling loop arrows -->
  <path d="M 750 270 L 750 300" stroke="#e08a1e" stroke-width="1.5" marker-end="url(#arrAmber)"/>
  <path d="M 355 365 L 340 365 L 340 240 L 355 240" fill="none" stroke="#e08a1e" stroke-width="1.5" marker-end="url(#arrAmber)"/>
</svg>"""
    with open(os.path.join(FIG_DIR, "Fig2_cooling_water_chain.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    print("Fig2_cooling_water_chain.svg generated.")


def make_fig3():
    """Fig 3: Timescale gap mechanism between water and power domains, comparing passive and proactive control."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 520" width="1000" height="520" style="background:#ffffff; font-family:Arial, Helvetica, sans-serif;">
  <defs>
    <marker id="arrowB" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#1b4f72"/>
    </marker>
    <marker id="arrowR" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#c0392b"/>
    </marker>
    <marker id="arrowG" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#27ae60"/>
    </marker>
  </defs>

  <!-- Outer Boundary -->
  <rect x="15" y="15" width="970" height="490" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>

  <!-- Top Section: Water Domain Slow Dynamics (Buffer Depletion Timeline) -->
  <g transform="translate(35, 35)">
    <rect x="0" y="0" width="930" height="145" rx="6" fill="#eaf3fb" stroke="#2980b9" stroke-width="1.5"/>
    <text x="20" y="26" font-size="14" font-weight="bold" fill="#1b4f72">水侧慢动态 · 冷却储水缓冲耗竭时间轴 (Water-side Slow Dynamics: Minutes to Hours)</text>

    <!-- Main Axis Line -->
    <line x1="50" y1="80" x2="880" y2="80" stroke="#1b4f72" stroke-width="2.5" marker-end="url(#arrowB)"/>

    <!-- Point 0: Municipal Outage -->
    <circle cx="90" cy="80" r="6" fill="#c0392b"/>
    <text x="90" y="60" font-size="11" font-weight="bold" text-anchor="middle" fill="#c0392b">t = 0</text>
    <text x="90" y="105" font-size="10" font-weight="bold" text-anchor="middle" fill="#1b4f72">市政失压</text>
    <text x="90" y="120" font-size="9" text-anchor="middle" fill="#5b6b7a">H &lt; 28 m (补水停)</text>

    <!-- Buffer Period: SAET Window -->
    <rect x="130" y="45" width="480" height="25" rx="4" fill="#d4e6f7" stroke="#2980b9" stroke-width="1"/>
    <text x="370" y="62" font-size="11" font-weight="bold" text-anchor="middle" fill="#1b4f72">★ 冷却水系统储水缓冲耗竭窗口 (SAET = 88.6 – 124.8 min) · 可用主动控制时间</text>

    <!-- Point SAET: Tank drained, condenser trips -->
    <circle cx="610" cy="80" r="6" fill="#e74c3c"/>
    <text x="610" y="40" font-size="11" font-weight="bold" text-anchor="middle" fill="#c0392b">t = SAET (≈ 92 min)</text>
    <text x="610" y="105" font-size="10" font-weight="bold" text-anchor="middle" fill="#c0392b">保护动作跳机</text>
    <text x="610" y="120" font-size="9" text-anchor="middle" fill="#5b6b7a">Pc &gt; 35 kPa 强迫跳闸</text>

    <!-- Post Trip Horizon -->
    <text x="760" y="105" font-size="10" text-anchor="middle" fill="#5b6b7a">事故后恢复期</text>
    <text x="760" y="120" font-size="9" text-anchor="middle" fill="#5b6b7a">t &gt; 200 min</text>
  </g>

  <!-- Middle Bridge: Fast Cyber / ICS Link -->
  <g transform="translate(35, 190)">
    <rect x="0" y="0" width="930" height="40" rx="4" fill="#fef9e7" stroke="#e08a1e" stroke-width="1.2"/>
    <text x="465" y="25" font-size="12" font-weight="bold" fill="#7e5109" text-anchor="middle">⚡ 信息层快响应 (Cyber Fast Dynamics: Milliseconds to Seconds) —— 跨域早期预警零时延送达电力调度 EMS</text>
  </g>

  <!-- Bottom Left: Passive Control (No Warning) -->
  <g transform="translate(35, 245)">
    <rect x="0" y="0" width="455" height="245" rx="6" fill="#fdedec" stroke="#c0392b" stroke-width="1.5"/>
    <text x="20" y="28" font-size="13" font-weight="bold" fill="#922b21">被动控制 (PA: 无跨域预警)</text>
    <text x="20" y="48" font-size="10" fill="#5b6b7a">• 信息盲区：电力调度在机组突跳前对市政危机完全未知</text>

    <!-- Passive timeline -->
    <line x1="30" y1="100" x2="420" y2="100" stroke="#c0392b" stroke-width="1.5" marker-end="url(#arrowR)"/>
    <circle cx="50" cy="100" r="4" fill="#5b6b7a"/>
    <text x="50" y="85" font-size="9" text-anchor="middle" fill="#5b6b7a">t = 0</text>
    <text x="50" y="120" font-size="9" text-anchor="middle" fill="#5b6b7a">无预警/不动作</text>

    <circle cx="240" cy="100" r="5" fill="#c0392b"/>
    <text x="240" y="85" font-size="9" font-weight="bold" text-anchor="middle" fill="#c0392b">t = SAET (突跳)</text>
    <text x="240" y="120" font-size="9" font-weight="bold" text-anchor="middle" fill="#c0392b">机组瞬间脱网</text>

    <!-- Consequence box -->
    <rect x="25" y="145" width="405" height="85" rx="4" fill="#ffffff" stroke="#c0392b" stroke-width="1"/>
    <text x="35" y="168" font-size="11" font-weight="bold" fill="#c0392b">被动控制后果 (Passive Consequences):</text>
    <text x="35" y="188" font-size="10" fill="#1e293b">1. 备用在突跳后才起机，受爬坡率限制来不及填补缺口；</text>
    <text x="35" y="206" font-size="10" font-weight="bold" fill="#c0392b">2. 导致单机 485.6 MW 峰值缺额、49.1 MWh 损失电量；</text>
    <text x="35" y="222" font-size="10" fill="#5b6b7a">3. 同源三机造成 343.3 MW 峰值缺额、71.9 MWh 损失。</text>
  </g>

  <!-- Bottom Right: Proactive Control (With Early Warning) -->
  <g transform="translate(510, 245)">
    <rect x="0" y="0" width="455" height="245" rx="6" fill="#eafaf1" stroke="#27ae60" stroke-width="1.5"/>
    <text x="20" y="28" font-size="13" font-weight="bold" fill="#1e8449">主动控制 (SP/DP: 早期预警驱动)</text>
    <text x="20" y="48" font-size="10" fill="#5b6b7a">• 跨域协同：t=0 接收预警，主动利用 SAET 缓冲窗口协同调度</text>

    <!-- Proactive timeline -->
    <line x1="30" y1="100" x2="420" y2="100" stroke="#27ae60" stroke-width="1.5" marker-end="url(#arrowG)"/>
    <circle cx="50" cy="100" r="4" fill="#27ae60"/>
    <text x="50" y="85" font-size="9" font-weight="bold" text-anchor="middle" fill="#27ae60">t = 0 (预警)</text>
    <text x="50" y="120" font-size="9" font-weight="bold" text-anchor="middle" fill="#27ae60">备用提前起机</text>

    <!-- Ramp / Runback zone -->
    <rect x="50" y="70" width="200" height="15" rx="2" fill="#d1f2eb"/>
    <text x="150" y="82" font-size="8" font-weight="bold" text-anchor="middle" fill="#0e6251">受影响机组 Runback 软着陆</text>

    <circle cx="250" cy="100" r="5" fill="#27ae60"/>
    <text x="250" y="85" font-size="9" font-weight="bold" text-anchor="middle" fill="#27ae60">t = SAET (平稳过渡)</text>
    <text x="250" y="120" font-size="9" font-weight="bold" text-anchor="middle" fill="#27ae60">备用已足额就位</text>

    <!-- Proactive value box -->
    <rect x="25" y="145" width="405" height="85" rx="4" fill="#ffffff" stroke="#27ae60" stroke-width="1"/>
    <text x="35" y="168" font-size="11" font-weight="bold" fill="#1e8449">主动控制收益 (Proactive Benefits):</text>
    <text x="35" y="188" font-size="10" fill="#1e293b">1. 充分利用 88.6–124.8 min 慢动态缓冲窗口进行平滑爬坡；</text>
    <text x="35" y="206" font-size="10" font-weight="bold" fill="#1e8449">2. 峰值缺额 485.6 MW → 0 MW，损失电量 49.1 MWh → 0 MWh；</text>
    <text x="35" y="222" font-size="10" fill="#5b6b7a">3. k ≤ 2 组合失效下全部实现 0 缺额 (适用边界清晰确定)。</text>
  </g>
</svg>"""
    with open(os.path.join(FIG_DIR, "Fig3_timescale_gap_mechanism.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    print("Fig3_timescale_gap_mechanism.svg generated.")


if __name__ == "__main__":
    make_fig1()
    make_fig2()
    make_fig3()
