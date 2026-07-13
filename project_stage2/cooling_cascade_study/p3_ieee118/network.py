"""
P3 网络层 —— IEEE 118 交流网络封装 (基于 PYPOWER)
=================================================
职责:
  - 载入 case118, 建立基准运行点
  - 由基准潮流派生线路热稳定限值(case118原值为占位9900MVA, 不可用)
  - 提供: 设定各机组出力/投退、切负荷、跳线, 重解交流潮流
  - 输出: 支路潮流/负载率、母线电压、是否收敛、失负荷量

说明: 本层用准稳态(QSS)交流潮流刻画"每个宏观时步的网络稳态",
配合 cascade 层的过载跳线迭代, 实现级联分析。这是电网级联筛查的
通行做法; 精确机电暂态(ANDES RMS)可作为后续增强。
"""
import numpy as np
from pypower.api import case118, runpf, ppoption

PP_OPT = ppoption(VERBOSE=0, OUT_ALL=0, PF_MAX_IT=30)

# case118 列索引 (PYPOWER)
GEN_BUS, GEN_PG, GEN_QG, GEN_STATUS = 0, 1, 2, 7
GEN_PMAX, GEN_PMIN = 8, 9
BUS_I, BUS_TYPE, BUS_PD, BUS_QD, BUS_VM, BUS_VA = 0, 1, 2, 3, 7, 8
BR_F, BR_T, BR_STATUS, BR_PF, BR_PT = 0, 1, 10, 13, 15
BR_RATE_A = 5


class Network:
    def __init__(self, rating_factor=1.5, rating_floor=50.0):
        self.ppc = case118()
        self.baseMVA = self.ppc['baseMVA']
        # 备份原始
        self.gen0 = self.ppc['gen'].copy()
        self.bus0 = self.ppc['bus'].copy()
        self.branch0 = self.ppc['branch'].copy()
        # 基准潮流
        r, ok = runpf(self.ppc, PP_OPT)
        assert ok, "base case AC power flow failed"
        self.base = r
        # 派生线路限值: max(factor*|基准潮流|, floor)
        Pf0 = np.abs(r['branch'][:, BR_PF])
        self.rate = np.maximum(rating_factor * Pf0, rating_floor)
        # 记录初值
        self.P_load0 = r['bus'][:, BUS_PD].sum()
        self.P_gen0 = r['gen'][:, GEN_PG].sum()
        # 机组母线 -> gen行索引
        self.gbus = {int(b): i for i, b in enumerate(self.gen0[:, GEN_BUS])}

    def fresh(self):
        """返回可修改的工作副本 (gen, bus, branch)"""
        return (self.gen0.copy(), self.bus0.copy(), self.branch0.copy())

    def solve(self, gen, bus, branch):
        """在给定机组/负荷/支路状态下解交流潮流。
        返回 dict: ok, Pf(MW), util, Vm, Va, load_MW, gen_MW, islanded"""
        ppc = dict(self.ppc)
        ppc['gen'] = gen
        ppc['bus'] = bus
        ppc['branch'] = branch
        try:
            r, ok = runpf(ppc, PP_OPT)
        except Exception:
            return dict(ok=False)
        if not ok:
            return dict(ok=False)
        Pf = r['branch'][:, BR_PF]
        st = branch[:, BR_STATUS] > 0
        util = np.where(st, np.abs(Pf) / self.rate, 0.0)
        return dict(ok=True,
                    Pf=Pf, util=util,
                    Vm=r['bus'][:, BUS_VM], Va=r['bus'][:, BUS_VA],
                    load_MW=bus[:, BUS_PD].sum(),
                    gen_MW=r['gen'][:, GEN_PG].sum(),
                    branch=r['branch'])
