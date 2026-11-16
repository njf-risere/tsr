#!/usr/bin/env python3
"""Deterministic offline evaluator and verification suite for TSR Deep-v3 (Pillars D1..D4).

Reads frozen Commit-4 preregistration specs and Commit-5 raw logs/outputs, computes
all 6 preregistered confirmatory hypotheses (`H1..H6`) under one family-wise
Holm-Bonferroni correction (`K = 6`, `alpha = 0.05`) plus all prespecified secondary
and exploratory diagnostics, emits `summary_deep_v3.json` and 5 flat CSV tables,
and verifies byte-for-byte reproducibility, hygiene, markdown links, and git lineage.

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

DEEP_V3_DIR = Path(__file__).resolve().parent
HARNESS_DIR = DEEP_V3_DIR.parent
REPO_ROOT = HARNESS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness import arms_v2, evaluate_tsr_harness, exact_stats, providers, run_tsr_harness  # noqa: E402
from harness.deep_v3 import arms_v3, layer_a_v3, run_deep_v3  # noqa: E402
from harness.openstax import prepare_openstax_sample  # noqa: E402

V2_EVAL_SHA = "7ee697ce32e17dd5db329386cb3ce6b6df02b696"
DEEP_V3_PREREG_SHA = "d6f70e2802cb7b55d1871486e83378aaa55d349d"
DEEP_V3_PRE_EVAL_SHA = "502c27c21ea404a138017727d25b96372e5bf0c7"

COMMIT4_V3_FILES: tuple[str, ...] = (
    "harness/deep_v3/PREREGISTRATION_V3.md",
    "harness/deep_v3/__init__.py",
    "harness/deep_v3/arms_v3.py",
    "harness/deep_v3/crossing_battery_20.json",
    "harness/deep_v3/layer_a_v3.py",
    "harness/deep_v3/run_deep_v3.py",
    "harness/evaluate_tsr_harness.py",
)

COMMIT5_V3_FILES: tuple[str, ...] = (
    "harness/deep_v3/logs/live_calls_v3.jsonl",
    "harness/deep_v3/outputs/raw_d1a_web_ratings.json",
    "harness/deep_v3/outputs/raw_d1b_web_truthtable.json",
    "harness/deep_v3/outputs/raw_d2a_crossing_cal17.json",
    "harness/deep_v3/outputs/raw_d2b_crossing_battery20.json",
    "harness/deep_v3/outputs/raw_d3a_narrative_cal17.json",
    "harness/deep_v3/outputs/raw_d3b_passage_ratings.json",
    "harness/deep_v3/outputs/raw_d4_layer_a_audit.json",
    "harness/deep_v3/outputs/summary_deep_v3_raw.json",
)

OUTPUTS_DIR = DEEP_V3_DIR / "outputs"
PREREG_V3_MD_PATH = DEEP_V3_DIR / "PREREGISTRATION_V3.md"
RESULTS_V3_MD_PATH = DEEP_V3_DIR / "RESULTS_DEEP_V3.md"
RESULTS_V2_MD_PATH = HARNESS_DIR / "RESULTS.md"

SUMMARY_V3_PATH = OUTPUTS_DIR / "summary_deep_v3.json"
CSV_D1A_PATH = OUTPUTS_DIR / "d1a_web_bundles.csv"
CSV_D1B_PATH = OUTPUTS_DIR / "d1b_lexical_rigidity.csv"
CSV_D2_PATH = OUTPUTS_DIR / "d2_crossing_regime.csv"
CSV_D3_PATH = OUTPUTS_DIR / "d3_book_prose.csv"
CSV_D4_PATH = OUTPUTS_DIR / "d4_layer_a_v2_vs_v3.csv"

COMMIT6_GENERATED_REL_PATHS: tuple[str, ...] = (
    "harness/deep_v3/evaluate_deep_v3.py",
    "harness/deep_v3/RESULTS_DEEP_V3.md",
    "harness/deep_v3/outputs/summary_deep_v3.json",
    "harness/deep_v3/outputs/d1a_web_bundles.csv",
    "harness/deep_v3/outputs/d1b_lexical_rigidity.csv",
    "harness/deep_v3/outputs/d2_crossing_regime.csv",
    "harness/deep_v3/outputs/d3_book_prose.csv",
    "harness/deep_v3/outputs/d4_layer_a_v2_vs_v3.csv",
)

D1_ARMS: tuple[str, ...] = ("W_A0", "W_Ssyn", "W_Chal", "W_A3")
D3B_VARIANTS: tuple[str, ...] = ("V_A0", "V_Ssyn", "V_A3")
D1_CRITERIA: tuple[str, ...] = ("c1", "c2", "c3", "c4")


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
    return float(s[mid]) if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


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
    """Compute paired 2x2 counts and two-sided exact McNemar test across aligned keys."""
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


def _paired_diffs_stats(vals_a: list[float], vals_b: list[float]) -> dict[str, Any]:
    """Run paired exact permutation and exact sign tests on `vals_a - vals_b`."""
    diffs = [float(a) - float(b) for a, b in zip(vals_a, vals_b)]
    wins = sum(1 for d in diffs if d > 0.0)
    losses = sum(1 for d in diffs if d < 0.0)
    ties = sum(1 for d in diffs if d == 0.0)
    perm = exact_stats.exact_paired_permutation_test(diffs, seed=arms_v3.HARNESS_SEED_V3)
    sign = exact_stats.exact_sign_test(wins, losses, ties)
    return {
        "mean_a": round(sum(vals_a) / max(1, len(vals_a)), 6),
        "mean_b": round(sum(vals_b) / max(1, len(vals_b)), 6),
        "mean_diff": round(perm["mean_diff"], 6),
        "sign_test": sign,
        "paired_permutation_test": perm,
    }


def krippendorff_alpha_ordinal(units_ratings: list[list[int]]) -> float:
    """Compute Krippendorff's alpha for ordinal integer ratings (stdlib only)."""
    units = [u for u in units_ratings if len(u) >= 2]
    if not units:
        return 1.0
    cats = sorted({int(v) for u in units for v in u})
    if len(cats) <= 1:
        return 1.0
    n_c: Counter[int] = Counter(int(v) for u in units for v in u)
    n_total = sum(n_c.values())

    delta2: dict[tuple[int, int], float] = {}
    for i, c in enumerate(cats):
        delta2[(c, c)] = 0.0
        for j in range(i + 1, len(cats)):
            k = cats[j]
            mid_sum = (
                0.5 * n_c[c]
                + sum(n_c[cats[g]] for g in range(i + 1, j))
                + 0.5 * n_c[k]
            )
            d = mid_sum * mid_sum
            delta2[(c, k)] = d
            delta2[(k, c)] = d

    do_sum = 0.0
    for u in units:
        m_u = len(u)
        pair_sum = sum(
            delta2[(int(u[a]), int(u[b]))]
            for a in range(m_u)
            for b in range(m_u)
            if a != b
        )
        do_sum += pair_sum / (m_u - 1)
    d_o = do_sum / n_total

    de_sum = sum(n_c[c] * n_c[k] * delta2[(c, k)] for c in cats for k in cats)
    d_e = de_sum / (n_total * (n_total - 1))
    if d_e == 0.0:
        return 1.0 if d_o == 0.0 else 0.0
    return 1.0 - (d_o / d_e)


def _run_krippendorff_self_test() -> None:
    """Verify Krippendorff's ordinal alpha against Krippendorff (2011) Example C."""
    k2011_ex_c = [
        [1, 1, 1],
        [2, 2, 3, 2],
        [3, 3, 3, 3],
        [3, 3, 3, 3],
        [2, 2, 2, 2],
        [1, 2, 3, 4],
        [4, 4, 4, 4],
        [1, 1, 2, 1],
        [2, 2, 2, 2],
        [5, 5, 5],
        [1, 1],
        [3],
    ]
    alpha = krippendorff_alpha_ordinal(k2011_ex_c)
    assert abs(alpha - 0.8153875037548813) < 1e-12, f"Unexpected ordinal alpha={alpha}"
    assert krippendorff_alpha_ordinal([[3, 3, 3], [3, 3, 3]]) == 1.0


def _load_jsonl_by_key() -> tuple[list[dict[str, Any]], dict[tuple[str, str, str, str], list[dict[str, Any]]]]:
    records = [
        json.loads(line)
        for line in run_deep_v3.LIVE_LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        key = (rec["role"], rec["arm_id"], rec["item_id"], rec["model_id"])
        by_key[key].append(rec)
    return records, by_key


def _compute_provenance(
    log_records: list[dict[str, Any]],
    raw_summary: dict[str, Any],
) -> dict[str, Any]:
    """Summarize commit SHAs, file SHA-256 digests, live calls, retries, and latencies."""
    unique_keys: set[tuple[str, str, str, str]] = set()
    calls_by_role: Counter[str] = Counter()
    unique_by_role: Counter[str] = Counter()
    lat_by_model: dict[str, list[int]] = defaultdict(list)

    for rec in log_records:
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

    total_latency_ms = sum(int(r["latency_ms"]) for r in log_records)
    schema_errors = dict(raw_summary.get("schema_error_counts", {}))
    return {
        "parent_v2_eval_sha": V2_EVAL_SHA,
        "deep_v3_prereg_sha": DEEP_V3_PREREG_SHA,
        "deep_v3_pre_eval_sha": DEEP_V3_PRE_EVAL_SHA,
        "prereg_hashed_files_sha256": {
            **run_deep_v3.compute_hashed_file_digests(),
            "__init__.py": _sha256_file(DEEP_V3_DIR / "__init__.py"),
        },
        "raw_artifact_sha256": {
            rel: _sha256_file(REPO_ROOT / rel) for rel in COMMIT5_V3_FILES
        },
        "live_calls_total": len(log_records),
        "unique_call_keys": len(unique_keys),
        "retry_calls_total": len(log_records) - len(unique_keys),
        "calls_by_role": dict(sorted(calls_by_role.items())),
        "unique_calls_by_role": dict(sorted(unique_by_role.items())),
        "retry_calls_by_role": retries_by_role,
        "total_api_latency_ms": total_latency_ms,
        "total_api_latency_sec": round(total_latency_ms / 1000.0, 3),
        "latency_by_model": latency_summary,
        "schema_error_counts": schema_errors,
        "total_schema_errors": sum(int(v) for v in schema_errors.values()),
    }


def _evaluate_d1a(d1a: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Pillar D1a unlabeled 4-way web slot ratings and physics controls."""
    rater_ids = [m for m, _v in providers.GENERATORS]
    core_specs = {s["slot_id"]: s for s in arms_v3.CORE_WEB_SLOTS_14}
    nc_specs = {c["item_id"]: c for c in arms_v3.NEGATIVE_CONTROL_ITEMS_3}

    core_tasks = [t for t in d1a["tasks"] if t["metadata"]["stratum"] == "Core_Web"]
    nc_tasks = [t for t in d1a["tasks"] if t["metadata"]["stratum"] == "Negative_Control"]

    all_scores: dict[str, list[float]] = {a: [] for a in D1_ARMS}
    slot_means: dict[str, list[float]] = {a: [] for a in D1_ARMS}
    best_counts: Counter[str] = Counter()
    worst_counts: Counter[str] = Counter()
    per_rater_scores: dict[str, dict[str, list[float]]] = {
        rid: {a: [] for a in D1_ARMS} for rid in rater_ids
    }
    per_rater_best: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}
    per_rater_worst: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}

    arm_to_idx = {a: idx for idx, a in enumerate(D1_ARMS)}
    best_fleiss_rows: list[list[int]] = []
    worst_fleiss_rows: list[list[int]] = []
    alpha_units_all: list[list[int]] = []
    alpha_units_by_arm: dict[str, list[list[int]]] = {a: [] for a in D1_ARMS}
    per_slot_breakdown: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    for task in core_tasks:
        sid = task["task_id"]
        spec = core_specs[sid]
        slot_scores: dict[str, list[int]] = {a: [] for a in D1_ARMS}
        slot_best: Counter[str] = Counter()
        slot_worst: Counter[str] = Counter()
        brow = [0, 0, 0, 0]
        wrow = [0, 0, 0, 0]

        for rid in rater_ids:
            entry = task["by_model"][rid]
            hk = entry["call_meta"]["hidden_key"]
            parsed = entry["parsed"]
            inv = {arm: pos for pos, arm in hk.items()}
            ranks = {hk[str(c)]: idx + 1 for idx, c in enumerate(parsed["ranking"])}

            for arm in D1_ARMS:
                sc = int(parsed["scores"][inv[arm]])
                slot_scores[arm].append(sc)
                all_scores[arm].append(float(sc))
                per_rater_scores[rid][arm].append(float(sc))

            b_arm = hk[str(parsed["best_candidate"])]
            w_arm = hk[str(parsed["worst_candidate"])]
            best_counts[b_arm] += 1
            worst_counts[w_arm] += 1
            slot_best[b_arm] += 1
            slot_worst[w_arm] += 1
            per_rater_best[rid][b_arm] += 1
            per_rater_worst[rid][w_arm] += 1
            brow[arm_to_idx[b_arm]] += 1
            wrow[arm_to_idx[w_arm]] += 1

            csv_rows.append(
                {
                    "item_id": sid,
                    "stratum": "Core_Web",
                    "rater_id": rid,
                    "word_W_A0": spec["candidates"]["W_A0"],
                    "word_W_Ssyn": spec["candidates"]["W_Ssyn"],
                    "word_W_Chal": spec["candidates"]["W_Chal"],
                    "word_W_A3": spec["candidates"]["W_A3"],
                    "score_W_A0": int(parsed["scores"][inv["W_A0"]]),
                    "score_W_Ssyn": int(parsed["scores"][inv["W_Ssyn"]]),
                    "score_W_Chal": int(parsed["scores"][inv["W_Chal"]]),
                    "score_W_A3": int(parsed["scores"][inv["W_A3"]]),
                    "rank_W_A0": ranks["W_A0"],
                    "rank_W_Ssyn": ranks["W_Ssyn"],
                    "rank_W_Chal": ranks["W_Chal"],
                    "rank_W_A3": ranks["W_A3"],
                    "score_nc_correct": "",
                    "score_nc_wrong_condition": "",
                    "score_nc_spatial_error": "",
                    "score_nc_vague_generic": "",
                    "best_label": b_arm,
                    "worst_label": w_arm,
                    "best_word": spec["candidates"][b_arm],
                    "worst_word": spec["candidates"][w_arm],
                }
            )

        best_fleiss_rows.append(brow)
        worst_fleiss_rows.append(wrow)
        for arm in D1_ARMS:
            slot_means[arm].append(sum(slot_scores[arm]) / len(rater_ids))
            alpha_units_all.append(list(slot_scores[arm]))
            alpha_units_by_arm[arm].append(list(slot_scores[arm]))

        per_slot_breakdown.append(
            {
                "slot_id": sid,
                "candidates": dict(spec["candidates"]),
                "mean_scores": {
                    arm: round(sum(slot_scores[arm]) / len(rater_ids), 6) for arm in D1_ARMS
                },
                "best_rank_1_counts": {arm: slot_best[arm] for arm in D1_ARMS},
                "worst_rank_4_counts": {arm: slot_worst[arm] for arm in D1_ARMS},
            }
        )

    n_ratings = len(core_tasks) * len(rater_ids)
    arms_summary: dict[str, Any] = {}
    for arm in D1_ARMS:
        vals = all_scores[arm]
        b_cnt = best_counts[arm]
        w_cnt = worst_counts[arm]
        arms_summary[arm] = {
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
            "worst_rank_4_count": w_cnt,
            "worst_rank_4_share": round(w_cnt / n_ratings, 6),
            "per_rater": {
                rid: {
                    "mean_score": round(
                        sum(per_rater_scores[rid][arm]) / len(core_tasks), 6
                    ),
                    "best_count": per_rater_best[rid][arm],
                    "worst_count": per_rater_worst[rid][arm],
                }
                for rid in rater_ids
            },
        }

    paired_comparisons = {
        "H1_W_A0_vs_W_Ssyn": _paired_diffs_stats(slot_means["W_A0"], slot_means["W_Ssyn"]),
        "H2_W_A0_vs_W_Chal": _paired_diffs_stats(slot_means["W_A0"], slot_means["W_Chal"]),
        "secondary_W_A0_vs_W_A3": _paired_diffs_stats(slot_means["W_A0"], slot_means["W_A3"]),
    }

    # Physics negative calibration controls (NC01..NC03)
    nc_roles = ("correct", "wrong_condition", "spatial_error", "vague_generic")
    nc_correct_total = 0
    nc_by_item: list[dict[str, Any]] = []
    for task in nc_tasks:
        iid = task["task_id"]
        spec = nc_specs[iid]
        role_scores: dict[str, list[int]] = {r: [] for r in nc_roles}
        best_role_cnt: Counter[str] = Counter()
        for rid in rater_ids:
            entry = task["by_model"][rid]
            hk = entry["call_meta"]["hidden_key"]
            parsed = entry["parsed"]
            inv = {lbl: pos for pos, lbl in hk.items()}
            for r_lbl in nc_roles:
                role_scores[r_lbl].append(int(parsed["scores"][inv[r_lbl]]))
            b_lbl = hk[str(parsed["best_candidate"])]
            w_lbl = hk[str(parsed["worst_candidate"])]
            best_role_cnt[b_lbl] += 1
            if b_lbl == "correct":
                nc_correct_total += 1
            csv_rows.append(
                {
                    "item_id": iid,
                    "stratum": "Negative_Control",
                    "rater_id": rid,
                    "word_W_A0": "",
                    "word_W_Ssyn": "",
                    "word_W_Chal": "",
                    "word_W_A3": "",
                    "score_W_A0": "",
                    "score_W_Ssyn": "",
                    "score_W_Chal": "",
                    "score_W_A3": "",
                    "rank_W_A0": "",
                    "rank_W_Ssyn": "",
                    "rank_W_Chal": "",
                    "rank_W_A3": "",
                    "score_nc_correct": int(parsed["scores"][inv["correct"]]),
                    "score_nc_wrong_condition": int(parsed["scores"][inv["wrong_condition"]]),
                    "score_nc_spatial_error": int(parsed["scores"][inv["spatial_error"]]),
                    "score_nc_vague_generic": int(parsed["scores"][inv["vague_generic"]]),
                    "best_label": b_lbl,
                    "worst_label": w_lbl,
                    "best_word": spec["candidates"][b_lbl],
                    "worst_word": spec["candidates"][w_lbl],
                }
            )
        nc_by_item.append(
            {
                "item_id": iid,
                "control_best": spec["control_best"],
                "correct_rank_1_count": best_role_cnt["correct"],
                "mean_scores": {
                    r_lbl: round(sum(role_scores[r_lbl]) / len(rater_ids), 6)
                    for r_lbl in nc_roles
                },
            }
        )

    nc_total_ratings = len(nc_tasks) * len(rater_ids)
    summary = {
        "core_web": {
            "n_slots": len(core_tasks),
            "n_raters": len(rater_ids),
            "n_ratings": n_ratings,
            "arms": arms_summary,
            "inter_rater_agreement": {
                "fleiss_kappa_best_rank_1": round(
                    exact_stats.fleiss_kappa(best_fleiss_rows), 6
                ),
                "fleiss_kappa_worst_rank_4": round(
                    exact_stats.fleiss_kappa(worst_fleiss_rows), 6
                ),
                "krippendorff_alpha_ordinal_all_56_slot_arms": round(
                    krippendorff_alpha_ordinal(alpha_units_all), 6
                ),
                "krippendorff_alpha_ordinal_by_arm": {
                    arm: round(krippendorff_alpha_ordinal(alpha_units_by_arm[arm]), 6)
                    for arm in D1_ARMS
                },
            },
            "paired_comparisons_slot_level_n14": paired_comparisons,
            "per_slot_breakdown": per_slot_breakdown,
        },
        "negative_controls": {
            "n_items": len(nc_tasks),
            "n_raters": len(rater_ids),
            "n_ratings": nc_total_ratings,
            "correct_rank_1_count": nc_correct_total,
            "correct_rank_1_accuracy": round(nc_correct_total / max(1, nc_total_ratings), 6),
            "correct_rank_1_binom_gt_0_25_p": exact_stats.exact_binomial_test(
                nc_correct_total, nc_total_ratings, p0=0.25, alternative="greater"
            ),
            "by_item": nc_by_item,
        },
    }
    return summary, csv_rows


def _evaluate_d1b(d1b: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Pillar D1b 4-criteria boolean truth tables and collision-free CSP."""
    rater_ids = [m for m, _v in providers.GENERATORS]
    core_specs = {s["slot_id"]: s for s in arms_v3.CORE_WEB_SLOTS_14}

    all4_counts_total: Counter[str] = Counter()
    crit_counts_total: dict[str, Counter[str]] = {a: Counter() for a in D1_ARMS}
    all4_frac_by_arm: dict[str, list[float]] = {a: [] for a in D1_ARMS}
    slot_all4_counts: dict[str, Counter[str]] = {}
    fleiss_rows_224: list[list[int]] = []
    per_slot_breakdown: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    for task in d1b["tasks"]:
        sid = task["task_id"]
        spec = core_specs[sid]
        slot_all4: Counter[str] = Counter()
        slot_crit: dict[str, Counter[str]] = {a: Counter() for a in D1_ARMS}

        for rid in rater_ids:
            entry = task["by_model"][rid]
            hk = entry["call_meta"]["hidden_key"]
            ev = entry["parsed"]["evaluations"]
            inv = {arm: pos for pos, arm in hk.items()}
            for arm in D1_ARMS:
                row = ev[inv[arm]]
                passed_all4 = all(bool(row[ck]) for ck in D1_CRITERIA)
                for ck in D1_CRITERIA:
                    if bool(row[ck]):
                        crit_counts_total[arm][ck] += 1
                        slot_crit[arm][ck] += 1
                if passed_all4:
                    all4_counts_total[arm] += 1
                    slot_all4[arm] += 1

        slot_all4_counts[sid] = slot_all4
        for arm in D1_ARMS:
            all4_frac_by_arm[arm].append(slot_all4[arm] / len(rater_ids))
            for ck in D1_CRITERIA:
                t_cnt = slot_crit[arm][ck]
                fleiss_rows_224.append([t_cnt, len(rater_ids) - t_cnt])

        per_slot_breakdown.append(
            {
                "slot_id": sid,
                "candidates": dict(spec["candidates"]),
                "all4_counts_of_5": {arm: slot_all4[arm] for arm in D1_ARMS},
                "per_criterion_counts_of_5": {
                    arm: {ck: slot_crit[arm][ck] for ck in D1_CRITERIA} for arm in D1_ARMS
                },
            }
        )

        # Emit tidy long rows (14 slots x 4 candidate_arms x 5 raters = 280 rows)
        for arm in D1_ARMS:
            cword = spec["candidates"][arm]
            a4_cnt = slot_all4[arm]
            for rid in rater_ids:
                entry = task["by_model"][rid]
                inv = {arm_lbl: pos for pos, arm_lbl in entry["call_meta"]["hidden_key"].items()}
                row = entry["parsed"]["evaluations"][inv[arm]]
                csv_rows.append(
                    {
                        "slot_id": sid,
                        "candidate_arm": arm,
                        "candidate_word": cword,
                        "rater_id": rid,
                        "c1_core_mirror_role": bool(row["c1"]),
                        "c2_trap_free_nonspatial_unforced": bool(row["c2"]),
                        "c3_coupled_system_role": bool(row["c3"]),
                        "c4_everyday_secondary_register": bool(row["c4"]),
                        "all4_pass": all(bool(row[ck]) for ck in D1_CRITERIA),
                        "slot_arm_c1_count": slot_crit[arm]["c1"],
                        "slot_arm_c2_count": slot_crit[arm]["c2"],
                        "slot_arm_c3_count": slot_crit[arm]["c3"],
                        "slot_arm_c4_count": slot_crit[arm]["c4"],
                        "slot_arm_all4_count": a4_cnt,
                        "eligible_ge_3_of_5": a4_cnt >= 3,
                        "eligible_ge_4_of_5": a4_cnt >= 4,
                    }
                )

    n_ratings = len(d1b["tasks"]) * len(rater_ids)
    arms_summary: dict[str, Any] = {}
    for arm in D1_ARMS:
        a4 = all4_counts_total[arm]
        arms_summary[arm] = {
            "all4_pass_count": a4,
            "all4_pass_rate": round(a4 / n_ratings, 6),
            "per_criterion_pass_counts": {ck: crit_counts_total[arm][ck] for ck in D1_CRITERIA},
            "per_criterion_pass_rates": {
                ck: round(crit_counts_total[arm][ck] / n_ratings, 6) for ck in D1_CRITERIA
            },
            "slots_ge_4_of_5_all4": [
                s["slot_id"] for s in arms_v3.CORE_WEB_SLOTS_14 if slot_all4_counts[s["slot_id"]][arm] >= 4
            ],
            "slots_ge_3_of_5_all4": [
                s["slot_id"] for s in arms_v3.CORE_WEB_SLOTS_14 if slot_all4_counts[s["slot_id"]][arm] >= 3
            ],
        }

    mean_others_frac = [
        (
            all4_frac_by_arm["W_Ssyn"][i]
            + all4_frac_by_arm["W_Chal"][i]
            + all4_frac_by_arm["W_A3"][i]
        )
        / 3.0
        for i in range(len(d1b["tasks"]))
    ]
    h3_test = _paired_diffs_stats(all4_frac_by_arm["W_A0"], mean_others_frac)

    slot_ids = [s["slot_id"] for s in arms_v3.CORE_WEB_SLOTS_14]
    a0_ge4 = {sid: slot_all4_counts[sid]["W_A0"] >= 4 for sid in slot_ids}
    ssyn_ge4 = {sid: slot_all4_counts[sid]["W_Ssyn"] >= 4 for sid in slot_ids}
    mcnemar_ge4 = _mcnemar_from_paired_bools(slot_ids, a0_ge4, ssyn_ge4)

    csp_results: dict[str, Any] = {}
    for label, thresh in (("consensus_ge_4_of_5", 4), ("majority_ge_3_of_5", 3)):
        eligible = {
            s["slot_id"]: [
                s["candidates"][arm]
                for arm in D1_ARMS
                if slot_all4_counts[s["slot_id"]][arm] >= thresh
            ]
            for s in arms_v3.CORE_WEB_SLOTS_14
        }
        sol = arms_v3.solve_collision_free_web_assignments(eligible)
        csp_results[label] = {
            "threshold": thresh,
            "eligible_by_slot": eligible,
            "empty_slots": [sid for sid in slot_ids if not eligible[sid]],
            "non_empty_slots": [sid for sid in slot_ids if eligible[sid]],
            **sol,
        }

    summary = {
        "n_slots": len(d1b["tasks"]),
        "n_raters": len(rater_ids),
        "n_ratings_per_arm": n_ratings,
        "total_boolean_cells": len(fleiss_rows_224),
        "arms": arms_summary,
        "h3_w_a0_vs_mean_others_all4_fraction": h3_test,
        "secondary_w_a0_vs_w_ssyn_slot_ge_4_of_5_mcnemar": mcnemar_ge4,
        "inter_rater_agreement_fleiss_kappa_224_cells": round(
            exact_stats.fleiss_kappa(fleiss_rows_224), 6
        ),
        "csp_collision_free_assignments": csp_results,
        "per_slot_breakdown": per_slot_breakdown,
    }
    return summary, csv_rows


def _extract_raw_jsonl_parsed(
    log_by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]],
    role: str,
    arm_id: str,
    item_id: str,
    model_id: str,
) -> dict[str, Any] | None:
    recs = log_by_key.get((role, arm_id, item_id, model_id), [])
    if not recs:
        return None
    raw_txt = recs[-1].get("raw_response", "")
    try:
        parsed = providers.extract_first_json_object(raw_txt)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _evaluate_d2a(
    cal_items: list[dict[str, Any]],
    d2a: dict[str, Any],
    s1_v2_a0: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Pillar D2a Crossing-enabled calibration_17 vs Commit-2 M1 A0."""
    gen_ids = [m for m, _v in providers.GENERATORS]
    v2_by_id = {x["item_id"]: x for x in s1_v2_a0["items"]}
    cal_ids = [x["item_id"] for x in cal_items]

    d2a_cons_flags: dict[str, bool] = {}
    v2_cons_flags: dict[str, bool] = {}
    model_correct_all: Counter[str] = Counter()
    model_correct_k16: Counter[str] = Counter()
    per_item_rows: list[dict[str, Any]] = []
    schema_errors_list: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    d2a_cons_correct_all = 0
    d2a_cons_correct_k16 = 0
    d2a_valid_total = 0
    d2a_pooled_correct = 0

    for task in d2a["tasks"]:
        tid = task["task_id"]
        exp = task["metadata"]["expected_book_ruling"]
        v2_row = v2_by_id[tid]

        ruling_counts: Counter[str] = Counter()
        scope_counts: Counter[str] = Counter()
        valid_cnt = 0
        per_model_votes: dict[str, dict[str, str]] = {}
        err_models: list[str] = []

        for m in gen_ids:
            e = task["by_model"][m]
            if e["status"] == "ok":
                valid_cnt += 1
                d2a_valid_total += 1
                sc = e["parsed"]["scope_status"]
                ru = e["parsed"]["ruling"]
                scope_counts[sc] += 1
                ruling_counts[ru] += 1
                per_model_votes[m] = {"scope_status": sc, "ruling": ru}
                if ru == exp:
                    model_correct_all[m] += 1
                    d2a_pooled_correct += 1
                    if tid != "K17":
                        model_correct_k16[m] += 1
            else:
                err_models.append(m)
                per_model_votes[m] = {"scope_status": "SCHEMA_ERROR", "ruling": "SCHEMA_ERROR"}
                schema_errors_list.append(
                    {
                        "item_id": tid,
                        "model_id": m,
                        "errors": list(e["errors"]),
                    }
                )

        maj_ruling, maj_r_cnt = ruling_counts.most_common(1)[0] if ruling_counts else ("NONE", 0)
        maj_scope, maj_s_cnt = scope_counts.most_common(1)[0] if scope_counts else ("NONE", 0)
        cons4_r = maj_r_cnt >= 4
        cons4_s = maj_s_cnt >= 4
        cons_ok = cons4_r and maj_ruling == exp

        d2a_cons_flags[tid] = cons_ok
        v2_cons_flags[tid] = bool(v2_row["consensus_correct"])
        if cons_ok:
            d2a_cons_correct_all += 1
            if tid != "K17":
                d2a_cons_correct_k16 += 1

        exp_scope = "crossing_interface" if tid == "K17" else "in_scope"
        per_item_rows.append(
            {
                "item_id": tid,
                "expected_book_ruling": exp,
                "expected_scope_status_v3": exp_scope,
                "valid_calls": valid_cnt,
                "scope_counts": dict(scope_counts),
                "ruling_counts": dict(ruling_counts),
                "majority_scope_status": maj_scope,
                "consensus_4_of_5_scope": cons4_s,
                "majority_ruling": maj_ruling,
                "majority_ruling_count": maj_r_cnt,
                "consensus_4_of_5_ruling": cons4_r,
                "consensus_correct": cons_ok,
                "commit2_m1_a0_majority_ruling": v2_row["majority_ruling"],
                "commit2_m1_a0_majority_count": v2_row["majority_count"],
                "commit2_m1_a0_consensus_correct": bool(v2_row["consensus_correct"]),
                "per_model_votes": per_model_votes,
                "schema_error_models": err_models,
            }
        )

        csv_rows.append(
            {
                "substage": "D2a",
                "item_id": tid,
                "stratum": "calibration_17",
                "expected_scope_status": exp_scope,
                "expected_book_ruling": exp,
                "claude_sonnet_4_6_scope": per_model_votes["claude-sonnet-4.6"]["scope_status"],
                "claude_sonnet_4_6_ruling": per_model_votes["claude-sonnet-4.6"]["ruling"],
                "gpt_5_4_fast_scope": per_model_votes["gpt-5.4-fast"]["scope_status"],
                "gpt_5_4_fast_ruling": per_model_votes["gpt-5.4-fast"]["ruling"],
                "gemini_2_5_flash_scope": per_model_votes["gemini-2.5-flash"]["scope_status"],
                "gemini_2_5_flash_ruling": per_model_votes["gemini-2.5-flash"]["ruling"],
                "mistral_medium_3_5_scope": per_model_votes["mistral-medium-3.5"]["scope_status"],
                "mistral_medium_3_5_ruling": per_model_votes["mistral-medium-3.5"]["ruling"],
                "llama_4_maverick_scope": per_model_votes["llama-4-maverick"]["scope_status"],
                "llama_4_maverick_ruling": per_model_votes["llama-4-maverick"]["ruling"],
                "valid_call_count": valid_cnt,
                "schema_error_count": len(err_models),
                "strict_crossing_interface_count": scope_counts.get("crossing_interface", 0),
                "strict_in_scope_count": scope_counts.get("in_scope", 0),
                "strict_no_partner_count": scope_counts.get("no_partner", 0),
                "strict_open_joint_count": scope_counts.get("open_joint", 0),
                "raw_parsed_crossing_interface_count": scope_counts.get("crossing_interface", 0),
                "raw_parsed_no_partner_count": scope_counts.get("no_partner", 0),
                "strict_majority_scope_status": maj_scope,
                "strict_consensus_4_of_5_scope": cons4_s,
                "strict_majority_ruling": maj_ruling,
                "strict_consensus_4_of_5_ruling": cons4_r,
                "ruling_matches_expected": cons_ok,
                "scope_matches_expected": cons4_s and maj_scope == exp_scope,
                "schema_error_models": ";".join(err_models),
                "commit2_m1_a0_majority_ruling": v2_row["majority_ruling"],
                "commit2_m1_a0_consensus_correct": bool(v2_row["consensus_correct"]),
            }
        )

    k16_ids = [x for x in cal_ids if x != "K17"]
    k17_row = next(r for r in per_item_rows if r["item_id"] == "K17")
    summary = {
        "total_items": len(cal_items),
        "expected_calls": d2a["expected_calls"],
        "valid_calls": d2a["valid_calls"],
        "schema_error_count": d2a["schema_error_count"],
        "schema_errors": schema_errors_list,
        "consensus_4_of_5_correct_all_17": d2a_cons_correct_all,
        "consensus_4_of_5_accuracy_all_17": round(d2a_cons_correct_all / 17.0, 6),
        "consensus_4_of_5_correct_k01_k16": d2a_cons_correct_k16,
        "consensus_4_of_5_accuracy_k01_k16": round(d2a_cons_correct_k16 / 16.0, 6),
        "pooled_correct_of_85": d2a_pooled_correct,
        "pooled_accuracy_of_85": round(d2a_pooled_correct / 85.0, 6),
        "pooled_accuracy_of_valid": round(d2a_pooled_correct / max(1, d2a_valid_total), 6),
        "per_model_correct_all_17": {m: model_correct_all[m] for m in gen_ids},
        "per_model_correct_k01_k16": {m: model_correct_k16[m] for m in gen_ids},
        "vs_commit2_m1_a0_all_17_mcnemar": _mcnemar_from_paired_bools(
            cal_ids, d2a_cons_flags, v2_cons_flags
        ),
        "vs_commit2_m1_a0_k01_k16_mcnemar": _mcnemar_from_paired_bools(
            k16_ids, d2a_cons_flags, v2_cons_flags
        ),
        "k17_boyle_law_shift": {
            "d2a_scope_counts": k17_row["scope_counts"],
            "d2a_ruling_counts": k17_row["ruling_counts"],
            "d2a_consensus_correct": k17_row["consensus_correct"],
            "commit2_m1_a0_votes": v2_by_id["K17"]["votes"],
            "commit2_m1_a0_consensus_correct": v2_by_id["K17"]["consensus_correct"],
        },
        "items": per_item_rows,
    }
    return summary, csv_rows


def _evaluate_d2b(
    d2b: dict[str, Any],
    log_by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Pillar D2b Crossing Battery 20 (strict H4 + raw/valid-voter sensitivity)."""
    gen_ids = [m for m, _v in providers.GENERATORS]

    strict_mech_ci = 0
    strict_non_ci = 0
    valid_voter_mech_ci = 0
    valid_voter_non_ci = 0
    raw_parsed_mech_ci = 0
    raw_parsed_non_ci = 0

    lint_errors_audit: list[dict[str, Any]] = []
    per_item_rows: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    for task in d2b["tasks"]:
        tid = task["task_id"]
        strat = task["metadata"]["stratum"]
        exp_scope = task["metadata"]["expected_scope_status"]

        strict_scopes: Counter[str] = Counter()
        strict_rulings: Counter[str] = Counter()
        raw_scopes: Counter[str] = Counter()
        valid_cnt = 0
        per_model_votes: dict[str, dict[str, str]] = {}
        err_models: list[str] = []

        for m in gen_ids:
            e = task["by_model"][m]
            if e["status"] == "ok":
                valid_cnt += 1
                sc = e["parsed"]["scope_status"]
                ru = e["parsed"]["ruling"]
                strict_scopes[sc] += 1
                strict_rulings[ru] += 1
                raw_scopes[sc] += 1
                per_model_votes[m] = {"scope_status": sc, "ruling": ru}
            else:
                err_models.append(m)
                per_model_votes[m] = {"scope_status": "SCHEMA_ERROR", "ruling": "SCHEMA_ERROR"}
                raw_p = _extract_raw_jsonl_parsed(
                    log_by_key, d2b["role"], d2b["arm_id"], tid, m
                )
                raw_sc = raw_p.get("scope_status") if isinstance(raw_p, dict) else None
                raw_ru = raw_p.get("ruling") if isinstance(raw_p, dict) else None
                if isinstance(raw_sc, str) and raw_sc:
                    raw_scopes[raw_sc] += 1
                lint_errors_audit.append(
                    {
                        "item_id": tid,
                        "stratum": strat,
                        "model_id": m,
                        "errors": list(e["errors"]),
                        "raw_parsed_json_present": isinstance(raw_p, dict),
                        "raw_parsed_scope_status": raw_sc,
                        "raw_parsed_ruling": raw_ru,
                        "raw_parsed_variable_map": raw_p.get("variable_map") if isinstance(raw_p, dict) else None,
                        "raw_parsed_translation_template": raw_p.get("translation_template") if isinstance(raw_p, dict) else None,
                    }
                )

        s_ci = strict_scopes.get("crossing_interface", 0)
        r_ci = raw_scopes.get("crossing_interface", 0)
        strict_ge4_ci = s_ci >= 4
        valid_voter_ge_080_ci = valid_cnt > 0 and (s_ci / valid_cnt) >= 0.80
        raw_parsed_ge4_ci = r_ci >= 4

        if strat == "Mechanical_Crossing":
            if strict_ge4_ci:
                strict_mech_ci += 1
            if valid_voter_ge_080_ci:
                valid_voter_mech_ci += 1
            if raw_parsed_ge4_ci:
                raw_parsed_mech_ci += 1
        else:
            if strict_ge4_ci:
                strict_non_ci += 1
            if valid_voter_ge_080_ci:
                valid_voter_non_ci += 1
            if raw_parsed_ge4_ci:
                raw_parsed_non_ci += 1

        maj_scope, maj_s_cnt = strict_scopes.most_common(1)[0] if strict_scopes else ("NONE", 0)
        maj_ruling, maj_r_cnt = strict_rulings.most_common(1)[0] if strict_rulings else ("NONE", 0)
        cons4_s = maj_s_cnt >= 4
        cons4_r = maj_r_cnt >= 4

        item_record = {
            "item_id": tid,
            "stratum": strat,
            "expected_scope_status": exp_scope,
            "valid_calls": valid_cnt,
            "schema_error_count": len(err_models),
            "strict_scope_counts": dict(strict_scopes),
            "raw_parsed_scope_counts": dict(raw_scopes),
            "strict_ruling_counts": dict(strict_rulings),
            "strict_ge_4_of_5_crossing_interface": strict_ge4_ci,
            "valid_voter_ge_0_80_crossing_interface": valid_voter_ge_080_ci,
            "raw_parsed_ge_4_of_5_crossing_interface": raw_parsed_ge4_ci,
            "strict_majority_scope_status": maj_scope,
            "strict_consensus_4_of_5_scope": cons4_s,
            "strict_consensus_matches_expected_scope": cons4_s and maj_scope == exp_scope,
            "per_model_votes": per_model_votes,
            "unmapped_terms_by_model": {
                m: list(task["by_model"][m]["parsed"]["unmapped_terms"])
                for m in gen_ids
                if task["by_model"][m]["status"] == "ok"
            },
        }
        per_item_rows.append(item_record)

        csv_rows.append(
            {
                "substage": "D2b",
                "item_id": tid,
                "stratum": strat,
                "expected_scope_status": exp_scope,
                "expected_book_ruling": "",
                "claude_sonnet_4_6_scope": per_model_votes["claude-sonnet-4.6"]["scope_status"],
                "claude_sonnet_4_6_ruling": per_model_votes["claude-sonnet-4.6"]["ruling"],
                "gpt_5_4_fast_scope": per_model_votes["gpt-5.4-fast"]["scope_status"],
                "gpt_5_4_fast_ruling": per_model_votes["gpt-5.4-fast"]["ruling"],
                "gemini_2_5_flash_scope": per_model_votes["gemini-2.5-flash"]["scope_status"],
                "gemini_2_5_flash_ruling": per_model_votes["gemini-2.5-flash"]["ruling"],
                "mistral_medium_3_5_scope": per_model_votes["mistral-medium-3.5"]["scope_status"],
                "mistral_medium_3_5_ruling": per_model_votes["mistral-medium-3.5"]["ruling"],
                "llama_4_maverick_scope": per_model_votes["llama-4-maverick"]["scope_status"],
                "llama_4_maverick_ruling": per_model_votes["llama-4-maverick"]["ruling"],
                "valid_call_count": valid_cnt,
                "schema_error_count": len(err_models),
                "strict_crossing_interface_count": strict_scopes.get("crossing_interface", 0),
                "strict_in_scope_count": strict_scopes.get("in_scope", 0),
                "strict_no_partner_count": strict_scopes.get("no_partner", 0),
                "strict_open_joint_count": strict_scopes.get("open_joint", 0),
                "raw_parsed_crossing_interface_count": raw_scopes.get("crossing_interface", 0),
                "raw_parsed_no_partner_count": raw_scopes.get("no_partner", 0),
                "strict_majority_scope_status": maj_scope,
                "strict_consensus_4_of_5_scope": cons4_s,
                "strict_majority_ruling": maj_ruling,
                "strict_consensus_4_of_5_ruling": cons4_r,
                "ruling_matches_expected": "",
                "scope_matches_expected": cons4_s and maj_scope == exp_scope,
                "schema_error_models": ";".join(err_models),
                "commit2_m1_a0_majority_ruling": "",
                "commit2_m1_a0_consensus_correct": "",
            }
        )

    n_mech = sum(1 for t in d2b["tasks"] if t["metadata"]["stratum"] == "Mechanical_Crossing")
    n_non = sum(1 for t in d2b["tasks"] if t["metadata"]["stratum"] == "Non_Crossing_Boundary")
    assert n_mech == 7 and n_non == 13

    summary = {
        "total_items": len(d2b["tasks"]),
        "mechanical_crossing_count": n_mech,
        "non_crossing_boundary_count": n_non,
        "expected_calls": d2b["expected_calls"],
        "valid_calls": d2b["valid_calls"],
        "schema_error_count": d2b["schema_error_count"],
        "h4_strict_ge_4_of_5_crossing_interface": {
            "mechanical_crossing_pass": strict_mech_ci,
            "mechanical_crossing_total": n_mech,
            "mechanical_crossing_rate": round(strict_mech_ci / n_mech, 6),
            "non_crossing_boundary_pass": strict_non_ci,
            "non_crossing_boundary_total": n_non,
            "non_crossing_boundary_rate": round(strict_non_ci / n_non, 6),
            "fisher_2x2_p": exact_stats.exact_fisher_2x2(
                strict_mech_ci, n_mech - strict_mech_ci, strict_non_ci, n_non - strict_non_ci
            ),
        },
        "sensitivity_valid_voter_ge_0_80_crossing_interface": {
            "mechanical_crossing_pass": valid_voter_mech_ci,
            "mechanical_crossing_total": n_mech,
            "non_crossing_boundary_pass": valid_voter_non_ci,
            "non_crossing_boundary_total": n_non,
            "fisher_2x2_p": exact_stats.exact_fisher_2x2(
                valid_voter_mech_ci,
                n_mech - valid_voter_mech_ci,
                valid_voter_non_ci,
                n_non - valid_voter_non_ci,
            ),
        },
        "sensitivity_raw_parsed_json_ge_4_of_5_crossing_interface": {
            "mechanical_crossing_pass": raw_parsed_mech_ci,
            "mechanical_crossing_total": n_mech,
            "non_crossing_boundary_pass": raw_parsed_non_ci,
            "non_crossing_boundary_total": n_non,
            "fisher_2x2_p": exact_stats.exact_fisher_2x2(
                raw_parsed_mech_ci,
                n_mech - raw_parsed_mech_ci,
                raw_parsed_non_ci,
                n_non - raw_parsed_non_ci,
            ),
        },
        "non_crossing_boundary_5_of_5_no_partner_count": sum(
            1
            for r in per_item_rows
            if r["stratum"] == "Non_Crossing_Boundary"
            and r["strict_scope_counts"].get("no_partner", 0) == 5
        ),
        "schema_error_audit_template_lint": lint_errors_audit,
        "x007_x008_inspection": [
            r for r in per_item_rows if r["item_id"] in ("X007", "X008")
        ],
        "items": per_item_rows,
    }
    return summary, csv_rows


def _evaluate_d3a(
    cal_items: list[dict[str, Any]],
    d3a: dict[str, Any],
    s1_v2_a0: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Pillar D3a Ch. 2 narrative teaching vs Commit-2 M1 A0."""
    gen_ids = [m for m, _v in providers.GENERATORS]
    cal_by_id = {x["item_id"]: x for x in cal_items}
    v2_by_id = {x["item_id"]: x for x in s1_v2_a0["items"]}

    cal_ids = [x["item_id"] for x in cal_items]
    applied_later_ids = [x["item_id"] for x in cal_items if x["provenance"] == "applied_later"]
    construction_ids = [x["item_id"] for x in cal_items if x["provenance"] == "construction"]

    d3a_cons_flags: dict[str, bool] = {}
    v2_cons_flags: dict[str, bool] = {}
    d3a_call_flags: dict[str, bool] = {}
    v2_call_flags: dict[str, bool] = {}

    d3a_model_ok: Counter[str] = Counter()
    v2_model_ok: Counter[str] = Counter()
    d3a_pooled_ok = 0
    d3a_pooled_valid = 0
    v2_pooled_ok = 0
    v2_pooled_valid = 0

    per_item_rows: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    for task in d3a["tasks"]:
        tid = task["task_id"]
        ci = cal_by_id[tid]
        exp = ci["expected_book_ruling"]
        v2_row = v2_by_id[tid]

        ruling_counts: Counter[str] = Counter()
        scope_counts: Counter[str] = Counter()
        valid_cnt = 0
        err_models: list[str] = []

        for m in gen_ids:
            e = task["by_model"][m]
            if e["status"] == "ok":
                valid_cnt += 1
                d3a_pooled_valid += 1
                sc = e["parsed"]["scope_status"]
                ru = e["parsed"]["ruling"]
                scope_counts[sc] += 1
                ruling_counts[ru] += 1
                ok_m = ru == exp
                if ok_m:
                    d3a_model_ok[m] += 1
                    d3a_pooled_ok += 1
            else:
                err_models.append(m)
                sc = "SCHEMA_ERROR"
                ru = "SCHEMA_ERROR"
                ok_m = False

            v2_vote = v2_row["votes"][m]
            if v2_vote != "SCHEMA_ERROR":
                v2_pooled_valid += 1
                if v2_vote == exp:
                    v2_pooled_ok += 1
            v2_ok_m = v2_vote == exp
            if v2_ok_m:
                v2_model_ok[m] += 1

            call_key = f"{tid}:{m}"
            d3a_call_flags[call_key] = ok_m
            v2_call_flags[call_key] = v2_ok_m

        maj_ruling, maj_cnt = ruling_counts.most_common(1)[0]
        cons4 = maj_cnt >= 4
        cons_ok = cons4 and maj_ruling == exp
        d3a_cons_flags[tid] = cons_ok
        v2_cons_flags[tid] = bool(v2_row["consensus_correct"])

        per_item_rows.append(
            {
                "item_id": tid,
                "provenance": ci["provenance"],
                "description": ci["description"],
                "expected_book_ruling": exp,
                "valid_calls": valid_cnt,
                "scope_counts": dict(scope_counts),
                "ruling_counts": dict(ruling_counts),
                "majority_ruling": maj_ruling,
                "majority_count": maj_cnt,
                "consensus_4_of_5": cons4,
                "consensus_correct": cons_ok,
                "commit2_m1_a0_majority_ruling": v2_row["majority_ruling"],
                "commit2_m1_a0_majority_count": v2_row["majority_count"],
                "commit2_m1_a0_consensus_correct": bool(v2_row["consensus_correct"]),
                "schema_error_models": err_models,
            }
        )

        for m in gen_ids:
            e = task["by_model"][m]
            st = e["status"]
            sc = e["parsed"]["scope_status"] if st == "ok" else "SCHEMA_ERROR"
            ru = e["parsed"]["ruling"] if st == "ok" else "SCHEMA_ERROR"
            v2_ru = v2_row["votes"][m]
            csv_rows.append(
                {
                    "substage": "D3a_narrative_cal17",
                    "item_id": tid,
                    "stratum": ci["provenance"],
                    "model_id": m,
                    "status": st,
                    "expected_book_ruling": exp,
                    "d3a_scope_status": sc,
                    "d3a_ruling": ru,
                    "d3a_matches_expected": ru == exp,
                    "commit2_m1_a0_ruling": v2_ru,
                    "commit2_m1_a0_matches_expected": v2_ru == exp,
                    "d3a_consensus_4_of_5_correct": cons_ok,
                    "commit2_m1_a0_consensus_4_of_5_correct": bool(v2_row["consensus_correct"]),
                    "source_ref": "",
                    "score_V_A0": "",
                    "score_V_Ssyn": "",
                    "score_V_A3": "",
                    "rank_V_A0": "",
                    "rank_V_Ssyn": "",
                    "rank_V_A3": "",
                    "best_variant": "",
                    "worst_variant": "",
                }
            )

    d3a_cons_cnt = sum(1 for k in cal_ids if d3a_cons_flags[k])
    v2_cons_cnt = sum(1 for k in cal_ids if v2_cons_flags[k])
    d3a_app_cnt = sum(1 for k in applied_later_ids if d3a_cons_flags[k])
    v2_app_cnt = sum(1 for k in applied_later_ids if v2_cons_flags[k])
    d3a_con_cnt = sum(1 for k in construction_ids if d3a_cons_flags[k])
    v2_con_cnt = sum(1 for k in construction_ids if v2_cons_flags[k])

    summary = {
        "total_items": len(cal_items),
        "expected_calls": d3a["expected_calls"],
        "valid_calls": d3a["valid_calls"],
        "schema_error_count": d3a["schema_error_count"],
        "d3a_consensus_4_of_5_correct": d3a_cons_cnt,
        "d3a_consensus_4_of_5_accuracy": round(d3a_cons_cnt / 17.0, 6),
        "commit2_m1_a0_consensus_4_of_5_correct": v2_cons_cnt,
        "commit2_m1_a0_consensus_4_of_5_accuracy": round(v2_cons_cnt / 17.0, 6),
        "h5_consensus_vs_commit2_m1_a0_mcnemar": _mcnemar_from_paired_bools(
            cal_ids, d3a_cons_flags, v2_cons_flags
        ),
        "pooled_85_calls_comparison": {
            "d3a_correct_of_85": d3a_pooled_ok,
            "d3a_valid_calls": d3a_pooled_valid,
            "d3a_accuracy_of_85": round(d3a_pooled_ok / 85.0, 6),
            "d3a_accuracy_of_valid": round(d3a_pooled_ok / max(1, d3a_pooled_valid), 6),
            "commit2_m1_a0_correct_of_85": v2_pooled_ok,
            "commit2_m1_a0_valid_calls": v2_pooled_valid,
            "commit2_m1_a0_accuracy_of_85": round(v2_pooled_ok / 85.0, 6),
            "commit2_m1_a0_accuracy_of_valid": round(v2_pooled_ok / max(1, v2_pooled_valid), 6),
            "paired_mcnemar_85": _mcnemar_from_paired_bools(
                sorted(d3a_call_flags), d3a_call_flags, v2_call_flags
            ),
            "fisher_2x2_85_p": exact_stats.exact_fisher_2x2(
                d3a_pooled_ok, 85 - d3a_pooled_ok, v2_pooled_ok, 85 - v2_pooled_ok
            ),
        },
        "applied_later_13_subset": {
            "item_ids": applied_later_ids,
            "d3a_consensus_correct": d3a_app_cnt,
            "d3a_accuracy": round(d3a_app_cnt / 13.0, 6),
            "commit2_m1_a0_consensus_correct": v2_app_cnt,
            "commit2_m1_a0_accuracy": round(v2_app_cnt / 13.0, 6),
            "mcnemar": _mcnemar_from_paired_bools(
                applied_later_ids, d3a_cons_flags, v2_cons_flags
            ),
        },
        "construction_4_subset": {
            "item_ids": construction_ids,
            "d3a_consensus_correct": d3a_con_cnt,
            "commit2_m1_a0_consensus_correct": v2_con_cnt,
            "mcnemar": _mcnemar_from_paired_bools(
                construction_ids, d3a_cons_flags, v2_cons_flags
            ),
        },
        "per_model_correct_of_17": {
            m: {"d3a": d3a_model_ok[m], "commit2_m1_a0": v2_model_ok[m]} for m in gen_ids
        },
        "items": per_item_rows,
    }
    return summary, csv_rows


def _evaluate_d3b(d3b: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Pillar D3b 12 masked verbatim-derived Book excerpt ratings."""
    rater_ids = [m for m, _v in providers.GENERATORS]
    all_scores: dict[str, list[float]] = {v: [] for v in D3B_VARIANTS}
    passage_means: dict[str, list[float]] = {v: [] for v in D3B_VARIANTS}
    passage_strata: list[str] = []

    best_counts: Counter[str] = Counter()
    worst_counts: Counter[str] = Counter()
    per_rater_scores: dict[str, dict[str, list[float]]] = {
        rid: {v: [] for v in D3B_VARIANTS} for rid in rater_ids
    }
    per_rater_best: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}
    per_rater_worst: dict[str, Counter[str]] = {rid: Counter() for rid in rater_ids}

    var_to_idx = {v: i for i, v in enumerate(D3B_VARIANTS)}
    best_fleiss_rows: list[list[int]] = []
    worst_fleiss_rows: list[list[int]] = []
    alpha_units_all: list[list[int]] = []
    alpha_units_by_var: dict[str, list[list[int]]] = {v: [] for v in D3B_VARIANTS}
    per_passage_breakdown: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    for task in d3b["tasks"]:
        pid = task["task_id"]
        strat = task["metadata"]["stratum"]
        src_ref = task["metadata"]["source_ref"]
        passage_strata.append(strat)

        p_scores: dict[str, list[int]] = {v: [] for v in D3B_VARIANTS}
        p_best: Counter[str] = Counter()
        p_worst: Counter[str] = Counter()
        brow = [0, 0, 0]
        wrow = [0, 0, 0]

        for rid in rater_ids:
            entry = task["by_model"][rid]
            hk = entry["call_meta"]["hidden_key"]
            parsed = entry["parsed"]
            inv = {var: pos for pos, var in hk.items()}
            ranks = {hk[str(c)]: idx + 1 for idx, c in enumerate(parsed["ranking"])}

            for var in D3B_VARIANTS:
                sc = int(parsed["scores"][inv[var]])
                p_scores[var].append(sc)
                all_scores[var].append(float(sc))
                per_rater_scores[rid][var].append(float(sc))

            bv = hk[str(parsed["best_variant"])]
            wv = hk[str(parsed["worst_variant"])]
            best_counts[bv] += 1
            worst_counts[wv] += 1
            p_best[bv] += 1
            p_worst[wv] += 1
            per_rater_best[rid][bv] += 1
            per_rater_worst[rid][wv] += 1
            brow[var_to_idx[bv]] += 1
            wrow[var_to_idx[wv]] += 1

            csv_rows.append(
                {
                    "substage": "D3b_passage_ratings",
                    "item_id": pid,
                    "stratum": strat,
                    "model_id": rid,
                    "status": entry["status"],
                    "expected_book_ruling": "",
                    "d3a_scope_status": "",
                    "d3a_ruling": "",
                    "d3a_matches_expected": "",
                    "commit2_m1_a0_ruling": "",
                    "commit2_m1_a0_matches_expected": "",
                    "d3a_consensus_4_of_5_correct": "",
                    "commit2_m1_a0_consensus_4_of_5_correct": "",
                    "source_ref": src_ref,
                    "score_V_A0": int(parsed["scores"][inv["V_A0"]]),
                    "score_V_Ssyn": int(parsed["scores"][inv["V_Ssyn"]]),
                    "score_V_A3": int(parsed["scores"][inv["V_A3"]]),
                    "rank_V_A0": ranks["V_A0"],
                    "rank_V_Ssyn": ranks["V_Ssyn"],
                    "rank_V_A3": ranks["V_A3"],
                    "best_variant": bv,
                    "worst_variant": wv,
                }
            )

        best_fleiss_rows.append(brow)
        worst_fleiss_rows.append(wrow)
        for var in D3B_VARIANTS:
            passage_means[var].append(sum(p_scores[var]) / len(rater_ids))
            alpha_units_all.append(list(p_scores[var]))
            alpha_units_by_var[var].append(list(p_scores[var]))

        per_passage_breakdown.append(
            {
                "passage_id": pid,
                "stratum": strat,
                "source_ref": src_ref,
                "mean_scores": {
                    var: round(sum(p_scores[var]) / len(rater_ids), 6) for var in D3B_VARIANTS
                },
                "best_rank_1_counts": {var: p_best[var] for var in D3B_VARIANTS},
                "worst_rank_3_counts": {var: p_worst[var] for var in D3B_VARIANTS},
            }
        )

    n_ratings = len(d3b["tasks"]) * len(rater_ids)
    variants_summary: dict[str, Any] = {}
    for var in D3B_VARIANTS:
        vals = all_scores[var]
        b_cnt = best_counts[var]
        w_cnt = worst_counts[var]
        variants_summary[var] = {
            "mean_score": round(sum(vals) / n_ratings, 6),
            "sd_score": round(_sample_sd(vals), 6),
            "median_score": round(_median(vals), 6),
            "min_score": int(min(vals)),
            "max_score": int(max(vals)),
            "best_rank_1_count": b_cnt,
            "best_rank_1_share": round(b_cnt / n_ratings, 6),
            "best_rank_1_binom_gt_1_3_p": exact_stats.exact_binomial_test(
                b_cnt, n_ratings, p0=1.0 / 3.0, alternative="greater"
            ),
            "worst_rank_3_count": w_cnt,
            "worst_rank_3_share": round(w_cnt / n_ratings, 6),
            "per_rater": {
                rid: {
                    "mean_score": round(
                        sum(per_rater_scores[rid][var]) / len(d3b["tasks"]), 6
                    ),
                    "best_count": per_rater_best[rid][var],
                    "worst_count": per_rater_worst[rid][var],
                }
                for rid in rater_ids
            },
        }

    paired_all_12 = {
        "H6_V_A0_vs_V_Ssyn": _paired_diffs_stats(
            passage_means["V_A0"], passage_means["V_Ssyn"]
        ),
        "secondary_V_A0_vs_V_A3": _paired_diffs_stats(
            passage_means["V_A0"], passage_means["V_A3"]
        ),
    }

    stratified: dict[str, Any] = {}
    for stratum_name in ("structural_paragraphs", "polysemy_bridge_paragraphs"):
        idxs = [i for i, st in enumerate(passage_strata) if st == stratum_name]
        va0_s = [passage_means["V_A0"][i] for i in idxs]
        vss_s = [passage_means["V_Ssyn"][i] for i in idxs]
        va3_s = [passage_means["V_A3"][i] for i in idxs]
        stratified[stratum_name] = {
            "n_passages": len(idxs),
            "mean_V_A0": round(sum(va0_s) / len(idxs), 6),
            "mean_V_Ssyn": round(sum(vss_s) / len(idxs), 6),
            "mean_V_A3": round(sum(va3_s) / len(idxs), 6),
            "V_A0_vs_V_Ssyn": _paired_diffs_stats(va0_s, vss_s),
            "V_A0_vs_V_A3": _paired_diffs_stats(va0_s, va3_s),
        }

    summary = {
        "n_passages": len(d3b["tasks"]),
        "n_raters": len(rater_ids),
        "n_ratings": n_ratings,
        "variants": variants_summary,
        "inter_rater_agreement": {
            "fleiss_kappa_best_rank_1": round(exact_stats.fleiss_kappa(best_fleiss_rows), 6),
            "fleiss_kappa_worst_rank_3": round(exact_stats.fleiss_kappa(worst_fleiss_rows), 6),
            "krippendorff_alpha_ordinal_all_36_passage_variants": round(
                krippendorff_alpha_ordinal(alpha_units_all), 6
            ),
            "krippendorff_alpha_ordinal_by_variant": {
                var: round(krippendorff_alpha_ordinal(alpha_units_by_var[var]), 6)
                for var in D3B_VARIANTS
            },
        },
        "paired_comparisons_all_12": paired_all_12,
        "stratified_comparisons": stratified,
        "per_passage_breakdown": per_passage_breakdown,
    }
    return summary, csv_rows


def _evaluate_d4(
    s2_v2: dict[str, Any],
    la_v2: dict[str, Any],
    heldout_items: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate Pillar D4 deterministic Layer-A v2 vs Layer-A v3 comparison."""
    h40_map = {x["item_id"]: x for x in heldout_items}
    la_v3_fresh = layer_a_v3.evaluate_frozen_stage2_heldout_v3()

    arms_out: dict[str, Any] = {}
    csv_rows: list[dict[str, Any]] = []

    for arm_id in ("A0", "A3-1"):
        v2_arm = la_v2[arm_id]
        v3_arm = la_v3_fresh[arm_id]
        v3_reports = {r["item_id"]: r for r in v3_arm["per_item_reports"]}

        cross_v2: dict[str, list[str]] = defaultdict(list)
        for col in v2_arm["layer_a_collisions"]:
            if "variants" in col:
                for iids in col["variants"].values():
                    for iid in iids:
                        cross_v2[iid].append(f"{col['layer']}({col.get('physical', '')})")

        cross_v3: dict[str, list[str]] = defaultdict(list)
        for col in v3_arm["layer_a_collisions"]:
            if "variants" in col:
                for iids in col["variants"].values():
                    for iid in iids:
                        cross_v3[iid].append(f"{col['layer']}({col.get('physical', '')})")

        item_rows: list[dict[str, Any]] = []
        for entry in s2_v2[arm_id]["items"]:
            if not (entry.get("consensus_4_of_5") and entry.get("majority_ruling") in ("keep", "invert")):
                continue
            iid = entry["item_id"]
            canon = entry["canonical_model"]
            v2_item = entry["per_voter_layer_a"][canon]
            v3_item = v3_reports[iid]
            v2_passed = bool(v2_item["passed"])
            v3_passed = bool(v3_item["passed"])
            v2_layers = [c["layer"] for c in v2_item["collisions"]]
            v3_layers = [c["layer"] for c in v3_item["collisions"]]
            if not v2_passed and v3_passed:
                delta_lbl = "FIXED_BY_V3"
            elif v2_passed and v3_passed:
                delta_lbl = "PASSED_BOTH"
            elif not v2_passed and not v3_passed:
                delta_lbl = "STILL_FAILS"
            else:
                delta_lbl = "NEW_V3_FAIL"

            item_rows.append(
                {
                    "item_id": iid,
                    "stratum": h40_map[iid]["stratum"],
                    "canonical_model": canon,
                    "ruling": entry["majority_ruling"],
                    "v2_per_item_passed": v2_passed,
                    "v2_collisions": v2_layers,
                    "v3_per_item_passed": v3_passed,
                    "v3_collisions": v3_layers,
                    "cross_item_v2": sorted(set(cross_v2.get(iid, []))),
                    "cross_item_v3": sorted(set(cross_v3.get(iid, []))),
                    "delta": delta_lbl,
                }
            )
            csv_rows.append(
                {
                    "arm_id": arm_id,
                    "item_id": iid,
                    "stratum": h40_map[iid]["stratum"],
                    "equation_latex": h40_map[iid]["equation_latex"],
                    "canonical_model": canon,
                    "ruling": entry["majority_ruling"],
                    "layer_a_v2_passed": v2_passed,
                    "layer_a_v2_collisions": ";".join(v2_layers),
                    "layer_a_v2_joint_passes_all": bool(v2_arm["passes_all"]),
                    "layer_a_v3_passed": v3_passed,
                    "layer_a_v3_collisions": ";".join(v3_layers),
                    "layer_a_v3_joint_passes_all": bool(v3_arm["passes_all"]),
                    "cross_item_collisions_v2": ";".join(sorted(set(cross_v2.get(iid, [])))),
                    "cross_item_collisions_v3": ";".join(sorted(set(cross_v3.get(iid, [])))),
                    "delta_v2_to_v3": delta_lbl,
                }
            )

        arms_out[arm_id] = {
            "layer_a_v2": {
                "evaluated_items": v2_arm["evaluated_items"],
                "per_item_passed": v2_arm["per_item_passed"],
                "joint_collisions_count": v2_arm["layer_a_collisions_count"],
                "passes_all": v2_arm["passes_all"],
                "collisions": v2_arm["layer_a_collisions"],
            },
            "layer_a_v3": {
                "evaluated_items": v3_arm["evaluated_items"],
                "per_item_passed": v3_arm["per_item_passed"],
                "joint_collisions_count": v3_arm["layer_a_collisions_count"],
                "passes_all": v3_arm["passes_all"],
                "collisions": v3_arm["layer_a_collisions"],
            },
            "items": item_rows,
        }

    return arms_out, csv_rows


def build_all_artifacts() -> dict[Path, str]:
    """Compute `summary_deep_v3.json` and all 5 Deep-v3 CSVs purely in memory."""
    cal_items = _load_json(prepare_openstax_sample.CALIBRATION_17_PATH)["items"]
    heldout_items = _load_json(prepare_openstax_sample.HELDOUT_40_PATH)["items"]
    s1_v2 = _load_json(HARNESS_DIR / "outputs" / "stage1_m1_calibration.json")
    s2_v2 = _load_json(HARNESS_DIR / "outputs" / "stage2_m2_heldout.json")
    la_v2 = _load_json(HARNESS_DIR / "outputs" / "layer_a_summary.json")

    d1a_raw = _load_json(OUTPUTS_DIR / "raw_d1a_web_ratings.json")
    d1b_raw = _load_json(OUTPUTS_DIR / "raw_d1b_web_truthtable.json")
    d2a_raw = _load_json(OUTPUTS_DIR / "raw_d2a_crossing_cal17.json")
    d2b_raw = _load_json(OUTPUTS_DIR / "raw_d2b_crossing_battery20.json")
    d3a_raw = _load_json(OUTPUTS_DIR / "raw_d3a_narrative_cal17.json")
    d3b_raw = _load_json(OUTPUTS_DIR / "raw_d3b_passage_ratings.json")
    raw_summary = _load_json(OUTPUTS_DIR / "summary_deep_v3_raw.json")

    log_records, log_by_key = _load_jsonl_by_key()

    provenance = _compute_provenance(log_records, raw_summary)
    d1a_summary, d1a_csv_rows = _evaluate_d1a(d1a_raw)
    d1b_summary, d1b_csv_rows = _evaluate_d1b(d1b_raw)
    d2a_summary, d2a_csv_rows = _evaluate_d2a(cal_items, d2a_raw, s1_v2["A0"])
    d2b_summary, d2b_csv_rows = _evaluate_d2b(d2b_raw, log_by_key)
    d3a_summary, d3a_csv_rows = _evaluate_d3a(cal_items, d3a_raw, s1_v2["A0"])
    d3b_summary, d3b_csv_rows = _evaluate_d3b(d3b_raw)
    d4_summary, d4_csv_rows = _evaluate_d4(s2_v2, la_v2, heldout_items)

    h1 = d1a_summary["core_web"]["paired_comparisons_slot_level_n14"]["H1_W_A0_vs_W_Ssyn"]
    h2 = d1a_summary["core_web"]["paired_comparisons_slot_level_n14"]["H2_W_A0_vs_W_Chal"]
    h3 = d1b_summary["h3_w_a0_vs_mean_others_all4_fraction"]
    h4 = d2b_summary["h4_strict_ge_4_of_5_crossing_interface"]
    h5 = d3a_summary["h5_consensus_vs_commit2_m1_a0_mcnemar"]
    h6 = d3b_summary["paired_comparisons_all_12"]["H6_V_A0_vs_V_Ssyn"]

    named_pvalues: list[tuple[str, float]] = [
        ("H1_D1a_W_A0_vs_W_Ssyn_slot_perm", h1["paired_permutation_test"]["p_value"]),
        ("H2_D1a_W_A0_vs_W_Chal_slot_perm", h2["paired_permutation_test"]["p_value"]),
        ("H3_D1b_W_A0_vs_others_all4_perm", h3["paired_permutation_test"]["p_value"]),
        ("H4_D2b_Mechanical_vs_NonCrossing_strict_fisher", h4["fisher_2x2_p"]),
        ("H5_D3a_cal17_vs_M1_A0_mcnemar", h5["p_value"]),
        ("H6_D3b_V_A0_vs_V_Ssyn_passage_perm", h6["paired_permutation_test"]["p_value"]),
    ]
    holm_family = exact_stats.holm_bonferroni(named_pvalues)
    holm_by_name = {entry["name"]: entry for entry in holm_family}

    confirmatory = {
        "H1": {
            "pillar": "D1a",
            "comparison": "W_A0 vs W_Ssyn mean rater score per slot (W01..W14, N=14)",
            "primary_test": "exact_paired_permutation_test (2^14=16384)",
            **h1,
            "holm_bonferroni": holm_by_name["H1_D1a_W_A0_vs_W_Ssyn_slot_perm"],
        },
        "H2": {
            "pillar": "D1a",
            "comparison": "W_A0 vs W_Chal mean rater score per slot (W01..W14, N=14)",
            "primary_test": "exact_paired_permutation_test (2^14=16384)",
            **h2,
            "holm_bonferroni": holm_by_name["H2_D1a_W_A0_vs_W_Chal_slot_perm"],
        },
        "H3": {
            "pillar": "D1b",
            "comparison": "W_A0 vs mean(W_Ssyn, W_Chal, W_A3) all4 pass fraction (W01..W14, N=14)",
            "primary_test": "exact_paired_permutation_test (2^14=16384)",
            **h3,
            "holm_bonferroni": holm_by_name["H3_D1b_W_A0_vs_others_all4_perm"],
        },
        "H4": {
            "pillar": "D2b",
            "comparison": "Strict >=4/5 crossing_interface consensus: Mechanical_Crossing (7) vs Non_Crossing_Boundary (13)",
            "primary_test": "exact_fisher_2x2",
            **h4,
            "holm_bonferroni": holm_by_name["H4_D2b_Mechanical_vs_NonCrossing_strict_fisher"],
        },
        "H5": {
            "pillar": "D3a",
            "comparison": ">=4/5 consensus calibration accuracy on K01..K17: D3a vs Commit-2 M1 A0 (N=17)",
            "primary_test": "exact_mcnemar_test",
            "d3a_correct": d3a_summary["d3a_consensus_4_of_5_correct"],
            "commit2_m1_a0_correct": d3a_summary["commit2_m1_a0_consensus_4_of_5_correct"],
            **h5,
            "holm_bonferroni": holm_by_name["H5_D3a_cal17_vs_M1_A0_mcnemar"],
        },
        "H6": {
            "pillar": "D3b",
            "comparison": "V_A0 vs V_Ssyn mean rater score per excerpt (P01..P12, N=12)",
            "primary_test": "exact_paired_permutation_test (2^12=4096)",
            **h6,
            "holm_bonferroni": holm_by_name["H6_D3b_V_A0_vs_V_Ssyn_passage_perm"],
        },
    }

    summary_payload = {
        "schema_version": "tsr_deep_v3_eval_summary",
        "provenance": provenance,
        "confirmatory_hypotheses": confirmatory,
        "holm_bonferroni_family": holm_family,
        "pillar_d1a": d1a_summary,
        "pillar_d1b": d1b_summary,
        "pillar_d2": {
            "d2a_crossing_cal17": d2a_summary,
            "d2b_crossing_battery20": d2b_summary,
        },
        "pillar_d3": {
            "d3a_narrative_cal17": d3a_summary,
            "d3b_passage_ratings": d3b_summary,
        },
        "pillar_d4_layer_a_v2_vs_v3": d4_summary,
    }

    d1a_fields = [
        "item_id",
        "stratum",
        "rater_id",
        "word_W_A0",
        "word_W_Ssyn",
        "word_W_Chal",
        "word_W_A3",
        "score_W_A0",
        "score_W_Ssyn",
        "score_W_Chal",
        "score_W_A3",
        "rank_W_A0",
        "rank_W_Ssyn",
        "rank_W_Chal",
        "rank_W_A3",
        "score_nc_correct",
        "score_nc_wrong_condition",
        "score_nc_spatial_error",
        "score_nc_vague_generic",
        "best_label",
        "worst_label",
        "best_word",
        "worst_word",
    ]
    d1b_fields = [
        "slot_id",
        "candidate_arm",
        "candidate_word",
        "rater_id",
        "c1_core_mirror_role",
        "c2_trap_free_nonspatial_unforced",
        "c3_coupled_system_role",
        "c4_everyday_secondary_register",
        "all4_pass",
        "slot_arm_c1_count",
        "slot_arm_c2_count",
        "slot_arm_c3_count",
        "slot_arm_c4_count",
        "slot_arm_all4_count",
        "eligible_ge_3_of_5",
        "eligible_ge_4_of_5",
    ]
    d2_fields = [
        "substage",
        "item_id",
        "stratum",
        "expected_scope_status",
        "expected_book_ruling",
        "claude_sonnet_4_6_scope",
        "claude_sonnet_4_6_ruling",
        "gpt_5_4_fast_scope",
        "gpt_5_4_fast_ruling",
        "gemini_2_5_flash_scope",
        "gemini_2_5_flash_ruling",
        "mistral_medium_3_5_scope",
        "mistral_medium_3_5_ruling",
        "llama_4_maverick_scope",
        "llama_4_maverick_ruling",
        "valid_call_count",
        "schema_error_count",
        "strict_crossing_interface_count",
        "strict_in_scope_count",
        "strict_no_partner_count",
        "strict_open_joint_count",
        "raw_parsed_crossing_interface_count",
        "raw_parsed_no_partner_count",
        "strict_majority_scope_status",
        "strict_consensus_4_of_5_scope",
        "strict_majority_ruling",
        "strict_consensus_4_of_5_ruling",
        "ruling_matches_expected",
        "scope_matches_expected",
        "schema_error_models",
        "commit2_m1_a0_majority_ruling",
        "commit2_m1_a0_consensus_correct",
    ]
    d3_fields = [
        "substage",
        "item_id",
        "stratum",
        "model_id",
        "status",
        "expected_book_ruling",
        "d3a_scope_status",
        "d3a_ruling",
        "d3a_matches_expected",
        "commit2_m1_a0_ruling",
        "commit2_m1_a0_matches_expected",
        "d3a_consensus_4_of_5_correct",
        "commit2_m1_a0_consensus_4_of_5_correct",
        "source_ref",
        "score_V_A0",
        "score_V_Ssyn",
        "score_V_A3",
        "rank_V_A0",
        "rank_V_Ssyn",
        "rank_V_A3",
        "best_variant",
        "worst_variant",
    ]
    d4_fields = [
        "arm_id",
        "item_id",
        "stratum",
        "equation_latex",
        "canonical_model",
        "ruling",
        "layer_a_v2_passed",
        "layer_a_v2_collisions",
        "layer_a_v2_joint_passes_all",
        "layer_a_v3_passed",
        "layer_a_v3_collisions",
        "layer_a_v3_joint_passes_all",
        "cross_item_collisions_v2",
        "cross_item_collisions_v3",
        "delta_v2_to_v3",
    ]

    return {
        SUMMARY_V3_PATH: json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n",
        CSV_D1A_PATH: _render_csv_text(d1a_fields, d1a_csv_rows),
        CSV_D1B_PATH: _render_csv_text(d1b_fields, d1b_csv_rows),
        CSV_D2_PATH: _render_csv_text(d2_fields, d2a_csv_rows + d2b_csv_rows),
        CSV_D3_PATH: _render_csv_text(d3_fields, d3a_csv_rows + d3b_csv_rows),
        CSV_D4_PATH: _render_csv_text(d4_fields, d4_csv_rows),
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


def _verify_git_provenance_v3() -> dict[str, Any]:
    """Verify Commit 4, Commit 5, and Commit 6 lineage and blob immutability."""
    head_sha = _git_output("rev-parse", "HEAD")

    prereg_parent = _git_output("rev-parse", f"{DEEP_V3_PREREG_SHA}~1")
    if prereg_parent != V2_EVAL_SHA:
        raise RuntimeError(
            f"Expected {DEEP_V3_PREREG_SHA}~1 == {V2_EVAL_SHA}, got {prereg_parent}"
        )

    pre_eval_parent = _git_output("rev-parse", f"{DEEP_V3_PRE_EVAL_SHA}~1")
    if pre_eval_parent != DEEP_V3_PREREG_SHA:
        raise RuntimeError(
            f"Expected {DEEP_V3_PRE_EVAL_SHA}~1 == {DEEP_V3_PREREG_SHA}, got {pre_eval_parent}"
        )

    if head_sha == DEEP_V3_PRE_EVAL_SHA:
        mode = "pre_commit_6"
    else:
        anc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", DEEP_V3_PRE_EVAL_SHA, head_sha],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if anc.returncode != 0:
            raise RuntimeError(
                f"Expected {DEEP_V3_PRE_EVAL_SHA} to be an ancestor of HEAD ({head_sha})"
            )
        mode = "post_commit_6"

    c4_tree = set(_git_output("ls-tree", "-r", "--name-only", DEEP_V3_PREREG_SHA).splitlines())
    c5_tree = set(_git_output("ls-tree", "-r", "--name-only", DEEP_V3_PRE_EVAL_SHA).splitlines())

    for p in c4_tree:
        if p.startswith(("harness/deep_v3/logs/", "harness/deep_v3/outputs/")):
            raise RuntimeError(
                f"Commit 4 ({DEEP_V3_PREREG_SHA}) unexpectedly contains {p}"
            )
    for rel in COMMIT6_GENERATED_REL_PATHS:
        if rel in c4_tree:
            raise RuntimeError(
                f"Commit 4 ({DEEP_V3_PREREG_SHA}) unexpectedly contains {rel}"
            )
        if rel in c5_tree:
            raise RuntimeError(
                f"Commit 5 ({DEEP_V3_PRE_EVAL_SHA}) unexpectedly contains {rel}"
            )

    immutable_files = (*COMMIT4_V3_FILES, *COMMIT5_V3_FILES)
    for rel in immutable_files:
        expected_blob = _git_output("rev-parse", f"{DEEP_V3_PRE_EVAL_SHA}:{rel}")
        disk_blob = _git_output("hash-object", rel)
        if disk_blob != expected_blob:
            raise RuntimeError(
                f"Working tree file {rel} modified vs {DEEP_V3_PRE_EVAL_SHA}"
            )
        if mode == "post_commit_6":
            head_blob = _git_output("rev-parse", f"HEAD:{rel}")
            if head_blob != expected_blob:
                raise RuntimeError(
                    f"HEAD blob for {rel} modified vs {DEEP_V3_PRE_EVAL_SHA}"
                )

    return {
        "git_mode": mode,
        "head_sha": head_sha,
        "v2_eval_sha_verified": V2_EVAL_SHA,
        "deep_v3_prereg_sha_verified": DEEP_V3_PREREG_SHA,
        "deep_v3_pre_eval_sha_verified": DEEP_V3_PRE_EVAL_SHA,
        "immutable_commit4_commit5_blobs_verified": len(immutable_files),
    }


def write_outputs() -> dict[str, Any]:
    """Generate and write `summary_deep_v3.json` and all 5 Deep-v3 CSVs."""
    artifacts = build_all_artifacts()
    written: dict[str, int] = {}
    for path, content in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        raw_bytes = content.encode("utf-8")
        path.write_bytes(raw_bytes)
        written[str(path.relative_to(REPO_ROOT))] = len(raw_bytes)
    return {"write_outputs": "OK", "bytes_written": written}


def verify_offline() -> dict[str, Any]:
    """Run all offline checks: hygiene, v2 & v3 verifiers, byte parity, links, SHAs, and git lineage."""
    hygiene_v2 = run_tsr_harness.check_repo_hygiene(allow_live_artifacts=True)
    if hygiene_v2:
        raise RuntimeError("Repo hygiene check failed:\n- " + "\n- ".join(hygiene_v2))

    hygiene_v3 = run_deep_v3.check_v3_hygiene(allow_live_artifacts=True)
    if hygiene_v3:
        raise RuntimeError("Deep-v3 hygiene check failed:\n- " + "\n- ".join(hygiene_v3))

    _run_krippendorff_self_test()
    exact_stats._run_self_test()
    openstax_res = prepare_openstax_sample.run_verify_offline()
    v2_post_live = run_tsr_harness.run_verify_offline_post_live()
    v2_eval_res = evaluate_tsr_harness.verify_offline()
    v3_post_live = run_deep_v3.run_verify_offline()

    expected_artifacts = build_all_artifacts()
    verified_files: dict[str, str] = {}
    for path, expected_text in expected_artifacts.items():
        if not path.exists():
            raise RuntimeError(f"Missing evaluated Deep-v3 artifact: {path.relative_to(REPO_ROOT)}")
        actual_bytes = path.read_bytes()
        expected_bytes = expected_text.encode("utf-8")
        if actual_bytes != expected_bytes:
            raise RuntimeError(
                f"Byte mismatch on {path.relative_to(REPO_ROOT)}: "
                f"disk={len(actual_bytes)}B vs recomputed={len(expected_bytes)}B"
            )
        verified_files[str(path.relative_to(REPO_ROOT))] = hashlib.sha256(actual_bytes).hexdigest()

    link_errors = (
        evaluate_tsr_harness._verify_markdown_links(PREREG_V3_MD_PATH)
        + evaluate_tsr_harness._verify_markdown_links(RESULTS_V3_MD_PATH)
        + evaluate_tsr_harness._verify_markdown_links(RESULTS_V2_MD_PATH)
    )
    if link_errors:
        raise RuntimeError("Markdown link check failed:\n- " + "\n- ".join(link_errors))

    results_v3_txt = RESULTS_V3_MD_PATH.read_text(encoding="utf-8")
    for sha in (DEEP_V3_PREREG_SHA, DEEP_V3_PRE_EVAL_SHA):
        if sha not in results_v3_txt:
            raise RuntimeError(f"harness/deep_v3/RESULTS_DEEP_V3.md missing required SHA {sha}")

    git_info: dict[str, Any] = {"git_mode": "no_git_dir"}
    if (REPO_ROOT / ".git").exists():
        git_info = _verify_git_provenance_v3()

    return {
        "verify_offline": "OK",
        "openstax_verify": openstax_res["verify_offline"],
        "v2_post_live_verify": v2_post_live["verify_offline"],
        "v2_evaluate_verify": v2_eval_res["verify_offline"],
        "v3_post_live_verify": v3_post_live["verify_offline"],
        "verified_output_sha256": verified_files,
        "git_provenance_v3": git_info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="TSR Deep-v3 offline evaluator and verifier")
    parser.add_argument("--write", action="store_true", help="Write summary_deep_v3.json and 5 CSVs")
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
