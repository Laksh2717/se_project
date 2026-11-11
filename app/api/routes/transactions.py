import hashlib
import json

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.database import get_db
from app.schemas.transaction import DepositRequest, TransferRequest
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/v1", tags=["transactions"])


@router.post("/deposits")
def make_deposit(payload: DepositRequest, db: Session = Depends(get_db)):
    service = LedgerService(db)
    return service.deposit(payload.wallet_id, payload.amount_minor, payload.currency)


@router.post("/transfers")
def make_transfer(
    payload: TransferRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    effective_key = (idempotency_key or getattr(payload, "idempotency_key", None) or "").strip()
    if not effective_key:
        raise ValidationError("Idempotency-Key header is required")

    request_hash = hashlib.sha256(
        json.dumps(payload.model_dump(), sort_keys=True).encode("utf-8")
    ).hexdigest()
    service = LedgerService(db)
    return service.transfer(
        payload.source_wallet_id,
        payload.destination_wallet_id,
        payload.amount_minor,
        payload.currency,
        effective_key,
        request_hash,
    )
