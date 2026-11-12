from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="ck_txn_amount_positive"),
        CheckConstraint("type IN ('deposit','transfer','reversal')", name="ck_txn_type"),
    )

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    amount_minor = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    # unique: a transaction can be reversed at most once
    reverses_transaction_id = Column(String, ForeignKey("ledger_transactions.id"), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
