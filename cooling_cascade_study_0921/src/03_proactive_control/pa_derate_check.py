"""
PA 阶跃失电 vs 水力降额轨迹 复算实验 (评审 M5 补充实验)
======================================================
LP 的 PA 被动轨迹为 P_avail = Pg0·1[t < τ_i + t_trip,i] (满出力直至跳机,
瞬时归零)。物理链(Fig.7)显示跳机前存在 ~20 min 的背压降额段(k_p<1)。
本实验用统一语义(v3, 评审M1-A)前向积分得到的 k_p(t) 轨迹替换阶跃
(proactive_lp pa_traj="derate"), 复算 run_p6 CO 一例, 报告 PA 峰值/能量/
过载差异, 检验"阶跃简化是否偏保守"(峰值被最大化)。

实现: ProactiveLP(pa_traj="derate") (v3 附加参, 默认 "step" 与注册口径
逐字节等价); CO 场景(六机同源同时, 300 min 时域, DC-PTDF, R=0.01)。

输出: results/proactive_control/pa_derate_check.json
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from proactive_lp import ProactiveLP, critical_indicators   # noqa

RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
BUSES = [89, 80, 10, 66, 65, 26]


def solve(pa_traj):
    saet = critical_indicators(BUSES)
    lp = ProactiveLP(affected_buses=BUSES, horizon_min=300.0, dt_min=5.0,
                     enforce_dc=True, ramp_frac_per_min=0.01,
                     muni_offset_min=[0.0] * len(BUSES), pa_traj=pa_traj)
    r = lp.solve(mode="PA", T_ctrl=None)
    return dict(pa_traj=pa_traj,
                max_deficit_MW=round(float(r["max_deficit_MW"]), 2),
                energy_deficit_MWh=round(float(r["energy_deficit_MWh"]), 2),
                max_overload_MW=round(float(r["max_overload_MW"]), 2),
                feasible=bool(r["feasible"]))


def main():
    print("=" * 84)
    print(" PA 阶跃 vs 降额轨迹 复算 (CO 六机, 300 min, DC, R=0.01; 评审 M5)")
    print("=" * 84)
    step = solve("step")
    print(" [step  ] PA 峰值 %7.1f MW  能量 %7.1f MWh  过载 %6.1f MW"
          % (step["max_deficit_MW"], step["energy_deficit_MWh"], step["max_overload_MW"]))
    derate = solve("derate")
    print(" [derate] PA 峰值 %7.1f MW  能量 %7.1f MWh  过载 %6.1f MW"
          % (derate["max_deficit_MW"], derate["energy_deficit_MWh"], derate["max_overload_MW"]))
    dp = dict(peak_dMW=round(derate["max_deficit_MW"] - step["max_deficit_MW"], 2),
              energy_dMWh=round(derate["energy_deficit_MWh"] - step["energy_deficit_MWh"], 2),
              overload_dMW=round(derate["max_overload_MW"] - step["max_overload_MW"], 2))
    print("-" * 84)
    print(" 差异 (derate - step): 峰值 %+.1f MW, 能量 %+.1f MWh, 过载 %+.1f MW"
          % (dp["peak_dMW"], dp["energy_dMWh"], dp["overload_dMW"]))
    print(" 阶跃简化偏保守(峰值更高): %s" % bool(step["max_deficit_MW"] >= derate["max_deficit_MW"]))
    print("=" * 84)
    out = dict(version="v3", date="2026-09-20", buses=BUSES, horizon_min=300.0,
               dt_min=5.0, ramp_frac_per_min=0.01, mode="PA",
               semantics="统一热负荷口径(评审M1-A); derate=Pg·k_p(t) 轨迹(前向积分)",
               step=step, derate=derate, diff=dp,
               step_is_conservative_peak=bool(step["max_deficit_MW"] >= derate["max_deficit_MW"]))
    os.makedirs(RES, exist_ok=True)
    path = os.path.join(RES, "pa_derate_check.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved", path)


if __name__ == "__main__":
    main()
