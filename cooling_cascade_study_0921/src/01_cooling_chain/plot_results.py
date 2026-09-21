"""
Fig.7  Cooling-water fault mechanism chain (time series).
water level -> circulating flow -> back-pressure -> derating -> output / power loss
Reads results/cooling_chain/p1_smib_*.csv
 -> writes figures/Fig7_cooling_chain_timeseries.png (ramp0 case only)
校准 v2 (2026-09-02): ① mathtext 改 custom fontset(含 rm/it/bf/sf/tt/cal 全样式,
指向 figstyle 解析出的无衬线字体)——消除 DejaVu 混入与 cursive 回退, PDF 嵌入
字体实测仅 Liberation Sans 单一族; ② 图例位置显式化——(a) upper right /
(c) center left(数据空带), 不覆盖曲线; ③ (a) 增故障竖线标注 "Muni outage,
t = 1.0 min"(白描边, 措辞同 Fig6(b)/Fig9)。
数据核实 (2026-09-02, 1s 网格复跑, 轨迹逐列吻合): 六事件 ①失压 1.0 min
②补水箱排空 5.2 min ③71.8 min 进淹没不足降额带(m_cw 线性降额) ④93.4 min
背压越限 15 kPa(未及 1.2 m 跳泵水位, m_cw 余 36%) ⑤93.4 min 跳机(3 s 延时,
SAET=92.4 min=闭合账口径) ⑥出力 607 MW→0。跳泵事件确认不发生(原 caption ④
"循环水泵跳泵 m_cw→0"有误, 已改)。
"""
import os, sys, csv
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager

# 校准 v2 (2026-09-02): mathtext ($H_{tank}$/$m_{cw}$/$k_p$/m^3) 默认走 DejaVu,
# 与正文字体混入 —— 改 custom fontset 指向 figstyle 实际解析出的无衬线字体,
# 保持全图单一字体族 (同 Fig5 v2 消除 DejaVu 混入的处理原则)。
_FN = font_manager.findfont(font_manager.FontProperties(
    family=["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"]))
_MF = font_manager.FontProperties(fname=_FN).get_name()
plt.rcParams.update({"mathtext.fontset": "custom",
                     "mathtext.rm": _MF, "mathtext.it": _MF + ":italic",
                     "mathtext.bf": _MF + ":bold",
                     "mathtext.sf": _MF, "mathtext.tt": _MF, "mathtext.cal": _MF})
HALO = [pe.withStroke(linewidth=2.4, foreground="white")]

C = {"w": COLORS["muni"], "p": COLORS["ok"], "b": COLORS["power"],
     "f": "#8b3a62", "k": COLORS["amber"]}
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "figures")


def load_csv(path):
    d = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                d.setdefault(k, []).append(float(v))
    return {k: np.array(v) for k, v in d.items()}


def plot_one(path, t_fault=60.0, also_fig=False):
    d = load_csv(path)
    t = d["t"] / 60.0
    tf = t_fault / 60.0

    fig, ax = plt.subplots(3, 2, figsize=(12, 9.2))
    def mark(a):
        a.axvline(tf, color=COLORS["mut"], ls=":", lw=1)

    a = ax[0, 0]
    a.plot(t, d["H_tank"], color=C["w"], label="Make-up tank $H_{tank}$")
    a.plot(t, d["H_pool"], color=C["p"], label="Pool $H_{pool}$")
    a.set_ylabel("Water level (m)"); a.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    a.legend(loc="upper right"); mark(a)
    # v2: 故障竖线标注 (自含可读; 措辞风格同 Fig6(b)/Fig9)
    # 位置 (0.09, 0.86) va=center: 避开 H_tank 平顶(y≈0.95)/骤降段(x<0.06)与
    # H_pool(y≈0.775)——几何核验该带两曲线零覆盖
    a.text(0.09, 0.86, "Muni outage, t = %.1f min" % tf, transform=a.transAxes,
           fontsize=12, color="black", va="center", ha="left",
           path_effects=HALO, zorder=5)

    a = ax[0, 1]
    a.plot(t, d["m_cw"], color=C["w"])
    a.set_ylabel("$m_{cw}$ (m$^3$/s)"); a.set_title("(b)", fontsize=12, fontweight="bold", loc="left"); mark(a)

    a = ax[1, 0]
    a.plot(t, d["p_b"], color=C["b"])
    a.axhline(15.0, color="red", ls="--", lw=1, label="Hi-back-pressure trip 15 kPa")
    a.axhline(5.0, color="green", ls=":", lw=1, label="Design back-pressure 5 kPa")
    a.set_ylabel("Back-pressure (kPa)"); a.set_title("(c)", fontsize=12, fontweight="bold", loc="left")
    a.legend(loc="center left"); mark(a)

    a = ax[1, 1]
    a.plot(t, d["k_p"], color=C["k"])
    a.set_ylabel("$k_p$"); a.set_title("(d)", fontsize=12, fontweight="bold", loc="left"); a.set_ylim(0, 1.1); mark(a)

    a = ax[2, 0]
    a.plot(t, d["Paff_MW"], color=C["b"])
    a.set_ylabel("Output (MW)"); a.set_xlabel("Time (min)")
    a.set_title("(e)", fontsize=12, fontweight="bold", loc="left"); mark(a)

    a = ax[2, 1]
    a.plot(t, d["lost_MW"], color=C["f"])
    a.set_ylabel("Power loss (MW)"); a.set_xlabel("Time (min)")
    a.set_title("(f)", fontsize=12, fontweight="bold", loc="left"); mark(a)

    fig.tight_layout()
    if also_fig:
        fig.savefig(os.path.join(FIG, "Fig7_cooling_chain_timeseries.png"), **SAVE)
        print("saved Fig7 <-", os.path.basename(path))
    plt.close(fig)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    resdir = os.path.join(here, "..", "..", "results", "cooling_chain")
    args = sys.argv[1:]
    if args:
        files = [os.path.join(resdir, a) for a in args]
    else:
        files = [os.path.join(resdir, f) for f in os.listdir(resdir)
                 if f.startswith("p1_smib_") and f.endswith(".csv")]
    for f in sorted(files):
        tf = 60.0
        for part in os.path.basename(f).split("_"):
            if part.startswith("tf"):
                try: tf = float(part[2:])
                except: pass
        # ramp0 case is the canonical Fig.7
        plot_one(f, t_fault=tf, also_fig=("ramp0" in os.path.basename(f)))
