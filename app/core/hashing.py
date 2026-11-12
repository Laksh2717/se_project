"""Pure functions: request fingerprinting and the ledger hash chain (no database access)."""

import hashlib
import json
from datetime import datetime, timezone

GENESIS_HASH = "GENESIS"


def canonical_json(body) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def request_fingerprint(method: str, path: str, body) -> str:
    """SHA-256 of method + path + canonical body, stored with an Idempotency-Key."""
    raw = f"{method.upper()}\n{path}\n{canonical_json(body)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def canonical_ts(dt: datetime) -> str:
    """One timestamp format for hashing. SQLite returns naive datetimes, so naive means UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def entry_hash(prev_hash: str, transaction_id: str, wallet_id: str, direction: str,
               amount_minor: int, currency: str, created_at: datetime) -> str:
    payload = "|".join([prev_hash, transaction_id, wallet_id, direction,
                        str(amount_minor), currency, canonical_ts(created_at)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
