from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_transfer_validation_errors():
    response = client.post(
        "/v1/transfers",
        json={
            "source_wallet_id": "abc",
            "destination_wallet_id": "xyz",
            "amount_minor": 0,
            "currency": "USD",
            "idempotency_key": "key-1",
        },
    )
    assert response.status_code == 422


def test_deposit_invalid_amount():
    response = client.post(
        "/v1/deposits",
        json={"wallet_id": "missing-wallet", "amount_minor": -5, "currency": "USD"},
    )
    assert response.status_code == 422
