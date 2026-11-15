#!/usr/bin/env python3
"""Exact stdlib-only statistical tests and inter-rater agreement metrics.

Python 3.12+ standard library only. Zero third-party dependencies.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from typing import Any


def _binom_pmf(i: int, n: int, p: float) -> float:
    """Compute exact binomial PMF for `i` successes in `n` trials."""
    if i < 0 or i > n:
        return 0.0
    if p == 0.0:
        return 1.0 if i == 0 else 0.0
    if p == 1.0:
        return 1.0 if i == n else 0.0
    if n <= 1000:
        return math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
    log_pmf = (
        math.lgamma(n + 1)
        - math.lgamma(i + 1)
        - math.lgamma(n - i + 1)
        + i * math.log(p)
        + (n - i) * math.log1p(-p)
    )
    return math.exp(log_pmf)


def exact_mcnemar_test(n10: int, n01: int) -> float:
    """Two-sided exact McNemar test via exact binomial distribution (p0 = 0.5).

    `n10` and `n01` are the discordant cell counts. Returns `1.0` when `n10 + n01 == 0`.
    """
    if n10 < 0 or n01 < 0:
        raise ValueError(f"Discordant counts must be non-negative, got n10={n10}, n01={n01}")
    n = n10 + n01
    if n == 0:
        return 1.0
    k = min(n10, n01)
    if n <= 1000:
        tail = math.ldexp(sum(math.comb(n, i) for i in range(k + 1)), -n)
    else:
        tail = sum(_binom_pmf(i, n, 0.5) for i in range(k + 1))
    return min(1.0, 2.0 * tail)


def exact_sign_test(wins: int, losses: int, ties: int = 0) -> dict[str, Any]:
    """Two-sided exact sign test on non-tied wins vs. losses."""
    if wins < 0 or losses < 0 or ties < 0:
        raise ValueError(f"Counts must be non-negative, got wins={wins}, losses={losses}, ties={ties}")
    n_non_tied = wins + losses
    p_value = exact_mcnemar_test(wins, losses)
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "n_non_tied": n_non_tied,
        "p_value": p_value,
    }


def _hypergeom_pmf(x: int, r1: int, r2: int, c1: int, n: int) -> float:
    if n <= 1000:
        return (math.comb(r1, x) * math.comb(r2, c1 - x)) / math.comb(n, c1)
    log_p = (
        math.lgamma(r1 + 1)
        - math.lgamma(x + 1)
        - math.lgamma(r1 - x + 1)
        + math.lgamma(r2 + 1)
        - math.lgamma(c1 - x + 1)
        - math.lgamma(r2 - (c1 - x) + 1)
        - (math.lgamma(n + 1) - math.lgamma(c1 + 1) - math.lgamma(n - c1 + 1))
    )
    return math.exp(log_p)


def exact_fisher_2x2(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact test over 2x2 table [[a, b], [c, d]].

    Sums probabilities of all tables with fixed marginals having hypergeometric
    probability `<= p_obs + 1e-12`.
    """
    if min(a, b, c, d) < 0:
        raise ValueError(f"2x2 table counts must be non-negative, got {(a, b, c, d)}")
    r1 = a + b
    r2 = c + d
    c1 = a + c
    n = r1 + r2
    if n == 0:
        return 1.0
    x_min = max(0, c1 - r2)
    x_max = min(r1, c1)
    p_obs = _hypergeom_pmf(a, r1, r2, c1, n)
    cutoff = p_obs + 1e-12
    total_p = 0.0
    for x in range(x_min, x_max + 1):
        p_x = _hypergeom_pmf(x, r1, r2, c1, n)
        if p_x <= cutoff:
            total_p += p_x
    return min(1.0, max(0.0, total_p))


def _exact_sign_flip_extreme_count(nz_abs: list[float], threshold: float) -> int:
    """Count sign vectors in `{-1, +1}^N` with `|sum(s_i * nz_abs[i])| >= threshold`."""
    vals = sorted(nz_abs, reverse=True)
    n = len(vals)
    suffix = [0.0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + vals[i]

    pruning_tol = 1e-12

    def _dfs(idx: int, cur: float) -> int:
        rem = suffix[idx]
        if cur + rem < threshold - pruning_tol and cur - rem > -threshold + pruning_tol:
            return 0
        if cur - rem >= threshold + pruning_tol or -cur - rem >= threshold + pruning_tol:
            return 1 << (n - idx)
        if idx == n:
            return 1 if abs(cur) >= threshold else 0
        v = vals[idx]
        return _dfs(idx + 1, cur + v) + _dfs(idx + 1, cur - v)

    # Symmetry across +/- for vals[0] halves work while staying exact.
    return 2 * _dfs(1, vals[0])


def exact_paired_permutation_test(
    diffs: list[float],
    *,
    seed: int = 20261115,
    mc_draws: int = 100000,
) -> dict[str, Any]:
    """Two-sided paired sign-flip permutation test on `mean(diffs)`.

    Enumerates all `2^N_nz` sign assignments over non-zero differences when
    `N_nz <= 20`; otherwise uses deterministic Monte Carlo (`seed=20261115`).
    """
    n_items = len(diffs)
    if n_items == 0:
        return {
            "n_items": 0,
            "n_nonzero": 0,
            "mean_diff": 0.0,
            "method": "degenerate_empty",
            "p_value": 1.0,
        }
    fdiffs = [float(x) for x in diffs]
    mean_diff = sum(fdiffs) / n_items
    nz = [abs(x) for x in fdiffs if x != 0.0]
    n_nz = len(nz)
    if n_nz == 0:
        return {
            "n_items": n_items,
            "n_nonzero": 0,
            "mean_diff": 0.0,
            "method": "exact_sign_flip",
            "p_value": 1.0,
        }

    obs_abs_sum = abs(sum(fdiffs))
    threshold = obs_abs_sum - 1e-12
    if n_nz <= 20:
        extreme = _exact_sign_flip_extreme_count(nz, threshold)
        total = 1 << n_nz
        p_value = min(1.0, extreme / total)
        method = "exact_sign_flip"
    else:
        if mc_draws <= 0:
            raise ValueError(f"mc_draws must be positive, got {mc_draws}")
        rng = random.Random(seed)
        hits = 0
        for _ in range(mc_draws):
            bits = rng.getrandbits(n_nz)
            total_s = 0.0
            for v in nz:
                total_s += v if (bits & 1) else -v
                bits >>= 1
            if abs(total_s) >= threshold:
                hits += 1
        p_value = min(1.0, (hits + 1) / (mc_draws + 1))
        method = f"monte_carlo_{mc_draws}_seed_{seed}"

    return {
        "n_items": n_items,
        "n_nonzero": n_nz,
        "mean_diff": mean_diff,
        "method": method,
        "p_value": p_value,
    }


def exact_binomial_test(
    k: int,
    n: int,
    p0: float = 0.25,
    alternative: str = "two-sided",
) -> float:
    """Exact binomial test for `k` successes in `n` trials under `H0: p = p0`."""
    if n < 0 or k < 0 or k > n:
        raise ValueError(f"Invalid counts k={k}, n={n}")
    if not (0.0 <= p0 <= 1.0):
        raise ValueError(f"Probability p0 must be in [0, 1], got {p0}")
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(f"Invalid alternative {alternative!r}")
    if n == 0:
        return 1.0
    if alternative == "greater":
        p_val = sum(_binom_pmf(i, n, p0) for i in range(k, n + 1))
    elif alternative == "less":
        p_val = sum(_binom_pmf(i, n, p0) for i in range(0, k + 1))
    else:
        p_obs = _binom_pmf(k, n, p0)
        cutoff = p_obs + 1e-12
        p_val = sum(
            p_i for i in range(0, n + 1) if (p_i := _binom_pmf(i, n, p0)) <= cutoff
        )
    return min(1.0, max(0.0, p_val))


def cohens_kappa(pairs: list[tuple[Any, Any]]) -> float:
    """Compute Cohen's unweighted kappa across paired nominal ratings."""
    if not pairs:
        raise ValueError("cohens_kappa requires at least one rating pair")
    n = len(pairs)
    c1 = Counter(a for a, _ in pairs)
    c2 = Counter(b for _, b in pairs)
    cats = list(dict.fromkeys([*c1.keys(), *c2.keys()]))
    p_o = sum(1 for a, b in pairs if a == b) / n
    p_e = sum((c1[cat] / n) * (c2[cat] / n) for cat in cats)
    if abs(1.0 - p_e) <= 1e-15:
        return 1.0 if abs(1.0 - p_o) <= 1e-15 else 0.0
    return (p_o - p_e) / (1.0 - p_e)


def fleiss_kappa(subject_category_counts: list[list[int]]) -> float:
    """Compute Fleiss' kappa across `N` subjects, `k` categories, and fixed `n` raters."""
    if not subject_category_counts:
        raise ValueError("fleiss_kappa requires at least one subject row")
    n_subjects = len(subject_category_counts)
    n_cats = len(subject_category_counts[0])
    if n_cats == 0:
        raise ValueError("fleiss_kappa requires at least one category")
    raters_per_subject = sum(subject_category_counts[0])
    if raters_per_subject < 2:
        raise ValueError(f"fleiss_kappa requires >= 2 raters per subject, got {raters_per_subject}")
    for idx, row in enumerate(subject_category_counts):
        if len(row) != n_cats:
            raise ValueError(f"Row {idx} has {len(row)} categories, expected {n_cats}")
        if any(c < 0 for c in row):
            raise ValueError(f"Negative count in row {idx}: {row}")
        if sum(row) != raters_per_subject:
            raise ValueError(
                f"Row {idx} sums to {sum(row)} raters, expected {raters_per_subject}"
            )

    total_ratings = n_subjects * raters_per_subject
    p_j = [
        sum(row[j] for row in subject_category_counts) / total_ratings
        for j in range(n_cats)
    ]
    denom = raters_per_subject * (raters_per_subject - 1)
    p_i = [
        (sum(c * c for c in row) - raters_per_subject) / denom
        for row in subject_category_counts
    ]
    p_bar = sum(p_i) / n_subjects
    p_e = sum(pj * pj for pj in p_j)
    if abs(1.0 - p_e) <= 1e-15:
        return 1.0 if abs(1.0 - p_bar) <= 1e-15 else 0.0
    return (p_bar - p_e) / (1.0 - p_e)


def holm_bonferroni(named_pvalues: list[tuple[str, float]]) -> list[dict[str, Any]]:
    """Apply Holm-Bonferroni step-down family-wise error correction."""
    m = len(named_pvalues)
    if m == 0:
        return []
    indexed = sorted(
        [(idx, name, float(raw_p)) for idx, (name, raw_p) in enumerate(named_pvalues)],
        key=lambda t: (t[2], t[0]),
    )
    out: list[dict[str, Any]] = []
    running_max = 0.0
    for rank_idx, (_orig_idx, name, raw_p) in enumerate(indexed):
        if not (0.0 <= raw_p <= 1.0) or math.isnan(raw_p):
            raise ValueError(f"Invalid p-value for {name!r}: {raw_p!r}")
        adj = min(1.0, raw_p * (m - rank_idx))
        running_max = max(running_max, adj)
        out.append(
            {
                "name": name,
                "raw_p": raw_p,
                "holm_adjusted_p": running_max,
                "rank": rank_idx + 1,
                "rejected_0_05": running_max <= 0.05,
                "rejected_0_01": running_max <= 0.01,
            }
        )
    return out


def _run_self_test() -> None:
    """Run unit checks against known textbook exact statistics edge cases."""
    import itertools

    # 1. Exact McNemar & Sign test
    assert exact_mcnemar_test(0, 0) == 1.0
    assert exact_mcnemar_test(1, 1) == 1.0
    assert abs(exact_mcnemar_test(10, 0) - (2.0 / 1024.0)) < 1e-15
    assert abs(exact_mcnemar_test(9, 1) - (2.0 * 11.0 / 1024.0)) < 1e-15
    st = exact_sign_test(8, 2, ties=3)
    assert st["n_non_tied"] == 10
    assert abs(st["p_value"] - (2.0 * (1 + 10 + 45) / 1024.0)) < 1e-15

    # 2. Fisher 2x2 exact (Lady Tasting Tea: 4/4 -> 2/70 = 1/35)
    assert abs(exact_fisher_2x2(4, 0, 0, 4) - (2.0 / 70.0)) < 1e-12
    assert exact_fisher_2x2(0, 0, 0, 0) == 1.0
    assert abs(exact_fisher_2x2(5, 5, 5, 5) - 1.0) < 1e-12

    # 3. Exact paired permutation vs brute force 2^N on small N & zeros
    assert exact_paired_permutation_test([])["p_value"] == 1.0
    assert exact_paired_permutation_test([0.0, 0.0, 0.0])["p_value"] == 1.0
    sample_diffs = [1.5, -0.5, 2.0, 0.0, 1.0, 3.25, -0.75]
    res_perm = exact_paired_permutation_test(sample_diffs)
    nz_sample = [x for x in sample_diffs if x != 0.0]
    obs_abs = abs(sum(nz_sample)) - 1e-12
    brute_hits = sum(
        1
        for signs in itertools.product((-1.0, 1.0), repeat=len(nz_sample))
        if abs(sum(s * v for s, v in zip(signs, nz_sample))) >= obs_abs
    )
    assert res_perm["method"] == "exact_sign_flip"
    assert res_perm["n_items"] == 7 and res_perm["n_nonzero"] == 6
    assert abs(res_perm["p_value"] - brute_hits / (1 << len(nz_sample))) < 1e-15
    # Verify deterministic Monte Carlo path for N_nz > 20
    big_diffs = [float(i) for i in range(1, 24)]
    mc1 = exact_paired_permutation_test(big_diffs, seed=20261115, mc_draws=5000)
    mc2 = exact_paired_permutation_test(big_diffs, seed=20261115, mc_draws=5000)
    assert mc1 == mc2 and mc1["method"].startswith("monte_carlo_") and mc1["p_value"] < 0.001

    # 4. Exact binomial test
    assert abs(exact_binomial_test(0, 4, p0=0.5, alternative="two-sided") - 0.125) < 1e-15
    assert abs(exact_binomial_test(2, 4, p0=0.5, alternative="two-sided") - 1.0) < 1e-15
    assert abs(exact_binomial_test(4, 4, p0=0.5, alternative="greater") - 0.0625) < 1e-15
    assert abs(exact_binomial_test(1, 4, p0=0.5, alternative="less") - 0.3125) < 1e-15

    # 5. Cohen's kappa (including p_o == p_e == 1.0 and asymmetric zero-variance)
    assert cohens_kappa([("a", "a"), ("a", "a"), ("a", "a")]) == 1.0
    assert abs(cohens_kappa([("a", "a"), ("a", "a"), ("b", "a")]) - 0.0) < 1e-15
    assert abs(cohens_kappa([("a", "a"), ("b", "b"), ("a", "b")]) - 0.4) < 1e-15

    # 6. Fleiss' kappa (Wikipedia classic N=10, n=14, k=5 -> ~0.20993; plus constant edge)
    assert fleiss_kappa([[4, 0, 0], [4, 0, 0], [4, 0, 0]]) == 1.0
    wiki_counts = [
        [0, 0, 0, 0, 14],
        [0, 2, 6, 4, 2],
        [0, 0, 3, 5, 6],
        [0, 3, 9, 2, 0],
        [2, 2, 8, 1, 1],
        [7, 7, 0, 0, 0],
        [3, 2, 6, 3, 0],
        [2, 5, 3, 2, 2],
        [6, 5, 2, 1, 0],
        [0, 2, 2, 3, 7],
    ]
    assert abs(fleiss_kappa(wiki_counts) - 0.20993070442195522) < 1e-12

    # 7. Holm-Bonferroni monotonicity & rejection flags
    hb = holm_bonferroni([("h3", 0.40), ("h1", 0.002), ("h2", 0.02)])
    assert [r["name"] for r in hb] == ["h1", "h2", "h3"]
    assert abs(hb[0]["holm_adjusted_p"] - 0.006) < 1e-15 and hb[0]["rejected_0_01"]
    assert abs(hb[1]["holm_adjusted_p"] - 0.04) < 1e-15 and hb[1]["rejected_0_05"] and not hb[1]["rejected_0_01"]
    assert abs(hb[2]["holm_adjusted_p"] - 0.40) < 1e-15 and not hb[2]["rejected_0_05"]
    # Step-down monotonicity enforcement when sorted_p[1]*2 < sorted_p[0]*3
    hb_mono = holm_bonferroni([("a", 0.015), ("b", 0.016), ("c", 0.50)])
    assert abs(hb_mono[0]["holm_adjusted_p"] - 0.045) < 1e-15
    assert abs(hb_mono[1]["holm_adjusted_p"] - 0.045) < 1e-15

    print("EXACT_STATS_SELF_TEST_OK")


if __name__ == "__main__":
    _run_self_test()
