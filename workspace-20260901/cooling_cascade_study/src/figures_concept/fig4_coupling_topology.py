"""
Fig.4 (§3.1)  Water-power coupling topology — full-coupling edition (3 panels)
==============================================================================
原 Fig.4 三面板框架; 无总标题/子标题, 仅保留面板序号 (a)(b)(c)。
  (a) D-town 水网 (真实坐标, 归一化): 54 个耦合取水节点按失压分层【彩色高亮 + 标签】;
  (b) IEEE-118 单线图 (用户提供的清晰矢量版): 54 个耦合发电机【彩色圆环锚定 G 圆
      (assets/...coords.json 的 genG) + 黑色标签】;
  (c) 54 对耦合配对图 (bipartite matching): 左=取水节点(分层/失压序, 左侧分层彩条),
      右=发电机母线(bus 号序), 连线按分层着色; 不展示中间冷却水场站。
  原"保留三对"不再特殊标注, 与其所在分层样式完全一致。
输出: figures/Fig4_coupling_topology.png (300 dpi)
"""
import os, sys, json
import numpy as np
import wntr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle  # noqa
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patheffects as pe
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from adjustText import adjust_text

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "..", "00_muni_wdn", "data", "DTOWN.inp")
ONELINE = os.path.join(HERE, "assets", "IEEE118_oneline.png")
COORDS = os.path.join(HERE, "assets", "IEEE118_bus_label_coords.json")
CMAP = os.path.join(HERE, "..", "..", "results", "muni", "coupling_map.json")
OUT = os.path.join(HERE, "..", "..", "figures", "Fig4_coupling_topology.png")

STRATA = ["Q1_fast", "Q2", "Q3", "Q4_slow", "never"]
COL = {"Q1_fast": COLORS["power"], "Q2": COLORS["amber"], "Q3": COLORS["muni"],
       "Q4_slow": COLORS["ok"], "never": "#8a97a3"}
LAB = {"Q1_fast": "Q1 fast", "Q2": "Q2", "Q3": "Q3", "Q4_slow": "Q4 slow",
       "never": "never fails"}
HALO = [pe.withStroke(linewidth=1.4, foreground="white")]

rows = json.load(open(CMAP))["map"]
coords = json.load(open(COORDS))

# ================= figure layout (放大子图, 仅留序号) =================
fig = plt.figure(figsize=(15.2, 12.9))
gs = fig.add_gridspec(2, 2, height_ratios=[0.93, 1.17], hspace=0.10, wspace=0.05)
axA = fig.add_subplot(gs[0, 0])
axB = fig.add_subplot(gs[0, 1])
axC = fig.add_subplot(gs[1, :])
for ax in (axA, axB, axC):
    ax.set_facecolor("none")
    ax.grid(False)
    ax.axis("off")

# ================= (a) D-town =================
wn = wntr.network.WaterNetworkModel(INP)
nc = {n: wn.get_node(n).coordinates for n in wn.node_name_list}
_allx = np.array([c[0] for c in nc.values()])
_ally = np.array([c[1] for c in nc.values()])
x0, x1, y0, y1 = _allx.min(), _allx.max(), _ally.min(), _ally.max()

def NX(x):
    return (x - x0) / (x1 - x0)

def NY(y):
    return (y - y0) / (y1 - y0)

segs = [[(NX(nc[l.start_node_name][0]), NY(nc[l.start_node_name][1])),
         (NX(nc[l.end_node_name][0]), NY(nc[l.end_node_name][1]))]
        for l in (wn.get_link(x) for x in wn.pipe_name_list)]
axA.add_collection(LineCollection(segs, colors="black", linewidths=0.35, zorder=1))
axA.scatter([NX(nc[j][0]) for j in wn.junction_name_list],
            [NY(nc[j][1]) for j in wn.junction_name_list], s=4, c="black", zorder=2)
axA.scatter([NX(nc[t][0]) for t in wn.tank_name_list],
            [NY(nc[t][1]) for t in wn.tank_name_list],
            marker="^", s=26, facecolor="#5b6b7a", edgecolor="#5b6b7a", linewidths=0.8, zorder=3)
axA.scatter([NX(nc["R1"][0])], [NY(nc["R1"][1])], marker="s", s=70, c="#1a1a1a", zorder=4)
txtA = []
for r in rows:  # 54 耦合节点: 彩色高亮; 标签自动避让排布
    x, y = NX(nc[r["junction"]][0]), NY(nc[r["junction"]][1])
    axA.scatter([x], [y], s=32, facecolor=COL[r["stratum"]], edgecolor="k",
                linewidths=0.55, zorder=5)
    txtA.append(axA.text(x, y, r["junction"], fontsize=5.2, color="black",
                         path_effects=HALO, zorder=7))
adjust_text(txtA, ax=axA, force_text=(0.9, 0.9), force_points=(0.5, 0.5),
            expand_points=(1.6, 1.8), max_move=None, lim=500)
axA.text(-0.01, 1.02, "(a)", transform=axA.transAxes, fontsize=14, fontweight="bold",
         va="bottom")
axA.set_xlim(-0.03, 1.03)
axA.set_ylim(-0.04, 1.04)
axA.set_aspect("equal")
legA = [Line2D([0], [0], marker="o", color="none", markerfacecolor="#c4ccd3",
               markersize=3.5, label="Junction node"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#5b6b7a",
               markeredgecolor="#5b6b7a", markersize=6, label="Tank"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#1a1a1a",
               markersize=6, label="Water source")]
axA.legend(handles=legA, fontsize=7.5, loc="lower left", frameon=True)

# ================= (b) IEEE-118 one-line + highlights =================
img = mpimg.imread(ONELINE)
axB.imshow(img)
sc = img.shape[1] / coords["page_pt"][0]          # PDF pt -> pixel
txtB = []
for r in rows:  # 54 耦合发电机: 彩色圆环锚定 G 圆 + 黑色标签 (自动避让排布)
    gx, gy = coords["genG"].get(str(r["bus"]), coords["bus"][str(r["bus"])])
    px, py = gx * sc, gy * sc
    axB.scatter([px], [py], s=150, facecolor="none", edgecolor=COL[r["stratum"]],
                linewidths=1.6, zorder=5)
    txtB.append(axB.text(px, py, str(r["bus"]), fontsize=6.4, fontweight="bold",
                         color="black", path_effects=HALO, zorder=6))
adjust_text(txtB, ax=axB, force_text=(0.9, 0.9), force_points=(0.5, 0.5),
            expand_points=(1.6, 1.8), max_move=None, lim=500)
axB.text(-0.01, 1.02, "(b)", transform=axB.transAxes, fontsize=14, fontweight="bold",
         va="bottom")
axB.scatter([0.045], [0.045], transform=axB.transAxes, s=120, facecolor="white",
            edgecolor="black", linewidths=1.0, zorder=5)
axB.text(0.045, 0.045, "G", transform=axB.transAxes, fontsize=7.5, ha="center",
         va="center", zorder=6)
axB.text(0.075, 0.045, "Generator", transform=axB.transAxes, fontsize=8.5, va="center")
axB.plot([0.03, 0.062], [0.085, 0.085], transform=axB.transAxes, color="black", lw=3.0,
         zorder=5)
axB.text(0.075, 0.085, "Bus", transform=axB.transAxes, fontsize=8.5, va="center")

# ================= (c) 54-pair matching diagram =================
xL, xR = 0.30, 0.70
left = sorted(rows, key=lambda r: (STRATA.index(r["stratum"]),
                                   r["t_fail_h"] if r["t_fail_h"] is not None else 1e9,
                                   r["junction"]))
right = sorted(rows, key=lambda r: r["bus"])
yL = {r["junction"]: len(left) - 1 - i for i, r in enumerate(left)}
yR = {r["bus"]: len(right) - 1 - i for i, r in enumerate(right)}
n = len(rows)
for r in rows:  # 配对连线
    axC.plot([xL, xR], [yL[r["junction"]], yR[r["bus"]]], color=COL[r["stratum"]],
             lw=0.9, alpha=0.75, zorder=1)
# 左侧分层彩色条 + 分层名
i = 0
while i < len(left):
    s = left[i]["stratum"]
    j = i
    while j + 1 < len(left) and left[j + 1]["stratum"] == s:
        j += 1
    ya, yb = yL[left[j]["junction"]], yL[left[i]["junction"]]
    axC.plot([xL - 0.055, xL - 0.055], [ya, yb], color=COL[s], lw=3.0, zorder=2,
             solid_capstyle="butt")
    axC.text(xL - 0.075, (ya + yb) / 2,
             f"{LAB[s]}  (n={sum(1 for r in rows if r['stratum'] == s)})",
             fontsize=8.0, color=COL[s], ha="right", va="center", fontweight="bold")
    i = j + 1
for r in rows:  # 端点与标签 (样式统一, 无特殊标注)
    yl, yr = yL[r["junction"]], yR[r["bus"]]
    axC.scatter([xL], [yl], s=16, facecolor=COL[r["stratum"]], edgecolor="k",
                linewidths=0.45, zorder=3)
    axC.scatter([xR], [yr], s=16, facecolor=COL[r["stratum"]], edgecolor="k",
                linewidths=0.45, zorder=3)
    axC.text(xL - 0.012, yl, r["junction"], fontsize=5.8, ha="right",
             va="center", color="black")
    axC.text(xR + 0.012, yr, f"bus {r['bus']}", fontsize=5.8, ha="left", va="center",
             color="black")
axC.text(xL, n + 1.2, "Water intake junction", fontsize=9.5, ha="center",
         va="bottom", fontweight="bold", color="black")
axC.text(xR, n + 1.2, "Generator bus", fontsize=9.5, ha="center",
         va="bottom", fontweight="bold", color="black")
axC.text(-0.005, 1.01, "(c)", transform=axC.transAxes, fontsize=14, fontweight="bold",
         va="bottom")
axC.set_xlim(-0.02, 1.02)
axC.set_ylim(-2, n + 4)

# ================= legend (分层, 无特殊标注) =================
hand = [Line2D([0], [0], marker="o", color="none", markerfacecolor=COL[s],
               markeredgecolor="k", markersize=6, label=f"{LAB[s]}")
        for s in STRATA]
fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=9.5, frameon=True,
           bbox_to_anchor=(0.5, 0.0),
           title="Depressurization stratum of coupled intake (time from unique-source outage)")

fig.savefig(OUT, **SAVE)
plt.close(fig)
print("saved Fig4 (3-panel, no titles, uniform stratum styling)")
