"""
P6 主驱动 —— 被动/静态主动/动态主动 三策略对比 (对齐文献 Fig.6)
=============================================================
复刻 Yu et al.(Nat.Commun.2024) 的 PA/SP/DP 对比, 物理量 气->水, 潮流用 DC(方案B)。
输出: 控制台摘要 + results/p6_strategy_compare.json + 时序数据(供绘图)。
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proactive_lp import ProactiveLP, critical_indicators
import warning_indicators as wi

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "..", "results", "proactive_control")

STRAT = {"PA": "被动控制", "SP": "静态主动控制", "DP": "动态主动控制"}


def run(affected=(89, 80, 10), horizon_min=200, dt_min=5.0,
        ramp=0.01, alpha=1.5, enforce_dc=True):
    lp = ProactiveLP(affected_buses=list(affected), horizon_min=horizon_min,
                     dt_min=dt_min, enforce_dc=enforce_dc, ramp_frac_per_min=ramp)
    saet = critical_indicators(list(affected))

    results, series = {}, {}
    plans = {"PA": None, "SP": saet, "DP": [s * alpha for s in saet]}
    for mode in ["PA", "SP", "DP"]:
        r = lp.solve(mode=mode, T_ctrl=plans[mode])
        if not r["feasible"]:
            results[mode] = dict(feasible=False)
            continue
        results[mode] = dict(
            feasible=True,
            max_deficit_MW=round(r["max_deficit_MW"], 2),
            energy_deficit_MWh=round(r["energy_deficit_MWh"], 2),
            max_overload_MW=round(r["max_overload_MW"], 2))
        # 受影响机组总出力 & 缺额时序
        t = [i * dt_min for i in range(r["T"])]
        aff_total = r["Pg"][:, lp.aff_idx].sum(axis=1)
        series[mode] = dict(t=t, deficit=list(r["deficit"]),
                            aff_total=list(aff_total))

    # 早期预警指标
    ind = {str(b): wi.static_indicators(b) for b in affected}
    ind_out = {b: dict(SAET_min=round(v["SAET_min"], 1),
                       ASW0_m3=round(v["ASW0_m3"], 1)) for b, v in ind.items()}

    out = dict(affected=list(affected), horizon_min=horizon_min, dt_min=dt_min,
               ramp_frac_per_min=ramp, alpha=alpha, power_flow="DC",
               indicators=ind_out, results=results)
    with open(os.path.join(RESDIR, "p6_strategy_compare.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(RESDIR, "p6_timeseries.json"), "w") as f:
        json.dump(series, f)

    # 控制台摘要
    print("=" * 74)
    print(" P6 被动/静态主动/动态主动 对比 (DC潮流; 对齐文献 Fig.6)")
    print("=" * 74)
    print(f" 受影响机组: {list(affected)}  SAET(min): {[round(s,1) for s in saet]}")
    print("-" * 74)
    print(f" {'策略':<16}{'最大功率缺额':>14}{'总能量缺额':>14}{'最大过载':>12}")
    print("-" * 74)
    for m in ["PA", "SP", "DP"]:
        r = results[m]
        if r["feasible"]:
            print(f" {STRAT[m]:<14}{r['max_deficit_MW']:>12.1f}MW{r['energy_deficit_MWh']:>12.1f}MWh{r['max_overload_MW']:>10.1f}MW")
        else:
            print(f" {STRAT[m]:<14}{'不可行':>12}")
    print("-" * 74)
    print(" 结果: results/p6_strategy_compare.json")
    print("=" * 74)
    return out


if __name__ == "__main__":
    run()
