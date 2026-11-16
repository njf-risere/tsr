# TSR Automated Non-Cipher Evaluation Preregistration (v2)

**Branch:** `feat/automated-llm-harness`
**Scope:** [`harness/`](./) (pure Python 3.12+ standard library; zero modifications to `proof/` or `.github/`).
**Seeds:** Sampling / Shuffling Seed = `20261115`; Category-Preserving Derangement Seed = `101`.

---

## 1. Rationale for v2 Rebuild (Replacing `archive/cipher-harness-v1-724fab2`)

The earlier v1 cipher harness (`archive/cipher-harness-v1-724fab2`, including the dropped `part4_etymology/` Wiktionary module) had structural defects that prevented an unambiguous non-circular test of whether Book Ch. 2 & Ch. 16 naming reflects physical relations into coherent ordinary-English laws:

1. **Inline Glossary Leakage vs. Plain-English Evaluation:** v1 exposed `glossary_senses` prose definitions directly to Layer-B judges and rating evaluators, conflating dictionary memorization/lookup with ordinary-English semantic coherence. In v2, **zero inline glossary definitions appear in any prompt**: generators receive only the neutral `CONCEPTUAL_AXIS_PLAIN`, `Rule R`, and their arm's `Partner Lookup Table`, while Layer-B judges (`M3c`) and quality raters (`M4`) receive ONLY `CONCEPTUAL_AXIS_PLAIN` (which itself contains zero target words or morphological stems from `A0`, `A3-1`, or `S_syn`) and judge ordinary English.
2. **Calibration Giveaways & Dataset Hygiene:** v1 embedded explicit calibration equations inside `Rule R`, injected `"gravitational redshift"` into `K12` (whereas Ch. 16 #12 concerns gravitational wells and gravitational lensing), and risked thermodynamic boundary leakage from `K17` (Boyle's law). v2 removes all leaked calibration formulas from `Rule R`, restores `K12` to `"Gravitational wells and gravitational lensing of light around massive bodies"`, tests `K01..K17` unassisted in `M1` (`Rule R` + `Partner Lookup Table` only), and restricts worked calibration examples in `M2` strictly to `K01..K16`.
3. **Nomenclature & Permutation Defects:** v1 leaked `"Movement M"` dangling suffix artifacts, failed to permute `Vibration²` inside rotational/area compounds on `A3-1`, and omitted explicit `A0` partners for rotational mechanics and inertial frames in unified symmetric propagation. v2 renders `"Movement"` cleanly throughout, propagates `seed=101` symmetrically across `MIRROR`, `EXTENDED_PARTNERS`, rotational (`moment of inertia`, `angular momentum`, `angular velocity`, `angular acceleration`, `torque`), spacetime (`Vibration-Expansion`), and frame (`inertial frame/observer`) partners, and strips subscripts, primes, bars, vector arrows, and parenthetical qualifiers before `A1` lookup using `(?<![A-Za-z])...(?![A-Za-z])` boundaries instead of `\b`.
4. **Selection, Joint Audits, & Quarantine:** v2 picks the canonical consensus generator *after* running per-item Layer-A checks (`A1`/`A2`/`A3`) among agreeing voters (`>= 4/5`), runs Layer A jointly across all consensus items (`A1` cross-item bijection, `A2` composition, `A3` sign preservation, `A4` signed cycle consistency), excludes Adversarial Opponent (`M3b`) outputs from Layer B (`M3c`) and Stage 5 (`M4`), and replaces token heuristics with full cross-item shared-slot horizontal Layer-B pairs (`<= 6`/batch) plus unbatched `gemini-2.5-flash` Rule-1 adjudication on any `2/2` contradiction pair.
5. **Dropping Wiktionary (`part4_etymology`):** Lexicon polysemy counts from Wiktionary did not evaluate structural reflection validity and are intentionally omitted in v2; lexical discoverability is instead measured directly by leak-free Stage 6 (`M5`).

---

## 2. Locked Model Roster & Runtime Parameters

- **Endpoint & Client:** [`providers.py`](./providers.py) (`CheaperInferenceClient` against `api.cheaperinference.com/v1/chat/completions`, `timeout_sec = 240`, `temperature = 0.0`, `max_tokens` omitted from JSON payload so reasoning/completion tokens are never clipped, `top_p = 1.0` when `vendor == "mistral"` and `temperature == 0.0`, up to `3` JSON/schema validation retries; if all `3` attempts fail validation, a non-crashing `status = "schema_error"` record is persisted so remaining workers and stages continue cleanly and exact per-stage `schema_error_counts` are reported).
- **Generators (5):**
  1. `claude-sonnet-4.6` (`anthropic`)
  2. `gpt-5.4-fast` (`openai`)
  3. `gemini-2.5-flash` (`google`)
  4. `mistral-medium-3.5` (`mistral`)
  5. `llama-4-maverick` (`meta`)
- **Adversarial Opponent (1, Stage 3 `M3b`):** `deepseek-v4.1-flash-fast` (`deepseek`)
- **Zero-Glossary Layer-B Judges (2, Stage 4 `M3c`):** `claude-sonnet-4.6` (`anthropic`), `gpt-5.4-fast` (`openai`)
- **Stage 4 Rule-1 Arbiter (1, unbatched on `2/2` contradictions):** `gemini-2.5-flash` (`google`)
- **Zero-Glossary Plain-English Raters (4, Stage 5 `M4`):** `claude-sonnet-4.6`, `gpt-5.4-fast`, `gemini-2.5-flash`, `llama-4-maverick`

---

## 3. Experimental Arms & Projection Systems

Defined and self-tested in [`arms_v2.py`](./arms_v2.py):

- **`A0` (TSR Non-Cipher Partner Mirror):** Maps physical concepts (`mass -> Movement`, `density -> Desire`, `volume -> Vibrance`, `space -> Vibration`, `time -> Expansion`, `velocity -> rise per Expansion`, `acceleration -> Appreciation`, `force -> Frequency`, `speed of light -> Current`, `energy -> conscious energy`, `gravity -> Attraction`, `friction/damping -> resonance`, `spacetime -> Vibration-Expansion`, rotational & frame partners) directly to Book Ch. 2 & Ch. 16 terms without `"Movement M"`.
- **`A3-1` (Typed Category-Preserving Derangement, `seed = 101`):** 5-pool typed derangement (`quantity_pool` seed `101`, `phenom_pool` seed `118`, `dir_pool` seed `132`, `prop_pool` seed `148`, `meta_pool` seed `165` over `Vibrational Reality`, `Collective Reality`, `emotional evidence`, `realization`) matching `arms/a3_shuffled.py` (with clean `"Movement"`), propagated symmetrically across every mirror, extended, rotational, spacetime, and frame entry and all `K01..K16` calibration examples so every one of the `30/30` canonical slots has a strict non-identity bijective image.
- **`S_syn` (`SYNONYM_MAP_CH16` Projection for `M4`):** Deterministic 1-to-1 Book Ch. 16 single-sense English synonym substitution across all `30` canonical slots (`Movement -> responsiveness`, `Appreciation -> gratitude`, `Frequency -> urgency`, `Vibration -> pitch`, `Expansion -> growth`, `Desire -> longing`, `Vibrance -> capacity`, `Current -> stream`, `Attraction -> affinity`, `resonance -> harmony`, `conscious energy -> awareness`, `rise per Expansion -> pace`, `Vibration-Expansion -> pitch-growth`, `Idle -> stillness`, `Reflected -> echo`, `Tune -> focus`, `Vortex -> whirlpool`, `Convergence -> gathering`, `Intuition -> hunch`, `imagination -> imagery`, plus `collection -> absorption`, `receptive -> welcoming`, `limitless -> infinite`, `Out For -> outward-seeking`, `In To -> inward-arriving`, `Future -> onwardness`, `realization -> fulfillment`, `Vibrational Reality -> pitch reality`, `Collective Reality -> shared reality`, `emotional evidence -> felt evidence`). Rendered directly from each verified `A0` `{Slot}` `translation_template` (case-insensitive `{Slot}` lookup).
- **`D_A0` (Directional Polarity Reversal Control for `M4`):** Coherent statement reversing the causal/relational direction of `T_A0` while keeping the exact same `A0` target vocabulary set without inline contradictory appositives.

---

## 4. Information Isolation Matrix (Visible Inputs vs. Withheld Inputs)

Every stage enforces automated prompt isolation checks (`assert_prompt_isolation`, `assert_zero_target_stem_leak`, and `_check_zero_leaked_calibration_formulas`) in [`arms_v2.py`](./arms_v2.py):

| Stage & Metric | Visible Inputs Sent in Prompt | Withheld Inputs (Quarantined) |
| :--- | :--- | :--- |
| **Stage 1 (`M1`: Cal `K01..K17`)** | `CONCEPTUAL_AXIS_PLAIN`, arm `Partner Lookup Table`, `RULE_R_V2`, 13-key JSON schema, `(item_id, description, equation_latex)` | Worked `K01..K16` solutions, leaked calibration formulas, `formal_row_name`, `formal_source`, `expected_book_ruling`, `provenance`, `costs_count`, glossary definitions, other arm |
| **Stage 2 (`M2`: Held-out `E001..E040`)** | `CONCEPTUAL_AXIS_PLAIN`, arm `Partner Lookup Table`, `RULE_R_V2`, `K01..K16` rendered in the arm's own vocabulary, 13-key JSON schema, `(item_id, description, equation_latex)` | `K17` (Boyle's law), `stratum` (`Core`/`Boundary`), `overlaps_legacy_extension_test`, `volume`/`chapter`/`chapter_title`/`source_url`, glossary definitions, other arm |
| **Stage 3 (`M3b`: Opponent)** | `CONCEPTUAL_AXIS_PLAIN`, arm `Partner Lookup Table`, `RULE_R_V2`, `(item_id, description, equation_latex)`, canonical consensus item fields | `stratum`, `overlaps_legacy_extension_test`, glossary definitions, `S_syn`/`D_A0`, other generators' dissenting drafts |
| **Stage 4a (`M3c_single`: Vertical)** | `CONCEPTUAL_AXIS_PLAIN` (zero target stems), anonymized `eval_id`, `(description, equation_latex, translation_t)` | Opponent (`M3b`) critique/verdict, `Partner Lookup Table`, glossary definitions, arm labels (`A0`/`A3-1`), `stratum` |
| **Stage 4b (`M3c_pairs`: Horizontal, `<= 6`/batch)** | `CONCEPTUAL_AXIS_PLAIN` (zero target stems), opaque `pair_id`, `shared_words`, `(statement_a, statement_b)` | Physics equations & descriptions, Opponent (`M3b`) output, `Partner Lookup Table`, glossary definitions, arm labels (`A0`/`A3-1`) |
| **Stage 4c (`M3c_situation_match`: Rule 1)** | Unbatched pair `pair_id`, `shared_words`, `(statement_a, statement_b)` on `2/2` contradiction pairs | Physics equations & descriptions, prior Layer-B judge verdicts, Opponent output, `Partner Lookup Table`, glossary definitions, arm labels |
| **Stage 5a (`M4_item`: 4-way, `<= 5`/batch)** | `CONCEPTUAL_AXIS_PLAIN` (zero target stems), `item_id` (`A0 Core` consensus + `R9`, `R10`), deterministically shuffled `Candidate 1..4` (`T_A0`, `T_A3`, `S_syn`, `D_A0`) | Variant labels (`T_A0`/`T_A3`/`S_syn`/`D_A0`), physics equations & descriptions, `Partner Lookup Table`, glossary definitions, Opponent output, `stratum` |
| **Stage 5b (`M4_native_pair`, `<= 6`/batch)** | `CONCEPTUAL_AXIS_PLAIN` (zero target stems), `item_id` (items reaching `keep`/`invert` consensus in both `A0` & `A3-1`), shuffled `Candidate A / Candidate B` | Arm IDs (`A0`/`A3-1`), physics equations & descriptions, `Partner Lookup Table`, glossary definitions, Opponent output |
| **Stage 5c (`M4_bundle`: 3 perms x 4 raters)** | `CONCEPTUAL_AXIS_PLAIN` (zero target stems), all `M4_item` statements grouped as unlabeled `System 1..4` | System labels (`T_A0`/`T_A3`/`S_syn`/`D_A0`), physics equations & descriptions, `Partner Lookup Table`, glossary definitions, Opponent output |
| **Stage 6 (`M5`: Word Convergence, 12 x 5)** | `CONCEPTUAL_AXIS_PLAIN` (zero target stems) + single physical slot name (`mass`, `density`, `volume`, `space`, `time`, `velocity`, `acceleration`, `force`, `speed of light`, `gravity`, `friction`, `damping`) | **Zero** target words or stems from `A0`, `A3-1`, or `S_syn` anywhere in system or user prompt; no `Rule R`, no `Partner Lookup Table`, no physics equations |

---

## 5. Evaluation Metrics & Decision Rules (`M1`–`M5`)

Executed end-to-end by [`run_tsr_harness.py`](./run_tsr_harness.py):

- **`M1` (Zero-Shot Calibration Accuracy on `K01..K17`):** Exact ruling agreement against `expected_book_ruling` per model and per `>= 4/5` consensus item for both `A0` and `A3-1`, scored strictly post-generation.
- **`M2` & Layer A (Held-Out `E001..E040` Consensus & Formal Graph Integrity):**
  - Items reach consensus when `>= 4/5` generators agree on `ruling`.
  - For consensus `keep`/`invert` items, each agreeing voter undergoes per-item Layer-A verification (`run_layer_a_item_check`), and the canonical generator is picked in `GENERATORS` order **preferring Layer-A passers first** (falling back only if 0 pass).
  - Joint cross-item `run_layer_a_v2` evaluates all consensus `keep`/`invert` items within each arm jointly across `A1` (typed 1-to-1 bijection after subscript/prime/bar/parenthetical normalization, accepting explicit stripped Rule-R constants in `variable_map`), `A2` (formula token composition), `A3` (within-item numerator/denominator & sign preservation via recursive-descent AST parser supporting `\frac{A}{B} * C`, chained `=`, distributed vs. factored forms, and balanced subscripts), and `A4` (signed cycle & opposing-parallel-edge consistency).
- **`M3b` & `M3c` (Adversarial Stress-Test & Zero-Glossary Layer B):**
  - `M3b` attacks canonical `keep`/`invert` items adversarially (quarantined from Stage 4 & Stage 5).
  - `M3c` tests vertical coherence (`M3c_single`) and all shared-slot horizontal pairs (`M3c_pairs`, `<= 6`/call) with two zero-glossary judges; only `2/2` contradiction pairs confirmed by unbatched `gemini-2.5-flash` Rule-1 adjudication (`same_situation == true`) count as horizontal collisions.
- **`M4` (Zero-Glossary Plain-English Quality & Whole-System Rating):**
  - `M4_item` rates `(T_A0, T_A3, S_syn, D_A0)` 4-way quadruples across `A0 Core` consensus items plus controls `R9` and `R10`.
  - `M4_native_pair` tests native `A0` vs. native `A3-1` statements directly where both arms reached `keep`/`invert` consensus.
  - `M4_bundle` tests multi-law whole-system coherence across 3 order permutations per rater (`12` calls), enforcing strict consistency between `ranking`, `best_system == ranking[0]`, `worst_system == ranking[-1]`, and monotonically non-increasing `scores`.
- **`M5` (Leak-Free Vocabulary-Free Discovery Convergence):** Measures spontaneous lexical convergence across 5 independent LLMs on 12 base physical slots without any target vocabulary or stems in the prompts.

---

## 6. Frozen OpenStax Sampling Artifacts & Verification Manifest

Prepared and verified offline by [`prepare_openstax_sample.py`](./openstax/prepare_openstax_sample.py) (`openstax/osbooks-university-physics-bundle` commit `2300d5b8ca2571dacc6ec25ebef56ba8d49000a2`, `seed = 20261115`, `28 Core + 12 Boundary = 40` held-out equations + `17` calibration equations):

- [`heldout_equations_40.json`](./openstax/heldout_equations_40.json): `sha256: 10ecc2de0861821fd741e8f5f059b291f73cb310766afcc603cd7ffcfb6ebbdf` (byte-for-byte identical to `archive/cipher-harness-v1-724fab2`)
- [`calibration_equations_17.json`](./openstax/calibration_equations_17.json): `sha256: 2f18b33f834d54a820458dbe94050834ac3d5fc13a6e4250fc037652a31bc4a2` (clean `K12` restored to `"Gravitational wells and gravitational lensing of light around massive bodies"`)
- [`sample_manifest.json`](./openstax/sample_manifest.json): `sha256: 2ca80da951dca717095b2bafa8a95dcfd222334916e8833555332590307ecc3b`
- [`openstax_fetch_manifest.json`](./openstax/openstax_fetch_manifest.json): `sha256: a6892bf769f58a2929d6b4c4d225d1afc41fc1acb16dd8a521c47d78f82acef8`
- [`openstax_key_equations_raw.csv`](./openstax/openstax_key_equations_raw.csv): `sha256: 0cf6ee7c9ca09b0f2653f6253308d7f6532436f2f27cc5f4f4fa38fa4399db2d`
- [`exclusion_log.csv`](./openstax/exclusion_log.csv): `sha256: 83a9cef425774925e56b61a6b11fe86ed362647ab6b8786b14b4db1c1a44faad`
