"""Core ledger logic: deposits, transfers, reversals and reconciliation.

Rules this module enforces:
- Every write method runs inside ONE transaction started with BEGIN IMMEDIATE (see database.make_engine).
  The first statement of each method is the idempotency lookup, so no balance is read before the lock is held.
- Every movement of money is a balanced pair of entries (debit + credit). Deposits debit the system funding wallet.
- Ledger rows are only ever inserted. Mistakes are corrected by reversal transactions.
"""

import functools
import json
from datetime import datetime, timezone
from typing import Any, Callable, NamedTuple
from uuid import uuid4

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.constants import SUPPORTED_CURRENCIES
from app.core.errors import (ConflictError, InsufficientFundsError, NotFoundError, UnprocessableError)
from app.core.hashing import GENESIS_HASH, entry_hash
from app.models.idempotency_key import IdempotencyKey
from app.models.ledger_entry import LedgerEntry
from app.models.ledger_transaction import LedgerTransaction
from app.models.wallet import Wallet


class Result(NamedTuple):
    status: int
    body: dict
    replayed: bool = False


def _atomic(fn):
    """Roll the whole transaction back if anything goes wrong."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except BaseException:
            self.db.rollback()
            raise
    return wrapper


class LedgerService:
    def __init__(self, db: Session, clock: Callable[[], datetime] | None = None,
                 id_generator: Callable[[], str] | None = None):
        self.db = db
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.new_id = id_generator or (lambda: str(uuid4()))

    # ---------------------------------------------------------------- helpers
    def _replay(self, key: str, request_hash: str) -> Result | None:
        """Idempotency lookup. Must be the first statement of every write method."""
        record = self.db.get(IdempotencyKey, key)
        if record is None:
            return None
        self.db.rollback()  # nothing to write: release the write lock
        if record.request_hash != request_hash:
            raise UnprocessableError("IDEMPOTENCY_KEY_REUSED", "this Idempotency-Key was already used with a different request")
        return Result(record.response_status, json.loads(record.response_body), replayed=True)

    def _store(self, key: str, request_hash: str, status: int, body: dict, transaction_id: str) -> None:
        self.db.add(IdempotencyKey(key=key, request_hash=request_hash, response_status=status,
                                   response_body=json.dumps(body), transaction_id=transaction_id,
                                   created_at=self.clock()))

    def _new_txn(self, txn_type: str, amount: int, currency: str, reverses: str | None = None) -> LedgerTransaction:
        txn = LedgerTransaction(id=self.new_id(), type=txn_type, amount_minor=amount, currency=currency,
                                reverses_transaction_id=reverses, created_at=self.clock())
        self.db.add(txn)
        self.db.flush()
        return txn

    def _post(self, txn: LedgerTransaction, wallet: Wallet, direction: str, amount: int) -> None:
        """Insert one hash-chained ledger entry and move the wallet balance."""
        if direction == "DEBIT":
            wallet.balance_minor -= amount
            if wallet.balance_minor < 0 and not wallet.is_system:
                raise InsufficientFundsError("insufficient funds")
        else:
            wallet.balance_minor += amount
        prev = self.db.execute(select(LedgerEntry.entry_hash).order_by(LedgerEntry.seq.desc()).limit(1)).scalar() or GENESIS_HASH
        now = self.clock()
        self.db.add(LedgerEntry(
            transaction_id=txn.id, wallet_id=wallet.id, direction=direction, amount_minor=amount,
            currency=wallet.currency, prev_hash=prev,
            entry_hash=entry_hash(prev, txn.id, wallet.id, direction, amount, wallet.currency, now),
            created_at=now))
        self.db.flush()

    def _require_currency(self, currency: str) -> None:
        if currency not in SUPPORTED_CURRENCIES:
            raise UnprocessableError("CURRENCY_NOT_SUPPORTED", f"currency must be one of {', '.join(SUPPORTED_CURRENCIES)}")

    def _user_wallet(self, wallet_id: str) -> Wallet:
        wallet = self.db.get(Wallet, wallet_id)
        if wallet is None:
            raise NotFoundError(f"wallet {wallet_id} not found")
        if wallet.is_system:
            raise UnprocessableError("SYSTEM_WALLET_NOT_ALLOWED", "system wallets cannot be used in this operation")
        return wallet

    # ---------------------------------------------------------------- writes
    @_atomic
    def deposit(self, wallet_id: str, amount: int, currency: str, key: str, request_hash: str) -> Result:
        if (replay := self._replay(key, request_hash)):
            return replay
        self._require_currency(currency)
        wallet = self._user_wallet(wallet_id)
        if wallet.currency != currency:
            raise UnprocessableError("CURRENCY_MISMATCH", "wallet currency does not match the request currency")
        funding = self.db.execute(select(Wallet).where(Wallet.is_system.is_(True), Wallet.currency == currency)).scalar_one()
        txn = self._new_txn("deposit", amount, currency)
        self._post(txn, funding, "DEBIT", amount)
        self._post(txn, wallet, "CREDIT", amount)
        body = {"transaction_id": txn.id, "wallet_id": wallet.id, "amount_minor": amount, "currency": currency,
                "balance_minor": wallet.balance_minor, "status": "success"}
        self._store(key, request_hash, 201, body, txn.id)
        self.db.commit()
        return Result(201, body)

    @_atomic
    def transfer(self, source_id: str, destination_id: str, amount: int, currency: str, key: str, request_hash: str) -> Result:
        if (replay := self._replay(key, request_hash)):
            return replay
        source = self._user_wallet(source_id)
        destination = self._user_wallet(destination_id)
        if source.id == destination.id:
            raise UnprocessableError("SAME_WALLET", "source and destination wallets must differ")
        self._require_currency(currency)
        if source.currency != currency or destination.currency != currency:
            raise UnprocessableError("CURRENCY_MISMATCH", "both wallets must use the transfer currency")
        if source.balance_minor < amount:
            raise InsufficientFundsError("source wallet does not have sufficient balance")
        txn = self._new_txn("transfer", amount, currency)
        self._post(txn, source, "DEBIT", amount)
        self._post(txn, destination, "CREDIT", amount)
        body = {"transaction_id": txn.id, "source_wallet_id": source.id, "destination_wallet_id": destination.id,
                "amount_minor": amount, "currency": currency, "status": "success"}
        self._store(key, request_hash, 201, body, txn.id)
        self.db.commit()
        return Result(201, body)

    @_atomic
    def reverse(self, transaction_id: str, key: str, request_hash: str) -> Result:
        if (replay := self._replay(key, request_hash)):
            return replay
        original = self.db.get(LedgerTransaction, transaction_id)
        if original is None:
            raise NotFoundError(f"transaction {transaction_id} not found")
        if original.type == "reversal":
            raise ConflictError("a reversal cannot itself be reversed")
        if self.db.query(LedgerTransaction).filter(LedgerTransaction.reverses_transaction_id == transaction_id).first():
            raise ConflictError("transaction has already been reversed")
        entries = self.db.query(LedgerEntry).filter(LedgerEntry.transaction_id == transaction_id).order_by(LedgerEntry.seq).all()
        reversal = self._new_txn("reversal", original.amount_minor, original.currency, reverses=transaction_id)
        for entry in entries:
            wallet = self.db.get(Wallet, entry.wallet_id)
            self._post(reversal, wallet, "CREDIT" if entry.direction == "DEBIT" else "DEBIT", entry.amount_minor)
        body = {"transaction_id": reversal.id, "reverses_transaction_id": transaction_id,
                "amount_minor": original.amount_minor, "currency": original.currency, "status": "success"}
        self._store(key, request_hash, 201, body, reversal.id)
        self.db.commit()
        return Result(201, body)

    # ---------------------------------------------------------------- reads
    def get_transfer(self, transfer_id: str) -> dict[str, Any]:
        txn = self.db.get(LedgerTransaction, transfer_id)
        if txn is None or txn.type != "transfer":
            raise NotFoundError(f"transfer {transfer_id} not found")
        entries = self.db.query(LedgerEntry).filter(LedgerEntry.transaction_id == txn.id).order_by(LedgerEntry.seq).all()
        return {"id": txn.id, "type": txn.type, "amount_minor": txn.amount_minor, "currency": txn.currency,
                "reverses_transaction_id": txn.reverses_transaction_id,
                "created_at": txn.created_at.isoformat() if txn.created_at else None,
                "entries": [entry_to_dict(e) for e in entries]}

    def reconcile(self) -> dict[str, Any]:
        """Read-only integrity check. Run on a read session so all queries share one snapshot."""
        db = self.db
        problems: list[dict[str, Any]] = []

        def problem(kind, expected=None, actual=None, **extra):
            problems.append({"type": kind, "wallet_id": None, "transaction_id": None, "seq": None,
                             "expected": expected, "actual": actual, **extra})

        debit = func.coalesce(func.sum(case((LedgerEntry.direction == "DEBIT", LedgerEntry.amount_minor), else_=0)), 0)
        credit = func.coalesce(func.sum(case((LedgerEntry.direction == "CREDIT", LedgerEntry.amount_minor), else_=0)), 0)

        # (a) every transaction balances; transactions must have entries
        per_txn = {tid: (d, c) for tid, d, c in db.execute(select(LedgerEntry.transaction_id, debit, credit).group_by(LedgerEntry.transaction_id))}
        txn_ids = [t for (t,) in db.execute(select(LedgerTransaction.id))]
        for tid in txn_ids:
            d, c = per_txn.get(tid, (0, 0))
            if d != c or tid not in per_txn:
                problem("transaction_unbalanced", expected=c, actual=d, transaction_id=tid)
        # (b) whole ledger balances
        total_d, total_c = db.execute(select(debit, credit)).one()
        if total_d != total_c:
            problem("ledger_unbalanced", expected=total_c, actual=total_d)
        # (c) wallet balance == credits - debits
        per_wallet = {wid: c - d for wid, d, c in db.execute(select(LedgerEntry.wallet_id, debit, credit).group_by(LedgerEntry.wallet_id))}
        wallets = db.query(Wallet).all()
        for w in wallets:
            expected = per_wallet.get(w.id, 0)
            if w.balance_minor != expected:
                problem("wallet_balance_mismatch", expected=expected, actual=w.balance_minor, wallet_id=w.id)
        # (d) all balances of one currency (funding wallet included) sum to zero
        sums: dict[str, int] = {}
        for w in wallets:
            sums[w.currency] = sums.get(w.currency, 0) + w.balance_minor
        for currency, total in sums.items():
            if total != 0:
                problem("currency_sum_nonzero", expected=0, actual=total, currency=currency)
        # (e) hash chain: report the first broken sequence number
        prev = GENESIS_HASH
        entries = db.query(LedgerEntry).order_by(LedgerEntry.seq.asc()).all()
        for e in entries:
            expected_hash = entry_hash(prev, e.transaction_id, e.wallet_id, e.direction, e.amount_minor, e.currency, e.created_at)
            if e.prev_hash != prev or e.entry_hash != expected_hash:
                problem("hash_chain_break", expected=expected_hash, actual=e.entry_hash, seq=e.seq,
                        wallet_id=e.wallet_id, transaction_id=e.transaction_id)
                break
            prev = e.entry_hash

        return {"status": "PASS" if not problems else "FAIL", "transactions_checked": len(txn_ids),
                "entries_checked": len(entries), "wallets_checked": len(wallets), "discrepancies": problems}


def entry_to_dict(e: LedgerEntry) -> dict[str, Any]:
    return {"seq": e.seq, "transaction_id": e.transaction_id, "wallet_id": e.wallet_id, "direction": e.direction,
            "amount_minor": e.amount_minor, "currency": e.currency, "prev_hash": e.prev_hash,
            "entry_hash": e.entry_hash, "created_at": e.created_at.isoformat() if e.created_at else None}
