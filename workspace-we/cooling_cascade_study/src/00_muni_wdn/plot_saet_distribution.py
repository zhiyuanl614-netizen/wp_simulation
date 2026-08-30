"""
Fig.10  Network-wide distribution of intake depressurization times.
  (a) histogram (P10/median/P90 representative nodes)
  (b) cumulative failure fraction (CDF, with never-fail plateau)
  (c) spatial map coloured by failure time
Reads results/muni/saet_distribution.json -> figures/Fig10_depressurization_time_distribution.png
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.collections import LineCollection

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")

COLS = {"fast": COLORS["power"], "median": COLORS["amber"], "slow": COLORS["ok"]}
LAB = {"fast": "Fast (P10)", "median": "Median (P50)", "slow": "Slow (P90)"}


def main():
    with open(os.path.join(RES, "saet_distribution.json")) as f:
        o = json.load(f)
    s = o["stats"]
    dur = o["duration_h"]
    reps = o["representatives"]
    tf = o["tfail_h"]
    finite = np.array([v for v in tf.values() if v is not None])
    never = s["n_never_fail"]

    fig = plt.figure(figsize=(13.5, 4.6))
    gs = GridSpec(1, 3, figure=fig, wspace=0.30, width_ratios=[1, 1, 1.18])

    # (a) histogram
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(finite, bins=24, color=COLORS["muni"], alpha=0.85, edgecolor="white")
    for tag, r in reps.items():
        ax1.axvline(r["t_fail_h"], color=COLS[tag], lw=1.8, ls="--")
        yy = ax1.get_ylim()[1] * (0.95 if tag == "fast" else 0.80 if tag == "median" else 0.65)
        ax1.text(r["t_fail_h"] + 1, yy, f"{LAB[tag]}\n{r['node']}\n{r['t_fail_h']:.1f} h",
                 color=COLS[tag], fontsize=8, va="top")
    ax1.set_xlabel("Depressurization time (h, from source outage)")
    ax1.set_ylabel("Number of nodes")
    ax1.set_title("(a) Failure-time histogram\n(%d nodes failing within %d h)"
                  % (s["n_fail_within"], dur), fontsize=10.5)

    # (b) CDF
    ax2 = fig.add_subplot(gs[0, 1])
    xs = np.sort(finite)
    total = s["n_junctions"]
    ys = np.arange(1, len(xs) + 1) / total * 100
    ax2.plot(xs, ys, color=COLORS["power"])
    plateau = (total - never) / total * 100
    ax2.axhline(plateau, color=COLORS["mut"], ls=":", lw=1.2)
    ax2.text(dur * 0.98, plateau - 5,
             f"{plateau:.0f}% eventually fail\n({never} nodes / {never/total*100:.0f}% never fail)",
             ha="right", fontsize=8, color=COLORS["mut"])
    for tag, r in reps.items():
        ax2.axvline(r["t_fail_h"], color=COLS[tag], lw=1.2, ls="--")
    ax2.set_xlabel("Depressurization time (h)")
    ax2.set_ylabel("Cumulative failed nodes (%)")
    ax2.set_title("(b) Cumulative failure fraction (CDF)", fontsize=10.5)
    ax2.set_ylim(0, 100)

    # (c) spatial map
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.grid(False)
    nc = o["coords"]
    segs = [[nc[a], nc[b]] for a, b in o["edges"] if a in nc and b in nc]
    ax3.add_collection(LineCollection(segs, colors="#dddddd", linewidths=0.4, zorder=1))
    xs = [nc[j][0] for j in tf]; ys = [nc[j][1] for j in tf]
    cvals = np.array([tf[j] if tf[j] is not None else np.nan for j in tf], dtype=float)
    fin = ~np.isnan(cvals)
    ax3.scatter(np.array(xs)[~fin], np.array(ys)[~fin], c="#bbbbbb", s=7, zorder=2,
                label="Never fail (>%d h)" % dur)
    sc = ax3.scatter(np.array(xs)[fin], np.array(ys)[fin], c=cvals[fin], cmap="RdYlGn",
                     s=9, zorder=3, vmin=0, vmax=np.nanpercentile(cvals, 95))
    for tag, r in reps.items():
        j = r["node"]
        ax3.scatter([nc[j][0]], [nc[j][1]], marker="*", s=240, edgecolor="k",
                    facecolor=COLS[tag], linewidths=1.0, zorder=5)
        ax3.annotate(f"{LAB[tag]}\n{j}", (nc[j][0], nc[j][1]),
                     textcoords="offset points", xytext=(6, 6), fontsize=7.5,
                     color=COLS[tag], fontweight="bold")
    rc = o["reservoir_coord"]
    ax3.scatter([rc[0]], [rc[1]], marker="s", s=90, c="#1a1a1a", zorder=6, label="Source R1")
    ax3.scatter([v[0] for v in o["tanks"].values()], [v[1] for v in o["tanks"].values()],
                marker="^", s=50, edgecolor="k", facecolor="none", linewidths=0.8,
                zorder=4, label="Tanks")
    ax3.set_xticks([]); ax3.set_yticks([]); ax3.set_aspect("equal")
    ax3.set_title("(c) Spatial map of failure time (\u2605 = rep. nodes)", fontsize=10.5)
    ax3.legend(fontsize=7, loc="lower left")
    cbar = fig.colorbar(sc, ax=ax3, fraction=0.045, pad=0.02)
    cbar.set_label("Failure time (h)", fontsize=9)

    fig.suptitle("Intake depressurization time strongly depends on intake location "
                 "(0\u2013%.0f h; %.0f%% never fail)" % (s["max_h"], s["never_fail_pct"]),
                 fontsize=12.5, y=1.02)
    fig.savefig(os.path.join(FIG, "Fig10_depressurization_time_distribution.png"), **SAVE)
    print("saved Fig10")


if __name__ == "__main__":
    main()
