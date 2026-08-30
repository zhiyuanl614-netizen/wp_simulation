"""
Fig.5  Municipal WDN boundary: intake-node pressure-head trajectories,
28 m threshold, and staggered depressurization times.
Reads results/muni/muni_boundary.json -> figures/Fig5_muni_staggered_depressurization.png
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")


def main():
    with open(os.path.join(RES, "muni_boundary.json")) as f:
        o = json.load(f)
    t = np.array(o["t_h"])
    tf = o["t_fault_h"]
    thr = o["H_muni_min_m"]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    colors = {"bus89": COLORS["power"], "bus80": COLORS["muni"], "bus10": COLORS["ok"]}
    zone_en = {"bus89": "Zone T5", "bus80": "Zone T4", "bus10": "Zone T3"}
    y_off = {"bus89": (-86, 26), "bus80": (10, -24), "bus10": (10, 20)}
    for pk, pl in o["plants"].items():
        h = np.array(pl["head_m"])
        ax.plot(t, h, color=colors.get(pk), label=f"{pk} @ {pl['node']} ({zone_en.get(pk,'')})")
        tfa = pl["t_fail_after_fault_s"]
        if tfa is not None:
            tfh = tf + tfa / 3600.0
            ax.plot([tfh], [thr], "o", color=colors.get(pk), ms=7, zorder=5)
            ax.annotate(f"{pk} fails +{tfa/3600.0:.1f} h", (tfh, thr),
                        textcoords="offset points", xytext=y_off.get(pk, (6, -14)),
                        fontsize=8.5, color=colors.get(pk), fontweight="bold",
                        arrowprops=dict(arrowstyle="-", color=colors.get(pk), lw=0.7))

    ax.axhline(thr, ls="--", color="k", lw=1.1)
    ax.text(t[-1], thr + 1.6, f"Min. supply threshold = {thr:.0f} m (failure = warning trigger)",
            ha="right", va="bottom", fontsize=8.5)
    ax.axvline(tf, ls=":", color=COLORS["mut"], lw=1.1)
    ax.text(tf + 0.4, 4, f"Source pressure failure\n(reservoir head drop), t={tf:.0f} h",
            fontsize=8.5, color=COLORS["mut"])

    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Intake-node pressure head (m)")
    ax.set_title("Staggered depressurization of plant intake nodes\n"
                 "under municipal source-pressure failure (D-town)", fontsize=11.5)
    ax.set_ylim(0, None)
    ax.legend(loc="upper right")
    ax.text(0.985, 0.03,
            "Diurnal ripples = D-town real demand pattern; nodes fail sequentially\n"
            "as their zone tanks deplete; first crossing below 28 m is latched.",
            transform=ax.transAxes, fontsize=7, color=COLORS["mut"], va="bottom", ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Fig5_muni_staggered_depressurization.png"), **SAVE)
    print("saved Fig5")


if __name__ == "__main__":
    main()
