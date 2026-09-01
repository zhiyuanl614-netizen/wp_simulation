"""
Fig.12  电侧 N-k 跳闸扫描 (耦合发电机组合失效, PA vs SP)
=========================================================
(a) 最坏子集 (Pg top-k) 标度: 能量缺额 MWh (PA/SP) + 失去出力 MW (右轴);
(b) 全部子集 (最坏+3随机) 能量缺额分布, PA vs SP; 标注 SP 完全吸收比例。
数据: results/proactive_control/nk_scan.json
输出: figures/Fig12_nk_scaling.png (300 dpi)
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
OUT = os.path.join(HERE, "..", "..", "figures", "Fig12_nk_scaling.png")

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
axA.set_ylabel("energy deficit (MWh)")
axA.set_xticks(kw)
axA.legend(loc="upper left", frameon=True)
axB2 = axA.twinx()
axB2.plot(kw, lost, "v--", color=COLORS["mut"], lw=1.2, markersize=5,
          label="lost capacity")
axB2.set_ylabel("lost capacity (MW)", color=COLORS["mut"])
axB2.tick_params(colors=COLORS["mut"])
axB2.legend(loc="lower right", frameon=True)
axA.text(0.02, 0.97, "(a)", transform=axA.transAxes, fontsize=12,
         fontweight="bold", va="top")

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
nz = sum(1 for r in rows if (r["SP_energy_MWh"] or 0) == 0)
axB.axhline(0, color="#33414d", lw=0.7)
axB.set_xlabel("k (tripped coupled generators)")
axB.set_ylabel("energy deficit (MWh)")
axB.set_xticks(KS)
axB.legend(loc="upper left", frameon=True)
axB.text(0.98, 0.97, f"SP zero-deficit: {nz}/{len(rows)} contingencies",
         transform=axB.transAxes, ha="right", va="top", fontsize=9.5,
         bbox=dict(boxstyle="round", fc="white", ec=COLORS["ok"], alpha=0.9))
axB.text(0.02, 0.97, "(b)", transform=axB.transAxes, fontsize=12,
         fontweight="bold", va="top")

fig.tight_layout()
fig.savefig(OUT, **SAVE)
plt.close(fig)
print("saved", os.path.abspath(OUT))
