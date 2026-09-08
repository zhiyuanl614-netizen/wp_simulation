"""
②' 全序级联: 按 junction 失效顺序的 72h 联合 LP 级联仿真
==================================================================
事件: 有出力(Pg>0)且取水节点在 boundary 口径下失效的耦合机组,
  绝对跳机时刻 T_i = t_muni,i (h, 首破 28m) + SAET_i (min->h)。
窗口合并: 事件排序后, 相邻间隔 > GAP(200 min) 才另起新簇; 否则并入同一
  联合 LP —— 覆盖"多台机组冷却水中断窗口重叠"的综合调度 (用户指定)。
联合 LP 语义:
  * 已跳机组(前窗)以零出力带入本窗 (负偏移), 其失去出力按剩余机组备用
    裕度抬升 Pg0 (裕度不足部分由 deficit 吸收, 即"未完全恢复"的保守残差);
  * PA 被动因果约束仅作用于本窗新跳机组 (first_trip_override_min);
  * SP 以各机自身 SAET 为控制时间软着陆 (自其危机起点起算)。
对照基线:
  SUM: 每事件独立单机 LP (错峰分解: 能量相加/峰值取大);
  SIM: 全事件同时失效 (偏移 0, 保守上界)。
输出: results/proactive_control/full_order_cascade.json + 控制台摘要。
"""
import os, sys, json, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "01_cooling_chain"))
from proactive_lp import ProactiveLP
import warning_indicators as wi

RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
MUNI = os.path.join(HERE, "..", "..", "results", "muni")
GAP_MIN = 200.0          # 相邻事件间隔超过此值才视为独立 (单事件脉冲约 <=200 min)
WIN_MIN = 200.0          # 每簇末尾附加窗口
RAMP = 0.01


def build_events():
    rows = json.load(open(os.path.join(MUNI, "coupling_map.json")))["map"]
    fb = json.load(open(os.path.join(MUNI, "full_coupling_boundary.json")))
    ev = []
    for r in rows:
        if r["Pg_MW"] <= 0.0:
            continue
        pl = fb["plants"][str(r["bus"])]
        tf = pl["t_fail_h"]
        if tf is None:
            continue
        from params import Params, load_unit_from_gen
        Pg_, Pm_ = load_unit_from_gen(bus=r["bus"])
        t_trip, _ = wi._forward_water(Params(Pg_MW=Pg_, Pmax_MW=Pm_),
                                      out_frac_fn=None, dt=2.0, t_end=24*3600.0)
        if t_trip is None:
            continue  # 24h 内断水亦不跳机: 无级联事件
        saet = t_trip / 60.0
        ev.append(dict(bus=r["bus"], Pg=r["Pg_MW"], t_muni_h=tf,
                       saet_min=saet, T_h=tf + saet / 60.0))
    ev.sort(key=lambda e: e["T_h"])
    return ev


def clusterize(ev):
    clusters, cur = [], [ev[0]]
    for e in ev[1:]:
        if (e["T_h"] - cur[-1]["T_h"]) * 60.0 > GAP_MIN:
            clusters.append(cur)
            cur = [e]
        else:
            cur.append(e)
    clusters.append(cur)
    return clusters


def solve_cluster(cluster, prior):
    T0m = min(e["t_muni_h"] for e in cluster)      # 危机起点 (市政失压)
    horizon = (max(e["T_h"] for e in cluster) - T0m) * 60.0 + WIN_MIN
    dt = 5.0
    aff = list(prior) + [e["bus"] for e in cluster]
    offs = [-1.0e4] * len(prior) + [(e["t_muni_h"] - T0m) * 60.0 for e in cluster]
    lp = ProactiveLP(affected_buses=aff, horizon_min=horizon, dt_min=dt,
                     enforce_dc=True, ramp_frac_per_min=RAMP,
                     muni_offset_min=offs, dc_hard=True)
    # 前窗已跳机组: 零出力 + 失去出力按备用裕度抬升其余机组
    if prior:
        g = lp.net.gbus
        L = float(sum(lp.Pg0[g[b]] for b in prior))
        newPg0 = lp.Pg0.copy()
        for b in prior:
            newPg0[g[b]] = 0.0
        rest = [i for i in range(lp.ng) if i not in lp.aff_idx]
        head = np.clip(lp.Pmax[rest] - lp.Pg0[rest], 0.0, None)
        tot = head.sum()
        add = L * head / tot if tot > 1e-9 else np.full(len(rest), L / len(rest))
        for i, a in zip(rest, add):
            newPg0[i] = min(lp.Pmax[i], newPg0[i] + a)
        lp.Pg0 = newPg0
        lp.rest_cap = np.minimum(newPg0 + lp.reserve_frac * (lp.Pmax - newPg0),
                                 lp.Pmax)
    tc = [1.0] * len(prior) + [e["saet_min"] for e in cluster]
    override = min((e["t_muni_h"] - T0m) * 60.0 + e["saet_min"] for e in cluster)
    rec = dict(T0_h=round(T0m, 2), first_trip_h=round(cluster[0]["T_h"], 2),
               horizon_min=round(horizon, 0), dt=dt,
               buses_new=[e["bus"] for e in cluster],
               buses_prior=list(prior),
               lost_new_MW=round(sum(e["Pg"] for e in cluster), 1))
    for mode, kw in [("PA", dict(first_trip_override_min=override)),
                     ("SP", dict(T_ctrl=tc, first_trip_override_min=override))]:
        t0 = time.time()
        r = lp.solve(mode=mode, **kw)
        secs = round(time.time() - t0, 1)
        if r["feasible"]:
            rec[mode] = dict(feasible=True, s=secs,
                             maxdef_MW=round(r["max_deficit_MW"], 1),
                             energy_MWh=round(r["energy_deficit_MWh"], 1),
                             deficit=list(np.round(r["deficit"], 2)))
        else:
            rec[mode] = dict(feasible=False, s=secs, msg=r.get("msg", ""))
    return rec


def single_and_sim(ev):
    out = {"single": [], "sim": {}}
    for e in ev:
        hp = e["saet_min"] + WIN_MIN
        lp = ProactiveLP(affected_buses=[e["bus"]], horizon_min=hp,
                         dt_min=5.0, enforce_dc=True,
                         ramp_frac_per_min=RAMP, dc_hard=True)
        rec = dict(bus=e["bus"])
        for mode, tc in [("PA", None), ("SP", [e["saet_min"]])]:
            r = lp.solve(mode=mode, T_ctrl=tc)
            rec[mode] = (round(r["max_deficit_MW"], 1),
                         round(r["energy_deficit_MWh"], 1)) if r["feasible"] else None
        out["single"].append(rec)
    buses = [e["bus"] for e in ev]
    hs = max(e["saet_min"] for e in ev) + WIN_MIN
    lp = ProactiveLP(affected_buses=buses, horizon_min=hs,
                     dt_min=5.0, enforce_dc=True,
                     ramp_frac_per_min=RAMP, dc_hard=True)
    saet = [e["saet_min"] for e in ev]
    for mode, tc in [("PA", None), ("SP", saet)]:
        r = lp.solve(mode=mode, T_ctrl=tc)
        out["sim"][mode] = (round(r["max_deficit_MW"], 1),
                            round(r["energy_deficit_MWh"], 1)) if r["feasible"] else None
    return out


def main():
    ev = build_events()
    print("全序级联事件 %d 个 (有出力且取水失效机组); 时间范围 %.1f–%.1f h"
          % (len(ev), ev[0]["T_h"], ev[-1]["T_h"]))
    clusters = clusterize(ev)
    print("窗口合并: %d 簇 (GAP=%.0f min)" % (len(clusters), GAP_MIN))
    seq, prior = [], []
    for c in clusters:
        rec = solve_cluster(c, prior)
        prior += [e["bus"] for e in c]
        seq.append(rec)
        pa = rec.get("PA", {}); sp = rec.get("SP", {})
        print(" 簇 T0=%5.1fh 新跳%s (lost %.0f MW) | PA %s | SP %s | %.0fs"
              % (rec["T0_h"], rec["buses_new"], rec["lost_new_MW"],
                 "max %.0f MW / %.1f MWh" % (pa["maxdef_MW"], pa["energy_MWh"])
                 if pa.get("feasible") else "INF",
                 "max %.0f MW / %.1f MWh" % (sp["maxdef_MW"], sp["energy_MWh"])
                 if sp.get("feasible") else "INF",
                 pa.get("s", 0) + sp.get("s", 0)))
    base = single_and_sim(ev)

    def tot(mode, key):
        v = [c[mode][key] for c in seq if c[mode].get("feasible")]
        return round(sum(v), 1) if len(v) == len(seq) else None

    seq_sum = {m: dict(maxdef_MW=max([c[m]["maxdef_MW"] for c in seq] or [0]),
                       energy_MWh=tot(m, "energy_MWh")) for m in ("PA", "SP")}
    sum_e = {m: round(sum(s[m][1] for s in base["single"] if s[m]), 1) for m in ("PA", "SP")}
    sum_p = {m: max(s[m][0] for s in base["single"] if s[m]) for m in ("PA", "SP")}
    print("\n== 全序(SEQ) vs 独立和(SUM) vs 同时上界(SIM) ==")
    for m in ("PA", "SP"):
        print("  %s: SEQ max %.0f MW / %s MWh | SUM max %.0f MW / %.1f MWh | SIM %s"
              % (m, seq_sum[m]["maxdef_MW"], seq_sum[m]["energy_MWh"],
                 sum_p[m], sum_e[m], base["sim"][m]))
    out = dict(gap_min=GAP_MIN, win_min=WIN_MIN, ramp=RAMP,
               events=ev, clusters=seq,
               seq_totals=seq_sum,
               sum_baseline=dict(energy_MWh=sum_e, maxdef_MW=sum_p),
               sim_baseline=base["sim"],
               single=base["single"])
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "full_order_cascade.json"), "w"),
              ensure_ascii=False, indent=1)
    print("saved full_order_cascade.json")


if __name__ == "__main__":
    main()
