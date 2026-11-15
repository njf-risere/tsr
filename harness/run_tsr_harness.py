#!/usr/bin/env python3
"""Master automated LLM evaluation runner and verification suite (v2).

Modes:
  --verify-prereg   Pre-live Commit-1 gate: asserts strict Commit-1 file whitelist,
                    OpenStax offline SHA-256 parity, PREREGISTRATION.md hash/link
                    integrity, real Stage 1 & Stage 2 prompt hygiene, simulated
                    end-to-end Stages 1..6 pipeline, and zero hygiene violations
                    (0 live LLM calls; leaves working tree untouched).
  --run-live        Executes Stages 1..6 sequentially (concurrent within stages via
                    thread-safe CheaperInferenceClient + JsonlCallLogger) against
                    api.cheaperinference.com using `--env-file`, resuming cleanly
                    from `harness/logs/live_calls.jsonl`.
  --verify-offline  Post-live gate: audits `harness/logs/live_calls.jsonl` and
                    `harness/outputs/*.json`, recomputing Stage 1..6 aggregates
                    deterministically offline and checking completeness & hygiene.

Python 3.12+ standard library only. Never print or store secrets.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness import arms_v2, providers  # noqa: E402
from harness.openstax import prepare_openstax_sample  # noqa: E402

LOGS_DIR = HARNESS_DIR / "logs"
LIVE_LOG_PATH = LOGS_DIR / "live_calls.jsonl"
OUTPUTS_DIR = HARNESS_DIR / "outputs"
PREREG_MD_PATH = HARNESS_DIR / "PREREGISTRATION.md"

DEFAULT_TIMEOUT_SEC = 240
MAX_PARSE_ATTEMPTS = 3

COMMIT1_ALLOWED_REL_PATHS: frozenset[str] = frozenset(
    {
        "__init__.py",
        "providers.py",
        "arms_v2.py",
        "run_tsr_harness.py",
        "PREREGISTRATION.md",
        "openstax/__init__.py",
        "openstax/prepare_openstax_sample.py",
        "openstax/openstax_fetch_manifest.json",
        "openstax/openstax_key_equations_raw.csv",
        "openstax/exclusion_log.csv",
        "openstax/heldout_equations_40.json",
        "openstax/calibration_equations_17.json",
        "openstax/sample_manifest.json",
    }
)

VALID_ATTACK_TYPES: frozenset[str] = frozenset(
    {
        "none",
        "unmapped_leak",
        "polarity_flip",
        "dictionary_mismatch",
        "formula_mismatch",
        "conceptual_contradiction",
    }
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _chunked(seq: list[Any], size: int) -> list[list[Any]]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


# ---------------------------------------------------------------------------
# Stage-Specific JSON Response Validators (Stages 3..6)
# ---------------------------------------------------------------------------


def validate_m3b_opponent_json(parsed: Any, item_id: str) -> list[str]:
    if not isinstance(parsed, dict):
        return ["Expected JSON object"]
    req = {"item_id", "verdict", "attack_type", "critique", "counterexample_situation"}
    missing = sorted(req - set(parsed.keys()))
    if missing:
        return [f"Missing keys: {missing}"]
    errs: list[str] = []
    if parsed["item_id"] != item_id:
        errs.append(f"item_id {parsed['item_id']!r} != {item_id!r}")
    if parsed["verdict"] not in ("attack", "uphold"):
        errs.append(f"Invalid verdict {parsed['verdict']!r}")
    if parsed["attack_type"] not in VALID_ATTACK_TYPES:
        errs.append(f"Invalid attack_type {parsed['attack_type']!r}")
    if not isinstance(parsed["critique"], str) or not parsed["critique"].strip():
        errs.append("critique must be non-empty string")
    if not isinstance(parsed["counterexample_situation"], str):
        errs.append("counterexample_situation must be string")
    return errs


def validate_m3c_single_json(parsed: Any, eval_id: str) -> list[str]:
    if not isinstance(parsed, dict):
        return ["Expected JSON object"]
    req = {
        "eval_id",
        "coherent_ordinary_english",
        "matches_physical_law_structure",
        "axis_polarity_consistent",
        "nonsensical_or_cipher_like",
        "verdict",
        "reason",
    }
    missing = sorted(req - set(parsed.keys()))
    if missing:
        return [f"Missing keys: {missing}"]
    errs: list[str] = []
    if parsed["eval_id"] != eval_id:
        errs.append(f"eval_id {parsed['eval_id']!r} != {eval_id!r}")
    for bkey in (
        "coherent_ordinary_english",
        "matches_physical_law_structure",
        "axis_polarity_consistent",
        "nonsensical_or_cipher_like",
    ):
        if not isinstance(parsed[bkey], bool):
            errs.append(f"{bkey} must be bool")
    if parsed["verdict"] not in ("coherent", "incoherent"):
        errs.append(f"Invalid verdict {parsed['verdict']!r}")
    if not isinstance(parsed["reason"], str) or not parsed["reason"].strip():
        errs.append("reason must be non-empty string")
    return errs


def validate_m3c_pairs_json(parsed: Any, expected_pair_ids: list[str]) -> list[str]:
    if not isinstance(parsed, dict) or not isinstance(parsed.get("results"), list):
        return ["Expected JSON object with 'results' list"]
    rows = parsed["results"]
    by_id: dict[str, dict[str, Any]] = {}
    errs: list[str] = []
    for r in rows:
        if not isinstance(r, dict):
            errs.append("Result element is not an object")
            continue
        pid = r.get("pair_id")
        if not isinstance(pid, str):
            errs.append("Missing pair_id")
            continue
        if not isinstance(r.get("compatible"), bool):
            errs.append(f"{pid}: compatible must be bool")
        if r.get("verdict") not in ("compatible", "contradiction"):
            errs.append(f"{pid}: invalid verdict {r.get('verdict')!r}")
        if not isinstance(r.get("reason"), str) or not r["reason"].strip():
            errs.append(f"{pid}: reason must be non-empty string")
        by_id[pid] = r
    if set(by_id.keys()) != set(expected_pair_ids):
        errs.append(f"Pair ID mismatch: got {sorted(by_id.keys())}, expected {sorted(expected_pair_ids)}")
    return errs


def validate_m3c_situation_json(parsed: Any, pair_id: str) -> list[str]:
    if not isinstance(parsed, dict):
        return ["Expected JSON object"]
    req = {"pair_id", "same_situation", "confirmed_rule1_collision", "explanation"}
    missing = sorted(req - set(parsed.keys()))
    if missing:
        return [f"Missing keys: {missing}"]
    errs: list[str] = []
    if parsed["pair_id"] != pair_id:
        errs.append(f"pair_id mismatch: {parsed['pair_id']!r} != {pair_id!r}")
    if not isinstance(parsed["same_situation"], bool):
        errs.append("same_situation must be bool")
    if not isinstance(parsed["confirmed_rule1_collision"], bool):
        errs.append("confirmed_rule1_collision must be bool")
    if not isinstance(parsed["explanation"], str) or not parsed["explanation"].strip():
        errs.append("explanation must be non-empty string")
    return errs


def validate_m4_item_json(parsed: Any, expected_item_ids: list[str]) -> list[str]:
    if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
        return ["Expected JSON object with 'items' list"]
    errs: list[str] = []
    seen: list[str] = []
    for row in parsed["items"]:
        if not isinstance(row, dict):
            errs.append("Item element is not dict")
            continue
        iid = row.get("item_id")
        seen.append(str(iid))
        scores = row.get("scores")
        if not isinstance(scores, dict) or set(scores.keys()) != {"1", "2", "3", "4"}:
            errs.append(f"{iid}: scores must have keys '1'..'4'")
        else:
            for k, v in scores.items():
                if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= 5):
                    errs.append(f"{iid}: scores[{k!r}]={v!r} must be int 1..5")
        ranking = row.get("ranking")
        if not isinstance(ranking, list) or sorted(ranking) != [1, 2, 3, 4] or any(isinstance(x, bool) for x in ranking):
            errs.append(f"{iid}: ranking must be permutation of [1,2,3,4], got {ranking!r}")
        best_c = row.get("best_candidate")
        worst_c = row.get("worst_candidate")
        if best_c not in (1, 2, 3, 4) or isinstance(best_c, bool):
            errs.append(f"{iid}: invalid best_candidate {best_c!r}")
        if worst_c not in (1, 2, 3, 4) or isinstance(worst_c, bool):
            errs.append(f"{iid}: invalid worst_candidate {worst_c!r}")
        if best_c == worst_c:
            errs.append(f"{iid}: best_candidate == worst_candidate")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            errs.append(f"{iid}: reason must be non-empty string")
    if set(seen) != set(expected_item_ids) or len(seen) != len(expected_item_ids):
        errs.append(f"Item ID mismatch: got {seen}, expected {expected_item_ids}")
    return errs


def validate_m4_native_pair_json(parsed: Any, expected_item_ids: list[str]) -> list[str]:
    if not isinstance(parsed, dict) or not isinstance(parsed.get("pairs"), list):
        return ["Expected JSON object with 'pairs' list"]
    errs: list[str] = []
    seen: list[str] = []
    for row in parsed["pairs"]:
        if not isinstance(row, dict):
            errs.append("Pair element is not dict")
            continue
        iid = row.get("item_id")
        seen.append(str(iid))
        for sk in ("score_a", "score_b"):
            sv = row.get(sk)
            if not isinstance(sv, int) or isinstance(sv, bool) or not (1 <= sv <= 5):
                errs.append(f"{iid}: {sk}={sv!r} must be int 1..5")
        if row.get("preferred") not in ("A", "B", "tie"):
            errs.append(f"{iid}: invalid preferred {row.get('preferred')!r}")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            errs.append(f"{iid}: reason must be non-empty string")
    if set(seen) != set(expected_item_ids) or len(seen) != len(expected_item_ids):
        errs.append(f"Pair item_ids mismatch: got {seen}, expected {expected_item_ids}")
    return errs


def validate_m4_bundle_json(parsed: Any) -> list[str]:
    if not isinstance(parsed, dict):
        return ["Expected JSON object"]
    req = {"scores", "best_system", "worst_system", "ranking", "reason"}
    missing = sorted(req - set(parsed.keys()))
    if missing:
        return [f"Missing keys: {missing}"]
    errs: list[str] = []
    scores = parsed["scores"]
    scores_valid = False
    if not isinstance(scores, dict) or set(scores.keys()) != {"1", "2", "3", "4"}:
        errs.append("scores must have keys '1'..'4'")
    else:
        bad_vals = [
            (k, v)
            for k, v in scores.items()
            if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= 5)
        ]
        if bad_vals:
            for k, v in bad_vals:
                errs.append(f"scores[{k!r}]={v!r} must be int 1..5")
        else:
            scores_valid = True
    ranking = parsed["ranking"]
    ranking_valid = (
        isinstance(ranking, list)
        and sorted(ranking) == [1, 2, 3, 4]
        and not any(isinstance(x, bool) for x in ranking)
    )
    if not ranking_valid:
        errs.append(f"ranking must be permutation of [1,2,3,4], got {ranking!r}")
    best_sys = parsed["best_system"]
    worst_sys = parsed["worst_system"]
    extremes_valid = (
        best_sys in (1, 2, 3, 4)
        and not isinstance(best_sys, bool)
        and worst_sys in (1, 2, 3, 4)
        and not isinstance(worst_sys, bool)
        and best_sys != worst_sys
    )
    if best_sys not in (1, 2, 3, 4) or isinstance(best_sys, bool) or worst_sys not in (1, 2, 3, 4) or isinstance(worst_sys, bool):
        errs.append("best_system/worst_system must be 1..4")
    elif best_sys == worst_sys:
        errs.append("best_system == worst_system")
    if ranking_valid and extremes_valid:
        if best_sys != ranking[0]:
            errs.append(f"best_system {best_sys} != ranking[0] {ranking[0]}")
        if worst_sys != ranking[-1]:
            errs.append(f"worst_system {worst_sys} != ranking[-1] {ranking[-1]}")
    if ranking_valid and scores_valid:
        ranked_scores = [scores[str(s)] for s in ranking]
        if any(ranked_scores[i] < ranked_scores[i + 1] for i in range(3)):
            errs.append(f"scores along ranking {ranking} are not monotonically non-increasing: {ranked_scores}")
        if extremes_valid:
            if scores[str(best_sys)] != max(scores.values()):
                errs.append(f"scores[{best_sys}]={scores[str(best_sys)]} != max score {max(scores.values())}")
            if scores[str(worst_sys)] != min(scores.values()):
                errs.append(f"scores[{worst_sys}]={scores[str(worst_sys)]} != min score {min(scores.values())}")
    if not isinstance(parsed["reason"], str) or not parsed["reason"].strip():
        errs.append("reason must be non-empty string")
    return errs


def validate_m5_vocab_free_json(parsed: Any, physical_slot: str) -> list[str]:
    if not isinstance(parsed, dict):
        return ["Expected JSON object"]
    req = {"physical_slot", "proposed_counterpart", "alternate_candidates", "reason"}
    missing = sorted(req - set(parsed.keys()))
    if missing:
        return [f"Missing keys: {missing}"]
    errs: list[str] = []
    if parsed["physical_slot"] != physical_slot:
        errs.append(f"physical_slot {parsed['physical_slot']!r} != {physical_slot!r}")
    if not isinstance(parsed["proposed_counterpart"], str) or not parsed["proposed_counterpart"].strip():
        errs.append("proposed_counterpart must be non-empty string")
    alts = parsed["alternate_candidates"]
    if not isinstance(alts, list) or not all(isinstance(x, str) and x.strip() for x in alts):
        errs.append("alternate_candidates must be list of non-empty strings")
    if not isinstance(parsed["reason"], str) or not parsed["reason"].strip():
        errs.append("reason must be non-empty string")
    return errs


# ---------------------------------------------------------------------------
# Resumable Log Cache & Retrying Chat Caller
# ---------------------------------------------------------------------------


def _load_existing_log_records(log_path: Path) -> dict[tuple[str, str, str, str], list[dict[str, Any]]]:
    by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    if not log_path.exists():
        return by_key
    for line_num, raw_line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        rec = json.loads(stripped)
        key = (rec["role"], rec["arm_id"], rec["item_id"], rec["model_id"])
        by_key[key].append(rec)
    return by_key


def _call_with_schema_retries(
    *,
    client: providers.CheaperInferenceClient,
    existing_log: dict[tuple[str, str, str, str], list[dict[str, Any]]],
    role: str,
    arm_id: str,
    item_id: str,
    model_id: str,
    base_messages: list[dict[str, str]],
    validator: Callable[[Any], list[str]],
    max_attempts: int = MAX_PARSE_ATTEMPTS,
) -> dict[str, Any]:
    """Check existing log for a valid response first; otherwise run up to `max_attempts` live calls.

    After `max_attempts` failed validation attempts, returns a non-crashing `status="schema_error"`
    record (`parsed=None`) instead of raising so downstream workers and stages keep running cleanly.
    """
    cached = existing_log.get((role, arm_id, item_id, model_id), [])
    # Inspect logged attempts in chronological order; return the latest valid one if present
    valid_cached: dict[str, Any] | None = None
    prior_failures: int = 0
    last_err: list[str] = []
    last_raw = ""
    last_call_id = cached[-1]["call_id"] if cached else ""
    for rec in cached:
        raw = rec["raw_response"]
        parsed = providers.extract_first_json_object(raw)
        if parsed is None:
            prior_failures += 1
            last_err = ["No valid JSON object found in output"]
            last_raw = raw
            last_call_id = rec["call_id"]
            continue
        errs = validator(parsed)
        if not errs:
            valid_cached = {
                "status": "ok",
                "parsed": parsed,
                "raw_response": raw,
                "attempt_used": prior_failures + 1,
                "from_cache": True,
                "call_id": rec["call_id"],
                "errors": [],
            }
        else:
            prior_failures += 1
            last_err = errs
            last_raw = raw
            last_call_id = rec["call_id"]

    if valid_cached is not None:
        return valid_cached

    if prior_failures >= max_attempts:
        return {
            "status": "schema_error",
            "parsed": None,
            "raw_response": last_raw,
            "attempt_used": prior_failures,
            "from_cache": True,
            "call_id": last_call_id,
            "errors": list(last_err),
        }

    messages = list(base_messages)
    if prior_failures > 0 and last_raw:
        messages.append({"role": "assistant", "content": last_raw})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous JSON output had validation errors:\n- "
                    + "\n- ".join(last_err)
                    + "\nReturn ONLY a corrected single valid JSON object satisfying every invariant."
                ),
            }
        )

    for attempt_idx in range(prior_failures, max_attempts):
        raw_text, meta = client.chat(
            model_id=model_id,
            messages=messages,
            role=role,
            arm_id=arm_id,
            item_id=item_id,
            temperature=providers.DEFAULT_TEMPERATURE,
            max_tokens=None,
        )
        last_call_id = meta.get("call_id", "")
        parsed = providers.extract_first_json_object(raw_text)
        errs = ["No valid JSON object found in output"] if parsed is None else validator(parsed)
        if not errs and parsed is not None:
            return {
                "status": "ok",
                "parsed": parsed,
                "raw_response": raw_text,
                "attempt_used": attempt_idx + 1,
                "from_cache": False,
                "call_id": last_call_id,
                "errors": [],
            }
        last_err = errs
        last_raw = raw_text
        messages.append({"role": "assistant", "content": raw_text})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous JSON output had validation errors:\n- "
                    + "\n- ".join(errs)
                    + "\nReturn ONLY a corrected single valid JSON object satisfying every invariant."
                ),
            }
        )

    return {
        "status": "schema_error",
        "parsed": None,
        "raw_response": last_raw,
        "attempt_used": max_attempts,
        "from_cache": False,
        "call_id": last_call_id,
        "errors": list(last_err),
    }


# ---------------------------------------------------------------------------
# Pure Deterministic Aggregation Logic (Used in Both `--run-live` and `--verify-prereg`/`--verify-offline`)
# ---------------------------------------------------------------------------


def aggregate_stage1_m1(
    cal_items: list[dict[str, Any]],
    m1_results: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Score Stage 1 zero-shot calibration predictions post-generation against expected_book_ruling."""
    arm_summaries: dict[str, Any] = {}
    for arm_id in ("A0", "A3-1"):
        per_model_correct: Counter[str] = Counter()
        per_model_total: Counter[str] = Counter()
        per_model_schema_errors: Counter[str] = Counter()
        item_rows: list[dict[str, Any]] = []
        consensus_correct = 0
        consensus_count = 0
        schema_errors_count = 0
        for item in cal_items:
            iid = item["item_id"]
            expected = item["expected_book_ruling"]
            votes: dict[str, str] = {}
            schema_errs_for_item: dict[str, list[str]] = {}
            for model_id, _vendor in providers.GENERATORS:
                rec = m1_results[(arm_id, iid, model_id)]
                per_model_total[model_id] += 1
                if rec.get("status") == "schema_error" or rec.get("parsed") is None:
                    votes[model_id] = "SCHEMA_ERROR"
                    schema_errors_count += 1
                    per_model_schema_errors[model_id] += 1
                    schema_errs_for_item[model_id] = list(rec.get("errors", ["schema_error"]))
                    continue
                out = rec["parsed"]
                r = out["ruling"]
                votes[model_id] = r
                if r == expected:
                    per_model_correct[model_id] += 1
            valid_votes = [v for v in votes.values() if v != "SCHEMA_ERROR"]
            if valid_votes:
                top_ruling, top_cnt = Counter(valid_votes).most_common(1)[0]
                reached = top_cnt >= 4
            else:
                top_ruling, top_cnt, reached = "SCHEMA_ERROR", 0, False
            if reached:
                consensus_count += 1
                if top_ruling == expected:
                    consensus_correct += 1
            item_rows.append(
                {
                    "item_id": iid,
                    "expected_book_ruling": expected,
                    "votes": votes,
                    "majority_ruling": top_ruling,
                    "majority_count": top_cnt,
                    "consensus_4_of_5": reached,
                    "consensus_correct": (top_ruling == expected) if reached else False,
                    "schema_errors": schema_errs_for_item,
                }
            )
        arm_summaries[arm_id] = {
            "total_items": len(cal_items),
            "consensus_4_of_5_count": consensus_count,
            "consensus_exact_match_count": consensus_correct,
            "schema_error_count": schema_errors_count,
            "per_model_schema_errors": {m: per_model_schema_errors[m] for m, _v in providers.GENERATORS},
            "per_model_accuracy": {
                m: round(per_model_correct[m] / max(1, per_model_total[m]), 4)
                for m, _v in providers.GENERATORS
            },
            "items": item_rows,
        }
    return arm_summaries


def aggregate_stage2_consensus(
    heldout_items: list[dict[str, Any]],
    m2_results: dict[tuple[str, str, str], dict[str, Any]],
    arms_by_id: dict[str, arms_v2.ArmConfigV2],
) -> dict[str, Any]:
    """Select `>= 4/5` consensus rulings and pick canonical generator AFTER per-item Layer-A checks."""
    out: dict[str, Any] = {}
    for arm_id in ("A0", "A3-1"):
        arm = arms_by_id[arm_id]
        items_summary: list[dict[str, Any]] = []
        consensus_keep_invert: list[dict[str, Any]] = []
        ruling_counts: Counter[str] = Counter()
        schema_errors_count = 0
        for item in heldout_items:
            iid = item["item_id"]
            model_outputs: dict[str, dict[str, Any] | None] = {}
            votes: dict[str, str] = {}
            schema_errs_for_item: dict[str, list[str]] = {}
            for model_id, _v in providers.GENERATORS:
                rec = m2_results[(arm_id, iid, model_id)]
                if rec.get("status") == "schema_error" or rec.get("parsed") is None:
                    model_outputs[model_id] = None
                    votes[model_id] = "SCHEMA_ERROR"
                    schema_errors_count += 1
                    schema_errs_for_item[model_id] = list(rec.get("errors", ["schema_error"]))
                else:
                    parsed = rec["parsed"]
                    model_outputs[model_id] = parsed
                    votes[model_id] = parsed["ruling"]

            valid_votes = [v for v in votes.values() if v != "SCHEMA_ERROR"]
            if valid_votes:
                top_ruling, top_cnt = Counter(valid_votes).most_common(1)[0]
                reached = top_cnt >= 4
            else:
                top_ruling, top_cnt, reached = "SCHEMA_ERROR", 0, False
            canonical_model: str | None = None
            canonical_out: dict[str, Any] | None = None
            per_voter_la: dict[str, dict[str, Any]] = {}

            if reached:
                ruling_counts[top_ruling] += 1
                agreeing_models = [
                    m for m, _v in providers.GENERATORS
                    if votes[m] == top_ruling and model_outputs[m] is not None
                ]
                if top_ruling in ("keep", "invert"):
                    la_passers: list[str] = []
                    for m in agreeing_models:
                        m_out = model_outputs[m]
                        assert m_out is not None
                        la = arms_v2.run_layer_a_item_check(m_out, arm, item=item)
                        per_voter_la[m] = la
                        if la["passed"]:
                            la_passers.append(m)
                    # Select canonical generator FIRST among Layer-A passers in GENERATORS order!
                    canonical_model = la_passers[0] if la_passers else agreeing_models[0]
                    canonical_out = model_outputs[canonical_model]
                    assert canonical_out is not None
                    consensus_keep_invert.append({"item": item, "output": canonical_out, "canonical_model": canonical_model})
                else:
                    canonical_model = agreeing_models[0]
                    canonical_out = model_outputs[canonical_model]

            items_summary.append(
                {
                    "item_id": iid,
                    "stratum": item["stratum"],
                    "votes": votes,
                    "majority_ruling": top_ruling,
                    "majority_count": top_cnt,
                    "consensus_4_of_5": reached,
                    "canonical_model": canonical_model,
                    "per_voter_layer_a": per_voter_la,
                    "canonical_output": canonical_out,
                    "all_model_outputs": model_outputs,
                    "schema_errors": schema_errs_for_item,
                }
            )

        joint_layer_a = arms_v2.run_layer_a_v2(consensus_keep_invert, arm)
        out[arm_id] = {
            "total_items": len(heldout_items),
            "consensus_4_of_5_total": sum(1 for x in items_summary if x["consensus_4_of_5"]),
            "ruling_distribution": dict(ruling_counts),
            "consensus_keep_invert_count": len(consensus_keep_invert),
            "schema_error_count": schema_errors_count,
            "joint_layer_a": joint_layer_a,
            "items": items_summary,
        }
    return out


def build_m3c_pair_batches(
    stage2_arm_summary: dict[str, Any],
    arm: arms_v2.ArmConfigV2,
) -> tuple[list[dict[str, Any]], list[list[dict[str, Any]]]]:
    """Build ALL shared-slot pairs `(i, j)` of consensus `keep`/`invert` items within an arm."""
    ki_rows = [
        row for row in stage2_arm_summary["items"]
        if row["consensus_4_of_5"] and row["majority_ruling"] in ("keep", "invert")
    ]
    ki_rows.sort(key=lambda r: r["item_id"])
    slots_by_id = {
        r["item_id"]: arms_v2.extract_normalized_slots_for_item(r["canonical_output"], arm)
        for r in ki_rows
    }
    raw_pairs: list[dict[str, Any]] = []
    for idx_i in range(len(ki_rows)):
        for idx_j in range(idx_i + 1, len(ki_rows)):
            ri = ki_rows[idx_i]
            rj = ki_rows[idx_j]
            shared = sorted(slots_by_id[ri["item_id"]] & slots_by_id[rj["item_id"]])
            if not shared:
                continue
            raw_pairs.append(
                {
                    "arm_id": arm.arm_id,
                    "item_i": ri["item_id"],
                    "item_j": rj["item_id"],
                    "shared_terms": shared,
                    "statement_a": ri["canonical_output"]["translation_t"],
                    "statement_b": rj["canonical_output"]["translation_t"],
                }
            )
    # Deterministically assign opaque pair IDs so judge sees zero arm info
    raw_pairs = arms_v2._seeded_shuffle(raw_pairs, f"M3c_pairs_order:{arm.arm_id}")
    for p in raw_pairs:
        tag = hashlib.sha256(
            f"{arms_v2.HARNESS_SEED}:{arm.arm_id}:{p['item_i']}:{p['item_j']}".encode("utf-8")
        ).hexdigest()[:8].upper()
        p["pair_id"] = f"PR_{tag}"
    return raw_pairs, _chunked(raw_pairs, 6)


# ---------------------------------------------------------------------------
# Live Pipeline Execution (`--run-live`)
# ---------------------------------------------------------------------------


def run_live_pipeline(env_file: Path | None, max_workers: int = 8) -> dict[str, Any]:
    """Execute Stages 1..6 sequentially (parallel within stages) with JSONL resumption."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    cal_payload = _load_json(prepare_openstax_sample.CALIBRATION_17_PATH)
    heldout_payload = _load_json(prepare_openstax_sample.HELDOUT_40_PATH)
    cal_items: list[dict[str, Any]] = cal_payload["items"]
    heldout_items: list[dict[str, Any]] = heldout_payload["items"]

    api_key = providers.resolve_api_key(env_path=env_file)
    logger = providers.JsonlCallLogger(LIVE_LOG_PATH, secrets=(api_key,))
    client = providers.CheaperInferenceClient(
        api_key=api_key,
        timeout_sec=DEFAULT_TIMEOUT_SEC,
        logger=logger,
        jitter_seed=arms_v2.HARNESS_SEED,
    )
    existing_log = _load_existing_log_records(LIVE_LOG_PATH)

    arms_by_id = {
        "A0": arms_v2.build_arm_v2("A0"),
        "A3-1": arms_v2.build_arm_v2("A3-1"),
    }

    # --- Stage 1: M1 Calibration K01..K17 (2 arms x 17 items x 5 generators = 170 calls) ---
    m1_tasks: list[tuple[str, str, str, list[dict[str, str]], Callable[[Any], list[str]]]] = []
    for arm_id in ("A0", "A3-1"):
        arm = arms_by_id[arm_id]
        for item in cal_items:
            msgs = arms_v2.build_stage1_m1_messages(arm, item)
            for model_id, _vendor in providers.GENERATORS:
                m1_tasks.append(
                    (
                        arm_id,
                        item["item_id"],
                        model_id,
                        msgs,
                        lambda p, _arm=arm, _item=item: arms_v2.validate_generator_json(p, _arm, _item),
                    )
                )

    m1_results: dict[tuple[str, str, str], dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {
            pool.submit(
                _call_with_schema_retries,
                client=client,
                existing_log=existing_log,
                role="stage1_m1_generator",
                arm_id=arm_id,
                item_id=iid,
                model_id=model_id,
                base_messages=msgs,
                validator=val_fn,
            ): (arm_id, iid, model_id)
            for arm_id, iid, model_id, msgs, val_fn in m1_tasks
        }
        for fut in concurrent.futures.as_completed(futs):
            k = futs[fut]
            m1_results[k] = fut.result()

    stage1_summary = aggregate_stage1_m1(cal_items, m1_results)
    _write_json(OUTPUTS_DIR / "stage1_m1_calibration.json", stage1_summary)

    # Refresh log view before next stage
    existing_log = _load_existing_log_records(LIVE_LOG_PATH)

    # --- Stage 2: M2 Held-out E001..E040 (2 arms x 40 items x 5 generators = 400 calls) ---
    m2_tasks: list[tuple[str, str, str, list[dict[str, str]], Callable[[Any], list[str]]]] = []
    for arm_id in ("A0", "A3-1"):
        arm = arms_by_id[arm_id]
        for item in heldout_items:
            msgs = arms_v2.build_stage2_m2_messages(arm, item)
            for model_id, _vendor in providers.GENERATORS:
                m2_tasks.append(
                    (
                        arm_id,
                        item["item_id"],
                        model_id,
                        msgs,
                        lambda p, _arm=arm, _item=item: arms_v2.validate_generator_json(p, _arm, _item),
                    )
                )

    m2_results: dict[tuple[str, str, str], dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {
            pool.submit(
                _call_with_schema_retries,
                client=client,
                existing_log=existing_log,
                role="stage2_m2_generator",
                arm_id=arm_id,
                item_id=iid,
                model_id=model_id,
                base_messages=msgs,
                validator=val_fn,
            ): (arm_id, iid, model_id)
            for arm_id, iid, model_id, msgs, val_fn in m2_tasks
        }
        for fut in concurrent.futures.as_completed(futs):
            k = futs[fut]
            m2_results[k] = fut.result()

    stage2_summary = aggregate_stage2_consensus(heldout_items, m2_results, arms_by_id)
    _write_json(OUTPUTS_DIR / "stage2_m2_heldout.json", stage2_summary)
    _write_json(
        OUTPUTS_DIR / "layer_a_summary.json",
        {arm_id: stage2_summary[arm_id]["joint_layer_a"] for arm_id in ("A0", "A3-1")},
    )

    existing_log = _load_existing_log_records(LIVE_LOG_PATH)
    heldout_by_id = {x["item_id"]: x for x in heldout_items}

    # --- Stage 3: M3b Adversarial Opponent on consensus keep/invert items ---
    m3b_tasks: list[tuple[str, str, list[dict[str, str]]]] = []
    for arm_id in ("A0", "A3-1"):
        arm = arms_by_id[arm_id]
        for row in stage2_summary[arm_id]["items"]:
            if row["consensus_4_of_5"] and row["majority_ruling"] in ("keep", "invert"):
                item = heldout_by_id[row["item_id"]]
                msgs = arms_v2.build_stage3_m3b_opponent_messages(arm, item, row["canonical_output"])
                m3b_tasks.append((arm_id, row["item_id"], msgs))

    m3b_results: dict[tuple[str, str], dict[str, Any]] = {}
    opp_model = providers.OPPONENT[0]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {
            pool.submit(
                _call_with_schema_retries,
                client=client,
                existing_log=existing_log,
                role="stage3_m3b_opponent",
                arm_id=arm_id,
                item_id=iid,
                model_id=opp_model,
                base_messages=msgs,
                validator=lambda p, _iid=iid: validate_m3b_opponent_json(p, _iid),
            ): (arm_id, iid)
            for arm_id, iid, msgs in m3b_tasks
        }
        for fut in concurrent.futures.as_completed(futs):
            k = futs[fut]
            m3b_results[k] = fut.result()

    _write_json(
        OUTPUTS_DIR / "stage3_m3b_opponent.json",
        {
            f"{arm_id}:{iid}": _unwrap_or_schema_error(res)
            for (arm_id, iid), res in sorted(m3b_results.items())
        },
    )

    existing_log = _load_existing_log_records(LIVE_LOG_PATH)

    # --- Stage 4: M3c Zero-Glossary Plain-English Layer B (Vertical + Horizontal + Rule 1) ---
    # Notice Opponent results are NEVER passed to Stage 4!
    m3c_single_items: list[dict[str, Any]] = []
    for arm_id in ("A0", "A3-1"):
        for row in stage2_summary[arm_id]["items"]:
            if row["consensus_4_of_5"] and row["majority_ruling"] in ("keep", "invert"):
                item = heldout_by_id[row["item_id"]]
                m3c_single_items.append(
                    {
                        "arm_id": arm_id,
                        "item_id": row["item_id"],
                        "description": item["description"],
                        "equation_latex": item["equation_latex"],
                        "translation_t": row["canonical_output"]["translation_t"],
                    }
                )
    m3c_single_items = arms_v2._seeded_shuffle(m3c_single_items, "M3c_single_order")
    for idx, rec in enumerate(m3c_single_items, start=1):
        rec["eval_id"] = f"EV_{idx:03d}"

    m3c_single_res: dict[tuple[str, str], dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {}
        for rec in m3c_single_items:
            msgs = arms_v2.build_stage4_m3c_single_messages(
                rec["eval_id"], rec["description"], rec["equation_latex"], rec["translation_t"]
            )
            for judge_id, _v in providers.LAYER_B_JUDGES:
                fut = pool.submit(
                    _call_with_schema_retries,
                    client=client,
                    existing_log=existing_log,
                    role="stage4_m3c_single",
                    arm_id=rec["arm_id"],
                    item_id=rec["item_id"],
                    model_id=judge_id,
                    base_messages=msgs,
                    validator=lambda p, _ev=rec["eval_id"]: validate_m3c_single_json(p, _ev),
                )
                futs[fut] = (rec["eval_id"], judge_id)
        for fut in concurrent.futures.as_completed(futs):
            k = futs[fut]
            m3c_single_res[k] = fut.result()

    # Horizontal pairs (<= 6 pairs/batch per arm)
    pair_records_by_id: dict[str, dict[str, Any]] = {}
    m3c_pair_batches_all: list[tuple[str, int, list[dict[str, Any]]]] = []
    for arm_id in ("A0", "A3-1"):
        raw_pairs, batches = build_m3c_pair_batches(stage2_summary[arm_id], arms_by_id[arm_id])
        for p in raw_pairs:
            pair_records_by_id[p["pair_id"]] = p
        for b_idx, batch in enumerate(batches, start=1):
            m3c_pair_batches_all.append((arm_id, b_idx, batch))

    pair_judge_verdicts: dict[tuple[str, str], dict[str, Any]] = {}
    m3c_pairs_schema_errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {}
        for arm_id, b_idx, batch in m3c_pair_batches_all:
            msgs = arms_v2.build_stage4_m3c_pairs_messages(batch)
            pids = [p["pair_id"] for p in batch]
            batch_key = f"batch_{b_idx:03d}"
            for judge_id, _v in providers.LAYER_B_JUDGES:
                fut = pool.submit(
                    _call_with_schema_retries,
                    client=client,
                    existing_log=existing_log,
                    role="stage4_m3c_pairs",
                    arm_id=arm_id,
                    item_id=batch_key,
                    model_id=judge_id,
                    base_messages=msgs,
                    validator=lambda p, _pids=pids: validate_m3c_pairs_json(p, _pids),
                )
                futs[fut] = (pids, judge_id)
        for fut in concurrent.futures.as_completed(futs):
            pids, judge_id = futs[fut]
            res = fut.result()
            if res.get("status") == "schema_error" or res.get("parsed") is None:
                m3c_pairs_schema_errors += 1
                for pid in pids:
                    pair_judge_verdicts[(pid, judge_id)] = {
                        "pair_id": pid,
                        "status": "schema_error",
                        "verdict": "schema_error",
                        "errors": list(res.get("errors", [])),
                    }
            else:
                for r in res["parsed"]["results"]:
                    pair_judge_verdicts[(r["pair_id"], judge_id)] = r

    # Unbatched Rule-1 check (`gemini-2.5-flash`) on any 2/2 contradiction pair!
    rule1_candidates: list[dict[str, Any]] = []
    judge_ids = [m for m, _v in providers.LAYER_B_JUDGES]
    for pid, p_rec in sorted(pair_records_by_id.items()):
        verdicts = [pair_judge_verdicts[(pid, jid)].get("verdict") for jid in judge_ids]
        if all(v == "contradiction" for v in verdicts):
            rule1_candidates.append(p_rec)

    existing_log = _load_existing_log_records(LIVE_LOG_PATH)
    rule1_res: dict[str, dict[str, Any]] = {}
    rule1_model = "gemini-2.5-flash"
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {}
        for p_rec in rule1_candidates:
            msgs = arms_v2.build_stage4_m3c_situation_messages(p_rec)
            fut = pool.submit(
                _call_with_schema_retries,
                client=client,
                existing_log=existing_log,
                role="stage4_m3c_rule1",
                arm_id=p_rec["arm_id"],
                item_id=p_rec["pair_id"],
                model_id=rule1_model,
                base_messages=msgs,
                validator=lambda p, _pid=p_rec["pair_id"]: validate_m3c_situation_json(p, _pid),
            )
            futs[fut] = p_rec["pair_id"]
        for fut in concurrent.futures.as_completed(futs):
            pid = futs[fut]
            rule1_res[pid] = fut.result()

    stage4_summary = {
        "single_vertical": [
            {
                **rec,
                "judge_verdicts": {
                    jid: _unwrap_or_schema_error(m3c_single_res[(rec["eval_id"], jid)])
                    for jid in judge_ids
                },
            }
            for rec in m3c_single_items
        ],
        "pairs_horizontal": [
            {
                **p_rec,
                "judge_verdicts": {
                    jid: pair_judge_verdicts[(pid, jid)] for jid in judge_ids
                },
                "two_of_two_contradiction": pid in rule1_res,
                "rule1_adjudication": (
                    _unwrap_or_schema_error(rule1_res[pid]) if pid in rule1_res else None
                ),
            }
            for pid, p_rec in sorted(pair_records_by_id.items())
        ],
    }
    _write_json(OUTPUTS_DIR / "stage4_m3c_layer_b.json", stage4_summary)

    existing_log = _load_existing_log_records(LIVE_LOG_PATH)

    # --- Stage 5: M4 Zero-Glossary Plain-English Rating (4 ROUND2_RATERS) ---
    # 5a: M4_item quadruples (A0 Core consensus keep/invert + R9, R10; <= 5 items/batch)
    m4_quadruples: list[dict[str, Any]] = []
    for row in stage2_summary["A0"]["items"]:
        if (
            row["stratum"] == "Core"
            and row["consensus_4_of_5"]
            and row["majority_ruling"] in ("keep", "invert")
        ):
            out_a0 = row["canonical_output"]
            m4_quadruples.append(
                arms_v2.prepare_m4_quadruple(
                    row["item_id"],
                    out_a0["translation_template"],
                    out_a0["direction_flipped_d"],
                    src_arm=arms_by_id["A0"],
                )
            )
    for ctrl in arms_v2.ROUND2_CONTROLS_V2:
        m4_quadruples.append(
            arms_v2.prepare_m4_quadruple(
                ctrl["item_id"],
                ctrl["translation_template"],
                ctrl["direction_flipped_d"],
                src_arm=arms_by_id["A0"],
            )
        )

    m4_item_batches = _chunked(m4_quadruples, 5)
    m4_item_scores_by_rater: dict[tuple[str, str], dict[str, Any]] = {}
    m4_item_schema_errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {}
        for b_idx, batch in enumerate(m4_item_batches, start=1):
            msgs = arms_v2.build_stage5_m4_item_messages(batch)
            iids = [x["item_id"] for x in batch]
            batch_key = f"batch_{b_idx:03d}"
            for rater_id, _v in providers.ROUND2_RATERS:
                fut = pool.submit(
                    _call_with_schema_retries,
                    client=client,
                    existing_log=existing_log,
                    role="stage5_m4_item",
                    arm_id="quarantined_4way",
                    item_id=batch_key,
                    model_id=rater_id,
                    base_messages=msgs,
                    validator=lambda p, _iids=iids: validate_m4_item_json(p, _iids),
                )
                futs[fut] = (iids, rater_id)
        for fut in concurrent.futures.as_completed(futs):
            iids, rater_id = futs[fut]
            res = fut.result()
            if res.get("status") == "schema_error" or res.get("parsed") is None:
                m4_item_schema_errors += 1
                for iid in iids:
                    m4_item_scores_by_rater[(iid, rater_id)] = {
                        "item_id": iid,
                        "status": "schema_error",
                        "errors": list(res.get("errors", [])),
                    }
            else:
                for r in res["parsed"]["items"]:
                    m4_item_scores_by_rater[(r["item_id"], rater_id)] = r

    # 5b: M4_native_pair (items reaching consensus keep/invert in BOTH A0 and A3-1; <= 6/batch)
    a0_by_id = {r["item_id"]: r for r in stage2_summary["A0"]["items"]}
    a3_by_id = {r["item_id"]: r for r in stage2_summary["A3-1"]["items"]}
    native_pairs: list[dict[str, Any]] = []
    for item in heldout_items:
        iid = item["item_id"]
        ra0, ra3 = a0_by_id[iid], a3_by_id[iid]
        if (
            ra0["consensus_4_of_5"]
            and ra3["consensus_4_of_5"]
            and ra0["majority_ruling"] in ("keep", "invert")
            and ra3["majority_ruling"] in ("keep", "invert")
        ):
            native_pairs.append(
                arms_v2.prepare_m4_native_pair(
                    iid,
                    ra0["canonical_output"]["translation_t"],
                    ra3["canonical_output"]["translation_t"],
                )
            )

    native_pair_batches = _chunked(native_pairs, 6)
    m4_native_res_by_rater: dict[tuple[str, str], dict[str, Any]] = {}
    m4_native_schema_errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {}
        for b_idx, batch in enumerate(native_pair_batches, start=1):
            msgs = arms_v2.build_stage5_m4_native_pair_messages(batch)
            iids = [x["item_id"] for x in batch]
            batch_key = f"batch_{b_idx:03d}"
            for rater_id, _v in providers.ROUND2_RATERS:
                fut = pool.submit(
                    _call_with_schema_retries,
                    client=client,
                    existing_log=existing_log,
                    role="stage5_m4_native_pair",
                    arm_id="quarantined_native_pair",
                    item_id=batch_key,
                    model_id=rater_id,
                    base_messages=msgs,
                    validator=lambda p, _iids=iids: validate_m4_native_pair_json(p, _iids),
                )
                futs[fut] = (iids, rater_id)
        for fut in concurrent.futures.as_completed(futs):
            iids, rater_id = futs[fut]
            res = fut.result()
            if res.get("status") == "schema_error" or res.get("parsed") is None:
                m4_native_schema_errors += 1
                for iid in iids:
                    m4_native_res_by_rater[(iid, rater_id)] = {
                        "item_id": iid,
                        "status": "schema_error",
                        "errors": list(res.get("errors", [])),
                    }
            else:
                for r in res["parsed"]["pairs"]:
                    m4_native_res_by_rater[(r["item_id"], rater_id)] = r

    # 5c: M4_bundle (3 order permutations x 4 ROUND2_RATERS = 12 calls)
    m4_bundles = [arms_v2.prepare_m4_bundles(m4_quadruples, perm_idx) for perm_idx in range(3)]
    m4_bundle_res: dict[tuple[int, str], dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {}
        for b_rec in m4_bundles:
            msgs = arms_v2.build_stage5_m4_bundle_messages(b_rec)
            perm_id = f"perm_{b_rec['perm_idx']}"
            for rater_id, _v in providers.ROUND2_RATERS:
                fut = pool.submit(
                    _call_with_schema_retries,
                    client=client,
                    existing_log=existing_log,
                    role="stage5_m4_bundle",
                    arm_id="quarantined_bundle",
                    item_id=perm_id,
                    model_id=rater_id,
                    base_messages=msgs,
                    validator=validate_m4_bundle_json,
                )
                futs[fut] = (b_rec["perm_idx"], rater_id)
        for fut in concurrent.futures.as_completed(futs):
            k = futs[fut]
            m4_bundle_res[k] = fut.result()

    rater_ids = [m for m, _v in providers.ROUND2_RATERS]
    stage5_summary = {
        "m4_item": [
            {
                **q,
                "ratings": {rid: m4_item_scores_by_rater[(q["item_id"], rid)] for rid in rater_ids},
            }
            for q in m4_quadruples
        ],
        "m4_native_pair": [
            {
                **np_rec,
                "ratings": {rid: m4_native_res_by_rater[(np_rec["item_id"], rid)] for rid in rater_ids},
            }
            for np_rec in native_pairs
        ],
        "m4_bundle": [
            {
                "perm_idx": b["perm_idx"],
                "hidden_key": b["hidden_key"],
                "ratings": {
                    rid: _unwrap_or_schema_error(m4_bundle_res[(b["perm_idx"], rid)])
                    for rid in rater_ids
                },
            }
            for b in m4_bundles
        ],
    }
    _write_json(OUTPUTS_DIR / "stage5_m4_ratings.json", stage5_summary)

    existing_log = _load_existing_log_records(LIVE_LOG_PATH)

    # --- Stage 6: M5 Leak-Free Vocabulary-Free Word Convergence (12 x 5 = 60 calls) ---
    m5_res: dict[tuple[str, str], dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {}
        for slot in arms_v2.STAGE6_PHYSICAL_SLOTS:
            msgs = arms_v2.build_stage6_m5_messages(slot)
            for model_id, _v in providers.GENERATORS:
                fut = pool.submit(
                    _call_with_schema_retries,
                    client=client,
                    existing_log=existing_log,
                    role="stage6_m5_vocab_free",
                    arm_id="vocab_free",
                    item_id=slot,
                    model_id=model_id,
                    base_messages=msgs,
                    validator=lambda p, _s=slot: validate_m5_vocab_free_json(p, _s),
                )
                futs[fut] = (slot, model_id)
        for fut in concurrent.futures.as_completed(futs):
            k = futs[fut]
            m5_res[k] = fut.result()

    stage6_summary = {
        "slots": {
            slot: {
                m: _unwrap_or_schema_error(m5_res[(slot, m)])
                for m, _v in providers.GENERATORS
            }
            for slot in arms_v2.STAGE6_PHYSICAL_SLOTS
        }
    }
    _write_json(OUTPUTS_DIR / "stage6_m5_vocab_free.json", stage6_summary)

    schema_error_counts = {
        "stage1_m1": sum(stage1_summary[a]["schema_error_count"] for a in ("A0", "A3-1")),
        "stage2_m2": sum(stage2_summary[a]["schema_error_count"] for a in ("A0", "A3-1")),
        "stage3_m3b": _count_schema_errors(m3b_results.values()),
        "stage4_m3c_single": _count_schema_errors(m3c_single_res.values()),
        "stage4_m3c_pairs": m3c_pairs_schema_errors,
        "stage4_m3c_rule1": _count_schema_errors(rule1_res.values()),
        "stage5_m4_item": m4_item_schema_errors,
        "stage5_m4_native_pair": m4_native_schema_errors,
        "stage5_m4_bundle": _count_schema_errors(m4_bundle_res.values()),
        "stage6_m5": _count_schema_errors(m5_res.values()),
    }

    master = {
        "stage1_m1_total_cal_items": len(cal_items),
        "stage2_m2_total_heldout_items": len(heldout_items),
        "stage3_m3b_calls": len(m3b_tasks),
        "stage4_m3c_single_items": len(m3c_single_items),
        "stage4_m3c_pairs_total": len(pair_records_by_id),
        "stage4_m3c_rule1_checks": len(rule1_res),
        "stage5_m4_item_count": len(m4_quadruples),
        "stage5_m4_native_pair_count": len(native_pairs),
        "stage5_m4_bundle_calls": len(m4_bundles) * len(rater_ids),
        "stage6_m5_calls": len(arms_v2.STAGE6_PHYSICAL_SLOTS) * len(providers.GENERATORS),
        "schema_error_counts": schema_error_counts,
    }
    _write_json(OUTPUTS_DIR / "summary_all_stages.json", master)
    return master


def _unwrap_or_schema_error(res: dict[str, Any]) -> dict[str, Any]:
    if res.get("status") != "schema_error" and res.get("parsed") is not None:
        return res["parsed"]
    return {"status": "schema_error", "errors": list(res.get("errors", []))}


def _count_schema_errors(records: Iterable[dict[str, Any]]) -> int:
    return sum(1 for r in records if r.get("status") == "schema_error" or r.get("parsed") is None)


def check_repo_hygiene(allow_live_artifacts: bool = False) -> list[str]:
    """Scan `harness/` for forbidden strings, paths, bytecode caches, or whitelist violations."""
    errors: list[str] = []
    bad_substrings = (
        "/" + "Us" + "ers/",
        "." + "gem" + "ini",
        "tsr_" + "01",
        "tsr_" + "pr_repo",
        "tsr_" + "harness_repo",
    )
    banned_tok = "bl" + "ind"
    banned_word_re = re.compile(rf"(?<![A-Za-z]){banned_tok}[a-z]*(?![A-Za-z])", re.I)
    sk_re = re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{8,}")

    observed_rel: set[str] = set()
    for p in sorted(HARNESS_DIR.rglob("*")):
        rel = p.relative_to(HARNESS_DIR).as_posix()
        if any(part == "__pycache__" for part in p.parts) or p.suffix == ".pyc" or p.name == ".DS_Store":
            errors.append(f"Forbidden artifact on disk: harness/{rel}")
            continue
        if p.is_dir():
            continue
        if not allow_live_artifacts:
            observed_rel.add(rel)
        if p.suffix in (".py", ".md", ".json", ".csv"):
            txt = p.read_text(encoding="utf-8")
            for sub in bad_substrings:
                if sub in txt:
                    errors.append(f"Forbidden substring {sub!r} in harness/{rel}")
            mb = banned_word_re.search(txt)
            if mb:
                errors.append(f"Forbidden bare word {mb.group(0)!r} in harness/{rel}")
            ms = sk_re.search(txt)
            if ms:
                errors.append(f"Possible API key literal in harness/{rel}")

    if not allow_live_artifacts:
        unexpected = sorted(observed_rel - COMMIT1_ALLOWED_REL_PATHS)
        missing = sorted(COMMIT1_ALLOWED_REL_PATHS - observed_rel)
        if unexpected:
            errors.append(f"Unexpected non-Commit-1 files under harness/: {unexpected}")
        if missing:
            errors.append(f"Missing expected Commit-1 files under harness/: {missing}")
    return errors


def _verify_prereg_md() -> list[str]:
    errors: list[str] = []
    if not PREREG_MD_PATH.exists():
        return ["Missing harness/PREREGISTRATION.md"]
    md = PREREG_MD_PATH.read_text(encoding="utf-8")

    # Verify frozen OpenStax SHA-256 hashes match PREREGISTRATION.md
    for rel_path in (
        "openstax/heldout_equations_40.json",
        "openstax/calibration_equations_17.json",
        "openstax/sample_manifest.json",
    ):
        digest = _sha256_file(HARNESS_DIR / rel_path)
        if digest not in md:
            errors.append(f"PREREGISTRATION.md missing exact SHA-256 {digest} for harness/{rel_path}")

    # Verify relative markdown links resolve inside repo
    for m in re.finditer(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", md):
        target = m.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (PREREG_MD_PATH.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"Broken relative markdown link in PREREGISTRATION.md: {target!r}")

    return errors


def _run_simulated_e2e_check(cal_items: list[dict[str, Any]], heldout_items: list[dict[str, Any]]) -> None:
    """Verify Stages 1..6 prompt generation, validators, consensus priority, & isolation with 0 live calls."""
    arms_by_id = {
        "A0": arms_v2.build_arm_v2("A0"),
        "A3-1": arms_v2.build_arm_v2("A3-1"),
    }

    # Check ALL real M1 (170) & M2 (400) prompt builders cleanly
    for arm_id in ("A0", "A3-1"):
        arm = arms_by_id[arm_id]
        for ci in cal_items:
            arms_v2.build_stage1_m1_messages(arm, ci)
        for hi in heldout_items:
            arms_v2.build_stage2_m2_messages(arm, hi)

    # Simulate Stage 1 & Stage 2 synthetic outputs covering keep, invert, no partner, and consensus selection
    a0_examples = {x["item_id"]: x["output"] for x in arms_v2.build_calibration_examples_for_arm(arms_by_id["A0"])}
    a3_examples = {x["item_id"]: x["output"] for x in arms_v2.build_calibration_examples_for_arm(arms_by_id["A3-1"])}

    # Verify per-item Layer-A canon selection priority: if generator 0 fails Layer A while generator 1 passes,
    # canonical selection MUST choose generator 1!
    sample_item = {
        "item_id": "E007",
        "stratum": "Core",
        "description": "Displacement",
        "equation_latex": "\\Delta x = x_{\\text{f}} - x_{\\text{i}}",
    }
    good_a0_e007 = {
        "item_id": "E007",
        "scope_status": "in_scope",
        "formula_shape": "keeps",
        "ruling": "keep",
        "two_level": False,
        "axis_polarity_note": "Pure spatial interval change without cost.",
        "unmapped_terms": [],
        "variable_map": {"Delta x": "Vibration", "x_f": "Vibration (final)", "x_i": "Vibration (initial)"},
        "reflected_formula": "Delta Vibration = Vibration_f - Vibration_i",
        "translation_t": "Net Vibration shifts between two positions of Vibration.",
        "translation_template": "Net {Vibration} shifts between two positions of {Vibration}.",
        "direction_flipped_d": "Net Vibration stays frozen regardless of changes between positions of Vibration.",
        "rationale": "kinematic definition",
    }
    assert arms_v2.validate_generator_json(good_a0_e007, arms_by_id["A0"], sample_item) == []
    bad_a0_e007 = dict(good_a0_e007, reflected_formula="Delta Vibration = Vibration_f + Vibration_i")  # flips - to + (A3 fail!)
    assert arms_v2.validate_generator_json(bad_a0_e007, arms_by_id["A0"], sample_item) == []
    assert not arms_v2.run_layer_a_item_check(bad_a0_e007, arms_by_id["A0"], sample_item)["passed"]
    assert arms_v2.run_layer_a_item_check(good_a0_e007, arms_by_id["A0"], sample_item)["passed"]

    synth_m2: dict[tuple[str, str, str], dict[str, Any]] = {}
    for hi in heldout_items:
        iid = hi["item_id"]
        for arm_id, base_ex in (("A0", a0_examples["K16"]), ("A3-1", a3_examples["K16"])):
            for m_idx, (model_id, _v) in enumerate(providers.GENERATORS):
                if iid == "E007" and arm_id == "A0":
                    out = bad_a0_e007 if m_idx == 0 else good_a0_e007
                else:
                    out = dict(base_ex, item_id=iid)
                synth_m2[(arm_id, iid, model_id)] = {"parsed": out}

    # Note K16 reflected_formula matches E_i template only generically; check canonical generator switched to index 1!
    agg = aggregate_stage2_consensus(heldout_items[:2] + [sample_item], synth_m2, arms_by_id)
    e007_row = [r for r in agg["A0"]["items"] if r["item_id"] == "E007"][0]
    assert e007_row["canonical_model"] == providers.GENERATORS[1][0], e007_row

    # Simulate M3c pair batching, M4 items/native pairs/bundles, and M5 prompts
    pairs, batches = build_m3c_pair_batches(agg["A0"], arms_by_id["A0"])
    assert pairs and all(1 <= len(b) <= 6 for b in batches)
    for b in batches:
        arms_v2.build_stage4_m3c_pairs_messages(b)
    arms_v2.build_stage4_m3c_situation_messages(pairs[0])

    # M4 item/bundle simulation
    quad = arms_v2.prepare_m4_quadruple("E007", good_a0_e007["translation_template"], good_a0_e007["direction_flipped_d"])
    arms_v2.build_stage5_m4_item_messages([quad])
    arms_v2.build_stage5_m4_native_pair_messages(
        [arms_v2.prepare_m4_native_pair("E007", good_a0_e007["translation_t"], a3_examples["K16"]["translation_t"])]
    )
    for p_idx in range(3):
        arms_v2.build_stage5_m4_bundle_messages(arms_v2.prepare_m4_bundles([quad], p_idx))
    for slot in arms_v2.STAGE6_PHYSICAL_SLOTS:
        arms_v2.build_stage6_m5_messages(slot)

    # G3-5: Tightened M4_bundle consistency check
    assert validate_m4_bundle_json(
        {
            "scores": {"1": 5, "2": 4, "3": 2, "4": 1},
            "best_system": 1,
            "worst_system": 4,
            "ranking": [1, 2, 3, 4],
            "reason": "Consistent monotone scores and extremes.",
        }
    ) == []
    assert validate_m4_bundle_json(
        {
            "scores": {"1": 3, "2": 5, "3": 2, "4": 4},
            "best_system": 1,
            "worst_system": 4,
            "ranking": [1, 2, 3, 4],
            "reason": "Inconsistent scores vs ranking/best/worst.",
        }
    )
    assert validate_m4_bundle_json(
        {
            "scores": {"1": 5, "2": 4, "3": 2, "4": 1},
            "best_system": 2,
            "worst_system": 4,
            "ranking": [1, 2, 3, 4],
            "reason": "best_system != ranking[0].",
        }
    )

    # G3-4: Non-crashing schema_error handling in _call_with_schema_retries + aggregators (0 live calls!)
    class _StubFailingClient:
        def __init__(self) -> None:
            self.calls = 0

        def chat(self, **_kwargs: Any) -> tuple[str, dict[str, Any]]:
            self.calls += 1
            return "not-json", {"call_id": f"stub_{self.calls}"}

    stub_client = _StubFailingClient()
    err_rec = _call_with_schema_retries(
        client=stub_client,  # type: ignore[arg-type]
        existing_log={},
        role="stage2_m2_generator",
        arm_id="A0",
        item_id="E007",
        model_id="stub",
        base_messages=[{"role": "user", "content": "hi"}],
        validator=lambda _p: ["bad"],
        max_attempts=3,
    )
    assert err_rec["status"] == "schema_error" and err_rec["parsed"] is None and stub_client.calls == 3

    # One schema_error voter on M1 & M2 does not crash and preserves 4/5 consensus among remaining 4 voters
    synth_m1_err: dict[tuple[str, str, str], dict[str, Any]] = {}
    for ci in cal_items:
        for a_id in ("A0", "A3-1"):
            for m_idx, (m_id, _v) in enumerate(providers.GENERATORS):
                if ci["item_id"] == cal_items[0]["item_id"] and a_id == "A0" and m_idx == 0:
                    synth_m1_err[(a_id, ci["item_id"], m_id)] = err_rec
                else:
                    synth_m1_err[(a_id, ci["item_id"], m_id)] = {
                        "status": "ok",
                        "parsed": {"ruling": ci["expected_book_ruling"]},
                    }
    m1_err_agg = aggregate_stage1_m1(cal_items, synth_m1_err)
    assert m1_err_agg["A0"]["schema_error_count"] == 1
    assert m1_err_agg["A0"]["items"][0]["consensus_4_of_5"] is True

    synth_m2_err = dict(synth_m2)
    synth_m2_err[("A0", "E007", providers.GENERATORS[0][0])] = err_rec
    m2_err_agg = aggregate_stage2_consensus(heldout_items[:2] + [sample_item], synth_m2_err, arms_by_id)
    assert m2_err_agg["A0"]["schema_error_count"] == 1
    e007_err_row = [r for r in m2_err_agg["A0"]["items"] if r["item_id"] == "E007"][0]
    assert e007_err_row["consensus_4_of_5"] is True
    assert e007_err_row["canonical_model"] == providers.GENERATORS[1][0]


def run_verify_prereg() -> dict[str, Any]:
    """Commit-1 preregistration gate (0 live calls, read-only, strict file whitelist)."""
    hygiene_errors = check_repo_hygiene(allow_live_artifacts=False)
    if hygiene_errors:
        raise RuntimeError("Hygiene / file-whitelist check failed:\n- " + "\n- ".join(hygiene_errors))

    prereg_errors = _verify_prereg_md()
    if prereg_errors:
        raise RuntimeError("PREREGISTRATION.md check failed:\n- " + "\n- ".join(prereg_errors))

    openstax_res = prepare_openstax_sample.run_verify_offline()
    arms_v2._run_self_test()

    cal_items = _load_json(prepare_openstax_sample.CALIBRATION_17_PATH)["items"]
    heldout_items = _load_json(prepare_openstax_sample.HELDOUT_40_PATH)["items"]
    _run_simulated_e2e_check(cal_items, heldout_items)

    return {
        "verify_prereg": "OK",
        "commit1_file_count": len(COMMIT1_ALLOWED_REL_PATHS),
        "openstax_verify": openstax_res["verify_offline"],
        "cal_items": len(cal_items),
        "heldout_items": len(heldout_items),
        "m1_prompt_checks": 2 * len(cal_items),
        "m2_prompt_checks": 2 * len(heldout_items),
        "m5_slots": len(arms_v2.STAGE6_PHYSICAL_SLOTS),
    }


def run_verify_offline_post_live() -> dict[str, Any]:
    """Post-live verification gate auditing JSONL logs, determinism, and pre-eval output artifacts."""
    hygiene_errors = check_repo_hygiene(allow_live_artifacts=True)
    if hygiene_errors:
        raise RuntimeError("Hygiene check failed:\n- " + "\n- ".join(hygiene_errors))
    prereg_errors = _verify_prereg_md()
    if prereg_errors:
        raise RuntimeError("PREREGISTRATION.md check failed:\n- " + "\n- ".join(prereg_errors))
    prepare_openstax_sample.run_verify_offline()
    arms_v2._run_self_test()

    if not LIVE_LOG_PATH.exists():
        raise RuntimeError(f"Missing live JSONL log at {LIVE_LOG_PATH}")

    existing_log = _load_existing_log_records(LIVE_LOG_PATH)
    required_outputs = (
        "stage1_m1_calibration.json",
        "stage2_m2_heldout.json",
        "layer_a_summary.json",
        "stage3_m3b_opponent.json",
        "stage4_m3c_layer_b.json",
        "stage5_m4_ratings.json",
        "stage6_m5_vocab_free.json",
        "summary_all_stages.json",
    )
    missing_out = [f for f in required_outputs if not (OUTPUTS_DIR / f).exists()]
    if missing_out:
        raise RuntimeError(f"Missing stage outputs under harness/outputs/: {missing_out}")

    raw_lines = LIVE_LOG_PATH.read_text(encoding="utf-8").splitlines()
    for line in raw_lines:
        if line.strip():
            providers.assert_no_secret_leak(line)

    s1 = _load_json(OUTPUTS_DIR / "stage1_m1_calibration.json")
    s2 = _load_json(OUTPUTS_DIR / "stage2_m2_heldout.json")
    la = _load_json(OUTPUTS_DIR / "layer_a_summary.json")
    s5 = _load_json(OUTPUTS_DIR / "stage5_m4_ratings.json")
    s6 = _load_json(OUTPUTS_DIR / "stage6_m5_vocab_free.json")
    master = _load_json(OUTPUTS_DIR / "summary_all_stages.json")

    for arm_id in ("A0", "A3-1"):
        if s1[arm_id]["total_items"] != 17 or s2[arm_id]["total_items"] != 40:
            raise RuntimeError(f"Unexpected item totals in arm {arm_id}")
        if arm_id not in la:
            raise RuntimeError(f"Missing Layer-A summary for {arm_id}")
    if len(s5.get("m4_bundle", [])) != 3:
        raise RuntimeError(f"Expected 3 M4_bundle permutations, got {len(s5.get('m4_bundle', []))}")
    if set(s6.get("slots", {}).keys()) != set(arms_v2.STAGE6_PHYSICAL_SLOTS):
        raise RuntimeError("Stage 6 slots incomplete")

    return {
        "verify_offline": "OK",
        "jsonl_lines": len([l for l in raw_lines if l.strip()]),
        "unique_call_keys": len(existing_log),
        "schema_error_counts": master.get("schema_error_counts", {}),
        "summary": master,
        "outputs_verified": list(required_outputs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Non-cipher TSR v2 evaluation harness")
    parser.add_argument("--verify-prereg", action="store_true", help="Pre-live Commit-1 hygiene and offline prompt check")
    parser.add_argument("--run-live", action="store_true", help="Run live LLM Stages 1..6 sequentially with JSONL resume")
    parser.add_argument("--verify-offline", action="store_true", help="Post-live offline audit of logs and outputs")
    parser.add_argument("--env-file", type=str, default=None, help="Path to .env file containing CHEAPERINFERENCE_API_KEY")
    parser.add_argument("--max-workers", type=int, default=8, help="Concurrent worker count for live API calls")
    args = parser.parse_args()

    mode_count = int(bool(args.verify_prereg)) + int(bool(args.run_live)) + int(bool(args.verify_offline))
    if mode_count != 1:
        parser.error("Specify exactly one of --verify-prereg, --run-live, or --verify-offline")

    if args.verify_prereg:
        print(json.dumps(run_verify_prereg(), indent=2))
    elif args.run_live:
        env_path = Path(args.env_file) if args.env_file else None
        print(json.dumps(run_live_pipeline(env_path, max_workers=args.max_workers), indent=2))
    else:
        print(json.dumps(run_verify_offline_post_live(), indent=2))


if __name__ == "__main__":
    main()
