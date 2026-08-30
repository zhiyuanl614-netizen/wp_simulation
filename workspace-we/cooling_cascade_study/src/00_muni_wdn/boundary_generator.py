"""
市政供水管网边界生成器 (Municipal Water Distribution Network — Boundary Generator)
==================================================================================
角色定位: **上游边界生成器**, 不与下游耦合求解。
  用真实基准管网 (D-town) 的水力仿真, 生成各电厂配水节点的压头轨迹 H_muni_i(t),
  再经"最小供水阈值 28 m"判据, 得到各电厂供水失效时刻 t_fault_i。
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
  **带真实需水量改进版** (2013 BWN 长期改进竞赛): 399 节点中 348 个有真实需水、
  5 条日变化需水模式、7 个分区水箱、单水库总源。城市负荷真实, 无需人为补充。

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

# ---- 三座电厂的市政配水取水节点 (分处不同 DMA 供区, 产生错峰失压) ----
# 与 IEEE-118 电厂母线一一对应 (下游 P6 的同源/多源受影响机组)。
# 取水点在含电厂补水负荷工况下故障前压头均 >55 m (健康), 故障后单调错峰失效。
# 补水负荷 20 L/s (电厂循环水补水, 配水节点主导负荷)。
PLANT_INTAKES = {
    "bus89": {"node": "J411", "zone": "低区(标高 9 m, 弱缓冲)",  "makeup_Lps": 20.0},
    "bus80": {"node": "J371", "zone": "中区(标高 69 m, 中缓冲)", "makeup_Lps": 20.0},
    "bus10": {"node": "J197", "zone": "高区(标高 42 m, T3强缓冲)", "makeup_Lps": 20.0},
}


def _build_model(t_fault_h=6.0, decline_h=3.0, duration_h=72.0, step_min=15):
    """加载 D-town, 关水质, 注入电厂补水负荷, 施加水源压头下降故障。"""
    wn = wntr.network.WaterNetworkModel(INP)
    wn.options.quality.parameter = "NONE"            # 只解水力, 关水龄分析
    wn.options.time.duration = int(duration_h * 3600)
    wn.options.time.hydraulic_timestep = int(step_min * 60)
    wn.options.time.report_timestep = int(step_min * 60)
    # 压力驱动需水 (PDD): 压力不足时供水量按物理削减
    wn.options.hydraulic.demand_model = "PDD"
    wn.options.hydraulic.required_pressure = 15.0    # m
    wn.options.hydraulic.minimum_pressure = 0.0      # m

    # 电厂补水负荷 (配水节点的主导负荷)
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
        method="EPANET 2.2 EPS (quasi-steady, PDD, quality off)",
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
