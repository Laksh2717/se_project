from pydantic import BaseModel, ConfigDict

from app.schemas.common import CurrencyCode, UuidStr


class WalletCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UuidStr
    currency: CurrencyCode


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    currency: str
    balance_minor: int
    is_system: bool
