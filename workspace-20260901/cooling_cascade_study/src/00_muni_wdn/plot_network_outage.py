"""
Fig.6  Spatio-temporal pressure collapse under unique-source outage.
  top: (a) network pressure stats vs time; (b) failed-node fraction vs time
  bottom: spatial snapshots (nodes coloured by pressure)
Reads results/muni/network_outage.json -> figures/Fig6_network_outage_spatiotemporal.png
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


def main():
    with open(os.path.join(RES, "network_outage.json")) as f:
        o = json.load(f)
    s = o["stats"]
    t = np.array(s["t_h"])
    tf = o["t_fault_h"]
    thr = o["H_muni_min_m"]
    nc = o["node_coords"]

    fig = plt.figure(figsize=(13, 8.6))
    gs = GridSpec(2, len(o["snap_hours"]), figure=fig, height_ratios=[1.0, 1.12],
                  hspace=0.36, wspace=0.12)

    # (a) pressure stats vs time
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.fill_between(t, s["p10"], s["p90"], color="#9cc3e6", alpha=0.35, label="P10\u2013P90 band")
    ax1.plot(t, s["mean"], color=COLORS["muni"], label="Network mean")
    ax1.plot(t, s["p50"], color="#123a5c", lw=1.4, ls="--", label="Median")
    ax1.axhline(thr, color="k", ls=":", lw=1.1)
    ax1.text(t[-1], thr + 2, f"Threshold {thr:.0f} m", ha="right", fontsize=8.5)
    ax1.axvline(tf, color=COLORS["power"], ls=":", lw=1.3)
    ax1.text(tf + 0.5, ax1.get_ylim()[1] * 0.88, "Unique source\noutage t=%.0f h" % tf,
             color="black", fontsize=8.5)
    ax1.set_xlabel("Time (h)")
    ax1.set_ylabel("Node pressure head (m)")
    ax1.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    ax1.legend(fontsize=8.5, loc="lower left")

    # (b) failed-node fraction
    ax2 = fig.add_subplot(gs[0, 2:])
    fb = np.array(s["frac_below"]) * 100
    ax2.plot(t, fb, color=COLORS["power"])
    ax2.fill_between(t, 0, fb, color=COLORS["power"], alpha=0.15)
    ax2.axvline(tf, color=COLORS["power"], ls=":", lw=1.3)
    half = np.where(np.array(s["frac_below"]) >= 0.5)[0]
    if len(half):
        th50 = t[half[0]]
        ax2.axhline(50, color=COLORS["mut"], ls="--", lw=0.9)
        ax2.plot([th50], [50], "o", color="#7b241c", ms=8)
        ax2.annotate(f"Half of network fails\nt={th50:.0f} h (+{th50-tf:.0f} h)",
                     (th50, 50), textcoords="offset points", xytext=(12, -30),
                     fontsize=8.5, color="black",
                     arrowprops=dict(arrowstyle="->", color="black"))
    ax2.set_xlabel("Time (h)")
    ax2.set_ylabel("Failed nodes (%)")
    ax2.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
    ax2.set_ylim(0, 100)

    # bottom: spatial snapshots
    segs = [[nc[a], nc[b]] for a, b in o["edges"] if a in nc and b in nc]
    res_xy = o["reservoir_coord"]; tanks = o["tanks"]
    sub = "abcd"
    for col, h in enumerate(o["snap_hours"]):
        ax = fig.add_subplot(gs[1, col])
        ax.grid(False)
        ax.add_collection(LineCollection(segs, colors="#cccccc", linewidths=0.4, zorder=1))
        snap = o["snapshots"][str(h)]
        xs = [nc[j][0] for j in snap]; ys = [nc[j][1] for j in snap]
        cs = [snap[j] for j in snap]
        sc = ax.scatter(xs, ys, c=cs, cmap="RdYlBu", vmin=0, vmax=80, s=8, zorder=2)
        ax.scatter([res_xy[0]], [res_xy[1]], marker="s", s=80, c="#1a1a1a",
                   zorder=4, label="Source R1")
        ax.scatter([v[0] for v in tanks.values()], [v[1] for v in tanks.values()],
                   marker="^", s=50, edgecolor="k", facecolor=COLORS["ok"],
                   linewidths=0.6, zorder=3, label="Tanks")
        frac = np.mean(np.array(cs) < thr) * 100
        tag = "pre-outage" if h < tf else "+%.0f h" % (h - tf)
        ax.set_title("(c%d)" % (col + 1), fontsize=12, fontweight="bold", loc="left")
        ax.text(0.03, 0.96, "t=%d h (%s)\nfailed %.0f%%" % (h, tag, frac),
                transform=ax.transAxes, fontsize=8, color="black", va="top")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
        if col == 0:
            ax.legend(fontsize=6.8, loc="lower left")

    cbar = fig.colorbar(sc, ax=fig.get_axes()[2:], fraction=0.02, pad=0.01)
    cbar.set_label("Node pressure head (m)", fontsize=9)

    fig.savefig(os.path.join(FIG, "Fig6_network_outage_spatiotemporal.png"), **SAVE)
    print("saved Fig6")


if __name__ == "__main__":
    main()
