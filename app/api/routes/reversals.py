from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_write_db, idempotency_key
from app.api.routes.transactions import respond
from app.core.hashing import request_fingerprint
from app.schemas.common import PathUuid
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/v1", tags=["reversals"])


@router.post("/transactions/{transaction_id}/reversal", status_code=201, summary="Reverse a transfer or deposit (once, in full)")
def create_reversal(request: Request, transaction_id: PathUuid,
                    key: str = Depends(idempotency_key), db: Session = Depends(get_write_db)):
    fingerprint = request_fingerprint(request.method, request.url.path, {})
    return respond(LedgerService(db).reverse(transaction_id, key, fingerprint))
