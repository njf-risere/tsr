# Run 1: all nine domains, generation stage complete; opponent, decoys and judges pending

5–6 November 2026. Criteria v1, lexicon R1 v1. Calibration 22/22 reproduced from records alone.

## Status

The run stopped after the generation stage when the account's credits ran out. What exists is complete and reproducible; what is missing is staged (prompts written, keys saved) and resumes without regenerating anything.

| Stage | State |
| --- | --- |
| Generators | **4 of 5 complete** across all 7 batches, 91 relations each (88 new + 3 hidden calibration): Astra (OpenAI), Fable (Anthropic), Argon (Google), Kimi K3 (open-weights). Grok 4.7 produced only its canary before the credit stop. 364 per-record outputs ingested; every one in `raw/<model>/`. |
| Canary | 5 of 5 models clean: no TSR vocabulary leaked into the fictional-framework output; none reported knowing the framework. |
| Procedure + agreement gate | Done. See below. |
| Layer A (formal) | Done on the 75 provisional candidates: no collision. |
| Opponent | **Pending.** `prompts/opponent-{A..G}.md` written (75 rows). |
| Decoys | **Pending.** 225 statements (75 × T/D/W) in 4 blind lists, `prompts/rater-L{1..4}.md`; key in `decoys.json`. |
| Layer B (judges) | **Pending.** Set-level screening prompt over 91 sentences (75 new + 16 book) in `prompts/judge-screen.md`; key in `judge-screen-key.json`. Pairwise confirmation follows screening. |
| Layer C | Book text not available in the sandbox; will run on the candidates Layer B produces. |

Nothing below is a result about collisions. It is a result about whether the closed rule and five blind models agree on what the rule says, which is the precondition for collision testing.

## Agreement

- 91 rows. 4/4 agreement on shape: **84**. Majority matches the procedure: **80**.
- The three hidden calibration items landed where the book did, blind: damping 4/4 turns around; friction 4/4 turns around; interference 4/4 turns around. Phase 3's acceptance criterion is met for damping.
- **75 rows are provisional candidates**: the procedure forced them, all four live generators agreed on the shape, and at least one agreeing generator stated the reflection in frozen words with no NEW word, no numeral and no physical word on the nonphysical side. 13 turn around, 62 keep. They await the opponent and the decoy margin before they are forced rows.
- The 13 that turn: Hooke, gravitational potential energy (cost reading), resonance width, damping, friction, Fourier conduction, Joule heating, latent heat (cost reading), standing waves, interference, Lenz / self-inductance, Ohm (cost reading), decoherence. Exactly the procedure's list.
- 16 rows stay open: 15 because the procedure did not force them (open joints), 1 because the generators split 2/2 (Maxwell-Boltzmann width).

## What the generators did on the open joints (information for the author, not a ruling)

| Joint | Rows | Generators |
| --- | --- | --- |
| reverse_cost (difficulty falls with resistance) | Reynolds, terminal velocity, bound-state quantization, Yukawa range | **4/4 turned every one**, counting the resistance that is present and ignoring its direction. |
| heat_capacity_resistance | heat capacity (cost) | 4/4 turned it: all four treated thermal inertia as resistance. |
| separation_call | Coulomb 3/4 turned; Newtonian gravitation 3/4 turned; diffraction 4/4 turned; asymptotic freedom 4/4 turned | The models read an inverse-square falloff or an aperture as a separation made by distance. |
| refractive_index / barrier / string tension | TIR 3/4, Fresnel 3/4, tunneling 3/4, confinement 3/4 turned | The majority treats the medium, the barrier and the flux tube as resistance. |
| gravity_call | gravitational time dilation 4/4 keeps; torque 4/4 keeps | Agrees with the book's reading A and with the definition reading of torque. |

If the author closes these joints the way the models leaned (thermal inertia, media, barriers and tensions carry resistance; separation counts without a named difficulty; a cost that falls with resistance still "depends on resistance"), 14 more rows become forced and all 14 turn around. That is a change to R1 and to C0, made once, that reruns everything. The models' lean is recorded here because it is evidence about where the rule is unclear, not because it settles anything.

## Layer A on the 75 provisional candidates

- A1 mirror-twice: no new typed clash.
- A2 composition: every candidate with a fully mapped formula composes with the word map; no generator's consensus formula is a rewrite.
- A3 sign graph: 12 monotone claims supported by ≥ 2 agreeing generators, consistent with each other and with the book's four claims.
- A4 parity at the formula level: no failure. Reading-level non-compositions (Ohm cost from Ohm definition; Lenz from Faraday; Joule from Ohm; latent heat cost from its definition; gravitational PE from work) are informational, as the book's own row 8 is.

## Conflicts the generators themselves reported (two or more models)

Not scored; recorded because the extension-test key says a conflict flagged by two AIs is worth a look.

- **Numerals that will not leave the formula**: both uncertainty relations (ħ ÷ 2), zero-point energy (½), bound-state quantization (n², π², 2), velocity addition (1 + …). Under C1 the formula is not rewritten; under C5 numerals do not cross. The two criteria meet here. Current handling: the consensus formula is the word-map image with the numeral left in, and the row's reading is what crosses. Proposed criterion for the author: pure numbers in a kept formula are structure, not units, and stay; or they are units and the formula is marked "not reflected; reading only".
- **Superposition against "it isn't add either"**: Fable and Argon both flagged the sum. The consensus sentence (Argon) already says "culminate together" rather than "add". Layer B will test it against the book's interference ruling; Layer C decides whether Ch 16's "at a point" dissolves it.
- **Physical frequency**: phase velocity, group velocity, Doppler. All four models kept physical frequency unmapped and refused the pun. The trap held.
- **Energy-momentum relation**: Fable notes that the reflected relation makes C² × M = E hold only when momentum is zero. Argon flags the sum. This is a real question for Ch 17 (Momentum as M × C through time) and goes to Layer B against the book's E = mc² row.
- **Velocity addition keeps a limit on the limitless side**: Astra, Fable, Argon. The reflected sentence says rise per Expansion never passes the Current. The book says the same thing about the Current (row 9 turned, but as "nothing falls short", not "nothing exceeds"). Layer B pair: velocity addition × row 9.

## Deviations from the spec in this run

1. Models ran as blind agent sessions, not API calls: no temperature control, so the temperature-0 / 0.7 two-pass was not done. Each session saw one batch of 10–16 relations (the spec says one relation per prompt; round 1 also batched).
2. Amendment 1 (`prompts/amendment-1.md`) was issued to every generator session after two models read `shape: no partner` as "any term unmapped". It clarifies the field and does not change the rule. All four complete generators rewrote under it; the pre-amendment files were overwritten (the pre-amendment shape distribution is in the session log: Astra and Argon ~100% "no partner", Kimi already keeps/turns).
3. Four generators, not five; the agreement gate therefore required 4/4 instead of 4/5. Grok's canary is clean; its batches are the first thing to run on resume.
4. Layer B is staged as set-level screening then pairwise confirmation (two judges), not all-pairs judging, to fit the budget. Any pair flagged by either judge in screening goes to both judges in isolation.
5. Domains ran in parallel, not sequentially; no joint was closed between domains because closing joints is the author's call, and the procedure's open joints were known before any model ran.

## Hypothesis the run supports so far

Neither, yet. Collision testing needs forced rows, and forced rows need the opponent and the decoy margin. What can be said: the closed rule and four independent models agree on the shape of 84 of 91 relations, the three hidden book rulings were reproduced blind, and nothing formal collided among the 75 candidates. Where the models and the procedure disagree, the disagreement sits exactly on the joints the procedure had already marked open, and the models lean the same way on each.

## To resume

```
# 1. Grok, 7 batches + canary already done:   prompts/generator-{A..G}.md -> raw/grok/batch-X.json ; then ingest
# 2. Opponent (DeepSeek or another non-generator vendor): prompts/opponent-{A..G}.md -> raw/opponent/batch-X.json ; ingest ; stage_rows(with_opponent=True)
# 3. Raters (4 fresh models): prompts/rater-L{1..4}.md -> raw/raters/<model>-L1.json ; stage_decoy_score
# 4. Judges (2 vendors): prompts/judge-screen.md -> raw/judges/<model>-screen.json ; stage_judge_pair_prompts ; prompts/judge-pairs.md -> raw/judges/<model>-pairs.json
# 5. stage_finalize(book_path=<paperback.txt>)
```
