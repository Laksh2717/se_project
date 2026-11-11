from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.wallet import WalletCreate, WalletRead
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/v1", tags=["wallets"])


@router.post("/wallets", response_model=WalletRead)
def create_wallet(payload: WalletCreate, db: Session = Depends(get_db)):
    service = WalletService(db)
    wallet = service.create_wallet(payload.user_id, payload.currency, payload.is_system)
    return wallet


@router.get("/wallets/{wallet_id}", response_model=WalletRead)
def get_wallet(wallet_id: str, db: Session = Depends(get_db)):
    service = WalletService(db)
    wallet = service.get_wallet(wallet_id)
    return wallet
