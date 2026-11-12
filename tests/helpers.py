from uuid import uuid4

from sqlalchemy import text

ADMIN = {"X-Admin-Key": "change-me"}


def key() -> dict:
    return {"Idempotency-Key": uuid4().hex}


def make_wallet(client, currency="USD") -> str:
    user = client.post("/v1/users", json={"email": f"{uuid4().hex[:10]}@example.com", "name": "Test"})
    assert user.status_code == 201, user.text
    wallet = client.post("/v1/wallets", json={"user_id": user.json()["id"], "currency": currency})
    assert wallet.status_code == 201, wallet.text
    return wallet.json()["id"]


def deposit(client, wallet_id, amount, currency="USD", headers=None):
    return client.post(f"/v1/wallets/{wallet_id}/deposits", json={"amount_minor": amount, "currency": currency},
                       headers=key() if headers is None else headers)


def transfer(client, src, dst, amount, currency="USD", headers=None):
    return client.post("/v1/transfers", json={"source_wallet_id": src, "destination_wallet_id": dst,
                                              "amount_minor": amount, "currency": currency}, headers=key() if headers is None else headers)


def reverse(client, transaction_id, headers=None):
    return client.post(f"/v1/transactions/{transaction_id}/reversal", headers=key() if headers is None else headers)


def balance(client, wallet_id) -> int:
    return client.get(f"/v1/wallets/{wallet_id}").json()["balance_minor"]


def reconcile(client) -> dict:
    return client.get("/v1/admin/reconciliation", headers=ADMIN).json()


def scalar(app, sql, **params):
    with app.state.engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()
