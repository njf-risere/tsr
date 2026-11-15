#!/usr/bin/env python3
"""Deterministic offline evaluator and verification suite for TSR v2 harness.

Reads the frozen Commit-1 OpenStax/arms specs and Commit-2 raw stage outputs +
JSONL logs, computes exact stdlib statistics, emits `summary_v2.json` plus 4
flat CSV tables, and verifies reproducibility and commit/blob integrity.

Python 3.12+ standard library only. Zero live LLM calls.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness import arms_v2, exact_stats, providers, run_tsr_harness  # noqa: E402
from harness.openstax import prepare_openstax_sample  # noqa: E402

HARNESS_PREREG_SHA = "51109f83f96a94dfe7587c08a9ea972387b64889"
PRE_EVAL_COMMIT_SHA = "932205b733b505028adb32712594cb853321fac9"

RAW_STAGE_FILES: tuple[str, ...] = (
    "harness/logs/live_calls.jsonl",
    "harness/outputs/stage1_m1_calibration.json",
    "harness/outputs/stage2_m2_heldout.json",
    "harness/outputs/layer_a_summary.json",
    "harness/outputs/stage3_m3b_opponent.json",
    "harness/outputs/stage4_m3c_layer_b.json",
    "harness/outputs/stage5_m4_ratings.json",
    "harness/outputs/stage6_m5_vocab_free.json",
    "harness/outputs/summary_all_stages.json",
)

OUTPUTS_DIR = HARNESS_DIR / "outputs"
RESULTS_MD_PATH = HARNESS_DIR / "RESULTS.md"
SUMMARY_V2_PATH = OUTPUTS_DIR / "summary_v2.json"
CSV_M1_PATH = OUTPUTS_DIR / "m1_calibration_17.csv"
CSV_M2_M3_PATH = OUTPUTS_DIR / "m2_m3_heldout_40.csv"
CSV_M4_PATH = OUTPUTS_DIR / "m4_quadruple_ratings.csv"
CSV_M5_PATH = OUTPUTS_DIR / "m5_vocab_free_12.csv"

M4_VARIANTS: tuple[str, ...] = ("T_A0", "T_A3", "S_syn", "D_A0")
CONTROL_IDS: frozenset[str] = frozenset(c["item_id"] for c in arms_v2.ROUND2_CONTROLS_V2)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _median(vals: list[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def _sample_sd(vals: list[float]) -> float:
    n = len(vals)
    if n < 2:
        return 0.0
    mean = sum(vals) / n
    return math.sqrt(sum((x - mean) ** 2 for x in vals) / (n - 1))


def _percentile_sorted(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(q * (len(sorted_vals) - 1)))
    return float(sorted_vals[idx])


def _round_dict(d: dict[str, float], digits: int = 6) -> dict[str, float]:
    return {k: round(v, digits) for k, v in d.items()}


def _render_csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _mcnemar_from_paired_bools(
    keys: list[str],
    flags_a: dict[str, bool],
    flags_b: dict[str, bool],
) -> dict[str, Any]:
    """Compute paired 2x2 counts and exact McNemar test across aligned keys."""
    n11 = n10 = n01 = n00 = 0
    for k in keys:
        a = bool(flags_a[k])
        b = bool(flags_b[k])
        if a and b:
            n11 += 1
        elif a and not b:
            n10 += 1
        elif not a and b:
            n01 += 1
        else:
            n00 += 1
    return {
        "n_paired": len(keys),
        "n11_both_true": n11,
        "n10_first_only": n10,
        "n01_second_only": n01,
        "n00_both_false": n00,
        "p_value": exact_stats.exact_mcnemar_test(n10, n01),
    }


def _compute_provenance(master: dict[str, Any]) -> dict[str, Any]:
    """Summarize commit SHAs, raw file digests, call counts, latencies, and schema errors."""
    raw_lines = [
        json.loads(line)
        for line in run_tsr_harness.LIVE_LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    unique_keys: set[tuple[str, str, str, str]] = set()
    calls_by_role: Counter[str] = Counter()
    unique_by_role: Counter[str] = Counter()
    lat_by_model: dict[str, list[int]] = defaultdict(list)

    for rec in raw_lines:
        key = (rec["role"], rec["arm_id"], rec["item_id"], rec["model_id"])
        calls_by_role[rec["role"]] += 1
        if key not in unique_keys:
            unique_keys.add(key)
            unique_by_role[rec["role"]] += 1
        lat_by_model[rec["model_id"]].append(int(rec["latency_ms"]))

    retries_by_role = {
        role: calls_by_role[role] - unique_by_role[role]
        for role in sorted(calls_by_role)
    }

    latency_summary: dict[str, Any] = {}
    for model_id in sorted(lat_by_model):
        lats = sorted(float(x) for x in lat_by_model[model_id])
        n = len(lats)
        total_ms = int(sum(lats))
        latency_summary[model_id] = {
            "calls": n,
            "total_ms": total_ms,
            "total_sec": round(total_ms / 1000.0, 3),
            "mean_ms": round(total_ms / n, 2),
            "median_ms": round(_median(lats), 2),
            "p95_ms": round(_percentile_sorted(lats, 0.95), 2),
            "min_ms": int(lats[0]),
            "max_ms": int(lats[-1]),
        }

    total_latency_ms = sum(int(r["latency_ms"]) for r in raw_lines)
    schema_errors = dict(master.get("schema_error_counts", {}))
    return {
        "prereg_commit_sha": HARNESS_PREREG_SHA,
        "pre_eval_commit_sha": PRE_EVAL_COMMIT_SHA,
        "raw_stage_file_sha256": {
            rel: _sha256_file(REPO_ROOT / rel) for rel in RAW_STAGE_FILES
        },
        "live_calls_total": len(raw_lines),
        "unique_call_keys": len(unique_keys),
        "retry_calls_total": len(raw_lines) - len(unique_keys),
        "calls_by_role": dict(sorted(calls_by_role.items())),
        "unique_calls_by_role": dict(sorted(unique_by_role.items())),
        "retry_calls_by_role": retries_by_role,
        "total_api_latency_ms": total_latency_ms,
        "total_api_latency_sec": round(total_latency_ms / 1000.0, 3),
        "latency_by_model": latency_summary,
        "schema_error_counts": schema_errors,
        "total_schema_errors": sum(int(v) for v in schema_errors.values()),
    }


def _evaluate_stage1(
    cal_items: list[dict[str, Any]],
    s1: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Stage 1 (M1) calibration K01..K17 and K01..K16 vs K17 split."""
    cal_by_id = {x["item_id"]: x for x in cal_items}
    gen_ids = [m for m, _v in providers.GENERATORS]
    arms_out: dict[str, Any] = {}
    consensus_flags_all: dict[str, dict[str, bool]] = {}
    consensus_flags_k16: dict[str, dict[str, bool]] = {}
    per_model_flags: dict[str, dict[str, dict[str, bool]]] = defaultdict(dict)

    for arm_id in ("A0", "A3-1"):
        arm_raw = s1[arm_id]
        items_by_id = {r["item_id"]: r for r in arm_raw["items"]}
        k16_ids = [x["item_id"] for x in cal_items if x["item_id"] != "K17"]
        k16_cons_reached = 0
        k16_cons_correct = 0
        model_correct_all: Counter[str] = Counter()
        model_correct_k16: Counter[str] = Counter()
        misses: list[dict[str, Any]] = []
        consensus_flags_all[arm_id] = {}
        consensus_flags_k16[arm_id] = {}

        for ci in cal_items:
            iid = ci["item_id"]
            row = items_by_id[iid]
            exp = ci["expected_book_ruling"]
            ok = bool(row["consensus_correct"])
            consensus_flags_all[arm_id][iid] = ok
            if iid != "K17":
                consensus_flags_k16[arm_id][iid] = ok
                if row["consensus_4_of_5"]:
                    k16_cons_reached += 1
                    if ok:
                        k16_cons_correct += 1

            for m in gen_ids:
                m_ok = row["votes"][m] == exp
                per_model_flags[m].setdefault(arm_id, {})[iid] = m_ok
                if m_ok:
                    model_correct_all[m] += 1
                    if iid != "K17":
                        model_correct_k16[m] += 1

            if not ok or row["schema_errors"]:
                misses.append(
                    {
                        "item_id": iid,
                        "description": ci["description"],
                        "expected_book_ruling": exp,
                        "majority_ruling": row["majority_ruling"],
                        "majority_count": row["majority_count"],
                        "consensus_4_of_5": row["consensus_4_of_5"],
                        "consensus_correct": ok,
                        "votes": row["votes"],
                        "schema_errors": row["schema_errors"],
                    }
                )

        k17_row = items_by_id["K17"]
        arms_out[arm_id] = {
            "total_items": len(cal_items),
            "consensus_4_of_5_count": arm_raw["consensus_4_of_5_count"],
            "consensus_exact_match_count": arm_raw["consensus_exact_match_count"],
            "consensus_accuracy_all_17": round(arm_raw["consensus_exact_match_count"] / 17.0, 6),
            "schema_error_count": arm_raw["schema_error_count"],
            "per_model_schema_errors": arm_raw["per_model_schema_errors"],
            "per_model_correct_all_17": {m: model_correct_all[m] for m in gen_ids},
            "per_model_accuracy_all_17": {
                m: round(model_correct_all[m] / 17.0, 6) for m in gen_ids
            },
            "k01_k16_subset": {
                "total_items": len(k16_ids),
                "consensus_4_of_5_count": k16_cons_reached,
                "consensus_exact_match_count": k16_cons_correct,
                "consensus_accuracy": round(k16_cons_correct / 16.0, 6),
                "per_model_correct": {m: model_correct_k16[m] for m in gen_ids},
                "per_model_accuracy": {
                    m: round(model_correct_k16[m] / 16.0, 6) for m in gen_ids
                },
            },
            "k17_boyle_law": {
                "item_id": "K17",
                "description": cal_by_id["K17"]["description"],
                "expected_book_ruling": cal_by_id["K17"]["expected_book_ruling"],
                "majority_ruling": k17_row["majority_ruling"],
                "majority_count": k17_row["majority_count"],
                "consensus_4_of_5": k17_row["consensus_4_of_5"],
                "consensus_correct": k17_row["consensus_correct"],
                "votes": k17_row["votes"],
            },
            "misses_and_schema_error_items": misses,
        }

    all_ids = [x["item_id"] for x in cal_items]
    k16_ids = [x["item_id"] for x in cal_items if x["item_id"] != "K17"]
    a0_c17 = arms_out["A0"]["consensus_exact_match_count"]
    a3_c17 = arms_out["A3-1"]["consensus_exact_match_count"]
    a0_c16 = arms_out["A0"]["k01_k16_subset"]["consensus_exact_match_count"]
    a3_c16 = arms_out["A3-1"]["k01_k16_subset"]["consensus_exact_match_count"]

    comparison = {
        "all_17_mcnemar": _mcnemar_from_paired_bools(
            all_ids, consensus_flags_all["A0"], consensus_flags_all["A3-1"]
        ),
        "k01_k16_mcnemar": _mcnemar_from_paired_bools(
            k16_ids, consensus_flags_k16["A0"], consensus_flags_k16["A3-1"]
        ),
        "all_17_fisher": exact_stats.exact_fisher_2x2(
            a0_c17, 17 - a0_c17, a3_c17, 17 - a3_c17
        ),
        "k01_k16_fisher": exact_stats.exact_fisher_2x2(
            a0_c16, 16 - a0_c16, a3_c16, 16 - a3_c16
        ),
        "per_model_mcnemar_all_17": {
            m: _mcnemar_from_paired_bools(
                all_ids, per_model_flags[m]["A0"], per_model_flags[m]["A3-1"]
            )
            for m in gen_ids
        },
    }

    csv_rows: list[dict[str, Any]] = []
    for arm_id in ("A0", "A3-1"):
        items_by_id = {r["item_id"]: r for r in s1[arm_id]["items"]}
        for ci in cal_items:
            iid = ci["item_id"]
            row = items_by_id[iid]
            votes = row["votes"]
            csv_rows.append(
                {
                    "arm_id": arm_id,
                    "item_id": iid,
                    "row_num": ci["row_num"],
                    "provenance": ci["provenance"],
                    "expected_book_ruling": ci["expected_book_ruling"],
                    "has_mass_flag": ci["has_mass_flag"],
                    "definition_flag": ci["definition_flag"],
                    "costs_count": ci["costs_count"],
                    "claude_sonnet_4_6": votes["claude-sonnet-4.6"],
                    "gpt_5_4_fast": votes["gpt-5.4-fast"],
                    "gemini_2_5_flash": votes["gemini-2.5-flash"],
                    "mistral_medium_3_5": votes["mistral-medium-3.5"],
                    "llama_4_maverick": votes["llama-4-maverick"],
                    "majority_ruling": row["majority_ruling"],
                    "majority_count": row["majority_count"],
                    "consensus_4_of_5": row["consensus_4_of_5"],
                    "consensus_correct": row["consensus_correct"],
                    "schema_error_models": ";".join(sorted(row["schema_errors"].keys())),
                }
            )

    summary = {"arms": arms_out, "a0_vs_a3_1_comparison": comparison}
    return summary, csv_rows


def _evaluate_stage2(
    heldout_items: list[dict[str, Any]],
    s2: dict[str, Any],
    la: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate Stage 2 (M2) consensus rulings, Core/Boundary strata, and Layer A."""
    gen_ids = [m for m, _v in providers.GENERATORS]
    held_ids = [x["item_id"] for x in heldout_items]
    arms_out: dict[str, Any] = {}
    ki_flags: dict[str, dict[str, bool]] = {}
    la_item_flags: dict[str, dict[str, bool]] = {}

    for arm_id in ("A0", "A3-1"):
        arm_s2 = s2[arm_id]
        arm_la = la[arm_id]
        items_by_id = {r["item_id"]: r for r in arm_s2["items"]}
        ki_flags[arm_id] = {}
        la_item_flags[arm_id] = {}

        strat_counts: dict[str, Counter[str]] = {
            "Core": Counter(),
            "Boundary": Counter(),
        }
        strat_cons_counts: Counter[str] = Counter()
        non_cons_ids: list[str] = []
        ruling_with_nocons: Counter[str] = Counter()
        model_agree_cons: Counter[str] = Counter()
        model_agree_maj: Counter[str] = Counter()
        schema_err_items: list[dict[str, Any]] = []
        voter_la_passes = 0
        voter_la_total = 0

        for row in arm_s2["items"]:
            iid = row["item_id"]
            strat = row["stratum"]
            c4 = bool(row["consensus_4_of_5"])
            maj = row["majority_ruling"]
            eff = maj if c4 else "no_consensus"
            ruling_with_nocons[eff] += 1
            strat_counts[strat][eff] += 1
            if c4:
                strat_cons_counts[strat] += 1
            else:
                non_cons_ids.append(iid)

            is_ki = c4 and maj in ("keep", "invert")
            ki_flags[arm_id][iid] = is_ki
            if is_ki:
                canon = row["canonical_model"]
                la_item_flags[arm_id][iid] = bool(row["per_voter_layer_a"][canon]["passed"])
                for _m, la_res in row["per_voter_layer_a"].items():
                    voter_la_total += 1
                    if la_res.get("passed"):
                        voter_la_passes += 1

            for m in gen_ids:
                if row["votes"][m] == maj:
                    model_agree_maj[m] += 1
                    if c4:
                        model_agree_cons[m] += 1

            if row["schema_errors"]:
                schema_err_items.append(
                    {
                        "item_id": iid,
                        "stratum": strat,
                        "schema_errors": row["schema_errors"],
                    }
                )

        core_ki = strat_counts["Core"]["keep"] + strat_counts["Core"]["invert"]
        bound_ki = strat_counts["Boundary"]["keep"] + strat_counts["Boundary"]["invert"]
        bound_excl = strat_counts["Boundary"]["no partner"] + strat_counts["Boundary"].get(
            "indeterminate", 0
        )
        cons_total = arm_s2["consensus_4_of_5_total"]

        collisions = arm_la["layer_a_collisions"]
        coll_by_layer = Counter(c["layer"] for c in collisions)
        coll_items = sorted({c["item_id"] for c in collisions if "item_id" in c})

        arms_out[arm_id] = {
            "total_items": 40,
            "consensus_4_of_5_total": cons_total,
            "non_consensus_count": len(non_cons_ids),
            "non_consensus_items": sorted(non_cons_ids),
            "ruling_distribution_consensus": {
                "keep": arm_s2["ruling_distribution"].get("keep", 0),
                "invert": arm_s2["ruling_distribution"].get("invert", 0),
                "no partner": arm_s2["ruling_distribution"].get("no partner", 0),
                "indeterminate": arm_s2["ruling_distribution"].get("indeterminate", 0),
            },
            "ruling_distribution_with_no_consensus": dict(ruling_with_nocons),
            "consensus_keep_invert_count": arm_s2["consensus_keep_invert_count"],
            "schema_error_count": arm_s2["schema_error_count"],
            "schema_error_items": schema_err_items,
            "stratified": {
                "Core": {
                    "total_items": 28,
                    "consensus_4_of_5_count": strat_cons_counts["Core"],
                    "keep": strat_counts["Core"]["keep"],
                    "invert": strat_counts["Core"]["invert"],
                    "no_partner": strat_counts["Core"]["no partner"],
                    "indeterminate": strat_counts["Core"].get("indeterminate", 0),
                    "no_consensus": strat_counts["Core"]["no_consensus"],
                    "keep_invert_count": core_ki,
                    "keep_invert_rate_of_28": round(core_ki / 28.0, 6),
                    "keep_invert_rate_of_consensus": round(
                        core_ki / max(1, strat_cons_counts["Core"]), 6
                    ),
                },
                "Boundary": {
                    "total_items": 12,
                    "consensus_4_of_5_count": strat_cons_counts["Boundary"],
                    "keep": strat_counts["Boundary"]["keep"],
                    "invert": strat_counts["Boundary"]["invert"],
                    "no_partner": strat_counts["Boundary"]["no partner"],
                    "indeterminate": strat_counts["Boundary"].get("indeterminate", 0),
                    "no_consensus": strat_counts["Boundary"]["no_consensus"],
                    "keep_invert_count": bound_ki,
                    "exclusion_consensus_count": bound_excl,
                    "exclusion_consensus_rate_of_12": round(bound_excl / 12.0, 6),
                    "false_inclusion_keep_invert_rate": round(bound_ki / 12.0, 6),
                },
                "core_vs_boundary_keep_invert_fisher_p": exact_stats.exact_fisher_2x2(
                    core_ki, 28 - core_ki, bound_ki, 12 - bound_ki
                ),
            },
            "per_model_agreement_with_consensus_34": {
                m: {
                    "agree_count": model_agree_cons[m],
                    "total_consensus": cons_total,
                    "rate": round(model_agree_cons[m] / max(1, cons_total), 6),
                }
                for m in gen_ids
            },
            "per_model_agreement_with_majority_40": {
                m: {
                    "agree_count": model_agree_maj[m],
                    "total_items": 40,
                    "rate": round(model_agree_maj[m] / 40.0, 6),
                }
                for m in gen_ids
            },
            "layer_a": {
                "evaluated_items": arm_la["evaluated_items"],
                "per_item_passed": arm_la["per_item_passed"],
                "per_item_pass_rate": round(
                    arm_la["per_item_passed"] / max(1, arm_la["evaluated_items"]), 6
                ),
                "joint_collisions_count": arm_la["layer_a_collisions_count"],
                "passes_all": arm_la["passes_all"],
                "agreeing_voter_per_item_passes": voter_la_passes,
                "agreeing_voter_per_item_total": voter_la_total,
                "collisions_by_layer": dict(sorted(coll_by_layer.items())),
                "failure_item_ids": coll_items,
                "collisions": collisions,
            },
        }

    # Verify cross-arm consensus parity & paired tests
    consensus_diffs: list[dict[str, Any]] = []
    a0_items = {r["item_id"]: r for r in s2["A0"]["items"]}
    a3_items = {r["item_id"]: r for r in s2["A3-1"]["items"]}
    for iid in held_ids:
        r0 = a0_items[iid]["majority_ruling"] if a0_items[iid]["consensus_4_of_5"] else "no_consensus"
        r3 = a3_items[iid]["majority_ruling"] if a3_items[iid]["consensus_4_of_5"] else "no_consensus"
        if r0 != r3:
            consensus_diffs.append({"item_id": iid, "A0": r0, "A3-1": r3})

    shared_ki_ids = sorted(set(la_item_flags["A0"]) & set(la_item_flags["A3-1"]))
    a0_ki_cnt = arms_out["A0"]["consensus_keep_invert_count"]
    a3_ki_cnt = arms_out["A3-1"]["consensus_keep_invert_count"]
    a0_la_pass = arms_out["A0"]["layer_a"]["per_item_passed"]
    a3_la_pass = arms_out["A3-1"]["layer_a"]["per_item_passed"]
    a0_la_n = arms_out["A0"]["layer_a"]["evaluated_items"]
    a3_la_n = arms_out["A3-1"]["layer_a"]["evaluated_items"]

    comparison = {
        "consensus_ruling_diff_count": len(consensus_diffs),
        "consensus_ruling_diffs": consensus_diffs,
        "keep_invert_shared_ids": shared_ki_ids,
        "keep_invert_mcnemar": _mcnemar_from_paired_bools(
            held_ids, ki_flags["A0"], ki_flags["A3-1"]
        ),
        "keep_invert_fisher_p": exact_stats.exact_fisher_2x2(
            a0_ki_cnt, 40 - a0_ki_cnt, a3_ki_cnt, 40 - a3_ki_cnt
        ),
        "layer_a_per_item_shared_mcnemar": _mcnemar_from_paired_bools(
            shared_ki_ids, la_item_flags["A0"], la_item_flags["A3-1"]
        ),
        "layer_a_per_item_fisher_p": exact_stats.exact_fisher_2x2(
            a0_la_pass, a0_la_n - a0_la_pass, a3_la_pass, a3_la_n - a3_la_pass
        ),
    }

    return {"arms": arms_out, "a0_vs_a3_1_comparison": comparison}


def _evaluate_stage3(s3: dict[str, Any]) -> dict[str, Any]:
    """Evaluate Stage 3 (M3b) adversarial opponent uphold vs. attack rates."""
    arms_out: dict[str, Any] = {}
    uphold_flags: dict[str, dict[str, bool]] = {}

    for arm_id in ("A0", "A3-1"):
        prefix = f"{arm_id}:"
        rows = sorted(
            (k.split(":", 1)[1], v) for k, v in s3.items() if k.startswith(prefix)
        )
        verdict_counts: Counter[str] = Counter()
        attack_type_counts: Counter[str] = Counter()
        attacked_items: list[dict[str, Any]] = []
        uphold_flags[arm_id] = {}

        for iid, rec in rows:
            verdict = rec["verdict"]
            verdict_counts[verdict] += 1
            uphold_flags[arm_id][iid] = verdict == "uphold"
            if verdict == "attack":
                attack_type_counts[rec["attack_type"]] += 1
                attacked_items.append(
                    {
                        "item_id": iid,
                        "attack_type": rec["attack_type"],
                        "critique": rec["critique"],
                        "counterexample_situation": rec["counterexample_situation"],
                    }
                )

        n_eval = len(rows)
        n_up = verdict_counts["uphold"]
        n_att = verdict_counts["attack"]
        arms_out[arm_id] = {
            "evaluated_items": n_eval,
            "uphold_count": n_up,
            "attack_count": n_att,
            "uphold_rate": round(n_up / max(1, n_eval), 6),
            "attack_rate": round(n_att / max(1, n_eval), 6),
            "attack_type_counts": dict(sorted(attack_type_counts.items())),
            "attacked_items": attacked_items,
        }

    shared_ids = sorted(set(uphold_flags["A0"]) & set(uphold_flags["A3-1"]))
    comparison = {
        "shared_items_count": len(shared_ids),
        "fisher_uphold_p": exact_stats.exact_fisher_2x2(
            arms_out["A0"]["uphold_count"],
            arms_out["A0"]["attack_count"],
            arms_out["A3-1"]["uphold_count"],
            arms_out["A3-1"]["attack_count"],
        ),
        "mcnemar_uphold": _mcnemar_from_paired_bools(
            shared_ids, uphold_flags["A0"], uphold_flags["A3-1"]
        ),
    }
    return {"arms": arms_out, "a0_vs_a3_1_comparison": comparison}


def _evaluate_stage4(s4: dict[str, Any]) -> dict[str, Any]:
    """Evaluate Stage 4 (M3c) zero-glossary vertical and horizontal Layer B checks."""
    j1, j2 = (m for m, _v in providers.LAYER_B_JUDGES)
    bool_fields = (
        "coherent_ordinary_english",
        "matches_physical_law_structure",
        "axis_polarity_consistent",
        "nonsensical_or_cipher_like",
    )

    # 4a: Vertical
    vert_arms: dict[str, Any] = {}
    both_coh_flags: dict[str, dict[str, bool]] = {}
    judge_coh_flags: dict[str, dict[str, dict[str, bool]]] = defaultdict(dict)

    for arm_id in ("A0", "A3-1"):
        rows = sorted(
            (r for r in s4["single_vertical"] if r["arm_id"] == arm_id),
            key=lambda r: r["item_id"],
        )
        n = len(rows)
        both_coh_flags[arm_id] = {}
        pairs: list[tuple[str, str]] = []
        both_items: list[str] = []
        non_both_items: list[dict[str, Any]] = []
        at_least_1 = 0

        per_judge_stats: dict[str, Any] = {}
        for jid in (j1, j2):
            judge_coh_flags[jid][arm_id] = {}
            coh_cnt = sum(1 for r in rows if r["judge_verdicts"][jid]["verdict"] == "coherent")
            field_counts = {
                f: sum(1 for r in rows if bool(r["judge_verdicts"][jid][f]))
                for f in bool_fields
            }
            per_judge_stats[jid] = {
                "coherent_count": coh_cnt,
                "incoherent_count": n - coh_cnt,
                "coherent_rate": round(coh_cnt / max(1, n), 6),
                **{f"{f}_count": field_counts[f] for f in bool_fields},
                **{f"{f}_rate": round(field_counts[f] / max(1, n), 6) for f in bool_fields},
            }

        for r in rows:
            iid = r["item_id"]
            v1 = r["judge_verdicts"][j1]["verdict"]
            v2 = r["judge_verdicts"][j2]["verdict"]
            pairs.append((v1, v2))
            judge_coh_flags[j1][arm_id][iid] = v1 == "coherent"
            judge_coh_flags[j2][arm_id][iid] = v2 == "coherent"
            is_both = v1 == "coherent" and v2 == "coherent"
            both_coh_flags[arm_id][iid] = is_both
            if v1 == "coherent" or v2 == "coherent":
                at_least_1 += 1
            if is_both:
                both_items.append(iid)
            else:
                non_both_items.append(
                    {
                        "item_id": iid,
                        "eval_id": r["eval_id"],
                        "description": r["description"],
                        "judge_verdicts": {
                            jid: {
                                "verdict": r["judge_verdicts"][jid]["verdict"],
                                **{f: r["judge_verdicts"][jid][f] for f in bool_fields},
                            }
                            for jid in (j1, j2)
                        },
                    }
                )

        vert_arms[arm_id] = {
            "total_items": n,
            "both_coherent_2_of_2_count": len(both_items),
            "both_coherent_2_of_2_rate": round(len(both_items) / max(1, n), 6),
            "at_least_1_coherent_count": at_least_1,
            "at_least_1_coherent_rate": round(at_least_1 / max(1, n), 6),
            "coherent_2_of_2_items": both_items,
            "cohens_kappa_verdict": round(exact_stats.cohens_kappa(pairs), 6),
            "per_judge": per_judge_stats,
            "non_2_of_2_items": non_both_items,
        }

    shared_v_ids = sorted(set(both_coh_flags["A0"]) & set(both_coh_flags["A3-1"]))
    vert_comp = {
        "shared_items_count": len(shared_v_ids),
        "fisher_2_of_2_coherent_p": exact_stats.exact_fisher_2x2(
            vert_arms["A0"]["both_coherent_2_of_2_count"],
            vert_arms["A0"]["total_items"] - vert_arms["A0"]["both_coherent_2_of_2_count"],
            vert_arms["A3-1"]["both_coherent_2_of_2_count"],
            vert_arms["A3-1"]["total_items"] - vert_arms["A3-1"]["both_coherent_2_of_2_count"],
        ),
        "mcnemar_2_of_2_coherent": _mcnemar_from_paired_bools(
            shared_v_ids, both_coh_flags["A0"], both_coh_flags["A3-1"]
        ),
        "per_judge_comparison": {
            jid: {
                "fisher_p": exact_stats.exact_fisher_2x2(
                    vert_arms["A0"]["per_judge"][jid]["coherent_count"],
                    vert_arms["A0"]["per_judge"][jid]["incoherent_count"],
                    vert_arms["A3-1"]["per_judge"][jid]["coherent_count"],
                    vert_arms["A3-1"]["per_judge"][jid]["incoherent_count"],
                ),
                "mcnemar": _mcnemar_from_paired_bools(
                    shared_v_ids, judge_coh_flags[jid]["A0"], judge_coh_flags[jid]["A3-1"]
                ),
            }
            for jid in (j1, j2)
        },
    }

    # 4b & 4c: Horizontal pairs + Rule 1
    horiz_arms: dict[str, Any] = {}
    for arm_id in ("A0", "A3-1"):
        rows = sorted(
            (r for r in s4["pairs_horizontal"] if r["arm_id"] == arm_id),
            key=lambda r: r["pair_id"],
        )
        n_pairs = len(rows)
        pairs_k: list[tuple[str, str]] = []
        any_c = 0
        two_c = 0
        rule1_same_sit = 0
        rule1_confirmed = 0
        flagged_pairs: list[dict[str, Any]] = []
        per_j_horiz: dict[str, dict[str, Any]] = {}

        for jid in (j1, j2):
            c_cnt = sum(1 for r in rows if r["judge_verdicts"][jid]["verdict"] == "contradiction")
            per_j_horiz[jid] = {
                "compatible_count": n_pairs - c_cnt,
                "contradiction_count": c_cnt,
                "contradiction_rate": round(c_cnt / max(1, n_pairs), 6),
            }

        for r in rows:
            v1 = r["judge_verdicts"][j1]["verdict"]
            v2 = r["judge_verdicts"][j2]["verdict"]
            pairs_k.append((v1, v2))
            if r["two_of_two_contradiction"]:
                two_c += 1
            r1 = r.get("rule1_adjudication")
            if isinstance(r1, dict):
                if r1.get("same_situation"):
                    rule1_same_sit += 1
                if r1.get("confirmed_rule1_collision"):
                    rule1_confirmed += 1
            if v1 == "contradiction" or v2 == "contradiction":
                any_c += 1
                flagged_pairs.append(
                    {
                        "pair_id": r["pair_id"],
                        "item_i": r["item_i"],
                        "item_j": r["item_j"],
                        "shared_terms": r["shared_terms"],
                        "two_of_two_contradiction": r["two_of_two_contradiction"],
                        "rule1_adjudication": r1,
                        "judge_verdicts": {
                            jid: {
                                "verdict": r["judge_verdicts"][jid]["verdict"],
                                "compatible": r["judge_verdicts"][jid]["compatible"],
                                "reason": r["judge_verdicts"][jid]["reason"],
                            }
                            for jid in (j1, j2)
                        },
                    }
                )

        horiz_arms[arm_id] = {
            "total_pairs": n_pairs,
            "any_1_of_2_contradiction_count": any_c,
            "any_1_of_2_contradiction_rate": round(any_c / max(1, n_pairs), 6),
            "two_of_2_contradiction_count": two_c,
            "rule1_same_situation_count": rule1_same_sit,
            "confirmed_rule1_collision_count": rule1_confirmed,
            "cohens_kappa_verdict": round(exact_stats.cohens_kappa(pairs_k), 6),
            "per_judge": per_j_horiz,
            "flagged_any_contradiction_pairs": flagged_pairs,
        }

    horiz_comp = {
        "fisher_confirmed_rule1_p": exact_stats.exact_fisher_2x2(
            horiz_arms["A0"]["confirmed_rule1_collision_count"],
            horiz_arms["A0"]["total_pairs"] - horiz_arms["A0"]["confirmed_rule1_collision_count"],
            horiz_arms["A3-1"]["confirmed_rule1_collision_count"],
            horiz_arms["A3-1"]["total_pairs"] - horiz_arms["A3-1"]["confirmed_rule1_collision_count"],
        ),
        "fisher_any_1_of_2_contradiction_p": exact_stats.exact_fisher_2x2(
            horiz_arms["A0"]["any_1_of_2_contradiction_count"],
            horiz_arms["A0"]["total_pairs"] - horiz_arms["A0"]["any_1_of_2_contradiction_count"],
            horiz_arms["A3-1"]["any_1_of_2_contradiction_count"],
            horiz_arms["A3-1"]["total_pairs"] - horiz_arms["A3-1"]["any_1_of_2_contradiction_count"],
        ),
    }

    return {
        "vertical_single": {"arms": vert_arms, "a0_vs_a3_1_comparison": vert_comp},
        "horizontal_pairs": {"arms": horiz_arms, "a0_vs_a3_1_comparison": horiz_comp},
    }


def _summarize_m4_item_group(
    items: list[dict[str, Any]],
    rater_ids: list[str],
    *,
    include_paired_tests: bool,
) -> dict[str, Any]:
    """Summarize an M4_item group (Core items or Controls) across variants and raters."""
    n_items = len(items)
    n_raters = len(rater_ids)
    n_ratings = n_items * n_raters

    scores_all: dict[str, list[float]] = {v: [] for v in M4_VARIANTS}
    best_counts: Counter[str] = Counter()
    worst_counts: Counter[str] = Counter()
    item_means: dict[str, list[float]] = {v: [] for v in M4_VARIANTS}
    per_rater_scores: dict[str, dict[str, list[float]]] = {
        rid: {v: [] for v in M4_VARIANTS} for rid in rater_ids
    }
    per_rater_best: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}
    per_rater_worst: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}

    best_fleiss_rows: list[list[int]] = []
    worst_fleiss_rows: list[list[int]] = []
    score_fleiss_rows: dict[str, list[list[int]]] = {v: [] for v in M4_VARIANTS}
    var_to_idx = {v: i for i, v in enumerate(M4_VARIANTS)}

    for it in items:
        hk = it["hidden_key"]
        item_v_scores: dict[str, list[float]] = {v: [] for v in M4_VARIANTS}
        b_row = [0, 0, 0, 0]
        w_row = [0, 0, 0, 0]
        s_rows = {v: [0, 0, 0, 0, 0] for v in M4_VARIANTS}

        for rid in rater_ids:
            r = it["ratings"][rid]
            for pos, v in hk.items():
                sc = int(r["scores"][pos])
                scores_all[v].append(float(sc))
                item_v_scores[v].append(float(sc))
                per_rater_scores[rid][v].append(float(sc))
                s_rows[v][sc - 1] += 1
            bv = hk[str(r["best_candidate"])]
            wv = hk[str(r["worst_candidate"])]
            best_counts[bv] += 1
            worst_counts[wv] += 1
            per_rater_best[rid][bv] += 1
            per_rater_worst[rid][wv] += 1
            b_row[var_to_idx[bv]] += 1
            w_row[var_to_idx[wv]] += 1

        for v in M4_VARIANTS:
            item_means[v].append(sum(item_v_scores[v]) / n_raters)
            score_fleiss_rows[v].append(s_rows[v])
        best_fleiss_rows.append(b_row)
        worst_fleiss_rows.append(w_row)

    variants_summary: dict[str, Any] = {}
    for v in M4_VARIANTS:
        vals = scores_all[v]
        b_cnt = best_counts[v]
        w_cnt = worst_counts[v]
        variants_summary[v] = {
            "mean_score": round(sum(vals) / n_ratings, 6),
            "sd_score": round(_sample_sd(vals), 6),
            "median_score": round(_median(vals), 6),
            "min_score": int(min(vals)),
            "max_score": int(max(vals)),
            "best_rank_1_count": b_cnt,
            "best_rank_1_share": round(b_cnt / n_ratings, 6),
            "best_rank_1_binom_gt_0_25_p": exact_stats.exact_binomial_test(
                b_cnt, n_ratings, p0=0.25, alternative="greater"
            ),
            "best_rank_1_binom_two_sided_0_25_p": exact_stats.exact_binomial_test(
                b_cnt, n_ratings, p0=0.25, alternative="two-sided"
            ),
            "worst_rank_4_count": w_cnt,
            "worst_rank_4_share": round(w_cnt / n_ratings, 6),
            "per_rater": {
                rid: {
                    "mean_score": round(sum(per_rater_scores[rid][v]) / n_items, 6),
                    "best_count": per_rater_best[rid][v],
                    "worst_count": per_rater_worst[rid][v],
                }
                for rid in rater_ids
            },
        }

    out: dict[str, Any] = {
        "n_items": n_items,
        "n_raters": n_raters,
        "n_ratings": n_ratings,
        "item_ids": [it["item_id"] for it in items],
        "variants": variants_summary,
        "inter_rater_agreement": {
            "fleiss_kappa_best_variant": round(exact_stats.fleiss_kappa(best_fleiss_rows), 6),
            "fleiss_kappa_worst_variant": round(exact_stats.fleiss_kappa(worst_fleiss_rows), 6),
            "fleiss_kappa_scores_by_variant": {
                v: round(exact_stats.fleiss_kappa(score_fleiss_rows[v]), 6)
                for v in M4_VARIANTS
            },
        },
    }

    if include_paired_tests:
        pairs_to_test = [
            ("T_A0", "T_A3"),
            ("T_A0", "S_syn"),
            ("T_A0", "D_A0"),
            ("S_syn", "T_A3"),
            ("S_syn", "D_A0"),
            ("T_A3", "D_A0"),
        ]
        item_level_tests: dict[str, Any] = {}
        rating_level_tests: dict[str, Any] = {}
        for va, vb in pairs_to_test:
            key = f"{va}_minus_{vb}"
            idiffs = [a - b for a, b in zip(item_means[va], item_means[vb])]
            iwins = sum(1 for d in idiffs if d > 0.0)
            ilosses = sum(1 for d in idiffs if d < 0.0)
            ities = sum(1 for d in idiffs if d == 0.0)
            item_level_tests[key] = {
                "sign_test": exact_stats.exact_sign_test(iwins, ilosses, ities),
                "paired_permutation_test": exact_stats.exact_paired_permutation_test(idiffs),
            }

            rdiffs = [a - b for a, b in zip(scores_all[va], scores_all[vb])]
            rwins = sum(1 for d in rdiffs if d > 0.0)
            rlosses = sum(1 for d in rdiffs if d < 0.0)
            rties = sum(1 for d in rdiffs if d == 0.0)
            rating_level_tests[key] = {
                "sign_test": exact_stats.exact_sign_test(rwins, rlosses, rties),
                "paired_permutation_test": exact_stats.exact_paired_permutation_test(rdiffs),
            }

        out["paired_comparisons_item_level"] = item_level_tests
        out["paired_comparisons_rating_level"] = rating_level_tests

    return out


def _evaluate_stage5(
    s5: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Stage 5 (M4_item Core vs Controls, M4_native_pair, M4_bundle)."""
    rater_ids = [m for m, _v in providers.ROUND2_RATERS]

    # 5a: M4_item (Core separated from R9/R10)
    core_items = [x for x in s5["m4_item"] if x["item_id"] not in CONTROL_IDS]
    ctrl_items = [x for x in s5["m4_item"] if x["item_id"] in CONTROL_IDS]
    core_summary = _summarize_m4_item_group(core_items, rater_ids, include_paired_tests=True)
    ctrl_combined = _summarize_m4_item_group(ctrl_items, rater_ids, include_paired_tests=False)

    ctrl_by_id: dict[str, Any] = {}
    for cit in ctrl_items:
        hk = cit["hidden_key"]
        per_rater_detail: dict[str, Any] = {}
        for rid in rater_ids:
            r = cit["ratings"][rid]
            per_rater_detail[rid] = {
                "scores_by_variant": {v: int(r["scores"][pos]) for pos, v in hk.items()},
                "best_variant": hk[str(r["best_candidate"])],
                "worst_variant": hk[str(r["worst_candidate"])],
            }
        ctrl_by_id[cit["item_id"]] = {
            "summary": _summarize_m4_item_group([cit], rater_ids, include_paired_tests=False),
            "per_rater_detail": per_rater_detail,
        }

    # Build m4_quadruple_ratings.csv rows (72 rows: 18 items x 4 raters)
    m4_csv_rows: list[dict[str, Any]] = []
    for it in s5["m4_item"]:
        iid = it["item_id"]
        is_ctrl = iid in CONTROL_IDS
        hk = it["hidden_key"]
        pos_of = {v: pos for pos, v in hk.items()}
        for rid in rater_ids:
            r = it["ratings"][rid]
            ranks = {hk[str(cand_num)]: idx + 1 for idx, cand_num in enumerate(r["ranking"])}
            m4_csv_rows.append(
                {
                    "item_id": iid,
                    "is_control": is_ctrl,
                    "rater_id": rid,
                    "score_T_A0": r["scores"][pos_of["T_A0"]],
                    "score_T_A3": r["scores"][pos_of["T_A3"]],
                    "score_S_syn": r["scores"][pos_of["S_syn"]],
                    "score_D_A0": r["scores"][pos_of["D_A0"]],
                    "rank_T_A0": ranks["T_A0"],
                    "rank_T_A3": ranks["T_A3"],
                    "rank_S_syn": ranks["S_syn"],
                    "rank_D_A0": ranks["D_A0"],
                    "best_variant": hk[str(r["best_candidate"])],
                    "worst_variant": hk[str(r["worst_candidate"])],
                }
            )

    # 5b: M4_native_pair
    np_items = s5["m4_native_pair"]
    np_a0_scores: list[float] = []
    np_a3_scores: list[float] = []
    np_item_diffs: list[float] = []
    np_wins = Counter()
    np_item_wins = Counter()
    np_fleiss_rows: list[list[int]] = []
    np_per_rater: dict[str, Any] = {
        rid: {"A0_wins": 0, "A3-1_wins": 0, "ties": 0, "a0_scores": [], "a3_scores": []}
        for rid in rater_ids
    }

    for np_it in np_items:
        hk = np_it["hidden_key"]
        a0_pos = "A" if hk["A"] == "A0" else "B"
        a3_pos = "B" if a0_pos == "A" else "A"
        item_a0_s: list[float] = []
        item_a3_s: list[float] = []
        f_row = [0, 0, 0]  # [A0, A3-1, tie]

        for rid in rater_ids:
            r = np_it["ratings"][rid]
            sa0 = float(r[f"score_{a0_pos.lower()}"])
            sa3 = float(r[f"score_{a3_pos.lower()}"])
            np_a0_scores.append(sa0)
            np_a3_scores.append(sa3)
            item_a0_s.append(sa0)
            item_a3_s.append(sa3)
            np_per_rater[rid]["a0_scores"].append(sa0)
            np_per_rater[rid]["a3_scores"].append(sa3)

            pref = r["preferred"]
            winner = "tie" if pref == "tie" else hk[pref]
            np_wins[winner] += 1
            if winner == "A0":
                np_per_rater[rid]["A0_wins"] += 1
                f_row[0] += 1
            elif winner == "A3-1":
                np_per_rater[rid]["A3-1_wins"] += 1
                f_row[1] += 1
            else:
                np_per_rater[rid]["ties"] += 1
                f_row[2] += 1

        np_fleiss_rows.append(f_row)
        diff = (sum(item_a0_s) - sum(item_a3_s)) / len(rater_ids)
        np_item_diffs.append(diff)
        if diff > 0.0:
            np_item_wins["A0"] += 1
        elif diff < 0.0:
            np_item_wins["A3-1"] += 1
        else:
            np_item_wins["tie"] += 1

    np_rating_diffs = [a - b for a, b in zip(np_a0_scores, np_a3_scores)]
    np_summary = {
        "n_items": len(np_items),
        "n_raters": len(rater_ids),
        "n_ratings": len(np_items) * len(rater_ids),
        "item_ids": [x["item_id"] for x in np_items],
        "a0_mean_score": round(sum(np_a0_scores) / len(np_a0_scores), 6),
        "a0_sd_score": round(_sample_sd(np_a0_scores), 6),
        "a3_1_mean_score": round(sum(np_a3_scores) / len(np_a3_scores), 6),
        "a3_1_sd_score": round(_sample_sd(np_a3_scores), 6),
        "fleiss_kappa_preference": round(exact_stats.fleiss_kappa(np_fleiss_rows), 6),
        "rating_level": {
            "a0_wins": np_wins["A0"],
            "a3_1_wins": np_wins["A3-1"],
            "ties": np_wins["tie"],
            "sign_test": exact_stats.exact_sign_test(
                np_wins["A0"], np_wins["A3-1"], np_wins["tie"]
            ),
            "paired_permutation_test": exact_stats.exact_paired_permutation_test(np_rating_diffs),
        },
        "item_level": {
            "a0_mean_wins": np_item_wins["A0"],
            "a3_1_mean_wins": np_item_wins["A3-1"],
            "ties": np_item_wins["tie"],
            "sign_test": exact_stats.exact_sign_test(
                np_item_wins["A0"], np_item_wins["A3-1"], np_item_wins["tie"]
            ),
            "paired_permutation_test": exact_stats.exact_paired_permutation_test(np_item_diffs),
        },
        "per_rater": {
            rid: {
                "a0_wins": d["A0_wins"],
                "a3_1_wins": d["A3-1_wins"],
                "ties": d["ties"],
                "a0_mean_score": round(sum(d["a0_scores"]) / len(d["a0_scores"]), 6),
                "a3_1_mean_score": round(sum(d["a3_scores"]) / len(d["a3_scores"]), 6),
            }
            for rid, d in np_per_rater.items()
        },
    }

    # 5c: M4_bundle
    bundle_rows = s5["m4_bundle"]
    b_scores: dict[str, list[float]] = {v: [] for v in M4_VARIANTS}
    b_ranks: dict[str, list[int]] = {v: [] for v in M4_VARIANTS}
    b_best: Counter[str] = Counter()
    b_worst: Counter[str] = Counter()
    b_by_perm: dict[str, Any] = {}
    b_by_rater: dict[str, dict[str, list[float]]] = {
        rid: {v: [] for v in M4_VARIANTS} for rid in rater_ids
    }
    b_rater_best: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}
    b_rater_worst: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}
    b_perm_fleiss_rows: list[list[int]] = []
    var_to_idx = {v: i for i, v in enumerate(M4_VARIANTS)}

    for b in bundle_rows:
        hk = b["hidden_key"]
        p_idx = b["perm_idx"]
        p_scores: dict[str, list[float]] = {v: [] for v in M4_VARIANTS}
        p_best: Counter[str] = Counter()
        p_worst: Counter[str] = Counter()
        f_row = [0, 0, 0, 0]
        p_detail: dict[str, Any] = {}

        for rid in rater_ids:
            r = b["ratings"][rid]
            vscores = {v: int(r["scores"][pos]) for pos, v in hk.items()}
            vranks = {hk[str(sys_num)]: idx + 1 for idx, sys_num in enumerate(r["ranking"])}
            bv = hk[str(r["best_system"])]
            wv = hk[str(r["worst_system"])]
            b_best[bv] += 1
            b_worst[wv] += 1
            p_best[bv] += 1
            p_worst[wv] += 1
            b_rater_best[rid][bv] += 1
            b_rater_worst[rid][wv] += 1
            f_row[var_to_idx[bv]] += 1
            for v in M4_VARIANTS:
                b_scores[v].append(float(vscores[v]))
                b_ranks[v].append(vranks[v])
                p_scores[v].append(float(vscores[v]))
                b_by_rater[rid][v].append(float(vscores[v]))
            p_detail[rid] = {
                "scores": vscores,
                "best_system": bv,
                "worst_system": wv,
            }

        b_perm_fleiss_rows.append(f_row)
        b_by_perm[f"perm_{p_idx}"] = {
            "mean_scores": {v: round(sum(p_scores[v]) / len(rater_ids), 6) for v in M4_VARIANTS},
            "best_counts": {v: p_best[v] for v in M4_VARIANTS},
            "worst_counts": {v: p_worst[v] for v in M4_VARIANTS},
            "per_rater": p_detail,
        }

    bundle_systems: dict[str, Any] = {}
    n_b_calls = len(bundle_rows) * len(rater_ids)
    for v in M4_VARIANTS:
        vals = b_scores[v]
        ranks = b_ranks[v]
        bundle_systems[v] = {
            "mean_score": round(sum(vals) / n_b_calls, 6),
            "sd_score": round(_sample_sd(vals), 6),
            "median_score": round(_median(vals), 6),
            "mean_rank": round(sum(ranks) / n_b_calls, 6),
            "best_system_count": b_best[v],
            "best_system_share": round(b_best[v] / n_b_calls, 6),
            "worst_system_count": b_worst[v],
            "worst_system_share": round(b_worst[v] / n_b_calls, 6),
            "per_rater_mean_score": {
                rid: round(sum(b_by_rater[rid][v]) / len(bundle_rows), 6) for rid in rater_ids
            },
        }

    bundle_rater_means: dict[str, list[float]] = {
        v: [sum(b_by_rater[rid][v]) / len(bundle_rows) for rid in rater_ids]
        for v in M4_VARIANTS
    }
    bundle_paired_call: dict[str, Any] = {}
    bundle_paired_rater: dict[str, Any] = {}
    for va, vb in (("T_A0", "T_A3"), ("T_A0", "S_syn"), ("T_A0", "D_A0")):
        key = f"{va}_minus_{vb}"
        cdiffs = [a - b for a, b in zip(b_scores[va], b_scores[vb])]
        bundle_paired_call[key] = {
            "sign_test": exact_stats.exact_sign_test(
                sum(1 for d in cdiffs if d > 0.0),
                sum(1 for d in cdiffs if d < 0.0),
                sum(1 for d in cdiffs if d == 0.0),
            ),
            "paired_permutation_test": exact_stats.exact_paired_permutation_test(cdiffs),
        }
        rdiffs = [a - b for a, b in zip(bundle_rater_means[va], bundle_rater_means[vb])]
        bundle_paired_rater[key] = {
            "sign_test": exact_stats.exact_sign_test(
                sum(1 for d in rdiffs if d > 0.0),
                sum(1 for d in rdiffs if d < 0.0),
                sum(1 for d in rdiffs if d == 0.0),
            ),
            "paired_permutation_test": exact_stats.exact_paired_permutation_test(rdiffs),
        }

    bundle_summary = {
        "n_permutations": len(bundle_rows),
        "n_raters": len(rater_ids),
        "n_calls": n_b_calls,
        "systems": bundle_systems,
        "fleiss_kappa_best_system_across_perms": round(
            exact_stats.fleiss_kappa(b_perm_fleiss_rows), 6
        ),
        "order_stability_by_perm": b_by_perm,
        "per_rater_totals": {
            rid: {
                "best_counts": {v: b_rater_best[rid][v] for v in M4_VARIANTS},
                "worst_counts": {v: b_rater_worst[rid][v] for v in M4_VARIANTS},
                "mean_scores": {
                    v: round(sum(b_by_rater[rid][v]) / len(bundle_rows), 6) for v in M4_VARIANTS
                },
            }
            for rid in rater_ids
        },
        "paired_comparisons_call_level": bundle_paired_call,
        "paired_comparisons_rater_level": bundle_paired_rater,
    }

    summary = {
        "m4_item_core": core_summary,
        "m4_item_controls": {
            "combined": ctrl_combined,
            "by_item": ctrl_by_id,
        },
        "m4_native_pair": np_summary,
        "m4_bundle": bundle_summary,
    }
    return summary, m4_csv_rows


def _evaluate_stage6(
    s6: dict[str, Any],
    arm_a0: arms_v2.ArmConfigV2,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Stage 6 (M5) leak-free vocabulary-free slot convergence."""
    gen_ids = [m for m, _v in providers.GENERATORS]
    slots_data = s6["slots"]
    per_slot: dict[str, Any] = {}
    csv_rows: list[dict[str, Any]] = []

    total_primary_a0_matches = 0
    total_any_cand_a0_matches = 0
    total_primary_s_syn_matches = 0
    exact_primary_hits: list[dict[str, str]] = []
    exact_alt_hits: list[dict[str, str]] = []
    modal_shares: list[float] = []

    for slot in arms_v2.STAGE6_PHYSICAL_SLOTS:
        book_a0 = arm_a0.partner_lookup[slot.lower()]
        s_syn_target = arms_v2.SYNONYM_MAP_CH16[book_a0]
        slot_models = slots_data[slot]

        prim_norm: list[str] = []
        prim_matches_a0 = 0
        any_matches_a0 = 0
        prim_matches_syn = 0
        proposals: dict[str, Any] = {}

        for m in gen_ids:
            rec = slot_models[m]
            prop = rec["proposed_counterpart"].strip()
            alts = [a.strip() for a in rec["alternate_candidates"]]
            prop_l = prop.lower()
            alts_l = [a.lower() for a in alts]
            prim_norm.append(prop_l)

            is_prim_a0 = prop_l == book_a0.lower()
            is_alt_a0 = book_a0.lower() in alts_l
            is_prim_syn = prop_l == s_syn_target.lower()
            if is_prim_a0:
                prim_matches_a0 += 1
                total_primary_a0_matches += 1
                exact_primary_hits.append(
                    {"slot": slot, "model_id": m, "proposed": prop, "book_a0_partner": book_a0}
                )
            elif is_alt_a0:
                exact_alt_hits.append(
                    {"slot": slot, "model_id": m, "proposed": prop, "book_a0_partner": book_a0}
                )
            if is_prim_a0 or is_alt_a0:
                any_matches_a0 += 1
                total_any_cand_a0_matches += 1
            if is_prim_syn:
                prim_matches_syn += 1
                total_primary_s_syn_matches += 1

            proposals[m] = {
                "proposed_counterpart": prop,
                "alternate_candidates": alts,
                "exact_a0_primary": is_prim_a0,
                "exact_a0_in_alternates": is_alt_a0,
            }

        counts = Counter(prim_norm)
        top_count = counts.most_common(1)[0][1]
        tied_modals = [w for w, c in counts.items() if c == top_count]
        modal_word = tied_modals[0]
        modal_share = top_count / len(gen_ids)
        modal_shares.append(modal_share)

        per_slot[slot] = {
            "book_a0_partner": book_a0,
            "s_syn_partner": s_syn_target,
            "exact_a0_primary_matches": prim_matches_a0,
            "exact_a0_any_candidate_matches": any_matches_a0,
            "exact_s_syn_primary_matches": prim_matches_syn,
            "unique_primary_proposals_count": len(counts),
            "modal_word": modal_word,
            "modal_tied_candidates": tied_modals,
            "modal_count": top_count,
            "modal_share": round(modal_share, 6),
            "proposals": proposals,
        }

        csv_rows.append(
            {
                "physical_slot": slot,
                "book_a0_partner": book_a0,
                "s_syn_partner": s_syn_target,
                "claude_sonnet_4_6_primary": slot_models["claude-sonnet-4.6"]["proposed_counterpart"],
                "claude_sonnet_4_6_alternates": " | ".join(
                    slot_models["claude-sonnet-4.6"]["alternate_candidates"]
                ),
                "gpt_5_4_fast_primary": slot_models["gpt-5.4-fast"]["proposed_counterpart"],
                "gpt_5_4_fast_alternates": " | ".join(
                    slot_models["gpt-5.4-fast"]["alternate_candidates"]
                ),
                "gemini_2_5_flash_primary": slot_models["gemini-2.5-flash"]["proposed_counterpart"],
                "gemini_2_5_flash_alternates": " | ".join(
                    slot_models["gemini-2.5-flash"]["alternate_candidates"]
                ),
                "mistral_medium_3_5_primary": slot_models["mistral-medium-3.5"]["proposed_counterpart"],
                "mistral_medium_3_5_alternates": " | ".join(
                    slot_models["mistral-medium-3.5"]["alternate_candidates"]
                ),
                "llama_4_maverick_primary": slot_models["llama-4-maverick"]["proposed_counterpart"],
                "llama_4_maverick_alternates": " | ".join(
                    slot_models["llama-4-maverick"]["alternate_candidates"]
                ),
                "exact_a0_matches": prim_matches_a0,
                "exact_a0_any_candidate_matches": any_matches_a0,
                "modal_word": modal_word,
                "modal_count": top_count,
                "modal_share": round(modal_share, 6),
            }
        )

    total_calls = len(arms_v2.STAGE6_PHYSICAL_SLOTS) * len(gen_ids)
    summary = {
        "total_slots": len(arms_v2.STAGE6_PHYSICAL_SLOTS),
        "models_per_slot": len(gen_ids),
        "total_proposals": total_calls,
        "exact_a0_primary_matches": total_primary_a0_matches,
        "exact_a0_primary_match_rate": round(total_primary_a0_matches / total_calls, 6),
        "exact_a0_any_candidate_matches": total_any_cand_a0_matches,
        "exact_a0_any_candidate_match_rate": round(total_any_cand_a0_matches / total_calls, 6),
        "exact_s_syn_primary_matches": total_primary_s_syn_matches,
        "exact_s_syn_primary_match_rate": round(total_primary_s_syn_matches / total_calls, 6),
        "mean_modal_agreement_share": round(sum(modal_shares) / len(modal_shares), 6),
        "slots_with_exact_a0_primary_match": sorted({h["slot"] for h in exact_primary_hits}),
        "exact_primary_hits": exact_primary_hits,
        "exact_alternate_only_hits": exact_alt_hits,
        "per_slot": per_slot,
    }
    return summary, csv_rows


def _build_m2_m3_csv_rows(
    heldout_items: list[dict[str, Any]],
    s2: dict[str, Any],
    la: dict[str, Any],
    s3: dict[str, Any],
    s4: dict[str, Any],
    s5: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build 80 flat rows (2 arms x 40 held-out equations) across Stages 2..5."""
    j1, j2 = (m for m, _v in providers.LAYER_B_JUDGES)
    m4_item_ids = {x["item_id"] for x in s5["m4_item"]}
    m4_native_ids = {x["item_id"] for x in s5["m4_native_pair"]}
    single_by_key = {
        (r["arm_id"], r["item_id"]): r for r in s4["single_vertical"]
    }

    rows: list[dict[str, Any]] = []
    for arm_id in ("A0", "A3-1"):
        s2_by_id = {r["item_id"]: r for r in s2[arm_id]["items"]}
        joint_colls_by_id: dict[str, list[str]] = defaultdict(list)
        for c in la[arm_id]["layer_a_collisions"]:
            if "item_id" in c:
                joint_colls_by_id[c["item_id"]].append(c["layer"])
            elif "variants" in c:
                for iid_list in c["variants"].values():
                    for iid in iid_list:
                        joint_colls_by_id[iid].append(f"{c['layer']}({c.get('physical', '')})")

        for hi in heldout_items:
            iid = hi["item_id"]
            r2 = s2_by_id[iid]
            votes = r2["votes"]
            c4 = bool(r2["consensus_4_of_5"])
            maj = r2["majority_ruling"]
            canon = r2["canonical_model"] or ""
            is_ki = c4 and maj in ("keep", "invert")

            if is_ki:
                per_item_la_passed: Any = bool(r2["per_voter_layer_a"][canon]["passed"])
                joint_la_passed: Any = iid not in joint_colls_by_id
                la_failures = ";".join(sorted(set(joint_colls_by_id.get(iid, []))))
            else:
                per_item_la_passed = ""
                joint_la_passed = ""
                la_failures = ""

            opp = s3.get(f"{arm_id}:{iid}")
            m3b_verdict = opp["verdict"] if opp else ""
            m3b_attack = opp["attack_type"] if opp else ""

            sv = single_by_key.get((arm_id, iid))
            if sv:
                v_j1 = sv["judge_verdicts"][j1]["verdict"]
                v_j2 = sv["judge_verdicts"][j2]["verdict"]
                both_2_of_2: Any = v_j1 == "coherent" and v_j2 == "coherent"
            else:
                v_j1 = ""
                v_j2 = ""
                both_2_of_2 = ""

            rows.append(
                {
                    "arm_id": arm_id,
                    "item_id": iid,
                    "stratum": hi["stratum"],
                    "overlaps_legacy_extension_test": hi["overlaps_legacy_extension_test"],
                    "claude_sonnet_4_6": votes["claude-sonnet-4.6"],
                    "gpt_5_4_fast": votes["gpt-5.4-fast"],
                    "gemini_2_5_flash": votes["gemini-2.5-flash"],
                    "mistral_medium_3_5": votes["mistral-medium-3.5"],
                    "llama_4_maverick": votes["llama-4-maverick"],
                    "majority_ruling": maj,
                    "consensus_4_of_5": c4,
                    "canonical_model": canon,
                    "layer_a_passed": per_item_la_passed,
                    "joint_layer_a_passed": joint_la_passed,
                    "layer_a_failures": la_failures,
                    "m3b_verdict": m3b_verdict,
                    "m3b_attack_type": m3b_attack,
                    "m3c_single_verdict_j1": v_j1,
                    "m3c_single_verdict_j2": v_j2,
                    "m3c_single_2_of_2_coherent": both_2_of_2,
                    "in_m4_item": (arm_id == "A0" and iid in m4_item_ids),
                    "in_m4_native_pair": iid in m4_native_ids,
                }
            )
    return rows


def build_all_artifacts() -> dict[Path, str]:
    """Compute summary_v2.json and all 4 CSVs purely in memory."""
    cal_items = _load_json(prepare_openstax_sample.CALIBRATION_17_PATH)["items"]
    heldout_items = _load_json(prepare_openstax_sample.HELDOUT_40_PATH)["items"]

    s1 = _load_json(OUTPUTS_DIR / "stage1_m1_calibration.json")
    s2 = _load_json(OUTPUTS_DIR / "stage2_m2_heldout.json")
    la = _load_json(OUTPUTS_DIR / "layer_a_summary.json")
    s3 = _load_json(OUTPUTS_DIR / "stage3_m3b_opponent.json")
    s4 = _load_json(OUTPUTS_DIR / "stage4_m3c_layer_b.json")
    s5 = _load_json(OUTPUTS_DIR / "stage5_m4_ratings.json")
    s6 = _load_json(OUTPUTS_DIR / "stage6_m5_vocab_free.json")
    master = _load_json(OUTPUTS_DIR / "summary_all_stages.json")

    arm_a0 = arms_v2.build_arm_v2("A0")

    provenance = _compute_provenance(master)
    stage1_summary, m1_csv_rows = _evaluate_stage1(cal_items, s1)
    stage2_summary = _evaluate_stage2(heldout_items, s2, la)
    stage3_summary = _evaluate_stage3(s3)
    stage4_summary = _evaluate_stage4(s4)
    stage5_summary, m4_csv_rows = _evaluate_stage5(s5)
    stage6_summary, m5_csv_rows = _evaluate_stage6(s6, arm_a0)
    m2_m3_csv_rows = _build_m2_m3_csv_rows(heldout_items, s2, la, s3, s4, s5)

    m4_core = stage5_summary["m4_item_core"]
    m4_np = stage5_summary["m4_native_pair"]
    m4_bun = stage5_summary["m4_bundle"]

    named_pvalues: list[tuple[str, float]] = [
        ("M1_A0_vs_A3_1_cal17_mcnemar", stage1_summary["a0_vs_a3_1_comparison"]["all_17_mcnemar"]["p_value"]),
        ("M2_Core_vs_Boundary_A0_fisher", stage2_summary["arms"]["A0"]["stratified"]["core_vs_boundary_keep_invert_fisher_p"]),
        ("M2_LayerA_A0_vs_A3_1_mcnemar", stage2_summary["a0_vs_a3_1_comparison"]["layer_a_per_item_shared_mcnemar"]["p_value"]),
        ("M3b_Opponent_A0_vs_A3_1_mcnemar", stage3_summary["a0_vs_a3_1_comparison"]["mcnemar_uphold"]["p_value"]),
        ("M3c_Vertical_A0_vs_A3_1_mcnemar", stage4_summary["vertical_single"]["a0_vs_a3_1_comparison"]["mcnemar_2_of_2_coherent"]["p_value"]),
        ("M3c_Horizontal_A0_vs_A3_1_rule1_fisher", stage4_summary["horizontal_pairs"]["a0_vs_a3_1_comparison"]["fisher_confirmed_rule1_p"]),
        ("M4_item_Core_T_A0_vs_T_A3_item_perm", m4_core["paired_comparisons_item_level"]["T_A0_minus_T_A3"]["paired_permutation_test"]["p_value"]),
        ("M4_item_Core_T_A0_vs_S_syn_item_perm", m4_core["paired_comparisons_item_level"]["T_A0_minus_S_syn"]["paired_permutation_test"]["p_value"]),
        ("M4_item_Core_T_A0_vs_D_A0_item_perm", m4_core["paired_comparisons_item_level"]["T_A0_minus_D_A0"]["paired_permutation_test"]["p_value"]),
        ("M4_item_Core_T_A0_best_gt_0_25_binom", m4_core["variants"]["T_A0"]["best_rank_1_binom_gt_0_25_p"]),
        ("M4_native_pair_A0_vs_A3_1_item_perm", m4_np["item_level"]["paired_permutation_test"]["p_value"]),
        ("M4_bundle_T_A0_vs_T_A3_call_perm", m4_bun["paired_comparisons_call_level"]["T_A0_minus_T_A3"]["paired_permutation_test"]["p_value"]),
    ]

    summary_payload = {
        "schema_version": "tsr_eval_summary_v2",
        "provenance": provenance,
        "stage1_m1": stage1_summary,
        "stage2_m2": stage2_summary,
        "stage3_m3b": stage3_summary,
        "stage4_m3c": stage4_summary,
        "stage5_m4": stage5_summary,
        "stage6_m5": stage6_summary,
        "holm_bonferroni_family": exact_stats.holm_bonferroni(named_pvalues),
    }

    m1_fields = [
        "arm_id",
        "item_id",
        "row_num",
        "provenance",
        "expected_book_ruling",
        "has_mass_flag",
        "definition_flag",
        "costs_count",
        "claude_sonnet_4_6",
        "gpt_5_4_fast",
        "gemini_2_5_flash",
        "mistral_medium_3_5",
        "llama_4_maverick",
        "majority_ruling",
        "majority_count",
        "consensus_4_of_5",
        "consensus_correct",
        "schema_error_models",
    ]
    m2_m3_fields = [
        "arm_id",
        "item_id",
        "stratum",
        "overlaps_legacy_extension_test",
        "claude_sonnet_4_6",
        "gpt_5_4_fast",
        "gemini_2_5_flash",
        "mistral_medium_3_5",
        "llama_4_maverick",
        "majority_ruling",
        "consensus_4_of_5",
        "canonical_model",
        "layer_a_passed",
        "joint_layer_a_passed",
        "layer_a_failures",
        "m3b_verdict",
        "m3b_attack_type",
        "m3c_single_verdict_j1",
        "m3c_single_verdict_j2",
        "m3c_single_2_of_2_coherent",
        "in_m4_item",
        "in_m4_native_pair",
    ]
    m4_fields = [
        "item_id",
        "is_control",
        "rater_id",
        "score_T_A0",
        "score_T_A3",
        "score_S_syn",
        "score_D_A0",
        "rank_T_A0",
        "rank_T_A3",
        "rank_S_syn",
        "rank_D_A0",
        "best_variant",
        "worst_variant",
    ]
    m5_fields = [
        "physical_slot",
        "book_a0_partner",
        "s_syn_partner",
        "claude_sonnet_4_6_primary",
        "claude_sonnet_4_6_alternates",
        "gpt_5_4_fast_primary",
        "gpt_5_4_fast_alternates",
        "gemini_2_5_flash_primary",
        "gemini_2_5_flash_alternates",
        "mistral_medium_3_5_primary",
        "mistral_medium_3_5_alternates",
        "llama_4_maverick_primary",
        "llama_4_maverick_alternates",
        "exact_a0_matches",
        "exact_a0_any_candidate_matches",
        "modal_word",
        "modal_count",
        "modal_share",
    ]

    return {
        SUMMARY_V2_PATH: json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n",
        CSV_M1_PATH: _render_csv_text(m1_fields, m1_csv_rows),
        CSV_M2_M3_PATH: _render_csv_text(m2_m3_fields, m2_m3_csv_rows),
        CSV_M4_PATH: _render_csv_text(m4_fields, m4_csv_rows),
        CSV_M5_PATH: _render_csv_text(m5_fields, m5_csv_rows),
    }


def _git_output(*args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _verify_markdown_links(md_path: Path) -> list[str]:
    if not md_path.exists():
        return [f"Missing markdown file: {md_path.relative_to(REPO_ROOT)}"]
    text = md_path.read_text(encoding="utf-8")
    errors: list[str] = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (md_path.parent / target).resolve()
        if not resolved.exists():
            errors.append(
                f"Broken relative markdown link in {md_path.relative_to(REPO_ROOT)}: {target!r}"
            )
    return errors


def _verify_git_provenance() -> dict[str, Any]:
    """Verify Commit 1, Commit 2, and Commit 3 immutability via git."""
    head_sha = _git_output("rev-parse", "HEAD")
    commit1_tree = set(_git_output("ls-tree", "-r", "--name-only", HARNESS_PREREG_SHA).splitlines())
    commit2_tree = set(_git_output("ls-tree", "-r", "--name-only", PRE_EVAL_COMMIT_SHA).splitlines())

    forbidden_in_c1_prefixes = ("harness/logs/", "harness/outputs/")
    eval_paths = {
        "harness/exact_stats.py",
        "harness/evaluate_tsr_harness.py",
        "harness/RESULTS.md",
    }
    for p in commit1_tree:
        if p.startswith(forbidden_in_c1_prefixes) or p in eval_paths:
            raise RuntimeError(f"Commit 1 ({HARNESS_PREREG_SHA}) unexpectedly contains {p}")
    for p in eval_paths:
        if p in commit2_tree:
            raise RuntimeError(f"Commit 2 ({PRE_EVAL_COMMIT_SHA}) unexpectedly contains {p}")

    commit1_files = tuple(sorted(f"harness/{rel}" for rel in run_tsr_harness.COMMIT1_ALLOWED_REL_PATHS))
    immutable_files = (*commit1_files, *RAW_STAGE_FILES)

    if head_sha == PRE_EVAL_COMMIT_SHA:
        if _git_output("rev-parse", "HEAD~1") != HARNESS_PREREG_SHA:
            raise RuntimeError(f"Expected HEAD~1 == {HARNESS_PREREG_SHA}")
        mode = "pre_commit_3"
    else:
        if _git_output("rev-parse", "HEAD~1") != PRE_EVAL_COMMIT_SHA:
            raise RuntimeError(
                f"Expected HEAD~1 == {PRE_EVAL_COMMIT_SHA}, got {_git_output('rev-parse', 'HEAD~1')}"
            )
        if _git_output("rev-parse", "HEAD~2") != HARNESS_PREREG_SHA:
            raise RuntimeError(
                f"Expected HEAD~2 == {HARNESS_PREREG_SHA}, got {_git_output('rev-parse', 'HEAD~2')}"
            )
        mode = "post_commit_3"

    # Assert every Commit-1 and Commit-2 raw file blob matches PRE_EVAL_COMMIT_SHA on disk and at HEAD
    for rel in immutable_files:
        expected_blob = _git_output("rev-parse", f"{PRE_EVAL_COMMIT_SHA}:{rel}")
        disk_blob = _git_output("hash-object", rel)
        if disk_blob != expected_blob:
            raise RuntimeError(f"Working tree file {rel} modified vs {PRE_EVAL_COMMIT_SHA}")
        if mode == "post_commit_3":
            head_blob = _git_output("rev-parse", f"HEAD:{rel}")
            if head_blob != expected_blob:
                raise RuntimeError(f"HEAD blob for {rel} modified vs {PRE_EVAL_COMMIT_SHA}")

    return {
        "git_mode": mode,
        "head_sha": head_sha,
        "prereg_sha_verified": HARNESS_PREREG_SHA,
        "pre_eval_sha_verified": PRE_EVAL_COMMIT_SHA,
        "immutable_blobs_verified": len(immutable_files),
    }


def write_outputs() -> dict[str, Any]:
    """Generate and write `summary_v2.json` and the 4 summary CSVs."""
    artifacts = build_all_artifacts()
    written: dict[str, int] = {}
    for path, content in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))
        written[str(path.relative_to(REPO_ROOT))] = len(content.encode("utf-8"))
    return {"write_outputs": "OK", "bytes_written": written}


def verify_offline() -> dict[str, Any]:
    """Verify exact byte-for-byte parity, hygiene, self-tests, markdown links, and git history."""
    hygiene_errors = run_tsr_harness.check_repo_hygiene(allow_live_artifacts=True)
    if hygiene_errors:
        raise RuntimeError("Hygiene check failed:\n- " + "\n- ".join(hygiene_errors))

    openstax_res = prepare_openstax_sample.run_verify_offline()
    arms_v2._run_self_test()
    exact_stats._run_self_test()
    post_live_res = run_tsr_harness.run_verify_offline_post_live()

    expected_artifacts = build_all_artifacts()
    verified_files: dict[str, str] = {}
    for path, expected_text in expected_artifacts.items():
        if not path.exists():
            raise RuntimeError(f"Missing evaluated artifact: {path.relative_to(REPO_ROOT)}")
        actual_bytes = path.read_bytes()
        expected_bytes = expected_text.encode("utf-8")
        if actual_bytes != expected_bytes:
            raise RuntimeError(
                f"Byte mismatch on {path.relative_to(REPO_ROOT)}: "
                f"disk={len(actual_bytes)}B vs recomputed={len(expected_bytes)}B"
            )
        verified_files[str(path.relative_to(REPO_ROOT))] = hashlib.sha256(actual_bytes).hexdigest()

    link_errors = _verify_markdown_links(run_tsr_harness.PREREG_MD_PATH) + _verify_markdown_links(
        RESULTS_MD_PATH
    )
    if link_errors:
        raise RuntimeError("Markdown link check failed:\n- " + "\n- ".join(link_errors))

    results_txt = RESULTS_MD_PATH.read_text(encoding="utf-8")
    for sha in (HARNESS_PREREG_SHA, PRE_EVAL_COMMIT_SHA):
        if sha not in results_txt:
            raise RuntimeError(f"harness/RESULTS.md missing required commit SHA {sha}")

    git_info: dict[str, Any] = {"git_mode": "no_git_dir"}
    if (REPO_ROOT / ".git").exists():
        git_info = _verify_git_provenance()

    return {
        "verify_offline": "OK",
        "openstax_verify": openstax_res["verify_offline"],
        "post_live_verify": post_live_res["verify_offline"],
        "verified_output_sha256": verified_files,
        "git_provenance": git_info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="TSR v2 offline evaluator and verifier")
    parser.add_argument("--write", action="store_true", help="Write summary_v2.json and 4 CSVs")
    parser.add_argument(
        "--verify-offline",
        action="store_true",
        help="Recompute and assert byte-for-byte parity, self-tests, links, hygiene, and git history",
    )
    args = parser.parse_args()
    if int(bool(args.write)) + int(bool(args.verify_offline)) != 1:
        parser.error("Specify exactly one of --write or --verify-offline")

    if args.write:
        print(json.dumps(write_outputs(), indent=2))
    else:
        print(json.dumps(verify_offline(), indent=2))


if __name__ == "__main__":
    main()
