# IEEE 118-Bus 直流潮流标准算例

用于 DC-PF 仿真。

本文件夹包含：

| 文件 | 说明 |
|---|---|
| `case118.m` | MATPOWER 原版，MATLAB 可用 |
| `case118.py` | PYPOWER 版，Python 可用 |
| `bus.csv` | 118 个节点，Pd/Qd/Vm/Va/baseKV |
| `branch.csv` | 186 条支路，r/x/b/ratio |
| `gen.csv` | 54 台发电机，Pg/Pmax/Pmin |
| `dcpf_ieee118.py` | 纯 numpy 直流潮流求解器 |
| `dc_results_bus.csv` | DC-PF 节点角度结果 |
| `dc_results_branch.csv` | DC-PF 支路潮流结果 |
| `report_ieee118_dcpf.html` | 直流潮流计算报告（含图表，可直接浏览器打开） |

系统规模：
- 118 buses, 186 branches, 54 generators
- 总负荷 4242 MW
- Slack bus: 69
- baseMVA = 100

## 快速使用

```bash
pip install numpy pandas pypower
python dcpf_ieee118.py
```

运行 `dcpf_ieee118.py` 会从 `bus.csv` / `branch.csv` / `gen.csv` 读取数据，
用纯 NumPy 求解直流潮流，并把结果写入 `dc_results_bus.csv` 与
`dc_results_branch.csv`。

### 纯 NumPy 求解器输出（已校验）

```
 angle range    : -19.800 .. 11.185 deg   (以 slack=30° 为参考)
 max |Pflow|    : 450.00 MW
 slack inject   : 381.00 MW
```

求解器结果已与 PYPOWER `rundcpf` 交叉校验：
- 节点相角误差 < 5e-5 度
- 支路潮流误差 < 5e-4 MW

### PYPOWER 一行

```python
from pypower.api import case118, rundcpf
ppc = case118()
r = rundcpf(ppc)
```

### pandapower 一行

```python
import pandapower.networks as pn, pandapower as pp
net = pn.case118()
pp.rundcpp(net)
```

## 直流潮流模型

直流潮流假设：
1. 所有电压幅值 |V| = 1.0 p.u.
2. 支路电阻 r << x，忽略电阻（只用电抗 x）
3. 电压相角差很小，sin(θ) ≈ θ, cos(θ) ≈ 1
4. 忽略无功与网损

线性方程 `P = B' · θ`，去掉 slack 母线行列后求解相角 θ，
再回代求支路潮流 `P_ij = (θ_i − θ_j) / x_ij`。

## 数据文件字段

- `bus.csv` : `bus_id, type, Pd, Qd, Vm, Va, baseKV`
- `branch.csv` : `from_bus, to_bus, r, x, b, ratio, angle, status`
- `gen.csv` : `gen_id, bus, Pg, Qg, Vg, Pmax, Pmin`

## 来源

- MATPOWER: https://github.com/MATPOWER/matpower/blob/master/data/case118.m
- PYPOWER: https://github.com/rwl/PYPOWER
- 原始 IEEE CDF: https://labs.ece.uw.edu/pstca/
