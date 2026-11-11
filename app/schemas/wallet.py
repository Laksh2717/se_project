from pydantic import BaseModel, ConfigDict


class WalletCreate(BaseModel):
    user_id: str
    currency: str
    is_system: bool = False


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    currency: str
    balance_minor: int
    is_system: bool
