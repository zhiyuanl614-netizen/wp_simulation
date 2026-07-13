"""
P1 SMIB 最小闭环仿真驱动
========================
链条: 市政水网故障 -> 补水箱/集水池水位下降 -> 循环水泵流量下降/汽蚀跳泵
      -> 凝汽器背压上升 -> 高背压保护跳机 -> 单机(孤岛)频率响应

多时间尺度: 慢(水力/热力, 秒~分钟) + 快(机电, 毫秒~秒)。
采用统一显式积分(RK4, 小步长)打通全链条; 事件(跳泵/跳机)按状态判据触发。
准稳态解耦: 每步先解水力->热力(代数)->再推进机电。适合机理揭示。
"""
import argparse
import numpy as np
import csv
import os

from params import Params, load_unit_from_gen, tsat_from_p
import submodels as sm


def run(t_fault=60.0, ramp=0.0, t_end=1200.0, dt=0.05, bus=89, outdir="../results"):
    Pg, Pmax = load_unit_from_gen(bus=bus)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)

    # ---- 系统等值(MW制) ----
    sys = sm.system_setup(p)

    # ---- 初始状态 ----
    H_tank, H_pool = sm.equilibrate_water(p)   # 稳态平衡初值(含液位控制下垂)
    f = p.f0
    P_aff_gov = sys["P_aff0"]            # 受影响机组机械功率 MW
    P_rest_gov = sys["P_rest0"]          # 其余部分机械功率 MW
    Q_cond = p.Q_cond0
    load_shed_frac = 0.0                 # 累计UFLS减载比例

    pump_tripped = False
    gen_tripped = False
    t_pump_trip = None
    t_gen_trip = None
    ufls_fired = [False] * len(p.ufls_steps)
    hi_bp_timer = 0.0                     # 高背压持续计时

    rows = []
    n = int(t_end / dt) + 1
    for i in range(n):
        t = i * dt

        # ---- 子模型 W: 水力 (代数+慢动态; 损失随热负荷 Q_cond 变化) ----
        dHt, dHp, m_cw = sm.water_derivs(t, H_tank, H_pool, pump_tripped, p,
                                         t_fault, ramp, Q_cond_kW=Q_cond)

        # 跳泵判据: 淹没深度不足(NPSH)
        if (not pump_tripped) and H_pool <= p.H_submerge_min:
            pump_tripped = True
            t_pump_trip = t
            m_cw = 0.0

        # ---- 子模型 A: 凝汽器-低压缸 (代数) ----
        T_return_prev = rows[-1][ "T_return"] if rows else (p.T_wetbulb + p.tower_approach_K + 8)
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

        # UFLS 低频减载(分级, 一次性触发)
        for si, (f_th, shed) in enumerate(p.ufls_steps):
            if (not ufls_fired[si]) and f <= f_th:
                ufls_fired[si] = True
                load_shed_frac = min(0.9, load_shed_frac + shed)

        # ---- 子模型 B: 机电 (快动态, MW制) ----
        dfdt, dP_aff, dP_rest, P_mech, P_load = sm.mech_derivs_mw(
            f, P_aff_gov, P_rest_gov, load_shed_frac, k_p, gen_tripped, sys, p)
        P_aff = 0.0 if gen_tripped else P_aff_gov * k_p

        # 凝汽器热负荷随机械功率(弱耦合): 跳机后残余排汽衰减
        if gen_tripped:
            Q_cond = max(0.0, Q_cond - dt * p.Q_cond0 / 20.0)   # ~20s衰减
        else:
            Q_cond = p.lp_heat_frac * P_aff * 1000.0

        rows.append(dict(t=t, H_tank=H_tank, H_pool=H_pool, m_cw=m_cw,
                         T_cw_in=T_cw_in, T_return=T_return, p_b=p_b, k_p=k_p,
                         f=f, Paff_MW=P_aff, Prest_MW=P_rest_gov,
                         Pmech_MW=P_mech, Pload_MW=P_load,
                         shed=round(load_shed_frac,3),
                         pump=int(not pump_tripped), gen=int(not gen_tripped)))

        # ---- 显式推进(欧拉, dt小) ----
        H_tank = max(p.H_tank_min, H_tank + dt * dHt)
        H_pool = max(0.0, H_pool + dt * dHp)
        f = f + dt * dfdt
        P_aff_gov = min(max(P_aff_gov + dt * dP_aff, 0.0), sys["P_aff_rated"])
        P_rest_gov = min(max(P_rest_gov + dt * dP_rest, 0.0), sys["P_rest_rated"]*1.2)

        # 系统欠频崩溃保护 / 终止
        if f <= p.f_uf_trip:
            # 记录崩溃时刻并终止(级联失控)
            break

    # ---- 输出 CSV ----
    here = os.path.dirname(os.path.abspath(__file__))
    outpath = os.path.join(here, outdir)
    os.makedirs(outpath, exist_ok=True)
    tag = f"bus{bus}_tf{int(t_fault)}_ramp{int(ramp)}"
    csvfile = os.path.join(outpath, f"p1_smib_{tag}.csv")
    keys = ["t","H_tank","H_pool","m_cw","T_cw_in","T_return","p_b","k_p","f",
            "Paff_MW","Prest_MW","Pmech_MW","Pload_MW","shed","pump","gen"]
    with open(csvfile, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows[::max(1,int(1.0/dt))]:   # 每1秒抽稀输出
            w.writerow({k: (round(r[k],5) if isinstance(r[k],float) else r[k]) for k in keys})

    # ---- 关键事件与指标 ----
    f_arr = np.array([r["f"] for r in rows])
    t_arr = np.array([r["t"] for r in rows])
    f_nadir = f_arr.min()
    t_nadir = t_arr[f_arr.argmin()]
    summary = dict(bus=bus, Pg=Pg, Pmax=Pmax, t_fault=t_fault, ramp=ramp,
                   t_pump_trip=t_pump_trip, t_gen_trip=t_gen_trip,
                   buffer_pump=(None if t_pump_trip is None else round(t_pump_trip-t_fault,1)),
                   f_nadir=round(float(f_nadir),3), t_nadir=round(float(t_nadir),1),
                   pb_max=round(max(r["p_b"] for r in rows),2),
                   csv=os.path.basename(csvfile))
    return summary, csvfile, rows, p


def _print_summary(s):
    print("="*60)
    print(" P1 SMIB 冷却水故障级联 —— 仿真摘要")
    print("="*60)
    print(f" 机组          : bus {s['bus']}  Pg={s['Pg']} / Pmax={s['Pmax']} MW")
    print(f" 故障时刻      : t_fault = {s['t_fault']} s (市政断水, ramp={s['ramp']}s)")
    print(f" 循环水泵跳闸  : {s['t_pump_trip']} s   (断水后缓冲 {s['buffer_pump']} s)")
    print(f" 机组跳闸      : {s['t_gen_trip']} s")
    print(f" 最大背压      : {s['pb_max']} kPa (跳机定值见params)")
    print(f" 频率最低点    : {s['f_nadir']} Hz @ t={s['t_nadir']} s")
    print(f" 结果CSV       : {s['csv']}")
    print("="*60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--t_fault", type=float, default=60.0)
    ap.add_argument("--ramp", type=float, default=0.0, help="市政补水衰减时间s, 0=阶跃")
    ap.add_argument("--t_end", type=float, default=1200.0)
    ap.add_argument("--dt", type=float, default=0.05)
    ap.add_argument("--bus", type=int, default=89)
    a = ap.parse_args()
    s, csvfile, rows, p = run(t_fault=a.t_fault, ramp=a.ramp, t_end=a.t_end, dt=a.dt, bus=a.bus)
    _print_summary(s)
