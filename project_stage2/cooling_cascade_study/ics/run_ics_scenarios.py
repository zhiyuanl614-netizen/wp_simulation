"""
运行 ICS 场景 —— 有无早期预警对比
==================================
简化(依据研究者确认):
  - 检测只用【市政供水压力】作为源头信号; 不考虑补水箱/集水池/背压等内部子系统。
  - 不考虑检测延时/丢包/漏报: 市政压头跌破阈值即刻可靠预警。
  - 只对比两种情形:
        WARN   : 有早期预警(市政压力检出 -> 电网主动处置)
        NOWARN : 无早期预警(被动, 等机组跳机)

产出:
  - 控制台摘要
  - results/ics_warning_compare.json  (两种情形)
  - results/ics_timeseries.json
  - 数据库 ics_sim.db (WARN 情形, 供审计)
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ics_simulation import ICSCoolingGridSim

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "results")

CASES = {"WARN": "有早期预警(市政压力检出)", "NOWARN": "无早期预警(被动)"}


def main(t_fault=60.0, ramp=0.0, t_end=2600.0, dt=4.0, preemptive_shed=0.0):
    results, all_rows = {}, {}
    for key, wen in [("WARN", True), ("NOWARN", False)]:
        sim = ICSCoolingGridSim(warning_enabled=wen, t_fault=t_fault, ramp=ramp,
                                preemptive_shed=preemptive_shed,
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
              "f": [r["f"] for r in rows],
              "warned": [r["warned"] for r in rows]}
          for k, rows in all_rows.items()}
    with open(os.path.join(RESDIR, "ics_timeseries.json"), "w") as f:
        json.dump(ts, f)

    print("=" * 72)
    print(" ICS 有无早期预警对比 (检测量: 市政供水压力; 零时延、可靠)")
    print("=" * 72)
    print(f" {'情形':<28}{'检出t(s)':>9}{'预警送达(s)':>12}{'跳机t(s)':>10}{'f_nadir':>9}")
    print("-" * 72)
    for k in ["WARN", "NOWARN"]:
        s = results[k]
        dt_ = "-" if s["detect_t"] is None else f"{s['detect_t']:.0f}"
        wt = "-" if s["warn_arrival_t"] is None else f"{s['warn_arrival_t']:.0f}"
        gt = "-" if s["t_gen_trip"] is None else f"{s['t_gen_trip']:.0f}"
        print(f" {k}:{CASES[k]:<24}{dt_:>9}{wt:>12}{gt:>10}{s['f_nadir']:>9.2f}")
    print("-" * 72)
    print(" 数据库: results/ics_sim.db (WARN) | 摘要: ics_warning_compare.json")
    print("=" * 72)
    return results


if __name__ == "__main__":
    main()
