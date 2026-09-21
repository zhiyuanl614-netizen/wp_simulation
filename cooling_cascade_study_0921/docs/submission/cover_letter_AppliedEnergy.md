# Cover Letter — Applied Energy 投稿信（草稿）

> 使用说明：方括号处按实际作者信息补齐；建议随信附 `docs/verification/report_v4_20260920.md` 与净室复现证书作为可复现性补充证据。

---

Dear Editors,

We are pleased to submit our manuscript, "**Early-Warning-Driven Proactive Resilience Optimization of Urban Water–Power Cyber-Physical Systems**," for consideration as a Research Paper in *Applied Energy*.

Interdependence studies of water and power systems typically replace the plant-side cooling process with a direct coupling edge, and climate-impact studies address slow, weather-driven derating. The fast, fault-driven chain — from a municipal supply failure through in-plant storage, hydraulics, and condenser back pressure to the unit trip — has not been modeled for early-warning purposes. Our manuscript closes this gap and converts the resulting minute-scale buffer into measurable grid resilience.

Key results:

- A cross-domain early warning (a municipal head threshold that requires zero new sensors) driving LP-based proactive optimization eliminates the passive deficit entirely: 485.6 MW / 49.1 MWh to zero for a single unit, and zero deficit for all 24 multi-unit failure subsets under a 2,631 MW common-origin loss.
- The plant cooling buffers span 92.4–192.9 min across the six coupled units. A critical ramp-down rate of 0.545 %P_g/min exploits a derating self-protection feedback to extend unit running time to 1.98 times the buffer — a directly actionable runback tuning rule.
- The applicability boundary lies on reserve adequacy and ramping capability, not on failure size: the passive deficit saturates at 12–13 MWh beyond k = 2, and proactive control under the common-origin loss requires a reserve ramp rate R ≥ 0.005 p.u. P_max/min and a reserve-capacity fraction r_f > 0.5. This gives planners a concrete check — regional spinning reserves audited against a simultaneous loss of the full coupled set.

We believe the work fits *Applied Energy*'s systems-oriented readership: it quantifies an energy-system resilience mechanism, issues an explicit engineering recommendation (open the SCADA–EMS alarm interface, tune runbacks at the critical rate, audit reserves against common-origin loss), and demonstrates it on a real 399-node urban water network coupled to IEEE-118.

All models, code, and registered results are open and reproducible; a four-generation verification record, including an independent clean-room reproduction test, accompanies the submission. To our knowledge this is the first early-warning resilience study of interdependent water–power systems to model the complete fault-driven cooling-water chain explicitly, complementing (not overlapping) the climate-derating literature. The work is original, has not been published elsewhere, and is not under consideration by any other journal. The authors declare no conflicts of interest.

Thank you for your consideration.

Sincerely,

[Corresponding author name]
[Affiliation, email]
[Co-authors]

---

**可选：建议审稿人**（编辑部通常欢迎 3–5 位非合作者建议；以下均为领域内非关联研究者，供选择）
- [建议 1：气–电预警范式方向研究者]
- [建议 2：能源–水 nexus / 热电脆弱性方向研究者]
- [建议 3：电力系统韧性 / 备用容量规划方向研究者]
