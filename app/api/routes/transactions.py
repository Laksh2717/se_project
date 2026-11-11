import hashlib
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transaction import DepositRequest, TransferRequest
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/v1", tags=["transactions"])


@router.post("/deposits")
def make_deposit(payload: DepositRequest, db: Session = Depends(get_db)):
    service = LedgerService(db)
    return service.deposit(payload.wallet_id, payload.amount_minor, payload.currency)


@router.post("/transfers")
def make_transfer(payload: TransferRequest, db: Session = Depends(get_db)):
    request_hash = hashlib.sha256(
        json.dumps(payload.model_dump(), sort_keys=True).encode("utf-8")
    ).hexdigest()
    service = LedgerService(db)
    return service.transfer(
        payload.source_wallet_id,
        payload.destination_wallet_id,
        payload.amount_minor,
        payload.currency,
        payload.idempotency_key,
        request_hash,
    )
