"""
取水节点位置 → 电力影响的敏感性分析 (v2: 指定 6 对耦合)
========================================================
v2 (2026-09-15 重构) 相对 v1 的三处实质变化:

  (1) 受影响机组由三厂 (89/80/10) 改为耦合层指定的 **6 台** (89/80/10/66/65/26),
      集合取自 results/muni/coupling_map.json (单一真源)。

  (2) **DISP 布置不再使用 P10/P50/P90 全网代表节点**, 而使用这 6 个指定取水节点
      自身的 B-ST 真实失压时刻 (coupling_map.t_fail_h: 1.25/1.75/3.75/3.75/7.0/9.0 h)
      相对首破节点的偏移 —— 即"研究者实际选定的取水布置"的错峰结构。

  (3) **取消 v1 的单机分解 (峰值取 max / 能量取 sum)**。该分解成立的前提是各危机在
      时间上完全隔离 (v1 偏移 3.75/9.75/17.0 h, 间隔 ≫ 冷却窗口)。v2 的 6 节点同处
      DMA1, 相对偏移 = [0, 0.5, 2.5, 2.5, 5.75, 7.75] h, 存在 0.5 h 与 0 h 的相邻间隔,
      危机簇重叠 (如 {bus89,bus80} 与 {bus10,bus66} 重叠), 分解不再物理正确。
      故 v2 对 DISP 采用**带 muni_offset_min 的联合 LP** 直接求解长时域, 不再分解;
      时域自动取 max_i(τ_i + T_ctrl,i) + 30 min 以覆盖最迟机组的完整软着陆。

两种布置定义:
  CO   同源同时 (反事实共因): 6 台 τ=0 → 危机完全重叠, 联合 LP (300 min 时域)。
       对应"若 6 厂取水点同时失效"的最严苛共因情形。
  DISP 指定布置 (真实错峰):   6 台 τ = 各取水节点 B-ST 失压相对偏移 → 联合 LP
       (长时域, 含 muni_offset_min)。
  对比二者即"取水错峰对被动峰值的削峰作用"与"主动控制的稳健性"。

两级缓冲 (物理基础, 不变):
  市政级: 水源停供 → 取水节点跌破 28 m, 时长 t_muni(节点), 强依赖节点位置 (小时级);
  冷却级: 取水失效 → 机组跳机, 时长 = 冷却 SAET (88.6–185.5 min), 电厂内部属性。

输出: results/p6_node_sensitivity.json + 控制台摘要。
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proactive_lp import ProactiveLP, critical_indicators

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
MUNI_RES = os.path.join(HERE, "..", "..", "results", "muni")
DT_MIN = 5.0
HORIZON_CO_MIN = 300.0
ALPHA = 1.5


def coupled():
    cm = json.load(open(os.path.join(MUNI_RES, "coupling_map.json")))
    return [(r["bus"], r["t_fail_h"]) for r in sorted(cm["map"], key=lambda r: r["rank"])]


def _tctrl(buses, mode, saet):
    if mode == "PA":
        return None
    return saet if mode == "SP" else [s * ALPHA for s in saet]


def _solve(buses, mode, T_ctrl, offsets_min, horizon_min):
    lp = ProactiveLP(affected_buses=list(buses), horizon_min=horizon_min,
                     dt_min=DT_MIN, enforce_dc=True, ramp_frac_per_min=0.01,
                     muni_offset_min=offsets_min)
    r = lp.solve(mode=mode, T_ctrl=T_ctrl)
    return r


def _layout(offsets_h, horizon_min, label):
    buses = [b for b, _ in coupled()]
    saet = critical_indicators(buses)
    off_min = [o * 60.0 for o in offsets_h]
    res = {}
    for mode in ["PA", "SP", "DP"]:
        Tc = _tctrl(buses, mode, saet)
        r = _solve(buses, mode, Tc, off_min, horizon_min)
        res[mode] = dict(max_deficit_MW=round(float(r["max_deficit_MW"]), 2),
                         energy_deficit_MWh=round(float(r["energy_deficit_MWh"]), 2),
                         max_overload_MW=round(float(r["max_overload_MW"]), 2))
    print("    [%s] 联合 LP 求解完成 (horizon=%.0f min)" % (label, horizon_min))
    return res


def run(save=True):
    pairs = coupled()
    buses = [b for b, _ in pairs]
    tf = [t for _, t in pairs]
    t0 = min(tf)
    disp_off_h = [round(t - t0, 2) for t in tf]          # B-ST 相对偏移 (h)
    saet = critical_indicators(buses)

    # DISP 时域: 覆盖最迟机组 (τ + T_ctrl) 再加裕度
    max_end = max(o * 60.0 + (s * ALPHA) for o, s in zip(disp_off_h, saet))
    horizon_disp = float(int(np.ceil((max_end + 30.0) / 10.0) * 10))

    out = dict(version="v2",
               affected=buses, dt_min=DT_MIN, alpha=ALPHA, power_flow="DC",
               cooling_SAET_min=[round(s, 1) for s in saet],
               intake_nodes=[r["junction"] for r in
                             sorted(json.load(open(os.path.join(MUNI_RES, "coupling_map.json")))["map"],
                                    key=lambda r: r["rank"])],
               muni_tfail_BST_h=tf,
               muni_offsets_h=dict(CO=[0.0] * len(buses), DISP=disp_off_h),
               horizon_min=dict(CO=HORIZON_CO_MIN, DISP=horizon_disp),
               method=dict(
                   CO="联合 LP, τ=0 (反事实共因: 6 厂同时危机)",
                   DISP="联合 LP + muni_offset_min (指定布置真实错峰; v2 取消单机分解)"),
               layouts={})

    print("=" * 84)
    print(" 取水节点位置 → 电力影响 敏感性 v2 (6 台 bus %s; DC潮流)"
          % ",".join(str(b) for b in buses))
    print("=" * 84)
    print(" 冷却级 SAET(min, 节点无关): %s" % out["cooling_SAET_min"])
    print(" B-ST 失压时刻(h): %s  → DISP 相对偏移(h): %s" % (tf, disp_off_h))
    print("-" * 84)

    out["layouts"]["CO"] = dict(
        name="同源同时(反事实共因, τ=0 → 危机完全重叠)",
        method=out["method"]["CO"], offsets_h=[0.0] * len(buses),
        results=_layout([0.0] * len(buses), HORIZON_CO_MIN, "CO"))
    out["layouts"]["DISP"] = dict(
        name="指定取水布置(6 节点 B-ST 真实错峰)",
        method=out["method"]["DISP"], offsets_h=disp_off_h,
        results=_layout(disp_off_h, horizon_disp, "DISP"))

    if save:
        with open(os.path.join(RES, "p6_node_sensitivity.json"), "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("saved", os.path.join(RES, "p6_node_sensitivity.json"))

    print("-" * 84)
    for key in ["CO", "DISP"]:
        lay = out["layouts"][key]
        print(" [%s] %s" % (key, lay["name"]))
        for m in ["PA", "SP", "DP"]:
            r = lay["results"][m]
            print("    %-4s 最大缺额 %8.1f MW   能量缺额 %8.1f MWh   最大过载 %6.1f MW"
                  % (m, r["max_deficit_MW"], r["energy_deficit_MWh"], r["max_overload_MW"]))
    print("-" * 84)
    co = out["layouts"]["CO"]["results"]["PA"]
    dp = out["layouts"]["DISP"]["results"]["PA"]
    print(" 机理结论:")
    print("  • 被动(PA): 同时共因峰值叠加 %.1f MW / %.1f MWh;" % (
        co["max_deficit_MW"], co["energy_deficit_MWh"]))
    print("             指定布置错峰削峰至 %.1f MW / %.1f MWh (Δ=%.0f%% 峰值)" % (
        dp["max_deficit_MW"], dp["energy_deficit_MWh"],
        100 * (1 - dp["max_deficit_MW"] / co["max_deficit_MW"])))
    print("  • 主动(SP/DP): CO %.1f/%.1f → DISP %.1f/%.1f —— 主动控制对取水错峰稳健" % (
        out["layouts"]["CO"]["results"]["SP"]["max_deficit_MW"],
        out["layouts"]["CO"]["results"]["SP"]["energy_deficit_MWh"],
        out["layouts"]["DISP"]["results"]["SP"]["max_deficit_MW"],
        out["layouts"]["DISP"]["results"]["SP"]["energy_deficit_MWh"]))
    print("=" * 84)
    return out


if __name__ == "__main__":
    run()
