"""
运行 ICS 场景 —— 有无早期预警对比
==================================
研究目标: 冷却水系统水源中断(市政配水节点不能为补水箱补水)对电力系统的影响,
在【有无早期预警】两种情形下对比。影响量化(对齐文献): 少发功率(MW) + 损失电量(MWh)。

简化(依据研究者确认):
  - 检测只用【市政供水压力】作为源头信号; 不考虑补水箱/集水池/背压等内部子系统。
  - 不考虑检测延时/丢包/漏报: 市政压头跌破阈值即刻可靠预警。
  - 两种情形:
        WARN   : 有早期预警(市政压力检出 -> 电网主动 runback + 备用预起机)
        NOWARN : 无早期预警(被动, 等机组跳机后备用才响应)

产出: 控制台摘要 + results/ics_warning_compare.json + ics_timeseries.json
      + 数据库 ics_sim.db (WARN, 供审计)
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ics_simulation import ICSCoolingGridSim

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "..", "results", "ics")

CASES = {"WARN": "有早期预警(市政压力检出)", "NOWARN": "无早期预警(被动)"}


def main(t_fault=60.0, ramp=0.0, t_end=7000.0, dt=8.0):
    results, all_rows = {}, {}
    for key, wen in [("WARN", True), ("NOWARN", False)]:
        sim = ICSCoolingGridSim(warning_enabled=wen, t_fault=t_fault, ramp=ramp,
                                db_reset=(key == "WARN"))
        s = sim.run(t_end=t_end, dt=dt)
        results[key] = s
        all_rows[key] = sim.rows

    with open(os.path.join(RESDIR, "ics_warning_compare.json"), "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ts = {k: {"t": [r["t"] for r in rows],
              "muni": [r["muni"] for r in rows],
              "H_pool": [r["H_pool"] for r in rows],
              "p_b": [r["p_b"] for r in rows],
              "deficit": [r["deficit"] for r in rows],
              "lost": [r["lost"] for r in rows],
              "warned": [r["warned"] for r in rows]}
          for k, rows in all_rows.items()}
    with open(os.path.join(RESDIR, "ics_timeseries.json"), "w") as f:
        json.dump(ts, f)

    print("=" * 82)
    print(" ICS 有无早期预警对比 —— 水源中断对电力系统的影响 (检测量: 市政供水压力)")
    print("=" * 82)
    print(f" {'情形':<26}{'检出t(s)':>9}{'跳机t(s)':>10}{'少发功率峰值(MW)':>18}{'损失电量(MWh)':>16}")
    print("-" * 82)
    for k in ["WARN", "NOWARN"]:
        s = results[k]
        dt_ = "-" if s["detect_t"] is None else f"{s['detect_t']:.0f}"
        gt = "-" if s["t_gen_trip"] is None else f"{s['t_gen_trip']:.0f}"
        print(f" {k}:{CASES[k]:<22}{dt_:>9}{gt:>10}{s['max_deficit_MW']:>18.1f}{s['energy_deficit_MWh']:>16.2f}")
    print("-" * 82)
    print(" 数据库: results/ics_sim.db (WARN) | 摘要: ics_warning_compare.json")
    print("=" * 82)
    return results


if __name__ == "__main__":
    main()
