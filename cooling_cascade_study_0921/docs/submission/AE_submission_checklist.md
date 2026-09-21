# Applied Energy 投稿就绪清单（2026-09-21）

> 依据 Elsevier/Applied Energy 投稿规范整理（第三方指南汇总，最终以 Editorial Manager 提交门户的即时校验为准）。

## 已完成项（本轮）

| 项 | 要求 | 状态 |
|---|---|---|
| 摘要 | ≤200–300 词（两来源不一致，取保守 200） | ✅ **191 词**（含时标分离归因从句；保留缺口定位、485.6→0、SUET 92.4–192.9、r\* 1.98×、瓶颈重定位） |
| 关键词 | 4–8 个 | ✅ 6 个（避开与题目纯重复，含 reserve adequacy） |
| Highlights | 3–5 条 × ≤85 字符（含空格，系统硬校验） | ✅ 5 条，62–79 字符（`论文完整版.md` 摘要块后，提交时单独粘贴） |
| Graphical abstract | 单栏，最小 531×1328 px | ✅ `figures/GraphicalAbstract_AppliedEnergy.png`（2221×1072 px，脚本 `scripts/make_graphical_abstract.py` 可复现） |
| 正文语言/节题 | 纯英文 | ✅ 双语节题已转纯英文；修复尾部致谢重复＋残片损伤 |
| 数据与代码可用性声明 | 必需 | ✅ 已有专节（Zenodo+DOI 计划；提交前补 CRediT/资助/利益声明） |
| 引用体例 | Elsevier 数字方括号＋DOI | ✅ [1]–[51]（#33 扩充后，27 篇新增全部联网核实；首现顺序编号） |
| 图件分辨率 | ≥300 dpi | ✅ 全部 300 dpi PNG（矢量版可按需再出） |
| 复现包 | — | ✅ v4 验证报告＋净室复现证书（见下） |
| Cover letter | — | ✅ `cover_letter_AppliedEnergy.md`（作者信息留待补齐） |

## ⚠️ 最大风险项：正文字数超标

**实测：正文 15,719 词**（不含表格/题注/显示公式；含题注 18,600）。

- AE 上限存在两说：**8,000 词**（多数第三方指南，正文口径，不含摘要/参考文献/题注/表格）或 **12,000 词**（全文口径）。无论按哪个口径，当前均**超标**，存在 desk-return 风险。
- **压缩方案（建议单独立轮执行，方案先行）：**

| 章 | 现词数 | 目标 | 手段 |
|---|---|---|---|
| ch2 方法 | 4,642 | ~2,400 | 推导细节、阈值四点论证、边界口径细则 → Supplementary Material，保留模型结构与关键方程 |
| ch3 案例 | 2,502 | ~1,400 | 硬过滤器与配对枚举 → Supplementary，保留注册与语义 |
| ch4 结果 | 2,486 | ~1,900 | 收紧叙述，数值全保留 |
| ch5 敏感性 | 2,808 | ~1,500 | 检查实验细节 → Supplementary，保留结论句与表格 |
| ch6 讨论 | 1,485 | ~600 | 与 ch7 合并为 Discussion and Conclusions，删与 ch4/5 的复述 |
| ch1 引言 | 1,141 | ~900 | 压缩定位段 |
| ch7 结论 | 655 | 并入 ch6 | 同上 |
| **合计** | **15,719** | **~8,700** | 再加一轮行文收紧至 ≤8,000（若按 12,000 口径则一步即达标） |

- 备选：若不愿压缩至此，改投无硬性字数上限的期刊（如 *RESS*、*Sustainable Energy, Grids and Networks*）。

## 提交前人工待办（作者侧）

1. 作者信息、CRediT、资助、利益冲突声明（投稿系统内单独填写；原 Data and Code Availability 与 Acknowledgments 节已按 #34 指示移除——注意 Elsevier 投稿流程仍会在系统内要求数据可用性声明，届时在线填写）。
2. 建议审稿人名单（cover letter 留位）。
3. Editorial Manager 提交时的即时校验（字数口径以门户为准）。
4. Graphical abstract 人工过目（本轮为脚本生成，三面板：缺额消除/SUET 窗＋r\*/R\* 边界）。
5. Zenodo 存档（当前声明为"将存档"）。

## 净室复现测试（本轮完成，证书见 `docs/verification/cleanroom_reproduction_20260921.md`）

- 全新目录 git clone（仅仓库内容，不含任何工作区状态）→ 按 README 装依赖 → 按 README 指令重跑 `critical_ramp_example.py` 与 `run_p6.py`。
- 锚点核对结果见证书文件。
