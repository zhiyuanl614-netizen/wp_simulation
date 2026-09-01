"""
P6 直流网络层 (DC-PF, 与文献一致)
==================================
按参照文献(Yu et al., Nat.Commun.2024)方案 B: 全流程采用直流潮流。
- 提供 PTDF 灵敏度矩阵, 用于线性规划的支路潮流约束: Pf = PTDF · (Pinj)
- 提供基准直流潮流、由基准潮流派生的线路热稳定限值
- 供 P6 主动控制 LP 与级联评估共用

说明: 直流潮流忽略电阻/无功/电压, 支路有功潮流对节点净注入线性:
    Pf_ℓ = Σ_n PTDF[ℓ,n] · Pinj_n         (Pinj = Pgen - Pload, MW)
"""
import numpy as np
from pypower.api import case118, ext2int, makePTDF, rundcpf, ppoption

PP_OPT = ppoption(VERBOSE=0, OUT_ALL=0)

# case118 列索引 (PYPOWER, 外部编号)
GEN_BUS, GEN_PG, GEN_STATUS, GEN_PMAX, GEN_PMIN = 0, 1, 7, 8, 9
BUS_I, BUS_TYPE, BUS_PD = 0, 1, 2
BR_F, BR_T, BR_STATUS, BR_PF = 0, 1, 10, 13


class DCNetwork:
    """IEEE-118 直流网络封装 (PTDF 线性模型)。"""

    def __init__(self, rating_factor=1.5, rating_floor=50.0):
        self.ext = case118()
        self.baseMVA = self.ext['baseMVA']
        self.gen0 = self.ext['gen'].copy()
        self.bus0 = self.ext['bus'].copy()
        self.branch0 = self.ext['branch'].copy()

        self.nb = self.bus0.shape[0]
        self.nl = self.branch0.shape[0]
        self.ng = self.gen0.shape[0]

        # 母线外部编号 -> 内部行索引
        self.busext = self.bus0[:, BUS_I].astype(int)
        self.bus_i = {int(b): k for k, b in enumerate(self.busext)}
        # 机组母线 -> gen 行索引
        self.gbus = {int(b): i for i, b in enumerate(self.gen0[:, GEN_BUS])}

        # ---- PTDF (内部编号, 以内部 slack 为参考) ----
        ppci = ext2int(case118())
        self.PTDF = makePTDF(ppci['baseMVA'], ppci['bus'], ppci['branch'])  # (nl, nb)

        # ---- 基准直流潮流, 派生线路限值 ----
        r, ok = rundcpf(self.ext, PP_OPT)
        assert ok, "base DC power flow failed"
        self.base = r
        Pf0 = np.abs(r['branch'][:, BR_PF])
        self.rate = np.maximum(rating_factor * Pf0, rating_floor)  # 线路热稳定限值 MW

        # 基准注入 (MW)
        self.Pload0_bus = self.bus0[:, BUS_PD].copy()
        self.P_load0 = float(self.Pload0_bus.sum())
        self.Pgen0 = self.gen0[:, GEN_PG].copy()
        self.P_gen0 = float(self.Pgen0.sum())

    # ---- 节点净注入 (MW) -> 支路潮流 (MW) via PTDF ----
    def branch_flows(self, Pinj_bus):
        """Pinj_bus: 长度 nb 的节点净注入(MW, 内部/外部同序). 返回支路潮流 Pf(MW)."""
        return self.PTDF.dot(Pinj_bus)

    def gen_bus_incidence(self):
        """机组 -> 母线 关联矩阵 Ag (nb x ng): 第 i 列在机组所在母线处为 1."""
        Ag = np.zeros((self.nb, self.ng))
        for i in range(self.ng):
            b = int(self.gen0[i, GEN_BUS])
            Ag[self.bus_i[b], i] = 1.0
        return Ag

    def full_dcpf(self, gen_pg, bus_pd, branch_status=None):
        """给定机组出力/母线负荷/支路状态, 解完整直流潮流, 返回 util/收敛性(连通性)."""
        ppc = {k: v for k, v in self.ext.items()}
        g = self.gen0.copy(); g[:, GEN_PG] = gen_pg
        b = self.bus0.copy(); b[:, BUS_PD] = bus_pd
        br = self.branch0.copy()
        if branch_status is not None:
            br[:, BR_STATUS] = branch_status
        ppc = dict(self.ext); ppc['gen'] = g; ppc['bus'] = b; ppc['branch'] = br
        try:
            r, ok = rundcpf(ppc, PP_OPT)
        except Exception:
            return dict(ok=False)
        if not ok:
            return dict(ok=False)
        Pf = r['branch'][:, BR_PF]
        st = br[:, BR_STATUS] > 0
        util = np.where(st, np.abs(Pf) / self.rate, 0.0)
        return dict(ok=True, Pf=Pf, util=util,
                    load_MW=float(b[:, BUS_PD].sum()),
                    gen_MW=float(r['gen'][:, GEN_PG].sum()),
                    branch=r['branch'])
