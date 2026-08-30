"""
P1 故障机理链仿真驱动
=====================
链条: 市政配水节点压头失效(<28m) -> 补水箱/集水池水位下降
      -> 循环水泵流量下降/汽蚀跳泵 -> 凝汽器背压上升
      -> 高背压保护跳机 -> 机组少发功率

多时间尺度: 慢(水力/热力, 秒~分钟)。采用显式积分打通全链条;
事件(跳泵/跳机)按状态判据触发。本模块产出:
  - 机组跳机时刻(=静态可用逃逸时间 SAET, 早期预警窗口)
  - 受影响机组少发功率 lost(t) = Pg - Pg·k_p (跳机后=Pg)
不计算系统频率(与 ICS/P6 一致, 影响以少发功率衡量; 频率非本研究指标)。
"""
import argparse
import numpy as np
import csv
import os

from params import Params, load_unit_from_gen
import submodels as sm


def run(t_fault=60.0, ramp=0.0, t_end=1200.0, dt=0.05, bus=89, outdir="../../results/cooling_chain"):
    Pg, Pmax = load_unit_from_gen(bus=bus)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)

    # ---- 初始状态(稳态平衡水位, 含液位控制下垂) ----
    H_tank, H_pool = sm.equilibrate_water(p)
    Q_cond = p.Q_cond0

    pump_tripped = False
    gen_tripped = False
    t_pump_trip = None
    t_gen_trip = None
    hi_bp_timer = 0.0                     # 高背压持续计时

    rows = []
    n = int(t_end / dt) + 1
    for i in range(n):
        t = i * dt

        # ---- 子模型 W: 水力 (损失随热负荷 Q_cond 变化) ----
        dHt, dHp, m_cw = sm.water_derivs(t, H_tank, H_pool, pump_tripped, p,
                                         t_fault, ramp, Q_cond_kW=Q_cond)

        # 跳泵判据: 淹没深度不足(NPSH)
        if (not pump_tripped) and H_pool <= p.H_submerge_min:
            pump_tripped = True
            t_pump_trip = t
            m_cw = 0.0

        # ---- 子模型 A: 凝汽器-低压缸 (代数) ----
        T_return_prev = rows[-1]["T_return"] if rows else (p.T_wetbulb + p.tower_approach_K + 8)
        T_cw_in = sm.basin_temp(T_return_prev, m_cw, p)
        p_b, T_return = sm.condenser(m_cw, T_cw_in, Q_cond, p)
        k_p = sm.power_derate(p_b, p)

        # 高背压跳机判据(带延时)
        if p_b >= p.p_b_trip_kPa:
            hi_bp_timer += dt
        else:
            hi_bp_timer = 0.0
        if (not gen_tripped) and hi_bp_timer >= p.trip_delay_s:
            gen_tripped = True
            t_gen_trip = t

        # ---- 机组出力与少发功率 ----
        P_aff = 0.0 if gen_tripped else Pg * k_p     # 机组实际出力 MW
        lost = Pg - P_aff                            # 少发功率 MW

        # 凝汽器热负荷随机械功率(弱耦合): 跳机后残余排汽衰减
        if gen_tripped:
            Q_cond = max(0.0, Q_cond - dt * p.Q_cond0 / 20.0)   # ~20s衰减
        else:
            Q_cond = p.lp_heat_frac * P_aff * 1000.0

        rows.append(dict(t=t, H_tank=H_tank, H_pool=H_pool, m_cw=m_cw,
                         T_cw_in=T_cw_in, T_return=T_return, p_b=p_b, k_p=k_p,
                         Paff_MW=P_aff, lost_MW=lost,
                         pump=int(not pump_tripped), gen=int(not gen_tripped)))

        # ---- 显式推进水位 ----
        H_tank = max(p.H_tank_min, H_tank + dt * dHt)
        H_pool = max(0.0, H_pool + dt * dHp)

        # 跳机后再跑一段展示少发功率, 然后终止
        if gen_tripped and t > (t_gen_trip + 120):
            break

    # ---- 输出 CSV ----
    here = os.path.dirname(os.path.abspath(__file__))
    outpath = os.path.join(here, outdir)
    os.makedirs(outpath, exist_ok=True)
    tag = f"bus{bus}_tf{int(t_fault)}_ramp{int(ramp)}"
    csvfile = os.path.join(outpath, f"p1_smib_{tag}.csv")
    keys = ["t", "H_tank", "H_pool", "m_cw", "T_cw_in", "T_return", "p_b", "k_p",
            "Paff_MW", "lost_MW", "pump", "gen"]
    with open(csvfile, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows[::max(1, int(1.0 / dt))]:   # 每1秒抽稀输出
            w.writerow({k: (round(r[k], 5) if isinstance(r[k], float) else r[k]) for k in keys})

    # ---- 关键事件与指标 ----
    saet = None if t_gen_trip is None else round(t_gen_trip - t_fault, 1)
    summary = dict(bus=bus, Pg=Pg, Pmax=Pmax, t_fault=t_fault, ramp=ramp,
                   t_pump_trip=t_pump_trip, t_gen_trip=t_gen_trip,
                   SAET_s=saet, SAET_min=(None if saet is None else round(saet / 60.0, 1)),
                   pb_max=round(max(r["p_b"] for r in rows), 2),
                   lost_max=round(max(r["lost_MW"] for r in rows), 1),
                   csv=os.path.basename(csvfile))
    return summary, csvfile, rows, p


def _print_summary(s):
    print("=" * 60)
    print(" P1 故障机理链 —— 仿真摘要")
    print("=" * 60)
    print(f" 机组          : bus {s['bus']}  Pg={s['Pg']} / Pmax={s['Pmax']} MW")
    print(f" 故障时刻      : t_fault = {s['t_fault']} s (市政断水, ramp={s['ramp']}s)")
    print(f" 循环水泵跳闸  : {s['t_pump_trip']} s")
    print(f" 机组跳闸      : {s['t_gen_trip']} s")
    print(f" 缓冲窗口 SAET : {s['SAET_s']} s ({s['SAET_min']} min)")
    print(f" 最大背压      : {s['pb_max']} kPa")
    print(f" 最大少发功率  : {s['lost_max']} MW")
    print(f" 结果CSV       : {s['csv']}")
    print("=" * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--t_fault", type=float, default=60.0)
    ap.add_argument("--ramp", type=float, default=0.0, help="市政补水衰减时间s, 0=阶跃")
    ap.add_argument("--t_end", type=float, default=2400.0)
    ap.add_argument("--dt", type=float, default=0.05)
    ap.add_argument("--bus", type=int, default=89)
    a = ap.parse_args()
    s, csvfile, rows, p = run(t_fault=a.t_fault, ramp=a.ramp, t_end=a.t_end, dt=a.dt, bus=a.bus)
    _print_summary(s)
