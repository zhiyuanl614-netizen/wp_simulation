"""
DP 困难场景差异化扫描 + LP 备用容量（reserve_frac）扫描（P1-3 首选方案 + P1-2 LP 侧）
====================================================================================
背景: R 扫描（ramp_rate_scan.py）造出了 "SP 有残差且系爬坡驱动" 的困难区域（低 R 的
CO 三机场景），使指导文档 P1-3 的**首选方案**（困难场景下 DP vs SP 差异化）可解；
同时补齐 P1-2 的 LP 侧备用容量轴（此前论文只有速率轴 R，缺容量轴 reserve_frac）。

(A) DP over R:  3 场景 × 9 R × DP（T_ctrl = 1.5×SAET，α=1.5 与 run_p6/node_sensitivity 一致）
    —— 检验 (i) 低 R 的 CO 区域 DP 是否优于 SP（更长窗口 → 更多备用爬坡积累，
       预期 SP 相变点按 ≈1/α 下移）；(ii) k=3 的 57.12 MW 网络地板对 DP 是否同样
       成立（窗口延长不改变网络输送约束，预期 DP 与 SP 同地板——反向加固结论）。
(B) reserve_frac 扫描: rf ∈ {1.0, 0.5, 0.35, 0.25} × 3 场景 × PA/SP，固定 R=0.01
    —— LP 备用上限 rest_cap = Pg0 + rf×(Pmax−Pg0)（全部 54 台）；
       备用容量轴：鉴别 k≥3 残留地板与 CO 可行性对备用容量的敏感性
       （备用容量不足 → 容量型缺额，与网络型地板、爬坡型相变三种机制可区分）。

严格复用 ProactiveLP（horizon 200 min / dt 5 min / DC-PTDF / 过载权重 5 / PA 因果约束），
除 mode/T_ctrl/reserve_frac 外口径与 ramp_rate_scan.py 完全一致。

回归锚点（容差 0.06）:
  - DP@R=0.01: CO = 0 MW/0 MWh/过载 36.76（run_p6 / p6_node_sensitivity CO 的 DP 行）;
    单机 bus89 = 0/0（node_sensitivity DISP 单机 DP）。
  - rf=1.0 各行 = ramp_rate_scan.json 的 R=0.01 列（同参数 LP，应逐位一致）。

输出: results/proactive_control/dp_reserve_scan.json + .csv
      figures/Fig14_ramp_rate_scan.png 重绘（叠加 DP 曲线；复用 ramp_rate_scan.make_figure）
"""
import os
import sys
import csv
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # src/ → figstyle
from proactive_lp import ProactiveLP, critical_indicators   # noqa: E402
import figstyle                                             # noqa: E402
from ramp_rate_scan import SCENARIOS, R_GRID, HORIZON_MIN, DT_MIN, ZERO_THR, make_figure  # noqa: E402

RES = os.path.join(HERE, "..", "..", "results", "proactive_control")

ALPHA = 1.5                 # DP 时间比（与 run_p6 / node_sensitivity 一致）
RF_GRID = [1.0, 0.5, 0.35, 0.25]
R_BASE = 0.01               # (B) 固定基线爬坡率
TOL = 0.06


def _rec(name, label, buses, saet, R, rf, mode, r, dt_s):
    rec = dict(scenario=name, label=label, buses=list(buses),
               R_per_min=R, reserve_frac=rf, mode=mode,
               saet_min=[round(s, 1) for s in saet])
    if r["feasible"]:
        rec.update(feasible=True,
                   max_deficit_MW=round(float(r["max_deficit_MW"]), 2),
                   energy_deficit_MWh=round(float(r["energy_deficit_MWh"]), 2),
                   max_overload_MW=round(float(r["max_overload_MW"]), 2),
                   final_deficit_MW=round(float(r["deficit"][-1]), 2),
                   solve_s=round(dt_s, 1))
    else:
        rec.update(feasible=False, max_deficit_MW=None, energy_deficit_MWh=None,
                   max_overload_MW=None, final_deficit_MW=None, solve_s=round(dt_s, 1))
    return rec


def scan_dp_over_r():
    """(A) DP 模式沿 R 网格（3 场景 × 9 R）。"""
    rows = []
    for name, label, buses in SCENARIOS:
        saet = critical_indicators(buses)
        Tc = [s * ALPHA for s in saet]
        print(f"\n=== (A) DP over R: {name} ({label})  T_ctrl = {[round(t,1) for t in Tc]} min ===")
        for R in R_GRID:
            lp = ProactiveLP(affected_buses=list(buses), horizon_min=HORIZON_MIN,
                             dt_min=DT_MIN, enforce_dc=True, ramp_frac_per_min=R)
            t0 = time.time()
            r = lp.solve(mode="DP", T_ctrl=Tc)
            rec = _rec(name, label, buses, saet, R, 1.0, "DP", r, time.time() - t0)
            rows.append(rec)
            print(f"  R={R:<6g} DP: maxdef {rec['max_deficit_MW']:>8} MW"
                  f"  energy {rec['energy_deficit_MWh']:>8} MWh"
                  f"  ovl {rec['max_overload_MW']:>7} MW"
                  f"  final {rec['final_deficit_MW']:>7} MW  ({rec['solve_s']:5.1f}s)")
    return rows


def scan_reserve_frac():
    """(B) reserve_frac 扫描（3 场景 × 4 rf × PA/SP，固定 R=0.01）。"""
    rows = []
    for name, label, buses in SCENARIOS:
        saet = critical_indicators(buses)
        print(f"\n=== (B) reserve_frac 扫描 @R=0.01: {name} ({label}) ===")
        for rf in RF_GRID:
            lp = ProactiveLP(affected_buses=list(buses), horizon_min=HORIZON_MIN,
                             dt_min=DT_MIN, enforce_dc=True,
                             ramp_frac_per_min=R_BASE, reserve_frac=rf)
            for mode, Tc in [("PA", None), ("SP", saet)]:
                t0 = time.time()
                r = lp.solve(mode=mode, T_ctrl=Tc)
                rec = _rec(name, label, buses, saet, R_BASE, rf, mode, r, time.time() - t0)
                rows.append(rec)
                print(f"  rf={rf:<5g} {mode}: maxdef {rec['max_deficit_MW']:>8} MW"
                      f"  energy {rec['energy_deficit_MWh']:>8} MWh"
                      f"  ovl {rec['max_overload_MW']:>7} MW"
                      f"  final {rec['final_deficit_MW']:>7} MW  ({rec['solve_s']:5.1f}s)")
    return rows


def check_anchors(dp_rows, rf_rows):
    """DP@0.01 对齐既定结果；rf=1.0 与 ramp_rate_scan.json 的 R=0.01 列逐位一致。"""
    with open(os.path.join(RES, "ramp_rate_scan.json")) as f:
        ramp = json.load(f)
    ramp01 = {(r["scenario"], r["mode"]): r for r in ramp["rows"] if r["R_per_min"] == 0.01}
    dp = {(r["scenario"]): r for r in dp_rows if r["R_per_min"] == 0.01}
    rf10 = {(r["scenario"], r["mode"]): r for r in rf_rows if r["reserve_frac"] == 1.0}
    results = []

    def add(ok, desc, expect, got):
        results.append(dict(check=desc, expected=expect, got=got, ok=bool(ok)))
        print(f"  [{'OK ' if ok else 'FAIL'}] {desc}: expect {expect}, got {got}")

    a = dp["S2_CO_3unit"]
    add(a["max_deficit_MW"] == 0.0 and a["energy_deficit_MWh"] == 0.0
        and abs(a["max_overload_MW"] - 36.76) <= TOL,
        "DP@R=0.01 CO 峰值/能量/过载 (run_p6·node_sensitivity DP)", "0/0/36.76",
        f"{a['max_deficit_MW']}/{a['energy_deficit_MWh']}/{a['max_overload_MW']}")
    b = dp["S1_single_bus89"]
    add(b["max_deficit_MW"] == 0.0 and b["energy_deficit_MWh"] == 0.0,
        "DP@R=0.01 单机 bus89 峰值/能量 (node_sensitivity DISP 单机 DP)", "0/0",
        f"{b['max_deficit_MW']}/{b['energy_deficit_MWh']}")

    for (sc, mode), ref in sorted(ramp01.items()):
        got = rf10.get((sc, mode))
        ok = (got is not None
              and abs(got["max_deficit_MW"] - ref["max_deficit_MW"]) <= 0.01
              and abs(got["energy_deficit_MWh"] - ref["energy_deficit_MWh"]) <= 0.01)
        add(ok, f"rf=1.0 {sc} {mode} = R 扫描 R=0.01 列（峰值/能量）",
            f"{ref['max_deficit_MW']}/{ref['energy_deficit_MWh']}",
            f"{got['max_deficit_MW']}/{got['energy_deficit_MWh']}" if got else None)
    return results


def phase_dp(dp_rows):
    """DP 相变点：最小零缺额 R（口径同 ramp_rate_scan.phase_points）。"""
    ph = {}
    for name, label, buses in SCENARIOS:
        e = sorted([(r["R_per_min"], r["energy_deficit_MWh"]) for r in dp_rows
                    if r["scenario"] == name and r["feasible"]])
        nonzero = [R for R, v in e if v > ZERO_THR]
        zeros = [R for R, v in e if v <= ZERO_THR]
        monotone = all(Rz > Rn for Rz in zeros for Rn in nonzero)
        if not nonzero:
            d = dict(sp_zero_down_to_R=min(zeros), note="DP 零缺额直到网格下限")
        elif not zeros:
            d = dict(sp_nonzero_up_to_R=max(nonzero), note="DP 缺额直到网格上限仍非零")
        else:
            R_star = min(zeros)
            d = dict(R_star=R_star, R_below_nonzero=max(R for R in nonzero if R < R_star),
                     note=f"DP 相变点 R*_DP ∈ ({max(R for R in nonzero if R < R_star):g}, {R_star:g}]")
        d["dp_energy_vs_R"] = {f"{R:g}": v for R, v in e}
        d["monotone_in_R"] = bool(monotone)
        ph[name] = d
    return ph


def phase_rf(rf_rows):
    """备用容量相变点：SP 零缺额的最小 rf（rf 越小备用越少）。"""
    ph = {}
    for name, label, buses in SCENARIOS:
        e = sorted([(r["reserve_frac"], r["energy_deficit_MWh"]) for r in rf_rows
                    if r["scenario"] == name and r["mode"] == "SP" and r["feasible"]])
        nonzero = [rf for rf, v in e if v > ZERO_THR]
        zeros = [rf for rf, v in e if v <= ZERO_THR]
        monotone = all(z > n for z in zeros for n in nonzero)   # rf 越大越易为零
        if not nonzero:
            d = dict(sp_zero_down_to_rf=min(zeros), note="SP 零缺额直到 rf 下限 0.25")
        elif not zeros:
            d = dict(sp_nonzero_up_to_rf=min(nonzero), note="SP 缺额直到 rf=1.0 仍非零")
        else:
            rf_star = min(zeros)                                # 最小可行 rf
            d = dict(rf_star=rf_star, rf_below_nonzero=max(nonzero),
                     note=f"备用容量相变点 rf* ∈ ({max(nonzero):g}, {rf_star:g}]")
        d["sp_energy_vs_rf"] = {f"{rf:g}": v for rf, v in e}
        d["monotone_in_rf"] = bool(monotone)
        ph[name] = d
    return ph


def main():
    t0 = time.time()
    print("== (A) DP 差异化扫描（沿 R 网格）＋ (B) LP 备用容量 reserve_frac 扫描 ==")
    dp_rows = scan_dp_over_r()
    rf_rows = scan_reserve_frac()

    print("\n== 回归锚点校验 ==")
    anchors = check_anchors(dp_rows, rf_rows)
    n_ok = sum(a["ok"] for a in anchors)
    assert n_ok == len(anchors), f"回归锚点 {len(anchors)-n_ok} 项不一致, 结果不可信, 终止"

    dp_ph = phase_dp(dp_rows)
    rf_ph = phase_rf(rf_rows)
    print("\n== DP 相变点 ==")
    for name, d in dp_ph.items():
        print(f"  {name}: {d['note']}  (单调性: {d['monotone_in_R']})")
    print("== 备用容量相变点 (SP) ==")
    for name, d in rf_ph.items():
        print(f"  {name}: {d['note']}  (单调性: {d['monotone_in_rf']})")

    out = dict(
        title="DP 差异化扫描（over R）＋ LP 备用容量 reserve_frac 扫描（P1-3 首选方案 + P1-2 LP 侧）",
        generated=time.strftime("%Y-%m-%d %H:%M:%S"),
        caliber=("ProactiveLP 严格复用（同 ramp_rate_scan）：horizon 200 min, dt 5 min, DC-PTDF, "
                 "过载权重 5, PA 因果约束；(A) DP = T_ctrl 1.5×SAET 沿 R 网格；"
                 "(B) reserve_frac ∈ {1.0,0.5,0.35,0.25} 固定 R=0.01，"
                 "rest_cap = Pg0 + rf×(Pmax−Pg0)（全部 54 台）"),
        alpha=ALPHA, r_grid=R_GRID, rf_grid=RF_GRID, r_base=R_BASE,
        scenarios=[dict(name=n, label=l, buses=b) for n, l, b in SCENARIOS],
        dp_rows=dp_rows, rf_rows=rf_rows,
        dp_phase_points=dp_ph, rf_phase_points=rf_ph,
        regression_anchors=anchors, anchors_all_ok=True,
        notes=[
            "DP 语义与 run_p6/node_sensitivity 一致：受影响机组在 1.5×SAET 窗口线性软着陆（更长窗口→备用更多爬坡积累）",
            "rf=1.0 行与 ramp_rate_scan.json 的 R=0.01 列为同一 LP（逐位一致，作为自洽校验）",
            "备用容量型缺额（rf 过低时系统总可用容量 < 负荷 4242 MW）与网络型地板（k=3 的 57.12 MW）、爬坡型相变（CO 的 R*）为三种可区分机制",
        ],
    )
    with open(os.path.join(RES, "dp_reserve_scan.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    fields = ["scan", "scenario", "label", "buses", "R_per_min", "reserve_frac", "mode",
              "feasible", "max_deficit_MW", "energy_deficit_MWh", "max_overload_MW",
              "final_deficit_MW", "saet_min", "solve_s"]
    with open(os.path.join(RES, "dp_reserve_scan.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in dp_rows:
            w.writerow({**r, "scan": "DP_over_R", "buses": ";".join(map(str, r["buses"])),
                        "saet_min": ";".join(str(s) for s in r["saet_min"])})
        for r in rf_rows:
            w.writerow({**r, "scan": "reserve_frac", "buses": ";".join(map(str, r["buses"])),
                        "saet_min": ";".join(str(s) for s in r["saet_min"])})

    # 图 14 重绘（PA/SP 来自 ramp_rate_scan.json, DP 叠加）
    with open(os.path.join(RES, "ramp_rate_scan.json")) as f:
        ramp = json.load(f)
    make_figure(ramp["rows"], ramp["phase_points"], dp_rows=dp_rows, dp_ph=dp_ph)

    print(f"\n结果: {os.path.join(RES, 'dp_reserve_scan.json')} / .csv")
    print(f"总耗时 {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
