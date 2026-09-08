"""
Fig.11  电侧 N-k 跳闸扫描 (耦合发电机组合失效, PA vs SP)
=========================================================
(a) 最坏子集 (Pg top-k) 标度: 能量缺额 MWh (PA/SP) + 失去出力 MW (右轴);
(b) 全部子集 (最坏+3随机) 能量缺额分布, PA vs SP。
数据: results/proactive_control/nk_scan.json
输出: figures/Fig11_nk_scaling.png (300 dpi)
校准 v2 (2026-09-02, 用户指令: 规范字体/图例, 同前序图件):
- 面板序号由轴内 ax.text 改标准 set_title(loc="left") 加粗 12 号左上(轴外);
- (b) 轴内注记 "SP zero-deficit: n/24" 9.5 号违规 -> 移入图注(18/24), 轴内
  只留图例(upper left, 数据最高点 y-frac 0.69 之下净空);
- (a) 双图例(轴 upper left + twinx lower right)合并为单图例 4 条目置于
  lower right——左上/左中带被 k=3 的 112 MWh 点与 lost 虚线斜穿, 右下带
  (k>=7.6, y<0.30) 为唯一净空区; lost 条目注明 (right axis);
- twinx 补 grid(False)(防双网格叠加) 并显示右轴脊(中性色);
- 轴标签首字母大写, 与 Fig10 等一致。
数据核实 (2026-09-02): 复跑 nk_scan.py 24 条数据字段零差异(仅 LP 求解耗时
字段 _s 随机器浮动); SP 零缺额 18/24; k*=3 边界: k<=2 全 0/0, k>=3 最坏
残留 95.6-128.2 MWh; k=3 worst = [69, 80, 89] (Pg top-3)。
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import figstyle  # noqa
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "..", "..", "results", "proactive_control",
                                   "nk_scan.json")))
OUT = os.path.join(HERE, "..", "..", "figures", "Fig11_nk_scaling.png")

KS = sorted({r["k"] for r in rows})
worst = {r["k"]: r for r in rows if r["subset"] == "worst"}

fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.0, 5.2))

# ---------------- (a) worst-case scaling ----------------
kw = KS
pa = [worst[k]["PA_energy_MWh"] or 0.0 for k in kw]
sp = [worst[k]["SP_energy_MWh"] or 0.0 for k in kw]
lost = [worst[k]["lost_MW"] for k in kw]
axA.plot(kw, pa, "o-", color=COLORS["PA"], label="PA (passive)")
axA.plot(kw, sp, "s-", color=COLORS["SP"], label="SP (proactive, SAET)")
axA.fill_between(kw, sp, pa, color=COLORS["ok"], alpha=0.15,
                 label="deficit avoided by warning")
axA.set_xlabel("k (coupled generators tripped, worst case)")
axA.set_ylabel("Energy deficit (MWh)")
axA.set_xticks(kw)
axA.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
axB2 = axA.twinx()
axB2.grid(False)                                   # v2: 防双网格叠加
axB2.plot(kw, lost, "v--", color=COLORS["mut"], lw=1.2, markersize=5,
          label="lost capacity (right axis)")
axB2.set_ylabel("Lost capacity (MW)", color=COLORS["mut"])
axB2.tick_params(colors=COLORS["mut"])
axB2.spines["right"].set_visible(True)             # v2: 右轴脊可见以标示副轴
axB2.spines["right"].set_color(COLORS["mut"])
# v2: 双图例合并为单图例 4 条目, 置 lower right (唯一净空带)
h1, l1 = axA.get_legend_handles_labels()
h2, l2 = axB2.get_legend_handles_labels()
axA.legend(h1 + h2, l1 + l2, loc="lower right", frameon=True)

# ---------------- (b) all subsets ----------------
rng = np.random.default_rng(7)
for side, key, col, mk in [(0, "PA_energy_MWh", COLORS["PA"], "o"),
                           (1, "SP_energy_MWh", COLORS["SP"], "s")]:
    for k in KS:
        vals = [r[key] or 0.0 for r in rows if r["k"] == k]
        x = k + (side - 0.5) * 0.28 + rng.uniform(-0.05, 0.05, len(vals))
        axB.scatter(x, vals, s=30, color=col, marker=mk, edgecolor="k",
                    linewidths=0.5, zorder=3)
    axB.scatter([], [], s=30, color=col, marker=mk, edgecolor="k", linewidths=0.5,
                label="PA (passive)" if side == 0 else "SP (proactive)")
axB.axhline(0, color="#33414d", lw=0.7)
axB.set_xlabel("k (coupled generators tripped)")
axB.set_ylabel("Energy deficit (MWh)")
axB.set_xticks(KS)
axB.set_title("(b)", fontsize=12, fontweight="bold", loc="left")
axB.legend(loc="upper left", frameon=True)

fig.tight_layout()
fig.savefig(OUT, **SAVE)
plt.close(fig)
print("saved", os.path.abspath(OUT))
