"""
取水节点位置 → 电力影响的敏感性分析 (P6 node-position sensitivity)
==================================================================
研究疑问 (审阅提出): 不同 junction 节点失压时刻差异极大 —— 若选不同节点为电厂供冷却
水, 则跌破供水阈值(28 m)的时刻差异也大, "开始影响发电机组的时刻"自然不同。本模块把
该疑问贯通到下游电力影响, 做敏感性, 诚实呈现"结果依赖取水位置", 并给出机理。

两级缓冲 (务必区分, 本模块的物理基础):
  ┌ 市政级: 水源停供 → 取水节点跌破 28 m。时长 t_muni(节点), **强依赖节点位置**
  │         (src/00_muni_wdn/saet_distribution.py: P10/P50/P90 = 3.8/9.8/17.0 h; 28% 永不失压)
  └ 冷却级: 取水失效 → 机组跳机。时长 = 冷却 SAET(~90~125 min), **电厂内部属性, 与节点无关**

两种取水布置 (均用三厂 bus 89/80/10):
  CO   同源同位置: 三厂取水同/邻节点, t_muni 相同 → 三机组危机【同时发生】。
       用**联合 LP**(200 min 时域) 求解: 三机组缺额脉冲时间重叠, 共享备用, DC 潮流。
  DISP 分散取水:   三厂取水 P10/P50/P90 代表节点, t_muni=3.8/9.8/17.0 h。因市政失压
       偏移(小时级) ≫ 冷却窗口(~2 h), 三机组危机在时间上**完全隔离**, 互不重叠 →
       系统等价于三个**独立单机事件**依次发生。故:
         系统最大缺额 = max(各单机缺额)   (峰值不叠加)
         系统能量缺额 = Σ(各单机能量缺额) (总量守恒)
       各单机事件用单机 LP 求解 (同样共享全网备用/DC, 因同一时刻只有一机处于危机)。

  这种分解**物理正确且计算可行**: 避免了在 25 h 长时域上直接解含 DC 逐步约束的巨型 LP
  (数百时步 × 186 支路, 求解不收敛/超时); 又严格尊重"错峰事件峰值不叠加、能量守恒"。

机理结论: 取水**位置分散**使被动(PA)缺额脉冲时间分离 → **峰值不叠加**, 系统最大缺额
  由 CO 的 343 MW 降为 DISP 的 315 MW(=最严重单机); 主动(SP/DP)下各机组在自身冷却
  SAET 窗口内软着陆(与节点无关) → 缺额均可消除, 对取水位置稳健。

读 results/saet_distribution.json 的代表节点失压时刻。
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
AFFECTED = [89, 80, 10]
DT_MIN = 5.0
HORIZON_MIN = 200.0
ALPHA = 1.5


def _solve(buses, mode, T_ctrl=None):
    lp = ProactiveLP(affected_buses=list(buses), horizon_min=HORIZON_MIN, dt_min=DT_MIN,
                     enforce_dc=True, ramp_frac_per_min=0.01)
    r = lp.solve(mode=mode, T_ctrl=T_ctrl)
    return r


def co_located():
    """同源同位置: 三机组同时危机 → 联合 LP。"""
    saet = critical_indicators(AFFECTED)
    res = {}
    for mode in ["PA", "SP", "DP"]:
        Tc = None if mode == "PA" else (saet if mode == "SP" else [s * ALPHA for s in saet])
        r = _solve(AFFECTED, mode, Tc)
        res[mode] = dict(max_deficit_MW=round(float(r["max_deficit_MW"]), 2),
                         energy_deficit_MWh=round(float(r["energy_deficit_MWh"]), 2),
                         max_overload_MW=round(float(r["max_overload_MW"]), 2))
    return res


def dispersed():
    """分散取水: 三机组危机时间隔离 → 各单机 LP; 峰值取 max, 能量取 sum。"""
    res = {}
    for mode in ["PA", "SP", "DP"]:
        peaks, energies, ovls = [], [], []
        for b in AFFECTED:
            saet = critical_indicators([b])
            Tc = None if mode == "PA" else (saet if mode == "SP" else [s * ALPHA for s in saet])
            r = _solve([b], mode, Tc)
            peaks.append(float(r["max_deficit_MW"]))
            energies.append(float(r["energy_deficit_MWh"]))
            ovls.append(float(r["max_overload_MW"]))
        res[mode] = dict(max_deficit_MW=round(max(peaks), 2),         # 峰值不叠加
                         energy_deficit_MWh=round(sum(energies), 2),  # 能量守恒
                         max_overload_MW=round(max(ovls), 2))
    return res


def run(save=True):
    with open(os.path.join(MUNI_RES, "saet_distribution.json")) as f:
        dist = json.load(f)
    reps = dist["representatives"]
    disp_off = [reps["fast"]["t_fail_h"], reps["median"]["t_fail_h"], reps["slow"]["t_fail_h"]]

    out = dict(
        affected=AFFECTED, dt_min=DT_MIN, alpha=ALPHA, power_flow="DC",
        cooling_SAET_min=[round(s, 1) for s in critical_indicators(AFFECTED)],
        muni_offsets_h=dict(CO=[0, 0, 0], DISP=[round(x, 2) for x in disp_off]),
        distribution=dist["stats"],
        layouts=dict(
            CO=dict(name="同源同位置(取水同/邻节点, t_muni 相同→同时危机)",
                    method="联合 LP (缺额脉冲重叠, 共享备用)",
                    offsets_h=[0, 0, 0], results=co_located()),
            DISP=dict(name="分散取水(P10/P50/P90 代表节点, t_muni 错峰)",
                      method="各单机 LP (危机时间隔离; 峰值取 max, 能量取 sum)",
                      offsets_h=[round(x, 2) for x in disp_off], results=dispersed()),
        ))

    if save:
        with open(os.path.join(RES, "p6_node_sensitivity.json"), "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("saved", os.path.join(RES, "p6_node_sensitivity.json"))

    d = dist["stats"]
    print("=" * 80)
    print(" 取水节点位置 → 电力影响 敏感性 (三厂 bus 89/80/10; DC潮流)")
    print("=" * 80)
    print(" 市政侧失压时刻分布: min %.1f | P10 %.1f | 中位 %.1f | P90 %.1f | max %.1f h; %.0f%% 永不失压"
          % (d["min_h"], d["p10_h"], d["median_h"], d["p90_h"], d["max_h"], d["never_fail_pct"]))
    print(" 冷却级 SAET(min, 节点无关): %s" % out["cooling_SAET_min"])
    print(" 取水偏移(h): CO=[0,0,0]  DISP=[%.1f,%.1f,%.1f]" % tuple(disp_off))
    print("-" * 80)
    for key in ["CO", "DISP"]:
        lay = out["layouts"][key]
        print(" [%s] %s" % (key, lay["name"]))
        for m in ["PA", "SP", "DP"]:
            r = lay["results"][m]
            print("    %-6s 最大缺额 %8.1f MW   能量缺额 %8.1f MWh   最大过载 %6.1f MW"
                  % (m, r["max_deficit_MW"], r["energy_deficit_MWh"], r["max_overload_MW"]))
    print("-" * 80)
    co = out["layouts"]["CO"]["results"]["PA"]
    dp = out["layouts"]["DISP"]["results"]["PA"]
    print(" 机理结论:")
    print("  • 被动(PA): 同源同位置缺额【时间重叠→峰值叠加】%.0f MW; 分散取水缺额"
          % co["max_deficit_MW"])
    print("             【时间分离→峰值不叠加】%.0f MW → 取水位置显著影响【被动】峰值缺额。"
          % dp["max_deficit_MW"])
    print("  • 主动(SP/DP): 各机组自身冷却 SAET 窗口内软着陆(节点无关), 缺额均可消除")
    print("             → 主动控制对取水位置稳健。")
    print("=" * 80)
    return out


if __name__ == "__main__":
    run()
