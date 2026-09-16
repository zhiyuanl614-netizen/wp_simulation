"""
③′ 水量账闭合 (城市轨迹 -> 电厂补水阀, 物理补水口径)  [v2: 6 台指定机组]
=====================================================
闭合此前"城市侧只反馈压头、电厂侧合成阶跃"的松耦合接口:

  1. 物理补水需求: q_phys = 0.453 m^3/s @707MW, 按 Pmax 线性缩放
     (蒸发+排污+风吹, 见 01_cooling_chain/params.py 标定)。
  2. 城市可供份额: PDD f(p)=sqrt(clip(p/20,0,1)), 用 boundary 口径压头轨迹
     (full_coupling_boundary.json) 逐时计算; 物理口径可供量 = f·q_phys。
  3. 电厂链闭合重算: 补水阀进水 = f(p(t))·Cv·开度·sqrt(max(p−H_tank,0))
     (以城市实际压头为驱动压头并乘 PDD 可供份额, 取代合成 32->0 阶跃);
     热负荷双变体: Pg(调度点) 与 Pmax(额定, 鲁棒变体, 解决 Pg=0 退化)。
     SAET_closed = t_trip − 6h (boundary 口径故障起点)。

输出: results/muni/closed_water_balance.json / .csv
对照列: SAET_pub_min = 已发布(合成阶跃+Pg) 值, 来自 coupling_rule_verification.json。
"""
import os, sys, json, csv
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.join(HERE, "..", "01_cooling_chain")
sys.path.insert(0, CC)
import params as PM
import submodels as sm

RES = os.path.join(HERE, "..", "..", "results", "muni")
FB = json.load(open(os.path.join(RES, "full_coupling_boundary.json")))
CM = json.load(open(os.path.join(RES, "coupling_map.json")))
VER = json.load(open(os.path.join(RES, "coupling_rule_verification.json")))
PUB = {v["bus"]: v["SAET_min"] for v in VER}
rows = {r["bus"]: r for r in CM["map"]}
T_F = FB["boundary_protocol"]["t_fault_h"]


def q_phys_of(Pmax):
    return 0.453 * Pmax / 707.0                      # m^3/s


def chain_closed(p_par, p_traj, t_grid, heat_MW, dt=1.0):
    """城市轨迹驱动电厂水链; 返回 t_trip (绝对 h) 或 None。"""
    p = p_par
    Ht, Hp = sm.equilibrate_water(p)
    pump_tripped = gen_tripped = False
    hi_bp = 0.0
    Q_cond = p.lp_heat_frac * heat_MW * 1000.0
    Tret = p.T_wetbulb + p.tower_approach_K + 8.0
    t_trip = None
    t_end = min(len(t_grid) * 0.25, 72.0)
    n = int((t_end * 3600) / dt)
    for i in range(n + 1):
        t = i * dt / 3600.0                          # h
        pc = float(np.interp(t, t_grid, p_traj))     # 城市压头 m
        # ---- 闭合补水阀: 高位补水箱需 >=28m 充填压头 (阈值物理来源), ----
        # ---- 驱动压头 = p−28; 低于阈值补水归零 (与 R2 一致, 连续衰减) ----
        qmake = 0.0
        driving = pc - p.H_muni_min
        if driving > 0:
            opening = min(1.0, max(0.0, p.Kp_tank * (p.H_tank_set - Ht)))
            opening = max(opening, 0.02) if Ht < p.H_tank_set else opening
            qmake = p.Cv_make * opening * np.sqrt(driving)
        qgrav = sm.gravity_flow(Ht, Hp, p)
        m_cw = sm.pump_flow(Hp, pump_tripped, p)
        q_loss = sm.loss_flow(Q_cond, m_cw, p)
        dHt = (qmake - qgrav) / p.A_tank
        dHp = (qgrav + m_cw - m_cw - q_loss) / p.A_pool
        if Ht <= p.H_tank_min and dHt < 0:
            dHt = 0.0
        if Hp <= 0 and dHp < 0:
            dHp = 0.0
        if (not pump_tripped) and Hp <= p.H_submerge_min:
            pump_tripped = True
            m_cw = 0.0
        Tcin = sm.basin_temp(Tret, m_cw, p)
        pb, Tret = sm.condenser(m_cw, Tcin, Q_cond, p)
        if pb >= p.p_b_trip_kPa:
            hi_bp += dt
        else:
            hi_bp = 0.0
        if (not gen_tripped) and hi_bp >= p.trip_delay_s:
            gen_tripped = True
            t_trip = t
            break
        Ht = max(p.H_tank_min, Ht + dt * dHt)
        Hp = max(0.0, Hp + dt * dHp)
        if gen_tripped:
            break
    return t_trip


out = []
for bus in sorted(int(b) for b in FB["plants"]):
    pl = FB["plants"][str(bus)]
    r = rows[bus]
    p_traj = np.array(pl["pressure_m"], dtype=float)
    t_grid = np.arange(len(p_traj)) * 0.25
    qp = q_phys_of(r["Pmax_MW"])
    fser = np.sqrt(np.clip(p_traj / 20.0, 0.0, 1.0))
    ratio = float(fser.mean())
    req_m3 = qp * 3600.0 * 72.0
    del_m3 = ratio * req_m3
    par = PM.Params(Pg_MW=r["Pg_MW"], Pmax_MW=r["Pmax_MW"])
    par_x = PM.Params(Pg_MW=r["Pmax_MW"], Pmax_MW=r["Pmax_MW"])
    trip_pg = chain_closed(par, p_traj, t_grid, r["Pg_MW"])
    trip_px = chain_closed(par_x, p_traj, t_grid, r["Pmax_MW"])
    out.append(dict(
        rank=r["rank"], bus=bus, junction=r["junction"],
        Pg_MW=r["Pg_MW"], Pmax_MW=r["Pmax_MW"], demand_Lps=r["demand_Lps"],
        q_phys_Lps=round(qp * 1000, 1),
        avail_ratio_72h=round(ratio, 3),
        requested_m3=round(req_m3, 0),
        delivered_m3=round(del_m3, 0),
        SAET_pub_min=PUB.get(bus),
        SAET_closed_Pg_min=(round((trip_pg - T_F) * 60, 1)
                            if trip_pg is not None else ">72h"),
        SAET_closed_Pmax_min=(round((trip_px - T_F) * 60, 1)
                              if trip_px is not None else ">72h")))

out.sort(key=lambda o: o["rank"])
N = len(out)
tot_req = sum(o["requested_m3"] for o in out)
tot_del = sum(o["delivered_m3"] for o in out)
print("=" * 104)
print(" 闭合水量账 v2 (语义①: 城市轨迹驱动电厂补水阀; 物理补水口径) —— %d 台机组" % N)
print("=" * 104)
print("  #  bus   junction  Pg/Pmax(MW)   72h需求(m3)  72h可供(m3)  可供率  "
      "SAET_pub  SAET_closed_Pg  SAET_closed_Pmax")
for o in out:
    f = lambda v: (("%10.1f" % v) if isinstance(v, (int, float)) else ("%10s" % v))
    print("  %d  %-5d %-8s %5.0f/%-5.0f %12.0f %12.0f %6.1f%% %9s %14s %16s"
          % (o["rank"], o["bus"], o["junction"], o["Pg_MW"], o["Pmax_MW"],
             o["requested_m3"], o["delivered_m3"], 100 * o["avail_ratio_72h"],
             f(o["SAET_pub_min"]).strip(),
             (("%.1f min" % o["SAET_closed_Pg_min"])
              if isinstance(o["SAET_closed_Pg_min"], (int, float))
              else str(o["SAET_closed_Pg_min"])),
             (("%.1f min" % o["SAET_closed_Pmax_min"])
              if isinstance(o["SAET_closed_Pmax_min"], (int, float))
              else str(o["SAET_closed_Pmax_min"]))))
print("-" * 104)
print("  合计: 72h 需求 %.0f m3, 可供 %.0f m3 (%.1f%%)"
      % (tot_req, tot_del, 100 * tot_del / tot_req))
nfin_pg = sum(1 for o in out if isinstance(o["SAET_closed_Pg_min"], (int, float)))
nfin = sum(1 for o in out if isinstance(o["SAET_closed_Pmax_min"], (int, float)))
print("  Pg 口径: %d/%d 在 72h 内跳机;  Pmax 鲁棒变体: %d/%d 在 72h 内跳机"
      % (nfin_pg, N, nfin, N))
px = [o["SAET_closed_Pmax_min"] for o in out
      if isinstance(o["SAET_closed_Pmax_min"], (int, float))]
if px:
    print("  SAET_closed_Pmax(min): min %.1f / 中位 %.1f / max %.1f"
          % (min(px), float(np.median(px)), max(px)))
json.dump(out, open(os.path.join(RES, "closed_water_balance.json"), "w"),
          ensure_ascii=False, indent=1)
keys = []
for o in out:
    for k in o:
        if k not in keys:
            keys.append(k)
with open(os.path.join(RES, "closed_water_balance.csv"), "w", newline="") as fh:
    wd = csv.DictWriter(fh, fieldnames=keys)
    wd.writeheader()
    for o in out:
        wd.writerow(o)
print("saved closed_water_balance.json/.csv")
