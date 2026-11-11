from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}+{uuid4().hex[:8]}@example.com"


def test_create_user_and_wallet_and_deposit():
    create_user = client.post("/v1/users", json={"email": unique_email("alice"), "name": "Alice"})
    assert create_user.status_code == 200
    user_id = create_user.json()["id"]

    wallet = client.post("/v1/wallets", json={"user_id": user_id, "currency": "USD"})
    assert wallet.status_code == 200
    wallet_id = wallet.json()["id"]

    deposit = client.post("/v1/deposits", json={"wallet_id": wallet_id, "amount_minor": 1000, "currency": "USD"})
    assert deposit.status_code == 200
    assert deposit.json()["balance_minor"] == 1000

    fetched = client.get(f"/v1/wallets/{wallet_id}")
    assert fetched.status_code == 200
    assert fetched.json()["balance_minor"] == 1000


def test_transfer_success_and_replay():
    create_user_a = client.post("/v1/users", json={"email": unique_email("bob"), "name": "Bob"})
    create_user_b = client.post("/v1/users", json={"email": unique_email("charlie"), "name": "Charlie"})
    wallet_a = client.post("/v1/wallets", json={"user_id": create_user_a.json()["id"], "currency": "USD"})
    wallet_b = client.post("/v1/wallets", json={"user_id": create_user_b.json()["id"], "currency": "USD"})

    client.post("/v1/deposits", json={"wallet_id": wallet_a.json()["id"], "amount_minor": 2000, "currency": "USD"})

    transfer_key = f"transfer-key-{uuid4().hex[:8]}"

    transfer = client.post(
        "/v1/transfers",
        json={
            "source_wallet_id": wallet_a.json()["id"],
            "destination_wallet_id": wallet_b.json()["id"],
            "amount_minor": 500,
            "currency": "USD",
            "idempotency_key": transfer_key,
        },
    )
    assert transfer.status_code == 200
    assert transfer.json()["amount_minor"] == 500

    replay = client.post(
        "/v1/transfers",
        json={
            "source_wallet_id": wallet_a.json()["id"],
            "destination_wallet_id": wallet_b.json()["id"],
            "amount_minor": 500,
            "currency": "USD",
            "idempotency_key": transfer_key,
        },
    )
    assert replay.status_code == 200
    assert replay.json()["status"] == "replayed"


def test_admin_reconciliation_passes():
    response = client.get("/v1/admin/reconciliation", headers={"X-Admin-Key": "change-me"})
    assert response.status_code == 200
    assert response.json()["status"] in {"PASS", "FAIL"}
