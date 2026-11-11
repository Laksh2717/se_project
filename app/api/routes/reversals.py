import hashlib
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/v1", tags=["reversals"])


class ReversalRequest(BaseModel):
    idempotency_key: str


@router.post("/transactions/{transaction_id}/reversal")
def create_reversal(transaction_id: str, payload: ReversalRequest, db: Session = Depends(get_db)):
    request_hash = hashlib.sha256(
        json.dumps({"transaction_id": transaction_id, "idempotency_key": payload.idempotency_key}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    service = LedgerService(db)
    return service.reverse_transaction(transaction_id, payload.idempotency_key, request_hash)
