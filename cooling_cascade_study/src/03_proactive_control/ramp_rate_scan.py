"""
其余机组备用爬坡率 R 扫描（审阅指导 P1-1 补充实验；ch5 §5.3 回填）
====================================================================
研究疑问 (审阅指导 P1-1): SP 可行性对其余机组备用爬坡率 R 的敏感性如何？
是否存在"R 减半 → SP 缺额转正"的相变点？k>=3 的 SP 残留缺额是爬坡驱动
还是网络/备用余量驱动？

v2 (2026-09-15 耦合层重构后): 三场景全部取自耦合层指定的 6 台凝汽式机组
(bus 89/80/10/66/65/26 ↔ J102/J97/J198/J5/J217/J177) 的子集。

严格复用既有 LP 链路 (proactive_lp.ProactiveLP), **仅把 ramp_frac_per_min
作为扫描变量**, 其余口径与 run_p6 / nk_scan 完全一致:
  - horizon 300 min (由 200 扩, 覆盖 6 台中最大 SAET 185.5 min 的软着陆窗口),
    时步 5 min, DC 潮流约束 (PTDF) enforce_dc=True
  - 备用上限 = 物理余量 (reserve_frac=1.0: Pg0 + 1.0*(Pmax-Pg0), 全部 54 台)
  - 目标 min Σdeficit + 5.0·Σoverload (过载松弛权重 5)
  - PA = 各机组水力跳闸时刻阶跃降零 (因果约束: 首跳前其余机组禁预升)
  - SP = 自危机起点按 T_ctrl=SAET 线性软着陆
  - 不传 first_trip_override_min / muni_offset_min (与 run_p6/nk_scan 同)

三场景 (全部与既定结果同口径, 可逐位回归校验):
  S1 单机 bus89 (607 MW, J102)      —— nk_scan k=1 worst 同子集
  S2 同源六机 CO (89,80,10,66,65,26) —— run_p6 / node_sensitivity CO 主场景 (ΣPg=2631 MW)
  S3 N-k worst k=3 (89,80,10)       —— nk_scan k=3 worst (v2 总体为 6 台, top-3 按 Pg 降序)

R 网格 {0.0025, 0.003, 0.0035, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.04}/min
  (覆盖审阅指导 P1-1 的 {0.005, 0.01, 0.02, 0.04}, 并在 0.005 以下加密以定位
   SP 相变点; 0.01 = run_p6/级联/取水敏感性既定值, 0.02 = nk_scan 默认值)

回归锚点 (v2 既定结果文件, 逐位复现校验, 容差 0.10 —— nk_scan.json 存 1 位小数):
  S1@0.02 / S3@0.02 与 nk_scan.json k=1 / k=3 worst 一致 (91.1 / 155.1 MW);
  S2@0.01 与 run_p6 CO τ=0 一致 (PA 334.88 MW / 59.61 MWh, SP 0/0)。

输出: results/proactive_control/ramp_rate_scan.json + .csv
      figures/Fig14_ramp_rate_scan.png (figstyle 统一样式, 300 dpi;
      若存在 dp_reserve_scan.json 则自动叠加 DP 曲线——DP 差异化扫描见 dp_reserve_scan.py)
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

RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
FIGDIR = os.path.join(HERE, "..", "..", "figures")

HORIZON_MIN = 300.0
DT_MIN = 5.0
R_GRID = [0.0025, 0.003, 0.0035, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.04]

SCENARIOS = [
    ("S1_single_bus89",  "Single bus89",           [89]),
    ("S2_CO_6unit",      "CO 6-unit (all coupled)", [89, 80, 10, 66, 65, 26]),
    ("S3_nk_worst_k3",   "N-k worst k=3",          [89, 80, 10]),
]

# (scenario, R, mode, field, expected, source) —— 与既定结果逐位对账
ANCHORS = [
    ("S1_single_bus89", 0.02, "PA", "max_deficit_MW",      91.1,  "nk_scan.json k=1 worst"),
    ("S1_single_bus89", 0.02, "PA", "energy_deficit_MWh",   7.6,  "nk_scan.json k=1 worst"),
    ("S1_single_bus89", 0.02, "SP", "energy_deficit_MWh",   0.0,  "nk_scan.json k=1 worst"),
    ("S2_CO_6unit",     0.01, "PA", "max_deficit_MW",     334.88, "run_p6 / p6_strategy_compare CO"),
    ("S2_CO_6unit",     0.01, "PA", "energy_deficit_MWh",  59.61, "run_p6 / p6_strategy_compare CO"),
    ("S2_CO_6unit",     0.01, "SP", "max_deficit_MW",       0.0,  "run_p6 / p6_strategy_compare CO"),
    ("S2_CO_6unit",     0.01, "SP", "energy_deficit_MWh",   0.0,  "run_p6 / p6_strategy_compare CO"),
    ("S3_nk_worst_k3",  0.02, "PA", "max_deficit_MW",     155.1,  "nk_scan.json k=3 worst"),
    ("S3_nk_worst_k3",  0.02, "PA", "energy_deficit_MWh",  12.9,  "nk_scan.json k=3 worst"),
    ("S3_nk_worst_k3",  0.02, "SP", "energy_deficit_MWh",   0.0,  "nk_scan.json k=3 worst"),
]
TOL = 0.10   # nk_scan.json 存 1 位小数 → 对账容差放宽至 0.10
ZERO_THR = 0.5   # MWh, 判 "SP 零缺额" 的阈值


def scan():
    rows = []
    for name, label, buses in SCENARIOS:
        saet = critical_indicators(buses)
        print(f"\n=== {name} ({label})  SAET = {[round(s, 1) for s in saet]} min ===")
        for R in R_GRID:
            lp = ProactiveLP(affected_buses=list(buses), horizon_min=HORIZON_MIN,
                             dt_min=DT_MIN, enforce_dc=True, ramp_frac_per_min=R)
            lost = round(float(sum(lp.Pg0[gi] for gi in lp.aff_idx)), 1)
            for mode, Tc in [("PA", None), ("SP", saet)]:
                t0 = time.time()
                r = lp.solve(mode=mode, T_ctrl=Tc)
                dt_s = time.time() - t0
                rec = dict(scenario=name, label=label, buses=list(buses),
                           R_per_min=R, mode=mode, lost_MW=lost,
                           saet_min=[round(s, 1) for s in saet])
                if r["feasible"]:
                    rec.update(feasible=True,
                               max_deficit_MW=round(float(r["max_deficit_MW"]), 2),
                               energy_deficit_MWh=round(float(r["energy_deficit_MWh"]), 2),
                               max_overload_MW=round(float(r["max_overload_MW"]), 2),
                               final_deficit_MW=round(float(r["deficit"][-1]), 2),
                               horizon_truncated=bool(float(r["deficit"][-1]) > ZERO_THR),
                               solve_s=round(dt_s, 1))
                else:
                    rec.update(feasible=False, max_deficit_MW=None,
                               energy_deficit_MWh=None, max_overload_MW=None,
                               final_deficit_MW=None, horizon_truncated=None,
                               solve_s=round(dt_s, 1))
                rows.append(rec)
                print(f"  R={R:<6g} {mode}: maxdef {rec['max_deficit_MW'] if rec['max_deficit_MW'] is not None else 'INF':>8}"
                      f" MW  energy {rec['energy_deficit_MWh'] if rec['energy_deficit_MWh'] is not None else 'INF':>8}"
                      f" MWh  ovl {rec['max_overload_MW'] if rec['max_overload_MW'] is not None else '-':>7}"
                      f" MW  final {rec['final_deficit_MW'] if rec['final_deficit_MW'] is not None else '-':>7}"
                      f" MW  ({rec['solve_s']:5.1f}s)")
    return rows


def check_anchors(rows):
    lookup = {(r["scenario"], r["R_per_min"], r["mode"]): r for r in rows}
    results = []
    for name, R, mode, field, expect, src in ANCHORS:
        r = lookup[(name, R, mode)]
        got = r.get(field)
        ok = (got is not None) and abs(got - expect) <= TOL
        results.append(dict(scenario=name, R_per_min=R, mode=mode, field=field,
                            expected=expect, got=got, source=src, ok=bool(ok)))
        flag = "OK " if ok else "FAIL"
        print(f"  [{flag}] {name} R={R:g} {mode} {field}: expect {expect}, got {got}  ({src})")
    return results


def phase_points(rows):
    """每场景 SP 相变点: 最小零缺额 R (其下紧邻网格点为非零)。"""
    ph = {}
    for name, label, buses in SCENARIOS:
        sp = sorted([r for r in rows if r["scenario"] == name and r["mode"] == "SP"
                     and r["feasible"]], key=lambda r: r["R_per_min"])
        e = [(r["R_per_min"], r["energy_deficit_MWh"]) for r in sp]
        nonzero = [R for R, v in e if v > ZERO_THR]
        zeros = [R for R, v in e if v <= ZERO_THR]
        monotone = all(Rz > Rn for Rz in zeros for Rn in nonzero)
        if not nonzero:
            d = dict(sp_zero_down_to_R=min(zeros),
                     note=f"SP 零缺额直到网格下限 R={min(zeros):g}/min")
        elif not zeros:
            d = dict(sp_nonzero_up_to_R=max(nonzero),
                     note=f"SP 缺额直到网格上限 R={max(nonzero):g}/min 仍非零")
        else:
            R_star = min(zeros)
            d = dict(R_star=R_star, R_below_nonzero=max(R for R in nonzero if R < R_star),
                     note=f"SP 相变点 R* ∈ ({max(R for R in nonzero if R < R_star):g}, {R_star:g}]")
        d["sp_energy_vs_R"] = {f"{R:g}": v for R, v in e}
        d["monotone_in_R"] = bool(monotone)
        ph[name] = d
    return ph


def make_figure(rows, ph, dp_rows=None, dp_ph=None):
    """R 扫描图：PA/SP 必绘；若给定 dp_rows（dp_reserve_scan.json）则叠加 DP 曲线与 DP 相变点。"""
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as mpe
    figstyle.apply()
    C = figstyle.COLORS
    col = {"S1_single_bus89": C["muni"], "S2_CO_6unit": C["power"],
           "S3_nk_worst_k3": C["amber"]}
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8))

    for ax, key, ylab in [(axes[0], "max_deficit_MW", "Peak deficit (MW)"),
                          (axes[1], "energy_deficit_MWh", "Energy deficit (MWh)")]:
        for name, label, buses in SCENARIOS:
            styles = [("PA", "s", "--", "white"), ("SP", "o", "-", None)]
            if dp_rows is not None:
                styles.append(("DP", "^", "-.", None))
            for mode, marker, ls, mfc in styles:
                src = dp_rows if (mode == "DP" and dp_rows is not None) else rows
                pts = sorted([(r["R_per_min"], r.get(key) or 0.0) for r in src
                              if r["scenario"] == name and r["mode"] == mode and r["feasible"]])
                if not pts:
                    continue
                kw = dict(color=col[name], ms=5, mec=col[name],
                          mfc=(mfc if mfc else col[name]))
                ax.plot([p[0] for p in pts], [p[1] for p in pts], ls, marker=marker,
                        label=f"{label} - {mode}", **kw)
        ax.set_xscale("log")
        ax.set_xlabel("Reserve ramp rate R (p.u. of $P_{\\max}$/min)")
        ax.set_ylabel(ylab)
        ax.set_xticks([0.0025, 0.005, 0.01, 0.02, 0.04])
        ax.set_xticklabels(["0.0025", "0.005", "0.01", "0.02", "0.04"])
        ax.axvline(0.01, color=C["mut"], ls=":", lw=1.2, zorder=0)

    axes[0].set_title("(a)", loc="left")
    axes[1].set_title("(b)", loc="left")
    axes[0].text(0.01, axes[0].get_ylim()[1] * 0.97, "R = 0.01 (baseline)",
                 color=C["mut"], fontsize=10, ha="left", rotation=90, va="top")

    # 相变点标注 (panel b): SP 与 DP 的 R* 各一枚箭头
    y_top = axes[1].get_ylim()[1]
    for i, (name, label, buses) in enumerate(SCENARIOS):
        for j, (tag, p) in enumerate([("SP", ph), ("DP", dp_ph or {})]):
            d = p.get(name, {})
            if "R_star" in d:
                y = y_top * (0.26 + 0.16 * i + 0.09 * j)
                tex = "$R^*$" if tag == "SP" else "$R^*_{\\mathrm{DP}}$"
                axes[1].annotate(f"{tex} = {d['R_star']:g}", xy=(d["R_star"], 0),
                                 xytext=(d["R_star"], y), color=col[name], fontsize=12,
                                 ha="center", zorder=6,
                                 path_effects=[mpe.withStroke(linewidth=3.0,
                                                              foreground="white")],
                                 arrowprops=dict(arrowstyle="->", color=col[name], lw=1.4))

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=12,
               frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    out = os.path.join(FIGDIR, "Fig14_ramp_rate_scan.png")
    fig.savefig(out, **figstyle.SAVE)
    print(f"\n图已保存: {out}")
    return out


def main():
    t0 = time.time()
    print("== 备用爬坡率 R 扫描 (仅 ramp_frac_per_min 为变量, 其余口径与 run_p6/nk_scan 一致) ==")
    rows = scan()

    print("\n== 回归锚点校验 (既定结果逐位对账) ==")
    anchors = check_anchors(rows)
    n_ok = sum(a["ok"] for a in anchors)
    assert n_ok == len(anchors), f"回归锚点 {len(anchors)-n_ok} 项不一致, 结果不可信, 终止"

    ph = phase_points(rows)
    print("\n== SP 相变点 ==")
    for name, d in ph.items():
        print(f"  {name}: {d['note']}  (单调性: {d['monotone_in_R']})")

    n_trunc = sum(1 for r in rows if r.get("horizon_truncated"))
    if n_trunc:
        print(f"\n[提示] {n_trunc} 行末时步缺额 > {ZERO_THR} MW → 时域截断, 能量为下界")

    out = dict(
        title="其余机组备用爬坡率 R 扫描 (审阅指导 P1-1)",
        generated=time.strftime("%Y-%m-%d %H:%M:%S"),
        version="v2 (6-unit coupled set)",
        caliber=("ProactiveLP 严格复用: horizon 300 min, dt 5 min, DC-PTDF (enforce_dc=True), "
                 "备用上限=Pg0+1.0*(Pmax-Pg0) (全部 54 台), 目标 min Σdeficit+5.0·Σoverload, "
                 "PA=水力跳闸时刻阶跃降零(因果约束, 首跳前禁预升), SP=T_ctrl=SAET 线性软着陆; "
                 "仅 ramp_frac_per_min 为扫描变量"),
        scenarios=[dict(name=n, label=l, buses=b) for n, l, b in SCENARIOS],
        saet_min={n: [round(s, 1) for s in critical_indicators(b)] for n, l, b in SCENARIOS},
        R_grid=R_GRID,
        rows=rows,
        phase_points=ph,
        regression_anchors=anchors,
        anchors_all_ok=True,
        notes=[
            "R=0.01 为 run_p6/级联/取水敏感性既定口径; R=0.02 为 nk_scan 默认口径",
            f"末时步缺额 > {ZERO_THR} MW 的行标记 horizon_truncated=True（时域截断，能量为下界）；"
            f"v2 本次共 {n_trunc} 行截断（horizon 300 min）",
            "v2 场景总体 = 耦合层 6 台凝汽式机组 (89/80/10/66/65/26 ↔ J102/J97/J198/J5/J217/J177)："
            "S1={89}、S3={89,80,10}(=nk_scan k=3 worst)、S2=全 6 台同源同时 CO",
            "SP 相变点定义: 网格内最小零缺额(≤0.5 MWh)的 R, 其下紧邻网格点缺额非零",
        ],
    )
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "ramp_rate_scan.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    fields = ["scenario", "label", "buses", "R_per_min", "mode", "feasible",
              "max_deficit_MW", "energy_deficit_MWh", "max_overload_MW",
              "final_deficit_MW", "horizon_truncated", "lost_MW", "saet_min", "solve_s"]
    with open(os.path.join(RES, "ramp_rate_scan.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "buses": ";".join(map(str, r["buses"])),
                        "saet_min": ";".join(str(s) for s in r["saet_min"])})

    make_figure(rows, ph)
    print(f"\n结果: {os.path.join(RES, 'ramp_rate_scan.json')} / .csv")
    print(f"总耗时 {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
