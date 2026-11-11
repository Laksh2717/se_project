from pydantic import BaseModel, ConfigDict, Field


class DepositRequest(BaseModel):
    wallet_id: str
    amount_minor: int = Field(gt=0)
    currency: str


class TransferRequest(BaseModel):
    source_wallet_id: str
    destination_wallet_id: str
    amount_minor: int = Field(gt=0)
    currency: str
    idempotency_key: str


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    status: str
    message: str
