from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ledger_entry import LedgerEntry
from app.models.wallet import Wallet

router = APIRouter(prefix="/v1", tags=["wallet-entries"])


@router.get("/wallets/{wallet_id}/entries")
def get_wallet_entries(
    wallet_id: str,
    cursor: int | None = Query(default=None),
    limit: int = Query(default=100, le=100),
    db: Session = Depends(get_db),
):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="wallet not found")

    query = db.query(LedgerEntry).filter(LedgerEntry.wallet_id == wallet_id).order_by(LedgerEntry.seq.asc())
    if cursor is not None:
        query = query.filter(LedgerEntry.seq > cursor)

    entries = query.limit(limit).all()
    return {
        "wallet_id": wallet_id,
        "items": [
            {
                "seq": item.seq,
                "transaction_id": item.transaction_id,
                "wallet_id": item.wallet_id,
                "direction": item.direction,
                "amount_minor": item.amount_minor,
                "currency": item.currency,
                "prev_hash": item.prev_hash,
                "entry_hash": item.entry_hash,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in entries
        ],
        "next_cursor": entries[-1].seq if entries else None,
    }
