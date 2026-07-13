"""
P1 SMIB 四层子模型
==================
W: 水源侧水力学   -> m_cw, T_cw_in, 泵状态
A: 凝汽器-低压缸  -> 背压 p_b, 机械功率降额 k_p
B: 机电(SMIB孤岛) -> 频率 f
故障源: 市政水网故障 => Q_make(t) 降为 0
"""
import numpy as np
from params import psat_from_t, tsat_from_p


# ---------------- 故障源: 市政补水 ----------------
def muni_head(t, p, t_fault, ramp=0.0):
    """市政等效供水压头 m。正常=H_muni_head; 故障后按 ramp 降为0(ramp=0=阶跃失压)。"""
    if t < t_fault:
        return p.H_muni_head
    if ramp <= 0:
        return 0.0
    return p.H_muni_head * max(0.0, 1.0 - (t - t_fault) / ramp)


# ---------------- 子模型 W: 水力 ----------------
def make_flow(t, H_tank, p, t_fault, ramp):
    """市政->补水箱 补水流量 m^3/s (问题1: 市政压力直供 + 液位控制阀)。
    速率 = Cv·开度·√(市政压头 - 水箱背压); 液位越接近设定值, 阀开度越小(闭环)。
    市政故障 => 压头->0 => 补水归零。"""
    head = muni_head(t, p, t_fault, ramp)
    driving = head - H_tank                          # 有效驱动压头(高于箱内水位才进水)
    if driving <= 0:
        return 0.0
    # 液位控制阀开度: 水位低于设定->全开, 接近设定->关小 (P控制, 限幅0~1)
    opening = min(1.0, max(0.0, p.Kp_tank * (p.H_tank_set - H_tank) + 0.0))
    # 稳态时需保持微开以补损失: 用平滑下限避免完全关死
    opening = max(opening, 0.02) if H_tank < p.H_tank_set else opening
    return p.Cv_make * opening * np.sqrt(driving)


def gravity_flow(H_tank, H_pool, p):
    """补水箱->集水池 重力自流 m^3/s (问题2: 液位闭环调节阀)。
    阀开度由集水池水位偏差决定: 池位低于设定->开阀补水; 达到设定->关阀。
    补水量因而'取决于集水池的净损失'(按需补水)。补水箱放空则无水可补。"""
    if H_tank <= p.H_tank_min:
        return 0.0
    head = H_tank + p.dz - H_pool
    if head <= 0:
        return 0.0
    opening = min(1.0, max(0.0, p.Kp_pool * (p.H_pool_set - H_pool)))  # 集水池液位闭环
    return p.Cv_gravity * opening * np.sqrt(head)


def npsh_available(H_pool, m_cw, p):
    """可用汽蚀余量 NPSH_a (m)。= 大气压头 - 饱和蒸汽压头 + 淹没深度 - 吸入摩擦损失。
    摩擦损失∝流量^2。集水池水位越低 -> NPSH_a 越小。"""
    from params import psat_from_t
    # 用集水池水温近似(此处传入常温即可, 主导项是淹没深度)
    p_vap = 3.0  # kPa, ~24°C 饱和蒸汽压近似(对 NPSH 影响小)
    atm_head = (p.p_atm_kPa - p_vap) / (p.rho_water * 9.81) * 1000.0  # m
    fric = p.h_suction_fric * (m_cw / p.m_cw0) ** 2 if p.m_cw0 > 0 else 0.0
    return atm_head + H_pool - fric


def pump_flow(H_pool, pump_tripped, p):
    """循环水泵流量 m^3/s (问题3: NPSH/淹没深度判据)。
    - 淹没深度 = H_pool; 低于 H_submerge_min -> 进气/汽蚀 -> 跳泵(0)。
    - 淹没不足带(submerge_band)内: 流量随汽蚀线性降额。
    - 额定工况满流量运行。"""
    if pump_tripped or H_pool <= p.H_submerge_min:
        return 0.0
    margin = H_pool - p.H_submerge_min
    if margin < p.submerge_band:
        return p.m_cw0 * (margin / p.submerge_band)
    return p.m_cw0


def loss_flow(Q_cond_kW, m_cw, p):
    """冷却水循环损失 m^3/s (问题4: 随热负荷变化)。
    蒸发 ∝ 凝汽器热负荷; 排污 ∝ 蒸发; 风吹 ∝ 循环流量(近恒定)。"""
    evap = Q_cond_kW / p.h_fg / p.rho_water          # m^3/s
    blow = p.blowdown_ratio * evap
    drift = p.drift_frac * m_cw
    return evap + blow + drift


def equilibrate_water(p, Q_cond_kW=None, dt=1.0, t_settle=3000.0):
    """无故障下把水位积分到稳态(比例控制存在液位下垂), 返回(H_tank_eq, H_pool_eq)。
    用于设定仿真初值, 避免起始瞬间的非平衡漂移。"""
    if Q_cond_kW is None:
        Q_cond_kW = p.Q_cond0
    Ht, Hp = p.H_tank_set, p.H_pool_set
    for _ in range(int(t_settle / dt)):
        dHt, dHp, _ = water_derivs(0.0, Ht, Hp, False, p, t_fault=1e12, ramp=0,
                                   Q_cond_kW=Q_cond_kW)
        Ht = min(p.H_tank_set, max(0.0, Ht + dt * dHt))
        Hp = min(p.H_pool_set, max(0.0, Hp + dt * dHp))
        if abs(dHt) < 1e-7 and abs(dHp) < 1e-7:
            break
    return Ht, Hp


def water_derivs(t, H_tank, H_pool, pump_tripped, p, t_fault, ramp, Q_cond_kW=None):
    """返回 dH_tank/dt, dH_pool/dt, m_cw。
    Q_cond_kW: 当前凝汽器热负荷(决定损失, 随出力变化); None时用额定。"""
    if Q_cond_kW is None:
        Q_cond_kW = p.Q_cond0
    qmake = make_flow(t, H_tank, p, t_fault, ramp)   # 市政->补水箱
    qgrav = gravity_flow(H_tank, H_pool, p)          # 补水箱->集水池(闭环)
    m_cw = pump_flow(H_pool, pump_tripped, p)        # 循环水泵(NPSH)
    q_loss = loss_flow(Q_cond_kW, m_cw, p)           # 损失(随热负荷)
    # 补水箱: 进=市政补水, 出=向集水池自流
    dHt = (qmake - qgrav) / p.A_tank
    # 集水池: 进=自流补水+闭式回水(≈m_cw), 出=循环水泵抽水 + 损失
    q_return = m_cw                                   # 闭式回水近似=抽水
    dHp = (qgrav + q_return - m_cw - q_loss) / p.A_pool
    if H_tank <= p.H_tank_min and dHt < 0:
        dHt = 0.0
    if H_pool <= 0 and dHp < 0:
        dHp = 0.0
    return dHt, dHp, m_cw


def basin_temp(T_return, m_cw, p):
    """集水池水温准稳态: 冷却塔把回水冷却到 湿球+冷幅。
    水量减少时冷却塔散热能力下降->温度略升(简化: 进水温≈出塔水温, 但流量低时冷却不足)"""
    T_tower_out = p.T_wetbulb + p.tower_approach_K
    if m_cw <= 0:
        # 断流: 池水温向回水温漂移(失去冷却)
        return T_return
    # 流量偏低时冷却不足, 出塔温升高(简化线性)
    ratio = min(1.0, m_cw / p.m_cw0)
    penalty = (1.0 - ratio) * 0.5 * max(0.0, T_return - T_tower_out)
    return T_tower_out + penalty


# ---------------- 子模型 A: 凝汽器-低压缸 ----------------
def condenser(m_cw_vol, T_cw_in, Q_cond_kW, p):
    """输入循环水流量(m^3/s), 进水温, 凝汽器热负荷 -> 背压 p_b(kPa), 出水温 T_return"""
    if m_cw_vol <= 1e-6:
        # 断流: 换热几乎停止, 背压飙升(数值上给高值)
        p_b = min(50.0, p.p_b_trip_kPa * 3)
        T_return = T_cw_in + 30.0
        return p_b, T_return
    m_cw = m_cw_vol * p.rho_water                    # kg/s
    C_cw = m_cw * p.cp_water                          # kW/K
    UA = p.UA0 * (m_cw_vol / p.m_cw0) ** p.UA_exp     # 传热系数随流量
    NTU = UA / C_cw
    eps = 1.0 - np.exp(-NTU)
    eps = min(max(eps, 1e-3), 0.999)
    T_return = T_cw_in + Q_cond_kW / C_cw             # 循环水温升
    T_sat = T_cw_in + Q_cond_kW / (eps * C_cw)        # 饱和(冷凝)温度
    p_b = psat_from_t(T_sat)
    return p_b, T_return


def power_derate(p_b, p):
    """背压->机械功率降额系数 k_p (<=1)"""
    dp = max(0.0, p_b - p.p_b0_kPa)
    k = 1.0 - p.dPdp_frac_per_kPa * dp
    return max(0.0, k)


# ---------------- 子模型 B: 机电 (受影响机组 + 系统其余部分, COI频率, MW制) ----------------
def system_setup(p):
    """建立系统等值参数(MW制)。系统 = 受影响机组 + 其余部分。"""
    P_aff_rated = p.Pmax_MW
    P_rest_rated = P_aff_rated * p.H_rest_ratio          # 其余部分容量(≈惯性比例)
    Sbase = P_aff_rated + P_rest_rated
    # 总动能系数 (H*S), MW·s
    HS = p.H_aff * P_aff_rated + (p.H_aff) * P_rest_rated  # 其余部分惯性常数取同量级
    # 初始功率
    P_aff0 = p.Pg_MW                                     # 受影响机组初始出力 MW
    P_rest0 = P_rest_rated * (p.Pg_MW / p.Pmax_MW)       # 其余部分按同负荷率
    P_load0 = P_aff0 + P_rest0                           # 系统总负荷 MW
    return dict(Sbase=Sbase, HS=HS, P_aff_rated=P_aff_rated,
                P_rest_rated=P_rest_rated, P_aff0=P_aff0,
                P_rest0=P_rest0, P_load0=P_load0)


def mech_derivs_mw(f, P_aff_gov, P_rest_gov, load_shed_frac, k_p, gen_tripped, sys, p):
    """COI 频率动态(MW制)。
    状态: f(Hz), P_aff_gov(受影响机组机械功率 MW), P_rest_gov(其余部分机械功率 MW)
    返回 dfdt, dP_aff, dP_rest, P_mech, P_load
    """
    df_pu = (f - p.f0) / p.f0

    # 受影响机组机械功率(背压降额; 跳闸=0)
    P_aff = 0.0 if gen_tripped else P_aff_gov * k_p

    P_mech = P_aff + P_rest_gov
    # 负荷: UFLS 减载 + 频率调节(阻尼)
    P_load = sys["P_load0"] * (1.0 - load_shed_frac) * (1.0 + p.D_damp * df_pu)

    dfdt = p.f0 / (2.0 * sys["HS"]) * (P_mech - P_load)

    # 一次调频目标(MW):
    # 受影响机组
    aff_target = sys["P_aff0"] - (1.0 / p.R_droop) * df_pu * sys["P_aff_rated"]
    aff_target = min(max(aff_target, 0.0), sys["P_aff_rated"])
    dP_aff = (aff_target - P_aff_gov) / p.Tgov
    # 其余部分(有旋转备用上限)
    rest_cap = sys["P_rest0"] + p.rest_reserve * sys["P_rest_rated"]
    rest_target = sys["P_rest0"] - (1.0 / p.R_rest) * df_pu * sys["P_rest_rated"]
    rest_target = min(max(rest_target, 0.0), rest_cap)
    dP_rest = (rest_target - P_rest_gov) / p.Tgov

    return dfdt, dP_aff, dP_rest, P_mech, P_load
