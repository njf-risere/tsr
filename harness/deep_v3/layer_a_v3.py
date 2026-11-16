#!/usr/bin/env python3
"""Pillar D4: Deterministic algebraic, calculus, & rational-exponent Layer-A v3 audit.

Imports `harness.arms_v2` read-only and adds three strictly mathematical normalizations
while preserving every genuine A1, A2, A3, and A4 collision catch:
  1. Strip prime-bearing simple subscripts (`_S'S`, `_PS'`, `_j`) BEFORE standalone primes.
  2. Normalize standard English calculus & summation phrases case-insensitively BEFORE
     token extraction and AST parsing (`integral over path of -> int`, `d(X) -> (X)`).
  3. Compute exact rational (`fractions.Fraction`) net-exponent cancellation within each
     multiplicative/divisive monomial (`X^1 * X^-1 -> 0`) AND cross-check substituted
     `variable_map` monomial exponents against `reflected_formula`.

Zero live LLM calls. Python 3.12+ standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

DEEP_V3_DIR = Path(__file__).resolve().parent
HARNESS_DIR = DEEP_V3_DIR.parent
REPO_ROOT = HARNESS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness import arms_v2  # noqa: E402

# ---------------------------------------------------------------------------
# Normalization Helpers (Read-Only Extension of arms_v2)
# ---------------------------------------------------------------------------

_SUBSCRIPT_SIMPLE_V3_RE = re.compile(r"(?<=[A-Za-z0-9\)\]])_[A-Za-z0-9'\u2032\u2033]+")

_INTEGRAL_PHRASE_RE = re.compile(
    r"(?i)\b(?:(?:line|contour|surface|volume|path)\s+)?integral(?:\s+over\s+[A-Za-z0-9_'\s]+?)?\s+of\b"
)
_BARE_INTEGRAL_RE = re.compile(r"(?i)\bintegral\b")
_SUM_PHRASE_RE = re.compile(r"(?i)\bsum(?:\s+over\s+[A-Za-z0-9_'\s]+?)?\s+of\b")
_DIFF_PAREN_RE = re.compile(r"(?i)\bd\s*\(")
_DIFF_VAR_RE = re.compile(r"(?i)\bd\s+(?=[A-Za-z])")

_SUPERSCRIPT_CHAR_MAP: dict[str, str] = {
    "\u2070": "0",
    "\u00b9": "1",
    "\u00b2": "2",
    "\u00b3": "3",
    "\u2074": "4",
    "\u2075": "5",
    "\u2076": "6",
    "\u2077": "7",
    "\u2078": "8",
    "\u2079": "9",
}
_UNICODE_SUPERSCRIPT_RUN_RE = re.compile(
    r"\u207b?[\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079]+"
)

_TRAILING_QUALIFIER_PAREN_RE = re.compile(r"\s*\(([^()]{1,36})\)\s*$")
_MATH_OP_IN_PAREN_RE = re.compile(r"[+\-*/÷×^=]")


def _strip_balanced_subscripts_v3(s: str) -> str:
    """Remove all balanced `_{...}` and prime-bearing simple `_S'S` subscripts safely."""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == "_" and i + 1 < n and s[i + 1] == "{":
            res = arms_v2._read_balanced_brace(s, i + 1)
            if res is not None:
                _sub_content, next_i = res
                i = next_i
                continue
        out.append(s[i])
        i += 1
    s2 = "".join(out)
    return _SUBSCRIPT_SIMPLE_V3_RE.sub("", s2)


def _replace_unicode_superscripts(text: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        raw = m.group(0)
        neg = raw.startswith("\u207b")
        digits = "".join(_SUPERSCRIPT_CHAR_MAP[ch] for ch in raw.lstrip("\u207b"))
        return f"^(-{digits})" if neg else f"^{digits}"

    return _UNICODE_SUPERSCRIPT_RUN_RE.sub(_repl, text)


def normalize_calculus_phrases_v3(text: str) -> str:
    """Normalize standard English calculus/summation phrases case-insensitively before AST parsing."""
    s = _INTEGRAL_PHRASE_RE.sub(" int ", text)
    s = _BARE_INTEGRAL_RE.sub(" int ", s)
    s = _SUM_PHRASE_RE.sub(" sum ", s)
    s = _DIFF_PAREN_RE.sub(" (", s)
    s = _DIFF_VAR_RE.sub("", s)
    return s


def strip_math_decorations_v3(text: str, *, normalize_calculus: bool = True) -> str:
    """Strip TeX wrappers, prime-bearing subscripts, standalone primes, and calculus phrasing."""
    s = (
        text.replace("$", "")
        .replace("\u00b7", " * ")
        .replace("\\ ", " ")
        .replace("\\,", " ")
        .replace("\\;", " ")
        .replace("\\:", " ")
        .replace("\\!", " ")
    )
    s = _replace_unicode_superscripts(s)
    s = arms_v2._COMBINING_MARKS_RE.sub("", s)
    for _ in range(4):
        s_new = arms_v2._TEX_WRAPPER_RE.sub(r"\1", s)
        if s_new == s:
            break
        s = s_new
    s = _strip_balanced_subscripts_v3(s)
    s = arms_v2._PRIMES_RE.sub("", s)
    if normalize_calculus:
        s = normalize_calculus_phrases_v3(s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_target_token_v3(token: str) -> str:
    """Normalize a single target token from `variable_map`, keeping math parentheticals."""
    s = strip_math_decorations_v3(token, normalize_calculus=False)
    while True:
        m = _TRAILING_QUALIFIER_PAREN_RE.search(s)
        if not m:
            break
        inner = m.group(1)
        # Preserve genuine arithmetic expressions such as `(Appreciation / Vibration)`
        if _MATH_OP_IN_PAREN_RE.search(inner):
            break
        s = s[: m.start()].strip()
    return s


def normalize_phys_token_v3(token: str) -> str:
    """Normalize a physical variable/concept name cleanly for cross-item bijection checks."""
    s = strip_math_decorations_v3(token, normalize_calculus=False).lower()
    while arms_v2._TRAILING_PAREN_RE.search(s):
        s = arms_v2._TRAILING_PAREN_RE.sub("", s).strip()
    s = re.sub(r"[\\{}]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def extract_target_tokens_stripped_v3(
    expr: str,
    arm: arms_v2.ArmConfigV2,
    *,
    normalize_calculus: bool = True,
) -> tuple[list[str], list[str]]:
    """Extract valid arm target terms from `expr` after v3 subscript/prime/calculus normalization."""
    cleaned = strip_math_decorations_v3(expr, normalize_calculus=normalize_calculus)
    cleaned = arms_v2._TEX_CMD_TOKEN_RE.sub(
        lambda m: arms_v2._TEX_CMD_TOKEN_MAP[m.group(1)],
        cleaned,
    )
    matched: list[str] = []
    pat = re.compile(
        r"(?<![A-Za-z])("
        + "|".join(re.escape(t) for t in arm.valid_target_terms)
        + r")(?![A-Za-z])"
    )
    remainder_parts: list[str] = []
    pos = 0
    for m in pat.finditer(cleaned):
        remainder_parts.append(cleaned[pos : m.start()])
        matched.append(m.group(0))
        pos = m.end()
    remainder_parts.append(cleaned[pos:])
    remainder = " ".join(remainder_parts)
    unknowns: list[str] = []
    for alpha in re.findall(r"[A-Za-z]+", remainder):
        if (
            alpha not in arms_v2._ALLOWED_MATH_IDENTIFIERS
            and alpha.lower() not in arms_v2._ALLOWED_MATH_IDENTIFIERS
        ):
            unknowns.append(alpha)
    return matched, unknowns


# ---------------------------------------------------------------------------
# V3 AST Preprocessing & Rational Net-Exponent Monomial Algebra
# ---------------------------------------------------------------------------

def _preprocess_formula_for_ast_v3(expr: str) -> str:
    expanded = arms_v2._expand_latex_frac(expr)
    s = strip_math_decorations_v3(expanded, normalize_calculus=True)
    s = re.sub(r"\\sqrt\s*\[[^\]]*\]", "sqrt", s)
    s = re.sub(r"\\sqrt(?![A-Za-z])", "sqrt", s)
    s = re.sub(
        r"(?:\\(?:sum|int|oint|iint|prod)|(?<![A-Za-z])(?:sum|int|oint|iint|prod)(?![A-Za-z]))"
        r"(?:\s*\^\s*(?:\{[^{}]*\}|[A-Za-z0-9]+))?",
        " ",
        s,
    )
    s = re.sub(r"\^\s*\{([^{}]*)\}", r"^(\1)", s)
    s = s.replace("\u00f7", "/").replace("\u2212", "-").replace("\u00d7", "*")
    s = arms_v2._TEX_AST_CMD_RE.sub(lambda m: arms_v2._TEX_AST_CMD_MAP[m.group(1)], s)
    s = s.replace("{", "(").replace("}", ")").replace("[", "(").replace("]", ")")
    return re.sub(r"\s+", " ", s).strip()


def _tokenize_ast_v3(
    expr: str,
    arm: arms_v2.ArmConfigV2 | None = None,
) -> tuple[list[tuple[str, str]], dict[str, str]]:
    s = _preprocess_formula_for_ast_v3(expr)
    term_map: dict[str, str] = {}
    if arm is not None:
        pat = re.compile(
            r"(?<![A-Za-z])(" + "|".join(re.escape(t) for t in arm.valid_target_terms) + r")(?![A-Za-z])"
        )
        parts: list[str] = []
        pos = 0
        idx = 0
        for m in pat.finditer(s):
            parts.append(s[pos : m.start()])
            marker = f" __TERM{idx}__ "
            term_map[f"__TERM{idx}__"] = m.group(0)
            parts.append(marker)
            idx += 1
            pos = m.end()
        parts.append(s[pos:])
        s = "".join(parts)

    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "+-*/^":
            if ch == "*" and i + 1 < n and s[i + 1] == "*":
                tokens.append(("OP", "^"))
                i += 2
            else:
                tokens.append(("OP", ch))
            i += 1
        elif ch == "(":
            tokens.append(("LP", "("))
            i += 1
        elif ch == ")":
            tokens.append(("RP", ")"))
            i += 1
        elif ch.isdigit() or (ch == "." and i + 1 < n and s[i + 1].isdigit()):
            j = i + 1
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            tokens.append(("NUM", s[i:j]))
            i = j
        elif ch.isalpha() or ch == "_":
            j = i + 1
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            word = s[i:j]
            if word in term_map:
                tokens.append(("TERM", term_map[word]))
            else:
                tokens.append(("ID", word))
            i = j
        else:
            i += 1
    return tokens, term_map


def _parse_expr_ast_v3(expr: str, arm: arms_v2.ArmConfigV2 | None = None) -> Any:
    tokens, _ = _tokenize_ast_v3(expr, arm=arm)
    if not tokens:
        return arms_v2._NumNode("1")
    return arms_v2._ExprParser(tokens).parse_expr()


def _parse_equation_clauses_and_segments_v3(formula: str) -> list[list[str]]:
    if not formula or formula.strip().lower().startswith("none"):
        return []
    stripped_cond = arms_v2._strip_side_condition(formula)
    cleaned = strip_math_decorations_v3(stripped_cond, normalize_calculus=False)
    clauses = arms_v2._split_top_level_char(cleaned, ",")
    eq_lists: list[list[str]] = []
    for clause in clauses:
        if "=" in clause:
            segs = [seg for seg in arms_v2._split_top_level_char(clause, "=") if seg]
            if len(segs) >= 2:
                eq_lists.append(segs)
    return eq_lists


def _parse_equation_lhs_rhs_v3(formula: str) -> tuple[str, str] | None:
    eq_lists = _parse_equation_clauses_and_segments_v3(formula)
    if not eq_lists:
        return None
    segs = eq_lists[0]
    return segs[0], segs[-1]


def _try_eval_const_fraction(node: Any) -> Fraction | None:
    """Evaluate a pure constant AST subtree as an exact `Fraction` if possible."""
    if isinstance(node, arms_v2._NumNode):
        try:
            return Fraction(node.val)
        except ValueError:
            return None
    if isinstance(node, arms_v2._NegNode):
        inner = _try_eval_const_fraction(node.inner)
        return -inner if inner is not None else None
    if isinstance(node, arms_v2._AddNode):
        acc = Fraction(0)
        for t in node.terms:
            tv = _try_eval_const_fraction(t)
            if tv is None:
                return None
            acc += tv
        return acc
    if isinstance(node, arms_v2._MulNode):
        acc = Fraction(1)
        for f in node.factors:
            fv = _try_eval_const_fraction(f)
            if fv is None:
                return None
            acc *= fv
        return acc
    if isinstance(node, arms_v2._FracNode):
        nv = _try_eval_const_fraction(node.num)
        dv = _try_eval_const_fraction(node.den)
        if nv is None or dv is None or dv == 0:
            return None
        return nv / dv
    if isinstance(node, arms_v2._PowNode):
        bv = _try_eval_const_fraction(node.base)
        ev = _try_eval_const_fraction(node.exp)
        if bv is not None and ev is not None and ev.denominator == 1:
            if bv == 0 and ev < 0:
                return None
            return bv ** int(ev)
    return None


def _collect_monomial_or_mixed(
    node: Any,
    mult_exp: Fraction,
    term_sign: int,
    mono: dict[str, Fraction],
    quot_exact: dict[str, set[int]],
    overall_exact: dict[str, set[int]],
    arm: arms_v2.ArmConfigV2 | None,
) -> bool:
    """Accumulate exact rational exponents along pure multiplicative/divisive subtrees.

    Returns `True` iff the entire subtree was strictly monomial (no inner irreducible sums
    or non-`sqrt` functions), allowing exact net-exponent comparison.
    """
    if isinstance(node, arms_v2._NumNode):
        return True
    if isinstance(node, arms_v2._TermNode):
        mono[node.name] = mono.get(node.name, Fraction(0)) + mult_exp
        return True
    if isinstance(node, arms_v2._VarNode):
        if arm is None:
            if (
                node.name not in arms_v2._AST_CONST_OR_OP_IDENTIFIERS
                and node.name.lower() not in arms_v2._AST_CONST_OR_OP_IDENTIFIERS
            ):
                mono[node.name] = mono.get(node.name, Fraction(0)) + mult_exp
        return True
    if isinstance(node, arms_v2._NegNode):
        return _collect_monomial_or_mixed(
            node.inner, mult_exp, -term_sign, mono, quot_exact, overall_exact, arm
        )
    if isinstance(node, arms_v2._MulNode):
        is_pure = True
        for f in node.factors:
            ok = _collect_monomial_or_mixed(
                f, mult_exp, term_sign, mono, quot_exact, overall_exact, arm
            )
            is_pure = is_pure and ok
        return is_pure
    if isinstance(node, arms_v2._FracNode):
        ok_n = _collect_monomial_or_mixed(
            node.num, mult_exp, term_sign, mono, quot_exact, overall_exact, arm
        )
        ok_d = _collect_monomial_or_mixed(
            node.den, -mult_exp, term_sign, mono, quot_exact, overall_exact, arm
        )
        return ok_n and ok_d
    if isinstance(node, arms_v2._PowNode):
        exp_rat = _try_eval_const_fraction(node.exp)
        if exp_rat is not None:
            return _collect_monomial_or_mixed(
                node.base, mult_exp * exp_rat, term_sign, mono, quot_exact, overall_exact, arm
            )
        base_div = -1 if arms_v2._is_negative_exponent(node.exp) else 1
        div_sign = (1 if mult_exp >= 0 else -1) * base_div
        arms_v2._collect_node_var_polarities(
            node.base, term_sign, div_sign, quot_exact, overall_exact, arm=arm
        )
        return False
    if isinstance(node, arms_v2._FuncNode):
        if node.fn == "sqrt":
            return _collect_monomial_or_mixed(
                node.arg, mult_exp * Fraction(1, 2), term_sign, mono, quot_exact, overall_exact, arm
            )
        div_sign = 1 if mult_exp >= 0 else -1
        arms_v2._collect_node_var_polarities(
            node.arg, term_sign, div_sign, quot_exact, overall_exact, arm=arm
        )
        return False
    if isinstance(node, arms_v2._AddNode):
        # Record polarities inside nested irreducible sum (e.g. `1 - v^2 / c^2` under sqrt)
        div_sign = 1 if mult_exp >= 0 else -1
        sub_flat = arms_v2._flatten_additive_terms(node, sign=1, arm=arm)
        for sub_sign, sub_node in sub_flat:
            sub_mono: dict[str, Fraction] = {}
            _collect_monomial_or_mixed(
                sub_node,
                Fraction(1),
                sub_sign,
                sub_mono,
                quot_exact,
                overall_exact,
                arm,
            )
            for v, exp_val in sub_mono.items():
                if exp_val == 0:
                    continue
                inner_q = 1 if exp_val > 0 else -1
                # Mirror v2 polarity convention on nested divisor roots such as `sqrt(1 - v^2/c^2)`
                eff_q = div_sign * inner_q if div_sign < 0 or sub_sign > 0 else inner_q
                quot_exact[v].add(eff_q)
                overall_exact[v].add(term_sign * sub_sign * inner_q * div_sign)
        return False
    return True


def _analyze_expr_v3(
    expr: str,
    arm: arms_v2.ArmConfigV2 | None = None,
) -> dict[str, Any]:
    ast = _parse_expr_ast_v3(expr, arm=arm)
    flat = arms_v2._flatten_additive_terms(ast, sign=1, arm=arm)
    add_signs: list[int] = [s for s, _ in flat]
    quot_exact: dict[str, set[int]] = defaultdict(set)
    overall_exact: dict[str, set[int]] = defaultdict(set)
    term_records: list[tuple[int, dict[str, Fraction] | None]] = []

    for t_sign, t_node in flat:
        mono: dict[str, Fraction] = {}
        is_pure = _collect_monomial_or_mixed(
            t_node, Fraction(1), t_sign, mono, quot_exact, overall_exact, arm
        )
        cleaned_mono = {k: v for k, v in mono.items() if v != 0}
        for v, exp_val in cleaned_mono.items():
            q_sign = 1 if exp_val > 0 else -1
            quot_exact[v].add(q_sign)
            overall_exact[v].add(t_sign * q_sign)
        term_records.append((t_sign, cleaned_mono if is_pure else None))

    quot_ci: dict[str, set[int]] = defaultdict(set)
    overall_ci: dict[str, set[int]] = defaultdict(set)
    for k, vals in quot_exact.items():
        quot_ci[k.lower()].update(vals)
    for k, vals in overall_exact.items():
        overall_ci[k.lower()].update(vals)

    return {
        "add_signs": add_signs,
        "quot_exact": dict(quot_exact),
        "overall_exact": dict(overall_exact),
        "quot_ci": dict(quot_ci),
        "overall_ci": dict(overall_ci),
        "term_records": term_records,
    }


def _extract_var_signs_from_expr_v3(expr: str, arm: arms_v2.ArmConfigV2 | None = None) -> dict[str, int]:
    info = _analyze_expr_v3(expr, arm=arm)
    out: dict[str, int] = {}
    for k, s_set in info["overall_exact"].items():
        key = k if arm is not None else k.lower()
        if len(s_set) == 1:
            out[key] = next(iter(s_set))
    return out


def _extract_phys_token_from_key_v3(k: str) -> str:
    return strip_math_decorations_v3(k, normalize_calculus=False).replace("\\", "").strip()


def _parse_vmap_monomials(
    var_map: dict[str, Any],
    arm: arms_v2.ArmConfigV2,
) -> tuple[dict[str, dict[str, Fraction]], dict[str, dict[str, Fraction]]]:
    """Parse each pure product/quotient/power `variable_map` entry into exact target monomials."""
    exact_map: dict[str, dict[str, Fraction]] = {}
    ci_map: dict[str, dict[str, Fraction]] = {}
    for pk, raw_tv in var_map.items():
        tv_str = str(raw_tv)
        if arms_v2._is_stripped_constant_var_entry(pk, tv_str):
            cands = re.findall(r"[A-Za-z]+", _extract_phys_token_from_key_v3(pk))
            if cands:
                sym = cands[-1]
                exact_map[sym] = {}
                ci_map[sym.lower()] = {}
            continue
        norm_tv = normalize_target_token_v3(tv_str)
        toks, unk = extract_target_tokens_stripped_v3(norm_tv, arm, normalize_calculus=False)
        if unk or not toks:
            continue
        info = _analyze_expr_v3(norm_tv, arm=arm)
        if len(info["term_records"]) != 1:
            continue
        t_sign, t_mono = info["term_records"][0]
        if t_mono is None or t_sign < 0:
            continue
        cands = re.findall(r"[A-Za-z]+", _extract_phys_token_from_key_v3(pk))
        if not cands:
            continue
        sym = cands[-1]
        exact_map[sym] = t_mono
        ci_map[sym.lower()] = t_mono
    return exact_map, ci_map


def _substitute_phys_monomial(
    eq_mono: dict[str, Fraction],
    exact_map: dict[str, dict[str, Fraction]],
    ci_map: dict[str, dict[str, Fraction]],
) -> dict[str, Fraction]:
    """Substitute `variable_map` target monomials into a physical monomial & cancel exponents."""
    out: dict[str, Fraction] = {}
    for sym, phys_exp in eq_mono.items():
        t_mono: dict[str, Fraction] | None = None
        if sym in exact_map:
            t_mono = exact_map[sym]
        elif sym.lower() in ci_map:
            t_mono = ci_map[sym.lower()]
        elif f"d{sym}" in exact_map:
            t_mono = exact_map[f"d{sym}"]
        elif f"d{sym}".lower() in ci_map:
            t_mono = ci_map[f"d{sym}".lower()]
        if t_mono is None:
            continue
        for t_term, t_exp in t_mono.items():
            out[t_term] = out.get(t_term, Fraction(0)) + phys_exp * t_exp
    return {k: v for k, v in out.items() if v != 0}


def _mono_signature(sign: int, mono: dict[str, Fraction]) -> tuple[int, tuple[tuple[str, int, int], ...]]:
    return (
        sign,
        tuple(sorted((k, v.numerator, v.denominator) for k, v in mono.items())),
    )


def _format_mono(mono: dict[str, Fraction]) -> dict[str, str]:
    return {k: str(v) for k, v in sorted(mono.items())}


def _compare_rhs_segment_a3_v3(
    eq_str: str,
    refl_str: str,
    eq_seg: str,
    refl_seg: str,
    var_map: dict[str, Any],
    arm: arms_v2.ArmConfigV2,
    item_id: str,
) -> list[dict[str, Any]]:
    eq_info = _analyze_expr_v3(eq_seg, arm=None)
    refl_info = _analyze_expr_v3(refl_seg, arm=arm)
    collisions: list[dict[str, Any]] = []

    eq_add_signs: list[int] = eq_info["add_signs"]
    refl_add_signs: list[int] = refl_info["add_signs"]
    if len(eq_add_signs) >= 2 and len(eq_add_signs) == len(refl_add_signs):
        if sorted(eq_add_signs) != sorted(refl_add_signs):
            collisions.append(
                {
                    "layer": "A3_additive_sign_flip",
                    "item_id": item_id,
                    "equation_latex": eq_str,
                    "reflected_formula": refl_str,
                    "expected_signs": eq_add_signs,
                    "got_signs": refl_add_signs,
                }
            )

    # Pure monomial substituted exponent cross-check
    exact_map, ci_map = _parse_vmap_monomials(var_map, arm)
    eq_terms: list[tuple[int, dict[str, Fraction] | None]] = eq_info["term_records"]
    refl_terms: list[tuple[int, dict[str, Fraction] | None]] = refl_info["term_records"]
    if (
        exact_map
        and len(eq_terms) == len(refl_terms)
        and all(m is not None for _s, m in eq_terms)
        and all(m is not None for _s, m in refl_terms)
    ):
        expected_sigs = Counter(
            _mono_signature(s, _substitute_phys_monomial(m or {}, exact_map, ci_map))
            for s, m in eq_terms
        )
        got_sigs = Counter(_mono_signature(s, m or {}) for s, m in refl_terms)
        if expected_sigs != got_sigs:
            collisions.append(
                {
                    "layer": "A3_monomial_exponent_mismatch",
                    "item_id": item_id,
                    "equation_latex": eq_str,
                    "reflected_formula": refl_str,
                    "expected_terms": [
                        {
                            "sign": s,
                            "exponents": _format_mono(
                                _substitute_phys_monomial(m or {}, exact_map, ci_map)
                            ),
                        }
                        for s, m in eq_terms
                    ],
                    "got_terms": [
                        {"sign": s, "exponents": _format_mono(m or {})}
                        for s, m in refl_terms
                    ],
                }
            )
            return collisions

    # Direct quotient / overall sign check (for single-slot non-substituted or mixed expressions)
    eq_quot_exact = eq_info["quot_exact"]
    eq_overall_exact = eq_info["overall_exact"]
    eq_quot_ci = eq_info["quot_ci"]
    eq_overall_ci = eq_info["overall_ci"]
    refl_quot = refl_info["quot_exact"]
    refl_overall = refl_info["overall_exact"]

    targ_to_eq_syms: dict[str, list[str]] = defaultdict(list)
    for pk, tv in var_map.items():
        if arms_v2._is_stripped_constant_var_entry(pk, str(tv)):
            continue
        toks, unk = extract_target_tokens_stripped_v3(
            normalize_target_token_v3(str(tv)), arm, normalize_calculus=False
        )
        if unk or len(toks) != 1 or "\u00f7" in str(tv) or "/" in str(tv):
            continue
        cands = re.findall(r"[A-Za-z]+", _extract_phys_token_from_key_v3(pk))
        if not cands:
            continue
        targ_to_eq_syms[toks[0]].append(cands[-1])

    for targ_slot, syms in sorted(targ_to_eq_syms.items()):
        if targ_slot not in refl_quot:
            continue
        exp_quot: set[int] = set()
        exp_overall: set[int] = set()
        for sym_raw in syms:
            if sym_raw in eq_quot_exact:
                exp_quot.update(eq_quot_exact[sym_raw])
                exp_overall.update(eq_overall_exact[sym_raw])
            elif f"d{sym_raw}" in eq_quot_exact:
                exp_quot.update(eq_quot_exact[f"d{sym_raw}"])
                exp_overall.update(eq_overall_exact[f"d{sym_raw}"])
            elif sym_raw.lower() in eq_quot_ci:
                exp_quot.update(eq_quot_ci[sym_raw.lower()])
                exp_overall.update(eq_overall_ci[sym_raw.lower()])
        if not exp_quot:
            continue
        got_quot = refl_quot[targ_slot]
        got_overall = refl_overall[targ_slot]
        if exp_quot != got_quot or exp_overall != got_overall:
            collisions.append(
                {
                    "layer": "A3_exponent_or_quotient_flip",
                    "item_id": item_id,
                    "physical_vars": syms,
                    "target_slot": targ_slot,
                    "equation_quot_signs": sorted(exp_quot),
                    "reflected_quot_signs": sorted(got_quot),
                    "equation_overall_signs": sorted(exp_overall),
                    "reflected_overall_signs": sorted(got_overall),
                    "equation_latex": eq_str,
                    "reflected_formula": refl_str,
                }
            )
    return collisions


def _check_a3_formula_sign_and_monomial_v3(
    item: dict[str, Any],
    parsed: dict[str, Any],
    arm: arms_v2.ArmConfigV2,
) -> list[dict[str, Any]]:
    eq = item.get("equation_latex", "")
    refl = parsed.get("reflected_formula", "")
    eq_clauses = _parse_equation_clauses_and_segments_v3(eq)
    refl_clauses = _parse_equation_clauses_and_segments_v3(refl)
    if not eq_clauses or not refl_clauses:
        return []

    eq_rhs_candidates = [seg for clause in eq_clauses for seg in clause[1:]]
    refl_rhs_list = [seg for clause in refl_clauses for seg in clause[1:]]
    if not eq_rhs_candidates or not refl_rhs_list:
        return []

    var_map = parsed.get("variable_map", {})
    all_collisions: list[dict[str, Any]] = []
    for refl_rhs in refl_rhs_list:
        best_cols: list[dict[str, Any]] | None = None
        for eq_rhs in eq_rhs_candidates:
            cols = _compare_rhs_segment_a3_v3(
                eq, refl, eq_rhs, refl_rhs, var_map, arm, item["item_id"]
            )
            if best_cols is None or len(cols) < len(best_cols):
                best_cols = cols
            if not best_cols:
                break
        if best_cols:
            all_collisions.extend(best_cols)
    return all_collisions


# ---------------------------------------------------------------------------
# Public Layer-A v3 Audit API
# ---------------------------------------------------------------------------

def run_layer_a_v3_item_check(
    parsed: dict[str, Any],
    arm: arms_v2.ArmConfigV2,
    item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run Layer-A v3 per-item checks (`A1`, `A2`, `A3` + exact rational monomial cancellation)."""
    collisions: list[dict[str, Any]] = []
    if parsed.get("ruling") not in ("keep", "invert"):
        return {"item_id": parsed.get("item_id"), "passed": True, "collisions": []}

    var_map: dict[str, str] = parsed.get("variable_map", {})
    declared_target_terms: set[str] = set()

    for raw_phys, raw_targ in var_map.items():
        if arms_v2._is_stripped_constant_var_entry(raw_phys, raw_targ):
            continue
        norm_phys = normalize_phys_token_v3(raw_phys)
        norm_targ = normalize_target_token_v3(raw_targ)
        t_toks, unknowns = extract_target_tokens_stripped_v3(
            norm_targ, arm, normalize_calculus=False
        )
        if unknowns:
            collisions.append(
                {
                    "layer": "A1_invalid_target_token",
                    "physical": raw_phys,
                    "target": raw_targ,
                    "unknowns": unknowns,
                }
            )
        if not t_toks:
            collisions.append(
                {
                    "layer": "A1_missing_target_token",
                    "physical": raw_phys,
                    "target": raw_targ,
                }
            )
        declared_target_terms.update(t_toks)
        if norm_phys in arm.partner_lookup:
            expected_targ = arm.partner_lookup[norm_phys]
            exp_toks, _ = extract_target_tokens_stripped_v3(
                expected_targ, arm, normalize_calculus=False
            )
            if set(t_toks) != set(exp_toks) and norm_targ != expected_targ:
                collisions.append(
                    {
                        "layer": "A1_partner_table_mismatch",
                        "physical": norm_phys,
                        "expected": expected_targ,
                        "got": norm_targ,
                    }
                )

    eq_latex = (item or {}).get("equation_latex", "")
    has_algebra = bool(eq_latex) and not eq_latex.strip().lower().startswith("none")
    refl_formula = parsed.get("reflected_formula", "")
    if has_algebra or (refl_formula and not refl_formula.strip().lower().startswith("none")):
        f_toks, f_unknowns = extract_target_tokens_stripped_v3(
            refl_formula, arm, normalize_calculus=True
        )
        if f_unknowns:
            collisions.append(
                {
                    "layer": "A2_formula_unknown_tokens",
                    "reflected_formula": refl_formula,
                    "unknowns": f_unknowns,
                }
            )
        if not f_toks:
            collisions.append(
                {
                    "layer": "A2_formula_no_target_tokens",
                    "reflected_formula": refl_formula,
                }
            )
        if declared_target_terms and not set(f_toks).issubset(declared_target_terms):
            undeclared = sorted(set(f_toks) - declared_target_terms)
            collisions.append(
                {
                    "layer": "A2_formula_undeclared_target_tokens",
                    "undeclared": undeclared,
                    "declared": sorted(declared_target_terms),
                    "reflected_formula": refl_formula,
                }
            )

    if item is not None:
        collisions.extend(_check_a3_formula_sign_and_monomial_v3(item, parsed, arm))

    return {
        "item_id": parsed.get("item_id"),
        "passed": len(collisions) == 0,
        "collisions": collisions,
    }


def _unpack_joint_record(rec: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(rec, tuple) and len(rec) == 2:
        return rec[0], rec[1]
    if isinstance(rec, dict):
        item = rec["item"]
        parsed = rec["output"] if "output" in rec else rec["parsed"]
        return item, parsed
    raise TypeError(f"Unsupported Layer-A record format: {type(rec).__name__}")


def run_layer_a_v3_joint_check(
    items_with_parsed: Iterable[Any],
    arm: arms_v2.ArmConfigV2,
) -> dict[str, Any]:
    """Run FULL joint Layer-A v3 audit across consensus `keep`/`invert` items in `arm`."""
    all_collisions: list[dict[str, Any]] = []

    for c in arms_v2._check_static_arm_bijection(arm):
        all_collisions.append({"layer": "A1_static_arm", **c})

    phys_to_items: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    a4_edges: list[dict[str, Any]] = [dict(e) for e in arm.baseline_sign_edges]
    per_item_reports: list[dict[str, Any]] = []

    for rec in items_with_parsed:
        item, out = _unpack_joint_record(rec)
        if out.get("ruling") not in ("keep", "invert"):
            continue
        item_res = run_layer_a_v3_item_check(out, arm, item=item)
        per_item_reports.append(item_res)
        for col in item_res["collisions"]:
            all_collisions.append({"item_id": item["item_id"], **col})

        for raw_phys, raw_targ in out.get("variable_map", {}).items():
            if arms_v2._is_stripped_constant_var_entry(raw_phys, raw_targ):
                continue
            norm_phys = normalize_phys_token_v3(raw_phys)
            norm_targ = normalize_target_token_v3(raw_targ)
            toks, unk = extract_target_tokens_stripped_v3(
                norm_targ, arm, normalize_calculus=False
            )
            sig = norm_targ if unk or not toks else " | ".join(toks)
            if len(re.sub(r"[^A-Za-z]", "", norm_phys)) >= 3:
                phys_to_items[norm_phys][sig].append(item["item_id"])

        refl_pair = _parse_equation_lhs_rhs_v3(out.get("reflected_formula", ""))
        if refl_pair is not None:
            r_lhs, r_rhs = refl_pair
            lhs_toks, lhs_unk = extract_target_tokens_stripped_v3(
                r_lhs, arm, normalize_calculus=False
            )
            if len(lhs_toks) == 1 and not lhs_unk:
                dst = lhs_toks[0]
                rhs_signs = _extract_var_signs_from_expr_v3(r_rhs, arm=arm)
                if len(rhs_signs) == 1:
                    src_tok, sg = next(iter(rhs_signs.items()))
                    if src_tok != dst:
                        a4_edges.append(
                            {"from": src_tok, "to": dst, "sign": sg, "source": item["item_id"]}
                        )

    for norm_phys, sig_map in sorted(phys_to_items.items()):
        if len(sig_map) > 1:
            all_collisions.append(
                {
                    "layer": "A1_cross_item_one_to_many",
                    "physical": norm_phys,
                    "variants": dict(sig_map),
                }
            )

    for cyc in arms_v2._find_negative_cycle(a4_edges):
        all_collisions.append(cyc)

    return {
        "arm_id": arm.arm_id,
        "evaluated_items": len(per_item_reports),
        "per_item_passed": sum(1 for r in per_item_reports if r["passed"]),
        "layer_a_collisions": all_collisions,
        "layer_a_collisions_count": len(all_collisions),
        "passes_all": len(all_collisions) == 0,
        "per_item_reports": per_item_reports,
    }


def evaluate_frozen_stage2_heldout_v3() -> dict[str, Any]:
    """Deterministically audit frozen Commit-2 `stage2_m2_heldout.json` under Layer-A v3."""
    s2 = json.loads((HARNESS_DIR / "outputs" / "stage2_m2_heldout.json").read_text(encoding="utf-8"))
    h40 = json.loads(
        (HARNESS_DIR / "openstax" / "heldout_equations_40.json").read_text(encoding="utf-8")
    )
    h40_map = {x["item_id"]: x for x in h40["items"]}

    reports: dict[str, Any] = {}
    for arm_id in ("A0", "A3-1"):
        arm = arms_v2.build_arm_v2(arm_id)
        records: list[dict[str, Any]] = []
        for entry in s2[arm_id]["items"]:
            if entry.get("consensus_4_of_5") and entry.get("majority_ruling") in ("keep", "invert"):
                records.append(
                    {"item": h40_map[entry["item_id"]], "output": entry["canonical_output"]}
                )
        reports[arm_id] = run_layer_a_v3_joint_check(records, arm)
    return reports


# ---------------------------------------------------------------------------
# Self-Test Against Frozen Commit-2 Data & 6+ Bad Mutations
# ---------------------------------------------------------------------------

def _run_self_test() -> None:
    frozen = evaluate_frozen_stage2_heldout_v3()
    a0_res = frozen["A0"]
    a3_res = frozen["A3-1"]

    assert a0_res["evaluated_items"] == 16, f"A0 evaluated={a0_res['evaluated_items']}"
    assert a0_res["per_item_passed"] == 16, f"A0 passed={a0_res['per_item_passed']}: {a0_res['layer_a_collisions']}"
    assert a0_res["layer_a_collisions_count"] == 0, f"A0 collisions={a0_res['layer_a_collisions']}"
    assert a0_res["passes_all"] is True

    assert a3_res["evaluated_items"] == 16, f"A3 evaluated={a3_res['evaluated_items']}"
    assert a3_res["per_item_passed"] == 15, f"A3 passed={a3_res['per_item_passed']}: {a3_res['layer_a_collisions']}"
    assert a3_res["passes_all"] is False
    a3_e001_layers = [
        c["layer"] for c in a3_res["layer_a_collisions"] if c.get("item_id") == "E001"
    ]
    assert "A1_invalid_target_token" in a3_e001_layers, f"Missing E001 A1 fail: {a3_e001_layers}"
    assert any(
        c["layer"] == "A1_cross_item_one_to_many" and c.get("physical") == "alpha"
        for c in a3_res["layer_a_collisions"]
    ), f"Missing A1 alpha bijection collision: {a3_res['layer_a_collisions']}"

    arm_a0 = arms_v2.build_arm_v2("A0")

    # Mutation 1: quotient flip F = m a -> Frequency = Movement / Appreciation
    m1 = run_layer_a_v3_item_check(
        {
            "item_id": "M1",
            "ruling": "keep",
            "variable_map": {"F": "Frequency", "m": "Movement", "a": "Appreciation"},
            "reflected_formula": "Frequency = Movement / Appreciation",
        },
        arm_a0,
        item={"item_id": "M1", "equation_latex": "F = m a"},
    )
    assert not m1["passed"] and any(c["layer"].startswith("A3_") for c in m1["collisions"]), m1

    # Mutation 2: sign flip Delta x = x_f - x_i -> Vibration = Vibration_f + Vibration_i
    m2 = run_layer_a_v3_item_check(
        {
            "item_id": "M2",
            "ruling": "keep",
            "variable_map": {"Delta x": "Vibration", "x_f": "Vibration (f)", "x_i": "Vibration (i)"},
            "reflected_formula": "Vibration = Vibration_f + Vibration_i",
        },
        arm_a0,
        item={"item_id": "M2", "equation_latex": "\\Delta x = x_{\\text{f}} - x_{\\text{i}}"},
    )
    assert not m2["passed"] and any(c["layer"].startswith("A3_") for c in m2["collisions"]), m2

    # Mutation 3: uncanceled inverse on a_CM = R * alpha
    m3 = run_layer_a_v3_item_check(
        {
            "item_id": "E001",
            "ruling": "keep",
            "variable_map": {"a_CM": "Appreciation", "R": "Vibration", "alpha": "Appreciation / Vibration"},
            "reflected_formula": "Appreciation = (1 / Vibration) * (Appreciation / Vibration)",
        },
        arm_a0,
        item={"item_id": "E001", "equation_latex": "a_{\\text{CM}} = R \\alpha"},
    )
    assert not m3["passed"] and any(c["layer"].startswith("A3_") for c in m3["collisions"]), m3

    # Mutation 4: unknown hallucinated token in formula (A2)
    m4 = run_layer_a_v3_item_check(
        {
            "item_id": "M4",
            "ruling": "keep",
            "variable_map": {"a": "Appreciation", "r": "Vibration"},
            "reflected_formula": "Appreciation = Vibration * etherflux",
        },
        arm_a0,
        item={"item_id": "M4", "equation_latex": "a = r"},
    )
    assert not m4["passed"] and any(c["layer"].startswith("A2_") for c in m4["collisions"]), m4

    # Mutation 5: cross-item alpha bijection split (A1)
    m5 = run_layer_a_v3_joint_check(
        [
            {
                "item": {"item_id": "S1", "equation_latex": "a_{\\text{CM}} = R \\alpha"},
                "output": {
                    "item_id": "S1",
                    "ruling": "keep",
                    "variable_map": {"a_CM": "Appreciation", "R": "Vibration", "alpha": "Appreciation / Vibration"},
                    "reflected_formula": "Appreciation = Vibration * (Appreciation / Vibration)",
                },
            },
            {
                "item": {"item_id": "S2", "equation_latex": "a_{\\text{t}} = r \\alpha"},
                "output": {
                    "item_id": "S2",
                    "ruling": "keep",
                    "variable_map": {"a_t": "Appreciation", "r": "Vibration", "alpha": "Appreciation"},
                    "reflected_formula": "Appreciation = Vibration * Appreciation",
                },
            },
        ],
        arm_a0,
    )
    assert not m5["passes_all"] and any(
        c["layer"] == "A1_cross_item_one_to_many" and c.get("physical") == "alpha"
        for c in m5["layer_a_collisions"]
    ), m5

    # Mutation 6: A4 opposing-sign cycle across items (`Frequency -> Desire (+)` + `Desire -> Movement (+)` + `Movement -> Frequency (-)`)
    m6 = run_layer_a_v3_joint_check(
        [
            {
                "item": {"item_id": "C1", "equation_latex": "\\rho = k F"},
                "output": {
                    "item_id": "C1",
                    "ruling": "keep",
                    "variable_map": {"rho": "Desire", "F": "Frequency"},
                    "reflected_formula": "Desire = -Frequency",
                },
            },
        ],
        arm_a0,
    )
    assert not m6["passes_all"] and any(
        c["layer"].startswith("A4_") for c in m6["layer_a_collisions"]
    ), m6


if __name__ == "__main__":
    _run_self_test()
    print("LAYER_A_V3_SELF_TEST_OK")
