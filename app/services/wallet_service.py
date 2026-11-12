from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.constants import SUPPORTED_CURRENCIES
from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.models.user import User
from app.models.wallet import Wallet


class WalletService:
    def __init__(self, db: Session):
        self.db = db

    def create_wallet(self, user_id: str, currency: str) -> Wallet:
        currency = currency.upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise UnprocessableError("CURRENCY_NOT_SUPPORTED", f"currency must be one of {', '.join(SUPPORTED_CURRENCIES)}")
        user = self.db.get(User, user_id)  # first statement of the write transaction
        if user is None:
            self.db.rollback()
            raise NotFoundError(f"user {user_id} not found")
        if self.db.query(Wallet).filter(Wallet.user_id == user_id, Wallet.currency == currency).first():
            self.db.rollback()
            raise ConflictError("user already has a wallet in this currency")
        wallet = Wallet(id=str(uuid4()), user_id=user_id, currency=currency, balance_minor=0, is_system=False)
        self.db.add(wallet)
        self.db.commit()
        return wallet

    def get_wallet(self, wallet_id: str) -> Wallet:
        wallet = self.db.get(Wallet, wallet_id)
        if wallet is None:
            raise NotFoundError(f"wallet {wallet_id} not found")
        return wallet
