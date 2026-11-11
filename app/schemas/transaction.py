from pydantic import BaseModel, ConfigDict, Field, field_validator


class DepositRequest(BaseModel):
    wallet_id: str
    amount_minor: int = Field(gt=0)
    currency: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return normalized


class TransferRequest(BaseModel):
    source_wallet_id: str
    destination_wallet_id: str
    amount_minor: int = Field(gt=0)
    currency: str
    idempotency_key: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return normalized


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    status: str
    message: str
