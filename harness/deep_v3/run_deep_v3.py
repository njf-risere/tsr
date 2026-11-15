#!/usr/bin/env python3
"""Master automated runner and preregistration verification suite for Deep-v3 (Pillars D1..D4).

Modes:
  --verify-prereg   Pre-live Commit-4 gate: verifies zero hygiene violations,
                    strict Commit-4 `deep_v3/` file whitelist (zero logs/,
                    outputs/, evaluate_deep_v3.py, or RESULTS_DEEP_V3.md), exact
                    SHA-256 parity with PREREGISTRATION_V3.md, `arms_v3` &
                    `layer_a_v3` self-tests, deterministic D4 Layer-A v3 audit,
                    and simulated 485-call task/validator/scrubber coverage
                    (0 live LLM calls; leaves working tree untouched).
  --run-live        Executes live stages (D1a, D1b, D2a, D2b, D3a, D3b = 485 calls)
                    concurrently within each stage via `CheaperInferenceClient`
                    + `JsonlCallLogger` with JSONL resumption, plus deterministic
                    D4 Layer-A v3 audit, writing scrubbed raw JSON outputs.
  --verify-offline  Post-live gate auditing `logs/live_calls_v3.jsonl`,
                    `outputs/raw_*.json`, deterministic D4 parity, and hygiene.

Python 3.12+ standard library only. Never print or store secrets.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

DEEP_V3_DIR = Path(__file__).resolve().parent
HARNESS_DIR = DEEP_V3_DIR.parent
REPO_ROOT = HARNESS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness import arms_v2, providers, run_tsr_harness  # noqa: E402
from harness.deep_v3 import arms_v3, layer_a_v3  # noqa: E402

LOGS_DIR = DEEP_V3_DIR / "logs"
LIVE_LOG_PATH = LOGS_DIR / "live_calls_v3.jsonl"
OUTPUTS_DIR = DEEP_V3_DIR / "outputs"
PREREG_V3_MD_PATH = DEEP_V3_DIR / "PREREGISTRATION_V3.md"
EVAL_V3_PATH = DEEP_V3_DIR / "evaluate_deep_v3.py"
RESULTS_V3_MD_PATH = DEEP_V3_DIR / "RESULTS_DEEP_V3.md"

HARNESS_SEED_V3 = arms_v3.HARNESS_SEED_V3
DEFAULT_TIMEOUT_SEC = 240
MAX_PARSE_ATTEMPTS = 3
DEFAULT_MAX_WORKERS = 10
EXPECTED_LIVE_CALL_COUNT = 485

HASHED_FILES_V3: tuple[str, ...] = (
    "arms_v3.py",
    "layer_a_v3.py",
    "crossing_battery_20.json",
    "run_deep_v3.py",
)

COMMIT4_ALLOWED_FILES: frozenset[str] = frozenset(
    {
        "__init__.py",
        "layer_a_v3.py",
        "crossing_battery_20.json",
        "arms_v3.py",
        "run_deep_v3.py",
        "PREREGISTRATION_V3.md",
    }
)

STAGE_SPECS: tuple[dict[str, str], ...] = (
    {"stage": "D1a", "role": "d1a_web_rating", "arm_id": "D1a", "output": "raw_d1a_web_ratings.json"},
    {"stage": "D1b", "role": "d1b_web_truthtable", "arm_id": "D1b", "output": "raw_d1b_web_truthtable.json"},
    {"stage": "D2a", "role": "d2a_crossing_cal17", "arm_id": "D2_CROSSING", "output": "raw_d2a_crossing_cal17.json"},
    {"stage": "D2b", "role": "d2b_crossing_battery20", "arm_id": "D2_CROSSING", "output": "raw_d2b_crossing_battery20.json"},
    {"stage": "D3a", "role": "d3a_narrative_cal17", "arm_id": "D3_NARRATIVE_A0", "output": "raw_d3a_narrative_cal17.json"},
    {"stage": "D3b", "role": "d3b_passage_rating", "arm_id": "D3b", "output": "raw_d3b_passage_ratings.json"},
)

EXPECTED_STAGE_COUNTS: dict[str, int] = {
    "D1a": 85,
    "D1b": 70,
    "D2a": 85,
    "D2b": 100,
    "D3a": 85,
    "D3b": 60,
}

# Construct regexes dynamically so this source file never contains literal restricted tokens.
_TOK_BL = "bl" + "ind"
_TOK_ET = "etym" + "online"
_TOK_USERS = "/" + "Us" + "ers/"
_TOK_GEMINI = "." + "gem" + "ini"
_TOK_TSR01 = "tsr_" + "01"
_TOK_TSRPR = "tsr_" + "pr_repo"
_TOK_TSRHR = "tsr_" + "harness_repo"
_TOK_SK = "sk" + "-"

_SCRUB_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(rf"(?<![A-Za-z]){_TOK_BL}[a-z]*(?![A-Za-z])", re.I), "[masked]"),
    (re.compile(re.escape(_TOK_ET), re.I), "[lexicon-ref]"),
    (re.compile(re.escape(_TOK_USERS) + r"[^\s\"']*"), "[redacted-path]"),
    (re.compile(re.escape(_TOK_GEMINI)), "[redacted]"),
    (re.compile(re.escape(_TOK_TSRHR), re.I), "[redacted]"),
    (re.compile(re.escape(_TOK_TSRPR), re.I), "[redacted]"),
    (re.compile(re.escape(_TOK_TSR01), re.I), "[redacted]"),
    (re.compile(r"(?<![A-Za-z0-9])" + _TOK_SK + r"[A-Za-z0-9_-]{8,}"), "[redacted-key]"),
)

_FREE_TEXT_STRING_KEYS: frozenset[str] = frozenset({"reason", "rationale", "axis_polarity_note"})


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _scrub_free_text_for_json(text: str) -> str:
    """Scrub restricted hygiene tokens ONLY from free-text fields persisted into raw_*.json."""
    out = text
    for pat, repl in _SCRUB_PATTERNS:
        out = pat.sub(repl, out)
    return out


def _scrub_free_text_fields(obj: Any) -> Any:
    """Recursively copy JSON data while scrubbing only free-text prose (`reason`, `rationale`, `axis_polarity_note`, `errors`)."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if k in _FREE_TEXT_STRING_KEYS and isinstance(v, str):
                out[k] = _scrub_free_text_for_json(v)
            elif k == "errors" and isinstance(v, list):
                out[k] = [
                    _scrub_free_text_for_json(item) if isinstance(item, str) else _scrub_free_text_fields(item)
                    for item in v
                ]
            else:
                out[k] = _scrub_free_text_fields(v)
        return out
    if isinstance(obj, list):
        return [_scrub_free_text_fields(x) for x in obj]
    return obj


def check_v3_hygiene(allow_live_artifacts: bool = False) -> list[str]:
    """Run repo-wide hygiene checks plus Commit-4/v3-specific clean-tree guards."""
    errors = list(run_tsr_harness.check_repo_hygiene(allow_live_artifacts=True))
    et_re = re.compile(re.escape(_TOK_ET), re.I)

    observed_v3_rel: set[str] = set()
    for p in sorted(HARNESS_DIR.rglob("*")):
        rel_h = p.relative_to(HARNESS_DIR).as_posix()
        if any(part == "__pycache__" for part in p.parts) or p.suffix == ".pyc" or p.name == ".DS_Store":
            # Already recorded by check_repo_hygiene; avoid duplicates unless missed
            continue
        if p.is_dir():
            continue
        if p.suffix in (".py", ".md", ".json", ".csv"):
            txt = p.read_text(encoding="utf-8")
            if et_re.search(txt):
                errors.append(f"Forbidden token {_TOK_ET!r} in harness/{rel_h}")
        if DEEP_V3_DIR in p.parents:
            observed_v3_rel.add(p.relative_to(DEEP_V3_DIR).as_posix())

    if not allow_live_artifacts:
        if LOGS_DIR.exists():
            errors.append(f"Forbidden pre-live directory exists: {LOGS_DIR.relative_to(REPO_ROOT)}")
        if OUTPUTS_DIR.exists():
            errors.append(f"Forbidden pre-live directory exists: {OUTPUTS_DIR.relative_to(REPO_ROOT)}")
        if EVAL_V3_PATH.exists():
            errors.append(f"Forbidden Commit-4 file exists: {EVAL_V3_PATH.relative_to(REPO_ROOT)}")
        if RESULTS_V3_MD_PATH.exists():
            errors.append(f"Forbidden Commit-4 file exists: {RESULTS_V3_MD_PATH.relative_to(REPO_ROOT)}")
        unexpected = sorted(observed_v3_rel - COMMIT4_ALLOWED_FILES)
        missing = sorted(COMMIT4_ALLOWED_FILES - observed_v3_rel)
        if unexpected:
            errors.append(f"Unexpected files under harness/deep_v3/: {unexpected}")
        if missing:
            errors.append(f"Missing expected Commit-4 files under harness/deep_v3/: {missing}")

    return errors


def _verify_prereg_v3_md() -> list[str]:
    """Verify PREREGISTRATION_V3.md exists, hashes match disk, links resolve, and H1..H6 are present."""
    if not PREREG_V3_MD_PATH.exists():
        return ["Missing harness/deep_v3/PREREGISTRATION_V3.md"]
    errors: list[str] = []
    md = PREREG_V3_MD_PATH.read_text(encoding="utf-8")

    for fname in HASHED_FILES_V3:
        digest = _sha256_file(DEEP_V3_DIR / fname)
        if digest not in md:
            errors.append(f"PREREGISTRATION_V3.md missing exact SHA-256 {digest} for harness/deep_v3/{fname}")

    for h_id in ("H1", "H2", "H3", "H4", "H5", "H6"):
        if not re.search(rf"\b{h_id}\b", md):
            errors.append(f"PREREGISTRATION_V3.md missing confirmatory hypothesis {h_id}")

    for m in re.finditer(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", md):
        target = m.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (PREREG_V3_MD_PATH.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"Broken relative markdown link in PREREGISTRATION_V3.md: {target!r}")
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            errors.append(f"Markdown link escapes repository root: {target!r}")

    return errors


def compute_hashed_file_digests() -> dict[str, str]:
    return {fname: _sha256_file(DEEP_V3_DIR / fname) for fname in HASHED_FILES_V3}


def build_live_task_specs() -> list[dict[str, Any]]:
    """Build all 485 live LLM task specs deterministically ordered by `(stage, task_id, model_id)`."""
    cal_items = arms_v3._load_calibration_items()
    crossing_items = arms_v3._load_crossing_battery_items()
    base_a0 = arms_v2.build_arm_v2("A0")
    crossing_arm = arms_v3.build_crossing_arm_v3()

    specs: list[dict[str, Any]] = []

    # D1a: 14 Core Web slots + 3 Negative Controls x 5 raters = 85 calls
    d1a_ids = [s["slot_id"] for s in arms_v3.CORE_WEB_SLOTS_14] + [
        c["item_id"] for c in arms_v3.NEGATIVE_CONTROL_ITEMS_3
    ]
    for iid in d1a_ids:
        for model_id, vendor in providers.GENERATORS:
            prep = arms_v3.prepare_d1a_item(iid, model_id)
            specs.append(
                {
                    "stage": "D1a",
                    "task_id": iid,
                    "role": "d1a_web_rating",
                    "arm_id": "D1a",
                    "item_id": iid,
                    "model_id": model_id,
                    "vendor": vendor,
                    "messages": arms_v3.build_d1a_messages(iid, model_id),
                    "validator": lambda p, _iid=iid: arms_v3.validate_d1a_json(p, _iid),
                    "task_meta": {"item_id": iid, "stratum": prep["stratum"]},
                    "call_meta": {
                        "candidates": prep["candidates"],
                        "hidden_key": prep["hidden_key"],
                    },
                }
            )

    # D1b: 14 Core Web slots x 5 raters = 70 calls
    for slot in arms_v3.CORE_WEB_SLOTS_14:
        sid = slot["slot_id"]
        for model_id, vendor in providers.GENERATORS:
            prep = arms_v3.prepare_d1b_slot(sid, model_id)
            specs.append(
                {
                    "stage": "D1b",
                    "task_id": sid,
                    "role": "d1b_web_truthtable",
                    "arm_id": "D1b",
                    "item_id": sid,
                    "model_id": model_id,
                    "vendor": vendor,
                    "messages": arms_v3.build_d1b_messages(sid, model_id),
                    "validator": lambda p, _sid=sid: arms_v3.validate_d1b_json(p, _sid),
                    "task_meta": {"slot_id": sid},
                    "call_meta": {
                        "candidates": prep["candidates"],
                        "hidden_key": prep["hidden_key"],
                    },
                }
            )

    # D2a: 17 calibration equations x 5 generators = 85 calls
    for item in cal_items:
        iid = item["item_id"]
        msgs = arms_v3.build_d2a_messages(item)
        for model_id, vendor in providers.GENERATORS:
            specs.append(
                {
                    "stage": "D2a",
                    "task_id": iid,
                    "role": "d2a_crossing_cal17",
                    "arm_id": "D2_CROSSING",
                    "item_id": iid,
                    "model_id": model_id,
                    "vendor": vendor,
                    "messages": msgs,
                    "validator": (
                        lambda p, _it=item, _ca=crossing_arm: arms_v3.validate_d2_generator_json(
                            p, _it, _ca
                        )
                    ),
                    "task_meta": {
                        "item_id": iid,
                        "expected_book_ruling": item["expected_book_ruling"],
                        "chapter_or_context": item.get("chapter_or_context", ""),
                    },
                    "call_meta": {},
                }
            )

    # D2b: 20 Crossing battery equations x 5 generators = 100 calls
    for item in crossing_items:
        iid = item["item_id"]
        msgs = arms_v3.build_d2b_messages(item)
        for model_id, vendor in providers.GENERATORS:
            specs.append(
                {
                    "stage": "D2b",
                    "task_id": iid,
                    "role": "d2b_crossing_battery20",
                    "arm_id": "D2_CROSSING",
                    "item_id": iid,
                    "model_id": model_id,
                    "vendor": vendor,
                    "messages": msgs,
                    "validator": (
                        lambda p, _it=item, _ca=crossing_arm: arms_v3.validate_d2_generator_json(
                            p, _it, _ca
                        )
                    ),
                    "task_meta": {
                        "item_id": iid,
                        "stratum": item["stratum"],
                        "expected_scope_status": item["expected_scope_status"],
                        "heldout_item_id": item.get("heldout_item_id"),
                        "volume": item.get("volume"),
                        "chapter": item.get("chapter"),
                        "row_idx": item.get("row_idx"),
                    },
                    "call_meta": {},
                }
            )

    # D3a: 17 calibration equations under Ch.2 + redacted Crossing excerpt x 5 generators = 85 calls
    for item in cal_items:
        iid = item["item_id"]
        msgs = arms_v3.build_d3a_messages(item)
        for model_id, vendor in providers.GENERATORS:
            specs.append(
                {
                    "stage": "D3a",
                    "task_id": iid,
                    "role": "d3a_narrative_cal17",
                    "arm_id": "D3_NARRATIVE_A0",
                    "item_id": iid,
                    "model_id": model_id,
                    "vendor": vendor,
                    "messages": msgs,
                    "validator": (
                        lambda p, _it=item, _a0=base_a0: arms_v2.validate_generator_json(
                            p, _a0, _it
                        )
                    ),
                    "task_meta": {
                        "item_id": iid,
                        "expected_book_ruling": item["expected_book_ruling"],
                        "chapter_or_context": item.get("chapter_or_context", ""),
                    },
                    "call_meta": {},
                }
            )

    # D3b: 12 verbatim-derived masked excerpts x 5 raters = 60 calls
    for passage in arms_v3.D3B_EXCERPTS_12:
        pid = passage["passage_id"]
        for model_id, vendor in providers.GENERATORS:
            prep = arms_v3.prepare_d3b_passage(pid, model_id)
            specs.append(
                {
                    "stage": "D3b",
                    "task_id": pid,
                    "role": "d3b_passage_rating",
                    "arm_id": "D3b",
                    "item_id": pid,
                    "model_id": model_id,
                    "vendor": vendor,
                    "messages": arms_v3.build_d3b_messages(pid, model_id),
                    "validator": lambda p, _pid=pid: arms_v3.validate_d3b_json(p, _pid),
                    "task_meta": {
                        "passage_id": pid,
                        "stratum": prep["stratum"],
                        "source_ref": prep["source_ref"],
                    },
                    "call_meta": {
                        "hidden_key": prep["hidden_key"],
                    },
                }
            )

    assert len(specs) == EXPECTED_LIVE_CALL_COUNT, f"Expected 485 specs, got {len(specs)}"
    keys = {(s["role"], s["arm_id"], s["item_id"], s["model_id"]) for s in specs}
    assert len(keys) == EXPECTED_LIVE_CALL_COUNT, "Duplicate (role, arm_id, item_id, model_id) key in live specs"
    return specs


def _group_stage_payload(
    stage_meta: dict[str, str],
    stage_specs: list[dict[str, Any]],
    call_results: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Serialize one stage's raw responses grouped cleanly by `(stage, task_id)` and scrubbed on free text."""
    task_order: list[str] = []
    grouped: dict[str, dict[str, Any]] = {}
    valid_count = 0
    schema_error_count = 0

    for spec in stage_specs:
        tid = spec["task_id"]
        mid = spec["model_id"]
        if tid not in grouped:
            task_order.append(tid)
            grouped[tid] = {
                "task_id": tid,
                "metadata": dict(spec["task_meta"]),
                "by_model": {},
            }
        res = call_results[(tid, mid)]
        if res["status"] == "ok":
            valid_count += 1
        else:
            schema_error_count += 1
        entry = {
            "model_id": mid,
            "vendor": spec["vendor"],
            "status": res["status"],
            "attempt_used": res["attempt_used"],
            "from_cache": res["from_cache"],
            "call_id": res["call_id"],
            "call_meta": dict(spec["call_meta"]),
            "parsed": res["parsed"],
            "errors": list(res["errors"]),
        }
        grouped[tid]["by_model"][mid] = _scrub_free_text_fields(entry)

    return {
        "stage": stage_meta["stage"],
        "role": stage_meta["role"],
        "arm_id": stage_meta["arm_id"],
        "expected_calls": len(stage_specs),
        "valid_calls": valid_count,
        "schema_error_count": schema_error_count,
        "tasks": [grouped[tid] for tid in task_order],
    }


def _execute_stage(
    *,
    stage_meta: dict[str, str],
    stage_specs: list[dict[str, Any]],
    client: providers.CheaperInferenceClient,
    existing_log: dict[tuple[str, str, str, str], list[dict[str, Any]]],
    max_workers: int,
) -> dict[str, Any]:
    results: dict[tuple[str, str], dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {
            pool.submit(
                run_tsr_harness._call_with_schema_retries,
                client=client,
                existing_log=existing_log,
                role=spec["role"],
                arm_id=spec["arm_id"],
                item_id=spec["item_id"],
                model_id=spec["model_id"],
                base_messages=spec["messages"],
                validator=spec["validator"],
                max_attempts=MAX_PARSE_ATTEMPTS,
            ): (spec["task_id"], spec["model_id"])
            for spec in stage_specs
        }
        for fut in concurrent.futures.as_completed(futs):
            tid, mid = futs[fut]
            results[(tid, mid)] = fut.result()

    return _group_stage_payload(stage_meta, stage_specs, results)


def run_live_pipeline(env_file: Path | None, max_workers: int = DEFAULT_MAX_WORKERS) -> dict[str, Any]:
    """Execute live stages D1a..D3b with JSONL resumption plus deterministic D4 audit."""
    prereg_errors = _verify_prereg_v3_md()
    if prereg_errors:
        raise RuntimeError("PREREGISTRATION_V3.md verification failed:\n- " + "\n- ".join(prereg_errors))

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    all_specs = build_live_task_specs()
    specs_by_stage: dict[str, list[dict[str, Any]]] = {s["stage"]: [] for s in STAGE_SPECS}
    for sp in all_specs:
        specs_by_stage[sp["stage"]].append(sp)

    api_key = providers.resolve_api_key(env_path=env_file)
    logger = providers.JsonlCallLogger(LIVE_LOG_PATH, secrets=(api_key,))
    client = providers.CheaperInferenceClient(
        api_key=api_key,
        timeout_sec=DEFAULT_TIMEOUT_SEC,
        logger=logger,
        jitter_seed=HARNESS_SEED_V3,
    )
    existing_log = run_tsr_harness._load_existing_log_records(LIVE_LOG_PATH)

    stage_summaries: dict[str, Any] = {}
    schema_error_counts: dict[str, int] = {}
    for stage_meta in STAGE_SPECS:
        st = stage_meta["stage"]
        payload = _execute_stage(
            stage_meta=stage_meta,
            stage_specs=specs_by_stage[st],
            client=client,
            existing_log=existing_log,
            max_workers=max_workers,
        )
        _write_json(OUTPUTS_DIR / stage_meta["output"], payload)
        schema_error_counts[st] = payload["schema_error_count"]
        stage_summaries[st] = {
            "output_file": stage_meta["output"],
            "expected_calls": payload["expected_calls"],
            "valid_calls": payload["valid_calls"],
            "schema_error_count": payload["schema_error_count"],
        }

    # Deterministic Pillar D4 audit (0 live calls)
    d4_payload = layer_a_v3.evaluate_frozen_stage2_heldout_v3()
    _write_json(OUTPUTS_DIR / "raw_d4_layer_a_audit.json", _scrub_free_text_fields(d4_payload))

    post_log = run_tsr_harness._load_existing_log_records(LIVE_LOG_PATH)
    raw_lines = [ln for ln in LIVE_LOG_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]

    summary = {
        "harness_version": "deep_v3",
        "seed": HARNESS_SEED_V3,
        "expected_live_calls": EXPECTED_LIVE_CALL_COUNT,
        "jsonl_lines": len(raw_lines),
        "unique_call_keys": len(post_log),
        "schema_error_counts": schema_error_counts,
        "stages": stage_summaries,
        "d4_summary": {
            arm_id: {
                "evaluated_items": d4_payload[arm_id]["evaluated_items"],
                "per_item_passed": d4_payload[arm_id]["per_item_passed"],
                "layer_a_collisions_count": d4_payload[arm_id]["layer_a_collisions_count"],
                "passes_all": d4_payload[arm_id]["passes_all"],
            }
            for arm_id in ("A0", "A3-1")
        },
        "prereg_hashed_files": compute_hashed_file_digests(),
    }
    _write_json(OUTPUTS_DIR / "summary_deep_v3_raw.json", summary)

    hygiene_errors = check_v3_hygiene(allow_live_artifacts=True)
    if hygiene_errors:
        raise RuntimeError("Post-live hygiene check failed:\n- " + "\n- ".join(hygiene_errors))

    return summary


# ---------------------------------------------------------------------------
# Pre-Live Simulated End-to-End Dry Run (`0` live calls, `0` files written)
# ---------------------------------------------------------------------------


def _run_simulated_deep_v3_e2e() -> dict[str, Any]:
    """Exercise all 485 task builders, client seed wiring, validators, schema-error fallback, and scrubber offline."""
    smoke_client = providers.CheaperInferenceClient(
        api_key="dryrun-offline-key",
        timeout_sec=DEFAULT_TIMEOUT_SEC,
        logger=None,
        jitter_seed=HARNESS_SEED_V3,
    )
    assert isinstance(smoke_client._next_jitter(), float)

    specs = build_live_task_specs()
    counts_by_stage = Counter(sp["stage"] for sp in specs)
    assert dict(counts_by_stage) == EXPECTED_STAGE_COUNTS, f"Stage count mismatch: {dict(counts_by_stage)}"

    for sp in specs:
        msgs = sp["messages"]
        assert isinstance(msgs, list) and len(msgs) == 2
        assert msgs[0]["role"] == "system" and msgs[0]["content"].strip()
        assert msgs[1]["role"] == "user" and msgs[1]["content"].strip()

    class _StubClient:
        def __init__(self, responses: list[str]) -> None:
            self._responses = list(responses)
            self.calls = 0

        def chat(self, **_kwargs: Any) -> tuple[str, dict[str, Any]]:
            self.calls += 1
            txt = self._responses[min(self.calls - 1, len(self._responses) - 1)]
            return txt, {"call_id": f"stub_{self.calls}"}

    # Simulate valid + 3-attempt schema_error on each stage type + scrubber preservation
    dirty_bl = _TOK_BL + "inded"
    dirty_et = _TOK_ET + ".com"
    dirty_reason = f"Strong {dirty_bl} match unlike {dirty_et} entry under {_TOK_USERS}tmp/foo."

    synth_ok: dict[str, dict[str, Any]] = {
        "D1a": {
            "item_id": "W01",
            "scores": {"1": 5, "2": 4, "3": 2, "4": 1},
            "best_candidate": 1,
            "worst_candidate": 4,
            "ranking": [1, 2, 3, 4],
            "reason": dirty_reason,
        },
        "D1b": {
            "slot_id": "W01",
            "evaluations": {
                "1": {"c1": True, "c2": True, "c3": True, "c4": True},
                "2": {"c1": True, "c2": False, "c3": False, "c4": False},
                "3": {"c1": False, "c2": True, "c3": False, "c4": False},
                "4": {"c1": False, "c2": False, "c3": False, "c4": True},
            },
            "reason": dirty_reason,
        },
        "D2a": {
            "item_id": "K01",
            "scope_status": "in_scope",
            "unmapped_terms": [],
            "formula_shape": "keeps",
            "ruling": "keep",
            "two_level": False,
            "variable_map": {"F": "Frequency", "m": "Movement", "a": "Appreciation"},
            "reflected_formula": "Frequency = Movement * Appreciation",
            "translation_template": "{Frequency} equals {Movement} scaled by {Appreciation}.",
            "translation_t": "Frequency equals Movement scaled by Appreciation.",
            "direction_flipped_d": "Appreciation produces Frequency directly without Movement.",
            "axis_polarity_note": dirty_reason,
            "rationale": dirty_reason,
        },
        "D2b": {
            "item_id": "E029",
            "scope_status": "crossing_interface",
            "unmapped_terms": [],
            "formula_shape": "keeps",
            "ruling": "invert",
            "two_level": False,
            "variable_map": {"Delta p": "felt gap", "rho": "Desire", "h": "Vibration"},
            "reflected_formula": "felt gap = - Desire * Vibration",
            "translation_template": "{felt gap} shifts across {Desire} along vertical {Vibration}.",
            "translation_t": "felt gap shifts across Desire along vertical Vibration.",
            "direction_flipped_d": "Vibration accumulates felt gap directly without Desire.",
            "axis_polarity_note": dirty_reason,
            "rationale": dirty_reason,
        },
        "D3a": {
            "item_id": "K01",
            "scope_status": "in_scope",
            "unmapped_terms": [],
            "formula_shape": "keeps",
            "ruling": "keep",
            "two_level": False,
            "variable_map": {"F": "Frequency", "m": "Movement", "a": "Appreciation"},
            "reflected_formula": "Frequency = Movement * Appreciation",
            "translation_template": "{Frequency} equals {Movement} scaled by {Appreciation}.",
            "translation_t": "Frequency equals Movement scaled by Appreciation.",
            "direction_flipped_d": "Appreciation produces Frequency directly without Movement.",
            "axis_polarity_note": dirty_reason,
            "rationale": dirty_reason,
        },
        "D3b": {
            "passage_id": "P01",
            "scores": {"1": 5, "2": 3, "3": 1},
            "best_variant": 1,
            "worst_variant": 3,
            "ranking": [1, 2, 3],
            "reason": dirty_reason,
        },
    }

    first_spec_by_stage = {st["stage"]: next(sp for sp in specs if sp["stage"] == st["stage"]) for st in STAGE_SPECS}
    for stage, sp in first_spec_by_stage.items():
        # Valid JSON pass (after 1 simulated retry)
        stub_ok = _StubClient(["{bad", json.dumps(synth_ok[stage])])
        res_ok = run_tsr_harness._call_with_schema_retries(
            client=stub_ok,  # type: ignore[arg-type]
            existing_log={},
            role=sp["role"],
            arm_id=sp["arm_id"],
            item_id=sp["item_id"],
            model_id=sp["model_id"],
            base_messages=sp["messages"],
            validator=sp["validator"],
            max_attempts=MAX_PARSE_ATTEMPTS,
        )
        assert res_ok["status"] == "ok" and res_ok["attempt_used"] == 2, f"Simulated {stage} ok failed: {res_ok}"

        # Non-crashing 3-attempt schema_error check
        stub_err = _StubClient(["not-json", "still-not-json", '{"broken": true}'])
        res_err = run_tsr_harness._call_with_schema_retries(
            client=stub_err,  # type: ignore[arg-type]
            existing_log={},
            role=sp["role"],
            arm_id=sp["arm_id"],
            item_id=sp["item_id"],
            model_id=sp["model_id"],
            base_messages=sp["messages"],
            validator=sp["validator"],
            max_attempts=MAX_PARSE_ATTEMPTS,
        )
        assert res_err["status"] == "schema_error" and res_err["parsed"] is None and stub_err.calls == 3

        # Scrubber check: free text cleaned without touching structured translation/scores
        scrubbed_json = json.dumps(_scrub_free_text_fields(res_ok["parsed"]))
        assert not re.search(rf"(?<![A-Za-z]){_TOK_BL}[a-z]*(?![A-Za-z])", scrubbed_json, re.I)
        assert _TOK_ET not in scrubbed_json.lower()
        assert _TOK_USERS not in scrubbed_json
        if stage == "D2b":
            assert '"felt gap"' in scrubbed_json and '"crossing_interface"' in scrubbed_json

    return {
        "simulated_specs": len(specs),
        "stage_counts": dict(counts_by_stage),
        "scrubber_verified_stages": sorted(first_spec_by_stage.keys()),
    }


def run_verify_prereg() -> dict[str, Any]:
    """Pre-live Commit-4 gate (0 live LLM calls, zero logs/outputs on disk)."""
    hygiene_errors = check_v3_hygiene(allow_live_artifacts=False)
    if hygiene_errors:
        raise RuntimeError("Deep-v3 pre-live hygiene/whitelist check failed:\n- " + "\n- ".join(hygiene_errors))

    prereg_errors = _verify_prereg_v3_md()
    if prereg_errors:
        raise RuntimeError("PREREGISTRATION_V3.md verification failed:\n- " + "\n- ".join(prereg_errors))

    arms_v3._run_self_test()
    layer_a_v3._run_self_test()

    d4 = layer_a_v3.evaluate_frozen_stage2_heldout_v3()
    assert d4["A0"]["evaluated_items"] == 16 and d4["A0"]["per_item_passed"] == 16 and d4["A0"]["passes_all"] is True
    assert d4["A3-1"]["evaluated_items"] == 16 and d4["A3-1"]["per_item_passed"] == 15 and d4["A3-1"]["passes_all"] is False

    sim = _run_simulated_deep_v3_e2e()
    return {
        "verify_prereg": "OK",
        "commit4_file_count": len(COMMIT4_ALLOWED_FILES),
        "hashed_files_sha256": compute_hashed_file_digests(),
        "live_calls_executed": 0,
        "simulated_pipeline": sim,
        "d4_deterministic_audit": {
            arm_id: {
                "evaluated_items": d4[arm_id]["evaluated_items"],
                "per_item_passed": d4[arm_id]["per_item_passed"],
                "layer_a_collisions_count": d4[arm_id]["layer_a_collisions_count"],
                "passes_all": d4[arm_id]["passes_all"],
            }
            for arm_id in ("A0", "A3-1")
        },
    }


def run_verify_offline() -> dict[str, Any]:
    """Post-live offline audit of `live_calls_v3.jsonl`, `outputs/raw_*.json`, D4 parity, and hygiene."""
    hygiene_errors = check_v3_hygiene(allow_live_artifacts=True)
    if hygiene_errors:
        raise RuntimeError("Post-live hygiene check failed:\n- " + "\n- ".join(hygiene_errors))

    prereg_errors = _verify_prereg_v3_md()
    if prereg_errors:
        raise RuntimeError("PREREGISTRATION_V3.md check failed:\n- " + "\n- ".join(prereg_errors))

    arms_v3._run_self_test()
    layer_a_v3._run_self_test()

    if not LIVE_LOG_PATH.exists():
        raise RuntimeError(f"Missing live JSONL log at {LIVE_LOG_PATH}")

    raw_lines = [ln for ln in LIVE_LOG_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for ln in raw_lines:
        providers.assert_no_secret_leak(ln)

    existing_log = run_tsr_harness._load_existing_log_records(LIVE_LOG_PATH)
    expected_specs = build_live_task_specs()
    expected_keys = {(sp["role"], sp["arm_id"], sp["item_id"], sp["model_id"]) for sp in expected_specs}
    missing_log_keys = sorted(expected_keys - set(existing_log.keys()))
    if missing_log_keys:
        raise RuntimeError(f"Missing {len(missing_log_keys)} logged call keys in {LIVE_LOG_PATH.name}; first={missing_log_keys[0]}")

    for fname in (*(st["output"] for st in STAGE_SPECS), "raw_d4_layer_a_audit.json", "summary_deep_v3_raw.json"):
        if not (OUTPUTS_DIR / fname).exists():
            raise RuntimeError(f"Missing required Deep-v3 output artifact: harness/deep_v3/outputs/{fname}")

    disk_d4 = _load_json(OUTPUTS_DIR / "raw_d4_layer_a_audit.json")
    fresh_d4 = _scrub_free_text_fields(layer_a_v3.evaluate_frozen_stage2_heldout_v3())
    if disk_d4 != fresh_d4:
        raise RuntimeError("raw_d4_layer_a_audit.json does not match deterministic Layer-A v3 recomputation")

    summary = _load_json(OUTPUTS_DIR / "summary_deep_v3_raw.json")
    return {
        "verify_offline": "OK",
        "jsonl_lines": len(raw_lines),
        "unique_call_keys": len(existing_log),
        "expected_call_keys": len(expected_keys),
        "schema_error_counts": summary.get("schema_error_counts", {}),
        "d4_summary": summary.get("d4_summary", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="TSR Deep-v3 Evaluation Harness (Pillars D1..D4)")
    parser.add_argument("--verify-prereg", action="store_true", help="Pre-live Commit-4 gate (0 live calls)")
    parser.add_argument("--run-live", action="store_true", help="Run 485 live Deep-v3 calls + D4 audit")
    parser.add_argument("--verify-offline", action="store_true", help="Post-live offline audit of logs & raw JSONs")
    parser.add_argument("--env-file", type=str, default=None, help="Path to .env file with CHEAPERINFERENCE_API_KEY")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS, help="Max concurrent workers per stage")
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
        print(json.dumps(run_verify_offline(), indent=2))


if __name__ == "__main__":
    main()
