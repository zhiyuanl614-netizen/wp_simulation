"""
ICS 结果可视化 —— 有无早期预警对比
==================================
检测量: 市政供水压力(源头信号); 只对比 WARN vs NOWARN。
图: ① 市政压头 & 检出时刻  ② 集水池水位  ③ 背压  ④ 频率
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
        plt.rcParams["font.family"] = "Noto Sans CJK JP"
        break
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "results")

CASES = {"WARN": "有早期预警", "NOWARN": "无早期预警(被动)"}
COL = {"WARN": "#1f6fb2", "NOWARN": "#c0392b"}


def main():
    ts = json.load(open(os.path.join(RESDIR, "ics_timeseries.json")))
    summ = json.load(open(os.path.join(RESDIR, "ics_warning_compare.json")))

    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("ICS 早期预警对比 —— 检测量: 市政供水压力 (有预警 vs 无预警)",
                 fontsize=14, fontweight="bold")

    tW = np.array(ts["WARN"]["t"]) / 60

    # ① 市政压头 + 检出时刻
    a = ax[0, 0]
    a.plot(tW, ts["WARN"]["muni"], color="#555", lw=2, label="市政供水压头")
    a.axhline(5.0, color="red", ls="--", lw=1, label="检出阈值 5m")
    dt_ = summ["WARN"]["detect_t"]
    if dt_ is not None:
        a.axvline(dt_ / 60, color=COL["WARN"], ls=":", lw=1.8,
                  label=f"检出/预警 {dt_/60:.1f}min")
    a.set_title("① 市政供水压头 & 检出时刻(源头信号)")
    a.set_ylabel("压头 (m)"); a.set_xlabel("时间 (min)")
    a.legend(fontsize=9); a.grid(alpha=.3)

    # ② 集水池水位
    a = ax[0, 1]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["H_pool"], color=COL[k], lw=2,
               label=CASES[k])
    a.axhline(1.2, color="red", ls=":", lw=1, label="跳泵淹没线 1.2m")
    a.set_title("② 集水池水位"); a.set_ylabel("水位 (m)"); a.set_xlabel("时间 (min)")
    a.legend(fontsize=9); a.grid(alpha=.3)

    # ③ 背压
    a = ax[1, 0]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["p_b"], color=COL[k], lw=2,
               label=CASES[k])
    a.axhline(15.0, color="red", ls="--", lw=1, label="高背压跳机 15kPa")
    a.set_title("③ 凝汽器背压 (预警主动降负荷 vs 被动)")
    a.set_ylabel("背压 (kPa)"); a.set_xlabel("时间 (min)")
    a.legend(fontsize=9); a.grid(alpha=.3)

    # ④ 频率
    a = ax[1, 1]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["f"], color=COL[k], lw=2,
               label=f"{CASES[k]} (nadir {summ[k]['f_nadir']:.2f}Hz)")
    a.axhline(49.0, color="orange", ls="--", lw=1, label="UFLS-1 49Hz")
    a.set_title("④ 系统频率响应"); a.set_ylabel("f (Hz)"); a.set_xlabel("时间 (min)")
    a.legend(fontsize=9); a.grid(alpha=.3)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = os.path.join(RESDIR, "ics_warning_compare.png")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
