# TSR Non-Cipher Evaluation Results (v2)

**Branch:** `feat/automated-llm-harness`
**Preregistration Commit (`HARNESS_PREREG_SHA`):** `51109f83f96a94dfe7587c08a9ea972387b64889` ([PREREGISTRATION.md](./PREREGISTRATION.md))
**Pre-Eval Raw Data Commit (`PRE_EVAL_COMMIT_SHA`):** `932205b733b505028adb32712594cb853321fac9`
**Evaluators & Artifacts:** [`exact_stats.py`](./exact_stats.py), [`evaluate_tsr_harness.py`](./evaluate_tsr_harness.py), [`summary_v2.json`](./outputs/summary_v2.json), [`m1_calibration_17.csv`](./outputs/m1_calibration_17.csv), [`m2_m3_heldout_40.csv`](./outputs/m2_m3_heldout_40.csv), [`m4_quadruple_ratings.csv`](./outputs/m4_quadruple_ratings.csv), [`m5_vocab_free_12.csv`](./outputs/m5_vocab_free_12.csv)

---

## 1. Executive Summary (What PR #5 v2 Tests & Why v1 Was Replaced)

This evaluation tests whether Book Ch. 2 and Ch. 16's non-cipher physical-to-nonphysical nomenclature (`A0`, e.g., `mass -> Movement`, `space -> Vibration`, `time -> Expansion`, `acceleration -> Appreciation`, `force -> Frequency`, `gravity -> Attraction`, `friction/damping -> resonance`) reflects physics equations into coherent ordinary-English statements with cross-law structural consistency, without leaking glossary definitions or calibration solutions. The earlier v1 cipher harness (`archive/cipher-harness-v1-724fab2`, including the dropped Wiktionary `part4_etymology/` module) exposed prose glossary senses directly to Layer-B judges and raters, embedded worked calibration equations in `Rule R`, altered `K12`, carried `"Movement M"` suffix artifacts, and omitted symmetric permutation across rotational and frame slots. In v2, defined in [`arms_v2.py`](./arms_v2.py) and [`PREREGISTRATION.md`](./PREREGISTRATION.md), **zero inline glossary definitions appear in any prompt**, all calibration formulas are stripped from `Rule R`, `K17` (Boyle's law) is withheld from `M2` worked examples, and both `A0` and the `seed = 101` typed category-preserving derangement `A3-1` are evaluated across 6 stages (`M1`–`M5`) by 6 independent model families ([`providers.py`](./providers.py)).

Across **907 live API calls** (**822 unique call keys**, **85 retry calls**, **7 unrecovered schema errors**, all 7 from `llama-4-maverick`), the empirical record shows a sharp distinction between **structural/ordinary-English fluency under fixed templates** (where `A0` strongly outperforms `A3-1` and polarity-flipped `D_A0`) and **zero-glossary equation verification, native unaligned paraphrasing, formal graph parsing, and unassisted word discovery** (where both arms exhibit substantial misses, collisions, or null differences):

1. **Calibration (`M1`, `K01..K17`):** Both `A0` and `A3-1` achieve **`12/17` (`70.59%`)** consensus accuracy overall and **`12/16` (`75.00%`)** on `K01..K16` (`McNemar p = 1.0`), with unanimous `5/5` exclusion of `K17` (Boyle's law) as `"no partner"` due to blocklisted `temperature` and `pressure`.
2. **Held-Out Filtering & Layer A (`M2`, `E001..E040`):** Both arms reach identical `>= 4/5` consensus rulings on `34/40` equations (`13` `keep`, `3` `invert`, `18` `no partner`, `6` `no_consensus`). Stratified filtering cleanly separates `Core` (`16/28` `keep`/`invert`, `57.14%`) from `Boundary` (`0/12` `keep`/`invert`, `11/12 = 91.67%` consensus `"no partner"`, `Fisher p = 0.000899`, Holm-adjusted `p = 0.008088`). However, joint Layer A fails on **both** arms (`passes_all = false`): `A0` passes `12/16` (`75.00%`) per-item with `4` joint collisions (`E001`, `E002`, `E023`, `E027`), and `A3-1` passes `13/16` (`81.25%`) per-item with `5` joint collisions (`E001`, `E023`, `E027`, plus cross-item `A1` splitting of `alpha`).
3. **Adversarial Opponent (`M3b`):** `deepseek-v4.1-flash-fast` upholds `12/16` (`75.00%`) on `A0` vs. `13/16` (`81.25%`) on `A3-1` (`McNemar p = 1.0`), catching real edge defects on both arms (`E016`, `E021`, `E023`, `E039` on `A0`; `E002`, `E023`, `E039` on `A3-1`).
4. **Zero-Glossary Layer B (`M3c`):** Under strict zero-glossary vertical judging against the raw physics equation (`M3c_single`), `2/2` judge coherence is low on both arms: **`3/16` (`18.75%`)** for `A0` vs. **`2/16` (`12.50%`)** for `A3-1` (`McNemar p = 1.0`). Horizontally across all `81` shared-slot pairs per arm (`162` pairs total), **both** arms record **`0/81` (`0.00%`)** `2/2` contradictions and **`0` confirmed Rule-1 collisions** (`2/81` `1/2` flags on `A0`; `3/81` `1/2` flags on `A3-1`, `Fisher p = 1.0`).
5. **Zero-Glossary Ordinary-English Rating (`M4`):**
   - On **`M4_item` (`16` Core items x `4` raters = `64` ratings, separated from `R9`/`R10`)**, `T_A0` achieves mean **`4.5156`** (`SD = 0.7125`) and **`41/64` (`64.06%`)** `#1` selections (exact binomial vs. `0.25`, `p = 4.950e-11`, Holm-adjusted `5.940e-10`), compared to `S_syn` (`4.2969`, `13/64 = 20.31%`), `T_A3` (`3.7188`, `7/64 = 10.94%`), and `D_A0` (`2.2969`, `52/64 = 81.25%` worst). At the primary item level (`N = 16`), `T_A0` outscores `T_A3` on **`16/16` items** (`mean diff = +0.7969`, exact sign-flip `p = 3.052e-05`, Holm-adjusted `0.000336`) and `D_A0` on **`15/16` items** (`+2.2188`, `p = 6.104e-05`, Holm-adjusted `0.000610`), whereas `T_A0` vs. `S_syn` (`+0.2188`, `11` wins / `5` losses) is **not statistically significant** (`p = 0.2453`, Holm-adjusted `1.0`).
   - On synthetic controls **`R9` & `R10`** (`8` ratings), `D_A0` is rated worst **`8/8` (`100%`)** (`mean = 1.875`), confirming polarity sensitivity; `S_syn` averages `4.875` (`6/8` best) and `T_A0` averages `4.500` (`2/8` best).
   - On **`M4_native_pair`** (independently generated native `A0` vs. `A3-1` statements across the `16` shared consensus items), the result is a **null**: `A0` wins `31/64` vs. `A3-1` `23/64` with `10` ties (`mean = 3.2969` vs. `3.2188`; item-level `10` vs. `6`, exact sign-flip `p = 0.8267`).
   - On **`M4_bundle`** (`3` order permutations x `4` raters = `12` system-bundle calls), `T_A0` leads descriptively (`mean = 3.5000`, `5/12` best, `0/12` worst) over `S_syn` (`3.3333`, `4/12` best, `0/12` worst), `T_A3` (`2.5833`, `1/12` best, `4/12` worst), and `D_A0` (`2.1667`, `2/12` best, `8/12` worst), with call-level `T_A0 - T_A3` `p = 0.0156` (Holm-adjusted `0.125`, not significant after multiplicity or at `N = 4` rater level `p = 0.25`) and clear permutation-order drift (`perm_2` scores sharply higher for non-flipped systems than `perm_0`/`perm_1`).
6. **Leak-Free Discovery (`M5`):** Across `12` physical slots x `5` models (`60` proposals), `4/60` (`6.67%`) match Book `A0` primary targets exactly (`damping -> resonance` `3/5` primary and `5/5` including alternates; `gravity -> attraction` `1/5` primary), plus `2/60` (`3.33%`) match `S_syn` (`friction -> harmony`). Mean modal agreement across the 12 slots is `0.3833`.

---

## 2. Provenance, Call Ledger, Latency, & Schema Error Accounting

All metrics are computed deterministically from immutable Commit-2 outputs (`PRE_EVAL_COMMIT_SHA = 932205b733b505028adb32712594cb853321fac9`) and raw logs in [`live_calls.jsonl`](./logs/live_calls.jsonl) ([`run_tsr_harness.py`](./run_tsr_harness.py)).

| Role / Stage | Unique Keys | Total Live Calls | Retry Calls | Unrecovered `schema_error` |
| :--- | ---: | ---: | ---: | ---: |
| `stage1_m1_generator` | 170 | 223 | 53 | 5 |
| `stage2_m2_generator` | 400 | 429 | 29 | 2 |
| `stage3_m3b_opponent` | 32 | 32 | 0 | 0 |
| `stage4_m3c_single` | 64 | 64 | 0 | 0 |
| `stage4_m3c_pairs` | 56 | 56 | 0 | 0 |
| `stage4_m3c_rule1` | 0 | 0 | 0 | 0 |
| `stage5_m4_item` | 16 | 17 | 1 | 0 |
| `stage5_m4_native_pair` | 12 | 12 | 0 | 0 |
| `stage5_m4_bundle` | 12 | 14 | 2 | 0 |
| `stage6_m5_vocab_free` | 60 | 60 | 0 | 0 |
| **Total** | **822** | **907** | **85** | **7** |

Cumulative API latency across all 907 logged calls was **`5519.264 s`** (`5,519,264 ms`):

| Model | Calls | Total (s) | Mean (ms) | Median (ms) | p95 (ms) | Max (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-sonnet-4.6` | 205 | 1800.419 | 8782.53 | 7808.0 | 14771.0 | 23171 |
| `gpt-5.4-fast` | 198 | 647.735 | 3271.39 | 2914.5 | 5378.0 | 6267 |
| `gemini-2.5-flash` | 145 | 1854.616 | 12790.46 | 9101.0 | 29377.0 | 185765 |
| `mistral-medium-3.5` | 146 | 389.943 | 2670.84 | 2552.0 | 3770.0 | 4702 |
| `llama-4-maverick` | 181 | 364.647 | 2014.62 | 1964.0 | 2588.0 | 3973 |
| `deepseek-v4.1-flash-fast` | 32 | 461.904 | 14434.50 | 7978.5 | 35681.0 | 38714 |

All 7 unrecovered `schema_error` records occurred on `llama-4-maverick` (`Stage 1 A0`: `K08`, `K09`; `Stage 1 A3-1`: `K06`, `K07`, `K08`; `Stage 2 A0`: `E017`; `Stage 2 A3-1`: `E011`), leaving `>= 4` valid generators for consensus voting on every item except `Stage 1 A3-1 K06` (`3/4` valid votes `invert` + `1` `keep`).

---

## 3. Stage 1 (`M1`): Zero-Shot Calibration (`K01..K17` & `K01..K16` vs. `K17`)

Full item-level records are in [`m1_calibration_17.csv`](./outputs/m1_calibration_17.csv).

| Metric | `A0` | `A3-1` | `A0` vs. `A3-1` Exact Test |
| :--- | :---: | :---: | :--- |
| Reached `>= 4/5` consensus (`K01..K17`) | `15/17` (`88.24%`) | `14/17` (`82.35%`) | — |
| **Exact match on `K01..K17`** | **`12/17` (`70.59%`)** | **`12/17` (`70.59%`)** | McNemar `p = 1.0` (`n10=1, n01=1`); Fisher `p = 1.0` |
| **Exact match on `K01..K16`** | **`12/16` (`75.00%`)** | **`12/16` (`75.00%`)** | McNemar `p = 1.0` (`n10=1, n01=1`); Fisher `p = 1.0` |
| `K17` (Boyle's law, expected `keep`) | `0/1` (`5/5` `no partner`) | `0/1` (`5/5` `no partner`) | Identical unanimous exclusion |
| Schema errors | `2` (`llama-4-maverick`) | `3` (`llama-4-maverick`) | — |

Per-generator accuracy (`K01..K17` / `K01..K16`):
- `mistral-medium-3.5`: `15/17` (`88.24%`) / `15/16` (`93.75%`) on both `A0` and `A3-1`
- `gemini-2.5-flash`: `14/17` (`82.35%`) / `14/16` (`87.50%`) on both `A0` and `A3-1`
- `claude-sonnet-4.6`: `13/17` (`76.47%`) / `13/16` (`81.25%`) on `A0`; `12/17` (`70.59%`) / `12/16` (`75.00%`) on `A3-1` (`McNemar p = 1.0`)
- `gpt-5.4-fast`: `11/17` (`64.71%`) / `11/16` (`68.75%`) on `A0`; `13/17` (`76.47%`) / `13/16` (`81.25%`) on `A3-1` (`McNemar p = 0.5`)
- `llama-4-maverick`: `9/17` (`52.94%`) / `9/16` (`56.25%`) on both `A0` and `A3-1`

**Calibration Misses (`K01..K17`):**
- `K05` (time dilation, expected `keep`): `4/5` voted `invert` on both arms (only `mistral-medium-3.5` predicted `keep`).
- `K06` (length contraction, expected `keep`): `A0` `4/5` `invert`; `A3-1` `3/5` `invert` + `1` `keep` + `1` `SCHEMA_ERROR` (no consensus).
- `K16` (`F = ma`, expected `keep`): `3/5` `keep` on both arms (`mistral-medium-3.5` and `llama-4-maverick` voted `invert`; missed `>= 4/5` consensus).
- `K04` (special vs. general relativity, expected `keep`): `A0` `4/5` `keep` (correct); `A3-1` `3/5` `keep` (no consensus: `claude` voted `invert`, `llama` voted `no partner`).
- `K12` (gravitational wells & lensing, expected `keep`): `A0` `3/5` `keep` (no consensus: `gpt` `invert`, `llama` `no partner`); `A3-1` `5/5` `keep` (correct).
- `K17` (Boyle's law, expected `keep`): `5/5` voted `no partner` on both arms because `temperature` and `pressure` are listed on `UNMAPPED_BLOCKLIST_V2` and `K17` was tested strictly zero-shot.

---

## 4. Stage 2 (`M2`) Held-Out Filtering (`E001..E040`) & Formal Layer A

Full item-level data are in [`m2_m3_heldout_40.csv`](./outputs/m2_m3_heldout_40.csv) and [`layer_a_summary.json`](./outputs/layer_a_summary.json).

### 4.1 Consensus Ruling & Stratum Discrimination

Both `A0` and `A3-1` produced **identical consensus outcomes across all 40 held-out equations** (`0` cross-arm consensus differences; McNemar on `keep`/`invert` membership `p = 1.0`):

| Stratum (`N`) | `keep` | `invert` | `no partner` | `no_consensus` | `keep`/`invert` Rate |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `Core` (`28`) | `13` | `3` | `7` | `5` | `16/28` (`57.14%`; `16/23 = 69.57%` of consensus) |
| `Boundary` (`12`) | `0` | `0` | `11` | `1` | `0/12` (`0.00%`; `11/12 = 91.67%` consensus excluded) |
| **All (`40`)** | **`13`** | **`3`** | **`18`** | **`6`** | **`16/40` (`40.00%`; `34/40 = 85.00%` reached consensus)** |

Core vs. Boundary `keep`/`invert` discrimination is highly significant on both arms (**Fisher `2x2` exact `p = 0.0008987`**, Holm-adjusted `p = 0.008088`): **zero** of the 12 thermodynamic/fluid/circuit/optics `Boundary` equations leaked into `keep` or `invert` (`E009` fell short of `>= 4/5` consensus at `3/5` `no partner`, `1` `keep`, `1` `invert`). Per-model agreement across the 34 consensus items was `34/34` (`gemini`, `mistral`), `32/34` `A0` / `34/34` `A3-1` (`claude`), `33/34` `A0` / `31/34` `A3-1` (`gpt`), and `26/34` `A0` / `24/34` `A3-1` (`llama`). The 6 non-consensus items on both arms were `E008`, `E010`, `E013`, `E020`, `E040` (`Core`) and `E009` (`Boundary`).

### 4.2 Formal Layer-A Graph Integrity

Among the `16` shared consensus `keep`/`invert` items (`E001`, `E002`, `E007`, `E011`, `E014`, `E016`, `E018`, `E021`, `E022`, `E023`, `E027`, `E028`, `E030`, `E037`, `E038`, `E039`):

- **`A0`:** `12/16` (`75.00%`) passed per-item Layer A; **`4` joint collisions** (`passes_all = false`):
  - `E001` (`a_CM = R * alpha`) and `E002` (`a_t = r * alpha`): `A3_exponent_or_quotient_flip` because `alpha` was mapped to `Appreciation / Vibration` while `R`/`r` mapped to `Vibration`, producing mixed sign `[-1, 1]` on `Vibration` inside `Vibration * (Appreciation / Vibration)` rather than algebraic cancellation.
  - `E023` (work integral): `A2_formula_unknown_tokens` (`integral over path of ...` prose inside `reflected_formula`).
  - `E027` (relative acceleration): `A2_formula_unknown_tokens` (`AppreciationS` after prime stripping on `S'S`).
- **`A3-1`:** `13/16` (`81.25%`) passed per-item Layer A; **`5` joint collisions** (`passes_all = false`):
  - `E001`: `A1_invalid_target_token` (`alpha -> imagination (angular) = imagination / Appreciation`) and `A3_exponent_or_quotient_flip`.
  - `E023` & `E027`: `A2_formula_unknown_tokens` (`integral over path of ...` and `imaginationS`).
  - Joint `A1_cross_item_one_to_many`: `alpha` mapped differently between `E001` (`imagination (angular) = imagination / Appreciation`) and `E002` (`imagination`), which allowed `E002` to pass per-item checks while failing cross-item bijection.
- **Arm Comparison:** Per-item Layer-A pass rates do not differ (`12/16` vs. `13/16`, McNemar `p = 1.0`, `n10 = 0, n01 = 1`; Fisher `p = 1.0`), and neither arm passes joint Layer A cleanly.

---

## 5. Stage 3 (`M3b`): Adversarial Opponent & Stage 4 (`M3c`): Zero-Glossary Layer B

### 5.1 Stage 3 (`M3b`) Adversarial Opponent (`deepseek-v4.1-flash-fast`)

Quarantined adversarial stress-testing across the 16 consensus `keep`/`invert` items per arm:
- **`A0`:** `12/16` (`75.00%`) `uphold`, `4/16` (`25.00%`) `attack`:
  - `E016` (`polarity_flip` — inverse Lorentz transformation classified `keep` despite `gamma` denominator),
  - `E021` (`formula_mismatch` — `translation_t` dropped leading minus sign present in `reflected_formula`),
  - `E023` (`dictionary_mismatch` — work `W_AB` mapped to `conscious energy` instead of `Frequency × Vibration`),
  - `E039` (`polarity_flip` — normal force classified `keep` despite contact resistance barrier).
- **`A3-1`:** `13/16` (`81.25%`) `uphold`, `3/16` (`18.75%`) `attack`:
  - `E002` (`dictionary_mismatch` — `alpha` mapped to `imagination (angular)` instead of `imagination ÷ Appreciation`),
  - `E023` (`formula_mismatch` — `W_AB` mapped in `variable_map` as `Movement × Appreciation` but dropped `Appreciation` in `reflected_formula`),
  - `E039` (`polarity_flip` — normal force classified `keep`).
- **Comparison:** Fisher `p = 1.0`, paired McNemar `p = 1.0` (`n10 = 1, n01 = 2`, `11` both upheld, `2` both attacked).

### 5.2 Stage 4 (`M3c`) Zero-Glossary Layer B (`claude-sonnet-4.6` & `gpt-5.4-fast`)

**Vertical (`M3c_single`, `16` items per arm):**
When two zero-glossary judges evaluated whether `translation_t` both reads as coherent ordinary English AND matches the raw LaTeX physical law structure:

| Metric | `A0` (`16` items) | `A3-1` (`16` items) | `A0` vs. `A3-1` Exact Test |
| :--- | :---: | :---: | :--- |
| **`2/2` `coherent`** | **`3/16` (`18.75%`)** (`E007`, `E018`, `E027`) | **`2/16` (`12.50%`)** (`E007`, `E027`) | McNemar `p = 1.0` (`n10=1, n01=0`); Fisher `p = 1.0` |
| `>= 1/2` `coherent` | `7/16` (`43.75%`) | `6/16` (`37.50%`) | — |
| Judge Cohen's kappa (`verdict`) | `0.4286` | `0.3469` | — |
| `claude-sonnet-4.6` `coherent` | `6/16` (`37.50%`) | `5/16` (`31.25%`) | McNemar `p = 1.0`; Fisher `p = 1.0` |
| `gpt-5.4-fast` `coherent` | `4/16` (`25.00%`) | `3/16` (`18.75%`) | McNemar `p = 1.0`; Fisher `p = 1.0` |

Sub-field breakdown reveals *why* vertical coherence was low without a glossary: `gpt-5.4-fast` judged `coherent_ordinary_english = true` on `14/16` (`87.50%`) `A0` and `12/16` (`75.00%`) `A3-1` (and `nonsensical_or_cipher_like = false` on `14/16` `A0` and `12/16` `A3-1`), yet marked `matches_physical_law_structure = false` on `12/16` `A0` and `13/16` `A3-1` because nonphysical terms (`Appreciation`, `Movement`, `Frequency`, `resonance`) do not transparently reveal physical law semantics when no partner key is supplied. `claude-sonnet-4.6` was stricter on `coherent_ordinary_english` (`7/16` on both arms) and flagged `nonsensical_or_cipher_like = true` on `10/16` (`A0`) and `9/16` (`A3-1`).

**Horizontal (`M3c_pairs`, `81` shared-slot pairs per arm = `162` total):**
- **`A0`:** `0/81` `2/2` contradictions, **`0` confirmed Rule-1 collisions**, `2/81` (`2.47%`) `1/2` contradictions (both from `claude-sonnet-4.6` only: `PR_4438CB88` [`E007`, `E030` on `Vibration`] and `PR_9947B9F1` [`E023`, `E028` on `Vibration`]; `gpt-5.4-fast` `0/81`; Cohen's kappa `0.0`).
- **`A3-1`:** `0/81` `2/2` contradictions, **`0` confirmed Rule-1 collisions**, `3/81` (`3.70%`) `1/2` contradictions (all from `gpt-5.4-fast` only: `PR_20E84B63` [`E014`, `E027` on `Reflected`], `PR_E16E6B26` [`E021`, `E027` on `Reflected`], `PR_F0D052C0` [`E038`, `E039` on `Reflected`]; `claude-sonnet-4.6` `0/81`; Cohen's kappa `0.0`).
- **Comparison:** Fisher exact `p = 1.0` for both `0/81` vs. `0/81` Rule-1 collisions and `2/81` vs. `3/81` `1/2` contradictions.

---

## 6. Stage 5 (`M4`): Zero-Glossary Ordinary-English & Whole-System Ratings

All Stage 5 raters (`claude-sonnet-4.6`, `gpt-5.4-fast`, `gemini-2.5-flash`, `llama-4-maverick`) received zero equations, zero glossary definitions, and deterministically shuffled unlabeled candidates/systems ([`m4_quadruple_ratings.csv`](./outputs/m4_quadruple_ratings.csv)).

### 6.1 `M4_item` Core Equations (`16` Core Items x `4` Raters = `64` Ratings; Separated from `R9`/`R10`)

| Variant | Mean (SD) | Median | `#1` Best Count (Share) | Exact Binom vs. `0.25` (`>`) | `#4` Worst Count (Share) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`T_A0`** | **`4.5156` (`0.7125`)** | **`5.0`** | **`41/64` (`64.06%`)** | **`p = 4.950e-11`** | **`3/64` (`4.69%`)** |
| **`S_syn`** | `4.2969` (`0.7055`) | `4.0` | `13/64` (`20.31%`) | `p = 0.8442` | `1/64` (`1.56%`) |
| **`T_A3`** | `3.7188` (`0.9167`) | `4.0` | `7/64` (`10.94%`) | `p = 0.9985` | `8/64` (`12.50%`) |
| **`D_A0`** | `2.2969` (`1.1503`) | `2.0` | `3/64` (`4.69%`) | `p = 1.0000` | `52/64` (`81.25%`) |

Inter-rater agreement across the `16` Core items: Fleiss' kappa on `#4` worst variant = `0.3202`, on `#1` best variant = `0.0640` (reflecting `gemini-2.5-flash` splitting best picks across `T_A3` `6/16`, `T_A0` `5/16`, `S_syn` `3/16`, `D_A0` `2/16`, whereas `claude-sonnet-4.6` picked `T_A0` `15/16`, `gpt-5.4-fast` `12/16`, and `llama-4-maverick` `9/16`).

**Paired Comparisons (`T_A0` vs. Comparators):**
Primary inference uses item-level means (`N = 16`, exact `2^16 = 65,536` sign-flip enumeration) to avoid pseudo-replication across raters; rating-level checks (`N = 64`, `seed = 20261115`, `100,000` MC sign-flips) are shown alongside:

| Contrast | Mean Diff | Item-Level (`N=16`) Wins / Losses / Ties | Item Sign `p` | Item Exact Perm `p` | Rating-Level (`N=64`) MC Perm `p` |
| :--- | ---: | :---: | ---: | ---: | ---: |
| `T_A0 - T_A3` | `+0.7969` | `16 / 0 / 0` | `3.052e-05` | **`3.052e-05`** | `1.000e-05` |
| `T_A0 - D_A0` | `+2.2188` | `15 / 1 / 0` | `0.000519` | **`6.104e-05`** | `1.000e-05` |
| `T_A0 - S_syn` | `+0.2188` | `11 / 5 / 0` | `0.2101` | **`0.2453`** (NS) | `0.0924` (NS) |
| `S_syn - T_A3` | `+0.5781` | `13 / 0 / 3` | `0.000244` | `0.000244` | `1.000e-05` |
| `S_syn - D_A0` | `+2.0000` | `15 / 1 / 0` | `0.000519` | `6.104e-05` | `1.000e-05` |
| `T_A3 - D_A0` | `+1.4219` | `14 / 1 / 1` | `0.000977` | `0.000366` | `1.000e-05` |

### 6.2 `M4_item` Negative Controls (`R9` & `R10`, Separated from Core)

Across `R9` and `R10` (`8` ratings total), `D_A0` was ranked `#4` worst **`8/8` (`100%`)** (`Fleiss kappa = 1.0`; `R9 mean = 1.500`, `R10 mean = 2.250`, combined `1.875`), confirming that raters reject direction-flipped controls. Meanwhile, **`S_syn`** scored highest (`mean = 4.875`, `6/8` best; `R9 = 4.75`, `R10 = 5.00`), followed by **`T_A0`** (`mean = 4.500`, `2/8` best; `R9 = 4.50`, `R10 = 4.50`) and **`T_A3`** (`mean = 3.750`, `0/8` best; `R9 = 3.75`, `R10 = 3.75`).

### 6.3 `M4_native_pair` (Native `A0` vs. Native `A3-1`, `16` Items x `4` Raters = `64` Judgments)

When raters compared each arm's independently generated canonical `translation_t` directly head-to-head without shared template scaffolding, **no significant preference emerged**:
- `A0` mean = **`3.2969`** (`SD = 1.0493`) vs. `A3-1` mean = **`3.2188`** (`SD = 1.0308`), `mean diff = +0.0781`.
- Rating-level (`N = 64`): `31` `A0` wins, `23` `A3-1` wins, `10` ties (`sign p = 0.3409`, MC perm `p = 0.7426`; Fleiss' kappa on preference `0.2338`).
- Item-level (`N = 16`): `10` `A0` mean wins, `6` `A3-1` mean wins, `0` ties (`sign p = 0.4545`, exact sign-flip `p = 0.8267`).
- Per rater (`A0` / `A3-1` / `tie`): `claude` `5/6/5`, `gpt` `10/5/1`, `gemini` `8/6/2`, `llama` `8/6/2`.

### 6.4 `M4_bundle` (`3` Order Permutations x `4` Raters = `12` Whole-System Ratings)

| System | Mean (SD) | Median | Mean Rank | `#1` Best (`12`) | `#4` Worst (`12`) | `perm_0` Mean | `perm_1` Mean | `perm_2` Mean |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`T_A0`** | **`3.5000` (`1.2432`)** | `4.0` | **`1.6667`** | **`5/12` (`41.67%`)** | **`0/12` (`0.00%`)** | `3.25` | `3.25` | `4.00` |
| **`S_syn`** | `3.3333` (`1.3027`) | `4.0` | `2.0833` | `4/12` (`33.33%`) | `0/12` (`0.00%`) | `3.25` | `2.50` | `4.25` |
| **`T_A3`** | `2.5833` (`0.9003`) | `2.5` | `2.9167` | `1/12` (`8.33%`) | `4/12` (`33.33%`) | `2.25` | `2.00` | `3.50` |
| **`D_A0`** | `2.1667` (`1.1934`) | `2.0` | `3.3333` | `2/12` (`16.67%`) | `8/12` (`66.67%`) | `2.25` | `2.75` | `1.50` |

Order stability across `perm_0`, `perm_1`, `perm_2` was weak (`Fleiss kappa` on `#1` best across permutations = `-0.2245`): `perm_2` rated all non-flipped systems substantially higher (`4.00`, `4.25`, `3.50`) and `D_A0` lower (`1.50`) than `perm_0` and `perm_1` (where `gemini-2.5-flash` ranked `D_A0` `#1` twice). At call level (`N = 12`), `T_A0 - T_A3 = +0.9167` (`7` wins, `0` losses, `5` ties, exact perm `p = 0.0156`, Holm-adjusted `0.125` NS) and `T_A0 - D_A0 = +1.3333` (`10` wins, `2` losses, exact perm `p = 0.0493`). At rater-averaged level (`N = 4`, where minimum two-sided exact sign-flip p-value is `2/16 = 0.125`), `T_A0 - T_A3` and `T_A0 - D_A0` both yield `p = 0.25` (`3` wins, `0` losses, `1` tie), and `T_A0 - S_syn` (`+0.1667`) is null (`p = 0.7266` call-level; `p = 0.75` rater-level).

---

## 7. Stage 6 (`M5`): Leak-Free Vocabulary-Free Discovery Convergence

Full table in [`m5_vocab_free_12.csv`](./outputs/m5_vocab_free_12.csv). With zero target words or target stems in prompts across `12` physical slots x `5` models (`60` primary proposals):
- **Exact Book `A0` Primary Matches:** **`4/60` (`6.67%`)**, concentrated on two slots:
  - `damping` (`A0`: `resonance`): **`3/5`** primary matches (`gpt-5.4-fast`, `gemini-2.5-flash`, `mistral-medium-3.5`), plus **`2/5`** alternate matches (`claude-sonnet-4.6` and `llama-4-maverick` proposed `amplification` with `resonance` in `alternate_candidates`), giving **`5/5` (`100%`)** recall within top candidates on `damping`.
  - `gravity` (`A0`: `Attraction`): **`1/5`** primary match (`claude-sonnet-4.6` -> `attraction`); `gemini-2.5-flash` also listed `affinity` (`S_syn`) as an alternate.
- **Exact `S_syn` Primary Matches:** `2/60` (`3.33%`), both on `friction` (`mistral-medium-3.5` and `llama-4-maverick` proposed `harmony`, while `claude-sonnet-4.6` and `gpt-5.4-fast` proposed `flow`).
- **Overall Modal Agreement:** Mean modal share across all `12` slots is **`0.3833`** (`23/60` modal-word votes): `damping` (`0.60`, `resonance`); `0.40` (`2/5`) on `mass` (`lightness`), `density` (`openness`), `volume` (`scope` tied with `presence`), `space` (`unity`), `time` (`eternity`), `force` (`influence`), `speed of light` (`instant knowing`), `gravity` (`levity`), and `friction` (`flow` tied with `harmony`); and `0.20` (`1/5`, all 5 models distinct) on `velocity` and `acceleration`.

---

## 8. Holm-Bonferroni Multiple-Testing Family

Step-down Holm-Bonferroni correction across the `12` pre-specified primary comparative hypotheses:

| Rank | Hypothesis Test | Raw `p` | Holm Adjusted `p` | `<= 0.05` | `<= 0.01` |
| ---: | :--- | ---: | ---: | :---: | :---: |
| 1 | `M4_item_Core_T_A0_best_gt_0_25_binom` (`41/64` vs. `0.25`) | `4.950e-11` | `5.940e-10` | Yes | Yes |
| 2 | `M4_item_Core_T_A0_vs_T_A3_item_perm` (`16/16` items) | `3.052e-05` | `0.000336` | Yes | Yes |
| 3 | `M4_item_Core_T_A0_vs_D_A0_item_perm` (`15/16` items) | `6.104e-05` | `0.000610` | Yes | Yes |
| 4 | `M2_Core_vs_Boundary_A0_fisher` (`16/28` vs. `0/12`) | `0.000899` | `0.008088` | Yes | Yes |
| 5 | `M4_bundle_T_A0_vs_T_A3_call_perm` (`12` bundle calls) | `0.015625` | `0.125000` | No | No |
| 6 | `M4_item_Core_T_A0_vs_S_syn_item_perm` (`11/16` items) | `0.245270` | `1.000000` | No | No |
| 7 | `M4_native_pair_A0_vs_A3_1_item_perm` (`10/16` items) | `0.826691` | `1.000000` | No | No |
| 8 | `M1_A0_vs_A3_1_cal17_mcnemar` (`12/17` vs. `12/17`) | `1.000000` | `1.000000` | No | No |
| 9 | `M2_LayerA_A0_vs_A3_1_mcnemar` (`12/16` vs. `13/16`) | `1.000000` | `1.000000` | No | No |
| 10 | `M3b_Opponent_A0_vs_A3_1_mcnemar` (`12/16` vs. `13/16`) | `1.000000` | `1.000000` | No | No |
| 11 | `M3c_Vertical_A0_vs_A3_1_mcnemar` (`3/16` vs. `2/16`) | `1.000000` | `1.000000` | No | No |
| 12 | `M3c_Horizontal_A0_vs_A3_1_rule1_fisher` (`0/81` vs. `0/81`) | `1.000000` | `1.000000` | No | No |

---

## 9. Misses, Nulls, Collisions, & Limitations

1. **Both Arms Fail Joint Formal Layer A (`passes_all = false`):** Neither `A0` (`4` collisions across `E001`, `E002`, `E023`, `E027`) nor `A3-1` (`5` collisions across `E001`, `E002`, `E023`, `E027`) achieved a clean formal Layer-A pass. Notably, rotational entries mapping `alpha -> Appreciation / Vibration` while `R -> Vibration` trigger `A3` self-quotient alerts (`Vibration * (Appreciation / Vibration)`), and integral/prime notations (`E023`, `E027`) leak prose/unparsed tokens into `reflected_formula`.
2. **Low Zero-Glossary Layer-B Vertical Coherence (`M3c_single`):** Without a partner glossary, `2/2` judges marked only `3/16` (`18.75%`) of `A0` and `2/16` (`12.50%`) of `A3-1` as both ordinary-English coherent *and* faithful to the physical law (`McNemar p = 1.0`). While `gpt-5.4-fast` found `14/16` `A0` statements readable ordinary English, it judged `12/16` structurally unfaithful to the target equation when denied the vocabulary dictionary.
3. **`M4_native_pair` Null vs. `M4_item` Advantage:** When evaluating independently generated canonical translations head-to-head (`M4_native_pair`), raters showed **no significant preference** for `A0` over `A3-1` (`3.2969` vs. `3.2188`, `p = 0.8267` item-level). Thus, the strong `T_A0 > T_A3` effect observed in `M4_item` (`+0.7969`, `p = 3.052e-05`) holds specifically when sentence templates are held constant and only `{Slot}` vocabulary varies (alongside `S_syn` and `D_A0` anchors); independent generation in `A3-1` partially masked vocabulary awkwardness through different sentence framing and canonical model switches (`7/16` items selected a different canonical model between `A0` and `A3-1`).
4. **`T_A0` Does Not Significantly Outperform `S_syn`:** In both `M4_item` (`+0.2188`, `p = 0.2453`) and `M4_bundle` (`+0.1667`, `p = 0.7266`), the single-sense Ch. 16 synonym projection `S_syn` performed comparably to `T_A0` (and slightly higher on `R9`/`R10` synthetic controls, `4.875` vs. `4.500`). The ordinary-English advantage therefore tracks the semantic domain of Ch. 16 concepts rather than unique lexical superiority of exact Book spellings over close synonyms.
5. **Calibration Misses (`M1`):** Both arms scored `12/16` (`75.00%`) on `K01..K16`, systematically inverting `K05` (time dilation) and `K06` (length contraction) (`4/5` and `4/5`/`3/5` `invert`) and splitting `3/5` on `K16` (`F = ma`), while unanimously rejecting `K17` (Boyle's law) as `"no partner"` (`5/5`) under `UNMAPPED_BLOCKLIST_V2`.
6. **Whole-System Bundle Sensitivity (`M4_bundle`) & Small Rater Count:** With `4` raters and `3` permutations, `M4_bundle` showed strong order sensitivity (`Fleiss kappa = -0.2245` across permutations; `gemini-2.5-flash` favored `D_A0` in `perm_0`/`perm_1` before switching to `T_A0` in `perm_2`), and the call-level `T_A0 - T_A3` difference (`p = 0.0156`) did not survive Holm-Bonferroni correction (`adjusted p = 0.125`) or rater-averaged aggregation (`N = 4`, `p = 0.25`).
7. **Low Exact-Lexical Discovery in `M5` & Schema Errors:** Unassisted vocabulary-free LLMs recovered exact Book `A0` terms only `4/60` (`6.67%`) times (`damping -> resonance` `3/5`, `gravity -> attraction` `1/5`), with `0/5` exact primary matches across the remaining `10` slots (`mass`, `density`, `volume`, `space`, `time`, `velocity`, `acceleration`, `force`, `speed of light`, `friction`). All `7` unrecovered schema validation failures occurred on `llama-4-maverick`, and one `Core` item (`E037`) overlapped the earlier extension-test set.

---

## Follow-Up Deep-v3 Investigation

A pre-registered follow-up investigation ([`deep_v3/PREREGISTRATION_V3.md`](./deep_v3/PREREGISTRATION_V3.md), full analysis in [`deep_v3/RESULTS_DEEP_V3.md`](./deep_v3/RESULTS_DEEP_V3.md)) ran **485** additional live zero-glossary tasks (**657** total calls) plus deterministic Layer-A v3 auditing across four diagnostic pillars (`D1`–`D4`):
- **Multi-Job Web & Book Passage Discrimination (`D1a`, `D1b`, `D3b`):** Under three simultaneous structural/Cloze roles (`D1a`, `N = 14`), 4-criteria boolean truth tables (`D1b`, `N = 14`), and 12 masked verbatim-derived Book excerpts (`D3b`, `N = 12`), `A0` significantly outperformed both Ch. 16 synonyms (`S_syn`) and challengers (`W_Chal`) after Holm-Bonferroni correction (`K = 6`, all Holm-adjusted `p <= 0.00406`), though literal `c1` rejections on `4` slots (`W01, W02, W07, W10`) prevented a complete 14-slot CSP solution in `D1b` alone.
- **Crossing Boundary Protocol (`D2a` & `D2b`):** Adding `pressure -> felt gap` cleanly separated `Mechanical_Crossing` (`5/7` strict, `7/7` valid-voter/raw-JSON) from `Non_Crossing_Boundary` (`0/13`, unanimous `5/5` `no_partner`; strict Fisher `p = 0.001354`, Holm-adjusted `p = 0.004063`) and flipped `K17` (Boyle's law) to `4/5` `"keep"`, at the cost of lowering `D2a` `K01..K16` accuracy (`12/16 -> 7/16`).
- **Chapter 2 Narrative Teaching (`D3a`):** Supplying strictly Book Ch. 2 prose without Ch. 16's boundary clarifications reduced `K01..K17` consensus accuracy from `12/17` to `8/17` (`McNemar p = 0.125` NS; pooled `62/85 -> 48/85`, `p = 0.009355`), inducing `"invert"` rulings on `K16` (`5/5`), `K06` (`5/5`), and `K05` (`4/5`).
- **Deterministic Layer-A v3 (`D4`):** Normalizing calculus phrases, prime-bearing subscripts, and rational monomial exponents cleared all `4` `A0` false positives (`12/16 -> 16/16`, `passes_all = true`) while leaving `A3-1` failing (`15/16`, `3` collisions, `passes_all = false`).
