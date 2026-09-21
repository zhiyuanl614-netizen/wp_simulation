#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投稿用 Graphical Abstract (Applied Energy, Elsevier 规范: 单栏, 最小 531x1328 px).
输出 figures/GraphicalAbstract_AppliedEnergy.png, 13.28x5.31 in @200dpi = 2656x1062 px.
三联: (a) CO 场景 PA/SP 系统缺额 (预警消除); (b) 六机 SUET 窗 + r* 延伸; (c) SP 适用边界 R*."""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import figstyle
figstyle.apply()
C = figstyle.COLORS

RES = os.path.join(ROOT, "results", "proactive_control")
ts = json.load(open(os.path.join(RES, "p6_timeseries.json")))
rs = json.load(open(os.path.join(RES, "ramp_rate_scan.json")))

fig, axes = plt.subplots(1, 3, figsize=(13.28, 5.31),
                         gridspec_kw=dict(width_ratios=[1.25, 1.0, 1.0], wspace=0.30))

# ---- (a) PA vs SP 系统缺额 ----
ax = axes[0]
t = np.array(ts["PA"]["t"]) / 60.0
d = np.array(ts["PA"]["deficit"])
ax.fill_between(t, 0, d, color=C["PA"], alpha=0.85, lw=0)
ax.plot(t, d, color=C["PA"], lw=1.6)
ax.axhline(0, color=C["SP"], lw=2.4)
ax.annotate("Passive (no warning)\npeak 334.9 MW, 59.6 MWh", xy=(95, 334.9), xytext=(150, 290),
            fontsize=10.5, color=C["PA"],
            arrowprops=dict(arrowstyle="->", color=C["PA"], lw=1.2))
ax.text(0.985, 0.06, "With early warning: 0 MW deficit (SP)", transform=ax.transAxes,
        ha="right", fontsize=10.5, color=C["SP"], fontweight="bold")
ax.set_xlabel("Time after municipal failure (min)", fontsize=11)
ax.set_ylabel("System power deficit (MW)", fontsize=11)
ax.set_title("(a) Six-unit common-origin loss", fontsize=12, fontweight="bold", loc="left")
ax.set_xlim(0, 300); ax.set_ylim(0, 400)
ax.spines[["top", "right"]].set_visible(False)

# ---- (b) SUET 窗 + r* 延伸 ----
ax = axes[1]
buses = ["89", "80", "10", "66", "65", "26"]
suet = [92.4, 121.8, 130.0, 151.5, 151.9, 192.9]
y = np.arange(len(buses))
ax.barh(y, suet, height=0.62, color=C["cool"], alpha=0.9)
ax.barh(y[0], 183.3 - 92.4, left=92.4, height=0.62, color=C["amber"], alpha=0.9,
        hatch="//", edgecolor="white", lw=0.5)
for yi, s in zip(y, suet):
    ax.text(s + 4, yi, f"{s:.1f}", va="center", fontsize=10, color=C["mut"])
ax.text(183.3 + 6, 0, "1.98× via r*", va="center", fontsize=10.5,
        color=C["amber"], fontweight="bold")
ax.set_yticks(y, [f"bus {b}" for b in buses], fontsize=10.5)
ax.set_xlabel("Cooling-buffer window SUET (min)", fontsize=11)
ax.set_title("(b) Plant cooling buffers", fontsize=12, fontweight="bold", loc="left")
ax.set_xlim(0, 245)
ax.spines[["top", "right"]].set_visible(False)

# ---- (c) SP 适用边界 R* ----
ax = axes[2]
rows = [r for r in rs["rows"] if r["scenario"] == "S2_CO_6unit" and r["mode"] in ("PA", "SP")]
for mode, col in [("PA", C["PA"]), ("SP", C["SP"])]:
    rr = sorted([r for r in rows if r["mode"] == mode], key=lambda r: r["R_per_min"])
    ax.plot([r["R_per_min"] for r in rr], [r["energy_deficit_MWh"] for r in rr],
            "o-", color=col, lw=1.8, ms=5, label=mode)
ax.axvspan(0.0035, 0.005, color=C["mut"], alpha=0.15)
ax.annotate(r"$R^{*}\in(0.0035,0.005]$", xy=(0.0042, 300), fontsize=11,
            ha="center", color=C["mut"], fontweight="bold")
ax.axvline(0.01, color=C["mut"], ls=":", lw=1.3)
ax.text(0.01, 900, " baseline R", fontsize=9.5, color=C["mut"])
ax.set_xscale("log"); ax.set_yscale("symlog", linthresh=1)
ax.set_xlabel(r"Reserve ramp rate $R$ (p.u. $P_{\max}$/min)", fontsize=11)
ax.set_ylabel("Energy deficit (MWh)", fontsize=11)
ax.set_title("(c) Applicability boundary", fontsize=12, fontweight="bold", loc="left")
ax.legend(fontsize=10.5, frameon=False, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)

fig.suptitle("Early warning turns the plant cooling-water buffer into grid resilience",
             fontsize=14.5, fontweight="bold", y=0.99)
out = os.path.join(ROOT, "figures", "GraphicalAbstract_AppliedEnergy.png")
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
from PIL import Image
im = Image.open(out)
print("saved", out, im.size, "px")
