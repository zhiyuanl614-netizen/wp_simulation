"""
市政供水管网边界生成器 (Municipal Water Distribution Network — Boundary Generator)
==================================================================================
角色定位: **上游边界生成器**, 不与下游耦合求解。
  用真实基准管网 (D-town) 的水力仿真, 生成各电厂配水节点的压头轨迹 H_muni_i(t),
  再经"最小供水阈值 28 m"判据, 得到各电厂供水失效时刻 t_fault_i。
  v2 (2026-09-15): 电厂取水点由 v1 的三对改为 coupling_map.json 指定的
  **6 对** (bus 89/80/10/66/65/26 ↔ J102/J97/J198/J5/J217/J177);
  本模块不再硬编码取水点, 一律从 coupling_map.json 读取 (单一真源)。
  下游 (冷却水系统 / 电力系统 / P6 主动控制) 模型完全不变, 只把 t_fault_i / ramp_i
  作为边界参数读入。

为什么市政水网只作边界、不耦合进下游 (缓冲位置不对称):
  文献气网必须做网络水力仿真, 因为缓冲(line pack 管存气)分布在管网内, AET/SAET
  由管存气算出。本项目缓冲(可用储水量 ASW)在**电厂内部**(高位补水箱+集水池), 是
  集总的、不在市政管网里。故市政管网对下游只是一个压力边界, 不承载任何下游需要的
  缓冲物理 —— 用它生成 H_muni_i(t) 即充分。

为什么用 D-town (而非 C-town):
  同一 BWN 系列的 C-town 导出版 [JUNCTIONS] 需水量全为 0、无城市负荷 (校准用拓扑
  骨架), 需人为补背景负荷才能让水箱排空 —— 引入人为成分。D-town 是 C-town 拓扑的
  **带真实需水量改进版** (2013 BWN 长期改进竞赛): 399 节点中 348 个有真实需水
  (另 51 个基础需水为 0, 系纯过流/占位节点 —— 不可作电厂取水点, 见 coupling_map v2
  硬筛)、5 条日变化需水模式 (DMA1_pat..DMA5_pat, 各 168 个小时乘子)、7 个分区水箱、
  单水库总源。城市负荷真实, 无需人为补充。

数据来源 (务必署名, CC-BY-NC 4.0):
  Marchi, A. et al. via Ostfeld, Avi. "05 Long Term Improvement" (D-town) (2016).
  Battle of the Water Network Models. University of Kentucky Libraries.
  https://uknowledge.uky.edu/wdst_models/5   (CC BY-NC 4.0)

D-town 拓扑: 单水库 R1 (市政总源) + 11 泵 + 7 水箱 (T1..T7, 分区缓冲) + 399 节点 +
  443 管段 + 5 阀, 分层 DMA 结构。

故障施加 (水源压头下降, 更贴合"市政供水压力失效"的物理本意):
  市政总源 (水库 R1) 压头自 t_fault 起在 decline_h 小时内线性下降至近零,
  配水节点压力随之逐级失效。相比硬切管道, 压头下降既物理真实、又保持水力求解良态
  (D-town 的 11 泵在硬切总源后会进入不稳定工况使 EPANET 求解崩溃)。

仿真方法: EPANET 2.2 扩展时段准稳态 (EPS, 分钟级), 非亚秒级水锤暂态 —— 与本项目
  关心的失压传导时间尺度 (SAET, 分钟~小时) 一致。水质(水龄)分析已关闭, 只解水力。
"""
import os
import json
import numpy as np
import wntr

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "data", "DTOWN.inp")

# ---- 阈值 (与全项目一致, 见 src/01_cooling_chain/params.py) ----
H_MUNI_MIN = 28.0        # m, 最小供水阈值 = 失效判据 = ICS 预警阈值

# ---- 市政总源 (水库 R1) ----
SOURCE_RESERVOIR = "R1"

# ---- 电厂的市政配水取水节点 (v2: 研究者指定 6 对, 单一真源 = coupling_map.json) ----
# 与 IEEE-118 电厂母线一一对应 (下游 P6 的同源/多源受影响机组)。
# v2 (2026-09-15): 由 v1 的三对 (bus89-J411 / bus80-J371 / bus10-J197) 改为
# coupling_map.py 指定的 6 对 (bus 89/80/10/66/65/26 ↔ J102/J97/J198/J5/J217/J177)。
# 依据: ① J371 基础需水为 0 (本身不供水) 且 B-ST 下 72h 不失压, 不构成有效取水点;
#       ② IEEE-118 的 54 条 gen 中 35 台 Pg=0 (非凝汽式火电机组), 不建模冷却级联。
# 本模块【含】电厂补水负荷反馈 (与 full_coupling_boundary.py 的语义①"不反馈"并存,
# 两者给出 B-RT 的两个口径, 引用时须注明)。补水负荷 = coupling_map 的 makeup_Lps。
RES_MUNI = os.path.join(HERE, "..", "..", "results", "muni")


def _load_plant_intakes():
    """从 coupling_map.json (v2, 6 对) 构造 PLANT_INTAKES。"""
    cm = json.load(open(os.path.join(RES_MUNI, "coupling_map.json")))
    assert cm.get("version") == "v2", "boundary_generator 需 coupling_map v2 (指定 6 对)"
    return {("bus%d" % r["bus"]): dict(node=r["junction"],
                                       zone="DMA=%s 标高 %.0f m 需水 %.3f L/s"
                                            % (r["dma"], r["elev_m"], r["demand_Lps"]),
                                       makeup_Lps=r["makeup_Lps"],
                                       rank=r["rank"])
            for r in cm["map"]}


PLANT_INTAKES = _load_plant_intakes()

# 语义开关: False = 语义①(补水不反馈进城市水力, 项目权威口径);
#           True  = v1 遗留口径(补水作为节点负荷注入; 会使 J5 故障前压头崩至 17 m)
FEEDBACK_MAKEUP = False


def _build_model(t_fault_h=6.0, decline_h=3.0, duration_h=72.0, step_min=15):
    """加载 D-town, 关水质, 注入电厂补水负荷, 施加水源压头下降故障。"""
    wn = wntr.network.WaterNetworkModel(INP)
    wn.options.quality.parameter = "NONE"            # 只解水力, 关水龄分析
    wn.options.time.duration = int(duration_h * 3600)
    wn.options.time.hydraulic_timestep = int(step_min * 60)
    wn.options.time.report_timestep = int(step_min * 60)
    # 压力驱动需水 (PDD): 压力不足时供水量按物理削减
    wn.options.hydraulic.demand_model = "PDD"
    # v2: required_pressure 由 15 改为 20 m, 与 full_coupling_boundary.py 一致
    wn.options.hydraulic.required_pressure = 20.0    # m
    wn.options.hydraulic.minimum_pressure = 0.0      # m

    # ---- v2: 语义① —— 电厂补水【不】反馈进城市水力 ----
    # 依据 (docs/coupling_map.md §5 / 本轮 6 厂实测): 把额定补水 (6 路合计 95.7 L/s)
    # 作为节点负荷注入后, bus66 的取水节点 J5 (基础需水仅 0.194 L/s, 标高 22.75 m)
    # 故障前压头即由 38.0 m 崩塌至 17.0 m —— 低于 28 m 失效阈值, 在 t=0 就"已失效",
    # 破坏"故障前健康"前提, 且使该节点丧失作为级联起点的能力。
    # 故与 full_coupling_boundary.py 统一采用语义①: 城市水力保持无补水口径,
    # 额定补水作为【被评估的需求】事后按 PDD 份额评估可供性。
    # 若需恢复反馈口径, 置 FEEDBACK_MAKEUP=True (将复现上述 J5 崩塌)。
    if FEEDBACK_MAKEUP:
        for pk, info in PLANT_INTAKES.items():
            wn.get_node(info["node"]).add_demand(
                base=info["makeup_Lps"] / 1000.0, pattern_name=None)

    # 市政总源压力失效: 水库 R1 压头自 t_fault 起在 decline_h 内线性降至近零
    R1 = wn.get_node(SOURCE_RESERVOIR)
    base = R1.base_head
    n = int(duration_h * 3600 / (step_min * 60)) + 3
    mult = []
    for i in range(n):
        t = i * step_min / 60.0
        if t < t_fault_h:
            mult.append(1.0)
        else:
            mult.append(max(0.02, 1.0 - (t - t_fault_h) / decline_h))
    wn.add_pattern("r_decline", mult)
    R1.head_timeseries.base_value = base
    R1.head_timeseries.pattern_name = "r_decline"
    return wn


def generate(t_fault_h=6.0, decline_h=3.0, duration_h=72.0, step_min=15, save=True):
    """运行市政水网仿真, 输出各电厂配水节点压头轨迹与失效时刻。

    返回 dict:
      t_h            : 时间轴 (h)
      plants[bus]:
        node, zone
        head_m       : 配水节点压头轨迹 (m)
        t_fail_h     : 首次跌破 28 m 的绝对时刻 (h);  None=全程未失效
        t_fail_after_fault_s : 相对总源故障的失效延迟 (s), 供下游作 t_fault_i
        head0_m      : 故障前正常压头 (m)
    """
    wn = _build_model(t_fault_h, decline_h, duration_h, step_min)
    # EPANET 2.2; 临时文件写入独立临时目录, 避免污染工作区
    import tempfile
    _cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as _td:
        try:
            os.chdir(_td)                # EPANET 二进制输出写入临时目录
            res = wntr.sim.EpanetSimulator(wn).run_sim(version=2.2)
        finally:
            os.chdir(_cwd)
    pr = res.node["pressure"]
    t_h = (pr.index / 3600.0).to_numpy()

    plants = {}
    for pk, info in PLANT_INTAKES.items():
        node = info["node"]
        head = pr[node].to_numpy()
        head0 = float(head[t_h <= t_fault_h][-1]) if np.any(t_h <= t_fault_h) else float(head[0])
        below = np.where(head < H_MUNI_MIN)[0]
        post = below[t_h[below] >= t_fault_h] if len(below) else np.array([], dtype=int)
        if len(post):
            t_fail = float(t_h[post[0]])
            t_fail_after = (t_fail - t_fault_h) * 3600.0
        else:
            t_fail, t_fail_after = None, None
        plants[pk] = dict(
            node=node, zone=info["zone"], makeup_Lps=info["makeup_Lps"],
            head0_m=round(head0, 2),
            head_m=[round(float(x), 3) for x in head],
            t_fail_h=(round(t_fail, 3) if t_fail is not None else None),
            t_fail_after_fault_s=(round(t_fail_after, 1) if t_fail_after is not None else None),
        )

    out = dict(
        source="D-town (Ostfeld 2016, Battle of the Water Network Models, "
               "Univ. of Kentucky, CC BY-NC 4.0)",
        network="DTOWN.inp",
        method="EPANET 2.2 EPS (quasi-steady, PDD required=20m/min=0, quality off)",
        makeup_feedback=FEEDBACK_MAKEUP,
        semantics=("makeup NOT fed back into city hydraulics (语义①, 与 "
                   "full_coupling_boundary.py 一致)" if not FEEDBACK_MAKEUP else
                   "makeup injected as node demand (v1 legacy)"),
        fault_mode="source reservoir head decline",
        H_muni_min_m=H_MUNI_MIN,
        source_reservoir=SOURCE_RESERVOIR,
        t_fault_h=t_fault_h, decline_h=decline_h,
        duration_h=duration_h, step_min=step_min,
        t_h=[round(float(x), 4) for x in t_h],
        plants=plants,
    )
    if save:
        rdir = os.path.join(HERE, "..", "..", "results", "muni")
        os.makedirs(rdir, exist_ok=True)
        path = os.path.join(rdir, "muni_boundary.json")
        with open(path, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("saved", os.path.abspath(path))
    return out


if __name__ == "__main__":
    o = generate()
    print("\n市政总源压力失效: t_fault = %.1f h 起, 水库 %s 压头 %.1f h 内降至近零"
          % (o["t_fault_h"], o["source_reservoir"], o["decline_h"]))
    print("最小供水阈值 H_muni_min = %.0f m\n" % o["H_muni_min_m"])
    print("电厂    配水节点  DMA供区                正常压头   失效时刻(故障后)")
    print("-" * 76)
    rows = []
    for pk, pl in o["plants"].items():
        taf = pl["t_fail_after_fault_s"]
        taf_str = ("%.2f h" % (taf / 3600.0)) if taf is not None else "未失效(>%.0fh)" % o["duration_h"]
        print("%-7s %-8s %-20s %7.1f m   %14s" %
              (pk, pl["node"], pl["zone"], pl["head0_m"], taf_str))
        if taf is not None:
            rows.append((pk, taf))
    rows.sort(key=lambda x: x[1])
    if rows:
        print("\n错峰失压次序 (对齐文献: SAET 随与故障点距离/分区缓冲 从数分钟到数小时不等):")
        for i, (pk, taf) in enumerate(rows, 1):
            print("  %d) %s  故障后 %.2f h 失效" % (i, pk, taf / 3600.0))
