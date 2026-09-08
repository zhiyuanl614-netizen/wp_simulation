"""
全耦合映射 —— IEEE-118 全部 54 台发电机 ↔ D-town 取水 junction
================================================================
定位: 把"整城市供水-电力耦合系统"的耦合从 3 对指定配对扩展为【全耦合】:
54 台发电机(含平衡机)每台各有一个配水取水节点。设计见 docs/coupling_map.md。

耦合规则 (v1, 可复现):
  1. 保留已校验三对: bus89-J411, bus80-J371, bus10-J197 (沿用全部既有结果)。
  2. 基线健康筛选: 无故障 24h EPS 仿真, 候选 junction 需全程最小压头 > 32 m
     (正常可为高位补水箱补水; 与 saet_distribution.py 的健康判据一致)。
  3. 分层比例抽样: 按"唯一水源停供后失压时刻"把候选节点分为
     Q1(快)/Q2/Q3/Q4(慢)/never(72h 不失压) 五层; 51 个新耦合名额按各层节点数
     占全网比例分配(最大余数法), 层内按失压时刻等间距抽取 —— 使耦合节点集合的
     失压时刻分布复现全网分布, 不人为挑选。
  4. 确定性分配: 其余 51 台机按 bus 号升序, 与抽取节点按 (t_fail, 节点名) 升序
     一一配对; 不隐含"容量-位置"相关性。
  5. 补水负荷(供后续边界重跑用): makeup_Lps = clip(0.03*Pmax, 2, 20), 保留对=20。

输出:
  results/muni/coupling_map.json   全耦合表 + 规则 + 分层统计
  results/muni/coupling_map.csv    同上 (表格版)
  results/muni/coupling_map.png    空间总览 (D-town 上标出 54 个耦合节点)

数据来源 (CC-BY-NC 4.0, 须署名): Ostfeld, Avi. "05 Long Term Improvement" (D-town)
(2016). Battle of the Water Network Models. Univ. of Kentucky Libraries.
https://uknowledge.uky.edu/wdst_models/5
"""
import os, sys, json, csv, math
import numpy as np
import wntr

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "data", "DTOWN.inp")
RES = os.path.join(HERE, "..", "..", "results", "muni")
GEN_CSV = os.path.join(HERE, "..", "..", "..", "ieee118_dc", "gen.csv")
DIST_JSON = os.path.join(RES, "saet_distribution.json")

HEALTHY_MIN_HEAD = 32.0          # m, 基线健康判据 (与 saet_distribution 一致)
PRESERVED = {89: "J411", 80: "J371", 10: "J197"}   # 已校验三对, 原样保留
STRATA = ["Q1_fast", "Q2", "Q3", "Q4_slow", "never"]


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


def makeup_lps(g):
    if g["bus"] in PRESERVED:
        return 20.0
    return round(min(20.0, max(2.0, 0.03 * g["Pmax"])), 1)


def build(save=True):
    gens = load_gens()
    assert len(gens) == 54, f"gen.csv 应含 54 台机, 实得 {len(gens)}"
    dist = json.load(open(DIST_JSON))
    tfail = dist["tfail_h"]
    minhead, wn = baseline_min_head()

    used = set(PRESERVED.values())
    cand = [j for j in wn.junction_name_list
            if minhead[j] > HEALTHY_MIN_HEAD and j not in used and j in tfail]

    # ---- 分层: 有限失压时刻四分位 + never ----
    finite = np.array([tfail[j] for j in cand if tfail[j] is not None])
    q25, q50, q75 = np.percentile(finite, [25, 50, 75])

    def strat_of(j):
        t = tfail[j]
        if t is None:
            return "never"
        if t < q25:
            return "Q1_fast"
        if t < q50:
            return "Q2"
        if t < q75:
            return "Q3"
        return "Q4_slow"

    members = {s: sorted([j for j in cand if strat_of(j) == s],
                         key=lambda j: (tfail[j] if tfail[j] is not None else 1e9, j))
               for s in STRATA}

    # ---- 51 个名额按各层占【全网】比例分配 (最大余数, 含封顶与再分配) ----
    n_new = len(gens) - len(PRESERVED)              # 51
    allj = list(tfail.keys())
    w = {s: sum(1 for j in allj if strat_of(j) == s) for s in STRATA}
    totw = sum(w.values())
    alloc = {s: min(int(math.floor(n_new * w[s] / totw)), len(members[s])) for s in STRATA}
    rem = n_new - sum(alloc.values())
    order = sorted(STRATA, key=lambda s: -((n_new * w[s] / totw) % 1))
    while rem > 0:
        moved = False
        for s in order:
            if alloc[s] < len(members[s]):
                alloc[s] += 1
                rem -= 1
                moved = True
                if rem == 0:
                    break
        if not moved:
            raise RuntimeError("候选节点不足, 无法完成全耦合分配")

    # ---- 层内等间距抽取 ----
    picked = []
    for s in STRATA:
        m, k = members[s], alloc[s]
        if k <= 0:
            continue
        idx = np.round(np.linspace(0, len(m) - 1, k)).astype(int) if k > 1 else [len(m) // 2]
        picked += [(m[i], s) for i in idx]
    assert len(picked) == n_new and len({p for p, _ in picked}) == n_new

    # ---- 确定性配对: bus 升序 × (t_fail, 节点名) 升序 ----
    picked.sort(key=lambda pj: (tfail[pj[0]] if tfail[pj[0]] is not None else 1e9, pj[0]))
    new_gens = sorted([g for g in gens if g["bus"] not in PRESERVED],
                      key=lambda g: g["bus"])
    pairs = {g["bus"]: (j, s) for g, (j, s) in zip(new_gens, picked)}

    def dma_of(j):
        try:
            p = wn.get_node(j).demand_timeseries_list[0].pattern
            return p.name if p is not None else "none"
        except Exception:
            return "none"

    rows = []
    for g in gens:
        b = g["bus"]
        if b in PRESERVED:
            j, s = PRESERVED[b], strat_of(PRESERVED[b])
        else:
            j, s = pairs[b]
        rows.append(dict(gen_id=g["gen_id"], bus=b, Pg_MW=g["Pg"], Pmax_MW=g["Pmax"],
                         junction=j, stratum=s,
                         elev_m=round(float(wn.get_node(j).elevation), 1),
                         min_head0_m=round(minhead[j], 1),
                         t_fail_h=tfail[j],
                         dma=dma_of(j), makeup_Lps=makeup_lps(g),
                         preserved=(b in PRESERVED)))

    out = dict(
        version="v1",
        source=dist["source"], network="DTOWN.inp",
        rule=dict(
            preserved="bus89-J411 / bus80-J371 / bus10-J197 (已校验, 原样保留)",
            health=f"baseline 24h EPS min head > {HEALTHY_MIN_HEAD} m",
            stratify="失压时刻四分位 Q1-Q4 + never 五层, 名额按全网占比(最大余数法)",
            within="层内按 t_fail 等间距抽取",
            assign="bus 升序 × (t_fail, 节点名) 升序 确定性配对",
            makeup="clip(0.03*Pmax, 2, 20) L/s; 保留对=20"),
        quartiles_h=dict(q25=round(float(q25), 2), q50=round(float(q50), 2),
                         q75=round(float(q75), 2)),
        strata_alloc={s: alloc[s] for s in STRATA},
        n_coupled=len(rows), n_junctions=len(allj),
        map=rows)

    if save:
        os.makedirs(RES, exist_ok=True)
        with open(os.path.join(RES, "coupling_map.json"), "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        keys = ["gen_id", "bus", "Pg_MW", "Pmax_MW", "junction", "stratum",
                "elev_m", "min_head0_m", "t_fail_h", "dma", "makeup_Lps", "preserved"]
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

    COL = {"Q1_fast": COLORS["power"], "Q2": COLORS["amber"], "Q3": COLORS["muni"],
           "Q4_slow": COLORS["ok"], "never": "#8a97a3"}
    nc = {n: wn.get_node(n).coordinates for n in wn.node_name_list}

    fig, ax = plt.subplots(figsize=(9.5, 8.0))
    ax.grid(False)
    segs = [[nc[l.start_node_name], nc[l.end_node_name]] for l in
            [wn.get_link(x) for x in wn.pipe_name_list]]
    ax.add_collection(LineCollection(segs, colors="#dddddd", linewidths=0.4, zorder=1))
    for s in STRATA:
        pts = [r for r in out["map"] if r["stratum"] == s]
        xs = [nc[r["junction"]][0] for r in pts]
        ys = [nc[r["junction"]][1] for r in pts]
        ax.scatter(xs, ys, s=46, c=COL[s], edgecolor="k", linewidths=0.6, zorder=3,
                   label=f"{s} (n={len(pts)})")
    for r in out["map"]:
        if r["preserved"]:
            ax.scatter([nc[r["junction"]][0]], [nc[r["junction"]][1]], marker="*",
                       s=260, facecolor=COL[r["stratum"]], edgecolor="k",
                       linewidths=1.2, zorder=5)
            ax.annotate(f"bus{r['bus']}", (nc[r["junction"]][0], nc[r["junction"]][1]),
                        textcoords="offset points", xytext=(7, 6), fontsize=8,
                        fontweight="bold")
    rc = nc["R1"]
    ax.scatter([rc[0]], [rc[1]], marker="s", s=90, c="#1a1a1a", zorder=6,
               label="Source R1")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    ax.legend(fontsize=8.5, loc="lower left", title="coupled intake strata "
              "(★ = preserved pairs)")
    ax.set_title("Full coupling map: all 54 generators ↔ D-town intake junctions\n"
                 "(stratified by source-outage depressurization time)", fontsize=11.5)
    fig.tight_layout()
    if save:
        p = os.path.join(RES, "coupling_map.png")
        fig.savefig(p, **SAVE)
        print("saved", os.path.abspath(p))
    plt.close(fig)


if __name__ == "__main__":
    out, dist, wn = build()
    plot(out, dist, wn)
    print("=" * 78)
    print(" 全耦合映射: %d 台发电机 ↔ %d 个取水 junction (D-town 399 junction)"
          % (out["n_coupled"], out["n_coupled"]))
    print("=" * 78)
    print(" 分层名额:", out["strata_alloc"], " 四分位(h):", out["quartiles_h"])
    tf = [r["t_fail_h"] for r in out["map"] if r["t_fail_h"] is not None]
    print(" 耦合节点失压时刻: min %.1f / 中位 %.1f / max %.1f h; never=%d 台"
          % (min(tf), float(np.median(tf)), max(tf),
             sum(1 for r in out["map"] if r["t_fail_h"] is None)))
    print("-" * 78)
    for r in out["map"]:
        print("  gen%02d bus%-3d (%4.0f/%4.0f MW) <- %-6s %-8s t_fail=%s h  %s"
              % (r["gen_id"], r["bus"], r["Pg_MW"], r["Pmax_MW"], r["junction"],
                 r["stratum"],
                 "-" if r["t_fail_h"] is None else f"{r['t_fail_h']:.2f}",
                 "★保留" if r["preserved"] else ""))
