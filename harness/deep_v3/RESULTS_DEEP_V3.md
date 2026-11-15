# TSR Deep-v3 Evaluation Results (Pillars D1–D4)

**Branch:** `feat/automated-llm-harness`  
**Parent v2 Evaluation Commit:** `7ee697ce32e17dd5db329386cb3ce6b6df02b696` ([`RESULTS.md`](../RESULTS.md))  
**Deep-v3 Preregistration Commit (`DEEP_V3_PREREG_SHA`):** `d6f70e2802cb7b55d1871486e83378aaa55d349d` ([`PREREGISTRATION_V3.md`](./PREREGISTRATION_V3.md))  
**Deep-v3 Pre-Eval Raw Data Commit (`DEEP_V3_PRE_EVAL_SHA`):** `502c27c21ea404a138017727d25b96372e5bf0c7`  
**Evaluators & Artifacts:** [`evaluate_deep_v3.py`](./evaluate_deep_v3.py), [`exact_stats.py`](../exact_stats.py), [`summary_deep_v3.json`](./outputs/summary_deep_v3.json), [`d1a_web_bundles.csv`](./outputs/d1a_web_bundles.csv), [`d1b_lexical_rigidity.csv`](./outputs/d1b_lexical_rigidity.csv), [`d2_crossing_regime.csv`](./outputs/d2_crossing_regime.csv), [`d3_book_prose.csv`](./outputs/d3_book_prose.csv), [`d4_layer_a_v2_vs_v3.csv`](./outputs/d4_layer_a_v2_vs_v3.csv)

---

## 1. Executive Summary

Deep-v3 executed **485 unique pre-registered live tasks** (**657 total API calls** including **172 schema-retry calls**, **11 unrecovered schema errors**, **4,749.831 s** cumulative API latency) plus deterministic Layer-A v3 auditing (`D4`, `0` live calls) to test the open questions left by the v2 evaluation ([`RESULTS.md`](../RESULTS.md)). All tests remain strictly zero-glossary for unlabeled raters and leakage-free for generators, using exact stdlib statistics under one family-wise Holm-Bonferroni correction across the **6 confirmatory hypotheses (`H1`–`H6`, `alpha = 0.05`)**.

Across the four pillars, the empirical evidence divides cleanly between **strong, replicated separation of `A0` lexical structure and the Crossing Boundary protocol** (`5` of `6` confirmatory hypotheses rejected at Holm-adjusted `p <= 0.00406`) and **real diagnostic failures in isolated truth-table precision, template-lint compliance, and unassisted narrative rule generalization**:

1. **Multi-Job Web Discrimination (`D1a`, `H1` & `H2` — CONFIRMED):** When zero-glossary raters tested candidate words across three simultaneous first-order structural and Cloze roles without dictionary riddles (`W01..W14`), `W_A0` achieved mean **`4.4000`** (`SD = 0.9691`, **`56/70 = 80.00%`** `#1` best picks, **`0/70`** `#4` worst picks) vs. Ch. 16 synonyms `W_Ssyn` (**`3.0857`**, `#1 = 14.29%`; `H1`: `+1.3143`, `13/14` slot wins, exact perm `p = 0.000732`, Holm-adjusted **`p = 0.002930`**), conceptual challengers `W_Chal` (**`2.1714`**, `#1 = 4.29%`; `H2`: `+2.2286`, `14/14` slot wins, exact perm `p = 0.000122`, Holm-adjusted **`p = 0.000732`**), and `W_A3` (**`2.1857`**, `14/14` slot wins). Physics calibration controls (`NC01..NC03`) scored **`15/15` (`100%`)** `#1` accuracy (`5.00` mean).
2. **4-Criteria Rigidity & CSP (`D1b`, `H3` — CONFIRMED ON `H3`, NUANCED CSP RESULT):** On independent boolean truth tables (`c1..c4`), `W_A0` passed all 4 criteria jointly (`all4`) on **`47/70` (`67.14%`)** ratings vs. `W_Ssyn` **`3/70` (`4.29%`)**, `W_Chal` **`0/70` (`0.00%`)**, and `W_A3` **`1/70` (`1.43%`)** (`H3`: mean fraction diff `+0.652381`, `13/14` slots, exact perm `p = 0.000244`, Holm-adjusted **`p = 0.001221`**). However, while **zero** non-`W_A0` words reached even `>= 3/5` consensus on any slot (`0/14`), `W_A0` itself fell short of `>= 3/5` consensus on `4` slots (`W01` `0/5`, `W02` `1/5`, `W07` `2/5`, `W10` `2/5`) due specifically to literal readings of isolated `c1`, leaving `0` complete `14`-slot CSP assignments at both `>= 4/5` and `>= 3/5` thresholds.
3. **Crossing Boundary Protocol (`D2a` & `D2b`, `H4` — CONFIRMED ON `D2b`, MIXED ON `D2a`):**
   - On `D2b` (`crossing_battery_20.json`), strict `>= 4/5` `crossing_interface` consensus separated `Mechanical_Crossing` (**`5/7` = `71.43%`**) from `Non_Crossing_Boundary` (**`0/13` = `0.00%`**, all `13/13` unanimous `5/5` `no_partner`, including `X007` and `X008`), yielding exact Fisher `p = 0.001354`, Holm-adjusted **`p = 0.004063`** (`H4`). Crucially, the two missed `Mechanical_Crossing` items (`X004` `2/5` valid, `X005` `3/5` valid) failed **exclusively due to `{Slot}` template-lint errors**: under both valid-voter (`>= 80%` of `status=="ok"`) and raw parsed-JSON sensitivity checks, separation is **`7/7` (`100%`) vs. `0/13` (`0.00%`)**, exact Fisher **`p = 1.290e-5`**.
   - On `D2a` (`calibration_17`), `K17` (Boyle's law) flipped cleanly from `0/5` (`5/5` `no partner` in v2 `M1 A0`) to **`4/5` `crossing_interface` / `"keep"`**, **but overall `K01..K17` consensus accuracy dropped from `12/17` (`70.59%`) to `8/17` (`47.06%`)** (`McNemar p = 0.21875`) as Rule R v3's expanded Step 1a/1b guard induced over-exclusion, `gamma`-stripping misclassifications on `K02`, and `4` template-lint errors.
4. **Chapter 2 Narrative Teaching vs. Book Excerpts (`D3a` & `D3b` — `H5` LOSS / NOT REJECTED; `H6` CONFIRMED):**
   - **`D3a` (`H5`, LOSS / NOT REJECTED):** Supplying strictly Book Ch. 2 *"The One Rule"* verbatim (`idx=19..22`) plus standard scope rules **degraded** `K01..K17` `>= 4/5` consensus accuracy from **`12/17` (`70.59%`)** in Commit-2 `M1 A0` down to **`8/17` (`47.06%`)** (`McNemar p = 0.125`, `0` gains / `4` losses on `K04, K07, K08, K11`) and significantly reduced pooled `85`-call accuracy from **`62/85` (`72.94%`) to `48/85` (`56.47%`)** (paired McNemar `p = 0.009355`). Without Ch. 16's explicit boundary clarifications (`[definition: JUDGMENT]`, `#5 no mass in it`), models applied Ch. 2's resistance prose literally and ruled **5/5 `invert`** on `K16` (`F = m a`) and `K06`, and **4/5 `invert`** on `K05`.
   - **`D3b` (`H6`, CONFIRMED):** On `12` masked verbatim-derived Book excerpts (`P01..P12`), `V_A0` scored **`4.3167`** (`SD = 0.8129`, **`45/60 = 75.00%`** `#1` picks, `0/60` worst) vs. `V_Ssyn` (**`3.0000`**, `#1 = 20.00%`; `H6`: `+1.3167`, `11/12` wins, `P06` sole loss, exact perm `p = 0.001465`, Holm-adjusted **`p = 0.004063`**) and `V_A3` (**`2.0833`**, `12/12` wins, exact perm `p = 0.000488`).
5. **Deterministic Layer-A v3 Audit (`D4`, `0` Live Calls):** On frozen [`stage2_m2_heldout.json`](../outputs/stage2_m2_heldout.json), upgrading [`layer_a_v3.py`](./layer_a_v3.py) cleared all `4` algebraic/calculus/prime-subscript false positives on **`A0`** (**`12/16 -> 16/16`**, `0` joint collisions, **`passes_all = true`**) while preserving all genuine failures on **`A3-1`** (**`13/16 -> 15/16`**, `3` joint collisions including `E001` `"angular"` + `A3` mismatch and cross-item `A1` splitting of `alpha`, **`passes_all = false`**).

---

## 2. Provenance, Call Ledger, Latency, & Schema Errors

All results are computed deterministically from immutable Commit-4 specs (`d6f70e2802cb7b55d1871486e83378aaa55d349d`) and Commit-5 logs/outputs (`502c27c21ea404a138017727d25b96372e5bf0c7`) in [`live_calls_v3.jsonl`](./logs/live_calls_v3.jsonl).

| Stage / Role | Unique Keys | Total Live Calls | Retry Calls | Valid Calls | Unrecovered `schema_error` |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `D1a` (`d1a_web_rating`) | 85 | 106 | 21 | 85 | 0 |
| `D1b` (`d1b_web_truthtable`) | 70 | 70 | 0 | 70 | 0 |
| `D2a` (`d2a_crossing_cal17`) | 85 | 145 | 60 | 81 | 4 |
| `D2b` (`d2b_crossing_battery20`) | 100 | 146 | 46 | 94 | 6 |
| `D3a` (`d3a_narrative_cal17`) | 85 | 130 | 45 | 84 | 1 |
| `D3b` (`d3b_passage_rating`) | 60 | 60 | 0 | 60 | 0 |
| `D4` (`layer_a_v3` deterministic) | — | 0 | 0 | — | 0 |
| **Total** | **485** | **657** | **172** | **474** | **11** |

API latency across all `657` live calls totaled **`4749.831 s`** (`4,749,831 ms`):

| Model | Calls | Total (s) | Mean (ms) | Median (ms) | p95 (ms) | Max (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-sonnet-4.6` | 109 | 1314.001 | 12055.06 | 10734.0 | 24976.0 | 30667 |
| `gemini-2.5-flash` | 166 | 2278.327 | 13724.86 | 11048.0 | 32437.0 | 73416 |
| `gpt-5.4-fast` | 107 | 351.519 | 3285.22 | 3167.0 | 4327.0 | 8472 |
| `llama-4-maverick` | 143 | 436.775 | 3054.37 | 2174.0 | 6793.0 | 8095 |
| `mistral-medium-3.5` | 132 | 369.209 | 2797.04 | 2569.5 | 4008.0 | 10234 |

All `11` unrecovered `schema_error` records occurred exclusively on `{Slot}` template-lint validation in `D2a` (`4`), `D2b` (`6`), and `D3a` (`1`), while `D1a`, `D1b`, and `D3b` had `0` schema errors across `215` tasks.

---

## 3. Confirmatory Hypotheses (`H1`–`H6`) & Holm-Bonferroni Correction (`K = 6`)

All `6` pre-registered confirmatory hypotheses from [`PREREGISTRATION_V3.md`](./PREREGISTRATION_V3.md) §4 share a single family-wise Holm-Bonferroni correction (`alpha = 0.05`, `K = 6`):

| Rank | ID | Pillar | Comparison & Unit (`N`) | Exact Test | Observed Result | Raw `p` | Holm Adj. `p` | `<= 0.05` |
| ---: | :---: | :---: | :--- | :--- | :--- | ---: | ---: | :---: |
| 1 | **`H2`** | `D1a` | `W_A0` vs. `W_Chal` slot mean (`N = 14`) | Exact perm (`2^14`) | `4.4000` vs. `2.1714` (`+2.2286`, `14/14` wins) | `1.221e-4` | **`7.324e-4`** | **Yes** |
| 2 | **`H3`** | `D1b` | `W_A0` vs. mean(`W_Ssyn, W_Chal, W_A3`) `all4` (`N = 14`) | Exact perm (`2^14`) | `0.6714` vs. `0.0190` (`+0.6524`, `13/14` wins) | `2.441e-4` | **`1.221e-3`** | **Yes** |
| 3 | **`H1`** | `D1a` | `W_A0` vs. `W_Ssyn` slot mean (`N = 14`) | Exact perm (`2^14`) | `4.4000` vs. `3.0857` (`+1.3143`, `13/14` wins) | `7.324e-4` | **`2.930e-3`** | **Yes** |
| 4 | **`H4`** | `D2b` | Strict `>= 4/5` `crossing_interface`: `7` vs. `13` | Exact Fisher `2x2` | `5/7` (`71.43%`) vs. `0/13` (`0.00%`) | `1.354e-3` | **`4.063e-3`** | **Yes** |
| 5 | **`H6`** | `D3b` | `V_A0` vs. `V_Ssyn` passage mean (`N = 12`) | Exact perm (`2^12`) | `4.3167` vs. `3.0000` (`+1.3167`, `11/12` wins) | `1.465e-3` | **`4.063e-3`** | **Yes** |
| 6 | **`H5`** | `D3a` | `D3a` vs. Commit-2 `M1 A0` on `K01..K17` (`N = 17`) | Exact McNemar | `8/17` (`47.06%`) vs. `12/17` (`70.59%`, **loss**) | `0.125000` | `0.125000` | No |

*(Note: Under Holm-Bonferroni monotonicity, `H6`'s step-down adjusted `p = max(0.004063, 2 * 0.001465 = 0.002930) = 0.004063`.)*

---

## 4. Pillar D1: Multi-Job Web Discrimination & 4-Criteria CSP (`D1a` & `D1b`)

### 4.1 `D1a` Unlabeled 4-Way Slot Ratings (`W01..W14` & `NC01..NC03`)

Full rating records are in [`d1a_web_bundles.csv`](./outputs/d1a_web_bundles.csv). Across `14` Core slots x `5` zero-glossary raters (`70` ratings per candidate arm):

| Candidate Arm | Mean (SD) | Median | `#1` Best (`70`) | Exact Binom vs. `0.25` (`>`) | `#4` Worst (`70`) | Slot-Level `W_A0 - Arm` (`N = 14`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`W_A0`** | **`4.4000` (`0.9691`)** | **`5.0`** | **`56/70` (`80.00%`)** | **`p = 7.218e-22`** | **`0/70` (`0.00%`)** | — |
| **`W_Ssyn`** | `3.0857` (`1.2008`) | `3.0` | `10/70` (`14.29%`) | `p = 0.9901` | `6/70` (`8.57%`) | `+1.3143` (`13/1/0`; perm **`p = 0.000732`**, sign `p = 0.001831`) |
| **`W_Chal`** | `2.1714` (`1.2274`) | `2.0` | `3/70` (`4.29%`) | `p = 1.0000` | `30/70` (`42.86%`) | `+2.2286` (`14/0/0`; perm **`p = 0.000122`**, sign `p = 0.000122`) |
| **`W_A3`** | `2.1857` (`1.1331`) | `2.0` | `1/70` (`1.43%`) | `p = 1.0000` | `34/70` (`48.57%`) | `+2.2143` (`14/0/0`; perm **`p = 0.000122`**, sign `p = 0.000122`) |

**Per-Slot Summary & Sole `W_A0` Loss vs. `W_Ssyn`:**
- `W_A0` swept `#1` unanimously (`5/5`) on `5` slots — hitting unanimous `5.00` mean on `4` slots (`W09 Tune`, `W12 Vortex`, `W13 Convergence`, `W14 Intuition`) and `5/5` `#1` with mean `4.80` (`[5, 5, 4, 5, 5]`) on `W02 Current` — won `4/5` `#1` picks on `6` more slots (`W03 Vibration`, `W05 Desire`, `W06 Vibrance`, `W07 Appreciation`, `W08 Frequency`, `W11 Reflected`), and won `3/5` `#1` picks on `W01 Movement` (`3.40` vs. `responsiveness` `3.00`) and `W10 Idle` (`4.20` vs. `stillness` `3.40`).
- **Sole `W_A0` loss (`W04`):** On `W04`, `W_Ssyn` (`growth`, mean `4.80`, `4/5` `#1`) outscored `W_A0` (`Expansion`, mean `4.00`, `1/5` `#1`), because raters viewed `"growth"` as slightly more organic for irreversible novelty addition than `"Expansion"` in isolation (even though `"growth"` collides with `W07` in the CSP!).
- **Physics Calibration Controls (`NC01..NC03`):** All `5` raters selected the exact canonical physics term (`inertia`, `torque`, `equilibrium`) as `#1` (`5.00` mean) on **`15/15` (`100%`)** control trials (`exact binomial p = 9.313e-10`).
- **Inter-Rater Agreement:** `Fleiss' kappa` on `#1` pick = `0.1536`, `#4` pick = `0.2023`; `Krippendorff's alpha` (ordinal across all `56` `(slot, candidate)` units) = **`0.4251`**. All `5` raters independently ranked `W_A0` highest in mean score (`claude` `4.21` vs. `3.07`, `gpt` `4.36` vs. `3.07`, `gemini` `4.50` vs. `2.07`, `mistral` `4.79` vs. `3.57`, `llama` `4.14` vs. `3.64`).

### 4.2 `D1b` 4-Criteria Boolean Truth Tables & Collision-Free CSP (`W01..W14`)

Full boolean cells (`14` slots x `4` arms x `5` raters = `280` rows) are in [`d1b_lexical_rigidity.csv`](./outputs/d1b_lexical_rigidity.csv).

| Candidate Arm | `all4` Pass (`70`) | `c1` Core Mirror | `c2` Trap-Free | `c3` Coupled System | `c4` Everyday Register | Slots `>= 4/5` `all4` | Slots `>= 3/5` `all4` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`W_A0`** | **`47/70` (`67.14%`)** | `48/70` (`68.57%`) | `64/70` (`91.43%`) | `64/70` (`91.43%`) | `68/70` (`97.14%`) | **`8/14`** | **`10/14`** |
| **`W_Ssyn`** | `3/70` (`4.29%`) | `25/70` (`35.71%`) | `27/70` (`38.57%`) | `20/70` (`28.57%`) | `21/70` (`30.00%`) | `0/14` | `0/14` |
| **`W_Chal`** | `0/70` (`0.00%`) | `7/70` (`10.00%`) | `9/70` (`12.86%`) | `13/70` (`18.57%`) | `1/70` (`1.43%`) | `0/14` | `0/14` |
| **`W_A3`** | `1/70` (`1.43%`) | `2/70` (`2.86%`) | `33/70` (`47.14%`) | `8/70` (`11.43%`) | `5/70` (`7.14%`) | `0/14` | `0/14` |

- **Primary & Secondary Tests:** `H3` (`W_A0` vs. mean of `(W_Ssyn, W_Chal, W_A3)` `all4` fraction per slot) = `+0.6524` (`13` wins / `1` loss on `W01` where `W_A0` was `0/5` vs. `W_Ssyn` `1/5`, exact sign-flip `p = 0.000244`, Holm-adjusted **`p = 0.001221`**). Slot-level `>= 4/5` `all4` McNemar (`W_A0` vs. `W_Ssyn`): **`8/14` vs. `0/14`** (`n10 = 8, n01 = 0`, exact McNemar `p = 0.007813`). Five-rater `Fleiss' kappa` across all `224` (`14 x 4 x 4`) boolean cells = **`0.6268`**.
- **CSP Enumeration (`solve_collision_free_web_assignments`) — Crucial Nuance:**
  - At **`>= 4/5` supermajority consensus**: `total_count = 0` (`has_valid_assignment = false`). Eight slots (`W03 Vibration`, `W04 Expansion`, `W06 Vibrance`, `W08 Frequency`, `W11 Reflected`, `W12 Vortex`, `W13 Convergence`, `W14 Intuition`) admit **exclusively `W_A0`**, while `6` slots have empty eligible sets (`W01` `0/5`, `W02` `1/5`, `W05` `3/5`, `W07` `2/5`, `W09` `3/5`, `W10` `2/5`).
  - At **`>= 3/5` majority consensus**: `total_count = 0` (`has_valid_assignment = false`). Ten slots (`W03, W04, W05, W06, W08, W09, W11, W12, W13, W14`) admit **exclusively `W_A0`**, while `4` slots remain empty (`W01` `0/5`, `W02` `1/5`, `W07` `2/5`, `W10` `2/5`).
  - **Why those 4 slots failed isolated boolean `c1`:** `W_A0` excelled on `c2` (`91.4%`), `c3` (`91.4%`), and `c4` (`97.1%`), yet when `c1` was presented as a standalone binary question without surrounding Role 2/3 context, raters penalized `"Movement"` (`c1 = 0/5` vs. `c2=4/5, c3=4/5, c4=5/5` because `"Movement"` names motion rather than receptivity), `"Current"` (`c1 = 1/5` vs. `5/5` on `c2..c4`), `"Appreciation"` (`c1 = 2/5, c3 = 2/5` without the house-value compounding example), and `"Idle"` (`c1 = 2/5, c2 = 3/5` without the idling-engine contrast). Notably, **not a single `W_Ssyn`, `W_Chal`, or `W_A3` term qualified on any of the 14 slots at either `>= 3/5` or `>= 4/5`**.

---

## 5. Pillar D2: Crossing Boundary Protocol (`D2a` & `D2b`)

Full item-level outputs are in [`d2_crossing_regime.csv`](./outputs/d2_crossing_regime.csv).

### 5.1 `D2b` Crossing Battery (`crossing_battery_20.json`: `7` Mechanical Crossing vs. `13` Non-Crossing Boundary)

| Metric | `Mechanical_Crossing` (`N = 7`) | `Non_Crossing_Boundary` (`N = 13`) | Exact Fisher `2x2` `p` |
| :--- | :---: | :---: | ---: |
| **Strict `>= 4/5` `crossing_interface` (`H4`, Confirmatory)** | **`5/7` (`71.43%`)** (`E029, X001, X002, X003, X006`) | **`0/13` (`0.00%`)** (`13/13` are `5/5` `no_partner`) | **`0.001354`** (Holm **`0.004063`**) |
| **Valid-Voter Sensitivity (`>= 80%` of `status == "ok"` calls)** | **`7/7` (`100.00%`)** (`X004: 2/2`, `X005: 3/3`) | **`0/13` (`0.00%`)** | **`1.290e-5`** |
| **Raw Parsed-JSON Sensitivity (`>= 4/5` on `extract_first_json_object`)** | **`7/7` (`100.00%`)** (`X001: 5/5`, `X004: 5/5`, `X005: 5/5`) | **`0/13` (`0.00%`)** | **`1.290e-5`** |

**Transparent Audit of All `6` `D2b` Schema Errors (100% `{Slot}` Template Lint, `0%` Scope Misclassifications):**
All `6` unrecovered `D2b` schema errors (`6/100 = 6.0%`) occurred on `Mechanical_Crossing` equations, and in **all `6/6` cases** the final raw JSON response parsed cleanly with `scope_status = "crossing_interface"` and `ruling = "keep"`:
1. `X001` (`p = F/A`, `llama-4-maverick`): used invalid braced slot token `{Vibration²}` (`'Vibration squared'`) and left unresolved braces in prose fields.
2. `X004` (`F_1/A_1 = F_2/A_2`, `gpt-5.4-fast`): invented unmapped slot token `{area}` instead of `{Vibration} squared`.
3. `X004` (`gemini-2.5-flash`): mapped `F_1, F_2, A_1, A_2` in `variable_map` but summarized template solely with `{felt_gap}`, missing `['Frequency', 'Vibration']` placeholders.
4. `X004` (`llama-4-maverick`): identical template omission (`{felt_gap} equals {felt_gap}`), missing `['Frequency', 'Vibration']`.
5. `X005` (Bernoulli, `mistral-medium-3.5`): left literal `=` in `translation_template` vs. `"equals"` in `translation_t` (unwrapped mismatch).
6. `X005` (`llama-4-maverick`): wrapped literal `"constant"` in `{constancy}` (`Invalid slot tokens: ['constancy']`).

**Strict Boundary Guard Inspection (`X007` & `X008`):**
All `13/13` `Non_Crossing_Boundary` equations—the `11` held-out Boundary items (`E003, E004, E009, E012, E015, E019, E025, E031, E032, E033, E034`) **plus `X007` (combined ideal gas law `p_1 V_1 / T_1 = p_2 V_2 / T_2`) and `X008` (Poiseuille's law `Q = (p_2 - p_1) pi r^4 / (8 eta l)`)**—were rejected **`5/5` unanimously (`100%`) as `no_partner`**, with models explicitly citing active dynamical `T_1, T_2` (`X007`) and `Q, eta` (`X008`). Even mechanical PV work `X006` (`W = int p dV`) passed strict `4/5` `crossing_interface` (`mistral` conservative `no_partner`).

### 5.2 `D2a` Calibration 17 (`K01..K17`) vs. Commit-2 `M1 A0`

- **Positive Crossing Breakthrough on `K17` (Boyle's Law):** On `K17` (`P_1 V_1 = P_2 V_2 (constant T, n)`), `D2a` shifted from **`0/5` (`5/5` `"no partner"` in Commit-2 `M1 A0`)** to **`4/5` `crossing_interface` / `"keep"`** (`claude-sonnet-4.6`, `gpt-5.4-fast`, `gemini-2.5-flash`, `llama-4-maverick`; only `mistral-medium-3.5` kept `no_partner`).
- **Regression on `K01..K16` (`12/16 -> 7/16`, Overall `12/17 -> 8/17`):** Despite `K17`'s win, `D2a` consensus accuracy dropped on `K01..K17` from **`12/17` (`70.59%`)** to **`8/17` (`47.06%`)** (`n11=7, n10=1 [K17], n01=5 [K02, K04, K08, K09, K11], n00=4`, McNemar `p = 0.21875`; pooled `56/85 = 65.88%` vs. `62/85 = 72.94%`). Three factors caused the `5` item-level losses:
  1. **Rule R v3 Step 1a/1b over-exclusion & `gamma`-stripping side effects:** `mistral-medium-3.5` dropped from `15/17` in `M1 A0` to **`8/17`** (calling `K08` `no_partner` on `c`, `K05` `open_joint`, `K04/K12` `no_partner`, plus `2` `=`-vs-`equals` lint errors on `K07` and `K10`), while `gemini`, `mistral`, and `llama` switched `K02` (`Delta t = gamma v Delta x / c^2`) to `"keep"` after stripping `gamma`.
  2. **`4` template-lint errors** (`K07 mistral`, `K08 llama`, `K10 mistral`, `K14 gemini`), costing `>= 4/5` quorum on `K08` (`3/5` `invert`).
  3. **Qualitative frame/relativity splits** on `K04` (`2/5` `keep`, `2/5` `no_partner`, `1/5` `invert`) and `K11` (`3/5` `keep`, `1/5` `invert`, `1/5` `no_partner`). Notably, `gpt-5.4-fast` (`14/17` vs. `11/17`) improved under Rule R v3, showing the loss was driven primarily by `mistral` (`15 -> 8`) and `llama`/`gemini` template-lint and `gamma` over-stripping.

---

## 6. Pillar D3: Narrative Teaching (`D3a`) & Book Excerpt Discrimination (`D3b`)

Full item- and excerpt-level data are in [`d3_book_prose.csv`](./outputs/d3_book_prose.csv).

### 6.1 `D3a` Narrative Chapter 2 *"The One Rule"* (`K01..K17`) — Confirmatory Loss (`H5`)

| Comparison | `D3a` (Ch. 2 Verbatim + Scope Rules) | Commit-2 `M1 A0` (Unassisted Rule R) | Exact Test (`D3a` vs. `M1 A0`) |
| :--- | :---: | :---: | :--- |
| **`>= 4/5` Consensus `K01..K17` (`H5`, Primary)** | **`8/17` (`47.06%`)** | **`12/17` (`70.59%`)** | McNemar `p = 0.125` (`n11=8, n10=0, n01=4, n00=5`, NS **loss**) |
| **`applied_later` Subset (`13` items)** | `6/13` (`46.15%`) | `9/13` (`69.23%`) | McNemar `p = 0.25` (`n10=0, n01=3`) |
| **`construction` Subset (`4` items: `K07, K14..K16`)** | `2/4` (`50.00%`) | `3/4` (`75.00%`) | McNemar `p = 1.0` (`n10=0, n01=1`) |
| **Pooled Call-Level Accuracy (`85` calls)** | **`48/85` (`56.47%`; `48/84 = 57.14%` valid)** | **`62/85` (`72.94%`; `62/83 = 74.70%` valid)** | Paired McNemar **`p = 0.009355`** (`n10=6, n01=20`); Fisher `p = 0.036516` |
| **`K17` Boyle's Law (Orthogonal vs. `D2a`)** | `0/1` (`5/5` `no partner`) | `0/1` (`5/5` `no partner`) | Identical blocklist exclusion (`D2a` achieved `4/5` `keep`) |

**Why Book Ch. 2 Prose Alone Lowered Calibration Accuracy:**
- **Literal inversion of resistance-bearing definitions (`K16`, `K05`, `K06`):** Chapter 2 teaches *"If it depends on resistance, so that more mass means more of something, flipping resistant to receptive turns it around"* and *"Force reads how hard you're pushed against resistance, Frequency reads how freely you're yielding to receptivity"*, **without** Chapter 16's explicit boundary clarifications (`F = m a` is a `[definition: JUDGMENT]` `"keep"`, and `#5 time dilation` has `"no mass in it"` -> `"keep"`). Reading Ch. 2 alone led **`5/5` models (100%, up from `2/5` in `M1 A0`)** to rule **`invert`** on `K16` (`F_net = m a`), **`5/5`** to rule **`invert`** on `K06` (length contraction), and **`4/5`** to rule **`invert`** on `K05` (time dilation).
- **`4` Consensus Regressions (`K04, K07, K08, K11`) & Per-Model Drop:** `D3a` lost consensus on `K04` (`3/5` `keep`, `2/5` `no partner`), `K07` (`3/5` `keep`, `mistral` `invert`, `llama` `no partner`), `K08` (`2/5` `keep`, `2/5` `no partner`, `1/5` `invert`), and `K11` (`2/5` `keep`, `2/5` `invert`, `1` schema error on `mistral`). Across models: `claude` `13 -> 11`, `gpt` `11 -> 11`, `gemini` `14 -> 10`, `mistral` `15 -> 8`, `llama` `9 -> 8`.

### 6.2 `D3b` Masked Verbatim-Derived Book Excerpt Ratings (`P01..P12`) — Confirmed (`H6`)

| Variant | Mean (SD) | Median | `#1` Best (`60`) | Exact Binom vs. `1/3` (`>`) | `#3` Worst (`60`) | `V_A0 - Variant` (`N = 12`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`V_A0`** | **`4.3167` (`0.8129`)** | **`5.0`** | **`45/60` (`75.00%`)** | **`p = 4.897e-11`** | **`0/60` (`0.00%`)** | — |
| **`V_Ssyn`** | `3.0000` (`1.2073`) | `3.0` | `12/60` (`20.00%`) | `p = 0.9923` | `17/60` (`28.33%`) | `+1.3167` (`11/1/0`; perm **`p = 0.001465`**, sign `p = 0.006348`) |
| **`V_A3`** | `2.0833` (`1.0462`) | `2.0` | `3/60` (`5.00%`) | `p = 1.0000` | `43/60` (`71.67%`) | `+2.2333` (`12/0/0`; perm **`p = 0.000488`**, sign `p = 0.000488`) |

- **Stratified Breakdown (`N = 6` excerpts per stratum; minimum two-sided `2^6` p-value = `2/64 = 0.03125`):**
  - **`polysemy_bridge_paragraphs` (`P07..P12`):** `V_A0` = **`4.5000`** vs. `V_Ssyn` = `2.8000` (`+1.7000`, `6/6` wins, exact perm **`p = 0.03125`**) and `V_A3` = `2.1667` (`+2.3333`, `6/6` wins, exact perm **`p = 0.03125`**).
  - **`structural_paragraphs` (`P01..P06`):** `V_A0` = **`4.1333`** vs. `V_Ssyn` = `3.2000` (`+0.9333`, `5/6` wins, exact perm `p = 0.09375` NS at `N = 6`; sign `p = 0.21875`), and `V_A0` vs. `V_A3` (`2.0000`) = `+2.1333` (`6/6` wins, exact perm **`p = 0.03125`**).
- **Sole `V_A0` Loss (`P06`, Ch. 16 Gravity & Lenses):** On `P06`, `V_Ssyn` (`whirlpool basins within the stream`, `affinity`, `gathering`) outscored `V_A0` (`Vortex basins within the Current`, `Attraction`, `Convergence`) **`4.40` vs. `3.60`** (`4/5` `#1` picks vs. `1/5`), as raters found `"responsiveness ... whirlpool basins within the stream"` smoother in an isolated gravitational-basin analogy than `"Movement ... Vortex basins within the Current"`.
- **Inter-Rater Agreement:** `Fleiss' kappa` on `#1` pick = `0.0928`, `#3` pick = `0.0150`; `Krippendorff's alpha` (ordinal across `36` passage-variants) = **`0.5127`**.

---

## 7. Pillar D4: Deterministic Layer-A v2 vs. Layer-A v3 Audit (`0` Live Calls)

Side-by-side results on the `16` shared consensus `keep`/`invert` items in frozen Commit-2 [`stage2_m2_heldout.json`](../outputs/stage2_m2_heldout.json) are in [`d4_layer_a_v2_vs_v3.csv`](./outputs/d4_layer_a_v2_vs_v3.csv):

| Arm | Layer-A v2 (Commit 2) | Layer-A v3 (`layer_a_v3.py`, Deep-v3) | Item-Level Delta |
| :--- | :--- | :--- | :--- |
| **`A0`** | `12/16` (`75.00%`), `4` collisions, **`passes_all = false`** | **`16/16` (`100.00%`), `0` collisions, `passes_all = true`** | Cleared `E001`, `E002` (exact rational `Vibration^1 * Vibration^-1` cancellation), `E023` (`integral over path of`, `d(Vibration)`), `E027` (`_S'S` subscript before prime). |
| **`A3-1`** | `13/16` (`81.25%`), `5` collisions, **`passes_all = false`** | **`15/16` (`93.75%`), `3` collisions, `passes_all = false`** | Cleared `E023`, `E027`, but **`E001` still fails** (`A1_invalid_target_token`: `"angular"` in `alpha`; `A3_monomial_exponent_mismatch`: `imagination` vs. `Appreciation`) plus joint **`A1_cross_item_one_to_many`** on `alpha` (`E001` vs. `E002`). |

---

## 8. Limitations, Nulls, & Negative Findings

1. **`D3a` Narrative Teaching Loss (`H5`):** Providing verbatim Ch. 2 prose without Ch. 16's boundary table **reduced** calibration accuracy from `12/17` (`70.59%`) to `8/17` (`47.06%`) overall (`McNemar p = 0.125`) and from `62/85` to `48/85` pooled (`p = 0.009355`), inducing systematic `"invert"` rulings on `K16` (`5/5`), `K06` (`5/5`), and `K05` (`4/5`).
2. **No Complete 14-Slot CSP Solution in `D1b` at `>= 3/5` or `>= 4/5`:** Even though `W_A0` dominated `all4` (`67.14%` vs. `0%–4.29%`) and **zero** competitors passed `>= 3/5` on any slot, literal readings of isolated `c1` left `4` slots (`W01, W02, W07, W10`) empty at `>= 3/5`, preventing a full `14/14` assignment from truth tables alone without Role 2/3 context.
3. **`D2a` Calibration Trade-off (`12/17 -> 8/17`):** Extending Rule R for Crossing solved `K17` (`0/5 -> 4/5` `keep`) and `D2b` (`7/7` valid-voter separation vs. `0/13`), yet the added Step 1a/1b guard text and `gamma`-stripping clause reduced `D2a` `K01..K16` consensus accuracy (`12/16 -> 7/16`), largely due to `mistral-medium-3.5` (`15/17 -> 8/17`).
4. **Template-Lint Fragility on `D2b` (`6` Schema Errors):** On `X001`, `X004`, and `X005`, models reliably identified `crossing_interface` (`7/7` raw parsed JSON) yet failed strict `{Slot}` bracing/naming lint `6` times (`2/5` strict on `X004`, `3/5` strict on `X005`), confirming that strict template serialization—not conceptual boundary detection—was the sole bottleneck on `D2b`.
5. **Isolated Passage / Slot Counterexamples (`W04`, `P06`):** `W_Ssyn` beat `W_A0` on `W04` (`growth` `4.80` vs. `Expansion` `4.00`) and `V_Ssyn` beat `V_A0` on `P06` (`4.40` vs. `3.60`), showing that single-slot or purely visual gravitational-basin metaphors do not uniformly favor Book spellings over fluent synonyms.
