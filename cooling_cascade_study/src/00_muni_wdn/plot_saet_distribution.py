"""
Fig.12  Network-wide distribution of intake depressurization times.
  (a) histogram (P10/median/P90 representative nodes)
  (b) cumulative failure fraction (CDF, with never-fail plateau)
  (c) spatial map coloured by failure time
Reads results/muni/saet_distribution.json -> figures/Fig12_depressurization_time_distribution.png
校准 v2 (2026-09-02, 用户指令: 同步前序规范 + 画布改 2 行——上行 (a)(b)、下行 (c)
通栏并适当放大):
- 画布 1x3 (14x5.4) -> 2 行 (12.5x12.0, height_ratios=[1, 1.5]): (c) 地图受行高
  限制取 ~7.3x6.0 in (原 4.6x3.8 in, 面积 ~2.5x), 空间细节与标注可读性显著提升;
- 字号统一 12: (a) 代表节点标签 8 号自由文本 -> vline 入图例(免避让); (b) 平台
  注记 8 -> 12; (c) 代表节点标注 7.5 -> 12 加粗+白描边、图例 7 -> 12(新增
  P10/P50/P90 环标条目, 原 7.5 号脚注并入)、色标标签 9 -> 12;
- (c) 布局: 地图 anchor("W") 左置(与上行 (a) 左缘对齐), 色标按地图实际右缘
  显式 add_axes(等高贴边; fig.colorbar(ax=ax3) 会重切格元致地图坍缩, 弃用),
  图例改 figure 级锚定单元格右缘空带——三者零遮挡(v1 初版图例/色标以收缩
  轴框定位压地图 79/7 节点, 已修正);
- (c) 标记放大: 失压节点 9->22, 不失压 7->15, 环标 210->340, 水源 90->170,
  水箱 50->100, 管线 0.4->0.7; J89 (P90) 近图顶, 标注改右下偏移防越界。
口径: B-ST 合成阶跃(t=0, 与图 5/图 6/Q1-Q5 分层定义同一故障模型)。
数据核实 (2026-09-02): 复跑 saet_distribution.py 逐字节一致; 399 节点 289 失压
(72.4%)/110 不失压; 耦合 54 节点 38/16 与 full_coupling_boundary saet 复算一致。
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from matplotlib.collections import LineCollection

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")

COLS = {"fast": COLORS["power"], "median": COLORS["amber"], "slow": COLORS["ok"]}
LAB = {"fast": "Fast (P10)", "median": "Median (P50)", "slow": "Slow (P90)"}
HALO = [pe.withStroke(linewidth=2.4, foreground="white")]


def main():
    with open(os.path.join(RES, "saet_distribution.json")) as f:
        o = json.load(f)
    s = o["stats"]
    dur = o["duration_h"]
    reps = o["representatives"]
    tf = o["tfail_h"]
    finite = np.array([v for v in tf.values() if v is not None])
    never = s["n_never_fail"]

    fig = plt.figure(figsize=(12.5, 12.0))
    gs = GridSpec(2, 2, figure=fig, wspace=0.26, hspace=0.30,
                  height_ratios=[1, 1.5])

    # ---------------- (a) histogram ----------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(finite, bins=24, color=COLORS["muni"], alpha=0.85, edgecolor="white")
    for tag, r in reps.items():
        ax1.axvline(r["t_fail_h"], color=COLS[tag], lw=1.8, ls="--",
                    label="%s: %s, %.2f h" % (LAB[tag], r["node"], r["t_fail_h"]))
    ax1.set_xlabel("Depressurization time (h, from source outage)")
    ax1.set_ylabel("Number of nodes")
    ax1.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    ax1.legend(loc="upper right")

    # ---------------- (b) CDF ----------------
    ax2 = fig.add_subplot(gs[0, 1])
    xs = np.sort(finite)
    total = s["n_junctions"]
    ys = np.arange(1, len(xs) + 1) / total * 100
    ax2.plot(xs, ys, color=COLORS["power"])
    plateau = (total - never) / total * 100
    ax2.axhline(plateau, color=COLORS["mut"], ls=":", lw=1.2)
    ax2.text(dur * 0.98, plateau - 5,
             "%0.0f%% eventually fail\n(%d nodes / %0.0f%% never fail)" % (plateau, never, never / total * 100),
             ha="right", va="top", fontsize=12, color=COLORS["mut"])
    for tag, r in reps.items():
        ax2.axvline(r["t_fail_h"], color=COLS[tag], lw=1.2, ls="--")
    ax2.set_xlabel("Depressurization time (h)")
    ax2.set_ylabel("Cumulative failed nodes (%)")
    ax2.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
    ax2.set_ylim(0, 100)

    # ---------------- (c) spatial map (v2: 通栏放大) ----------------
    ax3 = fig.add_subplot(gs[1, :])
    ax3.grid(False)
    nc = o["coords"]
    segs = [[nc[a], nc[b]] for a, b in o["edges"] if a in nc and b in nc]
    ax3.add_collection(LineCollection(segs, colors="#dddddd", linewidths=0.7, zorder=1))
    xs = [nc[j][0] for j in tf]; ys = [nc[j][1] for j in tf]
    cvals = np.array([tf[j] if tf[j] is not None else np.nan for j in tf], dtype=float)
    fin = ~np.isnan(cvals)
    ax3.scatter(np.array(xs)[~fin], np.array(ys)[~fin], c="#bbbbbb", s=15, zorder=2,
                label="Never fail (>%d h)" % dur)
    sc = ax3.scatter(np.array(xs)[fin], np.array(ys)[fin], c=cvals[fin], cmap="RdYlGn",
                     s=22, zorder=3, vmin=0, vmax=np.nanpercentile(cvals, 95))
    for tag, r in reps.items():
        j = r["node"]
        ax3.scatter([nc[j][0]], [nc[j][1]], marker="o", s=340, edgecolor="black",
                    facecolor="none", linewidths=1.6, zorder=5)
        if tag == "slow":   # J89 近图顶, 标注移右下防越界
            ax3.annotate("%s\n%s" % (LAB[tag], j), (nc[j][0], nc[j][1]),
                         textcoords="offset points", xytext=(9, -10), fontsize=12,
                         color="black", fontweight="bold", path_effects=HALO,
                         va="top", zorder=6)
        else:
            ax3.annotate("%s\n%s" % (LAB[tag], j), (nc[j][0], nc[j][1]),
                         textcoords="offset points", xytext=(7, 7), fontsize=12,
                         color="black", fontweight="bold", path_effects=HALO, zorder=6)
    rc = o["reservoir_coord"]
    ax3.scatter([rc[0]], [rc[1]], marker="s", s=170, c="#1a1a1a", zorder=6,
                label="Source R1")
    ax3.scatter([v[0] for v in o["tanks"].values()], [v[1] for v in o["tanks"].values()],
                marker="^", s=100, edgecolor="k", facecolor="none", linewidths=0.9,
                zorder=4, label="Tanks")
    ax3.scatter([], [], marker="o", s=340, edgecolor="black", facecolor="none",
                linewidths=1.6, label="P10/P50/P90 representative")
    ax3.set_xticks([]); ax3.set_yticks([]); ax3.set_aspect("equal")
    ax3.set_title("(c)", fontsize=12, fontweight="bold", loc="left")
    # v2: 收紧默认边距(0.125/0.9/0.88/0.11)让通栏地图尽量大
    gs.update(left=0.075, right=0.985, bottom=0.06, top=0.965,
              wspace=0.22, hspace=0.30)
    # v2: 地图左缘对齐上行 (a) 轴盒左缘(锚点取 (a) 在格元内的水平分数)
    fig.canvas.draw()
    ren0 = fig.canvas.get_renderer()
    cell = ax3.get_subplotspec().get_position(fig)
    a0 = ax1.get_window_extent(ren0)
    m0 = ax3.get_window_extent(ren0)
    cw, bw = cell.width * fig.bbox.width, m0.width
    a_frac = min(max((a0.x0 - cell.x0 * fig.bbox.width) / max(cw - bw, 1), 0.0), 0.5)
    ax3.set_anchor((a_frac, 0.5))
    # v2: 色标显式定位——fig.colorbar(ax=ax3) 会在 subplotspec 轴上重切格元,
    # 与 aspect 收缩叠加后把地图挤成 ~1.9 in 窄条; 故按地图实际右缘 add_axes。
    fig.canvas.draw()
    mb = ax3.get_window_extent(fig.canvas.get_renderer())
    fb = fig.bbox
    cax = fig.add_axes([(mb.x1 + 0.10 * 72) / fb.width, mb.y0 / fb.height,
                        0.16 * 72 / fb.width, mb.height / fb.height])
    cbar = fig.colorbar(sc, cax=cax)
    cbar.set_label("Failure time (h)", fontsize=12)
    cbar.ax.tick_params(labelsize=12)
    # v2: 图例 figure 级, 锚定 (c) 单元格右缘的空带 (地图受行高限制仅占左半)
    hC, lC = ax3.get_legend_handles_labels()
    fig.legend(hC, lC, loc="center right", frameon=True,
               bbox_to_anchor=(cell.x1, (cell.y0 + cell.y1) / 2))

    fig.savefig(os.path.join(FIG, "Fig12_depressurization_time_distribution.png"), **SAVE)
    print("saved Fig12")


if __name__ == "__main__":
    main()
