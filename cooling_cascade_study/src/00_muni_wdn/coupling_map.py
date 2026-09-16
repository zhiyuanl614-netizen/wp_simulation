"""
指定耦合映射 —— 6 台燃煤火电机组 ↔ D-town 6 个真实供水 junction
================================================================
定位 (v2, 2026-09-15 重构): 把耦合从 v1 的"全 54 台发电机全耦合 + 失压时刻
分层比例抽样"改为【研究者指定的 6 对级联耦合】。两条重构依据:

  (1) **部分 junction 本身不供水** —— D-town 399 个 junction 中 51 个基础需水为 0
      (纯过流/占位节点, 无 pattern), 把它们指定为电厂取水点在物理上不成立。v1 映射
      中有 4 对踩坑, 其中 bus80–J371 (Pg=477 MW, 主力机组) 的取水节点需水为 0,
      且 J371 在 B-ST 口径下 72h 不失压 (never 层) —— 该对既不供水也不失效。
      v2 起以 `demand_Lps > 0` 为**硬筛条件**并在结果中逐节点登记需水量。

  (2) **并非全部 Gens 均为燃煤火电机组** —— IEEE-118 的 54 条 gen 记录中 35 台
      Pg=0 (多为调相机/占位, Pmax=100 为算例默认值), 不构成"循环冷却 + 市政补水"
      的凝汽式火电机组; 对其建模冷却级联无物理意义 (热负荷≈0 → 循环损失极小 →
      SAET > 24h → 不发生级联, 见 docs/coupling_map.md §6 附带发现)。v2 只保留
      6 台大出力机组。

耦合规则 (v2, 确定、可复现):
  1. **机组集合 (研究者指定)**: 6 台大出力凝汽式机组 bus 89/80/10/66/65/26
     (Pg = 607/477/450/392/391/314 MW, ΣPg = 2631 MW)。
  2. **取水节点集合 (研究者指定)**: J102/J97/J198/J5/J217/J177 —— 均属 DMA1 分区、
     基础需水 > 0 (真实供水节点)、B-ST 口径下 72h 内失压。
  3. **硬筛校验 (不合格即断言失败)**: demand_Lps > 0 (真实供水) 且
     baseline 24h EPS 全程最小压头 > 32 m (故障前可正常为高位补水箱补水) 且
     t_fail 在 72h 观测窗内存在 (会真正触发级联)。
  4. **rank↔rank 确定性配对**: 取水节点按 B-ST 失压时刻升序 (即研究者给出顺序
     J102/J97/J198/J5/J217/J177), 机组按 Pg 降序, 一一配对 ——
     失压最快的节点配最大机组, 构成最严苛 (最保守) 的组合。
  5. **补水负荷 (额定需求)**: makeup_Lps = clip(0.03*Pmax, 2, 20) L/s (容量缩放);
     单一规则、不再对特定对特例赋值。**不反馈进城市水力** (松耦合语义, 依据见
     docs/coupling_map.md §5), 仅作下游边界与可供性事后评估用。
  6. **取消 Q1–Q5 分层**: v2 不再做失压时刻分层比例抽样, 结果中不含 stratum 字段;
     图 4 / 图 5 相应取消分层着色与分层行序 (图 5 改按失压时刻升序排 6 行)。
     代价: 耦合集合不再"复现全网失压分布", 该论证在论文中相应改写为
     "研究者指定的 6 个真实供水节点 + 6 台大出力机组的针对性级联案例"。

输出:
  results/muni/coupling_map.json   6 对耦合表 + 规则 + 硬筛校验记录
  results/muni/coupling_map.csv    同上 (表格版)
  results/muni/coupling_map.png    空间总览 (D-town 上标出 6 个耦合节点)

数据来源 (CC-BY-NC 4.0, 须署名): Ostfeld, Avi. "05 Long Term Improvement" (D-town)
(2016). Battle of the Water Network Models. Univ. of Kentucky Libraries.
https://uknowledge.uky.edu/wdst_models/5
"""
import os, sys, json, csv
import numpy as np
import wntr

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "data", "DTOWN.inp")
RES = os.path.join(HERE, "..", "..", "results", "muni")
GEN_CSV = os.path.join(HERE, "..", "..", "..", "ieee118_dc", "gen.csv")
DIST_JSON = os.path.join(RES, "saet_distribution.json")

HEALTHY_MIN_HEAD = 32.0          # m, 基线健康判据 (与 saet_distribution 一致)
N_COUPLED = 6

# ---- 研究者指定的耦合集合 (v2) ----
# 机组: 6 台大出力凝汽式火电机组 (bus, 由 gen.csv 取 Pg/Pmax, 按 Pg 降序配对)
COUPLED_BUSES = [89, 80, 10, 66, 65, 26]
# 取水节点: 按 B-ST 失压时刻升序给出 (= 研究者指定顺序)
COUPLED_JUNCTIONS = ["J102", "J97", "J198", "J5", "J217", "J177"]


def load_gens():
    gens = []
    with open(GEN_CSV) as f:
        for r in csv.DictReader(f):
            gens.append(dict(gen_id=int(r["gen_id"]), bus=int(r["bus"]),
                             Pg=float(r["Pg"]), Pmax=float(r["Pmax"])))
    return sorted(gens, key=lambda g: g["bus"])


def baseline_min_head():
    """无故障 24h EPS: 各 junction 全程最小压头 (健康筛选用)。"""
    wn = wntr.network.WaterNetworkModel(INP)
    wn.options.quality.parameter = "NONE"
    wn.options.time.duration = 24 * 3600
    wn.options.time.hydraulic_timestep = 900
    wn.options.time.report_timestep = 900
    wn.options.hydraulic.demand_model = "PDD"
    wn.options.hydraulic.required_pressure = 20.0
    wn.options.hydraulic.minimum_pressure = 0.0
    import tempfile
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        try:
            os.chdir(td)
            res = wntr.sim.EpanetSimulator(wn).run_sim(version=2.2)
        finally:
            os.chdir(cwd)
    pr = res.node["pressure"]
    return {j: float(pr[j].min()) for j in wn.junction_name_list}, wn


def node_demand_lps(wn, j):
    """junction 基础需水 (L/s) —— v2 硬筛: >0 方为真实供水节点。"""
    return float(sum(d.base_value for d in wn.get_node(j).demand_timeseries_list)) * 1000.0


def makeup_lps(g):
    return round(min(20.0, max(2.0, 0.03 * g["Pmax"])), 1)


def build(save=True):
    gens_all = load_gens()
    assert len(gens_all) == 54, f"gen.csv 应含 54 台机, 实得 {len(gens_all)}"
    by_bus = {g["bus"]: g for g in gens_all}
    dist = json.load(open(DIST_JSON))
    tfail = dist["tfail_h"]
    minhead, wn = baseline_min_head()

    # ---- 硬筛校验: 真实供水 + 基线健康 + 会失压 ----
    checks = []
    for j in COUPLED_JUNCTIONS:
        assert j in wn.junction_name_list, f"{j} 不在 D-town junction 列表中"
        dm = node_demand_lps(wn, j)
        mh = minhead[j]
        tf = tfail.get(j)
        checks.append(dict(junction=j, demand_Lps=round(dm, 4),
                           elev_m=round(float(wn.get_node(j).elevation), 2),
                           min_head0_m=round(mh, 1), t_fail_h=tf,
                           pass_supply=(dm > 0.0),
                           pass_healthy=(mh > HEALTHY_MIN_HEAD),
                           pass_fails=(tf is not None)))
        bad = [k for k, v in (("需水量>0", dm > 0.0),
                              (f"基线min压头>{HEALTHY_MIN_HEAD}m", mh > HEALTHY_MIN_HEAD),
                              ("72h内失压", tf is not None)) if not v]
        assert not bad, f"取水节点 {j} 未通过硬筛: {bad}"

    # ---- rank↔rank 确定性配对: 节点按 t_fail 升序 × 机组按 Pg 降序 ----
    js = sorted(COUPLED_JUNCTIONS, key=lambda j: (tfail[j], j))
    gs = sorted((by_bus[b] for b in COUPLED_BUSES), key=lambda g: (-g["Pg"], g["bus"]))
    assert len(js) == len(gs) == N_COUPLED

    def dma_of(j):
        try:
            p = wn.get_node(j).demand_timeseries_list[0].pattern
            return p.name if p is not None else "none"
        except Exception:
            return "none"

    rows = []
    for rank, (g, j) in enumerate(zip(gs, js), start=1):
        rows.append(dict(rank=rank, gen_id=g["gen_id"], bus=g["bus"],
                         Pg_MW=g["Pg"], Pmax_MW=g["Pmax"],
                         junction=j,
                         elev_m=round(float(wn.get_node(j).elevation), 1),
                         demand_Lps=round(node_demand_lps(wn, j), 4),
                         min_head0_m=round(minhead[j], 1),
                         t_fail_h=tfail[j],
                         dma=dma_of(j), makeup_Lps=makeup_lps(g)))

    # 供下游/论文引用的排序键 (与 rank 一致)
    rows.sort(key=lambda r: r["rank"])

    out = dict(
        version="v2",
        source=dist["source"], network="DTOWN.inp",
        rule=dict(
            units="研究者指定 6 台大出力凝汽式机组 bus 89/80/10/66/65/26 (ΣPg=2631 MW)",
            intakes="研究者指定 6 个 D-town 真实供水 junction "
                    "J102/J97/J198/J5/J217/J177 (均 DMA1)",
            hard_filter=[f"demand_Lps > 0 (真实供水; D-town 399 节点中 51 个零需水)",
                         f"baseline 24h EPS min head > {HEALTHY_MIN_HEAD} m",
                         "t_fail 存在于 72h 观测窗内 (会真正触发级联)"],
            assign="rank↔rank: 取水节点按 t_fail 升序 × 机组按 Pg 降序 (最严苛组合)",
            makeup="clip(0.03*Pmax, 2, 20) L/s (单一规则, 无特例); 不反馈进城市水力",
            stratification="v2 取消 Q1–Q5 失压时刻分层 (无 stratum 字段); "
                           "图4/图5 相应取消分层着色与分层行序"),
        hard_filter_checks=checks,
        n_coupled=len(rows), n_junctions=len(tfail),
        n_junctions_zero_demand=sum(1 for j in tfail
                                    if node_demand_lps(wn, j) <= 0.0),
        sigma_Pg_MW=round(sum(r["Pg_MW"] for r in rows), 1),
        makeup_total_Lps=round(sum(r["makeup_Lps"] for r in rows), 1),
        t_fail_span_h=[min(r["t_fail_h"] for r in rows),
                       max(r["t_fail_h"] for r in rows)],
        map=rows)

    if save:
        os.makedirs(RES, exist_ok=True)
        with open(os.path.join(RES, "coupling_map.json"), "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        keys = ["rank", "gen_id", "bus", "Pg_MW", "Pmax_MW", "junction",
                "elev_m", "demand_Lps", "min_head0_m", "t_fail_h", "dma",
                "makeup_Lps"]
        with open(os.path.join(RES, "coupling_map.csv"), "w", newline="") as f:
            wd = csv.DictWriter(f, fieldnames=keys)
            wd.writeheader()
            for r in rows:
                wd.writerow({k: r[k] for k in keys})
        print("saved coupling_map.json / coupling_map.csv")
    return out, dist, wn


def plot(out, dist, wn, save=True):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
    import figstyle  # noqa
    from figstyle import COLORS, SAVE

    nc = {n: wn.get_node(n).coordinates for n in wn.node_name_list}

    fig, ax = plt.subplots(figsize=(9.5, 8.0))
    ax.grid(False)
    segs = [[nc[l.start_node_name], nc[l.end_node_name]] for l in
            [wn.get_link(x) for x in wn.pipe_name_list]]
    ax.add_collection(LineCollection(segs, colors="#dddddd", linewidths=0.4, zorder=1))

    # v2: 取消 Q1–Q5 分层着色 —— 6 个耦合节点统一语义色 + 失压时刻标注
    for r in out["map"]:
        x, y = nc[r["junction"]]
        ax.scatter([x], [y], s=130, c=COLORS["cool"], edgecolor="k",
                   linewidths=0.9, zorder=4)
        ax.annotate(f"bus{r['bus']} ← {r['junction']}\n"
                    f"t_fail={r['t_fail_h']:.2f} h  Pg={r['Pg_MW']:.0f} MW",
                    (x, y), textcoords="offset points", xytext=(9, 7),
                    fontsize=9, fontweight="bold", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.22", fc="white",
                              ec="#bbbbbb", lw=0.5, alpha=0.9))
    _px, _py = [], []
    for _pn in wn.pump_name_list:
        _lk = wn.get_link(_pn)
        _a = nc[_lk.start_node_name]; _b = nc[_lk.end_node_name]
        _px.append(0.5 * (_a[0] + _b[0])); _py.append(0.5 * (_a[1] + _b[1]))
    ax.scatter(_px, _py, s=110, facecolor="white", edgecolor="#333333",
               linewidths=1.0, zorder=5)
    ax.scatter(_px, _py, s=42, marker="^", facecolor="#5b6b7a",
               edgecolor="#333333", linewidths=0.5, zorder=6)
    rc = nc["R1"]
    ax.scatter([rc[0]], [rc[1]], marker="s", s=110, c="#1a1a1a", zorder=6,
               label="Source R1")
    ax.scatter([], [], s=130, c=COLORS["cool"], edgecolor="k", linewidths=0.9,
               label=f"coupled intake nodes (n={out['n_coupled']})")
    ax.scatter([], [], s=110, facecolor="white", edgecolor="#333333",
               linewidths=1.0, label="Pumps")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    ax.legend(fontsize=9.5, loc="lower left")
    ax.set_title("Designated coupling map: 6 thermal units ↔ 6 D-town intake junctions\n"
                 "(all intakes verified as real supply nodes: base demand > 0)",
                 fontsize=11.5)
    fig.tight_layout()
    if save:
        p = os.path.join(RES, "coupling_map.png")
        fig.savefig(p, **SAVE)
        print("saved", os.path.abspath(p))
    plt.close(fig)


if __name__ == "__main__":
    out, dist, wn = build()
    plot(out, dist, wn)
    print("=" * 86)
    print(" 指定耦合映射 v2: %d 台机组 ↔ %d 个取水 junction (D-town %d junction, 其中 %d 个零需水)"
          % (out["n_coupled"], out["n_coupled"], out["n_junctions"],
             out["n_junctions_zero_demand"]))
    print("=" * 86)
    print(" ΣPg = %.1f MW;  额定补水合计 = %.1f L/s;  失压时刻跨度 = %.2f–%.2f h (B-ST)"
          % (out["sigma_Pg_MW"], out["makeup_total_Lps"],
             out["t_fail_span_h"][0], out["t_fail_span_h"][1]))
    print("-" * 86)
    print(" 硬筛校验 (需水>0 / 基线健康 / 72h内失压):")
    for c in out["hard_filter_checks"]:
        print("   %-6s demand=%7.4f L/s  elev=%6.2f m  min_head0=%5.1f m  t_fail=%5.2f h  %s%s%s"
              % (c["junction"], c["demand_Lps"], c["elev_m"], c["min_head0_m"],
                 c["t_fail_h"], "✅" if c["pass_supply"] else "❌",
                 "✅" if c["pass_healthy"] else "❌",
                 "✅" if c["pass_fails"] else "❌"))
    print("-" * 86)
    print(" rank↔rank 配对 (节点按 t_fail 升序 × 机组按 Pg 降序):")
    for r in out["map"]:
        print("   #%d  bus%-4d (%6.1f/%6.1f MW) ← %-6s  %s  demand=%7.4f L/s  "
              "t_fail=%5.2f h  makeup=%4.1f L/s"
              % (r["rank"], r["bus"], r["Pg_MW"], r["Pmax_MW"], r["junction"],
                 r["dma"], r["demand_Lps"], r["t_fail_h"], r["makeup_Lps"]))
