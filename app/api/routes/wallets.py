from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_read_db, get_write_db
from app.schemas.common import PathUuid
from app.schemas.wallet import WalletCreate, WalletRead
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/v1", tags=["wallets"])


@router.post("/wallets", response_model=WalletRead, status_code=201, summary="Create a wallet for a user and currency")
def create_wallet(payload: WalletCreate, db: Session = Depends(get_write_db)):
    return WalletService(db).create_wallet(payload.user_id, payload.currency)


@router.get("/wallets/{wallet_id}", response_model=WalletRead, summary="Get a wallet and its balance")
def get_wallet(wallet_id: PathUuid, db: Session = Depends(get_read_db)):
    return WalletService(db).get_wallet(wallet_id)
