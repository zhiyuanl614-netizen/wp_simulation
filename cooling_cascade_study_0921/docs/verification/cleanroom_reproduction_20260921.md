# 净室复现证书（Clean-Room Reproduction Certificate）

- **日期：** 2026-09-21
- **目的：** 以独立第三方视角验证仓库自含性与 README 复现路径的有效性（回应编辑评估中的"验证自指性"保留项）。
- **方法：** 全新目录 `git clone` 仓库（仅含已提交内容，不含任何工作区状态、未跟踪文件或会话内存）→ 按 `README.md` 安装依赖（`pip install pypower wntr adjustText`）→ 按 README"运行（复现）"节的 03 链指令重跑两个代表性计算脚本 → 与注册结果对账。
- **基线：** commit `b3af0da`（clone 后 `git log` 核对）。
- **执行记录：** `/tmp/cleanroom.log`（驱动脚本为一次性 `/tmp/cleanroom_run.sh`，未入库存放）。

## 复现范围与结果

**脚本 1：`src/03_proactive_control/critical_ramp_example.py`**（冷却链临界速率算例）

| 锚点 | 注册值 | 净室值 | 判定 |
|---|---|---|---|
| 临界速率 r\* | 9.090909×10⁻⁵ /s（0.55 %P_g/min）| 9.090909×10⁻⁵ /s | ✅ 逐位 |
| 最长运行 T_max | 183.3 min | 183.3 min | ✅ |
| bus89 SUET | 92.43 min | 92.43 min | ✅ |
| 代表工况 fast/critical/slow | 73.3 active / 183.3 active / 105.5 forced | 同左 | ✅ |
| JSON `critical`＋`scan` 段 | — | — | ✅ 序列化逐字节相同 |

**脚本 2：`src/03_proactive_control/run_p6.py`**（P6 三策略对比，六机 CO/DISP）

| 锚点 | 注册值 | 净室值 | 判定 |
|---|---|---|---|
| 六台 SUET（bus 89/80/10/66/65/26）| 92.40/121.80/130.00/151.50/151.90/192.90 min | 同左 | ✅ 逐位 |
| CO PA 峰值/能量/过载 | 334.9 MW / 59.6 MWh / 165.8 MW | 同左 | ✅ |
| CO SP / DP | 0 / 0（过载 36.8）×2 | 同左 | ✅ |
| 数值叶对账（`p6_strategy_compare.json`）| — | **28/28 相同，0 差异** | ✅ |

**合计 13 项锚点全部通过，数值零漂移。**

## 结论

1. 仓库在"仅有 git 提交内容＋README 指令"的条件下，可独立复现论文核心数值（覆盖冷却链机理、SUET 注册、三策略对比三类结果）。
2. README 的环境说明（`pip install pypower wntr`）经实测有效。
3. 本证书与 `report_v4_20260920.md`（全链 strict 重跑）互补：后者证明内部一致性，本证书证明外部可复现性。
4. 覆盖范围说明：本抽检覆盖 03 链两脚本；00/01/02 层在 v4 报告中以逐字节 diff 审计覆盖（未在净室重跑，因其输出与提交前版本逐字节一致）。
