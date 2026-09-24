"""Process-safe API key rotation backed by files in the shared data volume."""

import fcntl
import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ApiKeyPoolExhaustedError(RuntimeError):
    """Raised when no API key has capacity left for the current day."""


@dataclass(frozen=True, slots=True)
class ApiKeyLease:
    """One counted use of an API key."""

    key: str
    index: int
    usage: int


class ApiKeyPool:
    """Atomically count, rotate, and disable API keys.

    The source file contains one key per line. Runtime state is stored separately
    and contains only key hashes, never the secrets themselves.
    """

    def __init__(
        self,
        keys_path: Path | None = None,
        keys: list[str] | None = None,
        state_path: Path | None = None,
        daily_limit: int = 1000,
    ) -> None:
        if daily_limit < 1:
            raise ValueError("API key daily limit must be positive")
        if (keys_path is None) == (keys is None):
            raise ValueError("Configure exactly one API key source")

        self._keys_path = keys_path
        self._keys = list(keys) if keys is not None else None

        default_state_path = (
            keys_path.with_name(f"{keys_path.stem}.state.json")
            if keys_path is not None
            else Path("data/api_keys.state.json")
        )
        self._state_path = state_path or default_state_path
        self._lock_path = self._state_path.with_suffix(
            f"{self._state_path.suffix}.lock"
        )
        self._daily_limit = daily_limit

    @classmethod
    def from_env(cls) -> ApiKeyPool:
        keys_path = Path(
            os.getenv("YANDEX_GEOCODER_API_KEYS_FILE", "data/api_keys.txt")
        )
        state_file = os.getenv("YANDEX_GEOCODER_API_KEYS_STATE_FILE")
        daily_limit = int(os.getenv("YANDEX_GEOCODER_API_KEY_LIMIT", "1000"))

        if keys_path.is_file():
            return cls(
                keys_path=keys_path,
                state_path=Path(state_file) if state_file else None,
                daily_limit=daily_limit,
            )

        fallback_key = os.getenv("YANDEX_GEOCODER_API_KEY")
        if fallback_key:
            return cls(
                keys=[fallback_key],
                state_path=Path(state_file) if state_file else None,
                daily_limit=daily_limit,
            )

        raise ValueError(
            f"API keys file not found: {keys_path}; "
            "YANDEX_GEOCODER_API_KEY is not configured"
        )

    @classmethod
    def from_env_or_none(cls) -> ApiKeyPool | None:
        keys_path = Path(
            os.getenv("YANDEX_GEOCODER_API_KEYS_FILE", "data/api_keys.txt")
        )
        if not keys_path.is_file() and not os.getenv("YANDEX_GEOCODER_API_KEY"):
            return None
        return cls.from_env()

    def acquire(self) -> ApiKeyLease:
        """Reserve and count one request on the first available key."""

        keys = self._read_keys()

        with self._locked_state(keys) as state:
            key_states = state["keys"]

            for index, key in enumerate(keys):
                key_state = key_states[self._fingerprint(key)]
                usage = int(key_state["usage"])

                if key_state["status"] != "active":
                    continue
                if usage >= self._daily_limit:
                    continue

                usage += 1
                key_state["usage"] = usage

                return ApiKeyLease(key=key, index=index, usage=usage)

        raise ApiKeyPoolExhaustedError(
            "All configured Yandex Geocoder API keys are exhausted or disabled"
        )

    def current_key_capacity(self) -> int:
        """Return remaining capacity of the key that will be selected next."""

        keys = self._read_keys()

        with self._locked_state(keys) as state:
            key_states = state["keys"]

            for key in keys:
                key_state = key_states[self._fingerprint(key)]
                if key_state["status"] != "active":
                    continue

                remaining = self._daily_limit - int(key_state["usage"])
                if remaining > 0:
                    return remaining

        return 0

    def has_available_key(self) -> bool:
        return self.current_key_capacity() > 0

    def disable(self, key: str, reason: str) -> None:
        """Permanently disable a key, for example after HTTP 403."""

        self._set_status(key, status="disabled", reason=reason)

    def exhaust(self, key: str, reason: str) -> None:
        """Disable a key until the daily counter resets, for example on 429."""

        self._set_status(key, status="exhausted", reason=reason)

    def _set_status(self, key: str, status: str, reason: str) -> None:
        keys = self._read_keys()
        fingerprint = self._fingerprint(key)

        with self._locked_state(keys) as state:
            key_state = state["keys"].get(fingerprint)
            if key_state is None:
                return

            key_state["status"] = status
            key_state["reason"] = reason

    def _read_keys(self) -> list[str]:
        if self._keys is not None:
            return self._validate_keys(self._keys, source="environment")

        if self._keys_path is None:
            raise ValueError("API keys source is not configured")

        try:
            lines = self._keys_path.read_text(encoding="utf-8-sig").splitlines()
        except FileNotFoundError as exc:
            raise ValueError(f"API keys file not found: {self._keys_path}") from exc

        keys = [
            line.strip()
            for line in lines
            if line.strip() and not line.lstrip().startswith("#")
        ]

        return self._validate_keys(keys, source=str(self._keys_path))

    @staticmethod
    def _validate_keys(keys: list[str], source: str) -> list[str]:
        if not keys:
            raise ValueError(f"No API keys found in {source}")
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate API keys found in {source}")

        return list(keys)

    @contextmanager
    def _locked_state(self, keys: list[str]) -> Iterator[dict[str, Any]]:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            state = self._load_state(keys)

            try:
                yield state
            finally:
                self._write_state(state)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load_state(self, keys: list[str]) -> dict[str, Any]:
        today = self._today()

        try:
            state: dict[str, Any] = json.loads(
                self._state_path.read_text(encoding="utf-8")
            )
        except FileNotFoundError, json.JSONDecodeError:
            state = {"date": today, "keys": {}}

        key_states = state.setdefault("keys", {})
        date_changed = state.get("date") != today

        for key in keys:
            fingerprint = self._fingerprint(key)
            key_state = key_states.setdefault(
                fingerprint,
                {"usage": 0, "status": "active", "reason": None},
            )

            if date_changed:
                key_state["usage"] = 0
                if key_state.get("status") == "exhausted":
                    key_state["status"] = "active"
                    key_state["reason"] = None

        state["date"] = today

        configured_fingerprints = {self._fingerprint(key) for key in keys}
        state["keys"] = {
            fingerprint: key_state
            for fingerprint, key_state in key_states.items()
            if fingerprint in configured_fingerprints
        }

        return state

    def _write_state(self, state: dict[str, Any]) -> None:
        temporary_path = self._state_path.with_name(
            f".{self._state_path.name}.{os.getpid()}.tmp"
        )

        temporary_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary_path, self._state_path)

    @staticmethod
    def _fingerprint(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).date().isoformat()
