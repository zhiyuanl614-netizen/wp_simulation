"""
P3 主驱动 —— 在 IEEE 118 上运行冷却水故障级联仿真
==================================================
用法:
  python run_p3.py --affected 89          --t_fault 60 --ramp 0     # 单机
  python run_p3.py --affected 89,80,10    --t_fault 60 --ramp 0     # 同源多机(共因)
  python run_p3.py --affected 89 --overload_margin 0.6              # 收紧线路限值看级联
输出: results/p3_<tag>.csv  (时序) + 摘要
"""
import os, sys, csv, argparse
import numpy as np
from cascade import Cascade
from network import BUS_PD, BR_STATUS, GEN_BUS

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "results")


def run(affected, t_fault=60.0, ramp=0.0, t_end=2000.0, dt=1.0,
        overload_margin=1.0, rating_factor=1.5, no_overload=False,
        proactive=False, t_detect=30.0, runback_rate_frac=0.002,
        runback_floor=0.0, reserve_boost=0.15, tertiary_rate=None,
        preemptive_shed=0.0, tag_extra=""):
    casc = Cascade(affected_buses=affected, t_fault=t_fault, ramp=ramp,
                   overload_trip=not no_overload, overload_margin=overload_margin,
                   rating_factor=rating_factor,
                   proactive=proactive, t_detect=t_detect,
                   runback_rate_frac=runback_rate_frac, runback_floor=runback_floor,
                   reserve_boost=reserve_boost, preemptive_shed=preemptive_shed)
    if tertiary_rate is not None:
        casc.tertiary_rate_MWps = tertiary_rate
    rows = []
    n_branch = casc.net.branch0.shape[0]
    tripped_lines = set()
    ev = []   # 事件日志

    n = int(t_end / dt) + 1
    prev_gen_state = {b: False for b in affected}
    v_collapse_t = None
    for i in range(n):
        t = i * dt
        out = casc.step(t, dt)
        res = out['res']
        if not res['ok']:
            ev.append((t, "潮流不收敛/系统解列"))
            rows.append(dict(t=t, f=out['f'], conv=0, load_MW=np.nan,
                             Vmin=np.nan, Vmax=np.nan, max_util=np.nan,
                             n_line_trip=len(tripped_lines), lost_MW=out['lost'],
                             deficit_MW=out['deficit']))
            break

        # 新增级联跳线
        for li in out['cascade_trips']:
            if li not in tripped_lines:
                tripped_lines.add(li)
                fb = int(casc.net.branch0[li, 0]); tb = int(casc.net.branch0[li, 1])
                ev.append((t, f"线路过载跳闸 {fb}->{tb} (支路#{li})"))

        # 机组跳闸事件
        for b in affected:
            g = casc.units[b]['gen_tripped']
            if g and not prev_gen_state[b]:
                ev.append((t, f"机组 bus{b} 高背压跳机"))
                prev_gen_state[b] = True

        Vm = res['Vm']; util = res['util']
        vmin = float(Vm.min()); vmax = float(Vm.max())
        if vmin < 0.90 and v_collapse_t is None:
            v_collapse_t = t
            ev.append((t, f"母线电压跌破0.90pu (Vmin={vmin:.3f})"))

        rows.append(dict(t=t, f=out['f'], conv=1, load_MW=res['load_MW'],
                         Vmin=vmin, Vmax=vmax, max_util=float(util.max()),
                         n_line_trip=len(tripped_lines), lost_MW=out['lost'],
                         deficit_MW=out['deficit']))

    # ---- 写 CSV ----
    os.makedirs(RESDIR, exist_ok=True)
    mode = "proact" if proactive else "react"
    tag = f"aff{'-'.join(map(str,affected))}_tf{int(t_fault)}_ramp{int(ramp)}_m{overload_margin}_{mode}{tag_extra}"
    csvfile = os.path.join(RESDIR, f"p3_{tag}.csv")
    keys = ["t","f","conv","load_MW","Vmin","Vmax","max_util","n_line_trip","lost_MW","deficit_MW"]
    with open(csvfile, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: (round(r[k],4) if isinstance(r[k],float) and not np.isnan(r[k]) else r[k]) for k in keys})

    # 事件日志
    evfile = os.path.join(RESDIR, f"p3_{tag}_events.csv")
    with open(evfile, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["t_s","event"])
        for t, e in ev: w.writerow([round(t,1), e])

    # ---- 摘要 ----
    f_arr = np.array([r["f"] for r in rows])
    conv = np.array([r["conv"] for r in rows])
    s = dict(affected=affected, t_fault=t_fault, ramp=ramp, margin=overload_margin,
             f_nadir=round(float(f_arr.min()),3),
             t_gen_trips={b: casc.units[b]['t_gen_trip'] for b in affected},
             n_line_trip=len(tripped_lines),
             final_load=round(float(rows[-1]["load_MW"]) if not np.isnan(rows[-1]["load_MW"]) else float('nan'),1),
             load_loss=round(casc.net.P_load0 - (rows[-1]["load_MW"] if not np.isnan(rows[-1]["load_MW"]) else casc.net.P_load0),1),
             vmin=round(float(np.nanmin([r["Vmin"] for r in rows])),3),
             converged_all=bool(conv.all()),
             csv=os.path.basename(csvfile), events=os.path.basename(evfile), n_events=len(ev))
    return s, rows, ev


def _print(s):
    print("="*64)
    print(" P3 IEEE118 冷却水故障级联 —— 仿真摘要")
    print("="*64)
    print(f" 受影响机组母线 : {s['affected']}")
    print(f" 故障           : t_fault={s['t_fault']}s  ramp={s['ramp']}s  过载阈值={s['margin']}")
    print(f" 机组跳机时刻   : {s['t_gen_trips']}")
    print(f" 频率最低点     : {s['f_nadir']} Hz")
    print(f" 最低母线电压   : {s['vmin']} pu")
    print(f" 级联跳线条数   : {s['n_line_trip']}")
    print(f" 最终负荷/失负荷: {s['final_load']} MW / 损失 {s['load_loss']} MW")
    print(f" 全程收敛       : {s['converged_all']}   事件数: {s['n_events']}")
    print(f" 结果           : {s['csv']}  ,  {s['events']}")
    print("="*64)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--affected", type=str, default="89")
    ap.add_argument("--t_fault", type=float, default=60.0)
    ap.add_argument("--ramp", type=float, default=0.0)
    ap.add_argument("--t_end", type=float, default=2000.0)
    ap.add_argument("--dt", type=float, default=1.0)
    ap.add_argument("--overload_margin", type=float, default=1.0)
    ap.add_argument("--rating_factor", type=float, default=1.5)
    ap.add_argument("--no_overload", action="store_true")
    # P4 早期预警/主动控制
    ap.add_argument("--proactive", action="store_true", help="启用早期预警主动控制")
    ap.add_argument("--t_detect", type=float, default=30.0, help="信息/ICS检测+通信延时s")
    ap.add_argument("--runback_rate_frac", type=float, default=0.002, help="主动降负荷速率(每秒占额定)")
    ap.add_argument("--runback_floor", type=float, default=0.0, help="主动降到最低出力比例")
    ap.add_argument("--reserve_boost", type=float, default=0.15, help="预警后额外释放备用比例")
    a = ap.parse_args()
    aff = [int(x) for x in a.affected.split(",")]
    s, rows, ev = run(aff, t_fault=a.t_fault, ramp=a.ramp, t_end=a.t_end, dt=a.dt,
                      overload_margin=a.overload_margin, rating_factor=a.rating_factor,
                      no_overload=a.no_overload, proactive=a.proactive,
                      t_detect=a.t_detect, runback_rate_frac=a.runback_rate_frac,
                      runback_floor=a.runback_floor, reserve_boost=a.reserve_boost)
    _print(s)
    print(f" 控制模式       : {'主动预警' if a.proactive else '被动响应'}"
          + (f" (检测延时{a.t_detect}s, 降负荷{a.runback_rate_frac}/s)" if a.proactive else ""))
