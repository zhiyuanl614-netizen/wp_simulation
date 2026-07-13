"""
P4 —— 早期预警韧性量化 (被动 vs 主动)
=====================================
核心科学问题: 水力慢动态(分钟级缓冲) 与 电力快动态 的时序差异,
能否作为"早期预警窗口" —— 市政水网故障信息经信息/工控系统(ICS)
提前告知电力系统, 使其在机组跳闸前主动调整(降负荷+预置备用),
从而把"被动等跳闸"转为"主动软着陆"。本脚本对比两种模式并量化韧性增益。

韧性指标:
  - 频率最低点 f_nadir (越高越好)
  - 是否触发 UFLS / 欠频崩溃
  - 首台机组跳机时刻 (主动降负荷可延后甚至避免)
  - 级联跳线条数 / 失负荷量
  - "韧性裕度" = f_nadir - 崩溃阈值
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


def series(rows, key):
    return np.array([r[key] for r in rows], dtype=float)


def run_pair(affected, ramp=0.0, t_end=3200.0, dt=4.0,
             t_detect=30.0, runback=0.0015, reserve_boost=0.0, preemptive_shed=0.15):
    """跑被动 + 主动 两次, 返回 (react, proact) 结果字典。
    主动 = 预置三级备用 + 速率受限 runback + 预防性切负荷(大故障必需)。"""
    common = dict(affected=affected, t_fault=60.0, ramp=ramp, t_end=t_end, dt=dt,
                  no_overload=True)
    sr, rr, er = run(**common, proactive=False)
    sp, rp, ep = run(**common, proactive=True, t_detect=t_detect,
                     runback_rate_frac=runback, reserve_boost=reserve_boost,
                     preemptive_shed=preemptive_shed)
    return (sr, rr), (sp, rp)


def plot_pair(react, proact, affected, outname):
    (sr, rr), (sp, rp) = react, proact
    tr = series(rr, "t") / 60.0
    tp = series(rp, "t") / 60.0

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f"P4 早期预警韧性对比 —— 同源{len(affected)}机共因故障  (母线 {affected})",
                 fontsize=14, fontweight="bold")

    a = ax[0]
    a.plot(tr, series(rr, "f"), color="#c0392b", lw=2, label=f"被动响应  (nadir {sr['f_nadir']:.2f} Hz)")
    a.plot(tp, series(rp, "f"), color="#1f6fb2", lw=2, label=f"主动预警  (nadir {sp['f_nadir']:.2f} Hz)")
    a.axhline(49.0, color="orange", ls="--", lw=1, label="UFLS-1 49 Hz")
    a.axhline(48.0, color="red", ls="--", lw=1, label="UFLS 48 Hz")
    a.axhline(47.0, color="darkred", ls=":", lw=1, label="崩溃阈值 47 Hz")
    a.axvline(60/60, color="gray", ls=":", lw=1)
    a.set_title("① 系统频率响应"); a.set_xlabel("时间 (min)"); a.set_ylabel("f (Hz)")
    a.grid(alpha=.3); a.legend(fontsize=9)

    a = ax[1]
    # 受影响机组总出力(近似: 初始 - lost)
    a.plot(tr, series(rr, "lost_MW"), color="#c0392b", lw=2, label="被动: 有功缺额")
    a.plot(tp, series(rp, "lost_MW"), color="#1f6fb2", lw=2, label="主动: 有功缺额")
    a.set_title("② 受影响机组有功缺额 (主动降负荷=平滑转移)")
    a.set_xlabel("时间 (min)"); a.set_ylabel("缺额 (MW)")
    a.grid(alpha=.3); a.legend(fontsize=9)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(RESDIR, outname)
    fig.savefig(out, dpi=120, bbox_inches="tight"); plt.close(fig)
    print("saved", out)


def resilience_table(react, proact):
    (sr, _), (sp, _) = react, proact
    def trips(s):
        return sorted([v for v in s['t_gen_trips'].values() if v is not None])
    print("\n" + "=" * 66)
    print(" P4 韧性量化对比 (同源多机共因故障)")
    print("=" * 66)
    print(f" {'指标':<22}{'被动响应':>16}{'主动预警':>16}")
    print("-" * 66)
    print(f" {'频率最低点 (Hz)':<20}{sr['f_nadir']:>16.2f}{sp['f_nadir']:>16.2f}")
    print(f" {'韧性裕度 f-47Hz (Hz)':<18}{sr['f_nadir']-47:>16.2f}{sp['f_nadir']-47:>16.2f}")
    tr, tp = trips(sr), trips(sp)
    print(f" {'首台跳机 (s)':<21}{(tr[0] if tr else float('nan')):>16.0f}{(tp[0] if tp else float('nan')):>16.0f}")
    print(f" {'跳机台数':<22}{len(tr):>16d}{len(tp):>16d}")
    print(f" {'级联跳线 (条)':<20}{sr['n_line_trip']:>16d}{sp['n_line_trip']:>16d}")
    print(f" {'失负荷 (MW)':<21}{sr['load_loss']:>16.1f}{sp['load_loss']:>16.1f}")
    gain = sp['f_nadir'] - sr['f_nadir']
    print("-" * 66)
    print(f" 频率韧性增益: +{gain:.2f} Hz   "
          f"({'避免崩溃' if sr['f_nadir']<47<=sp['f_nadir'] else '显著改善' if gain>0.3 else '改善有限'})")
    print("=" * 66)
    return dict(f_nadir_react=sr['f_nadir'], f_nadir_proact=sp['f_nadir'], gain=gain)


if __name__ == "__main__":
    # v2水力模型下(损失随热负荷,跳机被拉开), 危险阈值上移至 5 机共因
    affected = [89, 80, 10, 66, 65]
    react, proact = run_pair(affected, ramp=0.0, t_detect=300.0, runback=0.0015,
                             reserve_boost=0.0, preemptive_shed=0.15)
    plot_pair(react, proact, affected, "p4_warning_compare.png")
    resilience_table(react, proact)
