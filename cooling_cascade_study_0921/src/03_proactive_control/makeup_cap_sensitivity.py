"""
市政补水封顶敏感性实验 (评审 M2-2 补充实验)
==========================================
背景: 模型失效前均衡隐含市政节点背后是无限体积水源(均衡需 ~450 L/s·台),
而 Table 2 设计口径的市政连接仅为 12.4–20.0 L/s 备用补水(23× 口径差)。
§3.2 已澄清: 正常运行的循环损失由厂内一次补给(原水/水处理)覆盖, 市政连接
是"失效源信号 + 备用补水"。

本实验做归谬式敏感性检验: 若市政连接(按额定封顶)是唯一补水来源——
  Q_make(t) = min(自然需求, 额定封顶) (t < t_fail),  0 (t >= t_fail, B-ST 阶跃)
即从 t=0 起封顶补给, 重算六台跳机时刻, 与各自取水节点的市政失压时刻 t_fail
交错对比。预期: 集水池以净亏 ~430 L/s 排水, ~2 h 内抽干可用储量, 迟失效
节点(J217 7h / J177 9h)将先于市政失效跳机——证实"额定市政备用不可能支撑
失效前均衡", 与 §3.2 的水源架构澄清互为印证。

实现: warning_indicators._forward_water(make_cap_m3s=...) (v3 附加参, 默认
None 与注册口径逐字节等价); 边界仍为 B-ST 合成阶跃(与设计案例同口径)。

输出: results/proactive_control/makeup_cap_sensitivity.json
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "01_cooling_chain"))
sys.path.insert(0, HERE)
from params import Params, load_unit_from_gen          # noqa
import submodels as sm                                  # noqa
from warning_indicators import _forward_water, coupled_buses   # noqa

MUNI_RES = os.path.join(HERE, "..", "..", "results", "muni")
RES = os.path.join(HERE, "..", "..", "results", "proactive_control")
DT = 1.0
T_END = 24 * 3600.0


def main():
    cm = json.load(open(os.path.join(MUNI_RES, "coupling_map.json")))
    rows = sorted(cm["map"], key=lambda r: r["rank"])
    print("=" * 100)
    print(" 市政补水封顶敏感性 (评审 M2): 若额定市政连接是唯一补水来源")
    print(" 语义: B-ST 阶跃; Q_make = min(自然需求, 额定封顶) 直至 t_fail, 之后为 0")
    print("=" * 100)
    print(" %-6s %-7s %-8s %-10s %-14s %-14s %s"
          % ("bus", "node", "t_fail", "cap", "SUET基线(min)", "跳机(封顶,h)", "先于市政失效?"))
    out = dict(version="v3", date="2026-09-20",
               semantics=("B-ST; make-up = min(natural, rated cap) for t<t_fail, 0 after; "
                          "统一热负荷口径(评审M1-A); t_trip 自封顶起算(t=0)"),
               units=[])
    for r in rows:
        bus, jn = r["bus"], r["junction"]
        t_fail_h, cap_Lps = r["t_fail_h"], r["makeup_Lps"]
        Pg, Pmax = load_unit_from_gen(bus=bus)
        p = Params(Pg_MW=Pg, Pmax_MW=Pmax)
        # 基线(注册口径): t_fail 时刻断水, SUET 自 t_fail 起算
        t_trip0, _ = _forward_water(p, out_frac_fn=None, dt=DT)   # t_fault=0
        suet0 = (t_trip0 / 60.0) if t_trip0 is not None else float("inf")
        # 封顶场景: t=0 起封顶, t_fail 后归零
        t_trip, _ = _forward_water(p, t_fault=t_fail_h * 3600.0, ramp=0.0,
                                   out_frac_fn=None, dt=DT, t_end=T_END,
                                   make_cap_m3s=cap_Lps / 1000.0)
        t_trip_h = (t_trip / 3600.0) if t_trip is not None else None
        before = bool(t_trip_h is not None and t_trip_h < t_fail_h)
        # 均衡口径参考: 额定损失与封顶之差(净亏)
        net_deficit_Lps = p.Q_loss * 1000.0 - cap_Lps
        print(" %-6d %-7s %-8.2f %-10s %-14.1f %-14s %s"
              % (bus, jn, t_fail_h, f"{cap_Lps:.1f} L/s", suet0,
                 "inf" if t_trip_h is None else f"{t_trip_h:.2f}",
                 "YES" if before else "no"))
        out["units"].append(dict(bus=bus, junction=jn, Pg_MW=Pg, Pmax_MW=Pmax,
                                 t_fail_h=t_fail_h, cap_Lps=cap_Lps,
                                 Q_loss_rated_Lps=round(p.Q_loss * 1000.0, 1),
                                 net_deficit_Lps=round(net_deficit_Lps, 1),
                                 SUET_baseline_min=round(suet0, 1),
                                 t_trip_capped_h=(None if t_trip_h is None
                                                  else round(t_trip_h, 3)),
                                 trips_before_muni_failure=before))
    n_before = sum(u["trips_before_muni_failure"] for u in out["units"])
    out["summary"] = dict(
        n_units=len(out["units"]),
        n_trip_before_muni_failure=n_before,
        note=("若市政额定连接是唯一水源, %d/6 台将先于市政失效跳机——"
              "证实失效前均衡必须由厂内一次补给支撑(§3.2 澄清), 市政连接语义为"
              "失效源信号+备用补水" % n_before))
    print("-" * 100)
    print(" 结论: %d/6 台在封顶口径下先于市政失效跳机" % n_before)
    print("=" * 100)
    os.makedirs(RES, exist_ok=True)
    path = os.path.join(RES, "makeup_cap_sensitivity.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved", path)


if __name__ == "__main__":
    main()
