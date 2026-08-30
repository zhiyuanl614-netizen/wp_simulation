"""
Fig.9  Proactive control (LP + DC power flow): PA / SP / DP comparison.
Reads results/proactive_control/* -> figures/Fig9_PA_SP_DP_strategies.png
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
NAME = {"PA": "Passive (PA)", "SP": "Static proactive (SP)", "DP": "Dynamic proactive (DP)"}


def main():
    summ = json.load(open(os.path.join(RESDIR, "p6_strategy_compare.json")))
    ts = json.load(open(os.path.join(RESDIR, "p6_timeseries.json")))
    res = summ["results"]

    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.2))
    fig.suptitle("Proactive control (LP + DC power flow): passive / static / dynamic",
                 fontsize=12.5)

    a = ax[0]
    for m in ["PA", "SP", "DP"]:
        if m in ts:
            a.plot(ts[m]["t"], ts[m]["deficit"], color=COL[m], label=NAME[m])
    a.set_xlabel("Time (min)"); a.set_ylabel("Power deficit (MW)")
    a.set_title("(a) Power-deficit time series"); a.legend()

    a = ax[1]
    for m in ["PA", "SP", "DP"]:
        if m in ts:
            a.plot(ts[m]["t"], ts[m]["aff_total"], color=COL[m], label=NAME[m])
    a.set_xlabel("Time (min)"); a.set_ylabel("Affected-unit total output (MW)")
    a.set_title("(b) Affected-unit output (proactive = soft landing)"); a.legend()

    a = ax[2]
    modes = ["PA", "SP", "DP"]
    x = np.arange(len(modes)); w = 0.35
    maxdef = [res[m]["max_deficit_MW"] for m in modes]
    energy = [res[m]["energy_deficit_MWh"] for m in modes]
    a.bar(x - w/2, maxdef, w, color=COLORS["power"], label="Max power deficit (MW)")
    a2 = a.twinx(); a2.grid(False)
    a2.bar(x + w/2, energy, w, color=COLORS["muni"], label="Total energy deficit (MWh)")
    a.set_xticks(x); a.set_xticklabels(["PA", "SP", "DP"])
    a.set_ylabel("Max power deficit (MW)", color=COLORS["power"])
    a2.set_ylabel("Total energy deficit (MWh)", color=COLORS["muni"])
    a.set_title("(c) Key metrics")
    for i in range(len(modes)):
        a.text(x[i]-w/2, maxdef[i], f"{maxdef[i]:.0f}", ha="center", va="bottom", fontsize=8)
        a2.text(x[i]+w/2, energy[i], f"{energy[i]:.1f}", ha="center", va="bottom", fontsize=8)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(FIG, "Fig9_PA_SP_DP_strategies.png"), **SAVE)
    plt.close(fig)
    print("saved Fig9")


if __name__ == "__main__":
    main()
