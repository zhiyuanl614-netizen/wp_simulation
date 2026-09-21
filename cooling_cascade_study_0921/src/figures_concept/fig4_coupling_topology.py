"""
Fig.4 (§3.1)  Water-power coupling topology — designated-coupling edition (3 panels)
====================================================================================
无总标题/子标题, 仅保留面板序号 (a)(b)(c)。
  (a) D-town 水网 (真实坐标, 归一化): **6 个**指定耦合取水节点【统一语义色高亮 + 标签】;
  (b) IEEE-118 单线图 (用户提供的清晰矢量版): **6 台**耦合发电机【统一色圆环锚定 G 圆
      (assets/...coords.json 的 genG) + 黑色标签】;
  (c) **6 对**耦合配对图 (bipartite matching): 左=取水节点(按首破 28 m 时刻升序),
      右=发电机母线(与左侧耦合 Junction 同行对齐, 连线水平);
      不展示中间冷却水场站。
输出: figures/Fig4_coupling_topology.png (300 dpi)

v6 (2026-09-15, 用户指令"取消 Q1–Q5 分层 + 耦合缩减为 6 对"):
  - 耦合集合由 54 对(分层比例抽样) 改为研究者指定 6 对 (coupling_map v2);
  - **取消 Q1–Q5 分层**: 删除 STRATA/COL/LAB 分层色板、(c) 左侧分层彩条与
    "Qk (n=count)" 标签、分层图例 —— 全部耦合元素改用单一语义色 COLORS["cool"];
  - 排序键由 (stratum, t_fail, name) 改为 rank (coupling_map 已按 t_fail 升序
    × Pg 降序 确定性编号);
  - 元素数由 54 降至 6 -> 图内标签字号由 5.2–9.5 提升至 9–12 (可读性),
    (c) 每行加标 t_fail / Pg, adjustText 避让改为固定偏移(元素稀疏无需避让);
  - 画布按 6 行收高 (15.2x12.9 -> 15.2x9.2)。
校准规范 v2-v5 (2026-09-02, 沿用): 序号 (a)(b)(c) 加粗 12 号; (a) 序号与 (c) 同列
对齐(figure 坐标, 地图位置不动); (a)(b) 图例统一 8 号、单列、带框; (c) 右列 bus 与
左侧耦合 Junction 同行对齐(连线水平, 无交叉)。
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

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "..", "..", "data", "DTOWN.inp")
ONELINE = os.path.join(HERE, "assets", "IEEE118_oneline.png")
COORDS = os.path.join(HERE, "assets", "IEEE118_bus_label_coords.json")
CMAP = os.path.join(HERE, "..", "..", "results", "muni", "coupling_map.json")
OUT = os.path.join(HERE, "..", "..", "figures", "Fig4_coupling_topology.png")

# v6: 取消 Q1–Q5 分层 —— 单一语义色
COUP = COLORS["cool"]
def _pump_glyph(ax, xs, ys, s=1.0, z=4):
    """EPANET 泵符号: 白底圆 + 内三角(流向)。xs/ys 为已变换坐标列表。"""
    ax.scatter(xs, ys, s=120 * s, facecolor="white", edgecolor="#333333",
               linewidths=1.1, zorder=z)
    ax.scatter(xs, ys, s=45 * s, marker="^", facecolor="#5b6b7a",
               edgecolor="#333333", linewidths=0.6, zorder=z + 1)

HALO = [pe.withStroke(linewidth=1.6, foreground="white")]

_cm = json.load(open(CMAP))
assert str(_cm.get("version","")).startswith(("v2","v3")), "Fig4 需 coupling_map v2/v3 (指定 6 对, 无分层)"
rows = sorted(_cm["map"], key=lambda r: r["rank"])
coords = json.load(open(COORDS))

# ================= figure layout (放大子图, 仅留序号) =================
fig = plt.figure(figsize=(15.2, 9.2))
gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 0.75], hspace=0.10, wspace=0.05)
axA = fig.add_subplot(gs[0, 0])
axB = fig.add_subplot(gs[0, 1])
axC = fig.add_subplot(gs[1, :])
CELL_A = axA.get_position().frozen()
CELL_C = axC.get_position().frozen()
XC_LETTER = CELL_C.x0 - 0.005 * CELL_C.width        # 与 (c) 序号同列(figure 分数)
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
            marker="^", s=26, facecolor="#5b6b7a", edgecolor="#5b6b7a",
            linewidths=0.8, zorder=3)
# v3-fix(用户指令): 拓扑图补绘水泵 P1/P2 (R→J20 并联, 中点重合→垂直微偏移)
_pm = []
for _i, _pn in enumerate(wn.pump_name_list):
    _lk = wn.get_link(_pn)
    _a = nc[_lk.start_node_name]; _b = nc[_lk.end_node_name]
    _mx, _my = 0.5 * (_a[0] + _b[0]), 0.5 * (_a[1] + _b[1])
    _pm.append((NX(_mx), NY(_my) + (0.022 if _i else -0.022)))
_pump_glyph(axA, [q[0] for q in _pm], [q[1] for q in _pm], s=0.8, z=4)
if len(wn.pump_name_list) <= 2:
    axA.annotate("P1/P2", (_pm[0][0] + 0.02, _pm[0][1] - 0.02), fontsize=8.5,
                 color="#333333", fontweight="bold", path_effects=HALO, zorder=7)
axA.scatter([NX(nc["R1"][0])], [NY(nc["R1"][1])], marker="s", s=70, c="#1a1a1a", zorder=4)
# v6-fix: 6 节点在 DMA1 内成两簇(底 4 簇 + 顶 2), 标签按逐节点手工偏移避让
OFF = {   # junction: (dx, dy, ha, va)  —— 归一化地图坐标
    "J5":   (0.020, 0.055, "left",  "bottom"),
    "J97":  (0.020, 0.000, "left",  "center"),
    "J177": (0.020, -0.055, "left", "top"),
    "J102": (-0.020, 0.000, "right", "center"),
    "J198": (0.020, 0.000, "left",  "center"),
    "J217": (-0.020, 0.000, "right", "center"),
}
for r in rows:                       # v6: 6 个耦合节点, 统一色 + 手工偏移标签
    x, y = NX(nc[r["junction"]][0]), NY(nc[r["junction"]][1])
    dx, dy, ha, va = OFF[r["junction"]]
    axA.scatter([x], [y], s=95, facecolor=COUP, edgecolor="k", linewidths=0.9, zorder=5)
    axA.text(x + dx, y + dy, "%s\nbus%d" % (r["junction"], r["bus"]),
             fontsize=9, color="black", path_effects=HALO, zorder=7,
             ha=ha, va=va)
axA.text(XC_LETTER, CELL_A.y1 + 0.02 * CELL_A.height, "(a)", transform=fig.transFigure,
         fontsize=12, fontweight="bold", va="bottom")
axA.set_xlim(-0.03, 1.03)
axA.set_ylim(-0.04, 1.04)
axA.set_aspect("equal")
legA = [Line2D([0], [0], marker="o", color="none", markerfacecolor="#c4ccd3",
               markersize=3.5, label="Junction node"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COUP,
               markeredgecolor="black", markersize=7,
               label="Coupled intake (n=%d)" % len(rows)),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
               markeredgecolor="#333333", markersize=9, label="Pumps"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#5b6b7a",
               markeredgecolor="#5b6b7a", markersize=6, label="Tank"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#1a1a1a",
               markersize=6, label="Water source")]
axA.legend(handles=legA, fontsize=8, loc="lower right",
           bbox_to_anchor=(-0.008, -0.028), bbox_transform=axA.transData, ncol=1,
           frameon=True, columnspacing=1.0, handletextpad=0.5, handlelength=1.6,
           labelspacing=0.4)

# ================= (b) IEEE-118 one-line + highlights =================
img = mpimg.imread(ONELINE)
axB.imshow(img)
sc = img.shape[1] / coords["page_pt"][0]          # PDF pt -> pixel
for r in rows:                  # v6: 6 台耦合发电机, 统一色圆环
    gx, gy = coords["genG"].get(str(r["bus"]), coords["bus"][str(r["bus"])])
    px, py = gx * sc, gy * sc
    axB.scatter([px], [py], s=320, facecolor="none", edgecolor=COUP,
                linewidths=2.4, zorder=5)
    axB.text(px + 0.004 * img.shape[1], py, "bus%d" % r["bus"], fontsize=9,
             fontweight="bold", color="black", path_effects=HALO, zorder=6,
             va="center", ha="left")
axB.text(-0.01, 1.02, "(b)", transform=axB.transAxes, fontsize=12, fontweight="bold",
         va="bottom")
legB = [Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
               markeredgecolor=COUP, markeredgewidth=2.0, markersize=9,
               label="Coupled generator (n=%d)" % len(rows)),
        Line2D([0], [0], color="black", lw=3.0, label="Bus")]
axB.legend(handles=legB, fontsize=8, loc="lower left", ncol=1, frameon=True,
           columnspacing=1.0, handletextpad=0.5, borderaxespad=0.4,
           handlelength=1.6, labelspacing=0.4)

# ================= (c) 6-pair matching diagram =================
xL, xR = 0.30, 0.70
left = rows                                   # 已按 rank (= t_fail 升序) 排列
right = list(left)                            # 右列与左侧耦合 Junction 同行对齐
n = len(rows)
yL = {r["junction"]: n - 1 - i for i, r in enumerate(left)}
yR = {r["bus"]: n - 1 - i for i, r in enumerate(right)}
for r in rows:                                # 配对连线 (统一色)
    axC.plot([xL, xR], [yL[r["junction"]], yR[r["bus"]]], color=COUP,
             lw=1.6, alpha=0.85, zorder=1)
# v6-fix: 取消左侧分层彩条与 "Qk (n=..)" 标签; 集合规模并入列头, 不再占用左缘
for r in rows:                                # 端点与标签
    yl, yr = yL[r["junction"]], yR[r["bus"]]
    axC.scatter([xL], [yl], s=70, facecolor=COUP, edgecolor="k", linewidths=0.7,
                zorder=3)
    axC.scatter([xR], [yr], s=70, facecolor=COUP, edgecolor="k", linewidths=0.7,
                zorder=3)
    axC.text(xL - 0.012, yl, "%s   (t_fail %.2f h)" % (r["junction"], r["t_fail_h"]),
             fontsize=11, ha="right", va="center", color="black")
    axC.text(xR + 0.012, yr, "bus %d   (%.0f / %.0f MW)"
             % (r["bus"], r["Pg_MW"], r["Pmax_MW"]),
             fontsize=11, ha="left", va="center", color="black")
axC.text(xL, n + 0.55, "Water intake junction  (coupled set, n=%d)" % n,
         fontsize=12, ha="center", va="bottom", fontweight="bold", color="black")
axC.text(xR, n + 0.55, "Generator bus", fontsize=12, ha="center",
         va="bottom", fontweight="bold", color="black")
axC.text(-0.005, 1.03, "(c)", transform=axC.transAxes, fontsize=12, fontweight="bold",
         va="bottom")
axC.set_xlim(-0.02, 1.02)
axC.set_ylim(-1.2, n + 1.6)

fig.savefig(OUT, **SAVE)
plt.close(fig)
print("saved Fig4 (3-panel, %d designated pairs, no Q1-Q5 strata, uniform color)"
      % n)
