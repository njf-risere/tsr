#!/usr/bin/env python3
"""Prepare frozen OpenStax University Physics equations sample (seed = 20261115).

Fetches all 153 CNXML modules across the 22 chapters of
`openstax/osbooks-university-physics-bundle` at pinned commit
`2300d5b8ca2571dacc6ec25ebef56ba8d49000a2`, extracts the 321 Key Equations rows,
applies deterministic E1-E4 exclusions (52 excluded -> 269 eligible across 20
physical chapters), samples 2 equations per chapter (28 Core + 12 Boundary = 40),
shuffles and assigns neutral IDs E001..E040, emits calibration_equations_17.json
(K01..K17 from rule/tsr_formal_port.py:ROWS), and verifies `--verify-offline`.

Python 3.12+ standard library only.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import random
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OPENSTAX_DIR = Path(__file__).resolve().parent
HARNESS_DIR = OPENSTAX_DIR.parent
REPO_ROOT = HARNESS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rule.tsr_formal_port import ROWS as FORMAL_ROWS_17  # noqa: E402

ATTRIBUTION = "Access for free at https://openstax.org — Licensed under CC BY 4.0."
BUNDLE_REPO = "openstax/osbooks-university-physics-bundle"
BUNDLE_COMMIT_SHA = "2300d5b8ca2571dacc6ec25ebef56ba8d49000a2"
SAMPLING_SEED = 20261115
SAMPLES_PER_CHAPTER = 2

MANIFEST_PATH = OPENSTAX_DIR / "openstax_fetch_manifest.json"
RAW_CSV_PATH = OPENSTAX_DIR / "openstax_key_equations_raw.csv"
EXCLUSION_CSV_PATH = OPENSTAX_DIR / "exclusion_log.csv"
HELDOUT_40_PATH = OPENSTAX_DIR / "heldout_equations_40.json"
SAMPLE_MANIFEST_PATH = OPENSTAX_DIR / "sample_manifest.json"
CALIBRATION_17_PATH = OPENSTAX_DIR / "calibration_equations_17.json"
LEGACY_EXT_KEY_PATH = REPO_ROOT / "tests" / "extension-test-key.md"

CNXML_NS = "http://cnx.rice.edu/cnxml"
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
HTTP_TIMEOUT_SEC = 30
USER_AGENT = "TSRResearchAudit/1.0 (https://github.com/njfio/tsr)"

INCLUDED_CHAPTERS: list[tuple[int, int, str]] = [
    (1, 1, "Units and Measurement"),
    (1, 2, "Vectors"),
    (1, 3, "Motion Along a Straight Line"),
    (1, 4, "Motion in Two and Three Dimensions"),
    (1, 5, "Newton's Laws of Motion"),
    (1, 6, "Applications of Newton's Laws"),
    (1, 7, "Work and Kinetic Energy"),
    (1, 8, "Potential Energy and Conservation of Energy"),
    (1, 9, "Linear Momentum and Collisions"),
    (1, 10, "Fixed-Axis Rotation"),
    (1, 11, "Angular Momentum"),
    (1, 12, "Static Equilibrium and Elasticity"),
    (1, 13, "Gravitation"),
    (1, 14, "Fluid Mechanics"),
    (1, 15, "Oscillations"),
    (1, 16, "Waves"),
    (1, 17, "Sound"),
    (2, 1, "Temperature and Heat"),
    (2, 2, "The Kinetic Theory of Gases"),
    (2, 3, "The First Law of Thermodynamics"),
    (2, 4, "The Second Law of Thermodynamics"),
    (3, 5, "Relativity"),
]

BOUNDARY_CHAPTERS: frozenset[tuple[str, int]] = frozenset(
    {
        ("1", 14),
        ("1", 17),
        ("2", 1),
        ("2", 2),
        ("2", 3),
        ("2", 4),
    }
)

CORE_CHAPTERS: frozenset[tuple[str, int]] = frozenset(
    {("1", ch) for ch in range(3, 14)} | {("1", 15), ("1", 16), ("3", 5)}
)

CONSTRUCTION_ROW_NUMS: frozenset[int] = frozenset({7, 14, 15, 16})

CALIBRATION_17_SPECS: list[tuple[int, str, str]] = [
    (
        1,
        "First postulate of special relativity (the laws of physics are the same for every inertial observer)",
        "None (qualitative physical principle)",
    ),
    (
        2,
        "Relativity of simultaneity (two observers in relative motion do not share a simultaneous now because of spatial separation)",
        r"\Delta t = \frac{\gamma v \Delta x}{c^{2}} \quad (\text{for } \Delta t' = 0)",
    ),
    (
        3,
        "Principle of relativity (there is no preferred fixed inertial rest frame)",
        "None (qualitative physical principle)",
    ),
    (
        4,
        "Special versus general relativity (equivalence of inertial frames versus accelerating or gravitating frames)",
        "None (qualitative physical principle)",
    ),
    (
        5,
        "Relativistic time dilation between proper time and moving-frame coordinate time",
        r"\Delta t = \gamma \Delta \tau = \frac{\Delta \tau}{\sqrt{1 - v^{2}/c^{2}}}",
    ),
    (
        6,
        "Relativistic length contraction along the direction of relative motion",
        r"L = \frac{L_{0}}{\gamma} = L_{0} \sqrt{1 - \frac{v^{2}}{c^{2}}}",
    ),
    (
        7,
        "Mass-energy equivalence",
        r"E = m c^{2}",
    ),
    (
        8,
        "Relativistic kinetic energy and the rising energy cost of increasing speed for mass",
        r"K = (\gamma - 1) m c^{2}, \quad E = \gamma m c^{2}",
    ),
    (
        9,
        "Speed-of-light limit for massive particles (nothing with mass can reach the speed of light c)",
        r"v < c \quad (\gamma \to \infty \text{ as } v \to c \text{ for } m > 0)",
    ),
    (
        10,
        "Spacetime as one unified four-dimensional continuum (invariant spacetime interval)",
        r"s^{2} = c^{2} (\Delta t)^{2} - (\Delta x)^{2} - (\Delta y)^{2} - (\Delta z)^{2}",
    ),
    (
        11,
        "Mass-energy warps spacetime geometry",
        "None (qualitative physical principle)",
    ),
    (
        12,
        "Gravitational wells and gravitational lensing of light around massive bodies",
        "None (qualitative physical principle)",
    ),
    (
        13,
        "Conservation of total energy in an isolated physical system",
        r"E_{\text{i}} = E_{\text{f}} \quad (\Delta E_{\text{sys}} = 0)",
    ),
    (
        14,
        "Newton's third law of motion (reciprocal action-reaction force pair)",
        r"\vec{F}_{AB} = -\vec{F}_{BA}",
    ),
    (
        15,
        "Mass as the product of mass density and volume",
        r"m = \rho V",
    ),
    (
        16,
        "Newton's second law of motion (net force equals mass times acceleration)",
        r"\vec{F}_{\text{net}} = m \vec{a}",
    ),
    (
        17,
        "Boyle's law for an ideal gas (at constant temperature and fixed amount of gas, squeezing the volume raises the pressure)",
        r"P_{1} V_{1} = P_{2} V_{2} \quad (\text{constant } T, n)",
    ),
]

GREEK_AND_SYMBOL_MAP: dict[str, str] = {
    "\u03b1": r"\alpha",
    "\u03b2": r"\beta",
    "\u03b3": r"\gamma",
    "\u03b4": r"\delta",
    "\u03b5": r"\varepsilon",
    "\u03b7": r"\eta",
    "\u03b8": r"\theta",
    "\u03ba": r"\kappa",
    "\u03bb": r"\lambda",
    "\u03bc": r"\mu",
    "\u03c0": r"\pi",
    "\u03c1": r"\rho",
    "\u03c3": r"\sigma",
    "\u03c4": r"\tau",
    "\u03c6": r"\phi",
    "\u03d5": r"\phi",
    "\u03c9": r"\omega",
    "\u0394": r"\Delta",
    "\u0392": "B",
    "\u03a4": "T",
    "\u2211": r"\sum",
    "\u222b": r"\int",
    "\u222e": r"\oint",
    "\u2202": r"\partial",
    "\u00b1": r"\pm",
    "\u2213": r"\mp",
    "\u00d7": r"\times",
    "\u00b7": r"\cdot",
    "\u2264": r"\le",
    "\u2265": r"\ge",
    "\u2261": r"\equiv",
    "\u21d4": r"\Leftrightarrow",
    "\u2192": r"\to",
    "\u2225": r"\parallel",
    "\u22a5": r"\perp",
    "\u2212": "-",
    "\u2013": "-",
    "\u2032": "'",
    "\u2026": r"\dots",
    "\u22ef": r"\cdots",
    "\u2329": r"\langle",
    "\u232a": r"\rangle",
    "\u00b0": r"^\circ",
}

FUNCTION_NAMES = {"sin", "cos", "tan", "ln", "log", "lim", "max", "min"}
PUNCT_MTEXT = {",", ";", "(", ")", "[", "]", "/", "=", "+", "-", "."}

E2_BENCHMARK_17_OVERLAP_BY_KEY: dict[tuple[int, int, int], tuple[int, str]] = {
    (1, 5, 3): (16, "Restates benchmark Row 16 (Newton's second law, vector form F_net = ma)."),
    (1, 5, 4): (16, "Restates benchmark Row 16 (Newton's second law, scalar form F_net = ma)."),
    (1, 5, 5): (16, "Restates benchmark Row 16 (Newton's second law, component form sum F = ma)."),
    (1, 5, 6): (16, "Restates benchmark Row 16 (Newton's second law, momentum form F_net = dp/dt)."),
    (1, 5, 9): (14, "Restates benchmark Row 14 (Newton's third law, F_AB = -F_BA)."),
    (1, 8, 8): (13, "Restates benchmark Row 13 (closed-system total energy conservation Delta E = 0)."),
    (1, 9, 5): (16, "Restates benchmark Row 16 (Newton's second law in momentum form F = dp/dt)."),
    (1, 9, 10): (16, "Restates benchmark Row 16 (Newton's second law for an extended object F = dp_CM/dt)."),
    (1, 14, 1): (15, "Restates benchmark Row 15 (mass density definition rho = m/V)."),
    (3, 5, 1): (5, "Restates benchmark Row 5 (relativistic time dilation Delta t = gamma Delta tau)."),
    (3, 5, 2): (5, "Restates benchmark Row 5 (Lorentz factor gamma = 1/sqrt(1 - v^2/c^2))."),
    (3, 5, 3): (6, "Restates benchmark Row 6 (relativistic length contraction L = L_0 / gamma)."),
    (3, 5, 13): (10, "Restates benchmark Row 10 (invariant spacetime interval (Delta s)^2)."),
    (3, 5, 14): (10, "Restates benchmark Row 10 (invariant spacetime proper-time interval (Delta tau)^2)."),
    (3, 5, 19): (8, "Restates benchmark Row 8 (relativistic total energy E = gamma m c^2)."),
    (3, 5, 20): (8, "Restates benchmark Row 8 (relativistic kinetic energy K = (gamma - 1) m c^2)."),
}


@dataclass(frozen=True)
class RawEquationRow:
    volume: int
    chapter: int
    chapter_title: str
    row_idx: int
    eq_number: str
    description: str
    equation_latex: str
    source_url: str
    retrieved_utc: str

    def sort_key(self) -> tuple[int, int, int]:
        return (self.volume, self.chapter, self.row_idx)


@dataclass(frozen=True)
class EligibleLawRow:
    volume: int
    chapter: int
    chapter_title: str
    row_idx: int
    eq_number: str
    description: str
    equation_latex: str
    source_url: str
    stratum: str

    def sort_key(self) -> tuple[int, int, int]:
        return (self.volume, self.chapter, self.row_idx)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _http_get_with_status(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
        status = int(getattr(resp, "status", 200))
        data = resp.read()
    if status != 200:
        raise RuntimeError(f"Unexpected HTTP {status} fetching {url}")
    return status, data


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


def _norm_math_chars(text: str) -> str:
    cleaned = text.replace("\u200b", "").replace("\ufeff", "")
    return "".join(GREEK_AND_SYMBOL_MAP.get(ch, ch) for ch in cleaned)


def _join_tokens(tokens: list[str]) -> str:
    out = ""
    for tok in tokens:
        if not tok:
            continue
        if not out:
            out = tok
            continue
        if tok in {",", ";", ")", "]", "'", r"^\circ"} or tok.startswith(("_{", "^{")):
            out += tok
        elif out.endswith(("(", "[", "{", "_{", "^{")):
            out += tok
        elif out.endswith("'") and tok in {"=", "+", "-", ",", ";", ")", "]"}:
            out += tok
        else:
            out += " " + tok
    return out


def _mml_to_tex(node: ET.Element, inline_prose: bool = False) -> str:
    tag = _local_tag(node)
    if tag in {"math", "mrow", "mstyle", "mtd"}:
        children = list(node)
        tokens: list[str] = []
        i = 0
        while i < len(children):
            c = children[i]
            ctag = _local_tag(c)
            if ctag == "mo" and (c.text or "").strip() == "{" and i + 1 < len(children):
                nxt = children[i + 1]
                nxt_tag = _local_tag(nxt)
                table_node = None
                if nxt_tag == "mtable":
                    table_node = nxt
                elif nxt_tag == "mrow" and len(list(nxt)) == 1 and _local_tag(list(nxt)[0]) == "mtable":
                    table_node = list(nxt)[0]
                if table_node is not None:
                    case_rows = []
                    for mtr in table_node:
                        cells = [_mml_to_tex(mtd, inline_prose=inline_prose).strip() for mtd in mtr]
                        case_rows.append(" & ".join(cells).rstrip(","))
                    tokens.append(r"\begin{cases} " + r" \\ ".join(case_rows) + r" \end{cases}")
                    i += 2
                    continue
            if ctag == "mspace":
                width = c.attrib.get("width", "")
                prev_tok = tokens[-1] if tokens else ""
                next_tok = _mml_to_tex(children[i + 1], inline_prose=inline_prose) if i + 1 < len(children) else ""
                if (
                    width.startswith(("0.4", "0.5", "0.6", "1"))
                    and prev_tok not in {",", ";"}
                    and not next_tok.startswith(("(", r"\text{"))
                    and "=" in prev_tok + "".join(tokens[-6:])
                ):
                    tokens.append(";")
                i += 1
                continue
            rendered = _mml_to_tex(c, inline_prose=inline_prose).strip()
            if rendered:
                tokens.append(rendered)
            i += 1
        return _join_tokens(tokens)

    if tag == "mspace":
        return ""
    if tag == "mi":
        raw = (node.text or "").replace("\u200b", "").strip()
        if not raw:
            return ""
        return ("\\" + raw) if raw in FUNCTION_NAMES else _norm_math_chars(raw)
    if tag in {"mn", "mo"}:
        return _norm_math_chars((node.text or "").strip())
    if tag == "mtext":
        raw = (node.text or "").replace("\u200b", "").replace("\ufeff", "").strip()
        if not raw:
            return ""
        if raw == "\u0394":
            return r"\Delta"
        if raw in {"\u2212", "\u2013"}:
            return "-"
        if raw == "\u00b0":
            return r"^\circ"
        if raw in {",...", ",\u2026"}:
            return r", \dots"
        if raw in {"...", "\u2026"}:
            return r"\dots"
        if raw in PUNCT_MTEXT:
            return raw
        if raw in FUNCTION_NAMES:
            return "\\" + raw
        return _norm_math_chars(raw) if inline_prose else (r"\text{" + _norm_math_chars(raw) + "}")
    if tag == "mfrac":
        ch = list(node)
        if len(ch) == 2:
            num = _mml_to_tex(ch[0], inline_prose=inline_prose).strip()
            den = _mml_to_tex(ch[1], inline_prose=inline_prose).strip()
            return r"\frac{" + num + "}{" + den + "}"
        return "".join(_mml_to_tex(c, inline_prose=inline_prose) for c in ch)
    if tag == "msqrt":
        inner = _join_tokens([_mml_to_tex(c, inline_prose=inline_prose).strip() for c in node])
        return r"\sqrt{" + inner + "}"
    if tag == "msub":
        ch = list(node)
        base = _mml_to_tex(ch[0], inline_prose=inline_prose).strip()
        sub = _mml_to_tex(ch[1], inline_prose=inline_prose).strip()
        return f"{base}_{{{sub}}}" if sub else base
    if tag == "msup":
        ch = list(node)
        base = _mml_to_tex(ch[0], inline_prose=inline_prose).strip()
        sup = _mml_to_tex(ch[1], inline_prose=inline_prose).strip()
        if not sup:
            return base
        return f"{base}'" if sup == "'" else f"{base}^{{{sup}}}"
    if tag == "msubsup":
        ch = list(node)
        base = _mml_to_tex(ch[0], inline_prose=inline_prose).strip()
        sub = _mml_to_tex(ch[1], inline_prose=inline_prose).strip()
        sup = _mml_to_tex(ch[2], inline_prose=inline_prose).strip()
        res = base + (f"_{{{sub}}}" if sub else "")
        if sup:
            res += "'" if sup == "'" else f"^{{{sup}}}"
        return res
    if tag == "mover":
        ch = list(node)
        base = _mml_to_tex(ch[0], inline_prose=inline_prose).strip()
        acc = "".join(ch[1].itertext()).replace("\u200b", "").strip()
        if acc == "\u2192":
            return r"\vec{" + base + "}"
        if acc == "^":
            return r"\hat{" + base + "}"
        if acc in {"\u00af", "\u2013", "-"}:
            return (r"\bar{" + base + "}") if len(base) <= 3 else (r"\overline{" + base + "}")
        return base
    if tag == "munder":
        ch = list(node)
        base = _mml_to_tex(ch[0], inline_prose=inline_prose).strip()
        sub = _mml_to_tex(ch[1], inline_prose=inline_prose).strip()
        return f"{base}_{{{sub}}}" if sub else base
    if tag == "munderover":
        ch = list(node)
        base = _mml_to_tex(ch[0], inline_prose=inline_prose).strip()
        sub = _mml_to_tex(ch[1], inline_prose=inline_prose).strip()
        sup = _mml_to_tex(ch[2], inline_prose=inline_prose).strip()
        res = base + (f"_{{{sub}}}" if sub else "")
        if sup:
            res += f"^{{{sup}}}"
        return res
    if tag == "mtable":
        rows = []
        for mtr in node:
            cells = [_mml_to_tex(mtd, inline_prose=inline_prose).strip() for mtd in mtr]
            rows.append(" & ".join(cells))
        return "; ".join(rows)
    return _join_tokens([_mml_to_tex(c, inline_prose=inline_prose).strip() for c in node])


def _extract_entry_description(entry: ET.Element) -> str:
    parts: list[str] = []

    def walk(el: ET.Element) -> None:
        tag = _local_tag(el)
        if tag == "math":
            parts.append(_mml_to_tex(el, inline_prose=True))
            if el.tail:
                parts.append(el.tail)
            return
        if tag == "newline":
            parts.append(" ")
            if el.tail:
                parts.append(el.tail)
            return
        if el.text:
            parts.append(el.text)
        for child in el:
            walk(child)
        if el.tail:
            parts.append(el.tail)

    walk(entry)
    text = re.sub(r"\s+", " ", "".join(parts)).strip()
    return text.replace("\u2019", "'").replace("\u2018", "'")


def _extract_entry_equation_latex(entry: ET.Element) -> str:
    maths = entry.findall(f".//{{{MATHML_NS}}}math")
    if not maths:
        maths = [el for el in entry.iter() if _local_tag(el) == "math"]
    if not maths:
        return ""
    rendered = " ".join(_mml_to_tex(m) for m in maths)
    rendered = re.sub(r"\s+", " ", rendered).strip()
    rendered = re.sub(r"\s*([.,]+)$", lambda m: "" if m.group(1) in {".", ","} else m.group(0), rendered)
    return rendered.strip()


def _parse_collection_chapters(xml_bytes: bytes, volume: int) -> dict[str, list[str]]:
    root = ET.fromstring(xml_bytes)
    expected_titles = {t for v, _, t in INCLUDED_CHAPTERS if v == volume}
    found: dict[str, list[str]] = {}

    def walk(node: ET.Element) -> None:
        for child in node:
            tag = _local_tag(child)
            if tag == "subcollection":
                title = ""
                mods: list[str] = []
                for sub in child:
                    stag = _local_tag(sub)
                    if stag == "title" and sub.text:
                        title = re.sub(r"\s+", " ", sub.text).strip()
                    elif stag == "content":
                        for m in sub:
                            if _local_tag(m) == "module" and "document" in m.attrib:
                                mods.append(m.attrib["document"])
                if title in expected_titles:
                    found[title] = mods
                for sub in child:
                    if _local_tag(sub) == "content":
                        walk(sub)
            elif tag == "content":
                walk(child)

    walk(root)
    return found


def _extract_rows_from_cnxml(
    cnxml_bytes: bytes,
    volume: int,
    chapter: int,
    chapter_title: str,
    source_url: str,
    retrieved_utc: str,
) -> tuple[list[RawEquationRow], list[dict[str, Any]]]:
    root = ET.fromstring(cnxml_bytes)
    rows_out: list[RawEquationRow] = []
    skipped_headers: list[dict[str, Any]] = []
    for sec in root.iter(f"{{{CNXML_NS}}}section"):
        if sec.attrib.get("class") != "key-equations":
            continue
        last_desc = ""
        for idx, row_el in enumerate(sec.findall(f".//{{{CNXML_NS}}}row"), start=1):
            entries = row_el.findall(f"{{{CNXML_NS}}}entry")
            if len(entries) < 2:
                continue
            desc = _extract_entry_description(entries[0])
            eq_tex = _extract_entry_equation_latex(entries[1])
            if not eq_tex:
                skipped_headers.append({"table_row_idx": idx, "text": desc})
                continue
            if not desc:
                desc = last_desc
            else:
                last_desc = desc
            rows_out.append(
                RawEquationRow(
                    volume=volume,
                    chapter=chapter,
                    chapter_title=chapter_title,
                    row_idx=idx,
                    eq_number="",
                    description=desc,
                    equation_latex=eq_tex,
                    source_url=source_url,
                    retrieved_utc=retrieved_utc,
                )
            )
    return rows_out, skipped_headers


def fetch_pinned_openstax() -> tuple[dict[str, Any], list[RawEquationRow]]:
    """Fetch all 153 CNXML modules at pinned commit 2300d5b8ca2571dacc6ec25ebef56ba8d49000a2."""
    retrieved_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    collection_meta: dict[int, tuple[str, int, str, dict[str, list[str]]]] = {}
    collection_records: list[dict[str, Any]] = []

    for vol in (1, 2, 3):
        col_url = (
            f"https://raw.githubusercontent.com/{BUNDLE_REPO}/{BUNDLE_COMMIT_SHA}/"
            f"collections/university-physics-volume-{vol}.collection.xml"
        )
        status, col_bytes = _http_get_with_status(col_url)
        col_sha = _sha256_bytes(col_bytes)
        chapters_map = _parse_collection_chapters(col_bytes, vol)
        collection_meta[vol] = (col_url, status, col_sha, chapters_map)
        collection_records.append(
            {"volume": vol, "url": col_url, "http_status": status, "sha256": col_sha}
        )

    for vol, ch, ch_title in INCLUDED_CHAPTERS:
        if ch_title not in collection_meta[vol][3]:
            raise RuntimeError(f"Missing chapter in collection XML: Vol {vol} Ch {ch} ({ch_title})")

    module_tasks: list[tuple[int, int, str, str, str]] = []
    for vol, ch, ch_title in INCLUDED_CHAPTERS:
        for mod_id in collection_meta[vol][3][ch_title]:
            mod_url = (
                f"https://raw.githubusercontent.com/{BUNDLE_REPO}/{BUNDLE_COMMIT_SHA}/"
                f"modules/{mod_id}/index.cnxml"
            )
            module_tasks.append((vol, ch, ch_title, mod_id, mod_url))

    if len(module_tasks) != 153:
        raise RuntimeError(f"Expected 153 OpenStax modules across 22 chapters, got {len(module_tasks)}")

    def _download_mod(task: tuple[int, int, str, str, str]) -> tuple[tuple[int, int, str, str, str], int, bytes]:
        status, raw_bytes = _http_get_with_status(task[4])
        return task, status, raw_bytes

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        downloaded = list(pool.map(_download_mod, module_tasks))

    by_chapter_mods: dict[tuple[int, int], list[tuple[str, str, int, str, bytes]]] = {}
    module_manifests: list[dict[str, Any]] = []
    for (vol, ch, _title, mod_id, mod_url), status, raw_bytes in downloaded:
        sha = _sha256_bytes(raw_bytes)
        by_chapter_mods.setdefault((vol, ch), []).append((mod_id, mod_url, status, sha, raw_bytes))
        module_manifests.append(
            {
                "volume": vol,
                "chapter": ch,
                "module_id": mod_id,
                "url": mod_url,
                "http_status": status,
                "sha256": sha,
                "byte_length": len(raw_bytes),
            }
        )

    all_rows: list[RawEquationRow] = []
    chapter_manifests: list[dict[str, Any]] = []
    for vol, ch, ch_title in INCLUDED_CHAPTERS:
        col_url, _, col_sha, chapters_map = collection_meta[vol]
        mod_ids = chapters_map[ch_title]
        chapter_rows: list[RawEquationRow] = []
        skipped_headers: list[dict[str, Any]] = []
        key_mod_id = ""
        key_url = ""
        key_sha = ""
        for mod_id, mod_url, _status, mod_sha, mod_bytes in by_chapter_mods[(vol, ch)]:
            extracted, skipped = _extract_rows_from_cnxml(
                mod_bytes, vol, ch, ch_title, mod_url, retrieved_utc
            )
            if extracted or skipped:
                key_mod_id = mod_id
                key_url = mod_url
                key_sha = mod_sha
                chapter_rows.extend(extracted)
                skipped_headers.extend(skipped)
        if not key_mod_id:
            raise RuntimeError(f"No key-equations module found in Vol {vol} Ch {ch} ({ch_title})")
        all_rows.extend(chapter_rows)
        chapter_manifests.append(
            {
                "volume": vol,
                "chapter": ch,
                "chapter_title": ch_title,
                "collection_url": col_url,
                "collection_sha256": col_sha,
                "module_ids": mod_ids,
                "key_equations_module_id": key_mod_id,
                "key_equations_url": key_url,
                "key_equations_sha256": key_sha,
                "raw_row_count": len(chapter_rows),
                "skipped_non_equation_rows": skipped_headers,
            }
        )

    all_rows.sort(key=lambda r: r.sort_key())
    if len(all_rows) != 321:
        raise RuntimeError(f"Expected 321 raw Key Equations rows, got {len(all_rows)}")

    manifest: dict[str, Any] = {
        "attribution": ATTRIBUTION,
        "bundle_repo": BUNDLE_REPO,
        "bundle_commit_sha": BUNDLE_COMMIT_SHA,
        "retrieved_utc": retrieved_utc,
        "total_chapters": len(chapter_manifests),
        "total_modules": len(module_manifests),
        "total_raw_rows": len(all_rows),
        "collections": collection_records,
        "chapters": chapter_manifests,
        "modules": module_manifests,
    }
    return manifest, all_rows


def _normalize_formula_key(eq_latex: str) -> str:
    s = eq_latex.lower()
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = re.sub(r"[\\{}\s.,;]", "", s)
    return s


def classify_and_filter_rows(
    raw_rows: list[RawEquationRow],
) -> tuple[list[dict[str, str]], list[EligibleLawRow]]:
    """Apply deterministic E1-E4 exclusions in canonical (volume, chapter, row_idx) order."""
    ordered = sorted(raw_rows, key=lambda r: r.sort_key())
    exclusions: list[dict[str, str]] = []
    retained: list[RawEquationRow] = []
    seen_formula_by_law: dict[str, tuple[int, int, int, str]] = {}

    for row in ordered:
        key = row.sort_key()
        desc_l = row.description.lower()

        # E1_PURE_MATH
        e1_reason = ""
        if (row.volume, row.chapter) == (1, 1) and "percent uncertainty" in desc_l:
            e1_reason = "Pure algebraic percentage/relative-uncertainty formula with no physical quantity."
        elif (row.volume, row.chapter) == (1, 2):
            e1_reason = (
                "Chapter 2 Vectors identity: pure vector algebra, components, polar coordinates, "
                "or dot/cross product formula with no physical law relationship."
            )
        elif (row.volume, row.chapter) == (1, 13) and "conic sections" in desc_l:
            e1_reason = "Pure polar geometric equation of conic sections (alpha/r = 1 + e cos theta) without physical quantities."

        if e1_reason:
            exclusions.append(
                {
                    "volume": str(row.volume),
                    "chapter": str(row.chapter),
                    "row_idx": str(row.row_idx),
                    "eq_number": row.eq_number,
                    "description": row.description,
                    "equation_latex": row.equation_latex,
                    "exclusion_code": "E1_PURE_MATH",
                    "matched_benchmark_id": "",
                    "rationale": e1_reason,
                }
            )
            continue

        # E2_BENCHMARK_17_OVERLAP
        if key in E2_BENCHMARK_17_OVERLAP_BY_KEY:
            bm_id, reason = E2_BENCHMARK_17_OVERLAP_BY_KEY[key]
            exclusions.append(
                {
                    "volume": str(row.volume),
                    "chapter": str(row.chapter),
                    "row_idx": str(row.row_idx),
                    "eq_number": row.eq_number,
                    "description": row.description,
                    "equation_latex": row.equation_latex,
                    "exclusion_code": "E2_BENCHMARK_17_OVERLAP",
                    "matched_benchmark_id": str(bm_id),
                    "rationale": reason,
                }
            )
            continue

        # E3_DUPLICATE_VARIANT
        norm_eq = _normalize_formula_key(row.equation_latex)
        if key == (1, 10, 23) and "work-energy theorem" in desc_l:
            norm_eq = _normalize_formula_key(r"W_{net} = K_B - K_A")
        e3_reason = ""
        if norm_eq in seen_formula_by_law:
            prev_v, prev_c, prev_idx, prev_desc = seen_formula_by_law[norm_eq]
            same_law_pairs = {
                ("Total acceleration", "Total acceleration"),
                ("Work-energy theorem", "Work-energy theorem"),
                ("Speed of a compression wave in a fluid", "Speed of sound in a fluid"),
            }
            if prev_desc == row.description or (prev_desc, row.description) in same_law_pairs:
                e3_reason = (
                    f"Duplicate variant of earlier retained law V{prev_v} Ch.{prev_c} row {prev_idx} "
                    f"({prev_desc!r})."
                )
        if e3_reason:
            exclusions.append(
                {
                    "volume": str(row.volume),
                    "chapter": str(row.chapter),
                    "row_idx": str(row.row_idx),
                    "eq_number": row.eq_number,
                    "description": row.description,
                    "equation_latex": row.equation_latex,
                    "exclusion_code": "E3_DUPLICATE_VARIANT",
                    "matched_benchmark_id": "",
                    "rationale": e3_reason,
                }
            )
            continue

        # E4_NON_EQUATION
        has_rel_var = bool(re.search(r"[a-zA-Z\\]", row.equation_latex))
        is_unit_conversion = (
            ("unit conversion" in desc_l or "conversion factor" in desc_l)
            and not any(tok in desc_l for tok in ("velocity", "force", "energy", "pressure", "heat", "wave", "sound"))
        )
        is_bare_constant = (
            re.fullmatch(
                r"[A-Za-z_\\{}]+\s*=\s*[-+]?\d+(?:\.\d+)?(?:\s*\\times\s*10\^\{[-+]?\d+\})?(?:\s*\\text\{[^}]+\})?",
                row.equation_latex.strip(),
            )
            is not None
            and not has_rel_var
        )
        if not row.equation_latex.strip() or is_unit_conversion or is_bare_constant:
            exclusions.append(
                {
                    "volume": str(row.volume),
                    "chapter": str(row.chapter),
                    "row_idx": str(row.row_idx),
                    "eq_number": row.eq_number,
                    "description": row.description,
                    "equation_latex": row.equation_latex,
                    "exclusion_code": "E4_NON_EQUATION",
                    "matched_benchmark_id": "",
                    "rationale": "Non-equation header, bare numerical constant, or pure unit-conversion ratio.",
                }
            )
            continue

        seen_formula_by_law.setdefault(norm_eq, (row.volume, row.chapter, row.row_idx, row.description))
        retained.append(row)

    eligible: list[EligibleLawRow] = []
    for row in retained:
        tag = (str(row.volume), row.chapter)
        if tag in BOUNDARY_CHAPTERS:
            stratum = "Boundary"
        elif tag in CORE_CHAPTERS:
            stratum = "Core"
        else:
            raise RuntimeError(f"Eligible row belongs to uncategorized chapter {tag}")
        eligible.append(
            EligibleLawRow(
                volume=row.volume,
                chapter=row.chapter,
                chapter_title=row.chapter_title,
                row_idx=row.row_idx,
                eq_number=row.eq_number,
                description=row.description,
                equation_latex=row.equation_latex,
                source_url=row.source_url,
                stratum=stratum,
            )
        )

    if len(exclusions) != 52:
        raise RuntimeError(f"Expected 52 excluded rows, got {len(exclusions)}")
    if len(eligible) != 269:
        raise RuntimeError(f"Expected 269 eligible rows, got {len(eligible)}")
    chapters_present = {(r.volume, r.chapter) for r in eligible}
    if len(chapters_present) != 20:
        raise RuntimeError(f"Expected 20 eligible physical chapters, got {len(chapters_present)}")
    return exclusions, eligible


def _overlaps_legacy_extension_test(row: EligibleLawRow, legacy_key_text: str) -> bool:
    """Check whether a sampled equation matches a hidden calibration or test item in tests/extension-test-key.md."""
    desc_l = row.description.lower()
    eq_norm = _normalize_formula_key(row.equation_latex)
    # Verify legacy key file exists and covers the 3 hidden calibration items (friction, pressure/Boyle, interference)
    # plus momentum p=mv referenced on line 15 of tests/extension-test-key.md.
    assert "Friction" in legacy_key_text and "Pressure and Boyle" in legacy_key_text and "Wave interference" in legacy_key_text
    if (row.volume, row.chapter) == (1, 6) and "friction" in desc_l:
        return True
    if (row.volume, row.chapter) == (1, 14) and "definition of pressure" in desc_l:
        return True
    if (row.volume, row.chapter) == (1, 16) and "interference" in desc_l:
        return True
    if (row.volume, row.chapter) == (1, 9) and (
        "definition of momentum" in desc_l or eq_norm == "vecp=mvecv"
    ):
        return True
    return False


def sample_heldout_40(eligible: list[EligibleLawRow], legacy_key_text: str) -> list[dict[str, Any]]:
    """Draw 2 equations per chapter in sorted (volume, chapter) order using seed=20261115, then shuffle."""
    by_chapter: dict[tuple[int, int], list[EligibleLawRow]] = {}
    for row in sorted(eligible, key=lambda r: r.sort_key()):
        by_chapter.setdefault((row.volume, row.chapter), []).append(row)

    if len(by_chapter) != 20:
        raise RuntimeError(f"Expected 20 chapters for sampling, got {len(by_chapter)}")

    rng = random.Random(SAMPLING_SEED)
    sampled: list[EligibleLawRow] = []
    for ch_key in sorted(by_chapter.keys()):
        ch_rows = by_chapter[ch_key]
        if len(ch_rows) < SAMPLES_PER_CHAPTER:
            raise RuntimeError(f"Chapter {ch_key} has only {len(ch_rows)} eligible rows")
        sampled.extend(rng.sample(ch_rows, SAMPLES_PER_CHAPTER))

    rng.shuffle(sampled)
    if len(sampled) != 40:
        raise RuntimeError(f"Expected 40 sampled equations, got {len(sampled)}")

    out: list[dict[str, Any]] = []
    for idx, row in enumerate(sampled, start=1):
        out.append(
            {
                "item_id": f"E{idx:03d}",
                "volume": row.volume,
                "chapter": row.chapter,
                "chapter_title": row.chapter_title,
                "stratum": row.stratum,
                "row_idx": row.row_idx,
                "eq_number": row.eq_number,
                "description": row.description,
                "equation_latex": row.equation_latex,
                "source_url": row.source_url,
                "overlaps_legacy_extension_test": _overlaps_legacy_extension_test(row, legacy_key_text),
            }
        )
    return out


def build_calibration_17() -> list[dict[str, Any]]:
    """Derive K01..K17 verbatim from rule/tsr_formal_port.py:ROWS."""
    if len(FORMAL_ROWS_17) != 17 or len(CALIBRATION_17_SPECS) != 17:
        raise RuntimeError("Expected 17 rows in rule/tsr_formal_port.py:ROWS")
    items: list[dict[str, Any]] = []
    for idx, (formal_row, spec) in enumerate(zip(FORMAL_ROWS_17, CALIBRATION_17_SPECS), start=1):
        row_name, book_ruling, has_mass, is_definition, costs, formal_source = formal_row
        spec_num, desc, eq_tex = spec
        if spec_num != idx:
            raise RuntimeError(f"Spec index mismatch at row {idx}")
        if book_ruling not in ("keep", "invert"):
            raise RuntimeError(f"Unexpected book_ruling {book_ruling!r}")
        items.append(
            {
                "item_id": f"K{idx:02d}",
                "row_num": idx,
                "formal_row_name": row_name,
                "formal_source": formal_source,
                "description": desc,
                "equation_latex": eq_tex,
                "expected_book_ruling": book_ruling,
                "provenance": "construction" if idx in CONSTRUCTION_ROW_NUMS else "applied_later",
                "has_mass_flag": bool(has_mass),
                "definition_flag": bool(is_definition),
                "costs_count": int(costs),
            }
        )
    return items


def _render_csv_bytes(fieldnames: list[str], rows: list[dict[str, Any]]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})
    return buf.getvalue().encode("utf-8")


def _render_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _load_raw_csv(path: Path) -> list[RawEquationRow]:
    expected = [
        "volume",
        "chapter",
        "chapter_title",
        "row_idx",
        "eq_number",
        "description",
        "equation_latex",
        "source_url",
        "retrieved_utc",
    ]
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != expected:
            raise RuntimeError(f"Unexpected raw CSV header: {reader.fieldnames} != {expected}")
        rows: list[RawEquationRow] = []
        for rec in reader:
            rows.append(
                RawEquationRow(
                    volume=int(rec["volume"]),
                    chapter=int(rec["chapter"]),
                    chapter_title=rec["chapter_title"],
                    row_idx=int(rec["row_idx"]),
                    eq_number=rec["eq_number"],
                    description=rec["description"],
                    equation_latex=rec["equation_latex"],
                    source_url=rec["source_url"],
                    retrieved_utc=rec["retrieved_utc"],
                )
            )
    return rows


def _build_derived(
    manifest: dict[str, Any],
    raw_rows: list[RawEquationRow],
    raw_csv_bytes: bytes,
    manifest_bytes: bytes,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    exclusions, eligible = classify_and_filter_rows(raw_rows)
    legacy_key_text = LEGACY_EXT_KEY_PATH.read_text(encoding="utf-8")
    heldout_items = sample_heldout_40(eligible, legacy_key_text)
    cal_items = build_calibration_17()

    core_count = sum(1 for item in heldout_items if item["stratum"] == "Core")
    boundary_count = sum(1 for item in heldout_items if item["stratum"] == "Boundary")
    if core_count != 28 or boundary_count != 12:
        raise RuntimeError(f"Expected 28 Core + 12 Boundary, got {core_count} + {boundary_count}")

    excl_counts = {
        "E1_PURE_MATH": 0,
        "E2_BENCHMARK_17_OVERLAP": 0,
        "E3_DUPLICATE_VARIANT": 0,
        "E4_NON_EQUATION": 0,
    }
    for ex in exclusions:
        excl_counts[ex["exclusion_code"]] += 1

    exclusion_fields = [
        "volume",
        "chapter",
        "row_idx",
        "eq_number",
        "description",
        "equation_latex",
        "exclusion_code",
        "matched_benchmark_id",
        "rationale",
    ]
    excl_bytes = _render_csv_bytes(exclusion_fields, exclusions)
    heldout_payload = {
        "attribution": ATTRIBUTION,
        "bundle_repo": BUNDLE_REPO,
        "bundle_commit_sha": BUNDLE_COMMIT_SHA,
        "seed": SAMPLING_SEED,
        "total_items": len(heldout_items),
        "core_count": core_count,
        "boundary_count": boundary_count,
        "items": heldout_items,
    }
    heldout_bytes = _render_json_bytes(heldout_payload)
    cal_payload = {
        "source": "rule/tsr_formal_port.py:ROWS",
        "total_items": len(cal_items),
        "construction_count": sum(1 for x in cal_items if x["provenance"] == "construction"),
        "applied_later_count": sum(1 for x in cal_items if x["provenance"] == "applied_later"),
        "items": cal_items,
    }
    cal_bytes = _render_json_bytes(cal_payload)

    sample_manifest_payload = {
        "attribution": ATTRIBUTION,
        "bundle_repo": BUNDLE_REPO,
        "bundle_commit_sha": manifest["bundle_commit_sha"],
        "seed": SAMPLING_SEED,
        "counts": {
            "total_chapters_fetched": 22,
            "total_modules_fetched": 153,
            "raw_equations_total": len(raw_rows),
            "excluded_total": len(exclusions),
            "exclusion_counts": excl_counts,
            "eligible_total": len(eligible),
            "eligible_chapters": 20,
            "core_chapters": 14,
            "boundary_chapters": 6,
            "sampled_total": len(heldout_items),
            "sampled_core": core_count,
            "sampled_boundary": boundary_count,
            "overlaps_legacy_extension_test_count": sum(
                1 for x in heldout_items if x["overlaps_legacy_extension_test"]
            ),
            "calibration_total": len(cal_items),
        },
        "artifacts_sha256": {
            "openstax_fetch_manifest.json": _sha256_bytes(manifest_bytes),
            "openstax_key_equations_raw.csv": _sha256_bytes(raw_csv_bytes),
            "exclusion_log.csv": _sha256_bytes(excl_bytes),
            "heldout_equations_40.json": _sha256_bytes(heldout_bytes),
            "calibration_equations_17.json": _sha256_bytes(cal_bytes),
        },
    }
    sample_manifest_bytes = _render_json_bytes(sample_manifest_payload)

    outputs: dict[Path, bytes] = {
        EXCLUSION_CSV_PATH: excl_bytes,
        HELDOUT_40_PATH: heldout_bytes,
        CALIBRATION_17_PATH: cal_bytes,
        SAMPLE_MANIFEST_PATH: sample_manifest_bytes,
    }
    return outputs, sample_manifest_payload


def run_verify_offline() -> dict[str, Any]:
    """Verify exclusions, deterministic sampling (seed=20261115), and SHA-256 parity offline."""
    required = (
        MANIFEST_PATH,
        RAW_CSV_PATH,
        EXCLUSION_CSV_PATH,
        HELDOUT_40_PATH,
        SAMPLE_MANIFEST_PATH,
        CALIBRATION_17_PATH,
    )
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Missing required artifact for --verify-offline: {path}")

    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("bundle_commit_sha") != BUNDLE_COMMIT_SHA:
        raise RuntimeError(f"Unexpected bundle_commit_sha: {manifest.get('bundle_commit_sha')}")
    if manifest.get("attribution") != ATTRIBUTION:
        raise RuntimeError(f"Unexpected attribution: {manifest.get('attribution')!r}")
    if manifest.get("total_chapters") != 22 or manifest.get("total_modules") != 153:
        raise RuntimeError("Manifest chapter/module count mismatch")
    if any(m.get("http_status") != 200 for m in manifest.get("modules", [])):
        raise RuntimeError("Manifest contains non-200 HTTP module status")

    raw_csv_bytes = RAW_CSV_PATH.read_bytes()
    raw_rows = _load_raw_csv(RAW_CSV_PATH)
    if len(raw_rows) != 321 or len(raw_rows) != manifest.get("total_raw_rows"):
        raise RuntimeError(f"Raw equation count mismatch: {len(raw_rows)}")
    if [r.sort_key() for r in raw_rows] != sorted(r.sort_key() for r in raw_rows):
        raise RuntimeError("Raw CSV rows are not canonically sorted")

    outputs, summary = _build_derived(manifest, raw_rows, raw_csv_bytes, manifest_bytes)
    for out_path, expected_bytes in outputs.items():
        actual_bytes = out_path.read_bytes()
        if actual_bytes != expected_bytes:
            raise RuntimeError(f"Byte-for-byte parity mismatch on {out_path.name}")

    return {"verify_offline": "OK", **summary["counts"]}


def run_live() -> dict[str, Any]:
    """Fetch pinned OpenStax CNXML corpus, emit all harness/openstax/ prep files, and verify offline parity."""
    manifest, raw_rows = fetch_pinned_openstax()
    OPENSTAX_DIR.mkdir(parents=True, exist_ok=True)
    manifest_bytes = _render_json_bytes(manifest)
    raw_fields = [
        "volume",
        "chapter",
        "chapter_title",
        "row_idx",
        "eq_number",
        "description",
        "equation_latex",
        "source_url",
        "retrieved_utc",
    ]
    raw_dicts = [
        {
            "volume": str(r.volume),
            "chapter": str(r.chapter),
            "chapter_title": r.chapter_title,
            "row_idx": str(r.row_idx),
            "eq_number": r.eq_number,
            "description": r.description,
            "equation_latex": r.equation_latex,
            "source_url": r.source_url,
            "retrieved_utc": r.retrieved_utc,
        }
        for r in raw_rows
    ]
    raw_csv_bytes = _render_csv_bytes(raw_fields, raw_dicts)

    MANIFEST_PATH.write_bytes(manifest_bytes)
    RAW_CSV_PATH.write_bytes(raw_csv_bytes)

    outputs, _summary = _build_derived(manifest, raw_rows, raw_csv_bytes, manifest_bytes)
    for out_path, content_bytes in outputs.items():
        out_path.write_bytes(content_bytes)

    return run_verify_offline()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-offline",
        action="store_true",
        help="Re-verify exclusions, sampling (seed=20261115), and SHA-256 parity with zero network calls.",
    )
    args = parser.parse_args(argv)
    stats = run_verify_offline() if args.verify_offline else run_live()
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
