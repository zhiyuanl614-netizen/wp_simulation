"""
Fig.13  Intake-node position sensitivity.
  (a) municipal depressurization-time distribution + representative nodes
  (b) layout (CO vs DISP) x strategy (PA/SP/DP) max deficit
Reads results/proactive_control/p6_node_sensitivity.json + results/muni/saet_distribution.json
 -> figures/Fig13_intake_node_sensitivity.png
校准 v2 (2026-09-02, 用户指令: 同步前序规范——字号 12 统一/序号加粗左上/图例简洁
不覆盖主图):
- 字号统一 12: (a) 代表节点 8 号三行自由文本标签(需手动避让、压柱风险) → 3 条
  vline 入图例 upper right(与图 12(a) 同款式, 跨图一致); (b) 数值标签 9 -> 12、
  图例 8.5 -> 12;
- (b) 图例标签精简为 "CO (co-located intakes)"/"DISP (dispersed intakes)"
  ( simultaneity/staggered 语义移图注), 定点 upper right——SP/DP 组柱高为 0,
  右侧整带净空;
- (b) y 轴顶部 18% 余量防数值标签裁切(沿用图 10 方案);
- 机理结论(峰值不叠加 343→315 MW、主动对位置稳健)移图注(沿用图 11 方例);
- 旧编号残留修正: docstring "Fig.11" -> Fig.13、print("saved Fig11") -> Fig13。
数据核实 (2026-09-02): pip install pypower 后复跑 node_sensitivity.py (12 个 LP,
~178 s) -> p6_node_sensitivity.json 逐字节一致; CO PA 343.27 MW/71.93 MWh 与图 10
同一联合 LP 一致; DISP PA 314.95/52.48; SP/DP 双布置均 0/0。
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
MUNI_RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")

COLS = {"fast": COLORS["power"], "median": COLORS["amber"], "slow": COLORS["ok"]}
LAB = {"fast": "Fast (P10)", "median": "Median (P50)", "slow": "Slow (P90)"}


def main():
    with open(os.path.join(RES, "p6_node_sensitivity.json")) as f:
        o = json.load(f)
    with open(os.path.join(MUNI_RES, "saet_distribution.json")) as f:
        dist = json.load(f)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))

    # (a) municipal depressurization-time distribution
    tf = [v for v in dist["tfail_h"].values() if v is not None]
    ax1.hist(tf, bins=24, color=COLORS["muni"], alpha=0.85, edgecolor="white")
    reps = dist["representatives"]
    for tag, r in reps.items():
        ax1.axvline(r["t_fail_h"], color=COLS[tag], lw=1.8, ls="--",
                    label="%s: %s, %.2f h" % (LAB[tag], r["node"], r["t_fail_h"]))
    ax1.set_xlabel("Intake depressurization time (h, from outage)")
    ax1.set_ylabel("Number of nodes")
    ax1.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    ax1.legend(loc="upper right")

    # (b) layout x strategy
    modes = ["PA", "SP", "DP"]
    co = [o["layouts"]["CO"]["results"][m]["max_deficit_MW"] for m in modes]
    dp = [o["layouts"]["DISP"]["results"][m]["max_deficit_MW"] for m in modes]
    x = np.arange(len(modes)); w = 0.36
    b1 = ax2.bar(x - w/2, co, w, label="CO (co-located intakes)", color=COLORS["power"])
    b2 = ax2.bar(x + w/2, dp, w, label="DISP (dispersed intakes)", color=COLORS["muni"])
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax2.annotate(f"{h:.0f}", (bar.get_x() + bar.get_width()/2, h),
                         textcoords="offset points", xytext=(0, 3), ha="center",
                         fontsize=12, fontweight="bold")
    ax2.set_xticks(x); ax2.set_xticklabels(["Passive PA", "Static SP", "Dynamic DP"])
    ax2.set_ylabel("System max power deficit (MW)")
    ax2.set_ylim(0, max(co + dp) * 1.18)          # v2: 18% 顶部余量防标签裁切
    ax2.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
    ax2.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Fig13_intake_node_sensitivity.png"), **SAVE)
    print("saved Fig13")


if __name__ == "__main__":
    main()
