"""
市政侧失压时刻的全网分布 (Municipal-side depressurization-time distribution)
==========================================================================
研究疑问 (由审阅提出): 不同 junction 节点失压时刻差异极大 —— 若选不同节点为电厂供
冷却水, 则"跌破供水阈值(28 m)的时刻"差异也极大, "开始影响发电机组的时刻"自然不同。

本模块的定位: 把这一疑问从"担忧"变成**定量结果**。不再钦定某几个取水节点,而是
刻画唯一水源停供后**全网所有 junction 跌破 28 m 的时刻分布**, 并据此选取**可辩护的
代表性分位数节点** (P10/P50/P90 = 快/中/慢三类电厂), 供下游 P6 做**敏感性分析**。

关键物理澄清 (两级缓冲, 不可混淆):
  1) 市政级: 水源停供 → 电厂取水节点跌破 28 m。时长 t_muni(节点), **强依赖节点位置**
     (本模块量化: 0~数十小时不等, 部分高区节点因水箱重力供水长时间不失压)。
  2) 冷却级: 取水失效 → 机组跳机。时长 = 冷却侧 SAET(~90~125 min), 是**电厂内部**
     属性, 与节点无关 (见 src/03_proactive_control/warning_indicators.py)。
  节点选择影响的是【第1级】"开始影响机组的时刻", 而非第2级冷却缓冲窗口。

为何这是科学上正确的处理 (而非"选定一个节点报一个数"):
  真实电厂取水口位置是固定且已知的地理事实, 对具体电厂 t_muni 是确定值; 任意性仅源于
  "把虚构电厂映射到无真实电厂的基准网"——缺的是"电厂-管网地理关系"数据, 而非该量本身
  不确定。参照文献亦给范围("SAET 从数分钟到数小时不等"), 非单值。故正确做法是给出
  **分布 + 代表性分位数 + 敏感性**, 诚实呈现"结果依赖取水位置"。

停供: 唯一水源(水库 R1) 自 t=0 阶跃停供 (压头→0), PDD + 压力钳制为 0 (物理正确)。

输出:
  results/saet_distribution.json  全网逐节点失压时刻 + 分布统计 + P10/P50/P90 代表节点
  results/saet_distribution.png   ① 失压时刻直方图 ② 累计失压占比(CDF) ③ 空间分布着色

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

H_MUNI_MIN = 28.0
SOURCE_RESERVOIR = "R1"


def _sim(duration_h, step_min, outage):
    wn = wntr.network.WaterNetworkModel(INP)
    wn.options.quality.parameter = "NONE"
    wn.options.time.duration = int(duration_h * 3600)
    wn.options.time.hydraulic_timestep = int(step_min * 60)
    wn.options.time.report_timestep = int(step_min * 60)
    wn.options.hydraulic.demand_model = "PDD"
    wn.options.hydraulic.required_pressure = 20.0
    wn.options.hydraulic.minimum_pressure = 0.0
    if outage:
        R1 = wn.get_node(SOURCE_RESERVOIR)
        base = R1.base_head
        n = int(duration_h * 3600 / (step_min * 60)) + 3
        wn.add_pattern("outage", [0.001] * n)
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
    return wn, res


def analyze(duration_h=72.0, step_min=15, save=True):
    # 停供工况: 全网逐节点失压时刻
    wn, res = _sim(duration_h, step_min, outage=True)
    pr = res.node["pressure"]
    jn = wn.junction_name_list
    th = (pr.index / 3600.0).to_numpy()
    tfail = {}
    for j in jn:
        h = pr[j].to_numpy()
        b = np.where(h < H_MUNI_MIN)[0]
        tfail[j] = float(th[b[0]]) if len(b) else None      # None = 72h 内不失压

    # 正常工况(无停供)基线, 判定候选节点故障前是否健康
    wn0, res0 = _sim(24.0, step_min, outage=False)
    pr0 = res0.node["pressure"]
    healthy = {j: bool(pr0[j].min() > 32) for j in jn}

    finite = np.array([v for v in tfail.values() if v is not None])
    never = sum(1 for v in tfail.values() if v is None)

    # 可辩护的代表性分位数节点 (仅在"故障前健康且会失压"的节点中取)
    cand = {j: tfail[j] for j in jn if healthy[j] and tfail[j] is not None}
    cvals = np.array(list(cand.values()))
    reps = {}
    for pct, tag in [(10, "fast"), (50, "median"), (90, "slow")]:
        tgt = float(np.percentile(cvals, pct))
        j = min(cand, key=lambda k: abs(cand[k] - tgt))
        reps[tag] = dict(node=j, pctile=pct, t_fail_h=round(cand[j], 3),
                         elev_m=round(float(wn.get_node(j).elevation), 1))

    stats = dict(
        n_junctions=len(jn),
        n_fail_within=len(finite),
        n_never_fail=never,
        never_fail_pct=round(never / len(jn) * 100, 1),
        min_h=round(float(finite.min()), 2),
        p10_h=round(float(np.percentile(finite, 10)), 2),
        median_h=round(float(np.median(finite)), 2),
        p90_h=round(float(np.percentile(finite, 90)), 2),
        max_h=round(float(finite.max()), 2),
    )

    coords = {j: [round(float(wn.get_node(j).coordinates[0]), 2),
                  round(float(wn.get_node(j).coordinates[1]), 2)] for j in jn}
    edges = [[wn.get_link(ln).start_node_name, wn.get_link(ln).end_node_name]
             for ln in wn.pipe_name_list]

    out = dict(
        source="D-town (Ostfeld 2016, BWN Models, Univ. of Kentucky, CC BY-NC 4.0)",
        network="DTOWN.inp", method="EPANET 2.2 EPS (PDD, quality off)",
        fault="unique source (R1) step outage from t=0",
        H_muni_min_m=H_MUNI_MIN, duration_h=duration_h, step_min=step_min,
        stats=stats, representatives=reps,
        tfail_h={j: (round(v, 3) if v is not None else None) for j, v in tfail.items()},
        coords=coords, edges=edges,
        reservoir_coord=[round(float(wn.get_node(SOURCE_RESERVOIR).coordinates[0]), 2),
                         round(float(wn.get_node(SOURCE_RESERVOIR).coordinates[1]), 2)],
        tanks={t: [round(float(wn.get_node(t).coordinates[0]), 2),
                   round(float(wn.get_node(t).coordinates[1]), 2)]
               for t in wn.tank_name_list},
    )
    if save:
        os.makedirs(RES, exist_ok=True)
        path = os.path.join(RES, "saet_distribution.json")
        with open(path, "w") as f:
            json.dump(out, f, ensure_ascii=False)
        print("saved", os.path.abspath(path))
    return out


if __name__ == "__main__":
    o = analyze()
    s = o["stats"]
    print("\n唯一水源自 t=0 停供 → 全网 %d 个配水节点失压时刻分布" % s["n_junctions"])
    print("最小供水阈值 %.0f m\n" % o["H_muni_min_m"])
    print("失压时刻分布 (h):  min %.1f | P10 %.1f | 中位 %.1f | P90 %.1f | max %.1f"
          % (s["min_h"], s["p10_h"], s["median_h"], s["p90_h"], s["max_h"]))
    print("72h 内始终不失压节点: %d / %d (%.1f%%)"
          % (s["n_never_fail"], s["n_junctions"], s["never_fail_pct"]))
    print("\n→ 结论: 失压时刻【强依赖取水节点位置】, 从 %.1f h 到 %.1f h 不等, 且 %.0f%% 节点"
          " 长时间不失压。" % (s["min_h"], s["max_h"], s["never_fail_pct"]))
    print("\n可辩护的代表性取水节点 (供 P6 敏感性分析, 快/中/慢三类电厂):")
    for tag, r in o["representatives"].items():
        print("  %-7s (P%2d): 节点 %-6s  失压 %.2f h  标高 %.0f m"
              % (tag, r["pctile"], r["node"], r["t_fail_h"], r["elev_m"]))
