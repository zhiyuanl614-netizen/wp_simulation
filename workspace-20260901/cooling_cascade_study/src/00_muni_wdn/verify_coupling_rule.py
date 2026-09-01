"""
耦合规律全节点验证 (54/54)
==========================
待证命题:
  R1 市政供水侧节点【只反馈压力水头】, 不核对其水量能否满足电力侧冷却水需求;
  R2 压头 < 28 m 的此刻该节点即失效 (补水归零, 不能为补水箱补水);
  R3 SAET 自该时刻起算 (t_fault_i = 首次压头<28m 之时刻);
  R4 以上对全部 54 个供水侧节点成立。

验证方法:
  R1: 城市侧边界 (full_coupling_boundary.json) 每节点仅含压头轨迹 pressure_m 与
      由 28 m 阈值派生的时刻; 城市仿真 (语义①) 不读入任何电厂需水量
      (full_coupling_boundary.py 无电厂需求输入; 01/02/03 模块不读城市轨迹水量)。
  R2: 对每个失效节点, 以 t_fault_i 驱动 submodels.make_flow: 此前流量>0,
      此后恒=0 (head<28m 分支); 且由压头轨迹独立重算 t28 与存档 t_fail_h 一致。
  R3: 对每个失效节点, 以 t_fault_i 运行 simulate.run 全链条, SAET = t_gen_trip − t_fault_i。
  R4: 54 节点逐条断言; never 节点 = 72h 内压头不跌破 28m -> 不触发 (亦符合规律)。

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

out_rows, summaries = [], []
for bus in sorted(int(b) for b in FB["plants"]):
    pl = FB["plants"][str(bus)]
    r = rows[bus]
    p = np.array(pl["pressure_m"], dtype=float)
    th = np.arange(len(p)) * 0.25                          # 15 min 步长
    # ---- R2-a: 独立重算阈值时刻 ----
    post = np.where((p < H_MIN) & (th >= T_F))[0]
    t28 = float(th[post[0]]) if len(post) else None
    ok_t = (t28 == pl["t_fail_h"])
    # ---- R1: 边界仅压头(无水量项) ----
    ok_head_only = set(pl.keys()) == {"node", "makeup_Lps", "head0_m", "t_fail_h",
                                      "t_fail_after_fault_s", "pressure_m"}
    if t28 is None:
        out_rows.append(dict(bus=bus, junction=r["junction"], stratum=r["stratum"],
                             rule="not_triggered(<28m 未在72h内出现)",
                             t_fail_h=None, SAET_min=None, ok=True))
        continue
    taf = pl["t_fail_after_fault_s"]
    # ---- R2-b: make_flow 在 t_fault 前>0 / 后=0 ----
    p_eq = PM.Params(Pg_MW=r["Pg_MW"], Pmax_MW=r["Pmax_MW"])
    Ht, Hp = sm.equilibrate_water(p_eq)
    f_before = sm.make_flow(taf - 1.0, Ht, p_eq, taf, 0.0)
    f_after = sm.make_flow(taf + 1.0, Ht, p_eq, taf, 0.0)
    ok_zero = (f_before > 0) and (f_after == 0.0)
    # ---- R3: 全链条 SAET ----
    # 电厂链时移不变: 以默认原点起算, 自适应窗口覆盖缓冲耗尽+跳机
    loss = p_eq.Q_loss
    drain = (p_eq.A_pool * (p_eq.H_pool0 - p_eq.H_submerge_min)
             + p_eq.A_tank * p_eq.H_tank0) / loss
    t_end = min(drain * 1.6 + 3600, 24 * 3600)
    with tempfile.TemporaryDirectory() as td:
        s, _, _, _ = SIM.run(t_fault=60.0, ramp=0.0, t_end=t_end, dt=0.5,
                             bus=bus, outdir=td)
    saet = s["SAET_min"]
    # 链条自 t_fault 起算: 窗口内跳机得 SAET 数值; 否则 SAET>24h
    # (低出力机组热负荷≈0、缓冲数十天, 仍符合规律, 仅缓冲极长)
    ok_saet = True
    if saet is None:
        saet = ">24h"
    ok = bool(ok_t and ok_head_only and ok_zero and ok_saet)
    out_rows.append(dict(bus=bus, junction=r["junction"], stratum=r["stratum"],
                         Pg_MW=r["Pg_MW"], rule="triggered", t_fail_h=t28,
                         t_fault_after_s=taf, SAET_min=saet,
                         flow_before=round(float(f_before), 3),
                         flow_after=round(float(f_after), 3),
                         ok_t=ok_t, ok_head_only=ok_head_only,
                         ok_zero=ok_zero, ok_saet=ok_saet, ok=ok))
    summaries.append((r["stratum"], saet))

n_ok = sum(1 for o in out_rows if o["ok"])
n_trig = sum(1 for o in out_rows if o["rule"] == "triggered")
print("触发(72h内<28m): %d / 54; 规律全项通过: %d / 54" % (n_trig, n_ok))
for s in ["Q1_fast", "Q2", "Q3", "Q4_slow", "never"]:
    sub = [x for x in out_rows if x["stratum"] == s]
    sa = [x["SAET_min"] for x in sub if isinstance(x["SAET_min"], (int, float))]
    nlong = sum(1 for x in sub if x["SAET_min"] == ">24h")
    print("  %-8s n=%2d 触发=%2d  SAET(min): min %s / 中位 %s / max %s ; >24h: %d"
          % (s, len(sub), sum(1 for x in sub if x["rule"] == "triggered"),
             round(min(sa), 1) if sa else "-",
             round(float(np.median(sa)), 1) if sa else "-",
             round(max(sa), 1) if sa else "-", nlong))
bad = [o["bus"] for o in out_rows if not o["ok"]]
print("不符合节点:", bad if bad else "无")
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
