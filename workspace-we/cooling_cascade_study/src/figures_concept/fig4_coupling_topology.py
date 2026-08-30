"""
Fig.4 (§3.1)  Water-power coupling topology (planar, 3 panels)
==============================================================
(a) D-town water network topology (real coords): source / tank / junction only.
(b) IEEE-118 power grid (standard one-line diagram image) + Generator/Bus legend.
(c) Coupling excerpt: intake node -> cooling-water system nodes -> plant bus
    (one-line style, all black), with plant-bus electrical neighbours.
No panel titles; legends instead. Output: figures/Fig4_coupling_topology.png (300 dpi)
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
import wntr

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "..", "00_muni_wdn", "data", "DTOWN.inp")
ONELINE = os.path.join(HERE, "assets", "IEEE118_oneline.png")
OUT = os.path.join(HERE, "..", "..", "figures", "Fig4_coupling_topology.png")

PAIRS = [("J411", 89), ("J371", 80), ("J197", 10)]
GRID_NB = {89: [85, 88, 90, 92], 80: [77, 79, 81, 96, 97, 98, 99], 10: [9]}
# cooling-water system nodes (plant-internal), same for each plant
COOL = ["Make-up\ntank", "Pool", "Circ.\npump", "Condenser", "LP\ncylinder"]

fig = plt.figure(figsize=(13.5, 9.2))
gs = GridSpec(2, 2, figure=fig, height_ratios=[1.05, 1.05], hspace=0.12, wspace=0.14)

# ================= (a) D-town water network =================
axA = fig.add_subplot(gs[0, 0]); axA.grid(False); axA.set_axis_off()
wn = wntr.network.WaterNetworkModel(INP)
nc = {n: wn.get_node(n).coordinates for n in wn.node_name_list}
allx = np.array([c[0] for c in nc.values()]); ally = np.array([c[1] for c in nc.values()])
x0, x1, y0, y1 = allx.min(), allx.max(), ally.min(), ally.max()
def NX(x): return (x-x0)/(x1-x0)
def NY(y): return (y-y0)/(y1-y0)
for ln in wn.pipe_name_list:
    l = wn.get_link(ln); a, b = l.start_node_name, l.end_node_name
    if a in nc and b in nc:
        axA.plot([NX(nc[a][0]), NX(nc[b][0])], [NY(nc[a][1]), NY(nc[b][1])],
                 color="#b8c2cc", lw=0.5, zorder=1)
# junctions (black dots)
axA.scatter([NX(nc[j][0]) for j in wn.junction_name_list],
            [NY(nc[j][1]) for j in wn.junction_name_list],
            s=7, c="#1a1a1a", zorder=2)
# tanks (small black filled square)
axA.scatter([NX(nc[t][0]) for t in wn.tank_name_list],
            [NY(nc[t][1]) for t in wn.tank_name_list], marker="s", s=22,
            c="#1a1a1a", zorder=3)
# water source (small red filled star)
r = wn.reservoir_name_list[0]
axA.scatter([NX(nc[r][0])], [NY(nc[r][1])], marker="*", s=90, c="#c0392b",
            edgecolor="none", zorder=4)
axA.text(-0.02, 1.06, "(a)", transform=axA.transAxes, fontsize=13, fontweight="bold", va="top")
legA = [Line2D([0], [0], marker="o", color="none", markerfacecolor="#1a1a1a",
               markersize=4, label="Junction node"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#1a1a1a",
               markersize=6, label="Tank"),
        Line2D([0], [0], marker="*", color="none", markerfacecolor="#c0392b",
               markersize=10, label="Water source")]
axA.legend(handles=legA, fontsize=8.5, loc="lower left",
           bbox_to_anchor=(0.0, 0.0), frameon=True)   # bottom-left corner
axA.set_xlim(-0.05, 1.05); axA.set_ylim(-0.08, 1.08); axA.set_aspect("equal")

# ================= (b) IEEE-118 one-line + legend =================
axB = fig.add_subplot(gs[0, 1]); axB.grid(False); axB.set_axis_off()
axB.imshow(mpimg.imread(ONELINE))
axB.text(-0.02, 1.04, "(b)", transform=axB.transAxes, fontsize=13, fontweight="bold", va="top")
# overlay legend: G-circle = Generator, thick bar = Bus
axB.scatter([0.055], [0.055], transform=axB.transAxes, s=150, facecolor="white",
            edgecolor="black", linewidths=1.2, zorder=5)
axB.text(0.055, 0.055, "G", transform=axB.transAxes, fontsize=8, ha="center",
         va="center", zorder=6)
axB.text(0.085, 0.055, "Generator", transform=axB.transAxes, fontsize=9, va="center")
axB.plot([0.035, 0.075], [0.11, 0.11], transform=axB.transAxes, color="black",
         lw=3.2, zorder=5)
axB.text(0.085, 0.11, "Bus", transform=axB.transAxes, fontsize=9, va="center")

# ================= (c) coupling excerpt (one-line style, all black) =================
axC = fig.add_subplot(gs[1, :]); axC.grid(False); axC.set_axis_off()
axC.text(0.005, 1.06, "(c)", transform=axC.transAxes, fontsize=13, fontweight="bold", va="top")
ymap = {89: 0.80, 80: 0.50, 10: 0.20}
x_intake = 0.05
x_cool = np.linspace(0.15, 0.44, len(COOL))
x_bus = 0.60
BK = "#1a1a1a"

def bus_bar(x, y, w=0.028, lw=4):
    """one-line style bus = short thick vertical bar; returns."""
    axC.plot([x, x], [y-w, y+w], color=BK, lw=lw, zorder=5, solid_capstyle="butt")

def gen_symbol(x, y):
    axC.scatter([x], [y], s=150, facecolor="white", edgecolor=BK, linewidths=1.2, zorder=6)
    axC.text(x, y, "G", fontsize=8, ha="center", va="center", zorder=7)

for node, bus in PAIRS:
    yy = ymap[bus]
    # intake node (black circle)
    axC.scatter([x_intake], [yy], s=48, facecolor="white", edgecolor=BK,
                linewidths=1.2, zorder=5)
    axC.text(x_intake, yy-0.075, f"{node}\n(intake)", ha="center", va="top",
             fontsize=8.5, color=BK)
    # cooling-water system nodes (black boxes) + connecting black lines
    prev = (x_intake, yy)
    for i, (cx, name) in enumerate(zip(x_cool, COOL)):
        axC.plot([prev[0], cx], [prev[1], yy], color=BK, lw=1.2, zorder=3)
        axC.add_patch(plt.Rectangle((cx-0.026, yy-0.045), 0.052, 0.09,
                      facecolor="white", edgecolor=BK, lw=1.0, zorder=4))
        axC.text(cx, yy, name, ha="center", va="center", fontsize=6.6, color=BK, zorder=5)
        prev = (cx, yy)
    # link last cooling node -> plant bus
    axC.plot([prev[0], x_bus], [yy, yy], color=BK, lw=1.2, zorder=3)
    # plant bus (one-line bar) + generator
    bus_bar(x_bus, yy)
    gen_symbol(x_bus, yy + 0.075)
    axC.text(x_bus - 0.015, yy + 0.05, f"bus {bus}", fontsize=9, color=BK,
             ha="right", va="center", fontweight="bold")
    # electrical neighbours (thin bus bars, connected black lines)
    nbs = GRID_NB[bus]; n = len(nbs)
    step = min(0.05, 0.30 / max(n, 1)); gx = x_bus + 0.16
    for i, g in enumerate(nbs):
        gy = yy + step * (i - (n-1)/2.0) if n > 1 else yy
        axC.plot([x_bus, gx], [yy, gy], color=BK, lw=0.9, zorder=2)
        axC.plot([gx, gx], [gy-0.014, gy+0.014], color=BK, lw=2.2, zorder=3,
                 solid_capstyle="butt")
        axC.text(gx + 0.012, gy, str(g), fontsize=7, color=BK, va="center")

# column headers + cooling-system bracket label
axC.text(x_intake, 0.96, "Water intake", ha="center", fontsize=9.5, fontweight="bold", color=BK)
axC.text(x_cool.mean(), 0.96, "Cooling-water system (plant-internal)", ha="center",
         fontsize=9.5, fontweight="bold", color=BK)
axC.text(x_bus + 0.10, 0.96, "Power grid (plant bus + neighbours)", ha="center",
         fontsize=9.5, fontweight="bold", color=BK)
# legend for (c)
legC = [Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
               markeredgecolor=BK, markersize=7, label="Intake node"),
        plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=BK, label="Cooling-water node"),
        Line2D([0], [0], color=BK, lw=4, label="Bus"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
               markeredgecolor=BK, markersize=9, label="Generator (G)")]
axC.legend(handles=legC, fontsize=8.5, loc="lower center", ncol=4, frameon=True)
axC.set_xlim(0, 1.0); axC.set_ylim(0, 1.0)

fig.savefig(OUT, **SAVE)
print("saved Fig4 (3-panel, revised)")
