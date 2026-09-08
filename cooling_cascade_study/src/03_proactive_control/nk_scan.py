"""
② 电侧 N-k 跳闸扫描 (耦合发电机组合失效)
==========================================
总体: 在 54 个耦合发电机中, 取【有出力】的 19 台 (Pg>0; Pg=0 机组跳闸对功率
平衡无影响, 仅拓扑/预警意义, 见 docs/coupling_map.md §6) 作总体;
k = 1,2,3,6,9,12; 每 k: 最坏子集(按 Pg 降序 top-k) + 3 个固定种子随机子集。

每子集两策略 (ProactiveLP, DC 潮流, horizon 200 min / dt 5 min):
  PA 被动  : 机组按水力跳机轨迹被动退出, 缺额事后由备用补 (受爬坡限制)
  SP 主动  : 以各机 SAET 为控制时间提前软着陆 (早期预警的边际价值)

指标: 可行? / 最大功率缺额 MW / 总能量缺额 MWh / 失去出力 MW。
输出: results/proactive_control/nk_scan.json + nk_scan.csv
"""
import os, sys, json, csv, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from proactive_lp import ProactiveLP, critical_indicators

RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
CMAP = os.path.join(HERE, "..", "..", "results", "muni", "coupling_map.json")

HORIZON, DT = 200.0, 5.0
KS = [1, 2, 3, 6, 9, 12]
N_RAND = 3


def population():
    rows = json.load(open(CMAP))["map"]
    pop = [r for r in rows if r["Pg_MW"] > 0.0]
    return sorted(pop, key=lambda r: -r["Pg_MW"])


def subsets_for(k, pop):
    worst = [r["bus"] for r in pop[:k]]
    rng = np.random.default_rng(1000 + k)
    buses = [r["bus"] for r in pop]
    out = [("worst", worst)]
    for i in range(N_RAND):
        out.append((f"rand{i}", [int(b) for b in rng.choice(buses, size=k, replace=False)]))
    return out


def evaluate(sub, tag, k):
    buses = list(sub)
    rec = dict(k=k, subset=tag, buses=sorted(buses))
    lp = ProactiveLP(affected_buses=buses, horizon_min=HORIZON, dt_min=DT)
    lost = float(sum(lp.Pg0[gi] for gi in lp.aff_idx))
    rec["lost_MW"] = round(lost, 1)
    saet = critical_indicators(buses)
    for mode, Tc in [("PA", None), ("SP", saet)]:
        t0 = time.time()
        r = lp.solve(mode=mode, T_ctrl=Tc)
        dt_s = time.time() - t0
        if r["feasible"]:
            rec[f"{mode}_feasible"] = True
            rec[f"{mode}_maxdef_MW"] = round(r["max_deficit_MW"], 1)
            rec[f"{mode}_energy_MWh"] = round(r["energy_deficit_MWh"], 1)
        else:
            rec[f"{mode}_feasible"] = False
            rec[f"{mode}_maxdef_MW"] = None
            rec[f"{mode}_energy_MWh"] = None
        rec[f"{mode}_s"] = round(dt_s, 1)
    return rec


if __name__ == "__main__":
    pop = population()
    print("有出力耦合机组 %d 台; 总出力 %.0f MW" %
          (len(pop), sum(r["Pg_MW"] for r in pop)))
    rows = []
    for k in KS:
        for tag, sub in subsets_for(k, pop):
            rec = evaluate(sub, tag, k)
            rows.append(rec)
            pa = rec.get("PA_energy_MWh")
            sp = rec.get("SP_energy_MWh")
            print(" k=%2d %-6s lost=%6.0f MW | PA: %s %s MWh | SP: %s %s MWh"
                  % (k, tag, rec["lost_MW"],
                     "ok" if rec["PA_feasible"] else "INF",
                     pa if pa is not None else "-",
                     "ok" if rec["SP_feasible"] else "INF",
                     sp if sp is not None else "-"))
    os.makedirs(RES, exist_ok=True)
    json.dump(rows, open(os.path.join(RES, "nk_scan.json"), "w"), ensure_ascii=False,
              indent=1)
    keys = []
    for r in rows:
        for kk in r:
            if kk not in keys:
                keys.append(kk)
    with open(os.path.join(RES, "nk_scan.csv"), "w", newline="") as f:
        wd = csv.DictWriter(f, fieldnames=keys)
        wd.writeheader()
        for r in rows:
            wd.writerow({kk: r.get(kk) for kk in keys})
    # ---- 汇总: 随 k 的标度 ----
    print("\n== 随 k 标度 (最坏子集) ==")
    for k in KS:
        w = [r for r in rows if r["k"] == k and r["subset"] == "worst"][0]
        print(" k=%2d lost=%5.0f MW  PA能量缺额 %s MWh  SP能量缺额 %s MWh"
              % (k, w["lost_MW"],
                 w["PA_energy_MWh"] if w["PA_energy_MWh"] is not None else "不可行",
                 w["SP_energy_MWh"] if w["SP_energy_MWh"] is not None else "不可行"))
    print("saved nk_scan.json / nk_scan.csv")
