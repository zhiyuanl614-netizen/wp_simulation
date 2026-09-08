"""
Fig.6  Spatio-temporal pressure collapse under unique-source outage.
  top:  (a) network pressure stats vs time (P10-P90 band / mean / median + 28 m threshold)
        (b) failed-node fraction vs time (half-network marker + t=0 outage note)
  bottom: (c1)-(c4) 2x2 spatial snapshots (nodes coloured by pressure, RdYlBu 0-80 m
        -- same scale as Fig.5; grey pipes, black square = source R1, green triangles = tanks)
Reads results/muni/network_outage.json -> figures/Fig6_network_outage_spatiotemporal.png

校准 v2 (2026-09-02, 用户指令: 按前序图规范校准 + (c1)-(c4) 改 2x2):
- (c1)-(c4) 由 1x4 改 2x2: D-town 地图近正方形, 1x4 条带下每图仅 ~2.4 in 宽且垂向 ~43%
  留白; 2x2 后快照线性放大约 1.35x(面积 ~1.8x), 空间失效传播模式(源邻域->外围)可辨;
  时间序保持 Z 字阅读, 每图带显式 t= 标签(白色描边保证彩色底可读)。
- 全图 12 号统一 (Arial/Liberation Sans): 注释/快照标签/cbar 标签/图例; 无 6.5 类物理约束。
- 图例规范: (a) 统计三_entries 图例 12 号单行置右上(数据带之上, ylim 抬至 88 留隙);
  R1/Tanks 标记图例移至图底居中(12 号单行)——不覆盖任何快照内容, 全图图例字号统一。
- 阶跃停供 t=0: 原 (a)(b) 红色点线竖线退化贴 y 轴(视觉噪声) -> 删除竖线, 改 (b) 左上
  文字 "Source outage at t = 0 h" + 图注交代; 阈值线保留 (a) 右端标注(12 号)。
- 半网失效时刻 %.0f -> %.1f (12.5 h, 原 13 h 系四舍五入失真)。
校准 v4 (2026-09-02, 用户指令): (c) 画布与 (a)(b) 同列同宽(色标改专用轴置右缘外, 不再
挤占快照格子); (c1)-(c4) 序号/标签锚定收缩前格子边缘, 与 (a)(b) 文字框对齐; R1/Tanks
图例由图底居中移至 (c1) 右上方。t=0 语义: 本场景 t_fault=0(阶跃), t=0 快照为停供开启
时刻的初始状态(非 Fig5 边界协议 6 h 线性压降口径, 两者为不同烈度设计点)。
校准 v5 (2026-09-02, 用户指令): (c) 标签只保留 "t=n h"; 地图 set_anchor("W") 锚定格子
西缘——(c) 图内容左缘与 (a) 图左缘对齐(原 aspect 居中致地图右移 ~0.8 in)。
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle  # noqa
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")

HALO = [pe.withStroke(linewidth=2.4, foreground="white")]


def main():
    with open(os.path.join(RES, "network_outage.json")) as f:
        o = json.load(f)
    s = o["stats"]
    t = np.array(s["t_h"])
    tf = o["t_fault_h"]
    thr = o["H_muni_min_m"]
    nc = o["node_coords"]

    fig = plt.figure(figsize=(13, 13.6))
    gs = GridSpec(3, 2, figure=fig, height_ratios=[0.78, 1.0, 1.0],
                  hspace=0.30, wspace=0.16)

    # (a) pressure stats vs time
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.fill_between(t, s["p10"], s["p90"], color="#9cc3e6", alpha=0.35, label="P10\u2013P90 band")
    ax1.plot(t, s["mean"], color=COLORS["muni"], label="Network mean")
    ax1.plot(t, s["p50"], color="#123a5c", lw=1.4, ls="--", label="Median")
    ax1.axhline(thr, color="k", ls=":", lw=1.1)
    # 校准v2: 阈值线右端标注(12 号, 白描边), 取代图内散置文字
    ax1.text(t[-1], thr + 2.0, f"Threshold {thr:.0f} m", ha="right", va="bottom",
             fontsize=12, color="black", path_effects=HALO, zorder=5)
    ax1.set_ylim(0, 95)  # 校准v2: 抬高上限, 为右上单行图例让出净空(p90 峰 78.1 m)
    ax1.set_xlabel("Time (h)")
    ax1.set_ylabel("Node pressure head (m)")
    ax1.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    # 校准v2: 3 条目单行 12 号, 右上(p90 曲线之上)
    ax1.legend(fontsize=12, loc="upper right", ncol=3, columnspacing=1.0,
               handletextpad=0.4, handlelength=1.4, frameon=True)

    # (b) failed-node fraction
    ax2 = fig.add_subplot(gs[0, 1])
    fb = np.array(s["frac_below"]) * 100
    ax2.plot(t, fb, color=COLORS["power"])
    ax2.fill_between(t, 0, fb, color=COLORS["power"], alpha=0.15)
    # 校准v2: 删除退化贴轴的 t=0 红点竖线, 改左上文字
    ax2.text(0.03, 0.94, "Source outage at t = 0 h", transform=ax2.transAxes,
             fontsize=12, color="black", va="top")
    half = np.where(np.array(s["frac_below"]) >= 0.5)[0]
    if len(half):
        th50 = t[half[0]]
        ax2.axhline(50, color=COLORS["mut"], ls="--", lw=0.9)
        ax2.plot([th50], [50], "o", color="#7b241c", ms=8)
        # 校准v2: %.1f (12.5 h, 非 13), 12 号; 置曲线下方低谷区(t 14-42 h 段 fb>=37%,
        # 文字顶 29% 净空), 箭头指向标记点
        ax2.annotate(f"Half of network fails\nt={th50:.1f} h (+{th50 - tf:.1f} h)",
                     (th50, 50), textcoords="axes fraction", xytext=(0.20, 0.06),
                     ha="left", va="bottom", fontsize=12, color="black",
                     arrowprops=dict(arrowstyle="->", color="black"))
    ax2.set_xlabel("Time (h)")
    ax2.set_ylabel("Failed nodes (%)")
    ax2.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
    ax2.set_ylim(0, 100)

    # bottom: 2x2 spatial snapshots (c1)-(c4)
    # 校准v4(用户指令): (c) 画布与 (a)(b) 同列同宽——色标不再挤占快照格子(改专用轴置右缘外),
    # 序号/标签/图例锚定 aspect 收缩前的格子边缘, 与 (a)(b) 文字框对齐
    segs = [[nc[a], nc[b]] for a, b in o["edges"] if a in nc and b in nc]
    res_xy = o["reservoir_coord"]; tanks = o["tanks"]
    snap_axes, CELL = [], {}
    for k, h in enumerate(o["snap_hours"]):
        ax = fig.add_subplot(gs[1 + k // 2, k % 2])
        CELL[k] = ax.get_position().frozen()   # 收缩前格子(与 (a)(b) 网格同列)
        snap_axes.append(ax)
        ax.grid(False)
        ax.add_collection(LineCollection(segs, colors="#cccccc", linewidths=0.4, zorder=1))
        snap = o["snapshots"][str(h)]
        xs = [nc[j][0] for j in snap]; ys = [nc[j][1] for j in snap]
        cs = [snap[j] for j in snap]
        sc = ax.scatter(xs, ys, c=cs, cmap="RdYlBu", vmin=0, vmax=80, s=8, zorder=2)
        ax.scatter([res_xy[0]], [res_xy[1]], marker="s", s=80, c="#1a1a1a", zorder=4)
        ax.scatter([v[0] for v in tanks.values()], [v[1] for v in tanks.values()],
                   marker="^", s=50, edgecolor="k", facecolor=COLORS["ok"],
                   linewidths=0.6, zorder=3)
        # 校准v4: 序号锚定格子左缘(与 (a) 序号同列), 标签右对齐格子右缘(与 (b) 右缘平齐)
        # 校准v5(用户指令): 标签只保留时间(去掉 outage start/+X h/failed %——信息由 (b) 曲线与图注承载)
        ax.text(CELL[k].x0, CELL[k].y1 + 0.006, "(c%d)" % (k + 1),
                transform=fig.transFigure, fontsize=12, fontweight="bold", va="bottom")
        ax.text(CELL[k].x1, CELL[k].y1 + 0.006, "t=%d h" % h,
                transform=fig.transFigure, fontsize=12, color="black",
                ha="right", va="bottom")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
        ax.set_anchor("W")  # 校准v5(用户指令): 地图锚定格子西缘 -> (c) 内容左缘与 (a) 对齐

    # 校准v4: 色标专用轴置快照块右缘外(垂跨两行), 快照格子保持与 (a)(b) 同宽
    cax = fig.add_axes([0.915, CELL[2].y0, 0.016, CELL[0].y1 - CELL[2].y0])
    cbar = fig.colorbar(sc, cax=cax)
    cbar.set_label("Node pressure head (m)", fontsize=12)

    # 校准v4(用户指令): R1/Tanks 图例置于 (c1) 右上方(格子右上角, 大部落在地图右侧白带)
    handles = [Line2D([0], [0], marker="s", color="none", markerfacecolor="#1a1a1a",
                      markersize=8, label="Source R1"),
               Line2D([0], [0], marker="^", color="none", markerfacecolor=COLORS["ok"],
                      markeredgecolor="k", markersize=8, label="Tanks")]
    snap_axes[0].legend(handles=handles, fontsize=12, loc="upper right",
                        bbox_to_anchor=(CELL[0].x1, CELL[0].y1),
                        bbox_transform=fig.transFigure, ncol=1, frameon=True,
                        columnspacing=1.0, handletextpad=0.5, handlelength=1.4,
                        labelspacing=0.4)

    fig.savefig(os.path.join(FIG, "Fig6_network_outage_spatiotemporal.png"), **SAVE)
    print("saved Fig6 (2x2 snapshots, unified 12pt)")
    plt.close(fig)


if __name__ == "__main__":
    main()
