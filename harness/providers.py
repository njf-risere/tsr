"""Stdlib-only live API client, model registry, JSON extractors, and call logger.

Zero external dependencies (Python 3.12+ standard library only).
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

API_ENDPOINT = "https://api.cheaperinference.com/v1/chat/completions"
ENV_VAR_NAME = "CHEAPERINFERENCE_API_KEY"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TIMEOUT_SEC = 120
RETRY_BACKOFF_SECONDS: tuple[int, ...] = (2, 4, 8, 16, 32)
USER_AGENT = "TSRAutomatedHarness/1.0"

GENERATORS: tuple[tuple[str, str], ...] = (
    ("claude-sonnet-4.6", "anthropic"),
    ("gpt-5.4-fast", "openai"),
    ("gemini-2.5-flash", "google"),
    ("mistral-medium-3.5", "mistral"),
    ("llama-4-maverick", "meta"),
)

CODERS: tuple[tuple[str, str], ...] = GENERATORS

OPPONENT: tuple[str, str] = ("deepseek-v4.1-flash-fast", "deepseek")

LAYER_B_JUDGES: tuple[tuple[str, str], ...] = (
    ("claude-sonnet-4.6", "anthropic"),
    ("gpt-5.4-fast", "openai"),
)

ROUND2_RATERS: tuple[tuple[str, str], ...] = (
    ("claude-sonnet-4.6", "anthropic"),
    ("gpt-5.4-fast", "openai"),
    ("gemini-2.5-flash", "google"),
    ("llama-4-maverick", "meta"),
)

ALL_MODELS: dict[str, str] = {
    model_id: vendor
    for model_id, vendor in (*GENERATORS, OPPONENT, *LAYER_B_JUDGES, *ROUND2_RATERS)
}


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    vendor: str


def get_vendor(model_id: str) -> str:
    """Return the canonical vendor family for a registered model_id."""
    if model_id not in ALL_MODELS:
        raise ValueError(f"Unregistered model_id {model_id!r}; expected one of {sorted(ALL_MODELS)}")
    return ALL_MODELS[model_id]


def _parse_env_file(path: Path, key_name: str) -> str | None:
    if not path.is_file():
        raise RuntimeError(f"Env file not found: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() != key_name:
            continue
        val = v.strip()
        if len(val) >= 2 and ((val[0] == val[-1] == '"') or (val[0] == val[-1] == "'")):
            val = val[1:-1]
        if val:
            return val
    return None


def resolve_api_key(env_path: str | Path | None = None) -> str:
    """Resolve API key from environment or an explicit caller-supplied env file."""
    env_val = os.environ.get(ENV_VAR_NAME, "").strip()
    if env_val:
        return env_val
    if env_path is not None:
        file_val = _parse_env_file(Path(env_path), ENV_VAR_NAME)
        if file_val:
            return file_val
        raise RuntimeError(
            f"{ENV_VAR_NAME} was not found in {env_path}. "
            f"Export {ENV_VAR_NAME} or supply a valid --env-file containing {ENV_VAR_NAME}=..."
        )
    raise RuntimeError(
        f"Missing {ENV_VAR_NAME}: export {ENV_VAR_NAME} in your environment "
        f"or pass --env-file <path>."
    )


def _strip_code_fence_candidates(text: str) -> list[str]:
    """Return fenced code blocks first (if any), followed by the raw text."""
    candidates: list[str] = []
    for m in re.finditer(r"```(?:json|JSON)?\s*\n?(.*?)```", text, flags=re.DOTALL):
        inner = m.group(1).strip()
        if inner:
            candidates.append(inner)
    stripped = text.strip()
    if stripped:
        candidates.append(stripped)
    return candidates


def _scan_balanced_json(text: str, open_ch: str, close_ch: str, expected_type: type) -> Any | None:
    """Find and parse the first balanced JSON object or array in text."""
    n = len(text)
    i = 0
    while i < n:
        start = text.find(open_ch, i)
        if start == -1:
            return None
        depth = 0
        in_string = False
        escaped = False
        j = start
        while j < n:
            ch = text[j]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        snippet = text[start : j + 1]
                        try:
                            parsed = json.loads(snippet)
                        except json.JSONDecodeError:
                            break
                        if isinstance(parsed, expected_type):
                            return parsed
                        break
            j += 1
        i = start + 1
    return None


def extract_first_json_object(text: str) -> dict[str, Any] | None:
    """Extract the first balanced JSON object from raw LLM output (handling markdown fences)."""
    if not text:
        return None
    for candidate in _strip_code_fence_candidates(text):
        obj = _scan_balanced_json(candidate, "{", "}", dict)
        if obj is not None:
            return obj
    return None


def extract_first_json_array(text: str) -> list[Any] | None:
    """Extract the first balanced JSON array from raw LLM output (handling markdown fences)."""
    if not text:
        return None
    for candidate in _strip_code_fence_candidates(text):
        arr = _scan_balanced_json(candidate, "[", "]", list)
        if arr is not None:
            return arr
    return None


def _sanitize_error_text(msg: str, secrets: Iterable[str]) -> str:
    out = msg
    for sec in secrets:
        if sec and len(sec) >= 4:
            out = out.replace(sec, "[REDACTED]")
    out = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._-]+", r"\1[REDACTED]", out)
    out = re.sub(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{6,}", "[REDACTED_KEY]", out)
    return out


def assert_no_secret_leak(serialized_record: str, extra_secrets: Iterable[str] = ()) -> None:
    """Fail loudly if a Bearer token, API key prefix, or active key substring appears in a log record."""
    env_key = os.environ.get(ENV_VAR_NAME, "").strip()
    for secret in (*extra_secrets, env_key):
        if secret and len(secret) >= 6 and secret in serialized_record:
            raise RuntimeError("Refusing to log record containing API key substring.")
    if re.search(r"(?i)\bbearer\s+[A-Za-z0-9._-]{6,}", serialized_record):
        raise RuntimeError("Refusing to log record containing authorization Bearer header token.")
    if re.search(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{6,}", serialized_record):
        raise RuntimeError("Refusing to log record containing sk-* key pattern.")


class JsonlCallLogger:
    """Thread-safe JSONL call logger enforcing strict schema and zero secret leakage."""

    ALLOWED_KEYS: tuple[str, ...] = (
        "call_id",
        "timestamp_utc",
        "role",
        "arm_id",
        "item_id",
        "model_id",
        "vendor",
        "temperature",
        "prompt_sha256",
        "response_sha256",
        "latency_ms",
        "raw_response",
    )

    def __init__(self, log_path: str | Path, secrets: Iterable[str] = ()) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._secrets = tuple(s for s in secrets if s)

    def log_call(
        self,
        *,
        role: str,
        arm_id: str,
        item_id: str,
        model_id: str,
        vendor: str,
        temperature: float,
        prompt_sha256: str,
        response_sha256: str,
        latency_ms: int,
        raw_response: str,
        call_id: str | None = None,
        timestamp_utc: str | None = None,
        extra_secrets: Iterable[str] = (),
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "call_id": call_id or uuid.uuid4().hex,
            "timestamp_utc": timestamp_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "role": str(role),
            "arm_id": str(arm_id),
            "item_id": str(item_id),
            "model_id": str(model_id),
            "vendor": str(vendor),
            "temperature": float(temperature),
            "prompt_sha256": str(prompt_sha256),
            "response_sha256": str(response_sha256),
            "latency_ms": int(latency_ms),
            "raw_response": str(raw_response),
        }
        assert tuple(record.keys()) == self.ALLOWED_KEYS
        line = json.dumps(record, ensure_ascii=False)
        assert_no_secret_leak(line, extra_secrets=(*self._secrets, *extra_secrets))
        with self._lock:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return record


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"API response missing choices: keys={sorted(payload.keys())}")
    msg = choices[0].get("message")
    if not isinstance(msg, dict):
        raise RuntimeError("API response choices[0] missing message object")
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        if parts:
            return "".join(parts)
    raise RuntimeError(f"API response message.content has unexpected type: {type(content).__name__}")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_prompt_digest(messages: list[dict[str, str]]) -> str:
    canonical = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return _sha256_text(canonical)


class CheaperInferenceClient:
    """Live OpenAI-compatible stdlib client for api.cheaperinference.com."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        env_path: str | Path | None = None,
        endpoint: str = API_ENDPOINT,
        timeout_sec: int = DEFAULT_TIMEOUT_SEC,
        logger: JsonlCallLogger | None = None,
        jitter_seed: int | None = None,
    ) -> None:
        self._api_key = api_key if api_key else resolve_api_key(env_path=env_path)
        self.endpoint = endpoint
        self.timeout_sec = timeout_sec
        self.logger = logger
        self._rng = random.Random(jitter_seed)
        self._rng_lock = threading.Lock()

    def _next_jitter(self) -> float:
        with self._rng_lock:
            return self._rng.uniform(0.05, 0.75)

    def chat(
        self,
        *,
        model_id: str,
        messages: list[dict[str, str]],
        role: str,
        arm_id: str,
        item_id: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Execute one chat completion request with 4 retries on transient errors."""
        vendor = get_vendor(model_id)
        body: dict[str, Any] = {
            "model": model_id,
            "temperature": temperature,
            "messages": messages,
        }
        if temperature == 0.0 and vendor == "mistral":
            body["top_p"] = 1.0
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        payload_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
        prompt_sha256 = _canonical_prompt_digest(messages)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": USER_AGENT,
        }

        last_error: Exception | None = None
        total_attempts = 1 + len(RETRY_BACKOFF_SECONDS)
        for attempt in range(total_attempts):
            req = urllib.request.Request(
                self.endpoint,
                data=payload_bytes,
                headers=headers,
                method="POST",
            )
            t0 = time.monotonic()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                    status = getattr(resp, "status", 200)
                    raw_bytes = resp.read()
                latency_ms = int(round((time.monotonic() - t0) * 1000))
                if status == 429 or 500 <= status < 600:
                    raise urllib.error.HTTPError(
                        self.endpoint, status, f"HTTP {status}", resp.headers, None
                    )
                decoded = json.loads(raw_bytes.decode("utf-8"))
                content = _extract_message_content(decoded)
                response_sha256 = _sha256_text(content)
                record = {
                    "call_id": uuid.uuid4().hex,
                    "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "role": role,
                    "arm_id": arm_id,
                    "item_id": item_id,
                    "model_id": model_id,
                    "vendor": vendor,
                    "temperature": temperature,
                    "prompt_sha256": prompt_sha256,
                    "response_sha256": response_sha256,
                    "latency_ms": latency_ms,
                    "raw_response": content,
                }
                if self.logger is not None:
                    self.logger.log_call(**record, extra_secrets=(self._api_key,))
                return content, record
            except urllib.error.HTTPError as exc:
                status = exc.code
                if status != 429 and not (500 <= status < 600):
                    err_body = ""
                    try:
                        err_body = exc.read().decode("utf-8", errors="replace")[:500]
                    except Exception:
                        pass
                    clean_err = _sanitize_error_text(
                        f"Non-retryable HTTP {status} for model={model_id}: {err_body}",
                        (self._api_key,),
                    )
                    raise RuntimeError(clean_err) from exc
                last_error = exc
            except (
                urllib.error.URLError,
                TimeoutError,
                OSError,
                http.client.HTTPException,
                json.JSONDecodeError,
            ) as exc:
                last_error = exc

            if attempt < len(RETRY_BACKOFF_SECONDS):
                delay = RETRY_BACKOFF_SECONDS[attempt] + self._next_jitter()
                time.sleep(delay)

        clean_msg = _sanitize_error_text(
            f"Exhausted {len(RETRY_BACKOFF_SECONDS)} retries for model={model_id} "
            f"(role={role}, item_id={item_id}): {type(last_error).__name__}: {last_error}",
            (self._api_key,),
        )
        raise RuntimeError(clean_msg) from last_error


def _run_self_test() -> None:
    """Offline sanity check of model registries, JSON extractors, and key/log guards."""
    assert len(GENERATORS) == 5 and len({v for _, v in GENERATORS}) == 5
    assert OPPONENT[1] not in {v for _, v in GENERATORS}
    assert len(ALL_MODELS) == 6
    assert len(LAYER_B_JUDGES) == 2 and len({v for _, v in LAYER_B_JUDGES}) == 2
    assert len(ROUND2_RATERS) == 4 and len({v for _, v in ROUND2_RATERS}) == 4

    obj = extract_first_json_object('Preamble {not json}\n```json\n{"a": 1, "b": "{x}"}\n```\nTail')
    assert obj == {"a": 1, "b": "{x}"}, obj
    arr = extract_first_json_array('Here:\n```json\n[{"id": "W001", "x": "[ok]"}]\n```')
    assert arr == [{"id": "W001", "x": "[ok]"}], arr

    assert_no_secret_leak('{"raw_response": "task-specific Sanskrit *sk- root"}')
    fake_bearer = "Bea" + "rer abcdefgh123456"
    fake_sk = "sk-" + "proj12345678"
    for bad in (
        f'{{"raw_response": "Authorization: {fake_bearer}"}}',
        f'{{"raw_response": "key is {fake_sk}"}}',
    ):
        try:
            assert_no_secret_leak(bad)
            raise AssertionError(f"Expected secret leak failure on {bad}")
        except RuntimeError:
            pass
    print("PROVIDERS_SELF_TEST_OK")


if __name__ == "__main__":
    _run_self_test()
