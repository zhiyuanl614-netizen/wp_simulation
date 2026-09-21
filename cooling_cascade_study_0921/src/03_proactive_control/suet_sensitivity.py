"""
SUET 水侧参数一维敏感性 (评审 M3 补充实验)
==========================================
论文中心量 SUET 的水侧决定参数全部为单点工程典型值(λ_Q/γ/停留时间/approach/
湿球/ΔH_s/UA 流量指数), ch5 只扫了电力侧。本脚本对六台耦合机组逐一做一维
扫描(其余参数保持额定自洽标定), 给出 SUET 对各参数的敏感度表(tornado 数据)。

扫描轴与水平(评审 M3 建议):
  λ_Q  = lp_heat_frac        ∈ {1.00, 1.15, 1.35}      (基准 1.15)
  γ    = dPdp_frac_per_kPa   ∈ {0.010, 0.020, 0.030}   (基准 0.02, ±50%)
  停留时间 τ_pool            ∈ {3, τ_nominal, 5} min   (DL/T 5339 规范带 3–5 min;
                                   τ_nominal = A_pool·H_pool_set/m_cw0, 按机组各异)
  approach = tower_approach_K ∈ {3, 4, 5} K            (GB/T 50102 规范带 3–5 K)
  湿球  = T_wetbulb          ∈ {13, 15, 17} °C         (±2 K)
  ΔH_s  = submerge_band      ∈ {0.3, 0.5, 0.7} m       (基准 0.5, ±0.2)
  n     = UA_exp             ∈ {0.6, 0.8, 1.0}         (基准 0.8)

语义: v3 统一口径 (评审 M1-A, 2026-09-20): 热负荷 Q_cond = λ_Q·P_g·min(of, k_p),
与 simulate.py / §2.3.2 一致。改 approach/湿球等设计参数时 UA0 按"额定工况
自洽反推"原则同步重标定(Params.__post_init__), 即扫描的是设计意图参数而非
对已建成电厂的外生扰动。

输出: results/proactive_control/suet_sensitivity.json + 控制台摘要表
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "01_cooling_chain"))
sys.path.insert(0, HERE)
from params import Params, load_unit_from_gen          # noqa
from warning_indicators import _forward_water, coupled_buses   # noqa

RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
DT = 1.0
T_END = 36000.0   # 10 h: 极端水平(低 λ_Q/窄淹没带)下窗口可超 200 min, 须免积分域截断


def saet_min(bus, **overrides):
    """给定参数覆盖, 返回该机组 SUET (min)。None=不跳机(记 inf)。"""
    Pg, Pmax = load_unit_from_gen(bus=bus)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax, **overrides)
    t_trip, _ = _forward_water(p, out_frac_fn=None, dt=DT, t_end=T_END)
    return (t_trip / 60.0) if t_trip is not None else float("inf")


def pool_area_for_residence(bus, tau_min):
    """按目标停留时间(min)反推 A_pool: τ = A_pool·H_pool_set/m_cw0。"""
    Pg, Pmax = load_unit_from_gen(bus=bus)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
    return tau_min * 60.0 * p.m_cw0 / p.H_pool_set


def tau_nominal_min(bus):
    Pg, Pmax = load_unit_from_gen(bus=bus)
    p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
    return p.A_pool * p.H_pool_set / p.m_cw0 / 60.0


# (轴名, 参数键, 水平列表或 None=停留时间特殊轴, 基准水平)
AXES = [
    ("lambda_Q", "lp_heat_frac", [1.00, 1.15, 1.35], 1.15),
    ("gamma_per_kPa", "dPdp_frac_per_kPa", [0.010, 0.020, 0.030], 0.020),
    ("pool_residence_min", None, [3.0, "nominal", 5.0], "nominal"),
    ("tower_approach_K", "tower_approach_K", [3.0, 4.0, 5.0], 5.0),
    ("T_wetbulb_C", "T_wetbulb", [13.0, 15.0, 17.0], 15.0),
    ("submerge_band_m", "submerge_band", [0.3, 0.5, 0.7], 0.5),
    ("UA_exp_n", "UA_exp", [0.6, 0.8, 1.0], 0.8),
]


def main():
    buses = list(coupled_buses())
    baseline = {b: saet_min(b) for b in buses}
    print("=" * 96)
    print(" SUET 水侧参数一维敏感性 (v3 统一语义 M1-A; 六台 %s)" % "/".join(map(str, buses)))
    print(" 基准 SUET(min): %s" % {b: round(v, 1) for b, v in baseline.items()})
    print("=" * 96)

    out = dict(
        version="v3", date="2026-09-20",
        semantics=("统一语义(评审M1-A): Q_cond=λ_Q·P_g·min(of,k_p), 跳机判据同 simulate.py; "
                   "改设计参数时 UA0 按额定工况自洽反推同步重标定"),
        buses=buses, dt_s=DT,
        baseline_SAET_min={str(b): round(v, 2) for b, v in baseline.items()},
        axes=[],
    )

    for name, key, levels, base_level in AXES:
        axis = dict(axis=name, param=key, baseline_level=base_level,
                    levels=[], note="")
        rows = []
        for lv in levels:
            if name == "pool_residence_min":
                if lv == "nominal":
                    over = {}      # A_pool 基准(按机组各自 τ_nominal)
                    lv_label = "nominal"
                else:
                    lv_label = lv
            else:
                over = {key: lv}
                lv_label = lv
            saet = {}
            for b in buses:
                if name == "pool_residence_min" and lv != "nominal":
                    ov = dict(A_pool=pool_area_for_residence(b, lv))
                else:
                    ov = over
                saet[b] = saet_min(b, **ov)
            if name == "pool_residence_min" and lv == "nominal":
                axis["tau_nominal_min"] = {str(b): round(tau_nominal_min(b), 2) for b in buses}
            entry = dict(level=(lv_label if not isinstance(lv_label, float) else lv_label),
                         SAET_min={str(b): round(v, 2) for b, v in saet.items()})
            axis["levels"].append(entry)
            rows.append((lv_label, saet))

        # 敏感度汇总: 各水平六台 SUET 相对基准的最大绝对偏差(%)
        devs = []
        for lv_label, saet in rows:
            for b in buses:
                if baseline[b] != float("inf"):
                    devs.append(abs(saet[b] - baseline[b]) / baseline[b] * 100.0)
        all_vals = [v for _, s in rows for v in s.values() if v != float("inf")]
        axis["SUET_range_min"] = [round(min(all_vals), 2), round(max(all_vals), 2)]
        axis["max_abs_dev_pct"] = round(max(devs), 2) if devs else None
        out["axes"].append(axis)

        # 控制台: 每水平 bus89 + 六台区间
        print(" [%s] (基准水平 %s)" % (name, base_level))
        for lv_label, saet in rows:
            b89 = saet.get(89, float("nan"))
            span = (min(saet.values()), max(saet.values()))
            print("   level=%-8s bus89=%7.1f min   六台区间 [%6.1f, %6.1f] min"
                  % (str(lv_label), b89, span[0], span[1]))

    print("-" * 96)
    print(" 各轴最大 |ΔSUET| (相对基准, 六台最大):")
    for axis in out["axes"]:
        print("   %-20s %6.1f%%   (SUET 区间 %.1f–%.1f min)"
              % (axis["axis"], axis["max_abs_dev_pct"] or float("nan"),
                 axis["SUET_range_min"][0], axis["SUET_range_min"][1]))
    print("=" * 96)

    os.makedirs(RES, exist_ok=True)
    path = os.path.join(RES, "suet_sensitivity.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved", path)


if __name__ == "__main__":
    main()
