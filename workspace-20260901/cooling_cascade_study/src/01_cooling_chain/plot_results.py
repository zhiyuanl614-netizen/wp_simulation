"""
Fig.7  Cooling-water fault mechanism chain (time series).
water level -> circulating flow -> back-pressure -> derating -> output / power loss
Reads results/cooling_chain/p1_smib_*.csv
 -> writes figures/Fig7_cooling_chain_timeseries.png (ramp0 case only)
"""
import os, sys, csv
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
import figstyle
from figstyle import COLORS, SAVE
import matplotlib.pyplot as plt

C = {"w": COLORS["muni"], "p": COLORS["ok"], "b": COLORS["power"],
     "f": "#8b3a62", "k": COLORS["amber"]}
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "figures")


def load_csv(path):
    d = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                d.setdefault(k, []).append(float(v))
    return {k: np.array(v) for k, v in d.items()}


def plot_one(path, t_fault=60.0, also_fig=False):
    d = load_csv(path)
    t = d["t"] / 60.0
    tf = t_fault / 60.0

    fig, ax = plt.subplots(3, 2, figsize=(12, 9.2))
    def mark(a):
        a.axvline(tf, color=COLORS["mut"], ls=":", lw=1)

    a = ax[0, 0]
    a.plot(t, d["H_tank"], color=C["w"], label="Make-up tank $H_{tank}$")
    a.plot(t, d["H_pool"], color=C["p"], label="Pool $H_{pool}$")
    a.set_ylabel("Water level (m)"); a.set_title("(a)", fontsize=12, fontweight="bold", loc="left"); a.legend(); mark(a)

    a = ax[0, 1]
    a.plot(t, d["m_cw"], color=C["w"])
    a.set_ylabel("$m_{cw}$ (m$^3$/s)"); a.set_title("(b)", fontsize=12, fontweight="bold", loc="left"); mark(a)

    a = ax[1, 0]
    a.plot(t, d["p_b"], color=C["b"])
    a.axhline(15.0, color="red", ls="--", lw=1, label="Hi-back-pressure trip 15 kPa")
    a.axhline(5.0, color="green", ls=":", lw=1, label="Design back-pressure 5 kPa")
    a.set_ylabel("Back-pressure (kPa)"); a.set_title("(c)", fontsize=12, fontweight="bold", loc="left"); a.legend(); mark(a)

    a = ax[1, 1]
    a.plot(t, d["k_p"], color=C["k"])
    a.set_ylabel("$k_p$"); a.set_title("(d)", fontsize=12, fontweight="bold", loc="left"); a.set_ylim(0, 1.1); mark(a)

    a = ax[2, 0]
    a.plot(t, d["Paff_MW"], color=C["b"])
    a.set_ylabel("Output (MW)"); a.set_xlabel("Time (min)")
    a.set_title("(e)", fontsize=12, fontweight="bold", loc="left"); mark(a)

    a = ax[2, 1]
    a.plot(t, d["lost_MW"], color=C["f"])
    a.set_ylabel("Power loss (MW)"); a.set_xlabel("Time (min)")
    a.set_title("(f)", fontsize=12, fontweight="bold", loc="left"); mark(a)

    fig.tight_layout()
    if also_fig:
        fig.savefig(os.path.join(FIG, "Fig7_cooling_chain_timeseries.png"), **SAVE)
        print("saved Fig7 <-", os.path.basename(path))
    plt.close(fig)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    resdir = os.path.join(here, "..", "..", "results", "cooling_chain")
    args = sys.argv[1:]
    if args:
        files = [os.path.join(resdir, a) for a in args]
    else:
        files = [os.path.join(resdir, f) for f in os.listdir(resdir)
                 if f.startswith("p1_smib_") and f.endswith(".csv")]
    for f in sorted(files):
        tf = 60.0
        for part in os.path.basename(f).split("_"):
            if part.startswith("tf"):
                try: tf = float(part[2:])
                except: pass
        # ramp0 case is the canonical Fig.7
        plot_one(f, t_fault=tf, also_fig=("ramp0" in os.path.basename(f)))
