"""
P5 扩展(2/2) —— 预警可靠性与鲁棒预警-处置策略
================================================
现实中信息/工控系统(ICS)的预警并不完美:
  - 漏报(missed detection): 预警根本没到 -> 电网被动 -> 深跌
  - 时延抖动(lead jitter): 预警提前量随机 -> 处置窗口不确定
  - 误报(false alarm): 无故障却预警 -> 若采取切负荷=不必要代价

本脚本用蒙特卡洛评估不同"处置策略"在预警不确定下的**风险分布**,
并比较三类策略的期望韧性与尾部风险(是否会崩溃/触发UFLS):
  S-Reactive : 纯被动(不依赖预警)
  S-Trust    : 完全信任预警(仅预置备用, 不预防性切负荷)
  S-Robust   : 鲁棒策略(即使预警到达, 也保留一定预防性切负荷托底)

依赖 results/p5_lookup.json (由 build_lookup.py 生成)。
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "results")
for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp); plt.rcParams["font.family"] = "Noto Sans CJK JP"; break
plt.rcParams["axes.unicode_minus"] = False

LUT = json.load(open(os.path.join(RESDIR, "p5_lookup.json")))
SAFE_TH, UFLS_TH, COLLAPSE_TH = 49.0, 48.0, 47.0


def fnadir(sc, lead, shed):
    """在查找表上双线性(lead,shed)插值 f_nadir。lead<0 视为0(无预警)。"""
    lead = max(0.0, lead)
    leads = np.array(LUT["leads"], float)
    sheds = np.array(LUT["sheds"], float)
    tbl = LUT["lut"][str(sc)]
    # clamp
    lead = min(lead, leads.max()); shed = min(max(shed, 0.0), sheds.max())
    # 邻近网格
    li = np.searchsorted(leads, lead); li0 = max(0, li-1); li1 = min(len(leads)-1, li)
    si = np.searchsorted(sheds, shed); si0 = max(0, si-1); si1 = min(len(sheds)-1, si)
    def g(a, b): return tbl[str(int(leads[a]))][str(sheds[b])]
    l0, l1 = leads[li0], leads[li1]; s0, s1 = sheds[si0], sheds[si1]
    wl = 0.0 if l1 == l0 else (lead-l0)/(l1-l0)
    ws = 0.0 if s1 == s0 else (shed-s0)/(s1-s0)
    v = (g(li0,si0)*(1-wl)*(1-ws) + g(li1,si0)*wl*(1-ws)
         + g(li0,si1)*(1-wl)*ws + g(li1,si1)*wl*ws)
    return v


def simulate_strategy(sc, strategy, n=20000, seed=0,
                      p_miss=0.15, lead_mean=8.0, lead_std=3.0,
                      p_false=0.10):
    """蒙特卡洛: 返回该策略在故障(sc)下的 f_nadir 样本 + 误报代价样本。
    strategy: dict(shed_on_warn=..., shed_always=...)
      shed_always: 无论预警是否到达都预置的切负荷(托底)
      shed_on_warn: 收到预警后额外的切负荷
    """
    rng = np.random.default_rng(seed)
    nadirs = np.empty(n)
    for i in range(n):
        warned = rng.random() > p_miss                 # 是否收到预警
        if warned:
            lead = max(0.0, rng.normal(lead_mean, lead_std))
            shed = strategy["shed_always"] + strategy["shed_on_warn"]
        else:
            lead = 0.0
            shed = strategy["shed_always"]             # 漏报时只有托底切负荷
        nadirs[i] = fnadir(sc, lead, shed)
    # 误报代价: 期望不必要切负荷(仅托底部分, 因为误报时无故障却常备切负荷)
    false_cost = p_false * strategy["shed_always"] * 100.0   # %负荷·概率
    return nadirs, false_cost


def risk_metrics(nadirs):
    return dict(
        mean=float(nadirs.mean()),
        p_ufls=float((nadirs < UFLS_TH).mean()),        # 触发UFLS概率
        p_collapse=float((nadirs < COLLAPSE_TH).mean()), # 崩溃概率
        cvar5=float(np.sort(nadirs)[:max(1, len(nadirs)//20)].mean()),  # 5%最差期望(尾部)
    )


def run_for_scale(sc):
    strategies = {
        "S-Reactive (纯被动)":     dict(shed_always=0.0,  shed_on_warn=0.0),
        "S-Trust (信任预警,仅预置备用)": dict(shed_always=0.0,  shed_on_warn=0.0 if sc<=3 else 0.10),
        "S-Robust (鲁棒,托底切负荷)":  dict(shed_always=0.05, shed_on_warn=0.05 if sc<=3 else 0.10),
    }
    # 注: S-Trust 对小故障靠备用即可(shed=0); 大故障收到预警才切
    res = {}
    for name, st in strategies.items():
        nd, fc = simulate_strategy(sc, st)
        m = risk_metrics(nd); m["false_cost"] = fc; m["nadirs"] = nd; m["strat"] = st
        res[name] = m
    return res


def plot(all_res, outname="p5_reliability.png"):
    scales = sorted(all_res.keys())
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.8))
    fig.suptitle("P5 扩展 —— 预警不确定下的鲁棒策略风险评估 (蒙特卡洛, 漏报15%/时延抖动)",
                 fontsize=13.5, fontweight="bold")
    names = list(next(iter(all_res.values())).keys())
    colors = {"S-Reactive (纯被动)": "#c0392b",
              "S-Trust (信任预警,仅预置备用)": "#e08a1e",
              "S-Robust (鲁棒,托底切负荷)": "#1f6fb2"}

    # 图1: 期望 f_nadir vs 规模
    a = ax[0]
    x = np.arange(len(scales)); w = 0.26
    for k, nm in enumerate(names):
        vals = [all_res[sc][nm]["mean"] for sc in scales]
        a.bar(x + (k-1)*w, vals, w, label=nm, color=colors[nm])
    a.axhline(SAFE_TH, color="green", ls="--", lw=1, label="安全 49Hz")
    a.axhline(COLLAPSE_TH, color="darkred", ls=":", lw=1, label="崩溃 47Hz")
    a.set_xticks(x); a.set_xticklabels([f"{sc}机" for sc in scales])
    a.set_ylim(44, 50.3); a.set_ylabel("期望频率最低点 (Hz)")
    a.set_title("① 期望韧性"); a.legend(fontsize=7.5); a.grid(axis="y", alpha=.3)

    # 图2: 崩溃/UFLS 概率(尾部风险)
    a = ax[1]
    for k, nm in enumerate(names):
        vals = [all_res[sc][nm]["p_collapse"]*100 for sc in scales]
        a.bar(x + (k-1)*w, vals, w, label=nm, color=colors[nm])
    a.set_xticks(x); a.set_xticklabels([f"{sc}机" for sc in scales])
    a.set_ylabel("崩溃概率 P(f<47Hz) (%)")
    a.set_title("② 尾部风险(崩溃概率)"); a.legend(fontsize=7.5); a.grid(axis="y", alpha=.3)

    # 图3: 4机故障 f_nadir 分布(直方图)
    a = ax[2]
    sc = 4 if 4 in scales else scales[-1]
    for nm in names:
        a.hist(all_res[sc][nm]["nadirs"], bins=40, alpha=0.5, label=nm, color=colors[nm])
    a.axvline(SAFE_TH, color="green", ls="--", lw=1)
    a.axvline(COLLAPSE_TH, color="darkred", ls=":", lw=1)
    a.set_xlabel("f_nadir (Hz)"); a.set_ylabel("样本数")
    a.set_title(f"③ {sc}机故障 韧性分布"); a.legend(fontsize=7.5)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(RESDIR, outname); fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig); print("saved", out)


def main():
    all_res = {sc: run_for_scale(sc) for sc in LUT["scales"]}
    plot(all_res)
    # 导出(去掉大数组)
    obj = {}
    for sc, r in all_res.items():
        obj[str(sc)] = {nm: {k: round(v, 4) for k, v in m.items()
                             if k not in ("nadirs", "strat")}
                        for nm, m in r.items()}
    json.dump(obj, open(os.path.join(RESDIR, "p5_reliability.json"), "w"),
              ensure_ascii=False, indent=2)
    print("saved p5_reliability.json")
    # 控制台摘要
    print("\n=== 预警不确定下 各策略风险 (漏报15%) ===")
    for sc in LUT["scales"]:
        print(f"\n {sc}机共因故障:")
        for nm, m in all_res[sc].items():
            print(f"  {nm:<28} 期望f={m['mean']:.2f}Hz  "
                  f"崩溃P={m['p_collapse']*100:4.1f}%  UFLS_P={m['p_ufls']*100:4.1f}%  "
                  f"5%尾部={m['cvar5']:.2f}Hz")


if __name__ == "__main__":
    main()
