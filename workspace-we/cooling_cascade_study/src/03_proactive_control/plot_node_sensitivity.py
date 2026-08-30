"""
Fig.11  Intake-node position sensitivity.
  (a) municipal depressurization-time distribution + representative nodes
  (b) layout (CO vs DISP) x strategy (PA/SP/DP) max deficit
Reads results/proactive_control/p6_node_sensitivity.json + results/muni/saet_distribution.json
 -> figures/Fig11_intake_node_sensitivity.png
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))

    # (a) municipal depressurization-time distribution
    tf = [v for v in dist["tfail_h"].values() if v is not None]
    ax1.hist(tf, bins=24, color=COLORS["muni"], alpha=0.85, edgecolor="white")
    reps = dist["representatives"]
    for tag, r in reps.items():
        ax1.axvline(r["t_fail_h"], color=COLS[tag], lw=1.8, ls="--")
        yy = ax1.get_ylim()[1] * (0.95 if tag == "fast" else 0.80 if tag == "median" else 0.65)
        ax1.text(r["t_fail_h"] + 1, yy, f"{LAB[tag]}\n{r['node']}\n{r['t_fail_h']:.1f} h",
                 color=COLS[tag], fontsize=8, va="top")
    s = dist["stats"]
    ax1.set_xlabel("Intake depressurization time (h, from outage)")
    ax1.set_ylabel("Number of nodes")
    ax1.set_title("(a) Depressurization time depends strongly on intake location\n"
                  "(0\u2013%.0f h; %.0f%% never fail)" % (s["max_h"], s["never_fail_pct"]),
                  fontsize=10.5)

    # (b) layout x strategy
    modes = ["PA", "SP", "DP"]
    co = [o["layouts"]["CO"]["results"][m]["max_deficit_MW"] for m in modes]
    dp = [o["layouts"]["DISP"]["results"][m]["max_deficit_MW"] for m in modes]
    x = np.arange(len(modes)); w = 0.36
    b1 = ax2.bar(x - w/2, co, w, label="CO: co-located intakes (simultaneous)", color=COLORS["power"])
    b2 = ax2.bar(x + w/2, dp, w, label="DISP: dispersed intakes (staggered)", color=COLORS["muni"])
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax2.annotate(f"{h:.0f}", (bar.get_x() + bar.get_width()/2, h),
                         textcoords="offset points", xytext=(0, 3), ha="center",
                         fontsize=9, fontweight="bold")
    ax2.set_xticks(x); ax2.set_xticklabels(["Passive PA", "Static SP", "Dynamic DP"])
    ax2.set_ylabel("System max power deficit (MW)")
    ax2.set_title("(b) Intake layout \u00d7 control strategy \u2192 max deficit\n"
                  "Passive: dispersed peaks do not add up; proactive: robust (deficit eliminated)",
                  fontsize=10.5)
    ax2.legend(fontsize=8.5, loc="upper right")

    fig.suptitle("Intake-node position sensitivity: passive control is affected, "
                 "proactive control is robust", fontsize=12.5, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Fig11_intake_node_sensitivity.png"), **SAVE)
    print("saved Fig11")


if __name__ == "__main__":
    main()
