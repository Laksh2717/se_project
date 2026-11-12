from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_read_db, get_write_db, idempotency_key
from app.core.hashing import request_fingerprint
from app.schemas.common import PathUuid
from app.schemas.transaction import DepositRequest, TransferRequest
from app.services.ledger_service import LedgerService, Result

router = APIRouter(prefix="/v1", tags=["transactions"])


def respond(result: Result) -> JSONResponse:
    headers = {"Idempotent-Replayed": "true"} if result.replayed else None
    return JSONResponse(content=result.body, status_code=result.status, headers=headers)


@router.post("/wallets/{wallet_id}/deposits", status_code=201, summary="Fund a wallet from the system funding account")
def make_deposit(request: Request, wallet_id: PathUuid, payload: DepositRequest,
                 key: str = Depends(idempotency_key), db: Session = Depends(get_write_db)):
    fingerprint = request_fingerprint(request.method, request.url.path, payload.model_dump())
    return respond(LedgerService(db).deposit(wallet_id, payload.amount_minor, payload.currency, key, fingerprint))


@router.post("/transfers", status_code=201, summary="Transfer between two wallets (idempotent)")
def make_transfer(request: Request, payload: TransferRequest,
                  key: str = Depends(idempotency_key), db: Session = Depends(get_write_db)):
    fingerprint = request_fingerprint(request.method, request.url.path, payload.model_dump())
    return respond(LedgerService(db).transfer(payload.source_wallet_id, payload.destination_wallet_id,
                                              payload.amount_minor, payload.currency, key, fingerprint))


@router.get("/transfers/{transfer_id}", summary="Transfer details with its ledger entries")
def get_transfer(transfer_id: PathUuid, db: Session = Depends(get_read_db)):
    return LedgerService(db).get_transfer(transfer_id)
