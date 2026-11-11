import json
import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import ConflictError, InsufficientFundsError, NotFoundError, ValidationError
from app.models.idempotency_key import IdempotencyKey
from app.models.ledger_entry import LedgerEntry
from app.models.ledger_transaction import LedgerTransaction
from app.models.wallet import Wallet

settings = get_settings()


class LedgerService:
    def __init__(self, db: Session):
        self.db = db

    def _new_txn(self, txn_type: str, amount_minor: int, currency: str, reverses_transaction_id: str | None = None) -> LedgerTransaction:
        transaction = LedgerTransaction(
            id=str(uuid4()),
            type=txn_type,
            amount_minor=amount_minor,
            currency=currency.upper(),
            reverses_transaction_id=reverses_transaction_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def _last_entry_hash(self) -> str:
        row = self.db.query(LedgerEntry).order_by(LedgerEntry.seq.desc()).first()
        return row.entry_hash if row else "GENESIS"

    def _build_entry_hash(self, prev_hash: str, transaction_id: str, wallet_id: str, direction: str, amount_minor: int, currency: str, created_at: datetime) -> str:
        payload = "|".join([
            prev_hash,
            transaction_id,
            wallet_id,
            direction,
            str(amount_minor),
            currency,
            created_at.isoformat(),
        ])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _append_ledger_entry(self, transaction: LedgerTransaction, wallet: Wallet, direction: str, amount_minor: int) -> LedgerEntry:
        prev_hash = self._last_entry_hash()
        created_at = datetime.now(timezone.utc)
        entry_hash = self._build_entry_hash(prev_hash, transaction.id, wallet.id, direction, amount_minor, wallet.currency, created_at)
        entry = LedgerEntry(
            transaction_id=transaction.id,
            wallet_id=wallet.id,
            direction=direction,
            amount_minor=amount_minor,
            currency=wallet.currency,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            created_at=created_at,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def deposit(self, wallet_id: str, amount_minor: int, currency: str) -> dict[str, Any]:
        if amount_minor <= 0:
            raise ValidationError("amount_minor must be > 0")

        wallet = self.db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if not wallet:
            raise NotFoundError(f"Wallet {wallet_id} not found")
        if wallet.currency != currency.upper():
            raise ValidationError("wallet currency does not match request currency")

        try:
            transaction = self._new_txn("deposit", amount_minor, currency)
            wallet.balance_minor += amount_minor
            self._append_ledger_entry(transaction, wallet, "CREDIT", amount_minor)
            self.db.flush()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return {
            "transaction_id": transaction.id,
            "wallet_id": wallet.id,
            "balance_minor": wallet.balance_minor,
            "status": "success",
        }

    def transfer(self, source_wallet_id: str, destination_wallet_id: str, amount_minor: int, currency: str, idempotency_key: str, request_hash: str) -> dict[str, Any]:
        if amount_minor <= 0:
            raise ValidationError("amount_minor must be > 0")
        if source_wallet_id == destination_wallet_id:
            raise ValidationError("source and destination wallets must differ")

        source_wallet = self.db.query(Wallet).filter(Wallet.id == source_wallet_id).first()
        destination_wallet = self.db.query(Wallet).filter(Wallet.id == destination_wallet_id).first()
        if not source_wallet or not destination_wallet:
            raise NotFoundError("source and destination wallets must both exist")
        if source_wallet.currency != currency.upper() or destination_wallet.currency != currency.upper():
            raise ValidationError("both wallets must use the same currency")
        if source_wallet.balance_minor < amount_minor:
            raise InsufficientFundsError("source wallet does not have sufficient balance")

        existing = self.db.query(IdempotencyKey).filter(IdempotencyKey.key == idempotency_key).first()
        if existing:
            if existing.request_hash != request_hash:
                raise ConflictError("idempotency key already used with different request payload")
            response_payload = json.loads(existing.response_body)
            return {
                "transaction_id": existing.transaction_id,
                "status": "replayed",
                "message": "request replayed with same payload",
                "response": response_payload,
            }

        try:
            transaction = self._new_txn("transfer", amount_minor, currency)
            source_wallet.balance_minor -= amount_minor
            destination_wallet.balance_minor += amount_minor
            self._append_ledger_entry(transaction, source_wallet, "DEBIT", amount_minor)
            self._append_ledger_entry(transaction, destination_wallet, "CREDIT", amount_minor)

            response_payload = {
                "transaction_id": transaction.id,
                "source_wallet_id": source_wallet.id,
                "destination_wallet_id": destination_wallet.id,
                "amount_minor": amount_minor,
                "currency": currency.upper(),
                "status": "success",
            }

            record = IdempotencyKey(
                key=idempotency_key,
                request_hash=request_hash,
                response_status=200,
                response_body=json.dumps(response_payload),
                transaction_id=transaction.id,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(record)
            self.db.flush()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return response_payload

    def reverse_transaction(self, transaction_id: str, idempotency_key: str, request_hash: str) -> dict[str, Any]:
        original = self.db.query(LedgerTransaction).filter(LedgerTransaction.id == transaction_id).first()
        if not original:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        if original.type == "reversal" or original.reverses_transaction_id is not None:
            raise ConflictError("transaction is already reversed or is itself a reversal")

        existing = self.db.query(IdempotencyKey).filter(IdempotencyKey.key == idempotency_key).first()
        if existing:
            if existing.request_hash != request_hash:
                raise ConflictError("idempotency key already used with different request payload")
            response_payload = json.loads(existing.response_body)
            return {
                "transaction_id": existing.transaction_id,
                "status": "replayed",
                "message": "reversal replayed with same payload",
                "response": response_payload,
            }

        entries = self.db.query(LedgerEntry).filter(LedgerEntry.transaction_id == transaction_id).all()
        if not entries:
            raise ValidationError("transaction has no ledger entries to reverse")

        try:
            reversal_txn = self._new_txn("reversal", original.amount_minor, original.currency, reverses_transaction_id=transaction_id)
            reversal_payload = {
                "transaction_id": reversal_txn.id,
                "reverses_transaction_id": transaction_id,
                "amount_minor": original.amount_minor,
                "currency": original.currency,
                "status": "success",
            }

            for entry in entries:
                wallet = self.db.query(Wallet).filter(Wallet.id == entry.wallet_id).first()
                if not wallet:
                    raise NotFoundError(f"Wallet {entry.wallet_id} not found")

                target_direction = "CREDIT" if entry.direction == "DEBIT" else "DEBIT"
                if target_direction == "DEBIT" and wallet.balance_minor < entry.amount_minor:
                    raise InsufficientFundsError("reversal would make the wallet balance negative")

                wallet.balance_minor += entry.amount_minor if target_direction == "CREDIT" else -entry.amount_minor
                self._append_ledger_entry(reversal_txn, wallet, target_direction, entry.amount_minor)

            record = IdempotencyKey(
                key=idempotency_key,
                request_hash=request_hash,
                response_status=200,
                response_body=json.dumps(reversal_payload),
                transaction_id=reversal_txn.id,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(record)
            self.db.flush()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return reversal_payload

    def reconcile(self) -> dict[str, Any]:
        wallets = self.db.query(Wallet).all()
        entries = self.db.query(LedgerEntry).order_by(LedgerEntry.seq.asc()).all()
        transactions = self.db.query(LedgerTransaction).count()
        discrepancies = []

        per_transaction = {}
        for entry in entries:
            tx_id = entry.transaction_id
            per_transaction.setdefault(tx_id, {"debits": 0, "credits": 0})
            if entry.direction == "DEBIT":
                per_transaction[tx_id]["debits"] += entry.amount_minor
            elif entry.direction == "CREDIT":
                per_transaction[tx_id]["credits"] += entry.amount_minor

        for tx_id, totals in per_transaction.items():
            if totals["debits"] != totals["credits"]:
                discrepancies.append({
                    "transaction_id": tx_id,
                    "type": "transaction_balance_mismatch",
                    "expected": totals["credits"],
                    "actual": totals["debits"],
                })

        for wallet in wallets:
            expected = self.db.query(func.coalesce(func.sum(LedgerEntry.amount_minor), 0)).filter(
                LedgerEntry.wallet_id == wallet.id,
                LedgerEntry.direction == "CREDIT"
            ).scalar() or 0
            actual_debits = self.db.query(func.coalesce(func.sum(LedgerEntry.amount_minor), 0)).filter(
                LedgerEntry.wallet_id == wallet.id,
                LedgerEntry.direction == "DEBIT"
            ).scalar() or 0
            expected_balance = expected - actual_debits
            if wallet.balance_minor != expected_balance:
                discrepancies.append({
                    "wallet_id": wallet.id,
                    "type": "wallet_balance_mismatch",
                    "expected": expected_balance,
                    "actual": wallet.balance_minor,
                })

        prev_hash = "GENESIS"
        for entry in entries:
            expected_hash = self._build_entry_hash(prev_hash, entry.transaction_id, entry.wallet_id, entry.direction, entry.amount_minor, entry.currency, entry.created_at)
            if entry.entry_hash != expected_hash:
                discrepancies.append({
                    "wallet_id": entry.wallet_id,
                    "transaction_id": entry.transaction_id,
                    "type": "hash_chain_break",
                    "first_sequence": entry.seq,
                    "expected": expected_hash,
                    "actual": entry.entry_hash,
                })
                break
            prev_hash = entry.entry_hash

        status = "PASS" if not discrepancies else "FAIL"
        return {
            "status": status,
            "transactions_checked": transactions,
            "entries_checked": len(entries),
            "wallets_checked": len(wallets),
            "discrepancies": discrepancies,
        }
