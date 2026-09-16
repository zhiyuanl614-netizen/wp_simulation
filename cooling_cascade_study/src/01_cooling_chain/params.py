"""
P1 SMIB 参数模块
================
无现场数据 —— 参数按国家/国际标准 + 机组额定/实际出力拟合赋值。
额定容量 Pmax、实际出力 Pg 可直接取自 ieee118_dc/gen.csv。
所有取值均为"典型值/工程近似"，来源见 docs/parameter_fitting.md，用于机理验证。
"""
from dataclasses import dataclass, field
import os
import numpy as np

# ---- 从 IEEE 118 gen.csv 读取一台代表性机组（默认最大机组 bus89: Pg=607, Pmax=707）----
def load_unit_from_gen(bus=89, gen_csv=None):
    """返回 (Pg_MW, Pmax_MW)。找不到文件则回退到默认 600MW 级典型值。"""
    if gen_csv is None:
        here = os.path.dirname(os.path.abspath(__file__))
        gen_csv = os.path.join(here, "..", "..", "..", "ieee118_dc", "gen.csv")
    try:
        import csv
        with open(gen_csv) as f:
            for row in csv.DictReader(f):
                if int(float(row["bus"])) == bus:
                    return float(row["Pg"]), float(row["Pmax"])
    except Exception:
        pass
    return 607.0, 707.0  # 回退默认


@dataclass
class Params:
    # ===== 机组额定/实际出力（拟合基准，来自 gen.csv）=====
    Pmax_MW: float = 707.0          # 额定容量
    Pg_MW: float = 607.0            # 实际出力（初始运行点）

    # ===== 水源侧水力（子模型 W）=====
    # --- 高位补水箱 (市政压力直供 + 液位控制阀) ---
    A_tank: float = 30.0            # 补水箱底面积 m^2
    H_tank_set: float = 4.0         # 目标(满)水位 m
    H_tank0: float = 4.0            # 初始水位 m
    H_tank_min: float = 0.0         # 放空
    H_muni_head: float = 32.0       # 市政正常供水压头 m (>最小阈值, 可为高位补水箱供水)
    H_muni_min: float = 28.0        # 最小供水阈值 m (配水节点压头低于此->无法为补水箱补水=失效源)
    Cv_make: float = 0.30           # 补水阀流量系数 m^3/s / sqrt(m)
    Kp_tank: float = 0.5            # 补水箱液位控制增益
    # --- 集水池 (重力自流 + 液位控制阀) ---
    # 容积按规范: 有效停留时间 3-5 min×循环水量 (DL/T 5339 火力发电厂水工设计规范)
    A_pool: float = 1700.0          # 集水池底面积 m^2 (停留时间~4min, 见 __post_init__ 校验)
    H_pool_set: float = 3.0         # 目标水位 m
    H_pool0: float = 3.0            # 初始水位 m
    dz: float = 15.0                # 补水箱与集水池高差 m
    Cv_gravity: float = 0.60        # 重力补水阀流量系数 m^3/s / sqrt(m)
    Kp_pool: float = 0.8            # 集水池液位控制增益
    # --- 循环水泵 (NPSH / 最小淹没深度) ---
    # 循环水量按设计温升 8K 标定 (GB/T 50102 工业循环水冷却设计规范, 温升 8-10K)
    m_cw0_per_MW: float = 0.0295    # 额定循环水量系数 m^3/s per MW额定 (=温升8K, ≈106 m3/(h·MW))
    H_submerge_min: float = 1.2     # 泵吸口最小淹没深度(低于->进气/汽蚀跳泵) m
    submerge_band: float = 0.5      # 淹没不足流量线性降额带 m
    NPSH_r: float = 8.0             # 需求汽蚀余量(含淹没要求) m
    h_suction_fric: float = 1.0     # 额定流量下吸入管摩擦损失 m
    p_atm_kPa: float = 101.325      # 大气压 kPa
    # --- 冷却水损失 (随热负荷变化) ---
    # 规范: 循环冷却水总损失约 2-3% 循环量 (GB/T 50102):
    #   蒸发 ≈ 0.0016×冷却温降(K) (经验式, 温降8K→~1.3%); 排污按浓缩倍率; 风吹<0.05%
    h_fg: float = 2400.0            # 汽化潜热 kJ/kg (冷却塔散热工况近似)
    blowdown_ratio: float = 0.52    # 排污/蒸发 (浓缩倍率~3 => 使总损失≈2%循环量)
    drift_frac: float = 0.0005      # 风吹(飘滴)损失 占循环量 (现代收水器 <0.05%)
    tower_approach_K: float = 5.0   # 冷却塔冷幅(出塔水温-湿球) K (GB/T 50102: 3-5K)
    T_wetbulb: float = 15.0         # 环境湿球温度 °C  (设计进水温≈20°C, 与5kPa设计背压自洽)

    # ===== 凝汽器—低压缸（子模型 A）=====
    p_b0_kPa: float = 5.0           # 设计背压 kPa (额定工况)
    TTD_K: float = 4.0              # 设计端差(饱和温度-循环水出水温)
    cp_water: float = 4.187         # kJ/(kg·K)
    rho_water: float = 1000.0       # kg/m^3
    lp_heat_frac: float = 1.15      # 凝汽器热负荷/机械功率 近似倍率(含循环热耗)
    UA_exp: float = 0.8             # 传热系数随流量指数 U∝m^0.8
    # 汽轮机背压—功率修正 f(p_b): 线性微增出力率
    dPdp_frac_per_kPa: float = 0.02 # 背压每升高1kPa, 出力下降比例(近似2%/kPa)
    # 高背压保护
    p_b_trip_kPa: float = 15.0      # 高背压跳机定值 kPa (约设计值3倍)
    trip_delay_s: float = 3.0       # 保护延时 s

    # 注: 本研究影响以少发功率/损失电量衡量, 不含系统频率(与直流潮流口径一致)。
    # 电力系统侧的备用/主动控制参数见 p6_proactive_lp/ 与 ics/。

    def __post_init__(self):
        # 由额定功率标定循环水量与热负荷
        self.m_cw0 = self.m_cw0_per_MW * self.Pmax_MW          # m^3/s 额定循环水量
        self.Q_cond0 = self.lp_heat_frac * self.Pg_MW * 1000.0 # kW 初始凝汽器热负荷
        # 循环损失随热负荷变化: 蒸发∝热负荷, 排污∝蒸发, 风吹∝流量(近恒定)
        # 额定工况稳态损失(仅供缓冲时间参考; 动态值在 submodels.loss_flow 计算)
        evap0 = self.Q_cond0 / self.h_fg / self.rho_water      # m^3/s 蒸发(额定)
        blow0 = self.blowdown_ratio * evap0                    # m^3/s 排污
        drift0 = self.drift_frac * self.m_cw0                  # m^3/s 风吹
        self.Q_loss = evap0 + blow0 + drift0                   # m^3/s 额定总损失(参考)
        # 标定设计工况 UA (使额定流量下端差=TTD)
        C_cw0 = self.m_cw0 * self.rho_water * self.cp_water    # kW/K
        # 由 ε-NTU: ε=1-exp(-NTU), 端差 TTD 对应 ε≈Q/(C*(Tsat-Tin))
        # 反标定 UA0 使额定工况自洽
        self.C_cw0 = C_cw0
        # 目标: 额定工况饱和温度 = Psat^-1(p_b0). 用近似求 UA0.
        Tsat0 = tsat_from_p(self.p_b0_kPa)
        Tin0 = self.T_wetbulb + self.tower_approach_K   # 额定进水温≈出塔水温
        dT0 = Tsat0 - Tin0
        if dT0 <= 0:
            dT0 = 10.0
        eps0 = self.Q_cond0 / (C_cw0 * dT0)
        eps0 = min(max(eps0, 0.05), 0.99)
        NTU0 = -np.log(1 - eps0)
        self.UA0 = NTU0 * C_cw0                                # kW/K


# ---- 水蒸气饱和线 (Antoine, T in °C, 经 mmHg 换算到 kPa) ----
# 常用系数(水, 1-100°C): log10(P_mmHg) = A - B/(C + T_C)
_A, _B, _C = 8.07131, 1730.63, 233.426
_MMHG2KPA = 0.1333224

def psat_from_t(T_C):
    """饱和温度(°C)->饱和压力(kPa)"""
    return 10.0 ** (_A - _B / (_C + T_C)) * _MMHG2KPA

def tsat_from_p(P_kPa):
    """饱和压力(kPa)->饱和温度(°C)"""
    P_mmHg = max(P_kPa, 1e-3) / _MMHG2KPA
    return _B / (_A - np.log10(P_mmHg)) - _C
