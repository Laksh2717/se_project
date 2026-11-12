"""FR-4 / FR-5 / TQ-2: immutability, rollback, reconciliation, 503."""
import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app
from app.services.ledger_service import LedgerService
from tests.helpers import ADMIN, balance, deposit, key, make_wallet, reconcile, scalar, transfer


@pytest.mark.parametrize("sql", [
    "update ledger_entries set amount_minor = 1",
    "delete from ledger_entries",
    "update ledger_transactions set amount_minor = 1",
    "delete from ledger_transactions",
])
def test_ledger_tables_reject_update_and_delete(client, app, sql):
    deposit(client, make_wallet(client), 100)
    with pytest.raises(Exception, match="immutable"):
        with app.state.engine.begin() as conn:
            conn.execute(text(sql))


def test_no_api_route_edits_or_deletes_ledger_data(client):
    for method in ("put", "patch", "delete"):
        for path in ("/v1/transfers/00000000-0000-4000-8000-000000000000", "/v1/wallets/00000000-0000-4000-8000-000000000000/entries"):
            assert getattr(client, method)(path).status_code in (404, 405)


def test_failure_mid_transfer_rolls_everything_back(app, monkeypatch):
    client = TestClient(app, raise_server_exceptions=False)
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    before = {t: scalar(app, f"select count(*) from {t}") for t in ("ledger_entries", "ledger_transactions", "idempotency_keys")}
    original, calls = LedgerService._post, {"n": 0}

    def flaky(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("boom after the debit entry")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(LedgerService, "_post", flaky)
    h = key()
    r = transfer(client, a, b, 100, headers=h)
    assert r.status_code == 500 and "boom" not in r.text and "Traceback" not in r.text
    assert (balance(client, a), balance(client, b)) == (1000, 0)
    assert before == {t: scalar(app, f"select count(*) from {t}") for t in before}
    monkeypatch.setattr(LedgerService, "_post", original)
    assert transfer(client, a, b, 100, headers=h).status_code == 201  # same key can be retried
    assert reconcile(client)["status"] == "PASS"


def test_reconcile_passes_on_empty_and_requires_admin_key(client):
    assert reconcile(client)["status"] == "PASS"
    assert client.get("/v1/admin/reconciliation").status_code == 401
    assert client.get("/v1/admin/reconciliation", headers={"X-Admin-Key": "wrong"}).status_code == 401


def test_reconcile_detects_tampered_wallet_balance(client, app):
    a = make_wallet(client)
    deposit(client, a, 100)
    with app.state.engine.begin() as conn:
        conn.execute(text("update wallets set balance_minor = balance_minor + 5 where id = :id"), {"id": a})
    report = reconcile(client)
    assert report["status"] == "FAIL"
    bad = [d for d in report["discrepancies"] if d["type"] == "wallet_balance_mismatch"]
    assert bad and bad[0]["wallet_id"] == a and (bad[0]["expected"], bad[0]["actual"]) == (100, 105)


def test_reconcile_detects_tampered_ledger_row_and_reports_first_broken_seq(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 100)
    transfer(client, a, b, 10)
    with app.state.engine.begin() as conn:  # an attacker with file access removes the trigger first
        conn.execute(text("drop trigger prevent_update_ledger_entries"))
        conn.execute(text("update ledger_entries set amount_minor = amount_minor + 1 where seq = 3"))
    report = reconcile(client)
    brk = [d for d in report["discrepancies"] if d["type"] == "hash_chain_break"]
    assert report["status"] == "FAIL" and brk and brk[0]["seq"] == 3


def test_database_busy_returns_503_with_retry_after(tmp_path):
    url = f"sqlite:///{tmp_path / 'busy.db'}"
    app = create_app(url, busy_timeout_ms=50)
    client = TestClient(app)
    holder = sqlite3.connect(tmp_path / "busy.db", isolation_level=None)
    holder.execute("BEGIN IMMEDIATE")  # another writer holds the lock
    try:
        r = client.post("/v1/users", json={"email": "busy@example.com", "name": "Busy"})
    finally:
        holder.execute("ROLLBACK")
        holder.close()
    assert r.status_code == 503 and r.headers["Retry-After"] == "1" and r.json()["error"]["code"] == "DATABASE_BUSY"
    assert scalar(app, "select count(*) from users where email='busy@example.com'") == 0
