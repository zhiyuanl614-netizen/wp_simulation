"""
配对映射置换实验 (评审 M7 补充实验)
==================================
DISP 的"错峰削能量不削峰"结论部分内生於 rank↔rank 指定配对(最大机组←最早
失压节点)的方向。本脚本置换配对映射, 对每种配对解一个同口径联合 LP(DISP
时域, PA), 报告 PA 峰值/能量随配对的变化范围:

  designated  指定配对(基准): 机组按 Pg 降序 ← 节点按 t_fail 升序 (rank↔rank)
  reverse     反向配对:       最大机组 ← 最迟失压节点
  random-1/2/3 随机置换:      固定种子, 无偏对照

时域固定为 designated DISP 口径(max(τ_i+1.5·SAET_i)+30 min 向上取整到 10 min),
各配对同域可比。另对 designated/reverse 解 SP 检验主动控制零缺额稳健性。

输出: results/proactive_control/pairing_permutation.json
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from proactive_lp import ProactiveLP, critical_indicators   # noqa

RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
MUNI_RES = os.path.join(HERE, "..", "..", "results", "muni")
DT_MIN = 5.0
ALPHA = 1.5
RANDOM_SEEDS = [11, 23, 42]


def coupled():
    cm = json.load(open(os.path.join(MUNI_RES, "coupling_map.json")))
    return [(r["bus"], r["t_fail_h"]) for r in sorted(cm["map"], key=lambda r: r["rank"])]


def solve(buses, offsets_h, horizon_min, mode, saet):
    Tc = None if mode == "PA" else (saet if mode == "SP" else [s * ALPHA for s in saet])
    lp = ProactiveLP(affected_buses=list(buses), horizon_min=horizon_min,
                     dt_min=DT_MIN, enforce_dc=True, ramp_frac_per_min=0.01,
                     muni_offset_min=[o * 60.0 for o in offsets_h])
    r = lp.solve(mode=mode, T_ctrl=Tc)
    return dict(max_deficit_MW=round(float(r["max_deficit_MW"]), 2),
                energy_deficit_MWh=round(float(r["energy_deficit_MWh"]), 2),
                max_overload_MW=round(float(r["max_overload_MW"]), 2))


def main():
    pairs = coupled()
    buses = [b for b, _ in pairs]                     # Pg 降序 (rank 1..6)
    tf_sorted = sorted(t for _, t in pairs)           # t_fail 升序 (h)
    saet = critical_indicators(buses)
    print("=" * 92)
    print(" 配对映射置换实验 (评审 M7): PA 峰值/能量 vs 配对方向")
    print(" 机组(Pg降序): %s" % buses)
    print(" 节点失压时刻池(h, 升序): %s" % tf_sorted)
    print(" 冷却 SUET(min): %s" % [round(s, 1) for s in saet])
    print("=" * 92)

    # designated DISP 时域(与 node_sensitivity 同式), 各配对共用
    max_end = max(o * 60.0 + s * ALPHA for o, s in zip(tf_sorted, saet))
    horizon = float(int(np.ceil((max_end + 30.0) / 10.0) * 10))
    print(" 固定联合 LP 时域: %.0f min (designated DISP 口径)" % horizon)

    pairings = [("designated", list(tf_sorted)),
                ("reverse", list(reversed(tf_sorted)))]
    for seed in RANDOM_SEEDS:
        perm = np.random.default_rng(seed).permutation(len(tf_sorted))
        pairings.append((f"random-{seed}", [tf_sorted[i] for i in perm]))

    out = dict(version="v3", date="2026-09-20",
               buses=buses, tfail_pool_h=tf_sorted,
               cooling_SAET_min=[round(s, 1) for s in saet],
               horizon_min=horizon, dt_min=DT_MIN, alpha=ALPHA,
               power_flow="DC", ramp_frac_per_min=0.01,
               semantics="v3 统一语义(评审M1-A): SUET=92.4–192.9 min",
               pairings={})

    for name, offsets in pairings:
        pa = solve(buses, offsets, horizon, "PA", saet)
        entry = dict(offsets_h=offsets, PA=pa)
        print(" [%-12s] offsets(h)=%s" % (name, offsets))
        print("     PA  峰值 %7.1f MW   能量 %7.1f MWh   过载 %6.1f MW"
              % (pa["max_deficit_MW"], pa["energy_deficit_MWh"], pa["max_overload_MW"]))
        if name in ("designated", "reverse"):
            sp = solve(buses, offsets, horizon, "SP", saet)
            entry["SP"] = sp
            print("     SP  峰值 %7.1f MW   能量 %7.1f MWh   (主动控制零缺额检验)"
                  % (sp["max_deficit_MW"], sp["energy_deficit_MWh"]))
        out["pairings"][name] = entry

    # 汇总: PA 峰值/能量随配对的变化范围, designated 是否最坏方向
    pa_list = [(n, v["PA"]) for n, v in out["pairings"].items()]
    peaks = [p["max_deficit_MW"] for _, p in pa_list]
    energies = [p["energy_deficit_MWh"] for _, p in pa_list]
    desig = out["pairings"]["designated"]["PA"]
    out["summary"] = dict(
        PA_peak_range_MW=[min(peaks), max(peaks)],
        PA_energy_range_MWh=[min(energies), max(energies)],
        designated_is_worst_peak=bool(desig["max_deficit_MW"] == max(peaks)),
        designated_is_worst_energy=bool(desig["energy_deficit_MWh"] == max(energies)),
    )
    print("-" * 92)
    print(" PA 峰值范围 %.1f–%.1f MW; 能量范围 %.1f–%.1f MWh (跨 %d 种配对)"
          % (min(peaks), max(peaks), min(energies), max(energies), len(pa_list)))
    print(" 指定配对为最坏(峰值)方向: %s; 最坏(能量)方向: %s"
          % (out["summary"]["designated_is_worst_peak"],
             out["summary"]["designated_is_worst_energy"]))
    print("=" * 92)

    os.makedirs(RES, exist_ok=True)
    path = os.path.join(RES, "pairing_permutation.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved", path)


if __name__ == "__main__":
    main()
