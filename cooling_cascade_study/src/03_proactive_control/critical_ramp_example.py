"""
S2 —— 临界降出力速率数值算例（对齐文献 Fig.3，水侧类比）
==================================================================
参照 Yu et al. (Nat. Commun. 15:4714, 2024) Fig.3 的数值算例范式：
受影响机组按不同降出力速率 runback，展示
  (a) 机组出力轨迹 out_frac(t)——低于临界速率被强制跳机(✕)，
      高于临界速率主动停机(●)，等于临界速率运行时间最长；
  (b) 可用储水量 ASW(t) —— 对应文献的 ALP 曲线；
  (c) 运行时间 T_oper 随"满出力降零时长 1/r"的变化 —— 峰值即临界点。
物理：降出力 → 凝汽器热负荷下降 → 蒸发/排污损失减少 → 储水消耗变慢
      → 缓冲时间延长（"降额自保护"负反馈），故存在临界降出力速率。

输出:
  figures/Fig8_critical_ramp_example.png   (300 dpi, figstyle 统一样式)
  results/proactive_control/critical_ramp_example.json
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..")
sys.path.insert(0, SRC)                     # figstyle
sys.path.insert(0, os.path.join(HERE, "..", "01_cooling_chain"))
from params import Params, load_unit_from_gen          # noqa
import submodels as sm                                  # noqa
from warning_indicators import _forward_water, static_indicators   # noqa
import figstyle                                        # noqa
figstyle.apply()
import matplotlib.pyplot as plt

BUS = 89
FIG_OUT = os.path.join(SRC, "..", "figures", "Fig8_critical_ramp_example.png")
RES_OUT = os.path.join(SRC, "..", "results", "proactive_control", "critical_ramp_example.json")
DT = 1.0          # 与 warning_indicators 口径一致
T_END = 40000.0   # 慢速率需要更长积分域(主动停机验证)


def run_case(ramp_frac_per_s):
    """给定降出力速率 r(1/s)，前向积分返回 (T_oper_s, forced_trip, series)。"""
    Pg, Pmax = load_unit_from_gen(bus=BUS)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)

    def of(t):
        return max(0.0, 1.0 - ramp_frac_per_s * t)

    t_trip, series = _forward_water(p, out_frac_fn=of, dt=DT, t_end=T_END)
    t_zero = 1.0 / ramp_frac_per_s if ramp_frac_per_s > 0 else np.inf
    if t_trip is None or t_trip >= t_zero:
        return t_zero, False, series        # 主动停机成功
    return t_trip, True, series             # 被强制跳机


def asw_of(p, Ht, Hp):
    """可用储水量 ASW (m^3)：补水箱+集水池 相对跳泵最低水位。"""
    return p.A_tank * (Ht - p.H_tank_min) + p.A_pool * (Hp - p.H_submerge_min)


def main():
    Pg, Pmax = load_unit_from_gen(bus=BUS)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
    stat = static_indicators(bus=BUS)
    SAET_s = stat["SAET_s"]

    # ---- 扫描：满出力降零时长 1/r ∈ [600, 24000] s ----
    ramp_times = np.array([600, 900, 1200, 1600, 2000, 2600, 3400, 4400, 5600,
                           7200, 9000, 11000, 13000, 16000, 20000, 24000], dtype=float)
    scan = []
    for rt in ramp_times:
        r = 1.0 / rt
        T, forced, _ = run_case(r)
        scan.append(dict(ramp_time_s=rt, r_per_s=r, T_oper_s=T, forced_trip=forced))
        print(f"  1/r={rt:7.0f} s  T_oper={T:8.0f} s  {'FORCED TRIP' if forced else 'active stop'}")

    # 临界点 = 运行时间最长者
    i_crit = int(np.argmax([s["T_oper_s"] for s in scan]))
    crit = scan[i_crit]
    # 临界速率两侧加密（细化临界点附近）
    print(f"\n临界: 1/r* = {crit['ramp_time_s']:.0f} s "
          f"(r* = {crit['r_per_s']:.3e} /s = {100*crit['r_per_s']*60:.2f} %Pg/min), "
          f"T_max = {crit['T_oper_s']/60:.1f} min, SAET = {SAET_s/60:.1f} min")

    # ---- 代表曲线（供面板 a/b）: 快于临界(主动停) / 临界 / 慢于临界(强制跳) ----
    reps = []
    for idx, tag in [(i_crit - 4, "fast"), (i_crit, "critical"), (i_crit + 4, "slow")]:
        idx = min(max(idx, 0), len(scan) - 1)
        r = scan[idx]["r_per_s"]
        T, forced, series = run_case(r)
        reps.append(dict(tag=tag, ramp_time_s=scan[idx]["ramp_time_s"], r_per_s=r,
                         T_oper_s=T, forced=forced, series=series))
        print(f"  代表[{tag}] 1/r={scan[idx]['ramp_time_s']:.0f}s T={T/60:.1f}min "
              f"{'forced' if forced else 'active'}")

    # ---- 绘图（三联，镜像文献 Fig.3 b/c/d；校准规范 v2：Arial 12、序号左上、无描述性标题）----
    C = figstyle.COLORS
    LBL = {"fast": "Fast ramp",
           "critical": "Critical ramp",
           "slow": "Slow ramp"}
    fig, axes = plt.subplots(3, 1, figsize=(12, 9.6))   # 校准v3: 3x1 竖排(3行1列), X轴全宽拉伸

    # (a) 出力轨迹: 轨迹终止于事件时刻, 事件标记钉在曲线末端
    #     (强制跳机=背压越限, 出力在部分负荷下被切断 -> ✕ 位于当时出力;
    #      主动停机=降出力自然降零 -> ● 位于 0)
    ax = axes[0]
    for rep, style in zip(reps, ["--", "-", ":"]):
        s = [row for row in rep["series"] if row[0] <= rep["T_oper_s"]]
        t = np.array([row[0] for row in s]) / 60.0
        of = np.array([row[5] for row in s])
        lw, col = (2.4, C["warn"]) if rep["tag"] == "critical" else (1.6, C["mut"])
        ax.plot(t, of * Pg, style, lw=lw, color=col, label=LBL[rep["tag"]])
        if rep["forced"]:
            ax.plot([t[-1]], [of[-1] * Pg], "x", ms=11, mew=2.6, color=C["power"])
        else:
            ax.plot([t[-1]], [of[-1] * Pg], "o", ms=9, color=C["ok"])
    ax.axhline(0, color=C["mut"], lw=0.6)
    ax.set_xlabel("Time since supply failure (min)")
    ax.set_ylabel("Affected unit output (MW)")
    ax.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    ax.grid(alpha=0.3)

    # (b) ASW 轨迹: 强制跳机由背压越限触发(储水消耗->循环流量/冷却能力渐进劣化),
    #     先于储水耗尽 -> ✕ 位于跳机时刻的残余 ASW(约 10% ASW0), 与曲线末端重合
    ax = axes[1]
    for rep, style in zip(reps, ["--", "-", ":"]):
        s = [row for row in rep["series"] if row[0] <= rep["T_oper_s"]]
        t = np.array([row[0] for row in s]) / 60.0
        asw = np.array([asw_of(p, row[1], row[2]) for row in s])
        lw, col = (2.4, C["warn"]) if rep["tag"] == "critical" else (1.6, C["mut"])
        ax.plot(t, asw, style, lw=lw, color=col, label=LBL[rep["tag"]])
        if rep["forced"]:
            ax.plot([t[-1]], [asw[-1]], "x", ms=11, mew=2.6, color=C["power"])
        else:
            ax.plot([t[-1]], [asw[-1]], "o", ms=9, color=C["ok"])
    ax.axhline(0, color=C["power"], lw=0.8, ls="--")
    ax.set_xlabel("Time since supply failure (min)")
    ax.set_ylabel("Available stored water ASW (m³)")
    ax.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
    ax.grid(alpha=0.3)

    # (c) 运行时间 vs 降零时长（临界点=峰值）
    ax = axes[2]
    xs = np.array([s["ramp_time_s"] for s in scan]) / 60.0
    ys = np.array([s["T_oper_s"] for s in scan]) / 60.0
    forced_mask = np.array([s["forced_trip"] for s in scan])
    ax.plot(xs[forced_mask], ys[forced_mask], "s-", color=C["PA"], lw=1.8, ms=5,
            label="Forced trip")
    ax.plot(xs[~forced_mask], ys[~forced_mask], "o-", color=C["ok"], lw=1.8, ms=5,
            label="Active stop")
    ax.plot([crit["ramp_time_s"] / 60.0], [crit["T_oper_s"] / 60.0], "*", ms=17,
            color=C["warn"], zorder=5, label="Critical point")
    ax.axhline(SAET_s / 60.0, color=C["muni"], ls="--", lw=1.4,
               label="SAET (no ramp)")
    ax.set_xlabel("Full-load ramp-down time 1/r (min)")
    ax.set_ylabel("Operating time (min)")
    ax.set_title("(c)", fontsize=12, fontweight="bold", loc="left")
    ax.grid(alpha=0.3)

    # ---- 图例(面板内右上): (a)(b) 左列=速率曲线、右列=事件标记(●/✕), (c) 两列 ----
    for ax_ in (axes[0], axes[1]):
        ax_.plot([], [], "o", ms=9, color=C["ok"], ls="none", label="Active stop")
        ax_.plot([], [], "x", ms=11, mew=2.6, color=C["power"], ls="none",
                 label="Forced trip")
    LEG_KW = dict(loc="upper right", frameon=False, columnspacing=1.2,
                  handletextpad=0.5, borderaxespad=0.4, handlelength=2.0)
    axes[0].legend(ncol=2, **LEG_KW)
    axes[1].legend(ncol=2, **LEG_KW)
    axes[2].legend(ncol=2, **LEG_KW)

    fig.tight_layout()
    os.makedirs(os.path.dirname(FIG_OUT), exist_ok=True)
    fig.savefig(FIG_OUT, **figstyle.SAVE)
    print("figure saved:", FIG_OUT)

    # ---- 数据归档 ----
    out = dict(
        bus=BUS, Pg_MW=Pg, Pmax_MW=Pmax, dt_s=DT,
        SAET_min=SAET_s / 60.0, ASW0_m3=stat["ASW0_m3"],
        critical=dict(ramp_time_s=crit["ramp_time_s"],
                      r_per_s=crit["r_per_s"],
                      r_pct_per_min=100 * crit["r_per_s"] * 60,
                      T_oper_min=crit["T_oper_s"] / 60.0),
        scan=scan,
        note="对齐 Yu et al. Nat.Commun. 2024 Fig.3 数值算例（气->水类比）；"
             "市政边界为合成阶跃(B-ST 保守下界)。")
    os.makedirs(os.path.dirname(RES_OUT), exist_ok=True)
    json.dump(out, open(RES_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("results saved:", RES_OUT)


if __name__ == "__main__":
    main()
