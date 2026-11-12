from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="ck_entry_amount_positive"),
        CheckConstraint("direction IN ('DEBIT','CREDIT')", name="ck_entry_direction"),
    )

    seq = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey("ledger_transactions.id"), nullable=False)
    wallet_id = Column(String, ForeignKey("wallets.id"), nullable=False)
    direction = Column(String, nullable=False)
    amount_minor = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    prev_hash = Column(String, nullable=False)
    entry_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
