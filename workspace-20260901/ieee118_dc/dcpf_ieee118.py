#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dcpf_ieee118.py
================
纯 NumPy 实现的 IEEE 118 节点直流潮流 (DC Power Flow) 求解器。

直流潮流假设：
    1. 所有电压幅值 |V| = 1.0 p.u.
    2. 支路电阻 r << x，忽略电阻 (只用电抗 x)
    3. 电压相角差很小，sin(θ) ≈ θ, cos(θ) ≈ 1
    4. 忽略无功与网损

线性方程：
        P = B' * θ
其中 B' 为节点电纳矩阵 (由 1/x 组成)，P 为节点净注入有功 (标幺)。
去掉 slack 母线所在行/列后求解 θ，再回代求各支路潮流：
        P_ij = (θ_i - θ_j) / x_ij

用法：
    python dcpf_ieee118.py
    # 从 bus.csv / branch.csv / gen.csv 读取数据
    # 结果写入 dc_results_bus.csv 与 dc_results_branch.csv
"""

import numpy as np
import pandas as pd

BASEMVA = 100.0
SLACK_BUS = 69   # IEEE 118 标准 slack (type == 3)


def load_data(bus_csv="bus.csv", branch_csv="branch.csv", gen_csv="gen.csv"):
    bus = pd.read_csv(bus_csv)
    branch = pd.read_csv(branch_csv)
    gen = pd.read_csv(gen_csv)
    return bus, branch, gen


def build_bdc(bus, branch):
    """构造 DC 电纳矩阵 B'（节点 x 节点），返回矩阵与母线索引映射。"""
    ids = bus["bus_id"].to_numpy()
    n = len(ids)
    idx = {b: i for i, b in enumerate(ids)}      # bus_id -> 0..n-1

    B = np.zeros((n, n))
    for _, row in branch.iterrows():
        if int(row.get("status", 1)) == 0:
            continue
        f, t = int(row["from_bus"]), int(row["to_bus"])
        x = float(row["x"])
        if x == 0.0:
            continue
        ratio = float(row.get("ratio", 0.0)) or 1.0   # 0 视为 1
        b = 1.0 / (x * ratio)
        i, j = idx[f], idx[t]
        B[i, i] += b
        B[j, j] += b
        B[i, j] -= b
        B[j, i] -= b
    return B, idx, ids


def net_injection(bus, gen, idx):
    """节点净有功注入 P = Pg - Pd （标幺）。"""
    n = len(idx)
    P = np.zeros(n)
    # 负荷
    for _, row in bus.iterrows():
        P[idx[int(row["bus_id"])]] -= float(row["Pd"]) / BASEMVA
    # 发电
    for _, row in gen.iterrows():
        P[idx[int(row["bus"])]] += float(row["Pg"]) / BASEMVA
    return P


def solve_dcpf(bus, branch, gen, slack=SLACK_BUS):
    B, idx, ids = build_bdc(bus, branch)
    P = net_injection(bus, gen, idx)

    s = idx[slack]
    n = len(ids)
    mask = np.ones(n, dtype=bool)
    mask[s] = False

    # slack 处平衡功率：使总注入守恒（DC 无损，slack 承担不平衡量）
    P[s] = -P[mask].sum()

    # 去掉 slack 行列后求解 θ
    Bred = B[np.ix_(mask, mask)]
    Pred = P[mask]
    # slack 参考角：取自 bus 数据中 slack 母线的 Va (标准算例为 30°)
    slack_va_deg = float(bus.loc[bus["bus_id"] == slack, "Va"].iloc[0])
    theta_ref = np.radians(slack_va_deg)

    theta = np.zeros(n)
    theta[mask] = np.linalg.solve(Bred, Pred) + theta_ref
    theta[s] = theta_ref

    # 支路潮流 (MW): P_ij = (θi - θj) / (x*ratio)
    flows = []
    for _, row in branch.iterrows():
        f, t = int(row["from_bus"]), int(row["to_bus"])
        x = float(row["x"])
        ratio = float(row.get("ratio", 0.0)) or 1.0
        status = int(row.get("status", 1))
        if status == 0 or x == 0.0:
            pf = 0.0
        else:
            pf = (theta[idx[f]] - theta[idx[t]]) / (x * ratio) * BASEMVA
        flows.append((f, t, pf))

    theta_deg = np.degrees(theta)
    return ids, theta, theta_deg, flows, P


def main():
    bus, branch, gen = load_data()
    ids, theta, theta_deg, flows, P = solve_dcpf(bus, branch, gen)

    bus_res = pd.DataFrame({
        "bus_id": ids.astype(int),
        "Va_deg": np.round(theta_deg, 4),
        "Va_rad": np.round(theta, 6),
        "Pnet_MW": np.round(P * BASEMVA, 3),
    })
    bus_res.to_csv("dc_results_bus.csv", index=False)

    br_res = pd.DataFrame(flows, columns=["from_bus", "to_bus", "Pflow_MW"])
    br_res["Pflow_MW"] = br_res["Pflow_MW"].round(3)
    br_res.to_csv("dc_results_branch.csv", index=False)

    print("=" * 56)
    print(" IEEE 118-Bus  DC Power Flow  (pure NumPy)")
    print("=" * 56)
    print(f" baseMVA        : {BASEMVA:.0f}")
    print(f" buses          : {len(ids)}")
    print(f" branches       : {len(flows)}")
    print(f" slack bus      : {SLACK_BUS}")
    print(f" total load     : {bus['Pd'].sum():.1f} MW")
    print(f" total gen      : {gen['Pg'].sum():.1f} MW")
    print("-" * 56)
    print(f" angle range    : {theta_deg.min():.3f} .. {theta_deg.max():.3f} deg")
    print(f" max |Pflow|    : {br_res['Pflow_MW'].abs().max():.2f} MW")
    print(f" slack inject   : {P[np.where(ids==SLACK_BUS)[0][0]]*BASEMVA:.2f} MW")
    print("-" * 56)
    print(" results -> dc_results_bus.csv , dc_results_branch.csv")
    print("=" * 56)


if __name__ == "__main__":
    main()
