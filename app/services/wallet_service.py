from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.wallet import Wallet


class WalletService:
    def __init__(self, db: Session):
        self.db = db

    def create_wallet(self, user_id: str, currency: str, is_system: bool = False) -> Wallet:
        if not user_id or not currency:
            raise ValidationError("user_id and currency are required")

        wallet = Wallet(
            id=str(uuid4()),
            user_id=user_id,
            currency=currency.upper(),
            balance_minor=0,
            is_system=is_system,
        )
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def get_wallet(self, wallet_id: str) -> Wallet:
        wallet = self.db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if not wallet:
            raise NotFoundError(f"Wallet {wallet_id} not found")
        return wallet

    def get_wallets_for_user(self, user_id: str):
        return self.db.query(Wallet).filter(Wallet.user_id == user_id).all()
