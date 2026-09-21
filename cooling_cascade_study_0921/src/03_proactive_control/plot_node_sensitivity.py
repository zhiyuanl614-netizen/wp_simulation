"""
Fig.13  Intake-node position sensitivity (v2, 6-unit coupled set).
  (a) municipal depressurization-time distribution + percentile representatives
      + the 6 coupled intake junctions (B-ST t_fail) as a rug
  (b) layout (CO vs DISP) x strategy (PA/SP/DP) **peak** deficit (MW)
  (c) layout x strategy **energy** deficit (MWh)
Reads results/proactive_control/p6_node_sensitivity.json
    + results/muni/saet_distribution.json + results/muni/coupling_map.json
 -> figures/Fig13_intake_node_sensitivity.png

v2 重构说明 (2026-09-15, 耦合层改为 6 对 rank↔rank 指定配对后):
- 面板由 2 → 3: v2 中 CO(同源同时, τ=0) 与 DISP(指定布置, B-ST 真实错峰
  0/0.5/2.5/2.5/5.75/7.75 h) 的**峰值缺额完全相同**(334.88 MW), 差异只体现在
  **能量缺额**(59.61 → 43.73 MWh, -26.6%)。原 v1 双面板只画峰值(343→315 MW),
  在 v2 会退化为两组等高柱 → 误导。故 (b) 峰值 + (c) 能量并列, 机理写入图注:
  6 个取水点同处 DMA1 → 错峰窗口 (≤7.75 h) 远大于冷却危机窗口 (1.5–3.1 h),
  但首危机 (bus89, τ=0) 与次危机 (bus80, +0.5 h) 仍重叠, 峰值由最大单机
  (607 MW) 主导, 故削峰 ≈0%, 仅削能量。
- (a) 新增耦合取水点 rug: 6 点全部落在分布左尾 (1.25–9.0 h, P10=3.75 h),
  即"集中取水于同一分区 = 共因失效时间高度聚集"的直观证据。
- 数据核实: node_sensitivity.py v2 (2 个联合 LP, CO horizon 300 min /
  DISP horizon 780 min, ~18 min) → CO PA 334.88/59.61, DISP PA 334.88/43.73,
  SP/DP 双布置均 0/0 (过载松弛 36.76 MW 同 run_p6)。
校准沿用 v1 (2026-09-02 用户指令): 字号统一 12、序号加粗左上、图例定点不压主图、
y 轴顶部 18% 余量防数值标签裁切。
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpe

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
MUNI_RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")

COLS = {"fast": COLORS["power"], "median": COLORS["amber"], "slow": COLORS["ok"]}
LAB = {"fast": "Fast (P10)", "median": "Median (P50)", "slow": "Slow (P90)"}
MODES = ["PA", "SP", "DP"]
MODE_LAB = ["Passive PA", "Static SP", "Dynamic DP"]
LAYOUT_LAB = {"CO": "CO (co-located, $\\tau$=0)",
              "DISP": "DISP (designated intakes)"}


def main():
    with open(os.path.join(RES, "p6_node_sensitivity.json")) as f:
        o = json.load(f)
    with open(os.path.join(MUNI_RES, "saet_distribution.json")) as f:
        dist = json.load(f)
    with open(os.path.join(MUNI_RES, "coupling_map.json")) as f:
        cmap = json.load(f)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 5.0))

    # ---------------- (a) distribution + coupled intakes ----------------
    tf = [v for v in dist["tfail_h"].values() if v is not None]
    ax1.hist(tf, bins=24, color=COLORS["muni"], alpha=0.85, edgecolor="white")
    for tag, r in dist["representatives"].items():
        ax1.axvline(r["t_fail_h"], color=COLS[tag], lw=1.8, ls="--",
                    label="%s: %s, %.2f h" % (LAB[tag], r["node"], r["t_fail_h"]))

    # 6 个耦合取水节点 (B-ST 口径 t_fail): 柱顶之上的 rug + 旋转 90° 交错标签
    # (6 点全落 1.25-9.0 h, 水平间距 << 标签宽度 → 竖排标签是唯一不碰撞的排法)
    rows = sorted(cmap["map"], key=lambda r: r["rank"])
    nodes = [(r["junction"], r["t_fail_h"]) for r in rows]
    ymax = ax1.get_ylim()[1]
    ax1.set_ylim(0, ymax * 1.52)
    rug_y = ymax * 1.06
    ax1.plot([n[1] for n in nodes], [rug_y] * len(nodes), "|", ms=15, mew=2.4,
             color=COLORS["power"], label="Coupled intakes (n=6, B-ST)")
    lbl = {}                                   # 同时刻合并标注 (J198/J5 均 3.75 h)
    for jn, t in nodes:
        lbl.setdefault(round(t, 3), []).append(jn)
    for i, (t, jns) in enumerate(sorted(lbl.items())):
        ax1.plot([t, t], [0, rug_y], ls=":", lw=0.9, color=COLORS["power"], alpha=0.55,
                 zorder=1)
        ax1.annotate(", ".join(jns), xy=(t, rug_y),
                     xytext=(t, rug_y + ymax * (0.06 + 0.20 * (i % 2))),
                     rotation=90, ha="center", va="bottom", fontsize=11,
                     color=COLORS["power"], fontweight="bold", zorder=5,
                     path_effects=[mpe.withStroke(linewidth=2.6,
                                                           foreground="white")])
    ax1.set_xlabel("Intake depressurization time (h, from outage)")
    ax1.set_ylabel("Number of nodes")
    ax1.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    ax1.legend(loc="upper right", fontsize=12)

    # ---------------- (b) peak / (c) energy ----------------
    for ax, key, ylab, ttl in [(ax2, "max_deficit_MW", "Peak power deficit (MW)", "(b)"),
                               (ax3, "energy_deficit_MWh", "Energy deficit (MWh)", "(c)")]:
        vals = {}
        for L in ("CO", "DISP"):
            vals[L] = [o["layouts"][L]["results"][m][key] for m in MODES]
        x = np.arange(len(MODES)); w = 0.36
        bars = []
        for sgn, L, c in [(-1, "CO", COLORS["power"]), (1, "DISP", COLORS["muni"])]:
            b = ax.bar(x + sgn * w / 2, vals[L], w, label=LAYOUT_LAB[L], color=c)
            bars.append(b)
        for b in bars:
            for bar in b:
                h = bar.get_height()
                ax.annotate("%.1f" % h,
                            (bar.get_x() + bar.get_width() / 2, h),
                            textcoords="offset points", xytext=(0, 3),
                            ha="center", fontsize=12, fontweight="bold")
        ax.set_xticks(x); ax.set_xticklabels(MODE_LAB)
        ax.set_ylabel(ylab)
        ax.set_ylim(0, max(max(vals["CO"]), max(vals["DISP"])) * 1.18)
        ax.set_title(ttl, fontsize=12, fontweight="bold", loc="left")
        ax.legend(loc="upper right", fontsize=12)

    fig.tight_layout()
    out = os.path.join(FIG, "Fig13_intake_node_sensitivity.png")
    fig.savefig(out, **SAVE)
    print("saved", out)


if __name__ == "__main__":
    main()
