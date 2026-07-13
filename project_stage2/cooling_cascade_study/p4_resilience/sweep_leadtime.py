"""
P4 敏感性 —— 预警提前量(lead time) 对韧性的影响
================================================
科学问题: 水力慢动态提供的"缓冲时间"越长, 预警越早, 主动控制越从容。
本脚本扫描不同的"降负荷速率"(等效于不同预警提前量/处置强度),
量化频率韧性(f_nadir)随预警力度的变化, 定位"最小有效预警强度"。

同时对比: 无预警(被动) vs 不同 runback 速率(主动)。
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p3_ieee118"))
from run_p3 import run   # noqa

for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp); plt.rcParams["font.family"] = "Noto Sans CJK JP"; break
plt.rcParams["axes.unicode_minus"] = False
RESDIR = os.path.join(HERE, "..", "results")


def sweep(affected=(89, 80, 10, 66, 65), t_end=3200.0, dt=4.0, shed=0.15):
    # 被动基准
    sr, _, _ = run(affected=list(affected), t_fault=60.0, ramp=0.0,
                   t_end=t_end, dt=dt, no_overload=True, proactive=False)
    base_nadir = sr['f_nadir']
    # 被动下首台跳机时刻(用于换算"预警提前量")
    ptrips = [v for v in sr['t_gen_trips'].values() if v is not None]
    first_trip_passive = min(ptrips) if ptrips else t_end

    # 主动(含15%预防性切负荷): 扫描三级备用起机速率 —— 越快=预警窗口内能起更多备用
    rates = [0.3, 0.5, 0.75, 1.0, 1.5, 2.0]   # 相对基准(1.0 = ~15min全上)
    base_tert_rate = 900.0 / 900.0
    nadirs = []
    for k in rates:
        sp, _, _ = run(affected=list(affected), t_fault=60.0, ramp=0.0,
                       t_end=t_end, dt=dt, no_overload=True, proactive=True,
                       t_detect=300.0, runback_rate_frac=0.0015, reserve_boost=0.0,
                       preemptive_shed=shed, tertiary_rate=base_tert_rate * k)
        nadirs.append(sp['f_nadir'])

    # 扫描检测延时 t_detect (预警提前量: 越小=预警越早, 窗口越充分)
    detects = [60, 300, 600, 900, 1200, 1500, 1700]
    nadirs_d, leads = [], []
    for td in detects:
        sp, _, _ = run(affected=list(affected), t_fault=60.0, ramp=0.0,
                       t_end=t_end, dt=dt, no_overload=True, proactive=True,
                       t_detect=td, runback_rate_frac=0.0015, reserve_boost=0.0,
                       preemptive_shed=shed)
        nadirs_d.append(sp['f_nadir'])
        leads.append((first_trip_passive - (60.0 + td)) / 60.0)  # 预警提前量(min)

    return base_nadir, rates, nadirs, detects, nadirs_d, leads


def plot(base_nadir, rates, nadirs, detects, nadirs_d, leads, outname):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("P4 敏感性 —— 三级备用起机速率 / 预警提前量 对系统韧性的影响 (同源5机共因)",
                 fontsize=13.5, fontweight="bold")

    # 左: 三级备用起机速率 vs f_nadir
    a = ax[0]
    a.axhline(base_nadir, color="#c0392b", ls="--", lw=2, label=f"被动基准 {base_nadir:.2f} Hz")
    a.plot(rates, nadirs, "o-", color="#1f6fb2", lw=2, label="主动预警(t_detect=30s)")
    a.axhline(47.0, color="darkred", ls=":", lw=1, label="崩溃阈值 47 Hz")
    a.axhline(49.0, color="orange", ls="--", lw=1, label="UFLS-1 49 Hz")
    a.set_xlabel("三级备用起机速率 (相对基准, 1.0≈15min全上)"); a.set_ylabel("频率最低点 (Hz)")
    a.set_title("① 备用起机能力 → 韧性"); a.grid(alpha=.3); a.legend(fontsize=8.5)

    # 右: 预警提前量(min) vs f_nadir
    a = ax[1]
    a.axhline(base_nadir, color="#c0392b", ls="--", lw=2, label=f"被动基准 {base_nadir:.2f} Hz")
    a.plot(leads, nadirs_d, "s-", color="#2e8b57", lw=2, label="主动预警")
    a.axhline(47.0, color="darkred", ls=":", lw=1, label="崩溃阈值 47 Hz")
    a.axhline(49.0, color="orange", ls="--", lw=1, label="UFLS-1 49 Hz")
    a.set_xlabel("预警提前量 = 跳机时刻 − 预警时刻 (min, 越大=越早预警)")
    a.set_ylabel("频率最低点 (Hz)")
    a.set_title("② 预警提前量 → 韧性 (核心结论)"); a.grid(alpha=.3); a.legend(fontsize=8.5)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(RESDIR, outname)
    fig.savefig(out, dpi=120, bbox_inches="tight"); plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    r = sweep()
    plot(*r, "p4_leadtime_sweep.png")
    base, rates, nadirs, detects, nadirs_d, leads = r
    print("\n被动基准 f_nadir =", round(base, 2), "Hz")
    print("三级备用起机速率(x) -> f_nadir:", [(x, round(y,2)) for x, y in zip(rates, nadirs)])
    print("预警提前量(min)     -> f_nadir:", [(round(l,1), round(y,2)) for l, y in zip(leads, nadirs_d)])
