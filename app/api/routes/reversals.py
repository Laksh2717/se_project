import hashlib
import json

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.database import get_db
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/v1", tags=["reversals"])


class ReversalRequest(BaseModel):
    idempotency_key: str = ""


@router.post("/transactions/{transaction_id}/reversal")
def create_reversal(
    transaction_id: str,
    payload: ReversalRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    effective_key = (idempotency_key or payload.idempotency_key or "").strip()
    if not effective_key:
        raise ValidationError("Idempotency-Key header is required")

    request_hash = hashlib.sha256(
        json.dumps({"transaction_id": transaction_id, "idempotency_key": effective_key}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    service = LedgerService(db)
    return service.reverse_transaction(transaction_id, effective_key, request_hash)
