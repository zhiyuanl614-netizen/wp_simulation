"""
Fig.8  Early-warning comparison (WARN vs NOWARN).
Detection signal = municipal supply pressure; impact = power loss (MW) / energy loss (MWh).
(a) municipal head & detection  (b) pool level  (c) back-pressure  (d) power deficit
Reads results/ics/* -> figures/Fig8_early_warning_comparison.png
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "..", "results", "ics")
FIG = os.path.join(HERE, "..", "..", "figures")

CASES = {"WARN": "With early warning", "NOWARN": "No warning (passive)"}
COL = {"WARN": COLORS["muni"], "NOWARN": COLORS["power"]}


def main():
    ts = json.load(open(os.path.join(RESDIR, "ics_timeseries.json")))
    summ = json.load(open(os.path.join(RESDIR, "ics_warning_compare.json")))

    fig, ax = plt.subplots(2, 2, figsize=(12.5, 8.4))

    tW = np.array(ts["WARN"]["t"]) / 60

    a = ax[0, 0]
    a.plot(tW, ts["WARN"]["muni"], color=COLORS["mut"], label="Municipal supply head")
    a.axhline(28.0, color="red", ls="--", lw=1, label="Min. threshold 28 m (failure/warning)")
    dt_ = summ["WARN"]["detect_t"]
    if dt_ is not None:
        a.axvline(dt_ / 60, color=COL["WARN"], ls=":", lw=1.8,
                  label=f"Detection/warning {dt_/60:.1f} min")
    a.set_title("(a)", fontsize=12, fontweight="bold", loc="left")
    a.set_ylabel("Head (m)"); a.set_xlabel("Time (min)"); a.legend(fontsize=8.5)

    a = ax[0, 1]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["H_pool"], color=COL[k], label=CASES[k])
    a.axhline(1.2, color="red", ls=":", lw=1, label="Pump-trip submergence 1.2 m")
    a.set_title("(b)", fontsize=12, fontweight="bold", loc="left"); a.set_ylabel("Level (m)"); a.set_xlabel("Time (min)")
    a.legend(fontsize=8.5)

    a = ax[1, 0]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["p_b"], color=COL[k], label=CASES[k])
    a.axhline(15.0, color="red", ls="--", lw=1, label="Hi-back-pressure trip 15 kPa")
    a.set_title("(c)", fontsize=12, fontweight="bold", loc="left")
    a.set_ylabel("Back-pressure (kPa)"); a.set_xlabel("Time (min)"); a.legend(fontsize=8.5)

    a = ax[1, 1]
    for k in ["WARN", "NOWARN"]:
        a.plot(np.array(ts[k]["t"]) / 60, ts[k]["deficit"], color=COL[k],
               label=f"{CASES[k]}\n(peak {summ[k]['max_deficit_MW']:.0f} MW / "
                     f"{summ[k]['energy_deficit_MWh']:.1f} MWh)")
    a.set_title("(d)", fontsize=12, fontweight="bold", loc="left")
    a.set_ylabel("Power deficit (MW)"); a.set_xlabel("Time (min)"); a.legend(fontsize=8)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(FIG, "Fig8_early_warning_comparison.png"), **SAVE)
    plt.close(fig)
    print("saved Fig8")


if __name__ == "__main__":
    main()
