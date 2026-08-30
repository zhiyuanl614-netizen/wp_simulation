"""
P6 早期预警指标 (水侧, 类比文献 AET/ALP/SAET)
=============================================
参照文献 Yu et al.(Nat.Commun.2024) 的两个预警指标, 物理量由天然气->冷却水:

  文献(气)                          本项目(水)
  ─────────────────────────────    ────────────────────────────────────
  ALP  可用管存 (Available Line     ASW  可用储水量 (Available Stored
       Pack) = LP - LP_last              Water) = 补水箱+集水池当前可用水量
                                          − 维持循环水泵不跳的最低储水
  AET  可用逃逸时间 (Available       AET  可用逃逸时间 = 受影响机组进入
       Escape Time) = 进气压力            高背压/跳泵保护前的剩余时间
       跌到保护阈值前的剩余时间
  SAET 静态AET = 故障时刻初始AET    SAET 静态AET = 故障时刻初始缓冲窗口

计算方法(与文献一致的近似): 用 P1 水力-热力模型, 在"受影响机组按给定
降出力速率运行"的假设下前向积分, 得到跳机时刻 -> AET; 可用储水量 -> ASW。
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "01_cooling_chain"))
from params import Params, load_unit_from_gen   # noqa
import submodels as sm                            # noqa


def _forward_water(p, t_fault=0.0, ramp=0.0, out_frac_fn=None,
                   dt=1.0, t_end=12000.0):
    """前向积分水力-热力链, 返回 (t_trip, series)。
    out_frac_fn(t): 受影响机组出力比例(0..1)时间函数; None=恒定额定。
    t_trip: 机组因高背压/跳泵而退出的时刻 (相对 t_fault)。"""
    Ht, Hp = sm.equilibrate_water(p)
    pump_tripped = False
    gen_tripped = False
    Q_cond = p.Q_cond0
    hi_bp_timer = 0.0
    Tret = p.T_wetbulb + p.tower_approach_K + 8.0
    t_trip = None
    series = []
    n = int(t_end / dt) + 1
    for i in range(n):
        t = i * dt
        of = 1.0 if out_frac_fn is None else float(out_frac_fn(t))
        # 热负荷随出力
        Q_cond = p.lp_heat_frac * (p.Pg_MW * of) * 1000.0 if not gen_tripped else \
            max(0.0, Q_cond - dt * p.Q_cond0 / 20.0)
        dHt, dHp, m_cw = sm.water_derivs(t, Ht, Hp, pump_tripped, p,
                                         t_fault, ramp, Q_cond_kW=Q_cond)
        if (not pump_tripped) and Hp <= p.H_submerge_min:
            pump_tripped = True
            m_cw = 0.0
        T_cw_in = sm.basin_temp(Tret, m_cw, p)
        p_b, Tret = sm.condenser(m_cw, T_cw_in, Q_cond, p)
        # 高背压跳机判据
        if p_b >= p.p_b_trip_kPa:
            hi_bp_timer += dt
        else:
            hi_bp_timer = 0.0
        trip_now = (hi_bp_timer >= p.trip_delay_s) or (pump_tripped and p_b >= p.p_b_trip_kPa)
        if (not gen_tripped) and trip_now:
            gen_tripped = True
            t_trip = t
        series.append((t, Ht, Hp, m_cw, p_b, of))
        Ht = max(p.H_tank_min, Ht + dt * dHt)
        Hp = max(0.0, Hp + dt * dHp)
        if gen_tripped and t > (t_trip + 60):
            break
    return t_trip, series


def static_indicators(bus=89):
    """故障时刻的静态预警指标 SAET 与 ASW0 (受影响机组保持额定出力)。"""
    Pg, Pmax = load_unit_from_gen(bus=bus)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
    # SAET: 恒定额定出力下的跳机时刻(=初始缓冲窗口)
    t_trip, series = _forward_water(p, out_frac_fn=None)
    SAET = t_trip if t_trip is not None else np.inf
    # ASW0: 故障时刻补水箱+集水池 相对"跳泵最低水位"的可用储水量 (m^3)
    Ht0, Hp0 = sm.equilibrate_water(p)
    ASW0 = p.A_tank * (Ht0 - p.H_tank_min) + p.A_pool * (Hp0 - p.H_submerge_min)
    return dict(bus=bus, Pg=Pg, Pmax=Pmax, SAET_s=SAET,
                SAET_min=SAET / 60.0, ASW0_m3=ASW0,
                Ht0=Ht0, Hp0=Hp0)


def aet_under_ramp(bus, ramp_frac_per_s, dt=1.0):
    """给定受影响机组降出力速率(每秒占额定比例), 返回 AET(跳机时刻,s)。
    降出力: out_frac(t) = max(0, 1 - ramp_frac_per_s * t)。
    与文献一致: 降得越快, 背压上升越缓, 机组可'主动停机'而非被强制跳机。"""
    Pg, Pmax = load_unit_from_gen(bus=bus)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)

    def of(t):
        return max(0.0, 1.0 - ramp_frac_per_s * t)

    t_trip, _ = _forward_water(p, out_frac_fn=of, dt=dt)
    # 若在降到零前未触发保护, 则视为主动停机成功(AET=降到零所需时间)
    t_zero = (1.0 / ramp_frac_per_s) if ramp_frac_per_s > 0 else np.inf
    if t_trip is None or t_trip >= t_zero:
        return t_zero, True    # 主动停机成功(未被强制跳机)
    return t_trip, False       # 被强制跳机


if __name__ == "__main__":
    for b in [89, 80, 10, 66, 65]:
        s = static_indicators(b)
        print(f"bus{b}: SAET={s['SAET_min']:.1f}min  ASW0={s['ASW0_m3']:.0f} m3  "
              f"(Pg={s['Pg']:.0f}/Pmax={s['Pmax']:.0f})")
