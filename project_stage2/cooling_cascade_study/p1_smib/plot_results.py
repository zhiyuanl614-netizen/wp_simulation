"""
P1 SMIB 结果可视化
==================
读取 results/ 下的仿真 CSV, 绘制全链条时序图:
水位 -> 循环水流量 -> 背压 -> 降额系数 -> 频率 -> 功率
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 中文字体
for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
        plt.rcParams["font.family"] = "Noto Sans CJK JP"
        break
plt.rcParams["axes.unicode_minus"] = False

C = {"w":"#1f6fb2","p":"#2e8b57","b":"#c0392b","f":"#8b3a62","k":"#e07b39"}


def load_csv(path):
    d = {}
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            for k, v in row.items():
                d.setdefault(k, []).append(float(v))
    return {k: np.array(v) for k, v in d.items()}


def plot_one(path, t_fault=60.0):
    d = load_csv(path)
    t = d["t"] / 60.0   # 分钟
    tf = t_fault / 60.0

    fig, ax = plt.subplots(3, 2, figsize=(13, 9))
    fig.suptitle("P1 SMIB 冷却水故障级联全链条时序  (市政断水 → 跳机 → 频率响应)",
                 fontsize=15, fontweight="bold")

    def mark(a):
        a.axvline(tf, color="gray", ls=":", lw=1)
        a.grid(alpha=0.3)

    # 1 水位
    a = ax[0,0]
    a.plot(t, d["H_tank"], color=C["w"], label="高位补水箱 H_tank")
    a.plot(t, d["H_pool"], color=C["p"], label="集水池 H_pool")
    a.set_ylabel("水位 (m)"); a.set_title("① 水源侧水位"); a.legend(fontsize=9); mark(a)

    # 2 循环水流量
    a = ax[0,1]
    a.plot(t, d["m_cw"], color=C["w"])
    a.set_ylabel("m_cw (m³/s)"); a.set_title("② 循环水泵流量"); mark(a)

    # 3 背压
    a = ax[1,0]
    a.plot(t, d["p_b"], color=C["b"])
    a.axhline(15.0, color="red", ls="--", lw=1, label="高背压跳机定值 15kPa")
    a.axhline(5.0, color="green", ls=":", lw=1, label="设计背压 5kPa")
    a.set_ylabel("背压 (kPa)"); a.set_title("③ 凝汽器背压"); a.legend(fontsize=9); mark(a)

    # 4 降额系数
    a = ax[1,1]
    a.plot(t, d["k_p"], color=C["k"])
    a.set_ylabel("k_p"); a.set_title("④ 汽轮机机械功率降额系数"); a.set_ylim(0,1.1); mark(a)

    # 5 频率
    a = ax[2,0]
    a.plot(t, d["f"], color=C["f"])
    a.axhline(49.0, color="orange", ls="--", lw=1, label="UFLS 第1级 49Hz")
    a.axhline(50.0, color="gray", ls=":", lw=1)
    a.set_ylabel("频率 (Hz)"); a.set_xlabel("时间 (min)")
    a.set_title("⑤ 系统频率 (COI)"); a.legend(fontsize=9); mark(a)

    # 6 功率
    a = ax[2,1]
    if "Paff_MW" in d:
        a.plot(t, d["Paff_MW"], color=C["b"], label="受影响机组 P_aff")
        a.plot(t, d["Pmech_MW"], color=C["p"], label="系统总机械功率")
        a.plot(t, d["Pload_MW"], color=C["f"], ls="--", label="系统负荷(含UFLS)")
    a.set_ylabel("功率 (MW)"); a.set_xlabel("时间 (min)")
    a.set_title("⑥ 有功功率平衡"); a.legend(fontsize=9); mark(a)

    fig.tight_layout(rect=[0,0,1,0.97])
    out = path.replace(".csv", ".png")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("saved", out)
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    resdir = os.path.join(here, "..", "results")
    args = sys.argv[1:]
    if args:
        files = [os.path.join(resdir, a) for a in args]
    else:
        files = [os.path.join(resdir, f) for f in os.listdir(resdir) if f.startswith("p1_smib_") and f.endswith(".csv")]
    for f in sorted(files):
        # 从文件名解析 t_fault
        tf = 60.0
        for part in os.path.basename(f).split("_"):
            if part.startswith("tf"):
                try: tf = float(part[2:])
                except: pass
        plot_one(f, t_fault=tf)
