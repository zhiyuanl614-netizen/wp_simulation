"""
Fig.10  Proactive control (LP + DC power flow): PA / SP / DP comparison.
Reads results/proactive_control/* -> figures/Fig10_PA_SP_DP_strategies.png
校准 v2 (2026-09-02, 用户指令: 1x3 略显拥挤 + 图例遮挡内容 + (c) 双Y轴换法):
- 画布 1x3 (14x5.0) -> 2x2 (12.5x8.4, 与 Fig9 2x2 一致);
- 原 (c) 双 Y 轴分组柱状图拆分为两个单指标面板: (c) 峰值功率缺额 / (d) 损失
  电量, 恰好填满 2x2;
- 柱色改策略色 (PA/SP/DP 与 (a)(b) 曲线同色——颜色=策略、面板=指标; 原双 Y 轴
  的指标色语义由拆分后的 y 轴标签承担);
- 数值标签 8 -> 12 号 (统一字号规范), y 轴留 18% 顶部余量防裁切;
- 图例定点放置: (a) upper left (t<88.6 min 三策略缺额恒 0 的空带) /
  (b) upper right (t>150 min 三策略出力均归 0 的空带), 几何核验零覆盖;
- 图例标签精简为策略代码 PA/SP/DP (与 (c)(d) 柱状 x 刻度一致、颜色绑定;
  全称由图注定义)——初版全称图例右缘压 (a) 的 PA 尖峰点 (t=90 min, 343 MW),
  短代码后图例宽度 ~0.2 轴宽, 完全避开。
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "..", "results", "proactive_control")
FIG = os.path.join(HERE, "..", "..", "figures")
COL = {"PA": COLORS["PA"], "SP": COLORS["SP"], "DP": COLORS["muni"]}


def main():
    summ = json.load(open(os.path.join(RESDIR, "p6_strategy_compare.json")))
    ts = json.load(open(os.path.join(RESDIR, "p6_timeseries.json")))
    res = summ["results"]

    fig, ax = plt.subplots(2, 2, figsize=(12.5, 8.4))

    # (a) 系统功率缺额时序
    a = ax[0, 0]
    for m in ["PA", "SP", "DP"]:
        if m in ts:
            a.plot(ts[m]["t"], ts[m]["deficit"], color=COL[m], label=m)
    a.set_xlabel("Time (min)"); a.set_ylabel("Power deficit (MW)")
    a.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    a.legend(loc="upper left")

    # (b) 受影响机组总出力
    a = ax[0, 1]
    for m in ["PA", "SP", "DP"]:
        if m in ts:
            a.plot(ts[m]["t"], ts[m]["aff_total"], color=COL[m], label=m)
    a.set_xlabel("Time (min)"); a.set_ylabel("Affected-unit total output (MW)")
    a.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
    a.legend(loc="upper right")

    # (c)/(d) 原 (c) 双 Y 轴拆分: 单指标柱状图, 柱色=策略色(与线色一致)
    modes = ["PA", "SP", "DP"]
    x = np.arange(len(modes))
    panels = [("max_deficit_MW", "Max power deficit (MW)", "(c)", "%.0f"),
              ("energy_deficit_MWh", "Total energy deficit (MWh)", "(d)", "%.1f")]
    for j, (key, ylab, ttl, fmt) in enumerate(panels):
        a = ax[1, j]
        vals = [res[m][key] for m in modes]
        a.bar(x, vals, 0.55, color=[COL[m] for m in modes])
        a.set_xticks(x); a.set_xticklabels(modes)
        a.set_ylabel(ylab)
        a.set_title(ttl, fontsize=12, fontweight="bold", loc="left")
        a.set_ylim(0, max(vals) * 1.18 if max(vals) > 0 else 1.0)
        for xi, v in zip(x, vals):
            a.text(xi, v, fmt % v, ha="center", va="bottom", fontsize=12)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Fig10_PA_SP_DP_strategies.png"), **SAVE)
    plt.close(fig)
    print("saved Fig10")


if __name__ == "__main__":
    main()
