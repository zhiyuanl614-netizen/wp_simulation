"""
P5 —— 韧性图谱 (预警提前量 × 故障规模) + 最优预警-处置策略
============================================================
在 P4 基础上做二维扫描, 生成:
  (1) 韧性图谱: 横轴=预警提前量(min), 纵轴=故障规模(共因机组数),
      色标=频率最低点 f_nadir(Hz)  —— 一图看清"何时何种规模需要多早预警"。
  (2) 韧性增益图谱: ΔResilience = f_nadir(主动) - f_nadir(被动)。
  (3) 临界预警提前量曲线 t_lead*(故障规模): 使 f_nadir 恰达安全阈值的最小提前量。
  (4) 面向调度的最优预警-处置策略表。

故障规模: 由市政水网共因影响的机组数量表征(取最大的若干非平衡机组)。
预警提前量: 通过 t_detect 反算 (提前量 = 被动首台跳机时刻 - 预警时刻)。
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import TwoSlopeNorm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p3_ieee118"))
from run_p3 import run   # noqa

for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp); plt.rcParams["font.family"] = "Noto Sans CJK JP"; break
plt.rcParams["axes.unicode_minus"] = False
RESDIR = os.path.join(HERE, "..", "results")

# 故障规模: 逐步增加的共因机组集合(IEEE118 最大的非平衡机组)
FAULT_SETS = {
    1: [89],
    2: [89, 80],
    3: [89, 80, 10],
    4: [89, 80, 10, 66],
    5: [89, 80, 10, 66, 65],
}
SAFE_TH = 49.0     # 安全阈值(不触发 UFLS-1)
COLLAPSE_TH = 47.0
DT = 4.0
T_END = 3400.0   # v2水力模型下损失随热负荷, 跳机被拉开, 需更长窗口


def first_trip_time(affected):
    """被动情形下的首台跳机时刻(用于换算预警提前量)。"""
    s, _, _ = run(affected=list(affected), t_fault=60.0, ramp=0.0,
                  t_end=T_END, dt=DT, no_overload=True, proactive=False)
    trips = [v for v in s['t_gen_trips'].values() if v is not None]
    return (min(trips) if trips else T_END), s['f_nadir']


def build():
    scales = sorted(FAULT_SETS.keys())
    # 目标预警提前量网格(min): 提前量 = t_first_trip - (t_fault + t_detect)
    leads_min = [0.5, 1, 2, 3, 5, 8, 12, 18]

    nadir_active = np.full((len(scales), len(leads_min)), np.nan)
    nadir_passive = {}
    ftrip = {}
    for i, sc in enumerate(scales):
        aff = FAULT_SETS[sc]
        t_first, f_pass = first_trip_time(aff)
        nadir_passive[sc] = f_pass
        ftrip[sc] = t_first
        for j, lead in enumerate(leads_min):
            # 由目标提前量反算 t_detect
            t_detect = t_first - 60.0 - lead * 60.0
            if t_detect < 0:
                t_detect = 0.0
            s, _, _ = run(affected=list(aff), t_fault=60.0, ramp=0.0,
                          t_end=T_END, dt=DT, no_overload=True, proactive=True,
                          t_detect=t_detect, runback_rate_frac=0.0015,
                          reserve_boost=0.0)
            nadir_active[i, j] = s['f_nadir']

    gain = nadir_active - np.array([[nadir_passive[sc]] for sc in scales])

    # 临界预警提前量 t_lead*(scale): 使 nadir>=SAFE_TH 的最小 lead
    tlead_star = {}
    for i, sc in enumerate(scales):
        crit = None
        for j, lead in enumerate(leads_min):
            if nadir_active[i, j] >= SAFE_TH:
                crit = lead; break
        tlead_star[sc] = crit
    return dict(scales=scales, leads=leads_min, nadir_active=nadir_active,
                nadir_passive=nadir_passive, gain=gain, ftrip=ftrip,
                tlead_star=tlead_star)


def plot(D, outname="p5_resilience_map.png"):
    scales, leads = D['scales'], D['leads']
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.6))
    fig.suptitle("P5 韧性图谱 —— 预警提前量 × 故障规模  (同源共因冷却水故障, IEEE-118)",
                 fontsize=14, fontweight="bold")

    extent = [0, len(leads), 0, len(scales)]
    # 左: 主动频率最低点
    a = ax[0]
    im = a.imshow(D['nadir_active'], aspect='auto', origin='lower',
                  cmap='RdYlGn', vmin=44, vmax=50, extent=extent)
    a.set_xticks(np.arange(len(leads)) + 0.5); a.set_xticklabels(leads)
    a.set_yticks(np.arange(len(scales)) + 0.5); a.set_yticklabels(scales)
    a.set_xlabel("预警提前量 (min)"); a.set_ylabel("故障规模 (共因机组数)")
    a.set_title("① 主动预警下 频率最低点 f_nadir (Hz)")
    for i in range(len(scales)):
        for j in range(len(leads)):
            v = D['nadir_active'][i, j]
            a.text(j+0.5, i+0.5, f"{v:.1f}", ha='center', va='center', fontsize=8,
                   color='black')
    fig.colorbar(im, ax=a, label="f_nadir (Hz)")

    # 右: 韧性增益
    a = ax[1]
    g = D['gain']
    norm = TwoSlopeNorm(vmin=min(-0.1, g.min()), vcenter=0.0, vmax=max(0.1, g.max()))
    im = a.imshow(g, aspect='auto', origin='lower', cmap='RdYlGn', norm=norm, extent=extent)
    a.set_xticks(np.arange(len(leads)) + 0.5); a.set_xticklabels(leads)
    a.set_yticks(np.arange(len(scales)) + 0.5); a.set_yticklabels(scales)
    a.set_xlabel("预警提前量 (min)"); a.set_ylabel("故障规模 (共因机组数)")
    a.set_title("② 韧性增益 ΔResilience = f主动 − f被动 (Hz)")
    for i in range(len(scales)):
        for j in range(len(leads)):
            a.text(j+0.5, i+0.5, f"+{g[i,j]:.1f}", ha='center', va='center', fontsize=8,
                   color='black')
    fig.colorbar(im, ax=a, label="ΔResilience (Hz)")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(RESDIR, outname); fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig); print("saved", out)


def plot_critical(D, outname="p5_critical_leadtime.png"):
    scales = D['scales']
    xs = [sc for sc in scales if D['tlead_star'][sc] is not None]
    ys = [D['tlead_star'][sc] for sc in xs]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(xs, ys, "o-", color="#1f6fb2", lw=2, ms=9)
    for x, y in zip(xs, ys):
        ax.annotate(f"{y} min", (x, y), textcoords="offset points", xytext=(0, 10),
                    ha='center', fontsize=10, fontweight='bold')
    ax.set_xlabel("故障规模 (共因机组数)"); ax.set_ylabel("临界预警提前量 t_lead* (min)")
    ax.set_title("P5 临界预警提前量 —— 保证系统安全(f≥49Hz)所需的最小预警窗口",
                 fontsize=12, fontweight="bold")
    ax.grid(alpha=.3); ax.set_xticks(scales)
    # 标注被动 nadir
    txt = "被动基准 f_nadir:  " + "  ".join(
        f"{sc}机={D['nadir_passive'][sc]:.1f}Hz" for sc in scales)
    ax.text(0.02, 0.02, txt, transform=ax.transAxes, fontsize=8.5, color="#c0392b",
            va="bottom")
    fig.tight_layout()
    out = os.path.join(RESDIR, outname); fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig); print("saved", out)


def dump_json(D):
    out = os.path.join(RESDIR, "p5_summary.json")
    obj = dict(scales=D['scales'], leads=D['leads'],
               nadir_active=D['nadir_active'].round(2).tolist(),
               nadir_passive={str(k): round(v, 2) for k, v in D['nadir_passive'].items()},
               gain=D['gain'].round(2).tolist(),
               first_trip_s={str(k): round(v, 0) for k, v in D['ftrip'].items()},
               tlead_star={str(k): v for k, v in D['tlead_star'].items()})
    json.dump(obj, open(out, "w"), ensure_ascii=False, indent=2)
    print("saved", out)


if __name__ == "__main__":
    D = build()
    plot(D); plot_critical(D); dump_json(D)
    print("\n=== 临界预警提前量 t_lead* (保证 f>=49Hz) ===")
    for sc in D['scales']:
        print(f"  {sc}机共因: 被动 {D['nadir_passive'][sc]:.1f}Hz, "
              f"首台跳机 {D['ftrip'][sc]:.0f}s, t_lead*={D['tlead_star'][sc]} min")
