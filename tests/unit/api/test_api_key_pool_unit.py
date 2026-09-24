import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from backend.api.key_pool import ApiKeyPool, ApiKeyPoolExhaustedError


@pytest.fixture
def keys_path(tmp_path: Path) -> Path:
    path = tmp_path / "api_keys.txt"
    path.write_text("first-key\nsecond-key\n", encoding="utf-8")
    return path


def test_rotates_key_after_limit(keys_path: Path) -> None:
    pool = ApiKeyPool(keys_path=keys_path, daily_limit=2)

    leases = [pool.acquire() for _ in range(4)]

    assert [lease.key for lease in leases] == [
        "first-key",
        "first-key",
        "second-key",
        "second-key",
    ]

    with pytest.raises(ApiKeyPoolExhaustedError):
        pool.acquire()


def test_disable_skips_key_permanently(keys_path: Path) -> None:
    pool = ApiKeyPool(keys_path=keys_path, daily_limit=1000)

    first = pool.acquire()
    pool.disable(first.key, reason="HTTP 403")

    assert pool.acquire().key == "second-key"


def test_exhaust_skips_key_for_current_day(keys_path: Path) -> None:
    pool = ApiKeyPool(keys_path=keys_path, daily_limit=1000)

    first = pool.acquire()
    pool.exhaust(first.key, reason="HTTP 429")

    assert pool.acquire().key == "second-key"


def test_acquire_is_atomic_between_workers(keys_path: Path) -> None:
    pool = ApiKeyPool(keys_path=keys_path, daily_limit=50)

    with ThreadPoolExecutor(max_workers=10) as executor:
        leases = list(executor.map(lambda _: pool.acquire(), range(100)))

    assert sum(lease.key == "first-key" for lease in leases) == 50
    assert sum(lease.key == "second-key" for lease in leases) == 50

    state_path = keys_path.with_name("api_keys.state.json")
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert sorted(key_state["usage"] for key_state in state["keys"].values()) == [
        50,
        50,
    ]
    assert "first-key" not in state_path.read_text(encoding="utf-8")
    assert "second-key" not in state_path.read_text(encoding="utf-8")


def test_current_key_capacity_uses_first_available_key(keys_path: Path) -> None:
    pool = ApiKeyPool(keys_path=keys_path, daily_limit=3)

    pool.acquire()

    assert pool.current_key_capacity() == 2


def test_from_env_falls_back_to_single_env_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("YANDEX_GEOCODER_API_KEYS_FILE", raising=False)
    monkeypatch.delenv("YANDEX_GEOCODER_API_KEYS_STATE_FILE", raising=False)
    monkeypatch.setenv("YANDEX_GEOCODER_API_KEY", "fallback-key")

    pool = ApiKeyPool.from_env()

    assert pool.acquire().key == "fallback-key"
