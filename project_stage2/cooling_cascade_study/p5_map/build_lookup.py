"""
P5 扩展(1/2) —— 构建 f_nadir 查找表
====================================
为"预警可靠性/鲁棒策略"的蒙特卡洛分析预计算查找表:
  f_nadir(故障规模, 预警提前量 lead, 预防性切负荷 shed)
缓存到 results/p5_lookup.json, 供 reliability.py 快速插值使用。

lead=0 表示"无有效预警"(等价被动, 但仍可含预置切负荷)。
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p3_ieee118"))
from run_p3 import run                       # noqa
from resilience_map import FAULT_SETS, DT, T_END, first_trip_time  # noqa

RESDIR = os.path.join(HERE, "..", "results")

SCALES = [3, 4, 5]                # 预警敏感的中大规模故障
LEADS = [0, 1, 2, 3, 5, 8]       # min, 0=无有效预警
SHEDS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]


def build():
    lut = {}
    ftrip = {}
    for sc in SCALES:
        aff = FAULT_SETS[sc]
        t_first, f_pass = first_trip_time(aff)
        ftrip[sc] = t_first
        lut[str(sc)] = {}
        for lead in LEADS:
            lut[str(sc)][str(lead)] = {}
            for shed in SHEDS:
                if lead == 0:
                    # 无有效预警: 被动 + (若策略预置了切负荷, 则一直生效)
                    # 用 proactive=True, t_detect=0 但 lead=0 语义: 预警未提前
                    # 近似: 无预警=被动响应, 但预置切负荷仍可作为常备措施
                    s, _, _ = run(affected=list(aff), t_fault=60.0, ramp=0.0,
                                  t_end=T_END, dt=DT, no_overload=True,
                                  proactive=(shed > 0), t_detect=0.0,
                                  runback_rate_frac=0.0015, reserve_boost=0.0,
                                  preemptive_shed=shed)
                else:
                    t_detect = max(0.0, t_first - 60.0 - lead * 60.0)
                    s, _, _ = run(affected=list(aff), t_fault=60.0, ramp=0.0,
                                  t_end=T_END, dt=DT, no_overload=True,
                                  proactive=True, t_detect=t_detect,
                                  runback_rate_frac=0.0015, reserve_boost=0.0,
                                  preemptive_shed=shed)
                lut[str(sc)][str(lead)][str(shed)] = round(float(s['f_nadir']), 3)
                print(f"  sc={sc} lead={lead} shed={shed}: {s['f_nadir']:.2f}")
    obj = dict(scales=SCALES, leads=LEADS, sheds=SHEDS, ftrip=ftrip, lut=lut)
    out = os.path.join(RESDIR, "p5_lookup.json")
    json.dump(obj, open(out, "w"), ensure_ascii=False, indent=2)
    print("saved", out)
    return obj


if __name__ == "__main__":
    build()
