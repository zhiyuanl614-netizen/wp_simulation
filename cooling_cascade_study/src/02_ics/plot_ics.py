"""
Fig.9  Early-warning comparison (WARN vs NOWARN) —— 有无早期预警对比
====================================================================
核心结果图（创新点 2）: 市政水源中断下, 有/无早期预警两情形对比。
Detection signal = municipal supply pressure; impact = power deficit (MW)
/ energy deficit (MWh), 对齐参照文献的影响量化口径。
(a) municipal head & detection   (b) basin level
(c) back-pressure                (d) power deficit
Reads results/ics/* -> figures/Fig9_early_warning_comparison.png

校准规范 v2 (2026-09-02): Arial 12 全图统一（figstyle 全局）; 面板序号
(a)–(d) 加粗 12 号左上, 无描述性标题; 图例 12 号、精简、面板内定点放置
（矢量级验证零覆盖）; 阈值参考线作为图例条目, 图例定点放置并经矢量级零覆盖验证。
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "..", "results", "ics")
FIG = os.path.join(HERE, "..", "..", "figures")

CASES = {"WARN": "With early warning", "NOWARN": "No warning (passive)"}
COL = {"WARN": COLORS["muni"], "NOWARN": COLORS["power"]}

LEG_KW = dict(frameon=False, columnspacing=1.2, handletextpad=0.5,
              handlelength=2.0)


def main():
    ts = json.load(open(os.path.join(RESDIR, "ics_timeseries.json")))
    summ = json.load(open(os.path.join(RESDIR, "ics_warning_compare.json")))

    fig, ax = plt.subplots(2, 2, figsize=(12.5, 8.4))

    tW = np.array(ts["WARN"]["t"]) / 60

    # (a) 市政压头与预警检出（两情形故障相同, 只画一条）
    a = ax[0, 0]
    a.plot(tW, ts["WARN"]["muni"], color=COLORS["mut"], label="Municipal supply head")
    a.axhline(28.0, color="red", ls="--", lw=1, label="Supply-failure threshold (28 m)")
    dt_ = summ["WARN"]["detect_t"]
    if dt_ is not None:
        a.axvline(dt_ / 60, color=COL["WARN"], ls=":", lw=1.8,
                  label=f"Early warning issued (t = {dt_/60:.1f} min)")
    a.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    a.set_ylabel("Head (m)"); a.set_xlabel("Time (min)")
    a.legend(loc="center right", borderaxespad=0.6, **LEG_KW)

    # (b) 集水池水位（1.2 m 保护线入图例; 图例置于左下空白带, 抬离 1.2 m 线）
    a = ax[0, 1]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["H_pool"], color=COL[k], label=CASES[k])
    a.axhline(1.2, color="red", ls=":", lw=1, label="Pump-trip submergence (1.2 m)")
    a.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
    a.set_ylabel("Basin level (m)"); a.set_xlabel("Time (min)")
    a.legend(loc="lower left", bbox_to_anchor=(0.01, 0.07), borderaxespad=0, **LEG_KW)

    # (c) 凝汽器背压（15 kPa 跳机线入图例; 图例置于中部空白带, 远离 5 kPa 平台与 15 kPa 线）
    a = ax[1, 0]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["p_b"], color=COL[k], label=CASES[k])
    a.axhline(15.0, color="red", ls="--", lw=1, label="Back-pressure trip (15 kPa)")
    a.set_title("(c)", fontsize=12, fontweight="bold", loc="left")
    a.set_ylabel("Back-pressure (kPa)"); a.set_xlabel("Time (min)")
    a.legend(loc="center left", borderaxespad=0.6, **LEG_KW)

    # (d) 功率缺额（核心对比; 峰值/电量数字入图注, 图例只保留情形语义）
    a = ax[1, 1]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["deficit"], color=COL[k], label=CASES[k])
    a.set_title("(d)", fontsize=12, fontweight="bold", loc="left")
    a.set_ylabel("Power deficit (MW)"); a.set_xlabel("Time (min)")
    a.legend(loc="upper left", borderaxespad=0.6, **LEG_KW)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Fig9_early_warning_comparison.png"), **SAVE)
    plt.close(fig)
    print("saved Fig9")


if __name__ == "__main__":
    main()
