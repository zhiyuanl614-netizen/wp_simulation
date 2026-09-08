"""
P6 主动控制线性规划 (SP / DP, 与文献 Methods 一致)
==================================================
复刻参照文献(Yu et al., Nat.Commun.2024) 的主动控制 LP, 物理量 气->水:

目标: 最小化控制期内总能量缺额  min Σ_t deficit_t · Δt
决策: 各机组各时步出力 Pg[i,t]; 缺额 deficit_t (松弛, ≥功率不平衡)
约束:
  (功率平衡)   Σ_i Pg[i,t] + deficit_t = P_load_total          ∀t
  (容量)       Pmin_i ≤ Pg[i,t] ≤ Pmax_i                        ∀i,t (受影响机组上限=其可用出力)
  (爬坡)       −Rd_i·Δt ≤ Pg[i,t] − Pg[i,t−1] ≤ Ru_i·Δt         ∀i,t
  (直流潮流)   −rate_ℓ ≤ PTDF_ℓ·(Ag·Pg_t − Pd) ≤ rate_ℓ         ∀ℓ,t
  (气/水失效)  受影响机组 i∈SIG 在控制时间 T_i 末出力=0           (线性化: Pg[i,t]=0, t≥T_i)
  (被动对照)   受影响机组按其"实际水力跳机轨迹"被动退出

两种主动策略:
  SP 静态主动: T_i = SAET_i  (在静态逃逸时间内降到零)
  DP 动态主动: 迭代延长 T_i (用 AET 在 T_set=α·T_i 处重算), 动用更多备用/储水
被动 PA: 不预调, 机组按水力轨迹被动跳机, 缺额由备用事后补 (受爬坡限制)。

潮流: 方案 B, 全流程直流潮流 (PTDF)。
"""
import os, sys
import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "01_cooling_chain"))
from dc_network import DCNetwork, GEN_BUS, GEN_PG, GEN_PMAX, GEN_PMIN  # noqa
from params import Params, load_unit_from_gen                          # noqa
import warning_indicators as wi                                        # noqa


class ProactiveLP:
    def __init__(self, affected_buses=(89, 80, 10), horizon_min=40.0, dt_min=2.0,
                 ramp_frac_per_min=0.02, reserve_frac=1.0,
                 enforce_dc=True, muni_offset_min=None, dc_hard=False):
        self.net = DCNetwork()
        self.affected = list(affected_buses)
        self.T = int(horizon_min / dt_min) + 1     # 时步数
        self.dt = dt_min                            # min
        self.ramp = ramp_frac_per_min               # 每分钟占额定 (Ru=Rd), 与文献一致的关键约束
        self.reserve_frac = reserve_frac            # 备用上限占额定余量比例 (1.0=用满物理余量)
        self.enforce_dc = enforce_dc
        self.dc_hard = dc_hard   # True: 支路限额硬约束(无过载松弛), 缺额=最小切负荷
        # 市政级失压偏移(min): 各受影响机组"取水节点跌破28m→冷却危机起点"的时刻。
        # None=全 0(同源同位置, 同时发生); 非零=分散取水(各机组危机错峰起始)。
        if muni_offset_min is None:
            self.muni_offset_min = [0.0] * len(self.affected)
        else:
            self.muni_offset_min = list(muni_offset_min)

        self.ng = self.net.ng
        self.Ag = self.net.gen_bus_incidence()      # nb x ng
        self.Pmax = self.net.gen0[:, GEN_PMAX].copy()
        self.Pg0 = self.net.Pgen0.copy()
        self.Pd_bus = self.net.Pload0_bus.copy()
        self.Pload_tot = float(self.Pd_bus.sum())
        # 机组行索引: 受影响 / 其余
        self.aff_idx = [self.net.gbus[b] for b in self.affected]
        self.rest_idx = [i for i in range(self.ng) if i not in self.aff_idx]
        # 其余机组出力上限 = Pmax (两级备用: 旋转备用即物理余量; 用爬坡率约束响应速度)
        self.rest_cap = np.array([
            min(self.Pg0[i] + self.reserve_frac * (self.Pmax[i] - self.Pg0[i]), self.Pmax[i])
            for i in range(self.ng)])

    # ---- 受影响机组的可用出力上限轨迹 ----
    def _aff_avail_traj(self, mode, T_ctrl=None):
        """返回 avail[i_local][t]: 受影响机组各时步的出力上限(MW)。
        SP/DP: 按控制时间 T_ctrl 线性降到零(主动软着陆)。
        PA(被动): 按水力模型的实际跳机时刻突降到零。"""
        avail = {}
        for k, gi in enumerate(self.aff_idx):
            b = self.affected[k]
            Pg_i = self.Pg0[gi]
            off = self.muni_offset_min[k]           # 市政失压偏移(min): 危机起点
            if mode in ("SP", "DP"):
                Tc = T_ctrl[k]                      # 控制时间(min)
                traj = []
                for t in range(self.T):
                    tt = t * self.dt - off          # 相对该机组危机起点的时间
                    if tt < 0.0:
                        traj.append(Pg_i)           # 市政失压前: 满出力(未进入危机)
                    else:
                        frac = max(0.0, 1.0 - tt / max(Tc, 1e-6))
                        traj.append(Pg_i * frac)
                avail[k] = np.array(traj)
            else:  # PA 被动: 用水力跳机时刻(自危机起点起算)
                Pg, Pmax = load_unit_from_gen(bus=b)
                p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
                t_trip, _ = wi._forward_water(
                    p, out_frac_fn=None,
                    t_end=max(12000.0, (self.T * self.dt + 30.0) * 60.0))
                t_trip_min = (t_trip or 1e9) / 60.0 + off
                traj = [Pg_i if (t * self.dt) < t_trip_min else 0.0
                        for t in range(self.T)]
                avail[k] = np.array(traj)
        return avail

    # ---- 组装并求解 LP ----
    def solve(self, mode="SP", T_ctrl=None, first_trip_override_min=None):
        """mode: 'PA'/'SP'/'DP'. T_ctrl: SP/DP 各受影响机组控制时间(min)列表。
        返回 dict(Pg[T,ng], deficit[T], energy_deficit_MWh, max_deficit_MW, feasible)."""
        ng, T, dt = self.ng, self.T, self.dt
        nl = self.net.nl
        # 变量: Pg[i,t] (ng·T) + deficit[t] (T) + 线路过载松弛 ovl[ℓ,t] (nl·T, 仅DC时)
        use_ovl = self.enforce_dc and not self.dc_hard
        nvar = ng * T + T + (nl * T if use_ovl else 0)

        def gidx(i, t): return t * ng + i
        def didx(t): return ng * T + t
        def oidx(l, t): return ng * T + T + t * nl + l

        avail = self._aff_avail_traj(mode, T_ctrl)

        # 目标: min Σ deficit_t + w·Σ ovl (缺额为主, 过载松弛加大权重惩罚)
        c = np.zeros(nvar)
        for t in range(T):
            c[didx(t)] = 1.0
        if use_ovl:
            for t in range(T):
                for l in range(nl):
                    c[oidx(l, t)] = 5.0             # 过载惩罚权重(> 缺额, 尽量不过载)

        # 变量边界
        lb = np.zeros(nvar); ub = np.zeros(nvar)
        for t in range(T):
            for i in range(ng):
                lb[gidx(i, t)] = 0.0
                if i in self.aff_idx:
                    k = self.aff_idx.index(i)
                    ub[gidx(i, t)] = max(0.0, avail[k][t])          # 受影响机组: 可用出力上限
                else:
                    ub[gidx(i, t)] = self.rest_cap[i]               # 其余机组: 备用上限
            lb[didx(t)] = 0.0; ub[didx(t)] = self.Pload_tot
            if use_ovl:
                for l in range(nl):
                    lb[oidx(l, t)] = 0.0; ub[oidx(l, t)] = 1e5   # 过载松弛(MW), 非负

        # ---- 稀疏三元组组装 (避免稠密大矩阵爆内存) ----
        from scipy.sparse import coo_matrix

        # (等式) 功率平衡: Σ_i Pg[i,t] + deficit_t = Pload_tot
        er, ec, ev, b_eq = [], [], [], []
        for t in range(T):
            for i in range(ng):
                er.append(t); ec.append(gidx(i, t)); ev.append(1.0)
            er.append(t); ec.append(didx(t)); ev.append(1.0)
            b_eq.append(self.Pload_tot)
        n_eq = T

        # (不等式) 三元组
        ur, uc, uv, b_ub = [], [], [], []
        ri = 0

        def add_row(cols, vals, rhs):
            nonlocal ri
            for cc, vv in zip(cols, vals):
                ur.append(ri); uc.append(cc); uv.append(vv)
            b_ub.append(rhs); ri += 1

        # 爬坡: |Pg[i,t]-Pg[i,t-1]| ≤ Rlim (其余机组)
        for t in range(1, T):
            for i in self.rest_idx:
                Rlim = self.ramp * self.Pmax[i] * dt
                add_row([gidx(i, t), gidx(i, t-1)], [1.0, -1.0], Rlim)
                add_row([gidx(i, t), gidx(i, t-1)], [-1.0, 1.0], Rlim)
        # t=0 相对基准 Pg0
        for i in self.rest_idx:
            Rlim = self.ramp * self.Pmax[i] * dt
            add_row([gidx(i, 0)], [1.0], self.Pg0[i] + Rlim)
            add_row([gidx(i, 0)], [-1.0], -(self.Pg0[i] - Rlim))

        # (被动因果约束) PA: 跳机前其余机组不得预升出力
        if mode == "PA":
            if first_trip_override_min is not None:
                first_trip_min = float(first_trip_override_min)
            else:
                first_trip_min = min(
                    (t * self.dt for t in range(self.T)
                     for k in range(len(self.aff_idx)) if avail[k][t] == 0.0),
                    default=0.0)
            for i in self.rest_idx:
                for t in range(self.T):
                    if t * self.dt < first_trip_min:
                        add_row([gidx(i, t)], [1.0], self.Pg0[i])

        # (直流潮流+过载松弛): |PTDF·(Ag·Pg_t − Pd)| ≤ rate + ovl
        if use_ovl:
            M = self.net.PTDF.dot(self.Ag)              # nl x ng (稠密, 但小)
            base_inj = -self.net.PTDF.dot(self.Pd_bus)  # 常数
            for t in range(T):
                for l in range(self.net.nl):
                    cols = [gidx(i, t) for i in range(ng)] + [oidx(l, t)]
                    add_row(cols, list(M[l, :]) + [-1.0],
                            self.net.rate[l] - base_inj[l])
                    add_row(cols, list(-M[l, :]) + [-1.0],
                            self.net.rate[l] + base_inj[l])

        A_eq = coo_matrix((ev, (er, ec)), shape=(n_eq, nvar)).tocsr()
        A_ub = coo_matrix((uv, (ur, uc)), shape=(ri, nvar)).tocsr() if ri > 0 else None
        b_eq = np.array(b_eq)
        b_ub = np.array(b_ub) if b_ub else None

        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                      bounds=list(zip(lb, ub)), method="highs")
        if not res.success:
            return dict(feasible=False, msg=res.message)

        x = res.x
        Pg = np.array([[x[gidx(i, t)] for i in range(ng)] for t in range(T)])
        deficit = np.array([x[didx(t)] for t in range(T)])
        max_ovl = 0.0
        if use_ovl:
            ovl = np.array([[x[oidx(l, t)] for l in range(nl)] for t in range(T)])
            max_ovl = float(ovl.max())
        return dict(feasible=True,
                    Pg=Pg, deficit=deficit,
                    energy_deficit_MWh=float(deficit.sum() * dt / 60.0),
                    max_deficit_MW=float(deficit.max()),
                    max_overload_MW=max_ovl,
                    T=T, dt=dt, mode=mode)


def critical_indicators(affected):
    """各受影响机组的 SAET(min), 用于 SP 的控制时间。"""
    return [wi.static_indicators(b)["SAET_min"] for b in affected]


if __name__ == "__main__":
    aff = [89, 80, 10]
    lp = ProactiveLP(affected_buses=aff, horizon_min=200, dt_min=5.0)
    saet = critical_indicators(aff)
    print("SAET(min):", [round(s, 1) for s in saet])
    for mode, Tc in [("PA", None), ("SP", saet), ("DP", [s*1.5 for s in saet])]:
        r = lp.solve(mode=mode, T_ctrl=Tc)
        if r["feasible"]:
            print(f"{mode}: 最大缺额={r['max_deficit_MW']:.1f} MW  "
                  f"总能量缺额={r['energy_deficit_MWh']:.1f} MWh")
        else:
            print(f"{mode}: 不可行 ({r['msg']})")
