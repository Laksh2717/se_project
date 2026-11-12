from uuid import uuid4

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.constants import SUPPORTED_CURRENCIES, SYSTEM_USER_EMAIL

Base = declarative_base()


def make_engine(url: str, busy_timeout_ms: int = 5000):
    """Create the SQLite engine.

    - PRAGMAs are applied on EVERY new connection (foreign_keys and busy_timeout are per-connection).
    - The driver is put in manual-transaction mode so we control BEGIN ourselves:
      write sessions use BEGIN IMMEDIATE (take the write lock before reading balances),
      read sessions use BEGIN DEFERRED (one consistent snapshot in WAL mode).
    """
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):
        dbapi_conn.isolation_level = None  # we issue BEGIN ourselves
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")  # safe with WAL: a crash can lose only the last commit, never corrupt
        cur.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    @event.listens_for(engine, "begin")
    def _on_begin(conn):
        mode = "IMMEDIATE" if conn.get_execution_options().get("write") else "DEFERRED"
        conn.exec_driver_sql(f"BEGIN {mode}")

    return engine


def make_session_factories(engine):
    """Return (write_factory, read_factory) bound to the same engine."""
    write = sessionmaker(bind=engine.execution_options(write=True), autoflush=False, expire_on_commit=False)
    read = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return write, read


_TRIGGERS = [
    ("prevent_update_ledger_transactions", "UPDATE", "ledger_transactions"),
    ("prevent_delete_ledger_transactions", "DELETE", "ledger_transactions"),
    ("prevent_update_ledger_entries", "UPDATE", "ledger_entries"),
    ("prevent_delete_ledger_entries", "DELETE", "ledger_entries"),
]


def init_db(engine) -> None:
    """Create tables, immutability triggers and one system funding wallet per currency (idempotent)."""
    from app.models import User, Wallet  # noqa: F401  (also registers all models)

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        for name, op, table in _TRIGGERS:
            conn.execute(text(
                f"CREATE TRIGGER IF NOT EXISTS {name} BEFORE {op} ON {table} "
                f"BEGIN SELECT RAISE(ABORT, '{table} are immutable'); END;"
            ))

    write_engine = engine.execution_options(write=True)
    with Session(write_engine) as db:
        system_user = db.query(User).filter(User.email == SYSTEM_USER_EMAIL).first()
        if system_user is None:
            system_user = User(id=str(uuid4()), email=SYSTEM_USER_EMAIL, name="System")
            db.add(system_user)
            db.flush()
        for currency in SUPPORTED_CURRENCIES:
            exists = db.query(Wallet).filter(Wallet.user_id == system_user.id, Wallet.currency == currency).first()
            if exists is None:
                db.add(Wallet(id=str(uuid4()), user_id=system_user.id, currency=currency, balance_minor=0, is_system=True))
        db.commit()
