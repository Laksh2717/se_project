"""FR-2: Idempotency-Key header behaviour."""
import pytest

from tests.helpers import balance, deposit, key, make_wallet, reverse, scalar, transfer

BAD_KEYS = [None, "", "has space", "x" * 65, "bad!char"]


@pytest.mark.parametrize("bad", BAD_KEYS)
def test_missing_or_invalid_key_is_400_on_every_write(client, bad):
    a, b = make_wallet(client), make_wallet(client)
    h = {} if bad is None else {"Idempotency-Key": bad}
    assert deposit(client, a, 10, headers=h).status_code == 400
    assert transfer(client, a, b, 10, headers=h).status_code == 400
    assert client.post("/v1/transactions/00000000-0000-4000-8000-000000000000/reversal", headers=h).status_code == 400


def test_replay_returns_same_status_body_and_header_and_writes_nothing(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    h = key()
    first = transfer(client, a, b, 100, headers=h)
    entries = scalar(app, "select count(*) from ledger_entries")
    again = transfer(client, a, b, 100, headers=h)
    assert again.status_code == first.status_code == 201 and again.json() == first.json()
    assert again.headers["Idempotent-Replayed"] == "true" and "Idempotent-Replayed" not in first.headers
    assert scalar(app, "select count(*) from ledger_entries") == entries and balance(client, a) == 900


def test_replay_after_balance_drained_still_returns_stored_response(client):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 100)
    h = key()
    first = transfer(client, a, b, 100, headers=h)
    again = transfer(client, a, b, 100, headers=h)
    assert again.status_code == 201 and again.json() == first.json()


def test_same_key_different_body_is_422(client):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    h = key()
    transfer(client, a, b, 100, headers=h)
    r = transfer(client, a, b, 200, headers=h)
    assert r.status_code == 422 and r.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_same_key_on_a_different_endpoint_is_422(client):
    a, b = make_wallet(client), make_wallet(client)
    h = key()
    deposit(client, a, 500, headers=h)
    assert transfer(client, a, b, 100, headers=h).status_code == 422


def test_failed_request_leaves_no_key_and_retry_works(client, app):
    a, b = make_wallet(client), make_wallet(client)
    h = key()
    assert transfer(client, a, b, 100, headers=h).status_code == 422
    assert scalar(app, "select count(*) from idempotency_keys") == 0
    deposit(client, a, 100)
    assert transfer(client, a, b, 100, headers=h).status_code == 201


def test_deposit_and_reversal_are_idempotent(client):
    a = make_wallet(client)
    h = key()
    d1, d2 = deposit(client, a, 100, headers=h), deposit(client, a, 100, headers=h)
    assert d1.json() == d2.json() and balance(client, a) == 100
    rh = key()
    r1, r2 = reverse(client, d1.json()["transaction_id"], headers=rh), reverse(client, d1.json()["transaction_id"], headers=rh)
    assert r1.status_code == r2.status_code == 201 and r1.json() == r2.json() and balance(client, a) == 0
