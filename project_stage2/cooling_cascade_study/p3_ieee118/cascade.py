"""
P3 级联引擎 —— 冷却水故障驱动的 IEEE 118 准稳态级联仿真
========================================================
把 P1 的"水力-热力子模型"作为受影响机组的功率降额/跳机信号源,
在 IEEE 118 交流网络上, 逐宏观时步:
  1. 用 P1 子模型推进受影响机组的 m_cw / 背压 / 降额系数 k_p / 跳机
  2. 计算全系统有功不平衡 -> COI 频率偏差 -> 其余机组一次调频再调度
  3. 解交流潮流 -> 检查线路过载 -> 过载跳线(带迭代) -> 电压检查
  4. 记录: 频率、母线电压、支路负载率、级联跳线/失负荷

复用: P1 的 params/submodels; 网络层 network.Network
"""
import os, sys, csv
import numpy as np

# 导入 P1 子模型
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p1_smib"))
from params import Params, load_unit_from_gen        # noqa
import submodels as sm                                # noqa
from network import (Network, GEN_BUS, GEN_PG, GEN_STATUS, GEN_PMAX,
                     BUS_PD, BR_STATUS)               # noqa


class Cascade:
    def __init__(self, affected_buses=(89,), t_fault=60.0, ramp=0.0,
                 overload_trip=True, overload_margin=1.0,
                 overload_persist_s=5.0, rating_factor=1.5,
                 # ---- P4 早期预警 / 主动控制 ----
                 proactive=False, t_detect=30.0,
                 runback_rate_frac=0.002, runback_floor=0.0,
                 reserve_boost=0.15, preemptive_shed=0.0):
        self.net = Network(rating_factor=rating_factor)
        self.affected = list(affected_buses)
        self.t_fault = t_fault
        self.ramp = ramp
        self.overload_trip = overload_trip
        self.margin = overload_margin          # util>margin 视为过载
        self.persist = overload_persist_s
        # ---- P4 主动控制参数 ----
        self.proactive = proactive
        self.t_detect = t_detect               # 信息/ICS 检测+通信延时(s)
        self.runback_rate_frac = runback_rate_frac  # 主动降负荷速率(每秒占额定比例)
        self.runback_floor = runback_floor     # 主动降到的最低出力比例(0=停机)
        self.reserve_boost = reserve_boost     # 预警后额外启用的旋转备用比例
        self.preemptive_shed = preemptive_shed # 预警后预防性切负荷比例(可中断负荷/需求响应)
        self.cmd_frac = {b: 1.0 for b in self.affected}  # 各机组功率指令(主动降额)
        # 为每台受影响机组建立 P1 状态
        self.units = {}
        for b in self.affected:
            Pg, Pmax = load_unit_from_gen(bus=b)
            p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
            _Ht0, _Hp0 = sm.equilibrate_water(p)   # 稳态平衡初值
            self.units[b] = dict(
                p=p, H_tank=_Ht0, H_pool=_Hp0,
                Q_cond=p.Q_cond0, pump_tripped=False, gen_tripped=False,
                hi_bp_timer=0.0, m_cw=p.m_cw0, k_p=1.0, p_b=p.p_b0_kPa,
                t_pump_trip=None, t_gen_trip=None)
        # 频率/系统
        self.f0 = 50.0
        self.f = 50.0
        # 系统总惯量(MW·s): 取所有在运机组 H*Pmax, 典型H=4
        self.H_sys = 4.0
        self.Sbase_sys = float(self.net.gen0[:, GEN_PMAX].sum())
        self.D_load = 1.0
        self.R_sys = 0.05
        self.reserve_frac = 0.10   # 其余机组旋转备用总量(占其额定)
        # ---- 三级备用(慢起机): 预警窗口内提前起机是韧性提升的关键 ----
        self.tertiary_cap = 900.0        # 三级备用总容量 MW (燃机/水电/停机备用)
        self.tertiary_rate_MWps = 900.0 / 900.0  # 起机速率 MW/s (~15min 全部到位)

    # ---- 单台受影响机组的 P1 推进(一个宏观步 dt) ----
    def _step_unit(self, b, t, dt):
        u = self.units[b]; p = u['p']
        dHt, dHp, m_cw = sm.water_derivs(t, u['H_tank'], u['H_pool'],
                                         u['pump_tripped'], p, self.t_fault, self.ramp,
                                         Q_cond_kW=u['Q_cond'])
        if (not u['pump_tripped']) and u['H_pool'] <= p.H_submerge_min:
            u['pump_tripped'] = True; u['t_pump_trip'] = t; m_cw = 0.0
        # 凝汽器
        T_ret_prev = getattr(self, '_Tret', {}).get(b, p.T_wetbulb + p.tower_approach_K + 8)
        T_cw_in = sm.basin_temp(T_ret_prev, m_cw, p)
        p_b, T_return = sm.condenser(m_cw, T_cw_in, u['Q_cond'], p)
        k_p = sm.power_derate(p_b, p)
        # 高背压跳机
        if p_b >= p.p_b_trip_kPa:
            u['hi_bp_timer'] += dt
        else:
            u['hi_bp_timer'] = 0.0
        if (not u['gen_tripped']) and u['hi_bp_timer'] >= p.trip_delay_s:
            u['gen_tripped'] = True; u['t_gen_trip'] = t
        # ---- P4 主动降负荷(runback): 预警后逐步降低出力指令 ----
        # 关键物理约束: runback 卸下的发电量不能快于备用/切负荷的补充速率,
        # 否则会自造缺额、适得其反。故 runback 速率上限 = 三级备用起机速率占比。
        warned = self.proactive and (t >= self.t_fault + self.t_detect)
        if warned and not u['gen_tripped']:
            # 单机 runback 速率上限(占额定/s): 三级备用总起机速率 / 受影响机组总出力
            aff_total = self._expected_loss()
            rate_cap = (self.tertiary_rate_MWps / max(aff_total, 1.0))
            eff_rate = min(self.runback_rate_frac, rate_cap)
            self.cmd_frac[b] = max(self.runback_floor,
                                   self.cmd_frac[b] - eff_rate * dt)
        cmd = self.cmd_frac[b]
        # 实际出力 = 指令 × 背压降额 (取更严者)
        u['out_frac'] = min(cmd, k_p) if not u['gen_tripped'] else 0.0

        # 热负荷更新: 主动降负荷同时降低凝汽器热负荷 -> 减缓背压上升(关键正反馈缓解)
        if u['gen_tripped']:
            u['Q_cond'] = max(0.0, u['Q_cond'] - dt * p.Q_cond0 / 20.0)
        else:
            u['Q_cond'] = p.lp_heat_frac * (p.Pg_MW * u['out_frac']) * 1000.0
        # 积分水位
        u['H_tank'] = max(p.H_tank_min, u['H_tank'] + dt * dHt)
        u['H_pool'] = max(0.0, u['H_pool'] + dt * dHp)
        u['m_cw'] = m_cw; u['k_p'] = k_p; u['p_b'] = p_b
        if not hasattr(self, '_Tret'):
            self._Tret = {}
        self._Tret[b] = T_return
        return u

    def _expected_loss(self):
        """主动预警下, 对受影响机组'预期总损失'的估计(=其初始出力之和)。
        物理含义: 调度知道这些机组终将因冷却水故障退出, 故按其初始出力预置备用。"""
        return sum(self.net.gen0[self.net.gbus[b], GEN_PG] for b in self.affected)

    # ---- 计算受影响机组的目标出力(MW) ----
    def _affected_output(self):
        out = {}
        for b in self.affected:
            u = self.units[b]; p = u['p']
            if u['gen_tripped']:
                out[b] = 0.0
            else:
                out[b] = p.Pg_MW * u.get('out_frac', u['k_p'])
        return out

    # ---- 一个宏观时步 ----
    def step(self, t, dt):
        # 1) 推进受影响机组
        for b in self.affected:
            self._step_unit(b, t, dt)
        aff_out = self._affected_output()

        # 2) 有功不平衡 -> 频率 -> 其余机组一次调频
        gen, bus, branch = self.net.fresh()
        # 受影响机组损失量(相对初始)
        lost = 0.0
        for b in self.affected:
            gi = self.net.gbus[b]
            base = self.net.gen0[gi, GEN_PG]
            lost += (base - aff_out[b])
            gen[gi, GEN_PG] = aff_out[b]
            if self.units[b]['gen_tripped']:
                gen[gi, GEN_STATUS] = 0

        # ---- 准稳态一次调频 (droop) + 备用/裕度约束 ----
        # 在运其余机组(可参与一次调频)
        rest_idx = [i for i in range(gen.shape[0])
                    if int(gen[i, GEN_BUS]) not in self.affected and gen[i, GEN_STATUS] > 0]
        rest_cap = sum(self.net.gen0[i, GEN_PMAX] for i in rest_idx)
        # 各机组可用上调裕度(备用): min(备用配额, 物理余量 Pmax-Pg)
        # 主动模式: 预警后额外释放备用 (reserve_boost)
        warned = self.proactive and (t >= self.t_fault + self.t_detect)
        rfrac = self.reserve_frac + (self.reserve_boost if warned else 0.0)
        headroom = {}
        for i in rest_idx:
            avail = min(rfrac * self.net.gen0[i, GEN_PMAX],
                        max(0.0, self.net.gen0[i, GEN_PMAX] - self.net.gen0[i, GEN_PG]))
            headroom[i] = avail
        reserve_total = sum(headroom.values())

        # ---- 备用体系: 旋转备用(快, 固定) + 三级备用(慢起机, 需预警争取时间) ----
        # 关键物理(本研究核心):
        #   受影响机组总容量常 > 系统旋转备用, 仅靠旋转备用不足以承受多机跳闸。
        #   水力慢动态提供的"缓冲窗口"若经信息/ICS 提前预警, 可在跳机前
        #   启动三级备用(燃机/水电/停机备用), 使跳机时刻在线备用更充分。
        #   => 预警提前量(lead time) 直接决定"跳机时已就位的三级备用量"。
        #   被动: 无预警, 三级备用只能在跳机后才开始起机, 起机慢 -> 追不上 -> 深跌。
        spin_reserve = reserve_total                    # 旋转备用(快)
        # 三级备用起机: 主动=预警时刻起机; 被动=首台跳机后起机。速率有限。
        tert_rate = self.tertiary_rate_MWps            # MW/s 起机速率
        if warned:
            # 从预警时刻起, 已起机时长 = t - (t_fault + t_detect)
            elapsed = max(0.0, t - (self.t_fault + self.t_detect))
        else:
            # 被动: 从首台跳机时刻起
            first_trip = min([u['t_gen_trip'] for u in self.units.values()
                              if u['t_gen_trip'] is not None], default=None)
            elapsed = 0.0 if first_trip is None else max(0.0, t - first_trip)
        tert_online = min(self.tertiary_cap, tert_rate * elapsed)  # 已在线三级备用

        # 预防性切负荷(预警后, 逐步切除可中断负荷/需求响应): 直接减小需补偿的缺额
        shed_MW = 0.0
        if warned and self.preemptive_shed > 0:
            # 按预警后经过时间线性投入, 上限=preemptive_shed×系统负荷
            shed_cap = self.preemptive_shed * self.net.P_load0
            shed_ramp = shed_cap / 120.0               # ~2min 内切到位
            elapsed_w = max(0.0, t - (self.t_fault + self.t_detect))
            shed_MW = min(shed_cap, shed_ramp * elapsed_w)

        reserve_avail = spin_reserve + tert_online + shed_MW  # 可用总补偿(备用+切负荷)
        pickup = min(lost, reserve_avail)

        # ---- 频率: 未覆盖缺额 -> 频率跌落(一次调频刚度 + 负荷阻尼) ----
        K = rest_cap / self.R_sys                       # 一次调频刚度 MW/pu
        D_term = self.net.P_load0 * self.D_load         # 负荷频率调节 MW/pu
        unmet = max(0.0, lost - pickup)                 # 备用无法覆盖的永久缺额
        # 未覆盖缺额只能靠负荷阻尼在更低频率下平衡 -> 深跌
        df_pu = -unmet / max(D_term, 1e-6) if unmet > 0 else 0.0
        deficit = unmet
        self.f = self.f0 * (1.0 + df_pu)

        # 按可用裕度比例分摊已部署 pickup 到各机组
        if reserve_total > 1e-6 and pickup > 0:
            for i in rest_idx:
                share = headroom[i] / reserve_total
                gen[i, GEN_PG] = self.net.gen0[i, GEN_PG] + pickup * share

        # slack 母线由潮流自动平衡剩余不匹配(网损等)

        # 3) 解潮流 + 过载级联
        res = self.net.solve(gen, bus, branch)
        cascade_trips = []
        if res['ok'] and self.overload_trip:
            for _ in range(20):   # 过载跳线迭代
                over = np.where((res['util'] > self.margin) & (branch[:, BR_STATUS] > 0))[0]
                if len(over) == 0:
                    break
                # 跳最严重一条(逐条跳, 更贴近保护动作)
                worst = over[np.argmax(res['util'][over])]
                branch[worst, BR_STATUS] = 0
                cascade_trips.append(int(worst))
                res = self.net.solve(gen, bus, branch)
                if not res['ok']:
                    break

        return dict(t=t, f=self.f, deficit=deficit, lost=lost, pickup=pickup,
                    res=res, aff_out=aff_out, cascade_trips=cascade_trips,
                    branch=branch, gen=gen, bus=bus)
