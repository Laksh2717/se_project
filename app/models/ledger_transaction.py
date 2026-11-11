from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    amount_minor = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    reverses_transaction_id = Column(String, ForeignKey("ledger_transactions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    referenced_transaction = relationship("LedgerTransaction", remote_side="LedgerTransaction.id", uselist=False)
