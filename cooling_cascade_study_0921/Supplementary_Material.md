# Supplementary Material

**For:** Early-Warning-Driven Proactive Resilience Optimization of Urban Water–Power Cyber-Physical Systems

This supplement contains the derivations, justifications, and experimental details that support the main text. All equation, table, and figure numbers without an "S" prefix refer to the main text; equations within this supplement are numbered (S1), (S2), … where needed. No result in the main text depends on material available only here — every conclusion is stated, with its numbers, in the main text; this supplement records the full reasoning behind those conclusions.

## S1 Model derivations and justifications (Chapter 2)

The layer decomposition of the coupling framework (main-text §2.1, complementing Fig. 1):

**Table S1 Layer decomposition of the water–power coupling model**

| Layer | Object | Theory and method | Dominant dynamics | Key state variables | Downstream interface |
|---|---|---|---|---|---|
| Municipal distribution | D-town network | Extended-period simulation (EPS) + pressure-driven demand (PDD) | Hours (district-tank depletion) | Nodal head $H_{\mathrm{muni}}$ | Intake head trajectory → cooling-water layer |
| Cooling water | Make-up tank / sump / circulating pumps / cooling tower | Orifice flow + mass-balance ODEs + NPSH | Minutes (storage depletion) | Levels $H_t, H_p$; flow rate | Circulating-water flow → condenser–turbine layer |
| Condenser–turbine | Condenser / LP turbine | Antoine + ε-NTU + back-pressure correction | Seconds–minutes | Back pressure $p_b$; output $P_g$ | Unit derating / tripping → power system layer |
| Power system | IEEE-118 | DC power flow (PTDF) + two-level reserves + LP | Seconds–minutes | Line flows; generation deficit | None (terminal layer of the physical chain) |


### S1.1 Municipal demand semantics and sole-source scenario (§2.2)

A nodal demand is fully satisfied when the local head reaches the required level $p_{\mathrm{req}}$. Below this level, the demand is partially met according to a square-root law. The demand vanishes when the head falls to $p_{\min}$. This work sets $p_{\min}=0$ and $p_{\mathrm{req}}=20\ \mathrm{m}$, a reference service pressure above the local elevation that covers low-rise urban demand; the D-town junction elevations span more than 60 m, so it is this reference head above each elevation, not the elevation itself, that governs the availability factor.

In the sole-source outage scenario, the total head of the reservoir boundary is set to zero. The city side then relies solely on the district storage tanks, and nodal heads decline district by district. The failure time of each plant intake node is the first time its head falls below the threshold. This time is latched and is not reset by later fluctuations. The head trajectory constitutes the complete input to the plant cooling-water model.

### S1.2 Water-side parameter basis (§2.3.1)

The water side consists of a high-level make-up tank, a collection sump, and the circulating pumps. The tank has a cross-sectional area of $A_T = 30\ \mathrm{m^2}$ and a target level of $H_T^{\mathrm{set}} = 4\ \mathrm{m}$. It feeds the sump by gravity through a valve, with an elevation difference of $\Delta z = 15\ \mathrm{m}$. The sump has an area of $A_P = 1700\ \mathrm{m^2}$ and a target level of $H_P^{\mathrm{set}} = 3\ \mathrm{m}$, and the circulating pumps draw from it.

For Eq. (2.4)–(2.5), $C_v^{\mathrm{m}} = 0.30\ \mathrm{m^3 s^{-1} m^{-1/2}}$ is the valve coefficient and $K_T = 0.5$ is the proportional level control gain. For Eq. (2.6)–(2.7), $C_v^{\mathrm{g}} = 0.60$, $K_P = 0.8$, and $H_t^{\min} = 0$. For Eq. (2.9), $H_s = 1.2\ \mathrm{m}$ is the minimum submergence depth and $\Delta H_s = 0.5\ \mathrm{m}$ is the derating band.

For Eq. (2.10), $p_{\mathrm{atm}} = 101.325\ \mathrm{kPa}$ is the atmospheric pressure, $h_{f,0} = 1.0\ \mathrm{m}$ is the rated suction friction loss, and $p_{\mathrm{vap}} = 3.0\ \mathrm{kPa}$ is taken as a constant at ambient temperature. The required value is $\mathrm{NPSH}_r = 8\ \mathrm{m}$. At the equilibrium level the available margin is ample.

For Eq. (2.11)–(2.12), $h_{fg} = 2400\ \mathrm{kJ/kg}$ is the latent heat of vaporization, $\beta = 0.52$ is the blowdown ratio, and $\alpha_d = 0.05\%$ is the drift fraction.

Water temperature (Eq. (2.14)): the tower outlet temperature is $T_{\mathrm{to}} = T_{wb} + \Delta T_{\mathrm{appr}} = 20\,^{\circ}\mathrm{C}$, with $T_{wb} = 15\,^{\circ}\mathrm{C}$ and $\Delta T_{\mathrm{appr}} = 5\ \mathrm{K}$, and the mixing coefficient is $\chi = 0.5$.

Initialization: the initial levels are obtained by forward integration from the target levels under fault-free conditions, until the level derivatives fall below $10^{-7}$. The proportional controls retain a steady-state droop, and the integration removes the initial non-equilibrium drift. The sump volume is checked against the effective residence time of 3–5 min specified in DL/T 5339 [46]. The loss and tower parameters follow GB/T 50102 [37]. The elevated tank volume, the valve coefficients, and the controller gains are design-representative values. The tank contributes less than 4% of the total stored water, and these parameters affect only the pre-failure equilibrium.

### S1.3 Condenser calibration details (§2.3.2)

Back-calibration of the nominal conductance (Eq. (2.18)): $\lambda_Q = 1.15$ is the approximate ratio of the condenser heat load to the electrical output, including the cycle heat rate, derived from the rated design point with design back pressure $p_{b,0} = 5\ \mathrm{kPa}$, design inlet temperature $T_{\mathrm{in},0} = 20\,^{\circ}\mathrm{C}$, and rated heat load $Q_{\mathrm{cond},0} = \lambda_Q P_{g,0}$.

High-back-pressure protection: the trip setting is $p_b^{\mathrm{trip}} = 15\ \mathrm{kPa}$, about three times the design value, with a delay $\tau_d = 3\ \mathrm{s}$.

Zero-flow branch: the numerical fallback is $3\,p_b^{\mathrm{trip}}$, capped at 50 kPa.

### S1.4 Warning-threshold design considerations (§2.4.1)

The coincident-instant design is justified by four considerations. First, the nodal head is an existing measurement of the municipal SCADA, so the warning reuses available telemetry and requires no new sensing on the plant side. Second, the threshold coincides with the make-up failure criterion of Eq. (2.2), which introduces no independent tuning degree of freedom. The warning semantics are unique and conservative, since a warning implies a genuine interruption of the make-up supply. Third, the costs of false alarms and missed detections are asymmetric. Raising the threshold would trade false alarms for lead time, and lowering it would miss failures altogether. The failure threshold itself is therefore a parameter-free conservative lower bound. Fourth, the common origin $t_{\mathrm{warn}} = t_{\mathrm{fail}} = 0$ places the SUET window, the trip times, the reserve start-up, and the control horizon on a single time axis. The scenario results of Chapter 4 are therefore strictly comparable.

An even earlier trigger exists and is deliberately not used. The root cause, the full stop of the sole source, is an unambiguous event known to the water utility at the fault instant $t_{\mathrm{fault}}$, whereas the head threshold of Eq. (2.23) fires only at $t_{\mathrm{fail}}$, which lags $t_{\mathrm{fault}}$ by 1.25–9.00 h for the six intake nodes. A source-stop trigger would therefore extend every warning window by hours at no additional sensing, since the pump-station status is already part of the standard telemetry. This work keeps the head trigger by design: it shares the anchor of the failure criterion, requires no event-classification logic, and yields the conservative lower bound of the achievable lead time. The source-stop trigger is the natural first extension and can only enlarge the control windows, so the conclusions of Chapters 4 and 5 are lower bounds in this respect as well.

Graded warning levels are deliberately omitted. The failure source of this study is a deterministic sole-source outage, and the head trajectory declines monotonically. Two threshold levels would only create two redundant triggers of the same decision sequence and would add a tuning problem of threshold spacing. The SCADA state field nevertheless retains the interface for graded extensions. Measurement and communication delays are set to zero, and missed detections and packet losses are excluded. The conservatism is carried entirely by the condition that no warning is issued before the failure, Eq. (2.23). The dynamics of the information and control systems themselves, and the sensitivity to warning delays, are outside the scope of this study and are discussed in Chapter 7.

The passive-versus-active contrast behind the main-text mechanism (§2.4.2, aligned with the paradigm of [25]):

**Table S2 Passive versus active control driven by early warning (aligned with Table 1 of [25])**

| Attribute | Passive control (no warning) | Active control (early warning driven) |
|---|---|---|
| Information used | Power system only; the failure becomes known only after the trip | Municipal and power telemetry across domains (warning at an intake head below 28 m) |
| Action time | After the unit trip; slow response bound by start-up rates | At the failure instant; zero latency, fast response |
| Control effect | Post-event mobilization of reserves, deep deficit | Runback soft landing within the SUET window and reserve pre-ramping |


### S1.5 Proactive-control formulation details (§2.6)

Load constancy: the load $P_L$ is held at its base-case value over the control horizon; no forecast uncertainty or intra-horizon volatility is modeled, and since a load decline would only shrink the deficit, the constant-load setting is the conservative choice.

Constraint semantics. The nodal balance requires the generation plus the deficit slack to equal the load at every step (Eq. (2.30)). The capacity constraint (Eq. (2.31)) bounds the unit outputs, with the reserve ratio $\rho_{\mathrm{res}} = 1.0$ allowing the remaining units their full physical headroom; the timing of the reserve deployment is carried by the ramping constraint. The power-flow constraint (Eq. (2.33)) is soft by default through the overload slack; under the hard mode with $o \equiv 0$, the deficit degenerates to the minimum load shedding, and the weight $w$ shapes only the overload slack once the deficit has reached zero. The passive causality constraint (Eq. (2.34)) holds the remaining units at or below their base-case outputs before the first trip under the passive mode.

Dynamic proactive control: the scheme of [25] prolongs the control time iteratively and recomputes the AET at each extended setting point. The implementation of this study extends the control time in a single step, $T_i = \alpha\,\mathrm{SUET}_i$, without iteration. The conservatism and the limitations of this approximation are characterized in Chapter 5 of the main text.

## S2 Coupling registration and calibration details (Chapter 3)

### S2.1 Hard filters and deterministic pairing (§3.2)

The convergence of the coupling set is made permanent by three hard filters, fixed in `coupling_map.py` and registered in `results/muni/coupling_map.json`. A node qualifies only if its base demand is positive and if its minimum head over a fault-free 24 h run stays above 32 m. It must also experience a pressure-failure event within the 72 h window under the full stop of R1. The six designated intake nodes (J102, J97, J198, J5, J217, and J177, all in district DMA1) pass all three filters, 6/6.

The pairing is a rank-to-rank mapping. The six intake nodes are ordered by failure time, ascending, with ties broken by node index: J102 at 1.25 h, J97 at 1.75 h, J198 and J5 at 3.75 h, J217 at 7.00 h, and J177 at 9.00 h. The six units are ordered by output, descending: buses 89, 80, 10, 66, 65, and 26. Matching rank to rank pairs bus 89 with J102, bus 80 with J97, bus 10 with J198, bus 66 with J5, bus 65 with J217, and bus 26 with J177.

### S2.2 Make-up demand and boundary semantics (§3.2)

The rated make-up demand of each unit scales with capacity, $\text{makeup} = \mathrm{clip}(0.03\,P_{\max},\,2,\,20)$ L/s, 95.7 L/s for the six units in total. Two distinct water sources must be separated here. In normal operation the plant's circulating losses are covered by its own raw-water and treatment supply; the municipal connection of Eq. (2.4) is a standby make-up rated at the tabulated 12.4–20.0 L/s. In the failure scenario the municipal node carries a dual role: it delivers the failure signal, and its make-up vanishes at $t_{\mathrm{fail}}$, which realizes the semantics that the plant loses its make-up resupply, whatever the source, at that instant. The volumetric demand implied by the pre-failure equilibrium (up to about 450 L/s for the largest unit at the circulating-loss ratio of Chapter 2) is therefore not a claim about the municipal network; it is the open-loop loss rate that the in-plant buffer must ride through once resupply is lost. Feeding the rated standby demand back into the city hydraulics would be feasible in volume (95.7 of 245.8 L/s) but is deliberately not done, because any non-zero feedback would drain the district tanks faster and distort the city-wide failure distribution generated by the municipal model of Chapter 2. The case therefore keeps a no-feedback, loose-coupling semantics. The city pressures retain the no-make-up caliber, and the rated demand is assessed post hoc through the pressure-driven share $f = \sqrt{\mathrm{clip}(p/20,\,0,\,1)}$. Over the 72 h window under the ramped-failure boundary, the six nodes require 24,806 m³ in total, of which 17,717 m³ (71.4%) is available. The node-wise availability ranges from 51.8% to 98.6% and correlates negatively with the failure order. The earlier a node fails, the earlier it loses its municipal standby make-up, which agrees with the stagger physics.

### S2.3 Coupling verification rules (§3.2)

Three rules define the coupling interface. The city side feeds back only the head, without checking volumes. A head below 28 m marks the failure instant, at which the make-up flow is zeroed and the make-up tank can no longer be refilled. The SUET is measured from that instant. The verification script `verify_coupling_rule.py` re-derives all three rules for the six coupled nodes, independently and item by item, and all six pass (6/6, `results/muni/coupling_rule_verification.json`). The B-ST failure times agree digit for digit with the registration of Table 2. A verification chain at a 0.5 s step yields SUET = 92.4–192.9 min, identical digit for digit to the power-side LP chain at a 1 s step; both chains implement the heat-load update law of §2.3.2, and both are converged with respect to the integration step.

### S2.4 Parameter calibration details (§3.3)

Water-side buffer parameters. The storage parameters follow two Chinese design standards. The collection sump (suction well) follows the 3–5 min residence of DL/T 5339 [46]: 1,700 m² × 3 m ≈ 5,100 m³, a residence of 4.1 min at the rated circulating flow. The rated flow coefficient 0.0295 m³/(s·MW) (≈106 m³/(h·MW)) corresponds to a design temperature rise of 8 K, inside the 8–10 K band of GB/T 50102 [37]. Bus 89 thus draws ≈21 m³/s at rated output. The total circulating loss is ≈2.2%, within the 2–3% band of the standard [37]. Evaporation takes ≈1.3% by the empirical rule 0.0016×ΔT at ΔT = 8 K. Blowdown takes 0.52 times the evaporation (cycles of concentration ≈3), and drift takes 0.05% (modern drift eliminators). The cooling-tower approach is 5 K (standard 3–5 K [37]), and the design wet-bulb temperature is 15 °C, self-consistent with the 5 kPa design back pressure.

Condenser and protection parameters. The condenser and its protections follow the HEI/ASME PTC 12.2 performance system [18, 19] and the low-vacuum protection practice of steam turbines. The design back pressure is 5 kPa and the design terminal temperature difference is 4 K. The conductance scales with the circulating flow as $UA \propto m_{cw}^{0.8}$ (Dittus–Boelter analogy [20]), and the back-pressure output correction is linear at 0.02 per kPa. The high-back-pressure trip is set at 15 kPa, about three times the design value, with a 3 s delay. The circulating pump requires a minimum submergence of 1.2 m, a linear derating band of 0.5 m, and a required NPSH of 8 m. The municipal failure criterion is a nodal head below 28 m against a normal supply head of 32 m.

The consolidated parameter summary (main-text §3.3):

**Table S3 Parameter summary (representative unit bus 89, $P_g$ = 607 MW and $P_{\max}$ = 707 MW; full provenance in `docs/parameter_fitting.md`, hard-coded in `src/01_cooling_chain/params.py`)**

| Group | Parameter (symbol) | Value | Source / standard |
|---|---|---|---|
| Unit and municipal boundary | Rated / actual output $P_{\max}$ / $P_g$ | 707 / 607 MW | IEEE-118 `gen.csv` |
| | Normal head / failure threshold $H_{\mathrm{muni},0}$ / $H_{\mathrm{muni},\min}$ | 32 / 28 m | Service pressure of the supply network (failure source) |
| Buffer facilities | Make-up tank area × level ($A_{\mathrm{tank}} \times H$) | 30 m² × 4 m = 120 m³ | Emergency make-up buffer of the circulating water |
| | Sump area × level ($A_{\mathrm{pool}} \times H$, residence 4.1 min) | 1,700 m² × 3 m ≈ 5,100 m³ | DL/T 5339 (3–5 min) [46] |
| Circulating water and cooling tower | Rated flow coefficient $m_{cw,0}/P_{\max}$ | 0.0295 m³/(s·MW) (≈21 m³/s, rise 8 K) | GB/T 50102 (8–10 K) [37] |
| | Total circulating loss (evaporation + blowdown + drift) | ≈2.2% (1.3% + 0.52 × evaporation + 0.05%) | GB/T 50102 (2–3%; empirical 0.0016×ΔT) [37] |
| | Tower approach / design wet-bulb temperature | 5 K / 15 °C | GB/T 50102 (3–5 K) [37] |
| Pump and cavitation | Minimum submergence / derating band / NPSH$_r$ | 1.2 / 0.5 m / 8 m | Pump data sheet and circulating-pump protection practice |
| Condenser and protection | Design back pressure $p_{b,0}$ / design TTD | 5 kPa / 4 K | Rated-point self-consistency ($UA$ back-calculated by ε-NTU) |
| | Flow exponent $n$ ($UA \propto m_{cw}^n$) | 0.8 | Dittus–Boelter analogy [20] |
| | Back-pressure output rate γ | 0.02 kPa⁻¹ | Approximation of the turbine incremental output rate |
| | Trip setting $p_{b,\mathrm{trip}}$ / delay τ | 15 kPa (≈3× design) / 3 s | Low-vacuum protection practice |
| Power-side LP and power flow | LP horizon / step / ramp rate | 300 min / 5 min / 0.01 $P_{\max}$ min⁻¹ (N-k scans 0.02) | Typical values (two-tier reserve semantics, Chapter 2) |
| | Reserve ceiling | $P_{g,0}$ + 1.0 × ($P_{\max}$ − $P_{g,0}$) (full headroom) | As above |


## S3 Additional results and check-experiment details (Chapters 4–5)

### S3.1 Numerical implementation details (§3.5)

Solve order and event latching. Every simulation chain is an explicit-stepping, event-latching integrator. Within each step the equations are solved in a fixed causal order. The order starts from the municipal head (2.1) and the valve and pump flows (2.4)–(2.9). It continues with the level ODEs (2.13), the water temperature (2.14), and the ε-NTU condenser (2.16)–(2.17). It closes with the back-pressure derating and protection (2.19) and the grid response (2.26)–(2.37). Pump trips, unit tripping, warnings, and the protection-delay timers (3 s) are latched events.

Problem size. The proactive-control LP carries $(N_g + 1 + L)\times(T+1)$ decision variables. On IEEE-118, with $N_g$ = 54, $L$ = 186, and $T$ = 60, this amounts to about 1.5 × 10⁴ variables, and HiGHS solves it within seconds.

The simulation-chain registry (main-text §2.6 and §3.5):

**Table S4 Simulation chains and integration steps**

| Simulation chain | Code | Step | Notes |
|---|---|---|---|
| Municipal boundary generation (EPS/PDD) | `boundary_generator.py` etc. | 15 min × 72 h | WNTR hydraulics [32] |
| Mechanism chain | `simulate.py` | 0.05 s default (4 s for long horizons, output thinned to 1 s) | Explicit Euler; the 3 s protection delay is a true delay |
| Warning-indicator forward integration | `warning_indicators.py` | 1 s (the critical-rate case integrates over 40,000 s) | SUET / UET / CWR |
| ICS event simulation | `ics_simulation.py` | 8 s macro step, 1 s PLC sampling | The 3 s delay is realized as one qualifying macro step |


### S3.2 Water-side propagation details (§4.1)

Fig. S2 below shows the spatio-temporal collapse summarized in §4.1 of the main text (the failure-fraction statistics appear both there and in the caption). Two details beyond the summary: the overall maximum of the failed fraction occurs at 67 h, and the head quantiles descend in step, the P10 quantile crossing 28 m at +1.25 h and the median at +12.5 h.

Single-unit timeline (B-ST, bus 89), full event list verified on the 1 s grid: (i) municipal depressurization at $t = 1.0$ min; (ii) make-up tank depletion at $t = 5.2$ min, the sump becoming the only buffer; (iii) at $t = 71.9$ min the sump enters the submergence-derating band (<1.7 m) and the circulation derates linearly from rated; (iv) at $t = 93.4$ min the back pressure crosses 15 kPa with $m_{cw}$ down to 36% and the sump at 1.38 m, the 1.2 m pump-trip level never being reached, so the flow derating trips the protection before any pump trip; (v) the high-back-pressure trip at $t = 93.4$ min (3 s set delay, acting on the first step past the limit under the 4 s grid), 92.4 min after the municipal depressurization; (vi) the output falling from 607 MW to zero.

The staggered intake pressure maps and the network-wide spatio-temporal collapse (main-text §4.1):

![Fig. S1](figures/Fig5_muni_staggered_depressurization.png)

**Fig. S1 Pressure heat maps of all six coupled intake nodes after the full stop of the sole source R1 at $t = 0$ (B-ST synthetic step, same fault model as Fig. S2)**: rows are the intake nodes, each labeled with its node name and paired bus and ordered by failure time; color is the node pressure on the same RdYlBu 0–80 m scale as Fig. S2, with depressurization in red; open circles mark the first crossing of the 28 m threshold, labeled $t_{\mathrm{fail}}$, and trace the staggered failure front of 1.25–9.00 h; all six intake nodes pass the three hard filters. The ramped-failure caliber B-RT, a linear head decay over 3 h from $t = 6$ h, feeds the full-order cascade later in this chapter and the closed water balance in Chapter 5 and is not shown in this figure.

![Fig. S2](figures/Fig6_network_outage_spatiotemporal.png)

**Fig. S2 Spatio-temporal pressure collapse of the 399-node network after the full stop of R1 at $t = 0$ (idealized worst case)**: (a) the node-pressure P10–P90 band with the mean and median (black dotted line, the 28 m threshold); (b) the fraction of nodes below the threshold, 9.5% already in the instantaneous initial solution at $t = 0$ (the immediate redistribution of the step), 50.1% past half at +12.5 h, non-monotone under the diurnal demand with daily peaks of 69%/67%/72% and nocturnal troughs of 8%–37%, ending at 56.4%; (c1)–(c4) 2×2 spatial snapshots at $t = 0/12/24/48$ h (color as in Fig. S1; gray lines, pipes; ■, source R1; ▲, tanks; ○ plus △, pumps).

### S3.3 Check-experiment details (§5.1–§5.3)

Pairing permutation. Reassigning the six failure times across the six units — the identity, the reverse, a rotation, and two random permutations, five pairings in all (`pairing_permutation.json`) — leaves the proactive conclusion untouched: SP is at zero deficit under every permutation. The passive side follows a simple rule: the peak is set by the first unit to trip, whose solo loss meets the still-cold reserves, and the deficit episode is time-translation invariant thereafter. Whenever bus 89 leads, the passive metrics equal the DISP values exactly (334.9 MW / 43.7 MWh); when a smaller unit leads, the peak drops to 86.0–115.0 MW.

Slack-bus artifact. A k = 3 population that includes the slack bus, for example the subset {69, 80, 89}, exhibits an apparent R-insensitive steady-state floor of 57.12 MW. That floor is an artifact of the power-flow redistribution forced by the slack reassignment, not a generic property of the network transfer limits, and it does not appear under the designated population.

Rated-cap make-up stress, detail. The stress question is whether a plant restricted to its rated cap from the fault instant would drain its buffer ahead of the municipal failure latch and break the warning semantics. The capped run (`makeup_cap_sensitivity.json`) answers no. All six units still trip only after their own municipal failure, at 2.45–11.76 h against $t_{\mathrm{fail}}$ = 1.25–9.00 h; the post-failure windows shrink by 14–22% relative to the B-ST SUETs, and the failure order is fully preserved. The mechanism is again the derating self-protection feedback: the capped deficit derates the output, the heat load falls along $k_p$, and the storage loss self-throttles. A static estimate from the initial storage over the uncapped net deficit, about 1.8 h at bus 89, would predict the window collapsing to about a third of its B-ST value; the coupled dynamics give 1.2 h instead, a 22% shrink.

### S3.4 Closed water balance details (§5.3)

The plant make-up valves are driven by the true city-side B-RT head trajectory. The driving head is $p - 28$ m, the filling-head threshold of the make-up valve and the physical origin of the 28 m failure criterion. Below the threshold the make-up flow vanishes; above it, the flow decays continuously. The flow is further multiplied by the pressure-driven share $f(p) = \sqrt{\mathrm{clip}(p/20, 0, 1)}$ [34], which closes the loose-coupling interface of Chapter 3 on the water-quantity dimension. The physical make-up demand is scaled from the rated loss ($q_{\mathrm{phys}} = 0.453$ m³/s at 707 MW, scaled linearly with $P_{\max}$).

### S3.5 Remaining parameter sweeps, declared future work (§5.2)

The sweeps of the two-tier reserve parameters of the ICS event chain — the spinning-reserve fraction $\rho_r$, the slow-reserve capacity $C_{\mathrm{slow}}$, and its arrival time $T_{\mathrm{slow}}$ — and of the DP time ratio $\alpha$ remain scheduled as supplementary experiments, in the same future-work class as the warning-latency and missed-detection sweeps (Chapter 7). The applicability boundary of proactive control is quantified along four axes: failure scale (Chapter 4), ramping rate and reserve capacity (§5.2 of the main text), intake position (§5.1), and the water-side calibers (§5.3).

## S4 Verification and reproducibility record (§3.5)

The 16 computing scripts and 9 plotting scripts are re-run end to end in dependency order at every revision, with every results file carrying its registration semantics. The municipal, cooling-chain, and ICS layers reproduce their archived results byte for byte under the unified heat-load semantics of §2.3.2; the proactive-control layer is re-registered under the same semantics, its scan anchors re-derived and re-verified (10/10 on the ramp-rate scan, 8/8 on the DP and reserve-capacity scans). Four check experiments are additionally registered: the SUET parameter sensitivity (`suet_sensitivity.json`), the rated-cap make-up stress (`makeup_cap_sensitivity.json`), the overload-weight and PA-trajectory checks (`w_pa_checks.json`), and the pairing permutation (`pairing_permutation.json`). The verification report is `docs/verification/report_v4_20260920.md`, and an independent clean-room reproduction test (fresh clone, README-only instructions, 13 anchors at zero drift) is certified in `docs/verification/cleanroom_reproduction_20260921.md`.
