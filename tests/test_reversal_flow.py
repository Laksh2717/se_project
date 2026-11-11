from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}+{uuid4().hex[:8]}@example.com"


def test_reversal_creates_compensating_entries():
    create_user_a = client.post("/v1/users", json={"email": unique_email("alice"), "name": "Alice"})
    create_user_b = client.post("/v1/users", json={"email": unique_email("bob"), "name": "Bob"})
    wallet_a = client.post("/v1/wallets", json={"user_id": create_user_a.json()["id"], "currency": "USD"})
    wallet_b = client.post("/v1/wallets", json={"user_id": create_user_b.json()["id"], "currency": "USD"})

    client.post("/v1/deposits", json={"wallet_id": wallet_a.json()["id"], "amount_minor": 2000, "currency": "USD"})
    transfer = client.post(
        "/v1/transfers",
        json={
            "source_wallet_id": wallet_a.json()["id"],
            "destination_wallet_id": wallet_b.json()["id"],
            "amount_minor": 500,
            "currency": "USD",
            "idempotency_key": f"transfer-{uuid4().hex[:8]}",
        },
    )
    assert transfer.status_code == 200

    reversal = client.post(
        f"/v1/transactions/{transfer.json()['transaction_id']}/reversal",
        json={"idempotency_key": f"reversal-{uuid4().hex[:8]}"},
    )
    assert reversal.status_code == 200
    assert reversal.json()["reverses_transaction_id"] == transfer.json()["transaction_id"]
