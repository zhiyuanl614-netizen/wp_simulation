"""
Fig.5  Designated-coupling municipal boundary as a heatmap: rows = 6 intake nodes
(sorted by first-failure time ascending; every row labelled with its junction
name and coupled bus), columns = time (0-72 h), color = intake-node pressure
(RdYlBu as in Fig.6: failed/low head = red). Open circles mark each node's
first crossing of the service threshold (v3: 20 m) (the depressurization front).
Source outage = t=0 step (B-ST synthetic caliber -- same fault model as Fig.6;
the B-RT ramp protocol t=6h+3h-linear remains the downstream input caliber only).
Reads results/muni/full_coupling_boundary.json + coupling_map.json
-> figures/Fig5_muni_staggered_depressurization.png
Style: Fig.1-4 conventions (no titles, black annotations).

v4 (2026-09-15, 用户指令"取消 rows ordered Q1-Q5"):
  - 耦合集合由 54 对(分层比例抽样) 改为研究者指定 6 对 -> 6 行;
  - **取消 Q1–Q5 分层**: 删除分层白线、右侧 Q1(n=..)–Q5(n=..) 色键与
    "rows ordered Q1-Q5" 脚注; 行序改为纯按首破阈值时刻升序;
  - 行数由 54 降至 6 -> y 轴行标签由 6.5 号(物理不可分)恢复为 12 号统一字号,
    标签格式 "J102  (bus89)" 同时给出取水节点与耦合母线;
  - 画布按 6 行重新收高 (11.5x9.6 -> 11.5x4.6), 避免行高过大失真;
  - 增加失压时刻文本标注 (每行 ○ 右侧标 t_fail), 弥补分层信息取消后的时序可读性。
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle  # noqa
from figstyle import SAVE
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

HALO = [pe.withStroke(linewidth=2.4, foreground="white")]

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "muni")
FIG = os.path.join(HERE, "..", "..", "figures")


def main():
    fb = json.load(open(os.path.join(RES, "full_coupling_boundary.json")))
    cm = json.load(open(os.path.join(RES, "coupling_map.json")))
    assert str(cm.get("version","")).startswith(("v2","v3")), "Fig5 需 coupling_map v2/v3 (指定 6 对, 无分层)"
    nodelab = {int(r["bus"]): r["junction"] for r in cm["map"]}
    pg = {int(r["bus"]): r["Pg_MW"] for r in cm["map"]}
    thr = fb["boundary_protocol"]["H_muni_min_m"]
    tf = 0.0  # B-ST 合成阶跃口径——故障即仿真零点, 与 Fig6 一致
    plants = fb["plants"]

    # rows: 纯按首破阈值时刻升序 (never-fail 置末); v4 取消 Q1-Q5 分层
    order = [(int(b), plants[b]) for b in plants]
    order.sort(key=lambda bp: (bp[1]["t_fail_saet_h"] is None,
                               bp[1]["t_fail_saet_h"] or 0.0, bp[0]))
    n = len(order)
    H = np.array([p["pressure_saet_m"] for _, p in order])

    fig, ax = plt.subplots(figsize=(11.5, 4.6))
    im = ax.imshow(H, aspect="auto", cmap="RdYlBu", vmin=0, vmax=80,
                   extent=[0, 72, n, 0], interpolation="nearest")
    ax.grid(False)
    # 行间细分隔线 (仅视觉分行, 不含分层语义)
    for i in range(1, n):
        ax.hlines(i, 0, 72, color="white", lw=0.8, zorder=3, alpha=0.55)

    # depressurization front: first crossing of the 28 m threshold per row
    for i, (b, p) in enumerate(order):
        if p["t_fail_saet_h"] is not None:
            t = p["t_fail_saet_h"]
            ax.plot(t, i + 0.5, "o", ms=6.0, mfc="white", mec="black", mew=1.2,
                    zorder=4, clip_on=False)
            ax.text(t + 1.0, i + 0.5, "t_fail = %.2f h" % t, va="center",
                    ha="left", fontsize=12, color="black",
                    path_effects=HALO, zorder=5)

    # v4-fix: 注记移至右上(失效后的均一深红区, 无数据标注), 避免与首行 t_fail 重叠;
    # 深底故用白字 + 黑描边
    HALO_D = [pe.withStroke(linewidth=2.4, foreground="black")]
    ax.text(71.2, 0.16, "Source outage at t = 0 h",
            fontsize=12, color="white", path_effects=HALO_D, zorder=5, va="top",
            ha="right")

    # every junction name + coupled bus on the y axis (12 pt, v4 恢复统一字号)
    ax.set_yticks(np.arange(n) + 0.5)
    ax.set_yticklabels(["%s  (bus%d, %.0f MW)" % (nodelab[b], b, pg[b])
                        for b, _ in order], fontsize=12, color="black")
    ax.tick_params(axis="y", length=3, pad=4)

    ax.set_xlim(0, 72)
    ax.set_xticks([0, 12, 24, 36, 48, 60, 72])
    ax.set_ylim(n, 0)
    ax.set_xlabel("Time (h)")

    cbar = fig.colorbar(im, ax=ax, fraction=0.016, pad=0.155)
    cbar.set_label("Intake-node pressure (m)", fontsize=12)
    cbar.ax.axhline(thr, color="black", ls="--", lw=1.0)
    cbar.ax.text(-0.9, thr, "%.0f m" % thr, va="center", ha="right", fontsize=12,
                 color="black", transform=cbar.ax.get_yaxis_transform())

    fig.tight_layout()
    fig.text(0.02, -0.035, "rows ordered by first-fail time (ascending);   "
             "o = first crossing < %.0f m;   all 6 intakes verified as real "
             "supply nodes (base demand > 0)" % thr, fontsize=12, color="black",
             va="top")
    fig.savefig(os.path.join(FIG, "Fig5_muni_staggered_depressurization.png"), **SAVE)
    plt.close(fig)
    print("saved Fig5 (heatmap, %d labelled rows, ordered by first-fail time, "
          "no Q1-Q5 strata)" % n)


if __name__ == "__main__":
    main()
