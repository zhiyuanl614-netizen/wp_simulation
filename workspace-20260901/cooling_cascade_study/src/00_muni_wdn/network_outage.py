"""
唯一水源停供 → 全网节点压力崩溃分析 (Network-wide Source-Outage Analysis)
==========================================================================
研究焦点 (区别于 boundary_generator 的"3 电厂取水点错峰"): 模拟 D-town **唯一水源
(水库 R1) 完全停止供水**这一确定事件后, **整个管网全部 399 节点压力的时空演化** ——
失压如何从水源处开始、随各分区水箱逐级放空而在空间上扩散。

停供施加 (阶跃): 水源 R1 压头在 t_fault 时刻瞬间降至近零并保持 (唯一水源完全停供)。
  用"压头→0"而非"硬切出水管": 硬切会使 EPANET 稳态解在无水可供的节点算出大量
  非物理负压 (可达 -10^4 m); 压头→0 + PDD + minimum_pressure=0 则物理正确 ——
  水源停供后由 7 个分区水箱储水续供, 水箱逐级放空后所在区才真正失压。

物理正确性: 停供后压力并不立即崩溃 —— 全网水箱 (T1..T7) 靠储水继续供水, 维持一段
  时间 (缓冲窗口); 随水箱见底, 失压节点占比从初始扩大到全网大部, 呈**空间扩散**。

输出:
  results/network_outage.json  全网压力统计时间序列 + 若干快照时刻的逐节点压力
  results/network_outage.png   ① 全网压力统计随时间 ② 失压节点占比 ③④⑤ 空间快照

数据来源 (CC-BY-NC 4.0, 须署名):
  Ostfeld, Avi. "05 Long Term Improvement" (D-town) (2016).
  Battle of the Water Network Models. Univ. of Kentucky Libraries.
  https://uknowledge.uky.edu/wdst_models/5
"""
import os
import json
import numpy as np
import wntr

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "data", "DTOWN.inp")
RES = os.path.join(HERE, "..", "..", "results", "muni")

H_MUNI_MIN = 28.0        # m, 最小供水阈值 (失压判据, 与全项目一致)
SOURCE_RESERVOIR = "R1"  # D-town 唯一水源 (市政总源)
SNAP_HOURS = [0, 12, 24, 48]   # 空间快照时刻 (h); 停供自 t=0 起, 故均为停供后


def run_outage(t_fault_h=0.0, duration_h=72.0, step_min=15, save=True):
    wn = wntr.network.WaterNetworkModel(INP)
    wn.options.quality.parameter = "NONE"            # 只解水力
    wn.options.time.duration = int(duration_h * 3600)
    wn.options.time.hydraulic_timestep = int(step_min * 60)
    wn.options.time.report_timestep = int(step_min * 60)
    wn.options.hydraulic.demand_model = "PDD"
    wn.options.hydraulic.required_pressure = 20.0
    wn.options.hydraulic.minimum_pressure = 0.0      # 无水时压力钳制为 0 (物理正确)

    # 唯一水源阶跃停供: R1 压头在 t_fault 瞬间→近零并保持
    R1 = wn.get_node(SOURCE_RESERVOIR)
    base = R1.base_head
    n = int(duration_h * 3600 / (step_min * 60)) + 3
    mult = [1.0 if (i * step_min / 60.0) < t_fault_h else 0.001 for i in range(n)]
    wn.add_pattern("outage", mult)
    R1.head_timeseries.base_value = base
    R1.head_timeseries.pattern_name = "outage"

    import tempfile
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        try:
            os.chdir(td)
            res = wntr.sim.EpanetSimulator(wn).run_sim(version=2.2)
        finally:
            os.chdir(cwd)

    pr = res.node["pressure"]
    jn = wn.junction_name_list
    t_h = (pr.index / 3600.0).to_numpy()
    P = np.clip(pr[jn].to_numpy(), 0.0, None)     # 钳制负压假象

    # 全网压力统计时间序列
    stats = dict(
        t_h=[round(float(x), 4) for x in t_h],
        mean=[round(float(np.nanmean(P[i])), 2) for i in range(len(t_h))],
        p10=[round(float(np.nanpercentile(P[i], 10)), 2) for i in range(len(t_h))],
        p50=[round(float(np.nanpercentile(P[i], 50)), 2) for i in range(len(t_h))],
        p90=[round(float(np.nanpercentile(P[i], 90)), 2) for i in range(len(t_h))],
        frac_below=[round(float((pr[jn].to_numpy()[i] < H_MUNI_MIN).mean()), 4)
                    for i in range(len(t_h))],
    )

    # 空间快照: 各节点坐标 + 若干时刻压力
    coords = {j: [round(float(wn.get_node(j).coordinates[0]), 2),
                  round(float(wn.get_node(j).coordinates[1]), 2)] for j in jn}
    snaps = {}
    for h in SNAP_HOURS:
        i = int(round(h * 60 / step_min))
        i = min(i, len(t_h) - 1)
        snaps[str(h)] = {j: round(float(max(0.0, pr[jn].to_numpy()[i][k])), 2)
                         for k, j in enumerate(jn)}

    # 管段拓扑 (用于画网络) + 水箱/水源坐标
    edges = []
    for ln in wn.pipe_name_list:
        l = wn.get_link(ln)
        edges.append([l.start_node_name, l.end_node_name])
    node_all_coords = {nn: [round(float(wn.get_node(nn).coordinates[0]), 2),
                            round(float(wn.get_node(nn).coordinates[1]), 2)]
                       for nn in wn.node_name_list}

    out = dict(
        source="D-town (Ostfeld 2016, BWN Models, Univ. of Kentucky, CC BY-NC 4.0)",
        network="DTOWN.inp", method="EPANET 2.2 EPS (PDD, quality off)",
        fault="unique source (reservoir R1) step outage: head -> ~0",
        H_muni_min_m=H_MUNI_MIN, t_fault_h=t_fault_h,
        duration_h=duration_h, step_min=step_min,
        n_junctions=len(jn), snap_hours=SNAP_HOURS,
        stats=stats, coords=coords, snapshots=snaps,
        edges=edges, node_coords=node_all_coords,
        reservoir=SOURCE_RESERVOIR,
        reservoir_coord=node_all_coords[SOURCE_RESERVOIR],
        tanks={t: node_all_coords[t] for t in wn.tank_name_list},
    )
    if save:
        os.makedirs(RES, exist_ok=True)
        path = os.path.join(RES, "network_outage.json")
        with open(path, "w") as f:
            json.dump(out, f, ensure_ascii=False)
        print("saved", os.path.abspath(path))
    return out


if __name__ == "__main__":
    o = run_outage()
    s = o["stats"]
    tf = o["t_fault_h"]
    print("\n唯一水源 (水库 %s) 阶跃停供 @ t=%.0f h  →  全网 %d 节点压力崩溃"
          % (o["reservoir"], tf, o["n_junctions"]))
    print("最小供水阈值 %.0f m\n" % o["H_muni_min_m"])
    print(" 时刻(h)  全网均压(m)  中位压(m)  失压节点占比")
    print("-" * 48)
    for h in [0, 6, 12, 18, 24, 36, 48, 60, 72]:
        i = min(int(round(h * 60 / o["step_min"])), len(s["t_h"]) - 1)
        print(" %5d    %8.1f   %8.1f     %5.1f%%"
              % (h, s["mean"][i], s["p50"][i], s["frac_below"][i] * 100))
    # 全网半数失压的时刻
    fb = np.array(s["frac_below"]); th = np.array(s["t_h"])
    half = np.where(fb >= 0.5)[0]
    if len(half):
        print("\n全网 50%% 节点失压时刻: t=%.1f h (停供后 %.1f h)"
              % (th[half[0]], th[half[0]] - tf))
