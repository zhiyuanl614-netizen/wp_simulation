"""
P3 结果可视化 —— 频率/电压/负载率/级联对比
"""
import os, sys, csv
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


def load(path):
    d = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                try: val = float(v)
                except: val = np.nan
                d.setdefault(k, []).append(val)
    return {k: np.array(v) for k, v in d.items()}


def compare(specs, outname="p3_compare.png"):
    """specs: list of (csvfile, label, color)"""
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("P3 IEEE-118 冷却水故障级联对比  (单机 vs 同源多机共因)",
                 fontsize=15, fontweight="bold")
    for csvf, lab, col in specs:
        p = os.path.join(RESDIR, csvf)
        if not os.path.exists(p):
            continue
        d = load(p)
        t = d["t"] / 60.0
        # 频率
        ax[0,0].plot(t, d["f"], color=col, label=lab)
        # 最低母线电压
        ax[0,1].plot(t, d["Vmin"], color=col, label=lab)
        # 最大线路负载率
        ax[1,0].plot(t, d["max_util"], color=col, label=lab)
        # 级联跳线数
        ax[1,1].plot(t, d["n_line_trip"], color=col, label=lab)

    a = ax[0,0]; a.axhline(49.0, color="orange", ls="--", lw=1, label="UFLS-1 49Hz")
    a.axhline(48.0, color="red", ls="--", lw=1, label="UFLS 48Hz")
    a.set_title("① 系统频率 (COI)"); a.set_ylabel("f (Hz)"); a.grid(alpha=.3); a.legend(fontsize=8)

    a = ax[0,1]; a.axhline(0.90, color="red", ls="--", lw=1, label="0.90pu 下限")
    a.set_title("② 最低母线电压"); a.set_ylabel("Vmin (pu)"); a.grid(alpha=.3); a.legend(fontsize=8)

    a = ax[1,0]; a.axhline(1.0, color="red", ls="--", lw=1, label="额定限值")
    a.set_title("③ 最大线路负载率"); a.set_ylabel("max util"); a.set_xlabel("时间 (min)"); a.grid(alpha=.3); a.legend(fontsize=8)

    a = ax[1,1]
    a.set_title("④ 级联跳线累计条数"); a.set_ylabel("条"); a.set_xlabel("时间 (min)"); a.grid(alpha=.3); a.legend(fontsize=8)

    fig.tight_layout(rect=[0,0,1,0.96])
    out = os.path.join(RESDIR, outname)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    compare([
        ("p3_aff89_tf60_ramp0_m1.0_react.csv", "单机 bus89 (无过载跳线)", "#1f6fb2"),
        ("p3_aff89-80-10_tf60_ramp0_m1.0_react.csv", "同源3机共因 (89,80,10)", "#c0392b"),
    ])
