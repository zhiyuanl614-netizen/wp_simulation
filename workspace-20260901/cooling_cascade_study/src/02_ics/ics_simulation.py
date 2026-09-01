"""
ICS 协调器 —— 物理层 ⇄ 三级ICS ⇄ 电网
=====================================
单步执行顺序(自下而上采集, 自上而下下发):
  Step 1  物理层水力-热力推进(复用 src/01_cooling_chain/submodels.py)
  Step 2  PLC 采样传感器(市政/水箱/池/流量/背压)
  Step 3  SCADA 汇集归档 + 故障检测(市政供水压力) + 告警
  Step 4  调度中心决策 -> 是否发出/送达跨域预警
  Step 5  预警送达电网 -> 电网触发主动处置(备用预起机 + runback)
  Step 6  电网侧受影响机组少发功率 + 备用补偿 -> 功率缺额 / 能量缺额
  Step 7  快照归档 + 时间推进

影响量化(与参照文献一致): 用【少发功率(power deficit, MW)】与
【损失电量(energy deficit, MWh)】衡量水源中断对电力系统的影响,
不再使用频率最低点 f_nadir。
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "01_cooling_chain"))

from params import Params, load_unit_from_gen   # noqa
import submodels as sm                            # noqa
from db import ICSDatabase                        # noqa
from field_plc import FieldPLC                    # noqa
from scada import SCADA                           # noqa
from dispatch import DispatchCenter               # noqa


class ICSCoolingGridSim:
    """
    单机冷却水—ICS—电网耦合仿真。
    影响以【功率缺额 / 能量缺额】衡量(对齐文献): 受影响机组因水源中断而
    少发的功率, 扣除其余机组备用补偿后的未覆盖部分, 即为电力系统承受的缺额。
    主动处置(备用预起机 + runback)的触发时刻由 ICS 早期预警决定。
    """

    def __init__(self, bus=89, warning_enabled=True, t_fault=60.0, ramp=0.0,
                 sample_dt=1.0, runback_rate_frac=0.0015, db_reset=True):
        Pg, Pmax = load_unit_from_gen(bus=bus)
        self.p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
        self.bus = bus
        self.t_fault = t_fault
        self.ramp = ramp
        self.warning_enabled = warning_enabled
        self.runback_rate_frac = runback_rate_frac

        # ICS 组件
        self.db = ICSDatabase(reset=db_reset)
        self.plc = FieldPLC(sample_dt=sample_dt)
        self.scada = SCADA(self.db, warning_enabled=warning_enabled)
        self.dispatch = DispatchCenter(self.db)

        # 物理层初值(稳态平衡)
        self.H_tank, self.H_pool = sm.equilibrate_water(self.p)
        self.pump_tripped = False
        self.gen_tripped = False
        self.Q_cond = self.p.Q_cond0
        self.hi_bp_timer = 0.0
        self._Tret = self.p.T_wetbulb + self.p.tower_approach_K + 8
        self.cmd_frac = 1.0             # 机组出力指令(runback)

        # 电网侧: 其余机组两级备用(旋转备用 + 慢起机备用)
        self.P_aff0 = Pg               # 受影响机组初始出力 MW
        self.reserve_MW = 0.20 * Pg    # 快速旋转备用(可立即用)
        self.slow_reserve_cap = Pg     # 慢起机备用总量(需时间)
        self.slow_rate = Pg / 900.0    # 起机速率 MW/s (~15min 全上)
        self.warn_arrival_t = None
        self.t_pump_trip = None
        self.t_gen_trip = None

        self.rows = []

    def _muni_head(self, t):
        return sm.muni_head(t, self.p, self.t_fault, self.ramp)

    def step(self, t, dt):
        p = self.p
        # ---- Step 1: 物理层推进 ----
        dHt, dHp, m_cw = sm.water_derivs(t, self.H_tank, self.H_pool,
                                         self.pump_tripped, p, self.t_fault,
                                         self.ramp, Q_cond_kW=self.Q_cond)
        if (not self.pump_tripped) and self.H_pool <= p.H_submerge_min:
            self.pump_tripped = True
            self.t_pump_trip = t
            m_cw = 0.0
        T_cw_in = sm.basin_temp(self._Tret, m_cw, p)
        p_b, T_return = sm.condenser(m_cw, T_cw_in, self.Q_cond, p)
        self._Tret = T_return
        k_p = sm.power_derate(p_b, p)
        make = sm.make_flow(t, self.H_tank, p, self.t_fault, self.ramp)

        # 高背压保护跳机
        if p_b >= p.p_b_trip_kPa:
            self.hi_bp_timer += dt
        else:
            self.hi_bp_timer = 0.0
        if (not self.gen_tripped) and self.hi_bp_timer >= p.trip_delay_s:
            self.gen_tripped = True
            self.t_gen_trip = t

        phys = dict(muni_head=self._muni_head(t), H_tank=self.H_tank,
                    H_pool=self.H_pool, m_cw=m_cw, p_b=p_b, make_flow=make,
                    pump_tripped=self.pump_tripped)

        # ---- Step 2: PLC 采样 ----
        readings = self.plc.acquire(t, phys)
        actuators = self.plc.local_control_status(phys)

        # ---- Step 3: SCADA 汇集 + 检测 + 告警 ----
        self.scada.collect(t, readings, actuators)
        fault_active = t >= self.t_fault
        self.scada.monitor_and_alarm(t, fault_active)

        # ---- Step 4: 调度决策 -> 跨域预警 ----
        warned = self.dispatch.step(t, self.scada, fault_active)
        if warned and self.warn_arrival_t is None:
            self.warn_arrival_t = t

        # ---- Step 5: 电网主动处置(预警送达后 runback, 速率受限) ----
        if warned and not self.gen_tripped:
            rate_cap = self.slow_rate / max(self.P_aff0, 1.0)
            eff_rate = min(self.runback_rate_frac, rate_cap)
            self.cmd_frac = max(0.0, self.cmd_frac - eff_rate * dt)
        out_frac = min(self.cmd_frac, k_p) if not self.gen_tripped else 0.0

        # 热负荷更新(随出力->影响损失)
        if self.gen_tripped:
            self.Q_cond = max(0.0, self.Q_cond - dt * p.Q_cond0 / 20.0)
        else:
            self.Q_cond = p.lp_heat_frac * (p.Pg_MW * out_frac) * 1000.0

        # ---- Step 6: 少发功率 - 备用补偿 -> 功率缺额 ----
        P_aff = 0.0 if self.gen_tripped else p.Pg_MW * out_frac
        lost = self.P_aff0 - P_aff                  # 受影响机组少发功率 MW
        # 慢起机备用: 预警->提前起机; 否则跳机后才起机
        if warned:
            elapsed = max(0.0, t - self.warn_arrival_t)
        else:
            elapsed = 0.0 if self.t_gen_trip is None else max(0.0, t - self.t_gen_trip)
        slow_online = min(self.slow_reserve_cap, self.slow_rate * elapsed)
        reserve_avail = self.reserve_MW + slow_online
        pickup = min(lost, reserve_avail)           # 备用实际补偿
        deficit = max(0.0, lost - pickup)           # 未覆盖的功率缺额 MW (=电力系统承受的少发)

        # ---- Step 7: 快照 + 推进 ----
        self.db.write_snapshot(t, phys["muni_head"], self.H_tank, self.H_pool,
                               m_cw, p_b, 0 if self.pump_tripped else 1,
                               1 if self.gen_tripped else 0, deficit,
                               1 if warned else 0, 1 if fault_active else 0)
        self.rows.append(dict(t=t, muni=phys["muni_head"], H_tank=self.H_tank,
                              H_pool=self.H_pool, m_cw=m_cw, p_b=p_b, k_p=k_p,
                              out_frac=out_frac, warned=int(warned),
                              lost=lost, pickup=pickup, deficit=deficit))

        self.H_tank = max(p.H_tank_min, self.H_tank + dt * dHt)
        self.H_pool = max(0.0, self.H_pool + dt * dHp)

    def run(self, t_end=7000.0, dt=8.0):
        self.dt = dt
        n = int(t_end / dt) + 1
        for i in range(n):
            self.step(i * dt, dt)
        self.db.commit()
        return self.summary()

    def summary(self):
        deficit = np.array([r["deficit"] for r in self.rows])
        dt = getattr(self, "dt", 4.0)
        return dict(
            bus=self.bus, warning_enabled=self.warning_enabled,
            fault_t=self.t_fault,
            detect_t=self.scada._detect_t,
            warn_arrival_t=self.warn_arrival_t,
            t_gen_trip=self.t_gen_trip,
            max_deficit_MW=round(float(deficit.max()), 2),          # 少发功率峰值 MW
            energy_deficit_MWh=round(float(deficit.sum() * dt / 3600.0), 3),  # 损失电量 MWh
        )
