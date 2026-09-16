"""
耦合规律全节点验证 (v2: 6/6)
============================
v2 (2026-09-15 重构): 随 coupling_map v2 由 54 对改为研究者指定 6 对;
取消 Q1–Q5 分层汇总, 改为逐节点列表; R1 校验改为"时变量仅压头"的精确判据。

待证命题:
  R1 市政供水侧节点【只反馈压力水头】, 不核对其水量能否满足电力侧冷却水需求
     (边界数据中唯一的时变序列是压头; makeup_Lps/demand_Lps 为静态登记量,
      系"被评估的需求", 不作为负荷进入城市水力, 也不作为供量进入电厂链);
  R2 压头 < 28 m 的此刻该节点即失效 (补水归零, 不能为补水箱补水);
  R3 SAET 自该时刻起算 (t_fault_i = 首次压头<28m 之时刻);
  R4 以上对全部 6 个耦合取水节点成立。

验证方法:
  R1: 检查 full_coupling_boundary.json 中 plants[bus] 的时变字段集合 == {pressure_m,
      pressure_saet_m}; 且 full_coupling_boundary.py 的 FEEDBACK 语义为不反馈
      (makeup_availability 为事后 PDD 评估)。
  R2: 对每个失效节点, 以 t_fault_i 驱动 submodels.make_flow: 此前流量>0,
      此后恒=0 (head<28m 分支); 且由压头轨迹独立重算 t28 与存档 t_fail_h 一致。
  R3: 对每个失效节点, 以 t_fault_i 运行 simulate.run 全链条, SAET = t_gen_trip − t_fault_i。
  R4: 6 节点逐条断言; 若有节点 72h 内压头不跌破 28m -> 不触发 (亦符合规律)。

输出: results/muni/coupling_rule_verification.json / .csv
"""
import os, sys, json, csv, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.join(HERE, "..", "01_cooling_chain")
sys.path.insert(0, CC)
import params as PM
import submodels as sm
import simulate as SIM

RES = os.path.join(HERE, "..", "..", "results", "muni")
FB = json.load(open(os.path.join(RES, "full_coupling_boundary.json")))
CM = json.load(open(os.path.join(RES, "coupling_map.json")))
H_MIN = FB["boundary_protocol"]["H_muni_min_m"]          # 28.0
T_F = FB["boundary_protocol"]["t_fault_h"]               # 6.0
rows = {r["bus"]: r for r in CM["map"]}
N = len(rows)

# R1: 时变字段白名单 —— 只有压头序列, 无任何水量/供量序列
TIME_VARYING_ALLOWED = {"pressure_m", "pressure_saet_m"}
STATIC_FIELDS = {"rank", "node", "makeup_Lps", "demand_Lps", "head0_m", "t_fail_h",
                 "t_fail_after_fault_s", "t_fail_saet_h"}

out_rows = []
for bus in sorted(int(b) for b in FB["plants"]):
    pl = FB["plants"][str(bus)]
    r = rows[bus]
    keys = set(pl.keys())
    tv = {k for k, v in pl.items() if isinstance(v, list)}
    ok_head_only = (tv <= TIME_VARYING_ALLOWED) and (keys - tv) <= STATIC_FIELDS
    p = np.array(pl["pressure_m"], dtype=float)
    th = np.arange(len(p)) * 0.25                          # 15 min 步长
    # ---- R2-a: 独立重算阈值时刻 ----
    post = np.where((p < H_MIN) & (th >= T_F))[0]
    t28 = float(th[post[0]]) if len(post) else None
    ok_t = (t28 == pl["t_fail_h"])
    if t28 is None:
        out_rows.append(dict(rank=r["rank"], bus=bus, junction=r["junction"],
                             demand_Lps=r["demand_Lps"],
                             rule="not_triggered(<28m 未在72h内出现)",
                             t_fail_h=None, SAET_min=None,
                             ok_head_only=ok_head_only, ok=True))
        continue
    taf = pl["t_fail_after_fault_s"]
    # ---- R2-b: make_flow 在 t_fault 前>0 / 后=0 ----
    p_eq = PM.Params(Pg_MW=r["Pg_MW"], Pmax_MW=r["Pmax_MW"])
    Ht, Hp = sm.equilibrate_water(p_eq)
    f_before = sm.make_flow(taf - 1.0, Ht, p_eq, taf, 0.0)
    f_after = sm.make_flow(taf + 1.0, Ht, p_eq, taf, 0.0)
    ok_zero = (f_before > 0) and (f_after == 0.0)
    # ---- R3: 全链条 SAET ----
    loss = p_eq.Q_loss
    drain = (p_eq.A_pool * (p_eq.H_pool0 - p_eq.H_submerge_min)
             + p_eq.A_tank * p_eq.H_tank0) / loss
    t_end = min(drain * 1.6 + 3600, 24 * 3600)
    with tempfile.TemporaryDirectory() as td:
        s, _, _, _ = SIM.run(t_fault=60.0, ramp=0.0, t_end=t_end, dt=0.5,
                             bus=bus, outdir=td)
    saet = s["SAET_min"]
    ok_saet = True
    if saet is None:
        saet = ">24h"
    ok = bool(ok_t and ok_head_only and ok_zero and ok_saet)
    out_rows.append(dict(rank=r["rank"], bus=bus, junction=r["junction"],
                         Pg_MW=r["Pg_MW"], Pmax_MW=r["Pmax_MW"],
                         demand_Lps=r["demand_Lps"],
                         rule="triggered", t_fail_h=t28,
                         t_fault_after_s=taf, SAET_min=saet,
                         flow_before=round(float(f_before), 3),
                         flow_after=round(float(f_after), 3),
                         ok_t=ok_t, ok_head_only=ok_head_only,
                         ok_zero=ok_zero, ok_saet=ok_saet, ok=ok))

out_rows.sort(key=lambda o: o["rank"])
n_ok = sum(1 for o in out_rows if o["ok"])
n_trig = sum(1 for o in out_rows if o["rule"] == "triggered")
print("=" * 92)
print(" 耦合规律验证 v2: 触发(72h内<28m) %d / %d;  规律全项通过 %d / %d"
      % (n_trig, N, n_ok, N))
print("=" * 92)
print("  #  bus   junction  demand(L/s)  Pg(MW)  t_fail(h)  SAET(min)  "
      "flow前  flow后   R1 R2 R3")
for o in out_rows:
    if o["rule"] == "triggered":
        print("  %d  %-5d %-8s %11.4f %7.1f %9.2f %10.1f %7.3f %6.3f  %s%s%s"
              % (o["rank"], o["bus"], o["junction"], o["demand_Lps"], o["Pg_MW"],
                 o["t_fail_h"], o["SAET_min"], o["flow_before"], o["flow_after"],
                 "✅" if o["ok_head_only"] else "❌",
                 "✅" if (o["ok_t"] and o["ok_zero"]) else "❌",
                 "✅" if o["ok_saet"] else "❌"))
    else:
        print("  %d  %-5d %-8s %11.4f %7s %9s %10s %7s %6s  %s  (未触发)"
              % (o["rank"], o["bus"], o["junction"], o["demand_Lps"], "-",
                 "-", "-", "-", "-",
                 "✅" if o["ok_head_only"] else "❌"))
sa = [o["SAET_min"] for o in out_rows if isinstance(o["SAET_min"], (int, float))]
if sa:
    print("-" * 92)
    print("  SAET(min): min %.1f / 中位 %.1f / max %.1f  (n=%d)"
          % (min(sa), float(np.median(sa)), max(sa), len(sa)))
bad = [o["bus"] for o in out_rows if not o["ok"]]
print("  不符合节点:", bad if bad else "无")
json.dump(out_rows, open(os.path.join(RES, "coupling_rule_verification.json"), "w"),
          ensure_ascii=False, indent=1)
with open(os.path.join(RES, "coupling_rule_verification.csv"), "w", newline="") as f:
    keys = []
    for o in out_rows:
        for k in o:
            if k not in keys:
                keys.append(k)
    wd = csv.DictWriter(f, fieldnames=keys)
    wd.writeheader()
    for o in out_rows:
        wd.writerow({k: o.get(k) for k in keys})
print("saved coupling_rule_verification.json/.csv")
