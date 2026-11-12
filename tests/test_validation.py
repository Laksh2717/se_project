"""NFR (security/validation) and TQ-4 negative tests."""
import pytest

from tests.helpers import deposit, key, make_wallet, reconcile, scalar, transfer

ZERO = "00000000-0000-4000-8000-000000000000"


@pytest.mark.parametrize("amount", [0, -500, 10.5, 10.0, "10", True, None, 10**12 + 1])
def test_bad_amounts_are_400_and_store_nothing(client, app, amount):
    w = make_wallet(client)
    r = client.post(f"/v1/wallets/{w}/deposits", json={"amount_minor": amount, "currency": "USD"}, headers=key())
    assert r.status_code == 400 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert scalar(app, "select count(*) from ledger_entries") == 0


def test_max_amount_is_accepted(client):
    assert deposit(client, make_wallet(client), 10**12).status_code == 201


def test_malformed_ids_are_400(client):
    assert client.get("/v1/wallets/not-a-uuid").status_code == 400
    assert client.post("/v1/transfers", json={"source_wallet_id": "x", "destination_wallet_id": "y", "amount_minor": 1, "currency": "USD"}, headers=key()).status_code == 400
    assert client.post("/v1/wallets", json={"user_id": "x", "currency": "USD"}).status_code == 400


def test_unknown_and_missing_fields_are_400(client):
    a, b = make_wallet(client), make_wallet(client)
    body = {"source_wallet_id": a, "destination_wallet_id": b, "amount_minor": 1, "currency": "USD"}
    assert client.post("/v1/transfers", json={**body, "extra": 1}, headers=key()).status_code == 400
    assert client.post("/v1/transfers", json={k: v for k, v in body.items() if k != "currency"}, headers=key()).status_code == 400
    assert client.post("/v1/transfers", json={**body, "idempotency_key": "in-body"}, headers=key()).status_code == 400


def test_semantic_errors_are_422_or_404(client):
    a, b, eur = make_wallet(client), make_wallet(client), make_wallet(client, "EUR")
    deposit(client, a, 100)
    assert transfer(client, a, a, 10).status_code == 422                      # same wallet
    assert transfer(client, a, eur, 10).status_code == 422                    # currency mismatch
    assert transfer(client, a, b, 10, currency="EUR").status_code == 422      # wrong request currency
    assert transfer(client, a, ZERO, 10).status_code == 404                   # unknown wallet
    assert deposit(client, a, 10, currency="EUR").status_code == 422
    assert reconcile(client)["status"] == "PASS"


def test_unsupported_currency_is_422(client):
    user = client.post("/v1/users", json={"email": "c@example.com", "name": "C"}).json()["id"]
    r = client.post("/v1/wallets", json={"user_id": user, "currency": "XYZ"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "CURRENCY_NOT_SUPPORTED"


def test_duplicate_email_and_duplicate_wallet_are_409(client):
    body = {"email": "dup@example.com", "name": "D"}
    first = client.post("/v1/users", json=body)
    assert first.status_code == 201 and client.post("/v1/users", json=body).status_code == 409
    uid = first.json()["id"]
    assert client.post("/v1/wallets", json={"user_id": uid, "currency": "USD"}).status_code == 201
    assert client.post("/v1/wallets", json={"user_id": uid, "currency": "USD"}).status_code == 409
    assert client.post("/v1/wallets", json={"user_id": ZERO, "currency": "USD"}).status_code == 404


def test_clients_cannot_create_or_use_system_wallets(client, app):
    uid = client.post("/v1/users", json={"email": "s@example.com", "name": "S"}).json()["id"]
    assert client.post("/v1/wallets", json={"user_id": uid, "currency": "USD", "is_system": True}).status_code == 400
    funding = scalar(app, "select id from wallets where is_system=1 and currency='USD'")
    assert deposit(client, funding, 100).status_code == 422
    assert transfer(client, funding, make_wallet(client), 1).status_code == 422


def test_foreign_keys_are_enforced_on_every_connection(app):
    for _ in range(3):
        with app.state.engine.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_errors_use_one_envelope_and_never_leak_internals(client):
    for r in (client.get("/v1/wallets/bad"), client.get(f"/v1/wallets/{ZERO}"), client.get("/v1/admin/reconciliation")):
        assert set(r.json()) == {"error"} and {"code", "message"} <= set(r.json()["error"])
    assert "Traceback" not in client.get(f"/v1/wallets/{ZERO}").text


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
