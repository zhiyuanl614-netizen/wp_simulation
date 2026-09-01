"""
全耦合边界 + 一致性验证 + 补水可供性评估 (语义 ①: 补水不反馈进城市水力)
=========================================================================
背景 (docs/coupling_map.md §全耦合验证): 把 54 路额定补水 (299.7 L/s) 反馈进
D-town 基线不可行 (城市基线仅 ~246 L/s, 耦合节点 min 压头 −12 m); 即使昼间模式+
总量预算可行, 任何非零反馈都会耗尽水箱缓冲使 never 层 (~24 h) 失压, 与已发布
分层/保留三对矛盾。故最终语义: 城市水力保持无补水口径 (与 saet_distribution /
coupling_map 完全一致), 额定补水作为【被评估的需求】事后用 PDD 计算可供比例。

本模块输出 (results/muni/):
  full_coupling_boundary.json   54 母线全耦合边界 (boundary 口径压头轨迹) + 可供性
  full_coupling_consistency.csv 逐母线: 静态映射 strata/t_fail vs 本模块重算 (应 100%)

三组仿真 (均无补水反馈, EPANET 2.2, PDD required=20/min=0, 15 min):
  baseline : 无故障 24h            -> 健康/可行性 (耦合节点 min pressure)
  saet     : R1 自 t=0 阶跃停供 72h -> 重算 t_fail, 与 coupling_map 分层对比
  boundary : R1 自 t=6h 起 3h 降压  -> 54 条压头轨迹 + t_fail_after_fault_s (下游输入)
可供性评估: 对 boundary 轨迹, 按 EPANET PDD 供水分额 f(p)=sqrt(clip(p/20,0,1))
  计算各取水口额定补水的逐时可供量与 72h 累计可供/需求比。
"""
import os, json, csv, tempfile
import numpy as np
import wntr

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "data", "DTOWN.inp")
RES = os.path.join(HERE, "..", "..", "results", "muni")
CMAP = os.path.join(RES, "coupling_map.json")

H_MUNI_MIN = 28.0
HEALTHY_MIN = 32.0
P_REQ = 20.0
SOURCE = "R1"
STRATA = ["Q1_fast", "Q2", "Q3", "Q4_slow", "never"]


def _run(wn):
    with tempfile.TemporaryDirectory() as td:
        cwd = os.getcwd()
        try:
            os.chdir(td)
            res = wntr.sim.EpanetSimulator(wn).run_sim(version=2.2)
        finally:
            os.chdir(cwd)
    return res


def _model(duration_h, step_min):
    wn = wntr.network.WaterNetworkModel(INP)
    wn.options.quality.parameter = "NONE"
    wn.options.time.duration = int(duration_h * 3600)
    wn.options.time.hydraulic_timestep = int(step_min * 60)
    wn.options.time.report_timestep = int(step_min * 60)
    wn.options.hydraulic.demand_model = "PDD"
    wn.options.hydraulic.required_pressure = P_REQ
    wn.options.hydraulic.minimum_pressure = 0.0
    return wn


def pdd_frac(p):
    return np.sqrt(np.clip(p / P_REQ, 0.0, 1.0))


if __name__ == "__main__":
    cm = json.load(open(CMAP))
    rows = cm["map"]
    q = cm["quartiles_h"]
    mk_total = sum(r["makeup_Lps"] for r in rows)

    # ---------------- [1/3] baseline 健康/可行性 ----------------
    wn = _model(24.0, 15)
    res = _run(wn)
    prB = res.node["pressure"]
    flow = res.link["flowrate"]
    outl = [l for l in wn.link_name_list if wn.get_link(l).start_node_name == SOURCE]
    src_lps = float(flow[outl].sum(axis=1).mean() * 1000)
    base_lps = float(sum(sum(d.base_value for d in wn.get_node(j).demand_timeseries_list)
                         for j in wn.junction_name_list) * 1000)
    pmin = {r["junction"]: float(prB[r["junction"]].min()) for r in rows}
    n32 = sum(1 for v in pmin.values() if v <= HEALTHY_MIN)
    n28 = sum(1 for v in pmin.values() if v <= H_MUNI_MIN)
    print("== [1/3] baseline 24h (无补水反馈) ==")
    print("  水源平均出力 %.0f L/s, 基线需水 %.0f L/s; 额定补水(评估对象) %.1f L/s"
          % (src_lps, base_lps, mk_total))
    print("  耦合节点 min pressure: min %.1f m; <=32m: %d; <=28m: %d"
          % (min(pmin.values()), n32, n28))

    # ---------------- [2/3] saet 口径一致性 ----------------
    wn = _model(72.0, 15)
    R1 = wn.get_node(SOURCE)
    wn.add_pattern("outage", [0.001] * (72 * 4 + 3))
    R1.head_timeseries.base_value = R1.base_head
    R1.head_timeseries.pattern_name = "outage"
    prS = _run(wn).node["pressure"]
    thS = (prS.index / 3600.0).to_numpy()

    def strat_of(t):
        if t is None:
            return "never"
        return ("Q1_fast" if t < q["q25"] else "Q2" if t < q["q50"]
                else "Q3" if t < q["q75"] else "Q4_slow")

    cons = []
    for r in rows:
        h = prS[r["junction"]].to_numpy()
        b = np.where(h < H_MUNI_MIN)[0]
        t_new = float(thS[b[0]]) if len(b) else None
        cons.append(dict(bus=r["bus"], junction=r["junction"],
                         stratum_map=r["stratum"], stratum_new=strat_of(t_new),
                         t_fail_map_h=r["t_fail_h"],
                         t_fail_new_h=(round(t_new, 2) if t_new is not None else None)))
    agree = sum(1 for c in cons if (c["stratum_map"] == c["stratum_new"]
                                    and c["t_fail_map_h"] == c["t_fail_new_h"]))
    agree_s = sum(1 for c in cons if c["stratum_map"] == c["stratum_new"])
    print("== [2/3] saet 口径一致性 (应=100%%) ==")
    print("  分层一致 %d/54 (%.1f%%); 分层+时刻完全一致 %d/54"
          % (agree_s, 100.0 * agree_s / 54, agree))

    # ---------------- [3/3] boundary 口径 + 可供性评估 ----------------
    wn = _model(72.0, 15)
    R1 = wn.get_node(SOURCE)
    base = R1.base_head
    mult = []
    for i in range(72 * 4 + 3):
        t = i * 0.25
        mult.append(1.0 if t < 6.0 else max(0.02, 1.0 - (t - 6.0) / 3.0))
    wn.add_pattern("r_decline", mult)
    R1.head_timeseries.base_value = base
    R1.head_timeseries.pattern_name = "r_decline"
    prD = _run(wn).node["pressure"]
    thD = (prD.index / 3600.0).to_numpy()
    dt_h = float(thD[1] - thD[0])

    plants, avail_rows = {}, []
    for r in rows:
        j = r["junction"]
        h = prD[j].to_numpy()
        head0 = float(h[thD <= 6.0][-1])
        post = np.where((h < H_MUNI_MIN) & (thD >= 6.0))[0]
        t_fail = float(thD[post[0]]) if len(post) else None
        f = pdd_frac(h)                                   # PDD 可供份额
        delivered = f * r["makeup_Lps"]
        zero = np.where((h <= 0.0) & (thD >= 6.0))[0]
        t_zero = float(thD[zero[0]]) if len(zero) else None
        req_m3 = r["makeup_Lps"] * 3.6 * 72.0
        del_m3 = float(np.trapezoid(delivered, thD) * 3.6)
        i6 = np.argmin(np.abs(thD - 6.0))
        plants[str(r["bus"])] = dict(
            node=j, makeup_Lps=r["makeup_Lps"], head0_m=round(head0, 2),
            t_fail_h=(round(t_fail, 3) if t_fail is not None else None),
            t_fail_after_fault_s=(round((t_fail - 6.0) * 3600, 1)
                                  if t_fail is not None else None),
            pressure_m=[round(float(x), 2) for x in h])
        avail_rows.append(dict(bus=r["bus"], stratum=r["stratum"],
                               avail_frac_at_fault=round(float(f[i6]), 3),
                               t_to_zero_h=(round(t_zero, 2) if t_zero else None),
                               delivered_72h_m3=round(del_m3, 1),
                               requested_72h_m3=round(req_m3, 1),
                               delivery_ratio=round(del_m3 / req_m3, 3)))

    # 分层汇总可供性
    strat_avail = {}
    for s in STRATA:
        sub = [a for a in avail_rows if a["stratum"] == s]
        strat_avail[s] = dict(n=len(sub),
                              mean_delivery_ratio=round(
                                  sum(a["delivery_ratio"] for a in sub) / len(sub), 3),
                              n_zero_before_24h=sum(
                                  1 for a in sub if (a["t_to_zero_h"] or 99) <= 24))
    tot_req = sum(a["requested_72h_m3"] for a in avail_rows)
    tot_del = sum(a["delivered_72h_m3"] for a in avail_rows)
    print("== [3/3] boundary 口径 + 额定补水可供性 (PDD 事后评估) ==")
    for s in STRATA:
        a = strat_avail[s]
        print("  %-8s n=%2d  72h可供/需求=%5.1f%%  24h内断供节点 %2d"
              % (s, a["n"], 100 * a["mean_delivery_ratio"], a["n_zero_before_24h"]))
    print("  全网合计: 需求 %.0f m3, 可供 %.0f m3 (%.1f%%)"
          % (tot_req, tot_del, 100 * tot_del / tot_req))

    out = dict(
        source=cm["source"], network="DTOWN.inp",
        semantics="makeup NOT fed back into city hydraulics (见模块 docstring / docs)",
        method="EPANET 2.2 EPS (PDD required=20m/min=0, quality off), 15min",
        makeup_rated_total_Lps=round(mk_total, 1), n_coupled=len(rows),
        baseline=dict(source_supply_Lps=round(src_lps, 1),
                      base_demand_Lps=round(base_lps, 1),
                      healthy_min_m=HEALTHY_MIN, n_coupled_le32m=n32,
                      n_coupled_le28m=n28,
                      coupled_minp_min_m=round(min(pmin.values()), 1)),
        consistency=dict(quartiles_h=q, agree_strata=agree_s, agree_exact=agree,
                         n=len(cons), rows=cons),
        boundary_protocol=dict(t_fault_h=6.0, decline_h=3.0, duration_h=72.0,
                               H_muni_min_m=H_MUNI_MIN),
        makeup_availability=dict(pdd="f=sqrt(clip(p/20,0,1))",
                                 strata=strat_avail,
                                 total_requested_m3=round(tot_req, 1),
                                 total_delivered_m3=round(tot_del, 1),
                                 rows=avail_rows),
        plants=plants,
    )
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "full_coupling_boundary.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False)
    with open(os.path.join(RES, "full_coupling_consistency.csv"), "w", newline="") as f:
        wd = csv.DictWriter(f, fieldnames=list(cons[0].keys()))
        wd.writeheader()
        wd.writerows(cons)
    print("saved full_coupling_boundary.json / full_coupling_consistency.csv")
