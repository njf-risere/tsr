# TSR Deep-v3 Preregistration (`harness/deep_v3/`)

**Branch:** `feat/automated-llm-harness`  
**Parent Commits:** Commit 1 [`51109f83f96a94dfe7587c08a9ea972387b64889`], Commit 2 [`932205b733b505028adb32712594cb853321fac9`], Commit 3 [`7ee697ce32e17dd5db329386cb3ce6b6df02b696`]  
**Seeds:** Deep-v3 Shuffling Seed = `20261116`; Category-Preserving Derangement Seed = `101`.

---

## 1. Scope & Motivation Following v2 Results

The frozen v2 evaluation ([`RESULTS.md`](../RESULTS.md)) established significant Core-vs.-Boundary containment separation (`16/28` vs. `0/12`, exact Fisher `p = 0.00089872`, Holm-Bonferroni adjusted `p = 0.008088`), clear single-law plain-English preference for `T_A0` over shuffled `T_A3` (`p = 3.052e-5`) and directional reversal `D_A0` (`p = 6.104e-5`), and strict null divergence (`T_A0` vs. `S_syn`: `p = 0.24527` at the single-equation level; `M1`: `12/17` consensus parity without Book Ch. 2; `M5`: `6.67%` without web constraints; Layer A v2: `4` algebraic/notation false positives `E001, E002, E023, E027`).

Deep-v3 pre-registers **four targeted, zero-leakage diagnostic pillars (`D1`–`D4`)** to test those exact open questions without touching Commit-1 or Commit-2 files:

1. **Pillar D1 (`D1a` & `D1b` — Multi-Job Web Discrimination & 4-Criteria CSP):** Tests whether `A0`'s lexical assignments across `14` core Book slots (`W01..W14`) are distinguished from **both** Chapter-16 single-sense synonyms (`W_Ssyn`) and conceptual challengers (`W_Chal`) plus `A3-1` (`W_A3`) when three concrete first-order structural/contextual Cloze roles are judged simultaneously in zero-glossary English, and whether neutral boolean criteria `(c1..c4)` yield collision-free unique-word `14`-slot assignments via [`solve_collision_free_web_assignments`](./arms_v3.py).
2. **Pillar D2 (`D2a` & `D2b` — Crossing Boundary Protocol):** Tests whether explicitly adding the Chapter 16 Crossing entry `pressure -> felt gap` (`[crossing boundary]`) while distinguishing trailing parenthetical `(constant ...)` background qualifiers from active dynamical thermal/molar formula variables (`T`, `T_1`, `T_2`, `Delta T`, `Q`, `N`, `k_B`, `R`, `S` -> `no_partner`) unlocks pure mechanical pressure laws (`D2b` `Mechanical_Crossing`: `E029, X001..X006` -> `crossing_interface`) AND `K17` (`P_1 V_1 = P_2 V_2 (constant T, n)` -> zero-shot `crossing_interface`, `ruling = "keep"`, matching `expected_book_ruling: "keep"` in [`calibration_equations_17.json`](../openstax/calibration_equations_17.json)) without breaching the Boundary Guard on active thermal/molar/viscous laws (`D2b` `Non_Crossing_Boundary`: `11` held-out Boundary items plus `X007, X008` -> `no_partner`), under zero mention of `"Boyle"`, `"P_1"`, `"V_1"`, `"K17"`, or leaked calibration formulas.
3. **Pillar D3 (`D3a` & `D3b` — Narrative Teaching & Contextual Passage Discrimination):**
   - `D3a` supplies **strictly Book Chapter 2 *"The One Rule"* (`idx=19..22`) plus standard v2 `D3A_SCOPE_RULES`** (`pressure` remains in the unmapped blocklist -> `K17 = no partner` in `D3a`, providing a clean orthogonal factorial contrast against `D2a`'s Crossing rule while isolating the Ch. 2 narrative teaching effect on `K01..K17` vs. Commit-2 `M1 A0`, with zero Chapter 16 Crossing text, zero `applied_later` solutions, and zero `K14` leaks).
   - `D3b` tests `12` verbatim-derived multi-sentence Book excerpts (`P01..P06` `structural_paragraphs`, `P07..P12` `polysemy_bridge_paragraphs`) rendered grammatically across unlabeled masked variants `(V_A0, V_Ssyn, V_A3)`.
4. **Pillar D4 (`layer_a_v3.py` — Deterministic Algebraic & Calculus Layer-A Audit, `0` Live Calls):** Fixes the `3` purely mathematical normalization gaps identified in v2 (prime-bearing simple subscripts before standalone primes; case-insensitive English integral/summation/differential normalization; exact rational `Fraction` net-exponent cancellation and monomial cross-checks) while preserving all true `A1`/`A2`/`A3`/`A4` failure catches on frozen [`stage2_m2_heldout.json`](../outputs/stage2_m2_heldout.json).

---

## 2. Locked Model Roster, Runtime Parameters & Call Budget

- **Client & Logging:** [`providers.py`](../providers.py) (`CheaperInferenceClient` against `api.cheaperinference.com/v1/chat/completions`, `temperature = 0.0`, `top_p = 1.0` for `mistral`, `max_tokens` omitted, `timeout_sec = 240`, `MAX_PARSE_ATTEMPTS = 3`, concurrent worker pool `max_workers = 10` grouped by `(stage, task_id)`). Verbatim records append to `harness/deep_v3/logs/live_calls_v3.jsonl`; raw outputs in `harness/deep_v3/outputs/raw_*.json` scrub restricted tokens only in free-text prose (`reason`, `rationale`, `axis_polarity_note`, `errors`) without altering structured fields or raw JSONL `response_sha256`.
- **Generators / Zero-Glossary Raters (5 `providers.GENERATORS`):**
  1. `claude-sonnet-4.6` (`anthropic`)
  2. `gpt-5.4-fast` (`openai`)
  3. `gemini-2.5-flash` (`google`)
  4. `mistral-medium-3.5` (`mistral`)
  5. `llama-4-maverick` (`meta`)

| Stage | Scope & Design | Items | Models | Live Calls | Output Artifact |
| :--- | :--- | ---: | ---: | ---: | :--- |
| **`D1a`** | Unlabeled 4-way structural/contextual Cloze ratings (`W01..W14` + `NC01..NC03`) | 17 | 5 | 85 | `outputs/raw_d1a_web_ratings.json` |
| **`D1b`** | Zero-glossary 4-criteria boolean truth tables (`c1..c4` on `W01..W14`) | 14 | 5 | 70 | `outputs/raw_d1b_web_truthtable.json` |
| **`D2a`** | `crossing_interface`-enabled `calibration_17` (`K01..K17`, incl. `K17 = keep` zero-shot test) | 17 | 5 | 85 | `outputs/raw_d2a_crossing_cal17.json` |
| **`D2b`** | Crossing battery (`7` Mechanical Crossing + `13` Non-Crossing Boundary) | 20 | 5 | 100 | `outputs/raw_d2b_crossing_battery20.json` |
| **`D3a`** | Ch. 2 *"The One Rule"* verbatim + standard v2 scope rules on `calibration_17` (`K01..K17`) | 17 | 5 | 85 | `outputs/raw_d3a_narrative_cal17.json` |
| **`D3b`** | Masked 3-way Book excerpt ratings (`P01..P12`: `6` Structural + `6` Polysemy) | 12 | 5 | 60 | `outputs/raw_d3b_passage_ratings.json` |
| **`D4`** | Deterministic Layer-A v3 audit on frozen [`stage2_m2_heldout.json`](../outputs/stage2_m2_heldout.json) | 16x2 | — | 0 | `outputs/raw_d4_layer_a_audit.json` |
| **Total** | | | | **485** | |

---

## 3. Experimental Materials & Candidate Tables

### 3.1 Pillar D1 Core Web Slots (`W01..W14`) & Physics Calibration Controls (`NC01..NC03`)

Every un-substituted `D1a` and `D1b` prompt enforces `_check_d1_zero_candidate_leak` so zero candidate words or morphological stems appear anywhere in the structural prompts or criteria, and forbids meta-linguistic dictionary riddles (testing concrete first-order Cloze sentences in `Role 3` and neutral semantic fit in `c4`). Candidates `1..4` are deterministically shuffled per `(item_id, model_id)` with `seed = 20261116`.

| Slot | `W_A0` | `W_Ssyn` | `W_Chal` | `W_A3` |
| :--- | :--- | :--- | :--- | :--- |
| `W01` | `Movement` | `responsiveness` | `soul` | `Reflected` |
| `W02` | `Current` | `stream` | `source` | `Frequency` |
| `W03` | `Vibration` | `pitch` | `mind` | `Appreciation` |
| `W04` | `Expansion` | `growth` | `eternity` | `Vibrance` |
| `W05` | `Desire` | `longing` | `intensity` | `conscious energy` |
| `W06` | `Vibrance` | `capacity` | `openness` | `Desire` |
| `W07` | `Appreciation` | `gratitude` | `growth` | `imagination` |
| `W08` | `Frequency` | `urgency` | `will` | `Movement` |
| `W09` | `Tune` | `focus` | `surrender` | `resonance` |
| `W10` | `Idle` | `stillness` | `rest` | `rise per Expansion` |
| `W11` | `Reflected` | `echo` | `returning` | `Current` |
| `W12` | `Vortex` | `whirlpool` | `well` | `Attraction` |
| `W13` | `Convergence` | `gathering` | `lens` | `Intuition` |
| `W14` | `Intuition` | `hunch` | `expectation` | `Vortex` |

Physics negative-calibration controls (`NC01..NC03`) verify that zero-glossary raters reliably identify canonical physical law terms against plausible physics distractors: `NC01` (`inertia` vs. `impulse`, `elasticity`, `friction`), `NC02` (`torque` vs. `pressure`, `power`, `entropy`), `NC03` (`equilibrium` vs. `viscosity`, `acceleration`, `amplitude`).

### 3.2 Pillar D2 Crossing Battery (`crossing_battery_20.json`)

Extracted verbatim from [`openstax_key_equations_raw.csv`](../openstax/openstax_key_equations_raw.csv) with zero overlap with [`calibration_equations_17.json`](../openstax/calibration_equations_17.json):

- **`Mechanical_Crossing` (`7` items, expected `crossing_interface`):** `E029` (V1 C14 R4), `X001` (V1 C14 R2), `X002` (V1 C14 R3), `X003` (V1 C14 R5), `X004` (V1 C14 R6), `X005` (V1 C14 R10), `X006` (V2 C3 R2).
- **`Non_Crossing_Boundary` (`13` items, expected `no_partner`):** `E003`, `E004`, `E009`, `E012`, `E015`, `E019`, `E025`, `E031`, `E032`, `E033`, `E034` (the `11` non-`E029` held-out Boundary items from [`heldout_equations_40.json`](../openstax/heldout_equations_40.json)) plus `X007` (V2 C2 R2 Ideal gas law ratios if the amount of gas is constant, containing active dynamical `T_1, T_2`) and `X008` (V1 C14 R13 Poiseuille's law, containing active viscosity `eta` and pipe-flow rate `Q`).

### 3.3 Pillar D3b Masked Excerpts (`P01..P12`)

Rendered grammatically across `(V_A0, V_Ssyn, V_A3)` with zero un-slotted self-circular candidate words in explanatory frames, shuffled `1..3` per `(passage_id, model_id)` (`seed = 20261116`):

- **`structural_paragraphs` (`P01..P06`):**
  - `P01` (`Ch. 2, idx=20 (pdf_page 21)`): `{Movement}` (whole-part symphony unity).
  - `P02` (`Ch. 2, idx=20 (pdf_page 21)`): `{Vibration}`, `{Expansion}` (non-spatial qualitative continuum and whole-system irreversible addition).
  - `P03` (`Ch. 2, idx=21 & idx=24 (pdf_page 22/25)`): `{Movement}`, `{Desire}`, `{Vibrance}` (compositional factorization `Movement = Desire * Vibrance` vs. gravitational/relational pull).
  - `P04` (`Ch. 2, idx=22 (pdf_page 23)`): `{Vibration}`, `{Expansion}`, `{Appreciation}`, `{Current}`, `{Movement}`, `{Frequency}` (second-order climb, inward medium pull, and `Frequency = Movement * Appreciation`).
  - `P05` (`Ch. 2, idx=23 (pdf_page 24)`): `{Movement}`, `{Current}`, `{Vibrance}`, `{Vibration}`, `{Appreciation}`, `{Expansion}`, `{Frequency}` (continuous structural mirror correspondence).
  - `P06` (`Ch. 16, idx=119-120 (pdf_page 120-121)`): `{Movement}`, `{Vortex}`, `{Current}`, `{Attraction}`, `{Convergence}` (gravitational basin geometry and glass-free pathway focusing).
- **`polysemy_bridge_paragraphs` (`P07..P12`):**
  - `P07` (`Ch. 2 idx=20, 23 & Ch. 16 idx=121 (pdf_page 21, 24, 121)`): `{Idle}`, `{Reflected}`, `{Current}` (dynamically live inward-collecting medium without spatial displacement).
  - `P08` (`Ch. 16, idx=121 (pdf_page 122)`): `{Expansion}`, `{Appreciation}`, `{Current}`, `{Frequency}` (second-order compounding acceleration vs. outward expansion and ongoing present medium).
  - `P09` (`Ch. 16, idx=121 (pdf_page 122)`): `{Tune}`, `{Attraction}`, `{conscious_energy}` (deliberate non-forcing channel selection at the multiplier hinge).
  - `P10` (`Ch. 16, idx=120-121 (pdf_page 121-122)`): `{Expansion}`, `{Vibration}`, `{Frequency}` (irreversible widening, non-spatial continuum, and qualitative experiential pull).
  - `P11` (`Ch. 16, idx=122 (pdf_page 123)`): `{Desire}`, `{Movement}`, `{Out For}`, `{Current}`, `{Vibration}`, `{Vibrance}`, `{Frequency}` (directed wanting, self-contained unit, outward-forging aim, and oscillatory extent/rate).
  - `P12` (`Ch. 2 idx=24 & Ch. 16 idx=119 (pdf_page 25, 120)`): `{Intuition}`, `{Desire}`, `{Expansion}`, `{Movement}` (hinge direct apprehension, concentrated wanting, and non-duplicative Book structure).

---

## 4. Preregistered Confirmatory Hypotheses (`H1`–`H6`) & Exact Statistical Tests

All `6` confirmatory hypotheses share a single family-wise Holm-Bonferroni correction (`exact_stats.holm_bonferroni`, `alpha = 0.05`) using exact stdlib tests from [`exact_stats.py`](../exact_stats.py), treating slots, equations, calibration items, or passages (rather than pooled rater observations) as the primary unit of analysis:

| ID | Pillar | Comparison & Unit of Analysis | Primary Exact Test | Decision Rule / What It Tests |
| :--- | :--- | :--- | :--- | :--- |
| **`H1`** | `D1a` | `W_A0` vs. `W_Ssyn` mean rater score per slot on `W01..W14` (`N = 14` paired slots) | Two-sided exact sign-flip paired permutation test (`2^14 = 16,384` flips, `exact_paired_permutation_test`) | Tests whether multi-job structural constraints distinguish `A0` terms from Ch. 16 single-sense synonyms (`S_syn`). |
| **`H2`** | `D1a` | `W_A0` vs. `W_Chal` mean rater score per slot on `W01..W14` (`N = 14` paired slots) | Two-sided exact sign-flip paired permutation test (`2^14 = 16,384` flips, `exact_paired_permutation_test`) | Tests whether multi-job structural constraints distinguish `A0` terms from hand-crafted conceptual challengers (`W_Chal`). |
| **`H3`** | `D1b` | `W_A0` vs. mean of `(W_Ssyn, W_Chal, W_A3)` on per-slot `all4` boolean pass fraction (`c1..c4` all `true` across `5` raters) on `W01..W14` (`N = 14`) | Two-sided exact sign-flip paired permutation test (`2^14 = 16,384` flips, `exact_paired_permutation_test`) | Tests whether `A0` uniquely satisfies all `4` binary criteria jointly, paired with exact `solve_collision_free_web_assignments` enumeration. |
| **`H4`** | `D2b` | `>= 4/5` `crossing_interface` consensus rate: `Mechanical_Crossing` (`7` items) vs. `Non_Crossing_Boundary` (`13` items) (`N = 20`) | Two-sided `2x2` exact Fisher test (`exact_fisher_2x2`) | Tests whether adding `pressure -> felt gap` cleanly opens mechanical Crossing laws while leaving thermal/molar/viscous Boundary Guard items `no_partner`. |
| **`H5`** | `D3a` | `>= 4/5` consensus calibration accuracy on `K01..K17`: `D3a` (Ch. 2 *"The One Rule"* verbatim + standard v2 scope rules) vs. frozen Commit-2 [`stage1_m1_calibration.json`](../outputs/stage1_m1_calibration.json) `A0` (`12/17`, `N = 17`) | Two-sided exact McNemar test (`exact_mcnemar_test`) | Tests whether teaching strictly Book Ch. 2 *"The One Rule"* lifts `M1` `keep`/`invert` accuracy over unassisted Rule R. |
| **`H6`** | `D3b` | `V_A0` vs. `V_Ssyn` mean rater score per excerpt on `P01..P12` (`N = 12` paired excerpts) | Two-sided exact sign-flip paired permutation test (`2^12 = 4,096` flips, `exact_paired_permutation_test`) | Tests whether multi-sentence Book context separates `V_A0` from single-sense synonyms `V_Ssyn`. |

**Deterministic Audit (`D4`, `0` Live Calls — Outside Stochastic Holm Family):** Verifies algebraically that on the `16` frozen [`stage2_m2_heldout.json`](../outputs/stage2_m2_heldout.json) consensus `keep`/`invert` items per arm, `A0` achieves `16/16` per-item passed and `0` joint collisions (`passes_all == true`) whereas `A3-1` still fails (`15/16` per-item, failing `E001` `"angular"` and joint `A1_cross_item_one_to_many` on `alpha`, `passes_all == false`).

**Prespecified Secondary / Exploratory Diagnostics:** (1) `D1a` `W_A0` vs. `W_A3` on `W01..W14` + `NC01..NC03` `#1` control accuracy and `Fleiss' kappa`; (2) `D1b` majority (`>= 3/5`) per-criterion pass rates and unique-word CSP solution counts; (3) `D2a` `17`-item consensus ruling accuracy (`ruling == expected_book_ruling` on `K01..K17`, including `K17 = keep` via zero-shot `crossing_interface` under Step 1a constant side-condition handling) and orthogonal `D2a` vs. `D3a` contrast on `K17` (`crossing_interface` vs. `no_partner`); (4) `D3a` pooled `85`-call accuracy vs. Commit-2 `M1 A0` (`85` calls); (5) `D3b` stratified `structural_paragraphs` vs. `polysemy_bridge_paragraphs` comparisons and `V_A0` vs. `V_A3`.

---

## 5. Frozen Artifact SHA-256 Digests

- [`arms_v3.py`](./arms_v3.py): `sha256: 410b3d6f37d23828231a851fdb3d0f91ab5996e0ba9b08d61725b5bf237d7c21`
- [`layer_a_v3.py`](./layer_a_v3.py): `sha256: bab206f674b783f4f98df44fa11cc8cf644c8f0c39e4ac2d5d5397730a38eafb`
- [`crossing_battery_20.json`](./crossing_battery_20.json): `sha256: 6ad789cfd38b9e72c77df51caaf731e30e0cdc0230fbfa67cdda2ca2e52306f2`
- [`run_deep_v3.py`](./run_deep_v3.py): `sha256: 6ff0b2edd3dde5e9a48dcd50789582c93110a96c8671de820fb4677627b83c0f`
- [`__init__.py`](./__init__.py): `sha256: 5035f3ab27bffc637b6d4e9889077babca55a626533f636a1f5274ec73620900`

Source frozen references verified from Commit 1 & Commit 2:
- [`openstax_key_equations_raw.csv`](../openstax/openstax_key_equations_raw.csv): `sha256: 0cf6ee7c9ca09b0f2653f6253308d7f6532436f2f27cc5f4f4fa38fa4399db2d`
- [`calibration_equations_17.json`](../openstax/calibration_equations_17.json): `sha256: 2f18b33f834d54a820458dbe94050834ac3d5fc13a6e4250fc037652a31bc4a2`
- [`heldout_equations_40.json`](../openstax/heldout_equations_40.json): `sha256: 10ecc2de0861821fd741e8f5f059b291f73cb310766afcc603cd7ffcfb6ebbdf`
- [`stage1_m1_calibration.json`](../outputs/stage1_m1_calibration.json): `sha256: 5dd91e885ff36192f5bcf3db2ef2196b1aa6f5277ae2bffd3db35a70c6ba9472`
- [`stage2_m2_heldout.json`](../outputs/stage2_m2_heldout.json): `sha256: 1675d92fcee22084c79cdbe8e4c5ae6a22a6984ca6ddd47e3fa75dc4dd9f3e3d`
