"""
Fig.5  Full-coupling municipal boundary as a heatmap: rows = 54 intake nodes
(sorted by stratum Q1-Q5, then by first-failure time; every row labelled with
its junction name), columns = time (0-72 h), color = intake-node pressure
(RdYlBu as in Fig.6: failed/low head = red). White separators delimit strata;
open circles mark each node's first crossing of the 28 m threshold (the
staggered depressurization front); dotted line = source failure at t=6 h.
Reads results/muni/full_coupling_boundary.json + coupling_map.json
-> figures/Fig5_muni_staggered_depressurization.png
Style: Fig.1-4 conventions (no titles, black annotations, stratum palette).
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle  # noqa
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")

STRATA = ["Q1_fast", "Q2", "Q3", "Q4_slow", "never"]
LAB = {"Q1_fast": "Q1", "Q2": "Q2", "Q3": "Q3", "Q4_slow": "Q4", "never": "Q5"}
COL = {"Q1_fast": COLORS["power"], "Q2": COLORS["amber"], "Q3": COLORS["muni"],
       "Q4_slow": COLORS["ok"], "never": "#8a97a3"}


def main():
    fb = json.load(open(os.path.join(RES, "full_coupling_boundary.json")))
    cm = json.load(open(os.path.join(RES, "coupling_map.json")))
    strat = {int(r["bus"]): r["stratum"] for r in cm["map"]}
    nodelab = {int(r["bus"]): r["junction"] for r in cm["map"]}
    thr = fb["boundary_protocol"]["H_muni_min_m"]
    tf = fb["boundary_protocol"]["t_fault_h"]
    plants = fb["plants"]

    # rows: stratum order Q1->Q5, then first-failure time (never-fail last)
    order = []
    for s in STRATA:
        members = [(int(b), plants[b]) for b in plants if strat[int(b)] == s]
        members.sort(key=lambda bp: (bp[1]["t_fail_h"] is None,
                                     bp[1]["t_fail_h"] or 0.0, bp[0]))
        order += [(s, b, p) for b, p in members]
    n = len(order)
    H = np.array([p["pressure_m"] for _, _, p in order])

    fig, ax = plt.subplots(figsize=(11.5, 9.6))
    im = ax.imshow(H, aspect="auto", cmap="RdYlBu", vmin=0, vmax=80,
                   extent=[0, 72, n, 0], interpolation="nearest")
    ax.grid(False)

    # stratum separators + right-hand key outside the axes (Q1 (N=..) ... Q5)
    y = 0
    for s in STRATA:
        cnt = sum(1 for o in order if o[0] == s)
        if cnt == 0:
            continue
        ax.hlines(y, 0, 72, color="white", lw=1.1, zorder=3)
        yf = 1.0 - (y + cnt / 2.0) / n
        ax.text(1.015, yf, "$\\blacksquare$", transform=ax.transAxes, fontsize=11,
                color=COL[s], va="center", ha="left")
        ax.text(1.06, yf, "%s (N=%d)" % (LAB[s], cnt), transform=ax.transAxes,
                va="center", ha="left", fontsize=9.5, color="black")
        y += cnt
    ax.hlines(n, 0, 72, color="white", lw=1.1, zorder=3)

    # depressurization front: first crossing of the 28 m threshold per row
    for i, (s, b, p) in enumerate(order):
        if p["t_fail_h"] is not None:
            ax.plot(p["t_fail_h"], i + 0.5, "o", ms=3.4, mfc="white", mec="black",
                    mew=0.9, zorder=4)

    ax.axvline(tf, color="white", ls=":", lw=1.3, zorder=3)
    ax.text(tf + 0.8, 2.0, "Source pressure failure, t=%.0f h" % tf,
            fontsize=9, color="black")

    # every junction name on the y axis
    ax.set_yticks(np.arange(n) + 0.5)
    ax.set_yticklabels([nodelab[b] for _, b, _ in order], fontsize=6.5,
                       color="black")
    ax.tick_params(axis="y", length=2, pad=1.5)

    ax.set_xlim(0, 72)
    ax.set_xticks([0, 12, 24, 36, 48, 60, 72])
    ax.set_ylim(n, 0)
    ax.set_xlabel("Time (h)")

    cbar = fig.colorbar(im, ax=ax, fraction=0.016, pad=0.17)
    cbar.set_label("Intake-node pressure (m)", fontsize=9.5)
    cbar.ax.axhline(thr, color="black", ls="--", lw=1.0)
    cbar.ax.text(-0.9, thr, "%.0f m" % thr, va="center", ha="right", fontsize=8,
                 color="black", transform=cbar.ax.get_yaxis_transform())

    fig.tight_layout()
    fig.text(0.02, 0.005, "rows ordered Q1-Q5, then by first-fail time;   "
             "o = first crossing < %.0f m" % thr, fontsize=8.5, color="black")
    fig.savefig(os.path.join(FIG, "Fig5_muni_staggered_depressurization.png"), **SAVE)
    plt.close(fig)
    print("saved Fig5 (heatmap, 54 labelled rows, RdYlBu)")


if __name__ == "__main__":
    main()
