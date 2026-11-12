"""TQ-1: unit tests for hashing, timestamps and accounting helpers (no database)."""
from datetime import datetime, timezone

from app.core.hashing import GENESIS_HASH, canonical_ts, entry_hash, request_fingerprint


def test_fingerprint_is_stable_and_order_independent():
    assert request_fingerprint("POST", "/v1/transfers", {"a": 1, "b": 2}) == request_fingerprint("post", "/v1/transfers", {"b": 2, "a": 1})


def test_fingerprint_changes_with_body_or_path():
    base = request_fingerprint("POST", "/v1/transfers", {"amount_minor": 5})
    assert base != request_fingerprint("POST", "/v1/transfers", {"amount_minor": 6})
    assert base != request_fingerprint("POST", "/v1/other", {"amount_minor": 5})


def test_canonical_ts_treats_naive_as_utc():
    aware = datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
    assert canonical_ts(aware) == canonical_ts(aware.replace(tzinfo=None)) == "2026-01-02T03:04:05.123456Z"


def test_entry_hash_is_deterministic_and_chained():
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    h1 = entry_hash(GENESIS_HASH, "t1", "w1", "DEBIT", 100, "USD", ts)
    assert h1 == entry_hash(GENESIS_HASH, "t1", "w1", "DEBIT", 100, "USD", ts)
    assert h1 != entry_hash(GENESIS_HASH, "t1", "w1", "DEBIT", 101, "USD", ts)
    assert entry_hash(h1, "t1", "w2", "CREDIT", 100, "USD", ts) != entry_hash(GENESIS_HASH, "t1", "w2", "CREDIT", 100, "USD", ts)
