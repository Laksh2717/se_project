from pydantic import BaseModel, ConfigDict, Field, StrictInt

from app.core.constants import MAX_AMOUNT_MINOR
from app.schemas.common import CurrencyCode, UuidStr

# StrictInt rejects 10.5, 10.0, "10" and true; gt/le reject 0, negatives and absurd amounts.
AmountMinor = StrictInt


class DepositRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_minor: AmountMinor = Field(gt=0, le=MAX_AMOUNT_MINOR)
    currency: CurrencyCode


class TransferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_wallet_id: UuidStr
    destination_wallet_id: UuidStr
    amount_minor: AmountMinor = Field(gt=0, le=MAX_AMOUNT_MINOR)
    currency: CurrencyCode
