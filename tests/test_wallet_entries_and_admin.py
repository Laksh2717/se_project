from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}+{uuid4().hex[:8]}@example.com"


def test_wallet_entries_are_returned_in_order():
    user = client.post("/v1/users", json={"email": unique_email("entries-user"), "name": "Entries User"})
    wallet = client.post("/v1/wallets", json={"user_id": user.json()["id"], "currency": "USD"})
    client.post("/v1/deposits", json={"wallet_id": wallet.json()["id"], "amount_minor": 100, "currency": "USD"})

    response = client.get(f"/v1/wallets/{wallet.json()['id']}/entries")
    assert response.status_code == 200
    assert response.json()["items"][0]["direction"] == "CREDIT"


def test_admin_reconciliation_requires_key():
    response = client.get("/v1/admin/reconciliation")
    assert response.status_code == 401
