from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_read_db
from app.core.errors import NotFoundError
from app.models.ledger_entry import LedgerEntry
from app.models.wallet import Wallet
from app.schemas.common import PathUuid
from app.services.ledger_service import entry_to_dict

router = APIRouter(prefix="/v1", tags=["wallet-entries"])


@router.get("/wallets/{wallet_id}/entries", summary="Ledger entries of a wallet, ascending by sequence")
def get_wallet_entries(wallet_id: PathUuid, db: Session = Depends(get_read_db)):
    if db.get(Wallet, wallet_id) is None:
        raise NotFoundError(f"wallet {wallet_id} not found")
    entries = db.query(LedgerEntry).filter(LedgerEntry.wallet_id == wallet_id).order_by(LedgerEntry.seq.asc()).all()
    return {"wallet_id": wallet_id, "items": [entry_to_dict(e) for e in entries]}
