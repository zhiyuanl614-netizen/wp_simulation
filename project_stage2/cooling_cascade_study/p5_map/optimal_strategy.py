"""
P5 —— 面向调度的最优预警-处置策略
==================================
基于韧性图谱, 对每一"故障规模"给出达到安全阈值(f>=49Hz)所需的
最小处置组合。两个主动处置杠杆:
  (L1) 预置/提前起机三级备用  —— 受预警提前量约束(需时间起机)
  (L2) 预防性切负荷(可中断负荷/需求响应) —— 快速但有代价(失负荷)

策略搜索: 给定预警提前量, 先用 L1(免失负荷), 不足再加 L2(最小切负荷),
输出每种规模的"最小切负荷比例"随预警提前量的变化 -> 处置代价曲线。
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p3_ieee118"))
from run_p3 import run   # noqa
from resilience_map import FAULT_SETS, SAFE_TH, DT, T_END, first_trip_time  # noqa

for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp); plt.rcParams["font.family"] = "Noto Sans CJK JP"; break
plt.rcParams["axes.unicode_minus"] = False
RESDIR = os.path.join(HERE, "..", "results")


def min_shed_for_safe(aff, t_detect, shed_grid=(0.0, 0.03, 0.06, 0.10, 0.15, 0.20, 0.25, 0.30)):
    """给定预警延时, 找到使 f_nadir>=SAFE_TH 的最小预防性切负荷比例。返回(shed, nadir)。"""
    for shed in shed_grid:
        s, _, _ = run(affected=list(aff), t_fault=60.0, ramp=0.0, t_end=T_END, dt=DT,
                      no_overload=True, proactive=True, t_detect=t_detect,
                      runback_rate_frac=0.0015, reserve_boost=0.0, preemptive_shed=shed)
        if s['f_nadir'] >= SAFE_TH:
            return shed, s['f_nadir']
    return shed_grid[-1], s['f_nadir']   # 即使最大切负荷仍未达标


def build():
    scales = sorted(FAULT_SETS.keys())
    leads = [1, 3, 5, 8, 12]
    strat = {}   # scale -> list of (lead, min_shed, nadir)
    for sc in scales:
        aff = FAULT_SETS[sc]
        t_first, f_pass = first_trip_time(aff)
        rows = []
        for lead in leads:
            t_detect = max(0.0, t_first - 60.0 - lead * 60.0)
            shed, nadir = min_shed_for_safe(aff, t_detect)
            rows.append((lead, shed, nadir))
        strat[sc] = dict(passive=f_pass, first_trip=t_first, rows=rows)
    return scales, leads, strat


def plot(scales, leads, strat, outname="p5_optimal_strategy.png"):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = plt.cm.viridis(np.linspace(0, 0.85, len(scales)))
    for sc, c in zip(scales, colors):
        rows = strat[sc]['rows']
        xs = [r[0] for r in rows]
        ys = [r[1] * 100 for r in rows]   # 切负荷 %
        ax.plot(xs, ys, "o-", color=c, lw=2,
                label=f"{sc}机共因 (被动{strat[sc]['passive']:.1f}Hz)")
    ax.set_xlabel("预警提前量 (min)")
    ax.set_ylabel("达到安全(f≥49Hz)所需最小预防性切负荷 (%系统负荷)")
    ax.set_title("P5 最优预警-处置策略 —— 处置代价随预警提前量的变化",
                 fontsize=12.5, fontweight="bold")
    ax.grid(alpha=.3); ax.legend(fontsize=9)
    ax.text(0.02, 0.97, "曲线越低=代价越小; 预警越早, 越能用'预置备用'替代'切负荷'",
            transform=ax.transAxes, fontsize=9, va="top", color="#333")
    fig.tight_layout()
    out = os.path.join(RESDIR, outname); fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig); print("saved", out)


def dump(scales, leads, strat):
    obj = {str(sc): dict(passive=round(strat[sc]['passive'], 2),
                         first_trip_s=round(strat[sc]['first_trip'], 0),
                         rows=[dict(lead_min=r[0], min_shed=r[1], nadir=round(r[2], 2))
                               for r in strat[sc]['rows']])
           for sc in scales}
    out = os.path.join(RESDIR, "p5_strategy.json")
    json.dump(obj, open(out, "w"), ensure_ascii=False, indent=2)
    print("saved", out)


if __name__ == "__main__":
    scales, leads, strat = build()
    plot(scales, leads, strat); dump(scales, leads, strat)
    print("\n=== 最优处置策略 (最小切负荷% 达 f>=49Hz) ===")
    for sc in scales:
        print(f"\n {sc}机共因 (被动 {strat[sc]['passive']:.1f}Hz):")
        for lead, shed, nadir in strat[sc]['rows']:
            tag = "仅预置备用" if shed == 0 else f"+切负荷{shed*100:.0f}%"
            print(f"   预警{lead:>2}min -> {tag:<12} f_nadir={nadir:.1f}Hz")
